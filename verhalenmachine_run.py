#!/usr/bin/python
# -*- coding: latin-1 -*-
import RPi.GPIO as GPIO
import time
import datetime
import os
from verhalenmachine.log import setup_custom_logger
# from verhalenmachine.verhalenmachine import VolumioClient, Recorder
from verhalenmachine.player import VolumioClient
from verhalenmachine.recorder import Recorder
from verhalenmachine.button import Button
from verhalenmachine.led import Led
from verhalenmachine.kaku import KAKU
from verhalenmachine.vu import VU

logger = setup_custom_logger('root')
GPIO.setwarnings(False)
# import ConfigParser

try:
    # Check mic
    # mic=0
    # while mic==0:
    #     import re
    #     import subprocess
    #     device_re = re.compile("Bus\s+(?P<bus>\d+)\s+Device\s+(?P<device>\d+).+ID\s(?P<id>\w+:\w+)\s(?P<tag>.+)$", re.I)
    #     df = subprocess.check_output("lsusb")
    #     devices = []
    #     for i in df.split('\n'):
    #         if i:
    #             info = device_re.match(i)
    #             if info:
    #                 dinfo = info.groupdict()
    #                 dinfo['device'] = '/dev/bus/usb/%s/%s' % (dinfo.pop('bus'), dinfo.pop('device'))
    #                 devices.append(dinfo)
    #     print devices
    #     # check device mic
    #     # tag is ' '
    #     # blink the record light
    #     mic=1

    vu_play = VU(33) # vu meter for player
    player = VolumioClient(vu=vu_play)

    # TODO: Set volume for mic and headphones
    # https://unix.stackexchange.com/questions/32206/set-volume-from-terminal

    # client.set_callback(print_state, client)
    player.set_random()
    player.set_repeat()
    player.create_playlist()
    player.set_volume()

    # Wait for events from the volumio websocket connection in separate thread
    player.wait()

    player.start_vu_thread()

    # TODO: Clear queue?
    # https://volumio.org/forum/empty-the-play-queue-via-websocket-t9216.html#p45800
    # player.enqueue_playlist()
    # TODO: TEST whether queue is cleared
    # player.empty_queue_and_enqueue_playlist()

    # Set input and output
    vu_rec = VU(12) # vu meter for recorder
    recorder = Recorder(vu=vu_rec, player=player)
    recorder.set_volume()
    button1 = Button(37, 2000) # Blue
    button2 = Button(35, 2000) # Green
    button3 = Button(31, 2000) # Red
    led1 = Led(40) # Blue
    led2 = Led(38) # Green
    led3 = Led(36) # Red
    kaku = KAKU(15,16) # Klik Aan Klik Uit

    while True:
        # TODO: Refactor and use callback functions?

        # Check GPIO for record button events
        if GPIO.event_detected(button3.pin):
            if recorder.is_recording():
                led3.off()
                recorder.stop()
                kaku.off()
            else:
                if player.is_playing():
                    led2.off()
                    player.pause()
                kaku.on()
                time.sleep(0.5) # to prevent crackling from kaku
                led3.on()
                current_datetime = "%s" % (datetime.datetime.now().__format__("%Y-%m-%d_%T"))
                sound_file_name = "%s.wav" % (current_datetime)
                recorder.record(sound_file_name)

        # Check GPIO for play button events
        if GPIO.event_detected(button2.pin):
            if player.is_playing():
                led2.off()
                player.pause()
            else:
                if recorder.is_recording():
                    logging.debug("Opnemen en play")
                    recorder.stop()
                    led3.off()
                    kaku.off()
                led2.on()
                player.play()

        # Check GPIO for next button events
        if GPIO.event_detected(button1.pin):
            if recorder.is_recording():
                recorder.stop()
                led3.off()
                kaku.off()
            else:
                led1.blink(times=1, sleep=1)
                # if player.is_playing():
                #     player.pause()
                player.next()


        # Control player led also when play/ stop has been used externally
        if not player.is_playing():
            if led2.burning:
                led2.off()
                player.vu.move_to_percentage(0)
        else:
            if not led2.burning:
                led2.on()

        # Control recorder led & VU & KAKU also when recorder has been stopped externally
        if not recorder.is_recording():
            if led3.burning:
                led3.off()
                vu.stop()
                kaku.off()
        time.sleep(0.5)

except KeyboardInterrupt:  # If CTRL+C is pressed, exit cleanly:
    GPIO.cleanup()  # cleanup all GPIO
except Exception, e:
    logger.error(e, exc_info=True)
