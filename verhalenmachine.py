#!/usr/bin/python
# -*- coding: latin-1 -*-
import datetime
import logging, logging.handlers
import mpd
import os
import re
import RPi.GPIO as GPIO
import serial
import signal
import subprocess
import time


# TODO: Add configfile

# python-mpd2asdf


# from mpd import MPDClient
# client = MPDClient()
# # #to connect to MPD you need to know the IP address and port
# client.connect("localhost", 6600)

# #set the volume between 0 and 100
# client.setvol(100)
#
# #play song at certain position
# client.play(1)
#
# #pause and resume playback
# client.pause(0)
# client.pause(1)
#
# #skip to the next or previous track
# client.next()
# client.previous()
#
# #clear current playlist and load a new one
# client.playlistclear()
# client.load("nameofyourplaylist")


# class Employee:
#    'Common base class for all employees'
#    empCount = 0
#
#    def __init__(self, name, salary):
#       self.name = name
#       self.salary = salary
#       Employee.empCount += 1
#
#    def displayCount(self):
#      print "Total Employee %d" % Employee.empCount
#
#    def displayEmployee(self):
#       print "Name : ", self.name,  ", Salary: ", self.salary

HOME_DIR = os.path.dirname(os.path.realpath(__file__))

# LOGGING
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

    # TODO: Load local playlist
    # TODO: Set volume max and min

    def __init__(self):
        # pass
        from mpd import MPDClient
        self.client = MPDClient()
        self.client.connect("localhost", 6600)

        # TODO: Check whether this works
        self.client.repeat(1)
        self.client.random(1)

        # self.playing = False
        self.prev_volume = None

    # def is_playing(self):
    #     pass
    #
    # def is_paused(self):
    #     pass

    def play(self):
        # TODO: RESEARCH: how to control VU meter with audio input
        self.client.play()

    def pause(self):
        self.client.pause(1)

    def next(self):
        self.client.next()

    def stop(self):
        self.client.stop()

    def set_volume(self, new_volume):
        if new_volume != self.prev_volume:
            # if new_volume > 100:
            #     new_volume = 100
            # if new_volume < 0:
            #     new_volume = 0
            logger.debug("Changing volume from %s to %s" % (self.prev_volume, new_volume))
            self.client.setvol(new_volume)
            self.prev_volume = new_volume

    def set_volume_decimal(self, volume_decimal):
        self.set_volume(int(volume_decimal*100))

    def get_volume(self):
        return int(self.client.status().get('volume'))

    # def volume_change(self, increase=10):
    #     current_volume = int(client.status().get('volume'))
    #     new_volume = current_volume+increase
    #     if new_volume > 100:
    #         new_volume = 100
    #     if new_volume < 0:
    #         new_volume = 0
    #     self.set_volume(new_volume)

    def load_playlist(self):
        #TODO: Load playlist
        pass

    # def update_playlist(self):
    #     pass

class Recorder:
    'Recorder'
    recording = False
    last_recording_starttime = ""

    # TODO: Implement recording

    def __init__(self):
        self.SOUND_CARD_MIC = "plughw:CARD=Device,DEV=0"
        self.RECORDING_DIR = "/data/INTERNAL/"
        self.RECORDING_PROCESS_ID_FILE = "recprocess.pid"

    # def is_recording(self):
    #     pass

    def record(self, filename):
    # RESEARCH: how to control VU meter with mic input
        filepath = os.path.join(self.RECORDING_DIR+filename)
        args = [
            'arecord',
            '-D', self.SOUND_CARD_MIC,
            '-f', 'S16_LE',
            '-c1',
            '-r22050',
            '-V', 'mono',
            '--process-id-file', self.RECORDING_PROCESS_ID_FILE,
            filepath+".temp"
        ]
        logger.debug(args)
        proc = subprocess.Popen(args)

    def remove_temp_ext(self):
        #remove .temp extension files
        for root, dirs, files in os.walk(self.RECORDING_DIR):
            for filename in files:
                if os.path.splitext(filename)[1] == ".temp":
                    path_to_file = os.path.join(root, filename)
                    os.rename(path_to_file, os.path.splitext(path_to_file)[0])
                    logger.debug("Renamed temp file to %s", os.path.splitext(path_to_file)[0])


    def stop(self):
        pidfile = os.path.join(HOME_DIR, self.RECORDING_PROCESS_ID_FILE)
        f = open(pidfile)
        pid = int(f.readline().strip())
        f.close()
        logger.debug("Stopping recording process by killing PID %s", str(pid))
        os.kill(pid, signal.SIGINT)
        self.remove_temp_ext()

# class Buttons:
#     #TODO: set button numbers?
#     #TODO: save button state
#     #TODO: control lights
#
#     def __init__(self):
#         # Pin Setup:
#         GPIO.cleanup()
#         GPIO.setmode(GPIO.BOARD)  # Broadcom pin-numbering scheme
#         self.LED1PIN = 35
#         self.BUT1PIN = 38
#         self.BUT2PIN = 37
#         self.BUT3PIN = 36
#         self.BUT4PIN = 32
#         self.BUT5PIN = 31
#         self.BUT6PIN = 33
#
#         # Initiate LEDs:
#         if self.LED1PIN:
#             GPIO.setup(self.LED1PIN, GPIO.OUT)
#             GPIO.output(self.LED1PIN, GPIO.LOW)
#
#         # Initiate buttons:
#         if self.BUT1PIN:
#             # Button pin set as input w/ pull-up
#             GPIO.setup(self.BUT1PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#             GPIO.add_event_detect(self.BUT1PIN, GPIO.FALLING, bouncetime=200)
#         if self.BUT2PIN:
#             # Button pin set as input w/ pull-up
#             GPIO.setup(self.BUT2PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#             GPIO.add_event_detect(self.BUT2PIN, GPIO.FALLING, bouncetime=200)
#         if self.BUT3PIN:
#             # Button pin set as input w/ pull-up
#             GPIO.setup(self.BUT3PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#             GPIO.add_event_detect(self.BUT3PIN, GPIO.FALLING, bouncetime=200)
#         if self.BUT4PIN:
#             # Button pin set as input w/ pull-up
#             GPIO.setup(self.BUT4PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#             GPIO.add_event_detect(self.BUT4PIN, GPIO.FALLING, bouncetime=200)
#         if self.BUT5PIN:
#             # Button pin set as input w/ pull-up
#             GPIO.setup(self.BUT5PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#             GPIO.add_event_detect(self.BUT5PIN, GPIO.FALLING, bouncetime=200)
#         if self.BUT6PIN:
#             # Button pin set as input w/ pull-up
#             GPIO.setup(self.BUT6PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#             GPIO.add_event_detect(self.BUT6PIN, GPIO.FALLING, bouncetime=200)
#
#     def check_pressed(self, number):
#         pass
#
#     def turn_light_on(self, number):
#         pass
#
#     def turn_light_off(self, number):
#         pass

class Led:
    'LED'
    # TODO: Test!
    def __init__(self, pin):
        # Pin Setup:
        self.pin = pin

        # Initiate LED
        GPIO.setup(self.pin, GPIO.OUT)
        GPIO.output(self.pin, GPIO.LOW)

    def on(self):
        GPIO.output(self.pin, GPIO.HIGH)
        logger.debug("LED (pin %s) ON." % self.pin)

    def off(self):
        GPIO.output(self.pin, GPIO.LOW)
        logger.debug("LED (pin %s) OFF." % self.pin)

    def blink(self, times=1, sleep=0.5):
        self.on()
        time.sleep(sleep)
        self.off()

class Button:
    def __init__(self, pin):
        # Pin Setup:
        self.pin = pin
        self.pressed = False

        # Initiate button as input w/ pull-up
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.pin, GPIO.FALLING, bouncetime=200)


class Cleaner:
    # TODO: Implement cleaning
    def __init__(self):
        pass

    # what needs to be cleaned:
    # skip 0 byte wave files
    # Fixen als hij te lang opneemt wav-01, wav-02, wav-03
    # Te grote bestanden verwijderen apparaat
    # Opname stoppen na een uur?
    # Te grote files negeren

class Uploader:
    # TODO: Implement uploading
    def __init__(self):
        #     self.client = soundcloud.Client(
        #     # TODO: try to get this to work with just a secret key
        #     # TODO: add config
        #     self.client_id = config.get("upload", "client_id"),
        #     self.client_secret = config.get("upload", "client_secret"),
        #     self.username = config.get("upload", "username"),
        #     self.password = config.get("upload", "password"),
        # )
        pass

    def check_files_to_upload(self):
        # walk through all files in recording directory
        # logger.debug("Checking contents of %s", RECORDING_DIR)
        # from os.path import join, getsize
        # count = 0
        # # TODO: Replace with counter object
        # uploaded_track = False
        # for root, dirs, files in os.walk(RECORDING_DIR):
        #     for filename in files:
        #         # check whether it is a music file that can be uploaded to soundcloud
        #         # http://uploadandmanage.help.soundcloud.com/customer/portal/articles/2162441-uploading-requirements
        #         # AIFF, WAVE (WAV), FLAC, ALAC, OGG, MP2, MP3, AAC, AMR, and WMA
        #         # and ignore hidden files
        #         if filename.lower().endswith(('.aiff', '.wav', '.flac', '.alac', '.ogg', '.mp2', '.mp3', '.aac', '.amr', '.wma')) and not filename.startswith('.'):
        #             path_to_file = os.path.join(root, filename)
        #
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


# Serial port stuff
# def readlineCR(port):
#     rv = ""
#     while True:
#         ch = port.read()
#         rv += ch
#         if ch=='\r' or ch=='':
#             return rv

try:
    player = Player()
    recorder = Recorder()
    # buttons = Buttons()

    GPIO.cleanup()
    GPIO.setmode(GPIO.BOARD)  # Broadcom pin-numbering scheme
    button1 = Button(40)
    button2 = Button(38)
    button3 = Button(36)
    # led1 = Led(26)
    # led2 = Led(24)
    # led3 = Led(22)
    ser = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1.0)
    prev_input = None
    while True:
        if GPIO.event_detected(button1.pin):
            current_datetime = "%s" % (datetime.datetime.now().__format__("%Y-%m-%d_%T"))
            sound_file_name = "%s.wav" % (current_datetime)
            recorder.record(sound_file_name)
            # TODO: ADD PAUSE
            # TODO: ADD LED CONTROL
        if GPIO.event_detected(button2.pin):
            player.play()
            # TODO: ADD STOP
            # TODO: ADD LED CONTROL
        if GPIO.event_detected(button3.pin):
            player.next()
            # TODO: ADD LED CONTROL

        # if buttons.BUT1PIN and GPIO.event_detected(button1.[BUT1PIN]):
        #         # button_rec()
        #         current_datetime = "%s" % (datetime.datetime.now().__format__("%Y-%m-%d_%T"))
        #         sound_file_name = "%s.wav" % (current_datetime)
        #         recorder.record(sound_file_name)
        # if buttons.BUT2PIN and GPIO.event_detected(buttons.BUT2PIN):
        #         # button_prev()
        #         recorder.stop()
        # if buttons.BUT3PIN and GPIO.event_detected(buttons.BUT3PIN):
        #         # button_next()
        #         player.next()
        # if buttons.BUT4PIN and GPIO.event_detected(buttons.BUT4PIN):
        #         # button_stop()
        #         player.stop()
        # if buttons.BUT5PIN and GPIO.event_detected(buttons.BUT5PIN):
        #         # button_play()
        #         player.play()
        # if buttons.BUT6PIN and GPIO.event_detected(buttons.BUT6PIN):
        #         # button_pause()
        #         player.pause()

        # Read volume slider data
        ser.flushInput()
        ser_input = ser.readline()
        ser_decimals = re.findall("\d+\.\d+", ser_input)
        if len(ser_decimals) == 1 and ser_input != prev_input:
            player.set_volume_decimal(float(ser_input))
            prev_input = ser_input


        # TODO: PARALLEL PROCESS FOR VU METER
        # SEND BETWEEN 1 and 100 to serial port:
        # ser = serial.Serial("/dev/ttyAMA0", baudrate=57600, timeout=1.0)
        # python -m serial.tools.miniterm /dev/ttyUSB0 -b 57600
        # ser.write('50')

        # TODO:

        time.sleep(0.1)

except KeyboardInterrupt:  # If CTRL+C is pressed, exit cleanly:
    GPIO.cleanup()  # cleanup all GPIO
except Exception, e:
    logging.error(e, exc_info=True)
