from abc import ABCMeta, abstractmethod

class Component(metaclass=ABCMeta):
    @abstractmethod
    def set_pin(self):
        pass

    def __init__(self):
        self.set_pin()