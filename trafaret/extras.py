from . import Key, DataError, Any, catch_error, Dict


class KeysSubset(Key):
    """
    From checkers and converters dict must be returned. Some for errors.

    >>> from . import extract_error, Mapping, String
    >>> cmp_pwds = lambda x: {'pwd': x['pwd'] if x.get('pwd') == x.get('pwd1') else DataError('Not equal')}
    >>> d = Dict({KeysSubset('pwd', 'pwd1'): cmp_pwds, 'key1': String})
    >>> sorted(d.check({'pwd': 'a', 'pwd1': 'a', 'key1': 'b'}).keys())
    ['key1', 'pwd']
    >>> extract_error(d.check, {'pwd': 'a', 'pwd1': 'c', 'key1': 'b'})
    {'pwd': 'Not equal'}
    >>> extract_error(d.check, {'pwd': 'a', 'pwd1': None, 'key1': 'b'})
    {'pwd': 'Not equal'}
    >>> get_values = (lambda d, keys: [d[k] for k in keys if k in d])
    >>> join = (lambda d: {'name': ' '.join(get_values(d, ['name', 'last']))})
    >>> Dict({KeysSubset('name', 'last'): join}).check({'name': 'Adam', 'last': 'Smith'})
    {'name': 'Adam Smith'}
    >>> Dict({KeysSubset(): Dict({'a': Any})}).check({'a': 3})
    {'a': 3}
    """

    def __init__(self, *keys):
        self.keys = keys
        self.name = '[%s]' % ', '.join(self.keys)
        self.trafaret = Any()

    def __call__(self, data):
        subdict = dict((k, data.get(k)) for k in self.keys_names() if k in data)
        keys_names = self.keys_names()
        res = catch_error(self.trafaret, subdict)
        if isinstance(res, DataError):
            for k, e in res.error.items():
                yield k, e if isinstance(e, DataError) else DataError(e), keys_names
        else:
            for k, v in res.items():
                yield k, v, keys_names

    def keys_names(self):
        if isinstance(self.trafaret, Dict):
            for key in self.trafaret.keys_names():
                yield key
        for key in self.keys:
            yield key
