""" This module is expirement. API and implementation are unstable.
    Supposed to use with ``Request`` object or something like that.
"""
from collections import Mapping
from . import Trafaret, DataError, Key, catch_error, _empty


def get_deep_attr(obj, keys):
    """ Helper for DeepKey"""
    cur = obj
    for k in keys:
        if isinstance(cur, Mapping) and k in cur:
            cur = cur[k]
            continue
        else:
            try:
                cur = getattr(cur, k)
                continue
            except AttributeError:
                pass
        raise DataError(error='Unexistent key')
    return cur


class DeepKey(Key):
    """ Lookup for attributes and items
    Path in ``name`` must be delimited by ``.``.

    >>> from trafaret import Int
    >>> class A(object):
    ...     class B(object):
    ...         d = {'a': 'word'}
    >>> dict((DeepKey('B.d.a') >> 'B_a').pop(A))
    {'B_a': 'word'}
    >>> dict((DeepKey('c.B.d.a') >> 'B_a').pop({'c': A}))
    {'B_a': 'word'}
    >>> dict((DeepKey('B.a') >> 'B_a').pop(A))
    {'B.a': DataError(Unexistent key)}
    >>> dict(DeepKey('c.B.d.a', to_name='B_a', trafaret=Int()).pop({'c': A}))
    {'B_a': DataError(value can't be converted to int)}
    """

    def pop(self, data):
        try:
            yield self.get_name(), catch_error(self.trafaret,
                    get_deep_attr(data, self.name.split('.')))
        except DataError as e:
            if self.default != _empty:
                yield self.get_name(), self.default
            elif not self.optional:
                yield self.name, e


class Visitor(Trafaret):
    """ Check any object or mapping with ``DeepKey`` instances.
    This means that counts only existance and correctness of given paths.
    Visitor will not check for additional attributes etc.
    """

    def __init__(self, keys):
        self.keys = []
        for key, trafaret in keys.items():
            key_ = key if isinstance(key, DeepKey) else DeepKey(key)
            key_.set_trafaret(self._trafaret(trafaret))
            self.keys.append(key_)

    def _check_val(self, value):
        errors = {}
        data = {}
        for key in self.keys:
            for name, res in key.pop(value):
                if isinstance(res, DataError):
                    errors[name] = res
                else:
                    data[name] = res
        if errors:
            raise DataError(error=errors)
        return data
