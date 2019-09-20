import trafaret as t


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

def test_decimal():
    trafaret = t.ToDecimal()
    res = t.extract_error(trafaret, '')
    assert res == 'value can\'t be converted to Decimal'
