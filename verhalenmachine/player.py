import datetime
import logging, logging.handlers
# import mpd
import os
import psutil
import re
import RPi.GPIO as GPIO
# import serial
import signal
import sys
import subprocess
import tempfile
import time
# import pdb
import ConfigParser
import soundcloud
from socketIO_client import SocketIO, LoggingNamespace
import threading
import audioop
import math

import logging
logger = logging.getLogger('root')

HOME_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
config = ConfigParser.ConfigParser()
config.read(os.path.join(HOME_DIR, "verhalenmachine.cfg"))
# TODO: cleanup imports

class VolumioClient:
    """ Class for the websocket client to Volumio """
    """https://github.com/foxey/volumio-buddy/blob/master/volumio_buddy/volumio_buddy.py"""

    def __init__(self, vu):
        HOSTNAME='localhost'
        PORT=3000

        self._callback_function = False
        self._callback_args = False
        self.state = dict()
        self.state["status"] = ""
        self.prev_state = dict()
        self.prev_state["status"] = ""
        self.last_update_time = 0
        self.vu = vu

        self.default_playlist = config.get("recorder", "default_playlist")

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

    def set_volume(self):
        # amixer -c 0 sset PCM,0 96%
        # amixer -c 5 sset Mic,0 91%
        args = [
            'amixer',
            '-c', '0',
            'sset',
            'PCM,0',
            '96%'
        ]
        sub = subprocess.Popen(args)
        # args = [
        #     'arecord',
        #     '-D', self.SOUND_CARD_MIC,
        #     '-f', 'S16_LE',
        #     '-c', '1',
        #     '-r', '44100',
        #     '-V', 'mono',
        #     '--process-id-file', self.RECORDING_PROCESS_ID_FILE,
        #     self.filepath+".temp",
        #     # '2>', os.path.join(HOME_DIR, "vumeter.tmp"),
        # ]
        # sub = subprocess.Popen(args, stderr=output)
        pass

    def set_callback(self, callback_function, *callback_args):
        self._callback_function = callback_function
        self._callback_args = callback_args

    def control_vu(self):
        """
        Meant to run in a parallel thread.
        Will send player output to VU meter.
        """
        self.vu.start()

        #https://rvalbuena.blogspot.com/2014/04/led-vu-meter-using-mypishop-8x8-pimatrix.html
        # # This represents the sample (44100:16:2) that MPD is currently "playing"
        fifo = os.open('/tmp/mpd.fifo', os.O_RDONLY)

        while True:
            try:
                rawStream = os.read(fifo, 4096)
            except OSError as err:
                if err.errno == errno.EAGAIN or err.errno == errno.EWOULDBLOCK:
                    rawStream = None
                else:
                    raise

            # just_after_stream = False
            if rawStream:
                # TODO: Change to mono signal
                # TODO: Change dB scale to 0-100 scale

                leftChannel = audioop.tomono(rawStream, 2, 1, 0)
                rightChannel = audioop.tomono(rawStream, 2, 0, 1)
                stereoPeak = audioop.max(rawStream, 2)
                leftPeak = audioop.max(leftChannel, 2)
                rightPeak = audioop.max(rightChannel, 2)
                leftDB = 20 * math.log10(leftPeak) -74
                rightDB = 20 * math.log10(rightPeak) -74

                # logger.debug("RIGHT %s" % rightDB)
                # print(rightPeak, leftPeak, rightDB, leftDB)
                # out = 20 * math.log10(stereoPeak) -74
                # out = stereoPeak/40
                # if out > 90:
                #     out = 90
                # if out < 10:
                #     out = 0


                out = (rightDB + 20) * (70/23)
                logger.debug("MPD FIFO value %s" % out)

                self.vu.set_percentage(int(out))
                # time.sleep(0.5)
            else:
                self.vu.move_to_percentage(0)
            #     # TODO: Test
            #     # Turn meter down when stream stops
            #     # if just_after_stream:
            #     self.vu.move_to_percentage(0)
            #     self.vu.stop()
            #     # just_after_stream = False

    def start_vu_thread(self):
        t = threading.Thread(target=self.control_vu, args=())
        t.start()

    def play(self):
        self._client.emit('play')

    def pause(self):
        self._client.emit('pause')
        self.vu.move_to_percentage(0)

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

    # def play_playlist(self, name=None):
    #     if name==None:
    #         name=self.default_playlist
    #     self._client.emit('playPlaylist', {'name': name})

    # def add_to_playlist(self, uri, playlist_name=None, service=None):
    #     if playlist_name==None:
    #         playlist_name=self.default_playlist
    #     if service==None:
    #         service="mpd"
    #     # uri: mnt/INTERNAL/verhalenmachine_2017-12-01_20:04:45.wav
    #     self._client.emit('addToPlaylist', {'name': playlist_name, 'service': service, 'uri': uri})

    # def add_to_queue(self, uri):
    #     self._client.emit('addToQueue', {'uri':uri})
    #     self._client.emit('addToQueue', "{uri:%s}" % uri)
    #     self._client.emit('addToQueue', "{'uri':%s}" % uri)
    #     self._client.emit('addToQueue', "{'uri':'%s'}" % uri)
    #     # socketIO.emit('play',{"value":'5'})
    #     self._client.emit('addToQueue', {"uri":uri})
    #     self._client.emit('addToQueue', {"uri":'uri'})
    #     self._client.emit('pushQueue', '[{"uri":"%s","service":"mpd","name":"test.wav","tracknumber":0,"type":"track","trackType":"wav"}]' % uri)

    def add_to_queue_and_playlist(self, uri, sleep=5, update_database=True):
        # self._client.emit('addToQueue') # this triggers a database update?

        # arg = { "uri": uri,
        #         # "service": "mpd",
        #         # "name": "test.wav",
        #         # "tracknumber": 0,
        #         # "type":"track",
        #         # "trackType":"wav"
        #         }
        # self._client.emit('addToQueue', [arg])
        # prefix_filename = config.get("recorder", "prefix_filename")
        # self.PLAYER_DIR = config.get("player", "player_dir")
        # self.playerpath = os.path.join(self.PLAYER_DIR+prefix_filename+uri)
        # uri = self.playerpath
        # self._client.emit('addToQueue', {'uri':uri})
        # self._client.emit('addToQueue', "{uri:%s}" % uri)
        # self._client.emit('addToQueue', "{'uri':%s}" % uri)
        # self._client.emit('addToQueue', "{'uri':'%s'}" % uri)
        # # socketIO.emit('play',{"value":'5'})
        # self._client.emit('addToQueue', {"uri":uri})
        # self._client.emit('addToQueue', {"uri":'uri'})
        time.sleep(sleep)
        self.update_database(uri="INTERNAL")
        time.sleep(sleep)
        # self._client.emit('addToQueue', [arg])
        # time.sleep(5)
        logger.debug("Adding %s to queue" % uri)
        queuearg = { "uri": uri,
                # "service": "mpd",
                # "name": "test.wav",
                # "tracknumber": 0,
                # "type":"track",
                # "trackType":"wav"
        }
        self._client.emit('addToQueue', [queuearg])
        playlistarg = {
                "name": self.default_playlist,
                "service":"mpd",
                "uri": uri
        }
        self._client.emit('addToPlaylist', playlistarg)

        # self._client.emit('pushQueue', '[{"uri":"%s","service":"mpd","name":"test.wav","tracknumber":0,"type":"track","trackType":"wav"}]' % uri)

    def enqueue_playlist(self, name=None):
        if name==None:
            name=self.default_playlist
        self._client.emit('enqueue', {'name': name})

    def empty_queue_and_enqueue_playlist(self, name=None):
        if name==None:
            name=self.default_playlist
        self._client.emit('playPlaylist', {'name': name})
        time.sleep(2)
        self.pause()

    def set_random(self):
        self._client.emit('setRandom', {'value': 'true'})

    def set_repeat(self):
        self._client.emit('setRepeat', {'value': 'true'})

    def is_playing(self):
        if self.state["status"] == "play":
            logger.debug("VOLUMIO IS PLAYING: %s" % self.state["status"])
            return True
        logger.debug("VOLUMIO IS *NOT* PLAYING: %s" % self.state["status"])
        return False

    def update_database(self, uri=[]):
        from mpd import MPDClient
        self.mpdclient = MPDClient()
        self.mpdclient.connect("localhost", 6600)
        self.mpdclient.update([uri])
        self.mpdclient.close()
        self.mpdclient.disconnect()
        logger.debug("Updating MPD %s" %uri)

    def wait(self, **kwargs):
        self.wait_thread = threading.Thread(target=self._wait, args=(kwargs))
        self.wait_thread.start()
        print "started websocket wait thread"
        return self.wait_thread

    def _wait(self, **kwargs):
        while True:
            self._client.wait(kwargs)
            print "websocket wait loop terminated, restarting"
