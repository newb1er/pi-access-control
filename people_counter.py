from raspiot.Component import Generator
from raspiot.Pipeline import Pipeline
from gpiozero import DistanceSensor
from time import sleep, time
from os import getenv
from dotenv import load_dotenv
import urllib.request

pipeline = Pipeline()
load_dotenv()


class PeopleCounter(Generator):
    def __init__(self):
        super().__init__()
        self.people = 0

    def configure(self):
        self.threshold = 0.1
        self.frontSensor = DistanceSensor(echo=23, trigger=22)
        self.backSensor = DistanceSensor(echo=18, trigger=17)

    def run(self):
        self.entering = False
        self.leaving = False
        self.prevtime = time()
        while True:
            now = time()
            FrontDistance = self.frontSensor.distance
            BackDistance = self.backSensor.distance

            if BackDistance <= self.threshold and FrontDistance > self.threshold:
                if self.entering:
                    self.entering = False
                    self.prevtime = now
                    self.send(1)
                # elif now - self.prevtime > 1.5:
                #     self.leaving = True

            if FrontDistance <= self.threshold and BackDistance > self.threshold:
                # if self.leaving:
                #     self.leaving = False
                #     self.prevtime = now
                #     self.send(-1)
                # elif now - self.prevtime > 1.5:
                if now - self.prevtime > 1.5:
                    self.entering = True
            sleep(0.5)

    def send(self, change):
        self.people += change
        pipeline.publish('people_count', self.people)


class cloud:
    def __init__(self):
        key = getenv('THINGSPEAK_WRITE')
        self.URl = f'https://api.thingspeak.com/update?api_key={key}'
        self.HEADER = '&field1={}'

    def post(self, val):
        urllib.request.urlopen(self.URl + self.HEADER.format(val))
        print(f'val: {val}')


if __name__ == "__main__":
    thingspeak = cloud()
    def func(val): return print(f'counter: {val}')
    pipeline.subscribe('people_count', func)
    pipeline.subscribe('people_count', thingspeak.post)

    p = PeopleCounter()
    p.start()
