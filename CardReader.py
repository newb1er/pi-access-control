import threading
from time import sleep
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

class CardReader:
	def __init__(self, callback, sleep_interval = 0.01, unresponsive_period = 0.5):
		self.reader = SimpleMFRC522()
		# Card reader state.
		self.terminate = True
		self.pasue = False
		# Setup parameters.
		self.sleep_interval = sleep_interval
		self.unresponsive_period = unresponsive_period
		# Set up callback function and thread.
		self.callback = callback
		self.thread = threading.Thread(target = self.thread_card_reader, daemon = True)

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

	def thread_card_reader(self):
		while not self.terminate:
			uid, text = self.reader.read()
			if self.callback and not self.pasue:
				self.callback(uid, text)
				if self.unresponsive_period > 0:
					sleep(self.unresponsive_period)

# Just For Demo. Not real application.
AUTH_FILE = 'valid_card.txt'
LED_GREEN = 16
LED_RED = 18

# Get valid cards info from the AUTH_FILE.
def GetValidList():
	file = open(AUTH_FILE, 'r')
	info = [i.strip().split(' ') for i in file.readlines()]
	valid_uids = []
	valid_text = []
	for i in range(len(info)):
		valid_text.append(info[i][0])
		valid_uids.append(int(info[i][1]))
	return valid_text, valid_uids

# The callback function after the card reader gets card info.
def callback(card_uid, card_text):
	valid_text, valid_uids = GetValidList()
	# If the uid gotten is valid, the green(actually white) light turns on for a second.
	if card_uid in valid_uids:
		GPIO.output(LED_GREEN, GPIO.HIGH)
		sleep(1)
		GPIO.output(LED_GREEN, GPIO.LOW)
	# If the uid gotten is not valid, the red light turns on for a second.
	else:
		GPIO.output(LED_RED, GPIO.HIGH)
		sleep(1)
		GPIO.output(LED_RED, GPIO.LOW)

def main():
	# Setup GPIO on app start.
	GPIO.setmode(GPIO.BOARD)
	GPIO.setup(LED_GREEN, GPIO.OUT)
	GPIO.setup(LED_RED, GPIO.OUT)
	GPIO.output(LED_GREEN, GPIO.LOW)
	GPIO.output(LED_RED, GPIO.LOW)

	# Start the card reader.
	card_reader = CardReader(callback)
	card_reader.Start()
	print("Reading....")

	sleep(5)
	print("Pause....")
	# Pause the card reader from reading.
	card_reader.Pause()	 # DBG
	sleep(5)
	print("Resume....")
	# Resume the card reader to reading.
	card_reader.Resume() # DBG
	
	print('Input "quit" to quit:')
	while True:
		cmd = input()
		if cmd == 'quit':
			break
			
	# End the card reader.
	card_reader.Stop()

if __name__ == '__main__':
	main()
