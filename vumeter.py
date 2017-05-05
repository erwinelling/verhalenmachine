import serial

ser = serial.Serial("/dev/ttyUSB0", baudrate=57600, timeout=1.0)

i=1
while i<101:
    ser.write(i)
    if i == 100:
        i = 1
    i = i+1
