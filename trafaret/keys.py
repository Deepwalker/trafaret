import trafaret as t


def xor_key(first, second, trafaret):
    trafaret = t.Trafaret._trafaret(trafaret)
    def check_(value):
        if (first in value) ^ (second in value):
            key = first if first in value else second
            yield first, t.catch_error(trafaret, value[key]), (key,)
        elif first in value and second in value:
            yield first, t.DataError(error=f'correct only if {second} is not defined'), (first,)
            yield second, t.DataError(error=f'correct only if {first} is not defined'), (second,)
        else:
            yield first, t.DataError(error=f'is required if {second} is not defined'), (first,)
            yield second, t.DataError(error=f'is required if {first} is not defined'), (second,)
    return check_


def confirm_key(name, confirm_name, trafaret):
    def check_(value):
        first, second = None, None
        if name in value:
            first = value[name]
        else:
            yield name, t.DataError('is required'), (name,)
        if confirm_name in value:
            second = value[confirm_name]
        else:
            yield confirm_name, t.DataError('is required'), (confirm_name,)
        if not (first and second):
            return
        yield name, t.catch_error(trafaret, first), (name,)
        yield confirm_name, t.catch_error(trafaret, second), (confirm_name,)
        if first != second:
            yield confirm_name, t.DataError(f'must be equal to {name}'), (confirm_name,)
    return check_
