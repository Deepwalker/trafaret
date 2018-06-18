from .lib import _empty


class DataError(ValueError):
    """
    Error with data preserve
    error can be a message or None if error raised in childs
    data can be anything
    """
    __slots__ = ['error', 'name', 'value', 'trafaret', 'code']

    error_code = 'unknown'

    def __init__(self, error=None, name=None, value=_empty, trafaret=None, code=None):
        """
        :attribute error: can be a string, a list of dataerrors, a dict[string, dataerror]
        :attribute name:
        :attribute value: validated value that leads to this error
        :attribute trafaret: trafaret raised error
        :attribute code: code for error, like `value_is_to_big`
        """
        self.error = error
        self.name = name
        self.value = value
        self.trafaret = trafaret
        self.code = code or self.__class__.error_code

    def __str__(self):
        return str(self.error)

    def __repr__(self):
        return 'DataError(%r)' % str(self)

    def as_dict(self, value=False):
        # TODO FIXME to provide consisitence results
        if not isinstance(self.error, dict):
            if value and self.value != _empty:
                return '%s, got %r' % (str(self.error), self.value)
            else:
                return str(self.error)
        return dict((k, v.as_dict(value=value) if isinstance(v, DataError) else v)
                    for k, v in self.error.items())
