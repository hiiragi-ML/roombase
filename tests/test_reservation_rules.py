import unittest

from app.reservation_rules import TIME_SLOTS, get_slot_id
from datetime import time

class TestReservationRules(unittest.TestCase):
    def test_all_valid_slots(self):
        for slot_id, (start, end) in TIME_SLOTS.items():
            with self.subTest(slot_id=slot_id):
                result = get_slot_id(start, end)
                self.assertEqual(result, slot_id)

    def test_invalid_slot(self):
        result = get_slot_id(time(9, 0), time(10, 30))
        self.assertIsNone(result)