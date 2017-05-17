#!/usr/bin/python
# -*- coding: latin-1 -*-
import logging
import RPi.GPIO as GPIO
import serial
import time
import datetime
from verhalenmachine import Player, Recorder, kaku, Led, Button, Volumeslider

try:
    player = Player()
    player.update_database()
    player.load_playlist()

    recorder = Recorder()

    volumeslider = Volumeslider()
    kaku = kaku()

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
        # Check GPIO for button events
        if GPIO.event_detected(button1.pin):
            if recorder.is_recording():
                recorder.stop()
                # TODO: Maybe control leds totally separate from buttons
                led1.off()
                # kaku.off()
            else:
                if player.is_playing():
                    player.stop()
                current_datetime = "%s" % (datetime.datetime.now().__format__("%Y-%m-%d_%T"))
                sound_file_name = "%s.wav" % (current_datetime)
                recorder.record(sound_file_name)
                led1.on()
                # kaku.on()

        if GPIO.event_detected(button2.pin):
            if player.is_playing():
                player.stop()
                led2.off()
            else:
                player.play()
                led2.on()

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

        # Control recorder led also when recordering has been stopped externally
        if not recorder.is_recording():
            if led1.burning:
                led1.off()
            # if kaku.burning:
                # kaku.off()
                # TODO: implement kaku

        # Read volume slider data from serial port
        new_volume = volumeslider.read_new()
        if new_volume:
            player.set_volume_decimal(float(new_volume))

        time.sleep(0.5)
        # pdb.set_trace()

except KeyboardInterrupt:  # If CTRL+C is pressed, exit cleanly:
    GPIO.cleanup()  # cleanup all GPIO
except Exception, e:
    logging.error(e, exc_info=True)
