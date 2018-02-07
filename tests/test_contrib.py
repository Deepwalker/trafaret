import unittest
import datetime

from dateutil.tz import tzutc, tzoffset

import trafaret as t
from trafaret import DataError
from trafaret.contrib.rfc_3339 import DateTime, Date


class TestDateTime(unittest.TestCase):
    def test_datetime(self):
        check = DateTime()
        self.assertEqual(check('2017-09-01 23:59'),
                         datetime.datetime(2017, 9, 1, 23, 59))
        self.assertEqual(
            check('Fri Sep 1 23:59:59 UTC 2017'),
            datetime.datetime(2017, 9, 1, 23, 59, 59, tzinfo=tzutc()))
        self.assertEqual(
            check('Fri Sep 1 23:59:59 2017'),
            datetime.datetime(2017, 9, 1, 23, 59, 59))
        self.assertEqual(
            check('Fri, 1 Sep 2017 23:59:59 -0300'),
            datetime.datetime(2017, 9, 1, 23, 59, 59,
                              tzinfo=tzoffset(None, -10800)))
        self.assertEqual(
            check('2017-09-01T23:59:59.5-03:00'),
            datetime.datetime(2017, 9, 1, 23, 59, 59, 500000,
                              tzinfo=tzoffset(None, -10800)))
        self.assertEqual(
            check('20170901T235959.5-0300'),
            datetime.datetime(2017, 9, 1, 23, 59, 59, 500000,
                              tzinfo=tzoffset(None, -10800)))
        self.assertEqual(
            check('20170901T235959-0300'),
            datetime.datetime(2017, 9, 1, 23, 59, 59,
                              tzinfo=tzoffset(None, -10800)))
        self.assertEqual(check('2017-09-01T23:59:59'),
                         datetime.datetime(2017, 9, 1, 23, 59, 59))
        self.assertEqual(check('20170901T235959'),
                         datetime.datetime(2017, 9, 1, 23, 59, 59))
        self.assertEqual(check('20170901235959'),
                         datetime.datetime(2017, 9, 1, 23, 59, 59))
        self.assertEqual(check('2017-09-01T23:59'),
                         datetime.datetime(2017, 9, 1, 23, 59))
        self.assertEqual(check('20170901T2359'),
                         datetime.datetime(2017, 9, 1, 23, 59))
        self.assertEqual(check('2017-09-01T23'),
                         datetime.datetime(2017, 9, 1, 23))
        self.assertEqual(check('20170901T23'),
                         datetime.datetime(2017, 9, 1, 23))
        self.assertEqual(check('2017-09-01'),
                         datetime.datetime(2017, 9, 1))
        self.assertEqual(check('20170901'),
                         datetime.datetime(2017, 9, 1))
        self.assertEqual(check('09-01-2017'),
                         datetime.datetime(2017, 9, 1))
        self.assertEqual(check('09-01-17'),
                         datetime.datetime(2017, 9, 1))
        self.assertEqual(check('2017.Sep.01'),
                         datetime.datetime(2017, 9, 1))
        self.assertEqual(check('2017/09/01'),
                         datetime.datetime(2017, 9, 1))
        self.assertEqual(check('2017 09 01'),
                         datetime.datetime(2017, 9, 1))
        self.assertEqual(check('1st of September 2017'),
                         datetime.datetime(2017, 9, 1))

        # Note: to equality here we need to pass extra params to parse() method
        self.assertNotEqual(check('01-09-2017'),
                            datetime.datetime(2017, 9, 1))

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

    def test_repr(self):
        self.assertEqual(repr(DateTime()), '<DateTime>')
        self.assertEqual(repr(DateTime(allow_blank=True)), '<DateTime(blank)>')


class TestDate(unittest.TestCase):
    def test_date(self):
        check = Date()
        result = datetime.date(1954, 7, 29)
        for value in (datetime.date(1954, 7, 29),
                      '1954-07-29',
                      '29 July 1954',
                      '29.07.1954',
                      '29/07/1954',
                      '07/29/1954',
                      datetime.datetime(1954, 7, 29, 23, 59)):
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

    def test_repr(self):
        self.assertEqual(repr(Date()), '<Date>')
        self.assertEqual(repr(Date(allow_blank=True)), '<Date(blank)>')
