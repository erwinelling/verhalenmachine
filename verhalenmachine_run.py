#!/usr/bin/python
# -*- coding: latin-1 -*-
import logging
import RPi.GPIO as GPIO
import time
import datetime
from verhalenmachine import VolumioClient, Recorder, Led, Button, KAKU, VU

try:
    player = VolumioClient()
    # TODO: Set volume for mic and headphones
    # https://unix.stackexchange.com/questions/32206/set-volume-from-terminal

    # client.set_callback(print_state, client)
    # Wait for events from the volumio websocket connection in separate thread
    player.wait()
    player.set_random()
    player.set_repeat()
    player.create_playlist()
    player.set_volume()

    # TODO: Clear queue?
    # https://volumio.org/forum/empty-the-play-queue-via-websocket-t9216.html#p45800
    # player.enqueue_playlist()
    # TODO: TEST whether queue is cleared
    player.empty_queue_and_enqueue_playlist()

    vu = VU(12) # vu meter for recorder
    recorder = Recorder(vu=vu, player=player)
    recorder.set_volume()
    
    button1 = Button(37, 200) # Blue
    button2 = Button(35, 1000) # Green
    button3 = Button(33, 2000) # Red
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
                # player.add_to_queue("2018-02-12_09:46:19.wav") #plus player path plus prefix
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
                if recorder.is_recording():
                    logging.debug("Opnemen en play")
                    led3.off()
                    kaku.off()
                    recorder.stop()
                led2.on()
                player.play()

        # Check GPIO for next button events
        if GPIO.event_detected(button1.pin):
            if recorder.is_recording():
                led3.off()
                kaku.off()
                recorder.stop()
            else:
                led1.blink()
                # if player.is_playing():
                #     player.pause()
                player.next()

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

        time.sleep(0.6)

except KeyboardInterrupt:  # If CTRL+C is pressed, exit cleanly:
    GPIO.cleanup()  # cleanup all GPIO
except Exception, e:
    logging.error(e, exc_info=True)
