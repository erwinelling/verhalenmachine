#!/usr/bin/python
# -*- coding: latin-1 -*-
import logging
import RPi.GPIO as GPIO
import time
import datetime
from verhalenmachine import Player, Recorder, Led, Button, KAKU

try:
    player = Player()
    player.update_database()
    player.load_playlist()

    recorder = Recorder()

    GPIO.cleanup()
    GPIO.setmode(GPIO.BOARD)  # Broadcom pin-numbering scheme
    button1 = Button(37) # Blue
    button2 = Button(35) # Green
    button3 = Button(33) # Red
    led1 = Led(40) # Blue
    led2 = Led(38) # Green
    led3 = Led(36) # Red
    kaku = KAKU(15,16) # Klik Aan Klik Uit

    while True:
    # TODO: Maybe control leds totally separate from buttons

        # Check GPIO for record button events
        if GPIO.event_detected(button1.pin):
            if recorder.is_recording():
                recorder.stop()
                led1.off()
                kaku.off()
            else:
                if player.is_playing():
                    player.stop()
                    led2.off()
                current_datetime = "%s" % (datetime.datetime.now().__format__("%Y-%m-%d_%T"))
                sound_file_name = "%s.wav" % (current_datetime)
                recorder.record(sound_file_name)
                led1.on()
                kaku.on()

        # Check GPIO for play button events
        if GPIO.event_detected(button2.pin):
            if player.is_playing():
                player.stop()
                led2.off()
            else:
                player.play()
                led2.on()

        # Check GPIO for next button events
        if GPIO.event_detected(button3.pin):
            if not player.is_playing():
                player.play()
                led2.on()
            player.next()
            led3.blink()

        # Control player led also when play/ stop has been used externally
        if not player.is_playing():
            if led2.burning:
                led2.off()
        else:
            if not led2.burning:
                led2.on()

        # Control recorder led & VU & KAKU also when recorder has been stopped externally
        if not recorder.is_recording():
            if led1.burning:
                led1.off()
                # recorder.stop_vu()
                kaku.off()

        time.sleep(0.5)
        # pdb.set_trace()

except KeyboardInterrupt:  # If CTRL+C is pressed, exit cleanly:
    GPIO.cleanup()  # cleanup all GPIO
except Exception, e:
    logging.error(e, exc_info=True)
