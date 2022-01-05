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
from os import getenv
from dotenv import load_dotenv

load_dotenv()

GPIO.setwarnings(False)
g_MSG_Q = Queue()
accessController = AccessController.get_instance()

# token = 'JXlxZKN5sIcEEcDmveS9aOKo6ssR17e93xmThwVQKaE'# Line Token
token = getenv('LINE_NOTIFY_TOKEN')

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

def init_cloud():
    URl='https://api.thingspeak.com/update?api_key='
    KEY= getenv('THINGSPEAK_WRITE')
    HEADER='&field1={}&field2={}&field3={}&field4={}&field5={}'.format(0, 0, 0, 0, 0)
    NEW_URL=URl+KEY+HEADER
    data=urllib.request.urlopen(NEW_URL)
    

def read_allow_pass():
    url = 'https://api.thingspeak.com/channels/1626039/fields/4.json?results=1'
    KEY = getenv('THINGSPEAK_READ')
    data = requests.get(f'{url}&api_key={KEY}').json()
    print(data['feeds'][0]['field4'])
    return data['feeds'][0]['field4']

# Post number of valid access to the cloud.
def post_access_info(uid, validated: bool):
    access_granted_today = accessController.access_granted_today
    invalid_access_count = accessController.invalid_access_count
    is_invalid_access = not validated

    allow_pass = int(read_allow_pass())
    if not allow_pass:
        allow_pass = 0
    
    if not is_invalid_access:
        allow_pass += 1
    URl='https://api.thingspeak.com/update?api_key='
    KEY= getenv('THINGSPEAK_WRITE')
    HEADER='&field1={}&field2={}&field3={}&field4={}'.format(access_granted_today, invalid_access_count, is_invalid_access, allow_pass)
    NEW_URL=URl+KEY+HEADER
    data=urllib.request.urlopen(NEW_URL)
    print(HEADER)

'''
# Read data from cloud and put into queue
def read_data_display():
    URL='https://api.thingspeak.com/channels/1620808/fields/1.json?api_key='
    KEY='X9ZRWHS4GEMH0J90'
    HEADER='&results=1'
    NEW_URL=URL+KEY+HEADER
    get_data=requests.get(NEW_URL).json()
    channel_id=get_data['channel']['id']
    feild_1=get_data['feeds']
    t=[]
    for x in feild_1:
        t.append(x['field1'])
    g_MSG_Q.put(t[0])
'''

class CardReaderCloud(CardReader):
    def __init__(self, sleep_interval=0.01, unresponsive_period=0.5):
        CardReader.__init__(self, sleep_interval, unresponsive_period)
        self.buzzer = Buzzer(17)

    def callback(self, uid, text):
        validated = accessController.validate_card(uid)
        # Light the LED
        if validated:
            # print on to lcd screen
            g_MSG_Q.put(accessController.access_granted_today)
            GPIO.output(self.LED_GREEN, GPIO.HIGH)
            sleep(1)
            GPIO.output(self.LED_GREEN, GPIO.LOW)
        # If the uid gotten is not valid, the red light and buzzer turn on for a second.
        else:
            g_MSG_Q.put(-1)
            GPIO.output(self.LED_RED, GPIO.HIGH)
            self.buzzer.beep()
            sleep(2)
            self.buzzer.off()
            GPIO.output(self.LED_RED, GPIO.LOW)
            linenotify(token, 'Invalid Access Occurs!')
        # print on to lcd screen
        g_MSG_Q.put(accessController.access_granted_today)
        # post access information to the cloud.
        post_access_info(uid, validated)

class IntruderAlert(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.url = 'https://api.thingspeak.com/channels/1626255/fields/2.json?results=1'
        self.KEY = getenv('THINGSPEAK_CONTROLL_READ')
        self.terminate = True
        self.lastTime = None
    
    def run(self):
        self.terminate = False
        try:
            while not self.terminate:
                data = requests.get(f'{self.url}&api_key={self.KEY}').json()
                feed = data['feeds'][0]
                if self.lastTime and self.lastTime == feed['created_at']:
                    self.lastTime = feed['created_at']
                    continue
                else:
                    self.lastTime = feed['created_at']

                intrude = data['feeds'][0]['field2']
                print(f'intrude: {intrude}')

                if intrude is '1':
                    linenotify(token, 'Intruder!')
                sleep(5)
        finally:
            print('alert ended')
    
    def stop(self):
        self.terminate = True


if __name__ == '__main__':
    init_cloud()
    card_reader = CardReaderCloud()
    card_reader.start()
    lcd = LCD()
    print('Reading...')
    strLine1, strLine2 = 'People entered', 'today: 0'
    show_display(strLine1, strLine2)

    alert = IntruderAlert()
    alert.start()
    
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
        alert.stop()
        card_reader.stop()
        lcd.clear()
        print("Stop")
