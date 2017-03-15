# -*- coding: utf-8 -*-
import unittest
import trafaret as t
from collections import Mapping as AbcMapping
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
            'b': [str],
            'c': (str, str),
        })
        self.assertEqual(
            tt({'a': 5, 'b': ['a'], 'c': ['v', 'w']}),
            {'a': 5, 'b': ['a'], 'c': ('v', 'w')}
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


class TestCall(unittest.TestCase):
    def test_call(self):
        a_three = lambda val: val if val == 3 else t.DataError('not a 3')
        tt = construct([a_three])
        self.assertEqual(tt([3, 3, 3]), [3, 3, 3])

        with self.assertRaises(t.DataError):
            tt([5])
