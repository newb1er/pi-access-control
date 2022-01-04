from card_reader import CardReader
from access_control import AccessController
from signal import signal, SIGTERM, SIGHUP, pause
from rpi_lcd import LCD
import urllib.request
import RPi.GPIO as GPIO
from gpiozero import Buzzer
import requests
import threading
from time import sleep
from queue import Queue
import lineTool

GPIO.setwarnings(False)
g_MSG_Q = Queue()
accessController = AccessController.get_instance()

token = 'JXlxZKN5sIcEEcDmveS9aOKo6ssR17e93xmThwVQKaE'# Line Token

# LCD display funcitons
def show_display(strLine1, strLine2):
    def safe_exit(signum, frame):
        exit(1)
    try:
        signal(SIGTERM, safe_exit)
        signal(SIGHUP, safe_exit)
        if strLine2 == '':
            lcd.clear()
            lcd.text(strLine1, 1)
            sleep(2)
            lcd.clear()
        lcd.text(strLine1, 1)
        lcd.text(strLine2, 2)
    except KeyboardInterrupt:
        pass

# Get notification from Line
def linenotify(token, msg):
    lineTool.lineNotify(token, msg)

# Post number of valid access to the cloud.
def post_access_info(uid):
    access_granted_today = accessController.access_granted_today
    invalid_access_count = accessController.invalid_access_count
    is_invalid_access = not accessController.validate_card(uid)
    if is_invalid_access:
        g_MSG_Q.put(-1)
    URl='https://api.thingspeak.com/update?api_key='
    KEY= 'EZ7L9YX69P1XU3Q4'
    HEADER='&field1={}&field2={}&field3={}'.format(access_granted_today, invalid_access_count, is_invalid_access)
    NEW_URL=URl+KEY+HEADER
    print(NEW_URL)
    data=urllib.request.urlopen(NEW_URL)
    print(data)


class CardReaderCloud(CardReader):
    def __init__(self, sleep_interval=0.01, unresponsive_period=0.5):
        CardReader.__init__(self, sleep_interval, unresponsive_period)
        self.buzzer = Buzzer(17)

    def callback(self, uid, text):
        # post access information to the cloud.
        post_access_info(uid)
        g_MSG_Q.put(accessController.access_granted_today)
        # Light the LED
        if accessController.validate_card(uid):
            GPIO.output(self.LED_GREEN, GPIO.HIGH)
            sleep(1)
            GPIO.output(self.LED_GREEN, GPIO.LOW)
        # If the uid gotten is not valid, the red light and buzzer turn on for a second.
        else:
            GPIO.output(self.LED_RED, GPIO.HIGH)
            self.buzzer.beep()
            sleep(2)
            self.buzzer.off()
            GPIO.output(self.LED_RED, GPIO.LOW)
            linenotify(token, 'Invalid Access Occurs!')


if __name__ == '__main__':
    card_reader = CardReaderCloud()
    card_reader.start()
    lcd = LCD()
    print('Reading...')
    strLine1, strLine2 = 'People entered', 'today: 0'
    show_display(strLine1, strLine2)
    try:
        # LCD display if the queue is not empty
        while True:
            if not g_MSG_Q.empty():
                nPeople = g_MSG_Q.get()
                if nPeople == -1:
                    strLine1, strLine2 = 'Invalid Card!', ''
                else:
                    strLine1, strLine2 = 'People entered', 'today: ' + str(nPeople)
                show_display(strLine1, strLine2)
            sleep(0.01)
    except KeyboardInterrupt:
        card_reader.stop()
        lcd.clear()
        print("Stop")
