from .lib import _empty


class DataError(ValueError):
    """
    Error with data preserve
    error can be a message or None if error raised in childs
    data can be anything
    """
    __slots__ = ['error', 'name', 'value', 'trafaret']

    def __init__(self, error=None, name=None, value=_empty, trafaret=None):
        self.error = error
        self.name = name
        self.value = value
        self.trafaret = trafaret

    def __str__(self):
        return str(self.error)

    def __repr__(self):
        return 'DataError(%s)' % str(self)

    def as_dict(self, value=False):
        def as_dict(dataerror):
            if not isinstance(dataerror.error, dict):
                if value and dataerror.value != _empty:
                    return '%s, got %r' % (str(dataerror.error), dataerror.value)
                else:
                    return str(dataerror.error)
            return dict((k, v.as_dict(value=value) if isinstance(v, DataError) else v)
                        for k, v in dataerror.error.items())
        return as_dict(self)
