from decimal import Decimal

import pytest

import trafaret as t
from trafaret.codes import INVALID_DECIMAL


class TestToDecimal:
    @pytest.mark.parametrize('value, expected', [
        (0, Decimal('0.0000')),
        (1000, Decimal('1000.0000')),
        (1000.0, Decimal('1000.0000')),
        ('1000', Decimal('1000.0000')),
        ('1000.0', Decimal('1000.0000')),
        (-1000, Decimal('-1000.0000')),
        (-1000.0, Decimal('-1000.0000')),
        ('-1000', Decimal('-1000.0000')),
        ('-1000.0', Decimal('-1000.0000')),
    ])
    def test_to_decimal(self, value, expected):
        result = t.ToDecimal().check(value)
        assert result == expected

    def test_error_code(self):
        with pytest.raises(t.DataError) as err:
            t.ToDecimal().check('')
        assert err.value.code == INVALID_DECIMAL

    def test_extract_error(self):
        result = t.extract_error(t.ToDecimal(), '')
        assert result == 'value can\'t be converted to Decimal'

    def test_none_to_decimal(self):
        with pytest.raises(TypeError) as err:
            t.extract_error(t.ToDecimal(), None)
            assert err == 'conversion from NoneType to Decimal is not supported'

    @pytest.mark.parametrize('value, expected', [
        (t.ToDecimal(), '<ToDecimal>'),
        (t.ToDecimal[1:], '<ToDecimal(gte=1)>'),
        (t.ToDecimal[1:20], '<ToDecimal(gte=1, lte=20)>'),
    ])
    def test_repr(self, value, expected):
        assert repr(value) == expected


def test_num_meta_repr():
    res = t.ToInt[1:]
    assert repr(res) == '<ToInt(gte=1)>'
    res = t.ToInt[1:10]
    assert repr(res) == '<ToInt(gte=1, lte=10)>'
    res = t.ToInt[:10]
    assert repr(res) == '<ToInt(lte=10)>'
    res = t.ToFloat[1:]
    assert repr(res) == '<ToFloat(gte=1)>'
    res = t.ToInt > 3
    assert repr(res) == '<ToInt(gt=3)>'
    res = 1 < (t.ToFloat < 10)
    assert repr(res) == '<ToFloat(gt=1, lt=10)>'

def test_meta_res():
    res = (t.ToInt > 5).check(10)
    assert res == 10
    res = t.extract_error(t.ToInt > 5, 1)
    assert res == 'value should be greater than 5'
    res = (t.ToInt < 3).check(1)
    assert res == 1
    res = t.extract_error(t.ToInt < 3, 3)
    assert res == 'value should be less than 3'
    res = t.extract_error(t.ToInt >= 5, 1)
    assert res == 'value is less than 5'
    res = t.extract_error(t.ToInt <= 3, 4)
    assert res == 'value is greater than 3'
