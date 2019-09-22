# -*- coding: utf-8 -*-
import pytest
from decimal import Decimal

import trafaret as t
from trafaret.constructor import construct, C


class TestConstruct:
    def test_int(self):
        assert construct(int).check(5) == 5
        assert isinstance(construct(int), t.Int)

    def test_str(self):
        assert construct(str).check(u'blabla') == u'blabla'

    def test_unknown(self):
        assert construct(123) == 123


class TestComplexConstruct:
    def test_list(self):
        assert isinstance(construct([int]), t.List)
        assert construct([int]).check([5]) == [5]
        assert construct([int]).check([5, 6]) == [5, 6]

    def test_tuple(self):
        tt = construct((int,))
        assert isinstance(tt, t.Tuple)
        assert tt([5]) == (5,)


class TestDictConstruct:
    def test_dict(self):
        tt = construct({
            'a': int,
            'b': [str],  # test List
            'c': (str, str, 'atom string'),  # test Tuple
            'f': float,  # test float
            't': Decimal,  # test Type
            t.Key('k'): int,  # test Key
        })
        assert tt({
            'a': 5,
            'b': [u'a'],
            'c': [u'v', u'w', 'atom string'],
            'f': 0.1,
            't': Decimal('100'),
            'k': 100,
        }) == {
                'a': 5,
                'b': ['a'],
                'c': (u'v', u'w', 'atom string'),
                'f': 0.1,
                't': Decimal('100'),
                'k': 100,
        }

    def test_optional_key(self):
        tt = construct({'a': int, 'b?': bool})
        assert tt({'a': '5'}) == {'a': '5'}
        assert tt({'a': '5', 'b': True}) == {'a': '5', 'b': True}

    def test_c(self):
        tt = construct({'a': C & int & float})
        assert tt({'a': 5}) == {'a': 5.0}
        tt = construct(C | int | str)
        assert tt(5) == 5
        assert tt('a') == 'a'

    def test_bad_key(self):
        # 123 can not be constructed to Key
        with pytest.raises(ValueError):
            construct({123: t.String})


class TestCall:
    def test_call(self):
        a_three = lambda val: val if val == 3 else t.DataError('not a 3', code='not_a_3')
        tt = construct([a_three])
        assert tt([3, 3, 3]) == [3, 3, 3]

        with pytest.raises(t.DataError):
            tt([5])
