#!/usr/bin/python
# -*- coding: latin-1 -*-
import datetime
import logging, logging.handlers
import mpd
import os
import psutil
import re
import RPi.GPIO as GPIO
import serial
import signal
import subprocess
import time
import pdb

# TODO: Laden van playlist veranderen


HOME_DIR = os.path.dirname(os.path.realpath(__file__))

# TODO: Test configfile
# TODO: Add shit to configfile
config = ConfigParser.ConfigParser()
config.read(os.path.join(HOME_DIR, "verhalenmachine.cfg"))


# LOGGING
# TODO: Cleanup logging
LOG_FILE = os.path.join(HOME_DIR, "verhalenmachine.log")

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

fh = logging.handlers.RotatingFileHandler(
              LOG_FILE, maxBytes=5000000, backupCount=5)
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

class Player:
    'Player'

    def __init__(self):
        from mpd import MPDClient
        self.client = MPDClient()
        self.client.connect("localhost", 6600)

        # TODO: Check whether this works. It seems not.
        self.client.repeat(1)
        self.client.random(1)

        # TODO: Check volume max and min
        # TODO: Map slider to volume range
        self.min_volume = 0
        self.max_voume = 100
        self.prev_volume = None

    def is_playing(self):
        logger.debug("MPD status: %s" % self.client.status())
        if self.client.status().get('state') == "play":
            return True
        return False

    def play(self):
        self.client.play()

    def pause(self):
        self.client.pause(1)

    def next(self):
        self.client.next()

    def stop(self):
        self.client.stop()

    def set_volume(self, new_volume):
        if new_volume != self.prev_volume:
            if new_volume > self.max_volume:
                new_volume = self.max_volume
            if new_volume < self.min_volume:
                new_volume = self.min_volume
            logger.debug("Changing volume from %s to %s" % (self.prev_volume, new_volume))
            self.client.setvol(new_volume)
            self.prev_volume = new_volume

    def set_volume_decimal(self, volume_decimal):
        self.set_volume(int(volume_decimal*100))

    # def get_volume(self):
    #     return int(self.client.status().get('volume'))

    def load_playlist(self):
        self.client.clear()
        self.client.add('INTERNAL')

    def update_database(self):
        self.client.update()

class Recorder:
    '''
    Recorder
    arecord -D plughw:CARD=E205U,DEV=0 -f S16_LE -c1 -r 22050 -V mono -v bla.wav
    arecord -D plughw:CARD=Device,DEV=0 -f S16_LE -c1 -r 22050 -V mono -v bla.wav
    '''

    def __init__(self):
        # TODO: Throw exception when mic does not exist
        # self.SOUND_CARD_MIC = "plughw:CARD=Device,DEV=0" # USB audio card
        self.SOUND_CARD_MIC = "plughw:CARD=E205U,DEV=0" # Superlux USB mic
        self.RECORDING_DIR = "/data/INTERNAL/"
        self.RECORDING_PROCESS_ID_FILE = "recprocess.pid"

    def get_pid(self):
        try:
            pidfile = os.path.join(HOME_DIR, self.RECORDING_PROCESS_ID_FILE)
            f = open(pidfile)
            pid = int(f.readline().strip())
            f.close()
            return pid
        except:
            return False

    def is_recording(self):
        # TODO: Test
        if psutil.pid_exists(self.get_pid()):
            return True
        return False

        #  >>> import os.path
        #  >>> os.path.exists("/proc/0")
        #  False
        #  >>> os.path.exists("/proc/12")
        #  True

    def record(self, filename):
        # TODO: RESEARCH/ ASK DAVID how to control VU meter with mic input
        filepath = os.path.join(self.RECORDING_DIR+filename)
        args = [
            'arecord',
            '-D', self.SOUND_CARD_MIC,
            '-f', 'S16_LE',
            '-c1',
            '-r22050',
            '-V', 'mono',
            '-v', # for VU meter output, maybe use -vv or -v or -vvv
            '--process-id-file', self.RECORDING_PROCESS_ID_FILE,
            filepath+".temp"
        ]
        logger.debug(args)
        proc = subprocess.Popen(args, stdout=subprocess.PIPE)

    def remove_temp_ext(self):
        # remove .temp extension files
        for root, dirs, files in os.walk(self.RECORDING_DIR):
            for filename in files:
                if os.path.splitext(filename)[1] == ".temp":
                    path_to_file = os.path.join(root, filename)
                    os.rename(path_to_file, os.path.splitext(path_to_file)[0])
                    logger.debug("Renamed temp file to %s", os.path.splitext(path_to_file)[0])

    def stop(self):
        pid = self.get_pid()
        if pid:
            logger.debug("Stopping recording process by killing PID %s", str(pid))
            os.kill(pid, signal.SIGINT)
        self.remove_temp_ext()

    def dontplayfortoolong(self):
        # TODO: Give normal function name
        # TODO: Test whether this works
        # TODO: Check this periodically, like every 15mins (cron? https://stackoverflow.com/questions/3987041/python-run-function-from-the-command-line)
        # Fixen als hij te lang opneemt wav-01, wav-02, wav-03
        # Opname stoppen na een uur? (pid file leeftijd)
        import psutil, datetime, time
        if self.is_recording():
            p = psutil.Process(self.get_pid())
            create_time = p.create_time()
            current_time = time.time()
            if current_time - create_time > 30 * 60:
                # stop when recording longer than half an hour
                self.stop()

class Led:
    '''
    LED
    '''
    def __init__(self, pin):
        # Pin Setup:
        self.pin = pin

        # Initiate LED
        GPIO.setup(self.pin, GPIO.OUT)
        self.blink()

    def on(self):
        GPIO.output(self.pin, GPIO.HIGH)
        logger.debug("LED (pin %s) ON." % self.pin)

    def off(self):
        GPIO.output(self.pin, GPIO.LOW)
        logger.debug("LED (pin %s) OFF." % self.pin)

    def blink(self, times=1, sleep=0.5):
        count = 0
        while count<times:
            self.on()
            time.sleep(sleep)
            self.off()
            if count<times-1:
                time.sleep(sleep)
            count = count+1

class Kiku:
    '''
    Klik aan klik uit
    '''
    # TODO: Test!
    # TODO: Kijk of het goed gaat met meerdere seriele connecties
    def __init__(self):
        self.ser = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1.0)

    def on(self):
        self.ser.write("ka\r")

    def off(self):
        self.ser.write("ku\r")

class Button:
    def __init__(self, pin):
        # Pin Setup:
        self.pin = pin

        # Initiate button as input w/ pull-up
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.pin, GPIO.FALLING, bouncetime=200)

class Uploader:
    # TODO: Implement uploading
    # TODO: Implement uploading to several playlists again?

    def __init__(self):
        # TODO: Test
        self.client = soundcloud.Client(
            # TODO: try to get this to work with just a secret key
            self.client_id = config.get("upload", "client_id"),
            self.client_secret = config.get("upload", "client_secret"),
            self.username = config.get("upload", "username"),
            self.password = config.get("upload", "password"),
        )
        # TODO: Add to config
        self.RECORDING_DIR = "/data/INTERNAL/"

    def cleanrecordingdir(self):
        # TODO: Move to uploader?
        # TODO: Implement cleaning
        # TODO: Test whether this works
        # TODO: Do this periodically (cron?) or just before uploading
        for root, dirs, files in os.walk(self.RECORDING_DIR):
            for filename in files:
                if os.path.getsize(filename) == 0: # or os.path.getsize(filename) > xxxx
                    # Remove 0 byte files
                    # Remove bigger than x GB?
                    # TODO: Add max size
                    path_to_file = os.path.join(root, filename)
                    os.remove(path_to_file)

    def check_files_to_upload(self):
        # # walk through all files in recording directory
        # logger.debug("Checking contents of %s", self.RECORDING_DIR)
        # from os.path import join, getsize
        # count = 0
        # # TODO: Replace with counter object
        # uploaded_track = False
        # for root, dirs, files in os.walk(self.RECORDING_DIR):
        #     for filename in files:
        #         # check whether it is a music file that can be uploaded to soundcloud
        #         # http://uploadandmanage.help.soundcloud.com/customer/portal/articles/2162441-uploading-requirements
        #         # AIFF, WAVE (WAV), FLAC, ALAC, OGG, MP2, MP3, AAC, AMR, and WMA
        #         # and ignore hidden files
        #         if filename.lower().endswith(('.aiff', '.wav', '.flac', '.alac', '.ogg', '.mp2', '.mp3', '.aac', '.amr', '.wma')) and not filename.startswith('.'):
        #             path_to_file = os.path.join(root, filename)
        # #
        #             # TODO: Change this to a check of the id in the filename
        #             not_uploaded_file = os.path.splitext(path_to_file)[0]+".notuploaded"
        #             img_file = os.path.splitext(path_to_file)[0]+".jpg"
        #             # soundcloud_set_file = os.path.splitext(path_to_file)[0]+".setname"
        #             if os.path.isfile(not_uploaded_file):
        pass

    def upload_track(self, track):
        # get playlist
        # set_id = os.path.basename(os.path.normpath(os.path.dirname(path_to_file)))
        # logger.debug("Set id: %s", set_id)
        # playlist = client.get("/playlists/"+set_id)
        # logger.debug("Playlist: %s", playlist)
        #
        # # upload to soundcloud
        # datetimenow = datetime.datetime.now()
        # track_dict = {
        #     # TODO: Set more track data, get input somewhere
        #     'title': unicode(os.path.splitext(filename)[0]),
        #     'asset_data': open(path_to_file, 'rb'),
        #     'description': u'Dit is een van Jimmy\'s Verhalen. Opgenomen op %s om %s in de categorie "%s".' % (datetimenow.__format__("%e-%m-%Y"), datetimenow.__format__("%T"), playlist.title),
        #     'track_type': 'spoken',
        #     'purchase_url': "http://wijzijnjimmys.nl/verhalen/",
        #     'license': "cc-by-nc",
        #     'tag_list': "jimmys verhalen"
        #     # 'genre': 'Electronic',
        # }
        # if os.path.isfile(img_file):
        #     track_dict['artwork_data'] = open(img_file, 'rb')
        #
        # uploaded_track = client.post('/tracks', track=track_dict)
        # logger.debug("Uploaded %s to Soundcloud: %s (%s).", filename, uploaded_track.permalink_url, uploaded_track.id)
        #
        # # add soundcloud id to filename
        # filename_with_soundcloud_id = "%s.%s%s" % (os.path.splitext(path_to_file)[0], uploaded_track.id, os.path.splitext(path_to_file)[1])
        # os.rename(path_to_file, filename_with_soundcloud_id)
        #
        # # Add Track to right Set
        # # f = open(soundcloud_set_file)
        # # set_id = f.readline().strip().split("&", 1)[0].replace("id=", "")
        # # f.close()
        # if uploaded_track:
        # UPDATE_TRACKLIST
        # # remove .notuploaded file
        # os.remove(not_uploaded_file)
        # count +=1
        pass

    def update_tracklist(self, tracklist):
        #     # generate tracklist of current playlist
        #     track_id_list = []
        #     for track in playlist.tracks:
        #         track_id_list.append(track['id'])
        #     logger.debug("%s, %s", playlist.title, track_id_list)
        #
        #     # add uploaded track to list
        #     track_id_list.append(uploaded_track.id)
        #
        #     updated_playlist = client.put("/playlists/"+set_id, playlist={
        #         'tracks': map(lambda id: dict(id=id), track_id_list)
        #     })
        #     logger.debug("%s, %s", updated_playlist.title, track_id_list)
        pass

try:
    player = Player()
    player.update_database()
    player.load_playlist()

    recorder = Recorder()

    kiku = Kiku()

    GPIO.cleanup()
    GPIO.setmode(GPIO.BOARD)  # Broadcom pin-numbering scheme
    button1 = Button(40)
    button2 = Button(38)
    button3 = Button(36)
    led1 = Led(37)
    led2 = Led(35)
    led3 = Led(33)
    ser = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1.0)
    prev_input = None

    while True:
        if GPIO.event_detected(button1.pin):
            if recorder.is_recording():
                recorder.stop()
                # TODO: Control leds separately from buttons
                led1.off()
                # kiku.off()
            else:
                if player.is_playing():
                    player.stop()
                current_datetime = "%s" % (datetime.datetime.now().__format__("%Y-%m-%d_%T"))
                sound_file_name = "%s.wav" % (current_datetime)
                recorder.record(sound_file_name)
                led1.on()
                # kiku.on()

        if GPIO.event_detected(button2.pin):
            if player.is_playing():
                player.stop()
                led2.off()
            else:
                player.play()
                led2.on()

        if GPIO.event_detected(button3.pin):
            player.next()
            led3.blink(times=3, sleep=0.5)

        # Control player led also when play/ stop has been used externally
        if player.is_playing():
            led2.on()
        else:
            led2.off()

        # Control recorder led also when recordering has been stopped externally
        if not recorder.is_recording():
            led1.off()
            # TODO: implement kiku
            # kiku.off()

        # Read volume slider data from serial port
        ser.flushInput()
        ser_input = ser.readline()
        ser_decimals = re.findall("\d+\.\d+", ser_input)
        if len(ser_decimals) == 1 and ser_input != prev_input:
            logger.debug(ser_decimals)
            # logger.debug(int(float(ser_decimals[0])*100))
            player.set_volume_decimal(float(ser_decimals[0]))

            # ser_data = int(float(ser_decimals[0])*100)
            # if ser_data == 0:
            #     ser_data = 1
            # ser.write(str(ser_data)+"\r")

            prev_input = ser_input

        time.sleep(0.5)

except KeyboardInterrupt:  # If CTRL+C is pressed, exit cleanly:
    GPIO.cleanup()  # cleanup all GPIO
except Exception, e:
    logging.error(e, exc_info=True)
