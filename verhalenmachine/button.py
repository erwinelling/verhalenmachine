import RPi.GPIO as GPIO

class Button:
    def __init__(self, pin, bouncetime):
        # Pin Setup:
        self.pin = pin
        self.bouncetime = bouncetime

        # Initiate button as input w/ pull-up
        GPIO.setmode(GPIO.BOARD)  # Broadcom pin-numbering scheme
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.pin, GPIO.FALLING, bouncetime=self.bouncetime)
