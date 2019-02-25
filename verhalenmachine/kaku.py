import RPi.GPIO as GPIO
import time
import logging
logger = logging.getLogger('root')

class KAKU:
    '''
    Klik Aan Klik Uit
    TODO: TEST!
    '''
    def __init__(self, pin1, pin2):
        # Pin Setup:
        self.pin1 = pin1
        self.pin2 = pin2

        # Initiate KAKU
        GPIO.setmode(GPIO.BOARD)  # Broadcom pin-numbering scheme
        GPIO.setup(self.pin1, GPIO.OUT)
        GPIO.setup(self.pin2, GPIO.OUT)
        self.burning = False
        self.blink(times=1, sleep=0.5)

    def on(self):
        GPIO.output(self.pin1, GPIO.HIGH)
        GPIO.output(self.pin2, GPIO.LOW)
        time.sleep(0.05)
        GPIO.output(self.pin1, GPIO.LOW)
        self.burning = True
        logger.debug("KAKU (pins %s and %s): ON" % (self.pin1, self.pin2))

    def off(self):
        GPIO.output(self.pin1, GPIO.LOW)
        GPIO.output(self.pin2, GPIO.HIGH)
        time.sleep(0.05)
        GPIO.output(self.pin2, GPIO.LOW)
        self.burning = False
        logger.debug("KAKU (pins %s and %s): OFF" % (self.pin1, self.pin2))

    def blink(self, times=1, sleep=0.2):
        count = 0
        while count<times:
            self.on()
            time.sleep(sleep)
            self.off()
            if count<times-1:
                time.sleep(sleep)
            count = count+1
