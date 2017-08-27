import re
from .base import Trafaret, str_types


class RegexpRaw(Trafaret):
    """
    Check if given string match given regexp
    """
    __slots__ = ('regexp', 'raw_regexp')

    def __init__(self, regexp, re_flags=0):
        self.regexp = re.compile(regexp, re_flags) if isinstance(regexp, str_types) else regexp
        self.raw_regexp = self.regexp.pattern if self.regexp else None

    def check_and_return(self, value):
        if not isinstance(value, str_types):
            self._failure("value is not a string", value=value)
        match = self.regexp.match(value)
        if not match:
            self._failure('does not match pattern %s' % self.raw_regexp, value=value)
        return match

    def __repr__(self):
        return '<Regexp>'


class Regexp(RegexpRaw):
    def check_and_return(self, value):
        return super(Regexp, self).check_and_return(value).group()
