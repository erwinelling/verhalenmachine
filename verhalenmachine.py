#!/usr/bin/python
# -*- coding: latin-1 -*-
import logging, logging.handlers
import mpd
import os
import RPi.GPIO as GPIO
import time

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
    # empCount = 0
    playing = False

    def __init__(self):
        # pass
        from mpd import MPDClient
        self.client = MPDClient()
        self.client.connect("localhost", 6600)

        # TODO: Check whether this works
        self.client.repeat(1)
        self.client.random(1)

    # def is_playing(self):
    #     pass
    #
    # def is_paused(self):
    #     pass

    def play(self):
        # RESEARCH: how to control meter with audio input
        self.client.play()

    def pause(self):
        self.client.pause(1)

    def next(self):
        self.client.next()

    def stop(self):
        self.client.stop()

    def set_volume(self, volume):
        self.client.setvol(volume)

    def volume_change(self, increase=10):
        current_volume = int(client.status().get('volume'))
        new_volume = current_volume+increase
        if new_volume > 100:
            new_volume = 100
        if new_volume < 0:
            new_volume = 0
        self.set_volume(new_volume)

    def load_playlist(self):
        pass

    # def update_playlist(self):
    #     pass

class Recorder:
    'Recorder'
    recording = False
    last_recording_starttime = ""

    def __init__(self):
        pass

    # def is_recording(self):
    #     pass

    def record(self):
    # RESEARCH: how to control meter with mic input
        pass

    def stop(self):
        pass

class Buttons:
    #TODO: set button numbers?

    def __init__(self):
        pass

    def check_pressed(self, number):
        pass

    def turn_light_on(self, number):
        pass

    def turn_light_off(self, number):
        pass

class Cleaner:
    def __init__(self):
        pass

    # what needs to be cleaned:
    # skip 0 byte wave files
    # Fixen als hij te lang opneemt wav-01, wav-02, wav-03
    # Te grote bestanden verwijderen apparaat
    # Opname stoppen na een uur?
    # Te grote files negeren

class Uploader:
    def __init__(self):
        pass

    def check_files_to_upload(self):
        pass

    def upload_track(self, track):
        pass

    def upload_tracklist(self, tracklist):
        pass

try:
    player = Player()
    recorder = Recorder()

    player.play()


    while True:

        # if BUT1PIN and GPIO.event_detected(BUT1PIN):
        #         button_rec()
        # if BUT2PIN and GPIO.event_detected(BUT2PIN):
        #         button_prev()
        # if BUT3PIN and GPIO.event_detected(BUT3PIN):
        #         button_next()
        # if BUT4PIN and GPIO.event_detected(BUT4PIN):
        #         button_stop()
        # if BUT5PIN and GPIO.event_detected(BUT5PIN):
        #         button_play()
        # if BUT6PIN and GPIO.event_detected(BUT6PIN):
        #         button_pause()

        time.sleep(0.5)

except KeyboardInterrupt:  # If CTRL+C is pressed, exit cleanly:
    pass
    # GPIO.cleanup()  # cleanup all GPIO
except Exception, e:
    raise
    # logging.error(e, exc_info=True)
