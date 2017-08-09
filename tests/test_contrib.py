import unittest
import datetime

import trafaret as t
from trafaret.contrib.rfc_3339 import DateTime


class TestDateTime(unittest.TestCase):
    def test_datetime(self):
        check = DateTime()
        assert check('2017-09-01 23:59') == datetime.datetime(2017, 9, 1, 23, 59)
