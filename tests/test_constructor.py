# -*- coding: utf-8 -*-
import unittest
from collections import Mapping as AbcMapping
from decimal import Decimal

import trafaret as t
from trafaret import extract_error, ignore, DataError
from trafaret.extras import KeysSubset
from trafaret.constructor import construct, C


class TestConstruct(unittest.TestCase):
    def test_int(self):
        self.assertEqual(
            construct(int).check(5),
            5
        )
        self.assertIsInstance(construct(int), t.Int)

    def test_str(self):
        self.assertEqual(
            construct(str).check('blabla'),
            'blabla'
        )

    def test_unknown(self):
        self.assertEqual(construct(123), 123)


class TestComplexConstruct(unittest.TestCase):
    def test_list(self):
        self.assertIsInstance(construct([int]), t.List)
        self.assertEqual(
            construct([int]).check([5]),
            [5]
        )
        self.assertEqual(
            construct([int]).check([5, 6]),
            [5, 6]
        )

    def test_tuple(self):
        tt = construct((int,))
        self.assertIsInstance(tt, t.Tuple)
        self.assertEqual(tt([5]), (5,))


class TestDictConstruct(unittest.TestCase):
    def test_dict(self):
        tt = construct({
            'a': int,
            'b': [str],  # test List
            'c': (str, str, 'atom string'),  # test Tuple
            'f': float,  # test float
            't': Decimal,  # test Type
            t.Key('k'): int,  # test Key
        })
        self.assertEqual(
            tt({
                'a': 5,
                'b': ['a'],
                'c': ['v', 'w', 'atom string'],
                'f': 0.1,
                't': Decimal('100'),
                'k': 100,
            }),
            {
                'a': 5,
                'b': ['a'],
                'c': ('v', 'w', 'atom string'),
                'f': 0.1,
                't': Decimal('100'),
                'k': 100,
            }
        )

    def test_optional_key(self):
        tt = construct({'a': int, 'b?': bool})
        self.assertEqual(tt({'a': '5'}), {'a': 5})
        self.assertEqual(tt({'a': '5', 'b': True}), {'a': 5, 'b': True})

    def test_c(self):
        tt = construct({'a': C & int & float})
        self.assertEqual(tt({'a': 5}), {'a': 5.0})

        tt = construct(C | int | str)
        self.assertEqual(tt(5), 5)
        self.assertEqual(tt('a'), 'a')

    def test_bad_key(self):
        # 123 can not be constructed to Key
        with self.assertRaises(ValueError):
            construct({123: t.String})


class TestCall(unittest.TestCase):
    def test_call(self):
        a_three = lambda val: val if val == 3 else t.DataError('not a 3')
        tt = construct([a_three])
        self.assertEqual(tt([3, 3, 3]), [3, 3, 3])

        with self.assertRaises(t.DataError):
            tt([5])
