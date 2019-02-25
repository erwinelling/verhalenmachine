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
from threading import Thread

# TODO: cleanup imports

class Recorder:
    '''
    Recorder
    arecord -D plughw:CARD=E205U,DEV=0 -f S16_LE -c1 -r 22050 -V mono -v bla.wav
    arecord -D plughw:CARD=Device,DEV=0 -f S16_LE -c1 -r 22050 -V mono -v bla.wav

    arecord -D plughw:CARD=Device,DEV=0 /dev/null 2> ~/vu.txt
    2 staat voor file descriptor 2 (stderr)
    daar komt de error output uit

    '''

    def __init__(self, vu, player):
        # TODO: Throw exception when mic does not exist
        # self.SOUND_CARD_MIC = "plughw:CARD=Device,DEV=0" # USB audio card
        self.SOUND_CARD_MIC = config.get("recorder", "sound_card_mic")
        self.RECORDING_DIR = config.get("recorder", "recording_dir")
        self.PLAYER_DIR = config.get("player", "player_dir")
        self.RECORDING_PROCESS_ID_FILE = os.path.join(HOME_DIR, "recprocess.pid")
        self.filepath = "" #TODO: Refactor into something better than this variable
        self.playerpath = "" #TODO: Refactor into something better than this variable
        self.last_started_recording = 0
        self.vu = vu
        self.player = player
        logger.debug("VU: %s" % self.vu)

    def set_volume(self):
        # amixer -c 0 sset PCM,0 96%
        # amixer -c 5 sset Mic,0 91%
        args = [
            'amixer',
            '-c', '5',
            'sset',
            'Mic,0',
            '90%'
        ]
        sub = subprocess.Popen(args)


        # Gets a list of simple mixer controls
        # $ amixer scontrols
        # Then set it to the desired volume, as an example
        #
        # $ amixer sset 'Master' 50%
        pass

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
                    time.sleep(0.05)
                    # make sure pointing to the last place we read
                    output.seek(where)
                else:
                    # Try to parse percentages from output
                    possible_vu_percentage = lines[-3:-1].lstrip("0")
                    if possible_vu_percentage.isdigit() and possible_vu_percentage!="0":
                        logger.debug("VU: %s" % possible_vu_percentage)
                        self.vu.move_to_percentage(int(possible_vu_percentage))

                    # sys.__stdout__.write(lines)
                    sys.__stdout__.flush()
                    time.sleep(0.05)
            # A last write needed after subprocess ends
            sys.__stdout__.write(output.read())
            sys.__stdout__.flush()

    def record(self, filename):
        # arecord -D plughw:CARD=E205U,DEV=0 -V mono -r 44100 -c 1 -f s16_LE vutest.wav

        self.last_started_recording = time.time()
        prefix_filename = config.get("recorder", "prefix_filename")
        self.filepath = os.path.join(self.RECORDING_DIR+prefix_filename+filename)
        self.playerpath = os.path.join(self.PLAYER_DIR+prefix_filename+filename)
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
        logger.debug("Current file %s", self.filepath)
        # time.sleep(5) #wait for update to complete
        # args = {
        # uri=self.playerpath)
        t = Thread(target=self.player.add_to_queue_and_playlist, args=(self.playerpath, 5,))
        t.start()

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
