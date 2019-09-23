import pytest
import trafaret as t


def test_dataerror_value():
    error = t.DataError(error='Wait for good value', value='BAD ONE', code='bad_value')
    assert error.as_dict() == 'Wait for good value'
    assert error.as_dict(value=True) == "Wait for good value, got 'BAD ONE'"
    assert error.to_struct() == {
        'code': 'bad_value',
        'message': 'Wait for good value',
    }

def test_nested_dataerror_value():
    error = t.DataError(
        error={0: t.DataError(error='Wait for good value', value='BAD ONE', code='bad_value')},
        code='some_elements_going_mad',
    )
    assert error.as_dict() == {0: 'Wait for good value'}
    assert error.as_dict(value=True) == {0: "Wait for good value, got 'BAD ONE'"}
    assert error.to_struct() == {
        'code': 'some_elements_going_mad',
        'nested': {0: {
            'code': 'bad_value',
            'message': 'Wait for good value',
        }},
    }
    assert error.to_struct(value=True) == {
        'code': 'some_elements_going_mad',
        'nested': {0: {
            'code': 'bad_value',
            'message': "Wait for good value, got 'BAD ONE'",
        }},
    }


def test_dataerror_wrong_arg():
    with pytest.raises(RuntimeError):
        t.DataError(123)


def test_repr():
    assert repr(t.DataError('error')) == "DataError('error')"
