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
import ConfigParser
import soundcloud

HOME_DIR = os.path.dirname(os.path.realpath(__file__))

# TODO: Move classes to separate file(s)

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

        self.min_volume = 10
        self.max_volume = 90
        self.prev_volume = None

    def is_playing(self):
        status = self.client.status()
        # logger.debug("MPD status: %s" % status)
        if status.get('state') == "play":
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
        volume = self.min_volume + volume_decimal*(self.max_volume-self.min_volume)
        self.set_volume(int(volume))

    # def get_volume(self):
    #     return int(self.client.status().get('volume'))

    def load_playlist(self):
        # TODO: Laden van playlist veranderen, zodat dit samenwerkt met Volumio GUI
        # TODO: Echt een playlist van maken, zelfde naamgeving als bij uploaden
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
        self.filepath = ""

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
        if psutil.pid_exists(self.get_pid()):
            return True
            logger.debug("RECORDING")
        else:
            return False
            logger.debug("NOT RECORDING!")

    def record(self, filename):
        # TODO: RESEARCH/ ASK DAVID how to control VU meter with mic input
        self.filepath = os.path.join(self.RECORDING_DIR+"verhalenmachine_"+filename)
        args = [
            'arecord',
            '-D', self.SOUND_CARD_MIC,
            '-f', 'S16_LE',
            '-c1',
            '-r22050',
            '-V', 'mono',
            # '-v', # for VU meter output, maybe use -vv or -v or -vvv
            '--process-id-file', self.RECORDING_PROCESS_ID_FILE,
            self.filepath+".temp"
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

    def add_not_uploaded_file(self):
        # TODO: TEST
        if self.filepath:
            not_uploaded_file = os.path.splitext(self.filepath)[0] + ".notuploaded"
            f = open(not_uploaded_file, 'w')
            f.close()

    def stop(self):
        pid = self.get_pid()
        if pid:
            logger.debug("Stopping recording process by killing PID %s", str(pid))
            os.kill(pid, signal.SIGINT)
        self.remove_temp_ext()
        self.add_not_uploaded_file()
        # TODO: Aan playlist toevoegen?

    def dontrecordfortoolong(self):
        # TODO: Fixen als hij te lang opneemt wav-01, wav-02, wav-03 (>2GB)
        if self.is_recording():
            p = psutil.Process(self.get_pid())
            logger.debug("Recording: %s" % p)
            create_time = p.create_time()
            current_time = time.time()
            duration = (current_time - create_time)/60
            logger.debug("Recording for: %s" % duration)
            if duration > 30:
                # stop when recording longer than half an hour
                self.stop()
        else:
            logger.debug("Not recording")

class Led:
    '''
    LED
    '''
    def __init__(self, pin):
        # Pin Setup:
        self.pin = pin

        # Initiate LED
        GPIO.setup(self.pin, GPIO.OUT)
        self.burning = False
        self.blink()

    def on(self):
        GPIO.output(self.pin, GPIO.HIGH)
        self.burning = True
        logger.debug("LED (pin %s) ON." % self.pin)

    def off(self):
        GPIO.output(self.pin, GPIO.LOW)
        self.burning = False
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
        self.burning = False

    def on(self):
        self.ser.write("ka\r")
        self.burning = True
        logger.debug("KIKU ON")

    def off(self):
        self.ser.write("ku\r")
        self.burning = False
        logger.debug("KIKU OFF")

class Volumeslider:
    '''
    slider
    '''
    # TODO: Kijk of het goed gaat met meerdere seriele connecties
    def __init__(self):
        self.ser = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1.0)
        self.prev_input = None

    def read(self):
        self.ser.flushInput()
        ser_input = self.ser.readline()
        ser_decimals = re.findall("\d+\.\d+", ser_input)
        if len(ser_decimals) == 1:
            return ser_decimals[0]
        else:
            return None

        logger.debug("KIKU ON")

    def read_new(self):
        ser_decimals = self.read()
        if ser_decimals and ser_decimals != self.prev_input:
            logger.debug("VOLUME SLIDER: %s" % ser_decimals)
            self.prev_input = ser_decimals
            return ser_decimals
        else:
            return None

class Button:
    def __init__(self, pin):
        # Pin Setup:
        self.pin = pin

        # Initiate button as input w/ pull-up
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.pin, GPIO.FALLING, bouncetime=200)

class Uploader:
    # TODO: Implement uploading to several playlists again (settings or ip or wlan name or ...)
    # TODO: Add cronjob

    def __init__(self):
        # TODO: Add to config
        self.client = soundcloud.Client(client_id="2afa000b9c16670dd62c83700567487f", client_secret="dbf7e4b8b8140f142b62c8e93b4d0ab8", username="erwin@uptous.nl", password="ell82SOU!")
        logger.debug("SOUNDCLOUD connected to %s " % self.client.get('/me').username)

        # self.client = soundcloud.Client(
        #     client_id = config.get("upload", "client_id"),
        #     client_secret = config.get("upload", "client_secret"),
        #     username = config.get("upload", "username"),
        #     password = config.get("upload", "password"),
        # )

        # TODO: Add to config
        self.RECORDING_DIR = "/data/INTERNAL/"

    def clean_directory(self, directory=""):
        # TODO: Do this periodically (cron?) or just before uploading
        if directory == "":
            directory = self.RECORDING_DIR
        for root, dirs, files in os.walk(directory):
            for filename in files:
                # logger.debug("FILESIZE %s %s" % (filename, os.path.getsize(os.path.join(root, filename))))
                # Remove 0 byte files
                # TODO: Maybe add max size, i.e. Remove bigger than x GB? (x 1000 000 000 bytes)
                if filename.lower().endswith(('.aiff', '.wav', '.flac', '.alac', '.ogg', '.mp2', '.mp3', '.aac', '.amr', '.wma')) and not filename.startswith('.'):
                    if os.path.getsize(os.path.join(root, filename)) == 0: # or os.path.getsize(filename) > xxxx
                        path_to_file = os.path.join(root, filename)
                        logger.debug("REMOVING %s %s" % (filename, os.path.getsize(os.path.join(root, filename))))
                        os.remove(path_to_file)

    def upload_directory(self, directory=""):
        if directory == "":
            directory = self.RECORDING_DIR
        # walk through all files in recording directory
        logger.debug("Checking contents of %s", directory)
        count = 0
        # TODO: Replace with counter object
        for root, dirs, files in os.walk(directory):
            for filename in files:
                # check whether it is a music file that can be uploaded to soundcloud
                # http://uploadandmanage.help.soundcloud.com/customer/portal/articles/2162441-uploading-requirements
                # AIFF, WAVE (WAV), FLAC, ALAC, OGG, MP2, MP3, AAC, AMR, and WMA
                # and ignore hidden files
                if filename.lower().endswith(('.aiff', '.wav', '.flac', '.alac', '.ogg', '.mp2', '.mp3', '.aac', '.amr', '.wma')) and not filename.startswith('.'):
                    path_to_file = os.path.join(root, filename)
                    logger.debug(path_to_file)
                    not_uploaded_file = os.path.splitext(path_to_file)[0]+".notuploaded"
                    if os.path.isfile(not_uploaded_file):
                        self.upload_track(path_to_file)
                        count = count+1
        logger.debug("UPLOADED %s files" % count)

    def upload_track(self, path_to_file):
        # get playlist
        # set_id = os.path.basename(os.path.normpath(os.path.dirname(path_to_file)))
        # logger.debug("Set id: %s", set_id)
        # playlist = client.get("/playlists/"+set_id)
        # logger.debug("Playlist: %s", playlist)
        track_dict = {
            # TODO: Set more track data, get input somewhere
            'title': unicode(os.path.splitext(path_to_file)[0]),
            'asset_data': open(path_to_file, 'rb'),
            'description': u'Dit verhaal is opgenomen met de verhalenmachine op %s om %s.' % (datetime.datetime.now().__format__("%e-%m-%Y"), datetime.datetime.now().__format__("%T")),
            'track_type': 'spoken',
            'license': "cc-by-nc",
            'sharing': "private",
            # 'purchase_url': "http://wijzijnjimmys.nl/verhalen/",
            # 'tag_list': "jimmys verhalen"
            # 'genre': 'Electronic',
        }
        # if os.path.isfile(img_file):
        #     track_dict['artwork_data'] = open(img_file, 'rb')
        #
        uploaded_track = self.client.post('/tracks', track=track_dict)
        logger.debug("Uploaded %s to Soundcloud: %s (%s).", path_to_file, uploaded_track.permalink_url, uploaded_track.id)

        # remove .notuploaded file
        not_uploaded_file = os.path.splitext(path_to_file)[0]+".notuploaded"
        os.remove(not_uploaded_file)

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

        # count +=1
        return uploaded_track

    def create_playlist(self, name):
        # TODO: Implement
        # # create an array of track ids
        # tracks = map(lambda id: dict(id=id), [290, 291, 292])
        #
        # # create the playlist
        # client.post('/playlists', playlist={
        #     'title': 'My new album',
        #     'sharing': 'public',
        #     'tracks': tracks
        # })
        pass

    def update_playlist(self, tracklist):
        # TODO: Implement
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
