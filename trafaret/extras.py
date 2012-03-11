from . import Key, DataError, Any, catch_error, Dict, extract_error, Mapping, String


class KeysSubset(Key):
    """
    From checkers and converters dict must be returned. Some for errors.

    >>> cmp_pwds = lambda x: {'pwd': x['pwd'] if x.get('pwd') == x.get('pwd1') else DataError('Not equal')}
    >>> d = Dict({KeysSubset(['pwd', 'pwd1']): cmp_pwds, 'key1': String})
    >>> sorted(d.check({'pwd': 'a', 'pwd1': 'a', 'key1': 'b'}).keys())
    ['key1', 'pwd']
    >>> extract_error(d.check, {'pwd': 'a', 'pwd1': 'c', 'key1': 'b'})
    {'pwd': 'Not equal'}
    >>> extract_error(d.check, {'pwd': 'a', 'pwd1': None, 'key1': 'b'})
    {'pwd': 'Not equal'}
    """

    def __init__(self, keys, to_name=None):
        self.keys = keys
        self.name = '[%s]' % ', '.join(self.keys)
        self.to_name = to_name
        self.trafaret = Any()

    def pop(self, data):
        subdict = dict((k, data.pop(k)) for k in self.keys if k in data)
        res = catch_error(self.trafaret, subdict)
        if isinstance(res, DataError):
            res = res.error
        for k, v in res.items():
            yield k, v



