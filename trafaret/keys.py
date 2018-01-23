import trafaret as t


def subdict(name, *keys, **kw):
    """
    Subdict key.

    Takes a `name`, any number of keys as args and keyword argument `trafaret`.
    Use it like:

        def check_passwords_equal(data):
            if data['password'] != data['password_confirm']:
                return t.DataError('Passwords are not equal')
            return data['password']

        passwords_key = subdict(
            'password',
            t.Key('password', trafaret=check_password),
            t.Key('password_confirm', trafaret=check_password),
            trafaret=check_passwords_equal,
        )

        signup_trafaret = t.Dict(
            t.Key('email', trafaret=t.Email),
            passwords_key,
        )

    """
    trafaret = kw.pop('trafaret')  # coz py2k

    def inner(data, context=None):
        errors = False
        preserve_output = []
        touched = set()
        collect = {}
        for key in keys:
            for k, v, names in key(data, context=context):
                touched.update(names)
                preserve_output.append((k, v, names))
                if isinstance(v, t.DataError):
                    errors = True
                else:
                    collect[k] = v
        if errors:
            for out in preserve_output:
                yield out
        elif collect:
            yield name, t.catch(trafaret, collect), touched

    return inner


def xor_key(first, second, trafaret):
    """
    xor_key - takes `first` and `second` key names and `trafaret`.

    Checks if we have only `first` or only `second` in data, not both,
    and at least one.

    Then checks key value against trafaret.
    """
    trafaret = t.Trafaret._trafaret(trafaret)

    def check_(value):
        if (first in value) ^ (second in value):
            key = first if first in value else second
            yield first, t.catch_error(trafaret, value[key]), (key,)
        elif first in value and second in value:
            yield first, t.DataError(error='correct only if {} is not defined'.format(second)), (first,)
            yield second, t.DataError(error='correct only if {} is not defined'.format(first)), (second,)
        else:
            yield first, t.DataError(error='is required if {} is not defined'.format('second')), (first,)
            yield second, t.DataError(error='is required if {} is not defined'.format('first')), (second,)

    return check_


def confirm_key(name, confirm_name, trafaret):
    """
    confirm_key - takes `name`, `confirm_name` and `trafaret`.

    Checks if data['name'] equals data['confirm_name'] and both
    are valid against `trafaret`.
    """
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
            yield confirm_name, t.DataError('must be equal to {}'.format(name)), (confirm_name,)
    return check_
