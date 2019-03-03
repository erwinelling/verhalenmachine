import RPi.GPIO as GPIO
import time
import logging
logger = logging.getLogger('root')

class VU:
    def __init__(self, pin):
        # Pin Setup:
        self.pin = pin

        # Initiate VU
        GPIO.setmode(GPIO.BOARD)  # Broadcom pin-numbering scheme
        GPIO.setup(self.pin, GPIO.OUT)
        self.vumax = 70
        self.p = GPIO.PWM(self.pin, 50)  # channel=12 frequency=50Hz

        self.current_value = -1
        self.current_percentage = 0
        self.test()

    def test(self):
        self.start()
        # for dc in range(0, self.vumax+1, 5):
        #     self.set_value(dc)
        #     time.sleep(0.05)
        # for dc in range(self.vumax, -1, -5):
        #     self.set_value(dc)
        #     time.sleep(0.05)
        self.move_to_percentage(100)
        self.move_to_percentage(0)
        self.stop()

    def set_value(self, value):
        """
        Needs to have an open connection to work (vu.start)
        """
        if value > self.vumax:
            value = self.vumax
        if value < 0:
            value = 0

        self.p.ChangeDutyCycle(value)
        self.current_value = value
        logger.debug("VU (pin %s): %s" % (self.pin, value))

    def set_percentage(self, percentage):
        new_value = (int(percentage)*self.vumax)/100
        self.current_percentage = percentage
        self.set_value(new_value)

    def move_percentage(self, change):
        self.set_value(self.current_percentage + change)
        self.current_percentage = self.current_percentage + change

    def move_to_percentage(self, percentage):
        increase = 5
        if percentage < self.current_percentage:
            increase = -5

        for dc in range(self.current_percentage, percentage, increase):
            self.set_percentage(dc)
            time.sleep(0.01)

    def start(self):
        logger.debug("VU (pin %s) started" % (self.pin))
        self.p.start(0)

    def stop(self):
        self.p.stop()
