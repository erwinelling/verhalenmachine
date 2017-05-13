import os
import audioop
import time
import errno
import math
import serial

# https://stackoverflow.com/questions/21762412/mpd-fifo-python-audioop-arduino-and-voltmeter-faking-a-vu-meter
# https://github.com/project-owner/PeppyMeter
# https://volumio.org/forum/volumio-with-mpd-pipe-out-and-brutefir-t3635.html
# https://stackoverflow.com/questions/21762412/mpd-fifo-python-audioop-arduino-and-voltmeter-faking-a-vu-meter


# Open the FIFO that MPD has created for us
# This represents the sample (44100:16:2) that MPD is currently "playing"
fifo = os.open('/tmp/mpd.fifo', os.O_RDONLY)
ser = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1.0)

while 1:
    try:
        rawStream = os.read(fifo, 4096)
    except OSError as err:
        if err.errno == errno.EAGAIN or err.errno == errno.EWOULDBLOCK:
            rawStream = None
        else:
            raise

    if rawStream:
        # TODO: Change to mono signal
        # TODO: Change dB scale to 0-100 scale

            # leftChannel = audioop.tomono(rawStream, 2, 1, 0)
            # rightChannel = audioop.tomono(rawStream, 2, 0, 1)
            stereoPeak = audioop.max(rawStream, 2)
            # leftPeak = audioop.max(leftChannel, 2)
            # rightPeak = audioop.max(rightChannel, 2)
            # leftDB = 20 * math.log10(leftPeak) -74
            # rightDB = 20 * math.log10(rightPeak) -74

            # print(rightPeak, leftPeak, rightDB, leftDB)

            out = stereoPeak/40
            if out > 100:
                out = 100
            if out < 1:
                out = 1
            print out
            ser.write(str(out)+"\r")
            time.sleep(0.05)

# import serial
#
# ser = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1.0)
#
# i=1
# while i<101:
#     ser.write(i)
#     if i == 100:
#         i = 1
#     i = i+1

# TODO: Add output settings to mpd.conf (and restart) as Volumio deletes them when changes occur through the settings UI
# /etc/mpd.conf
#
# audio_output {
# type    "fifo"
# name    "my_fifo"
# path    "/tmp/mpd.fifo"
# format  "44100:16:2"
# }

# e.g.
# echo 'replaygain "album"' >> /etc/mpd.conf
# echo 'replaygain_preamp "0"' >> /etc/mpd.conf
# echo 'replaygain_limit "yes"' >> /etc/mpd.conf
#
# /etc/init.d/mpd restart
