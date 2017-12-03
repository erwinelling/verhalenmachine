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
import sys
import subprocess
import tempfile
import time
import pdb
import ConfigParser
import soundcloud
from socketIO_client import SocketIO, LoggingNamespace
from threading import Thread
# TODO: Cleanup unnecessary imports or move to functions

HOME_DIR = os.path.dirname(os.path.realpath(__file__))

config = ConfigParser.ConfigParser()
config.read(os.path.join(HOME_DIR, "verhalenmachine.cfg"))


# LOGGING
# TODO: Cleanup logging statements a bit
LOG_FILE = os.path.join(HOME_DIR, "verhalenmachine.log")

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')

fh = logging.handlers.RotatingFileHandler(
              LOG_FILE, maxBytes=5000000, backupCount=5)
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

# class Player:
#     'Player'
#     #TODO: Use this: https://volumio.github.io/docs/API/WebSocket_APIs.html
#     # https://github.com/foxey/volumio-buddy/blob/master/volumio_buddy/volumio_buddy.py
#     def __init__(self):
#         from mpd import MPDClient
#         self.client = MPDClient()
#         self.client.connect("localhost", 6600)
#
#         # TODO: Check whether this works. It seems not.
#         self.client.repeat(1)
#         self.client.random(1)
#
#         # self.min_volume = 10
#         # self.max_volume = 90
#         # self.prev_volume = None
#
#         # Default volume
#         default_volume = config.getint("player", "default_volume")
#         self.client.setvol(default_volume)
#
#     def is_playing(self):
#         status = self.client.status()
#         logger.debug("MPD status: %s" % status)
#         if status.get('state') == "play":
#             return True
#         return False
#
#     def play(self):
#         self.client.play()
#
#     def pause(self):
#         self.client.pause(1)
#
#     def next(self):
#         self.client.next()
#
#     def stop(self):
#         self.client.stop()
#
#     def load_playlist(self):
#         # TODO: Laden van playlist veranderen, zodat dit samenwerkt met Volumio GUI
#         # TODO: Echt een playlist van maken, zelfde naamgeving als bij uploaden
#         self.client.clear()
#         self.client.add('INTERNAL')
#
#     def update_database(self):
#         self.client.update()

class VolumioClient:
    """ Class for the websocket client to Volumio """
    """https://github.com/foxey/volumio-buddy/blob/master/volumio_buddy/volumio_buddy.py"""

    def __init__(self):
        HOSTNAME='localhost'
        PORT=3000

        self._callback_function = False
        self._callback_args = False
        self.state = dict()
        self.state["status"] = ""
        self.prev_state = dict()
        self.prev_state["status"] = ""
        self.last_update_time = 0

        self.default_playlist = config.get("player", "default_playlist")

        def _on_pushState(*args):
            self.state = args[0]
            if self._callback_function:
                # call callback functions with arguments we need
                self._callback_function(*self._callback_args)
            self.prev_state = self.state
            logger.debug("VOLUMIO: %s" % self.state["status"])

        self._client = SocketIO(HOSTNAME, PORT, LoggingNamespace)
        self._client.on('pushState', _on_pushState)
        self._client.emit('getState', _on_pushState)
        self._client.wait_for_callbacks(seconds=1)

    def set_callback(self, callback_function, *callback_args):
        self._callback_function = callback_function
        self._callback_args = callback_args

    def play(self):
        self._client.emit('play')

    def pause(self):
        self._client.emit('pause')

    def toggle_play(self):
        try:
            if self.state["status"] == "play":
                self._client.emit('pause')
            else:
                self._client.emit('play')
        except KeyError:
            self._client.emit('play')

    def volume_up(self):
        self._client.emit('volume', '+')

    def volume_down(self):
        self._client.emit('volume', '-')

    def previous(self):
        self._client.emit('prev')

    def next(self):
        self._client.emit('next')

    def seek(self, seconds):
        self._client.emit('seek', int(seconds))

    def create_playlist(self, name=None):
        if name==None:
            name=self.default_playlist

        self._client.emit('createPlaylist', {'name': name})

    def play_playlist(self, name=None):
        if name==None:
            name=self.default_playlist
        self._client.emit('playPlaylist', {'name': name})

    def add_to_playlist(self, uri, playlist_name=None, service=None):
        if playlist_name==None:
            playlist_name=self.default_playlist
        if service==None:
            service="mpd"
        # uri: mnt/INTERNAL/verhalenmachine_2017-12-01_20:04:45.wav
        self._client.emit('addToPlaylist', {'name': playlist_name, 'service': service, 'uri': uri})

    def set_random(self):
        self._client.emit('setRandom', 'true')

    def set_repeat(self):
        self._client.emit('setRepeat', 'true')

    def is_playing(self):
        if self.state["status"] == "play":
            logger.debug("VOLUMIO IS PLAYING: %s" % self.state["status"])
            return True
        logger.debug("VOLUMIO IS *NOT* PLAYING: %s" % self.state["status"])
        return False

    def wait(self, **kwargs):
        self.wait_thread = Thread(target=self._wait, args=(kwargs))
        self.wait_thread.start()
        print "started websocket wait thread"
        return self.wait_thread

    def _wait(self, **kwargs):
        while True:
            self._client.wait(kwargs)
            print "websocket wait loop terminated, restarting"

class Recorder:
    '''
    Recorder
    arecord -D plughw:CARD=E205U,DEV=0 -f S16_LE -c1 -r 22050 -V mono -v bla.wav
    arecord -D plughw:CARD=Device,DEV=0 -f S16_LE -c1 -r 22050 -V mono -v bla.wav

    arecord -D plughw:CARD=Device,DEV=0 /dev/null 2> ~/vu.txt
    2 staat voor file descriptor 2 (stderr)
    daar komt de error output uit

    '''

    def __init__(self, vu=None):
        # TODO: Throw exception when mic does not exist
        # self.SOUND_CARD_MIC = "plughw:CARD=Device,DEV=0" # USB audio card
        self.SOUND_CARD_MIC = config.get("recorder", "sound_card_mic")
        self.RECORDING_DIR = config.get("recorder", "recording_dir")
        self.RECORDING_PROCESS_ID_FILE = os.path.join(HOME_DIR, "recprocess.pid")
        self.filepath = ""
        self.last_started_recording = 0
        self.vu = vu
        logger.debug("VU: %s" % self.vu)

    def get_pid(self):
        try:
            pidfile = self.RECORDING_PROCESS_ID_FILE
            f = open(pidfile)
            pid = int(f.readline().strip())
            f.close()
            return pid
        except:
            return False

    def is_recording(self):
        time_since_last_started_recording = time.time() - self.last_started_recording
        if psutil.pid_exists(self.get_pid()):
            logger.debug("RECORDING")
            return True
        elif time_since_last_started_recording < 2:
            # Allow for 2 seconds startup time
            # logger.debug("PROBABLY RECORDING")
            return True
        else:
            # logger.debug("NOT RECORDING!")
            return False

    def record_and_control_vu(self, args):
        """
        Meant to run in a parallel thread.
        Will run the recorder and send output to VU meter.
        """
        # : Implement new way to control VU meter
        # https://stackoverflow.com/questions/38374063/python-can-we-use-tempfile-with-subprocess-to-get-non-buffering-live-output-in-p#_=_

        # the temp file will be automatically cleaned up using context manager
        with tempfile.TemporaryFile() as output:
            sub = subprocess.Popen(args, stderr=output)
            # sub.poll returns None until the subprocess ends,
            # it will then return the exit code, hopefully 0 ;)
            self.vu.start()
            while sub.poll() is None:
                where = output.tell()
                lines = output.read()
                if not lines:
                    # Adjust the sleep interval to your needs
                    time.sleep(0.1)
                    # make sure pointing to the last place we read
                    output.seek(where)
                else:
                    # Try to parse percentages from output
                    possible_vu_percentage = lines[-3:-1].lstrip("0")
                    if possible_vu_percentage.isdigit() and possible_vu_percentage!="0":
                        logger.debug("VU: %s" % possible_vu_percentage)
                        self.vu.set_percentage(possible_vu_percentage)

                    # sys.__stdout__.write(lines)
                    sys.__stdout__.flush()
                    time.sleep(0.1)
            # A last write needed after subprocess ends
            sys.__stdout__.write(output.read())
            sys.__stdout__.flush()

    def record(self, filename):
        # arecord -D plughw:CARD=E205U,DEV=0 -V mono -r 44100 -c 1 -f s16_LE vutest.wav

        self.last_started_recording = time.time()
        prefix_filename = config.get("recorder", "prefix_filename")
        self.filepath = os.path.join(self.RECORDING_DIR+prefix_filename+filename)
        args = [
            'arecord',
            '-D', self.SOUND_CARD_MIC,
            '-f', 'S16_LE',
            '-c', '1',
            '-r', '44100',
            '-V', 'mono',
            '--process-id-file', self.RECORDING_PROCESS_ID_FILE,
            self.filepath+".temp",
            # '2>', os.path.join(HOME_DIR, "vumeter.tmp"),
        ]
        logger.debug(args)

        t = Thread(target=self.record_and_control_vu, args=(args,))
        t.start()
        logger.debug("STARTED RECORDING THREAD")

    def remove_temp_ext(self):
        # remove .temp extension files
        for root, dirs, files in os.walk(self.RECORDING_DIR):
            for filename in files:
                if os.path.splitext(filename)[1] == ".temp":
                    path_to_file = os.path.join(root, filename)
                    os.rename(path_to_file, os.path.splitext(path_to_file)[0])
                    logger.debug("Renamed temp file to %s", os.path.splitext(path_to_file)[0])

    def add_not_uploaded_file(self):
        if self.filepath:
            not_uploaded_file = os.path.splitext(self.filepath)[0] + ".notuploaded"
            f = open(not_uploaded_file, 'w')
            f.close()

    def stop(self):
        pid = self.get_pid()
        if pid:
            logger.debug("Stopping recording process by killing PID %s", str(pid))
            os.kill(pid, signal.SIGINT)
        self.vu.stop()
        self.remove_temp_ext()
        self.add_not_uploaded_file()

        # TODO: Aan playlist toevoegen?

    def dontrecordfortoolong(self):
        """
        Meant to run as cronjob.
        """
        logger.debug("DO NOT RECORD FOR TOO LONG")
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


class VU:
    def __init__(self, pin):
        # Pin Setup:
        self.pin = pin

        # Initiate VU
        GPIO.setmode(GPIO.BOARD)  # Broadcom pin-numbering scheme
        GPIO.setup(self.pin, GPIO.OUT)
        self.vumax = 70
        self.p = GPIO.PWM(12, 50)  # channel=12 frequency=50Hz
        self.test()

    def test(self):
        self.start()
        for dc in range(0, self.vumax+1, 5):
            self.set_value(dc)
            time.sleep(0.05)
        for dc in range(self.vumax, -1, -5):
            self.set_value(dc)
            time.sleep(0.05)
        self.stop()

    def set_value(self, value):
        """
        Needs to have an open connection to work (vu.start)
        TODO: Move gradually, maybe in steps of 5? Also depending on number of reads of output
        """
        if value > self.vumax:
            value = vumax
        if value < 0:
            value = 0

        self.p.ChangeDutyCycle(value)
        self.current_value = value
        logger.debug("VU current value: %s" % value)

    def set_percentage(self, percentage):
        new_value = (int(percentage)*self.vumax)/100
        self.set_value(new_value)

    def move_to_value(self, value):
        # TODO: Move gradually
        pass

    def start(self):
        self.p.start(0)

    def stop(self):
        self.p.stop()

class Led:
    '''
    LED
    '''
    def __init__(self, pin):
        # Pin Setup:
        self.pin = pin

        # Initiate LED
        GPIO.setmode(GPIO.BOARD)  # Broadcom pin-numbering scheme
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

class KAKU:
    '''
    Klik Aan Klik Uit
    TODO: TEST!
    '''
    def __init__(self, pin1, pin2):
        # Pin Setup:
        self.pin1 = pin1
        self.pin2 = pin2

        # Initiate KAKU
        GPIO.setmode(GPIO.BOARD)  # Broadcom pin-numbering scheme
        GPIO.setup(self.pin1, GPIO.OUT)
        GPIO.setup(self.pin2, GPIO.OUT)
        self.burning = False
        self.blink(times=1, sleep=2)

    def on(self):
        GPIO.output(self.pin1, GPIO.HIGH)
        GPIO.output(self.pin2, GPIO.LOW)
        self.burning = True
        logger.debug("KAKU (pins %s and %s) ON." % (self.pin1, self.pin2))

    def off(self):
        GPIO.output(self.pin1, GPIO.LOW)
        GPIO.output(self.pin2, GPIO.HIGH)
        self.burning = False
        logger.debug("KAKU (pins %s and %s) OFF." % (self.pin1, self.pin2))

    def blink(self, times=1, sleep=0.5):
        count = 0
        while count<times:
            self.on()
            time.sleep(sleep)
            self.off()
            if count<times-1:
                time.sleep(sleep)
            count = count+1


class Button:
    def __init__(self, pin):
        # Pin Setup:
        self.pin = pin

        # Initiate button as input w/ pull-up
        GPIO.setmode(GPIO.BOARD)  # Broadcom pin-numbering scheme
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.pin, GPIO.FALLING, bouncetime=200)

class Uploader:
    # TODO: Maybe implement uploading to several playlists again (settings or ip or wlan name or ...)
    # TODO: Upload to playlist
    def __init__(self):
        # self.client = soundcloud.Client(client_id="2afa000b9c16670dd62c83700567487f", client_secret="dbf7e4b8b8140f142b62c8e93b4d0ab8", username="erwin@uptous.nl", password="ell82SOU!")
        self.client = soundcloud.Client(
            client_id = config.get("uploader", "client_id"),
            client_secret = config.get("uploader", "client_secret"),
            username = config.get("uploader", "username"),
            password = config.get("uploader", "password"),
        )
        logger.debug("SOUNDCLOUD connected to %s " % self.client.get('/me').username)

        self.RECORDING_DIR = config.get("uploader", "recording_dir")

    def clean_directory(self, directory=""):
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
        count = 0 # TODO: Remove and just us uploaded_track_list.length()
        uploaded_track_list=[]
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
                        uploaded_track = self.upload_track(path_to_file)
                        count = count+1

                        # TODO: Keep list of uploaded tracks
                        # uploaded_track_list.append(uploaded_track.id)

        # TODO: Create or appenn to playlist
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
        #     'title': name,
        #     'sharing': 'public',
        #     'tracks': tracks
        # })
        ## return created_playlist
        pass

    def update_playlist(self, tracklist):
        # TODO: Implement
        # playlist = client.get("/playlists/"+set_id)
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
        ## return updated_playlist
        pass
