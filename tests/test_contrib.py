import unittest
import datetime

import trafaret as t
from trafaret import DataError
from trafaret.contrib.rfc_3339 import DateTime, Date


class TestDateTime(unittest.TestCase):
    def test_datetime(self):
        check = DateTime()
        self.assertEqual(check('2017-09-01 23:59'),
                         datetime.datetime(2017, 9, 1, 23, 59))

    def test_datetime_blank(self):
        check = DateTime(allow_blank=True)
        with self.assertRaises(DataError):
            check('')

    def test_nullable_datetime(self):
        nullable_datetime = t.Or(DateTime, t.Null)
        self.assertIsNone(nullable_datetime.check(None))
        self.assertEqual(
            nullable_datetime.check(datetime.datetime(2017, 9, 1, 23, 59)),
            datetime.datetime(2017, 9, 1, 23, 59)
        )
        self.assertEqual(nullable_datetime.check('2017-09-01 23:59'),
                         datetime.datetime(2017, 9, 1, 23, 59))


class TestDate(unittest.TestCase):
    def test_date(self):
        check = Date()
        result = datetime.date(1954, 7, 29)
        for value in (datetime.date(1954, 7, 29),
                      '1954-07-29',
                      '29 July 1954',
                      '29.07.1954',
                      '29/07/1954',
                      '07/29/1954'):
            self.assertEqual(check(value), result)

    def test_date_blank(self):
        check = Date(allow_blank=True)
        with self.assertRaises(DataError):
            check('')

    def test_date_parse_failed(self):
        check = Date()

        with self.assertRaises(DataError):
            check('29071954')

        self.assertNotEqual(check('290754'), datetime.date(1954, 7, 29))
        self.assertEqual(check('290754'), datetime.date(2054, 7, 29))

    def test_nullable_date(self):
        nullable_date = t.Or(Date, t.Null)
        self.assertIsNone(nullable_date.check(None))
        self.assertEqual(nullable_date.check(datetime.date(1954, 7, 29)),
                         datetime.date(1954, 7, 29))
        self.assertEqual(nullable_date.check('1954-07-29'),
                         datetime.date(1954, 7, 29))
