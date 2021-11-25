import threading
from time import sleep
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from access_control import AccessController

mock_cardid = {
    947650382188: 'person1',
    146673054805: 'person2'
}

accessController = AccessController.get_instance()
accessController.credentials.get_identities(mock_cardid)


class CardReader:
    _instance = None

    @staticmethod
    def get_instance():
        if CardReader._instance is None:
            CardReader()
        return CardReader._instance

    def __init__(self, sleep_interval=0.01, unresponsive_period=0.5):
        if CardReader._instance is not None:
            raise Exception(
                'CardReader: only one instance can be created at a time')

        CardReader._instance = self

        self.reader = SimpleMFRC522()
        # Card reader state.
        self.terminate = True
        self.pasue = False
        # Setup parameters.
        self.sleep_interval = sleep_interval
        self.unresponsive_period = unresponsive_period
        # Set up callback function and thread.
        self.thread = threading.Thread(
            target=self.thread_card_reader, daemon=True)
        self.LED_GREEN = 16
        self.LED_RED = 18
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.LED_GREEN, GPIO.OUT)
        GPIO.setup(self.LED_RED, GPIO.OUT)
        GPIO.output(self.LED_GREEN, GPIO.LOW)
        GPIO.output(self.LED_RED, GPIO.LOW)

    # Start the card reader.
    def Start(self):
        # Check if Stop() was called before calling Start().
        if not self.thread:
            return
        # Cherck if Start() has already been called.
        if self.terminate == False:
            return
        self.terminate = False
        self.thread.start()

    # Stop the card reader. !{Cannot call Start() again after calling Stop()}!
    def Stop(self):
        self.terminate = True
        self.callback = None
        self.thread = None
        GPIO.cleanup()

    # Pause the card reader from reading.
    def Pause(self):
        self.pasue = True

    # Resume the card reader to reading.
    def Resume(self):
        self.pasue = False

    def callback(self, uid, text):
        if accessController.validate_card(uid):
            GPIO.output(self.LED_GREEN, GPIO.HIGH)
            sleep(1)
            GPIO.output(self.LED_GREEN, GPIO.LOW)
        # If the uid gotten is not valid, the red light turns on for a second.
        else:
            GPIO.output(self.LED_RED, GPIO.HIGH)
            sleep(1)
            GPIO.output(self.LED_RED, GPIO.LOW)

    def thread_card_reader(self):
        while not self.terminate:
            uid, text = self.reader.read()
            if self.callback and not self.pasue:
                self.callback(uid, text)
                if self.unresponsive_period > 0:
                    sleep(self.unresponsive_period)


# For testing.
card_reader = CardReader()
card_reader.Start()
print("Reading....")
sleep(20)
card_reader.Stop()
print("Stop")
