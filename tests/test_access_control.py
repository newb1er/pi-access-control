import unittest
import time
from src.access_control import AccessController

mock_identity = {
    "C12345678": "Michael",
    "B12345678": "Michael",
    "C75757575": "Jenny",
    "C98989898": "Leo",
    "B98989898": "Leo",
}

accessController = AccessController.get_instance()
accessController.credentials.get_identities(mock_identity)


class AccessControllerTestCase(unittest.TestCase):
    def tearDown(self):
        accessController.allowed_list.clear()
        list(map(lambda x: x.cancel(), accessController.timers))
        accessController.timers.clear()

    def test_validate_one_card(self):
        accessController.validate_card("C12345678")

        self.assertEqual(accessController.allowed_list, ["Michael"])

    def test_validate_multiple_cards(self):
        self.assertTrue(accessController.validate_card("C12345678"))
        accessController.validate_card("C75757575")
        accessController.validate_card("C98989898")

        self.assertEqual(accessController.allowed_list,
                         ["Michael", "Jenny", "Leo"])

    def test_validate_one_beacon_UID(self):
        accessController.validate_beacon_UID("B12345678")

        self.assertEqual(accessController.allowed_list, ["Michael"])

    def test_validate_multiple_beacon_UIDs(self):
        accessController.validate_beacon_UID("B12345678")
        accessController.validate_beacon_UID("B98989898")

        self.assertEqual(accessController.allowed_list, ["Michael", "Leo"])

    def test_validate_one_identity_with_different_methods(self):
        accessController.validate_card("C12345678")
        accessController.validate_beacon_UID("B12345678")

        self.assertEqual(accessController.allowed_list, ["Michael"])
