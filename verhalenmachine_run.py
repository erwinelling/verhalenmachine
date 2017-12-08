#!/usr/bin/python
# -*- coding: latin-1 -*-
import logging
import RPi.GPIO as GPIO
import time
import datetime
from verhalenmachine import VolumioClient, Recorder, Led, Button, KAKU, VU

try:
    player = VolumioClient()
    # client.set_callback(print_state, client)
    # Wait for events from the volumio websocket connection in separate thread
    player.wait()
    # player.set_random()
    player.set_repeat()
    player.create_playlist()

    vu = VU(12) # vu meter for recorder
    recorder = Recorder(vu=vu, player=player)
    button1 = Button(37) # Blue
    button2 = Button(35) # Green
    button3 = Button(33) # Red
    led1 = Led(40) # Blue
    led2 = Led(38) # Green
    led3 = Led(36) # Red
    kaku = KAKU(15,16) # Klik Aan Klik Uit

    # TODO: Clear queue?
    # player.enqueue_playlist()
    while True:
    # TODO: Refactor and use callback functions?

        # Check GPIO for record button events
        if GPIO.event_detected(button3.pin):
            if recorder.is_recording():
                led3.off()
                kaku.off()
                recorder.stop()
            else:
                if player.is_playing():
                    led2.off()
                    player.pause()
                led3.on()
                kaku.on()
                current_datetime = "%s" % (datetime.datetime.now().__format__("%Y-%m-%d_%T"))
                sound_file_name = "%s.wav" % (current_datetime)
                recorder.record(sound_file_name)

        # Check GPIO for play button events
        if GPIO.event_detected(button2.pin):
            if player.is_playing():
                led2.off()
                player.pause()
            else:
                # TODO: Maybe check if default playlist is still playing
                led2.on()
                player.play()

        # Check GPIO for next button events
        if GPIO.event_detected(button1.pin):
            led1.blink()
            if player.is_playing():
                player.pause()
            player.next()
            player.play()

        # Control player led also when play/ stop has been used externally
        if not player.is_playing():
            if led2.burning:
                led2.off()
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
        # pdb.set_trace()

except KeyboardInterrupt:  # If CTRL+C is pressed, exit cleanly:
    GPIO.cleanup()  # cleanup all GPIO
except Exception, e:
    logging.error(e, exc_info=True)
