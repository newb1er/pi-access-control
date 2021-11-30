""" Access Control

This module is aimed to check identity only.
No card reading functionality is implemented.

Typical Usage Example:
    accessController = AccessController()
"""

from threading import Timer


class IdentityCredentials:
    """a class storing identity credentials
    """

    def __init__(self):
        self.__ids = {}

    def validate(self, _id) -> str:
        return self.__ids.get(_id, None)

    # TODO: should be removed after database is built
    def get_identities(self, ids):
        """this function is built for unittest only and should be removed after database is built

        Args:
            ids (dict): mock database
        """
        self.__ids = ids


class Door:
    """this class is used for test only

    mocking door behavior
    """

    def __init__(self):
        self.timer = None

    def open(self):
        if self.timer is None:
            print("Door: door opened")
        else:
            self.timer.cancel()

        self.timer = Timer(5, self.close)

    def close(self):
        print("Door: door closed")


class AccessController:
    """ AccessController
    a singleton class
    instance should be obtained using `get_instance()`
    """
    _instance = None

    @staticmethod
    def get_instance():
        """obtain instance of AccessController
        """

        if AccessController._instance is None:
            AccessController()
        return AccessController._instance

    def __init__(self):
        if AccessController._instance is not None:
            raise Exception(
                "AccessController: only one instance can be created at a time")

        AccessController._instance = self
        self.door = Door()

        self.credentials = IdentityCredentials()
        self.allowed_list = []
        self.timers = []
        self.access_granted_today = 0
        self.access_granted_hour = 0
        self.invalid_access_occur = False
        self.invalid_access_count = 0

    def validate_card(self, cardId) -> bool:
        """validate identity by checking id of card

        **should be called by other instaces**

        Args:
            cardId (integer): id of card pass

        Returns:
            bool: if the id of the card is valid
        """
        pid = self.credentials.validate(cardId)
        if pid is None:
            self.invalid_access_occur = True
            self.invalid_access_count += 1
            return False

        self.access_granted(pid)
        return True

    def validate_beacon_UID(self, uid) -> bool:
        """validate identity by checking uid of beacom device

        **should be called by other instaces**

        Args:
            uid (str): uid of beacom device

        Returns:
            bool: if the uid is valid
        """
        pid = self.credentials.validate(uid)
        if pid is None:
            self.invalid_access_occur = True
            self.invalid_access_count += 1
            return False

        self.access_granted(pid)
        return True

    def access_granted(self, pid):
        """add identity to `allowed_list` and remove it after 3 sec

        Args:
            pid (string): id of individual
        """
        print(f"AccessController: Pid: {pid} access granted")
        # if pid has been validated, don't insert
        if pid not in self.allowed_list:
            self.allowed_list.append(pid)
            # pop pid after 3.0 seconds
            timer = Timer(3.0, lambda: self.allowed_list.pop(0))
            timer.start()
            self.timers.append(timer)
            self.access_granted_today += 1
            self.access_granted_hour += 1

        # self.after_granted()

    def after_granted(self):
        """handler function after access granted
        """
        self.door.open()
