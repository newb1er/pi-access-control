import cloud4rpi
import threading
import sys
from time import sleep
from os import getenv
from dotenv import load_dotenv


class Cloud4RpiVariable:
    """ A structure of Cloud4Rpi Variables

    Returns:
        (dict): a structure just like it is in the official document
    """
    __slots__ = ('title', 'type', 'bind', 'immutable', 'default')

    def __init__(self, title: str, type: str, bind: any, immutable=True, default=None):
        """
        Args:
            title (str): title show in panel
            type (str): type of variable
            bind (any): a variable to bind (not a function !!)
            immutable (bool, optional): whether binded variable is immutable. Defaults to True.
            default (any, optional): default value to binded variable (if immutable is set to True). \n\t\tDefaults to None.
        """
        self.title = title
        self.type = type
        self.bind = bind
        self.immutable = immutable
        self.default = default

    def __call__(self):
        return {
            self.title: {
                'type': self.type,
                'value': self.default,
                'bind': self._callback
            }
        }

    def __str__(self):
        return f'{{\n\t{self.title}: \
            {{\n\t\t\'type\': {self.type},\n\t\t\'value\': {self.value} \
                \n\t\t\'bind\': {self.bind}\n\t}}\n}}'

    def _callback(self, value=None):
        if self.immutable and value is not None:
            self.bind = value
        return self.bind


class Cloud4RpiConfig:
    """a structure class for class "Cloud"
    """
    variables = {}
    diagnostics = {}

    @classmethod
    def add_var(cls, var: dict):
        """add variables

        Args:
            var (dict): a dict object created from "Cloud4RpiVariable"
        """
        cls.variables = {**(cls.variables), **var}

    @classmethod
    def add_diag(cls, diag: dict):
        cls.diagnostics = {**(cls.diagnostics), **diag}


class Cloud(Cloud4RpiConfig, threading.Thread):
    """a class to publish variables to Cloud4Rpi

    Usage:
        `cloud = Cloud.get_instance()`\n
        `cloud.start() # just like normal threading object`
    """
    _instance = None

    DEVICE_TOKEN = None  # ! should not fill your token here
    DATA_SENDING_INTERVAL = 60  # secs
    DIAG_SENDING_INTERVAL = 650  # secs
    POLL_INTERVAL = 0.5  # secs

    @staticmethod
    def get_instance():
        if Cloud._instance is None:
            Cloud()
        return Cloud._instance

    def __init__(self):
        if Cloud._instance is not None:
            raise Exception(
                'Cloud: only one instance can be created at a time')

        Cloud._instance = self

        threading.Thread.__init__(self)
        self.daemon = True
        self.kill = False

        load_dotenv()
        self.DEVICE_TOKEN = getenv('DEVICE_TOKEN')

        if self.DEVICE_TOKEN is None:
            raise "no DEVICE_TOKEN found."

        self.init_connection()

    def init_connection(self):
        self.device = cloud4rpi.connect(self.DEVICE_TOKEN)

    def run(self):
        cloud4rpi.log.info('Service started. Start publishing...')
        data_timer = 0
        diag_timer = 0

        try:
            self.device.declare(self.variables)
            self.device.declare_diag(self.diagnostics)

            self.device.publish_config()

            sleep(1)
            while True:
                if self.kill is True:
                    break

                if data_timer <= 0:
                    self.device.publish_data()
                    data_timer = self.DATA_SENDING_INTERVAL

                if diag_timer <= 0:
                    self.device.publish_diag()
                    diag_timer = self.DIAG_SENDING_INTERVAL

                sleep(self.POLL_INTERVAL)
                data_timer -= self.POLL_INTERVAL
                diag_timer -= self.POLL_INTERVAL

        except Exception as e:
            error = cloud4rpi.get_error_message(e)
            cloud4rpi.log.exception(f'ERROR! {error} {sys.exc_info()[0]}')

        finally:
            cloud4rpi.log.info("Service stopping...")


if __name__ == '__main__':
    cloud = Cloud.get_instance()
    cloud.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        cloud.kill = True
        cloud.join()
