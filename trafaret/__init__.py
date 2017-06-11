# -*- coding: utf-8 -*-

import sys
import functools
import inspect
import re
import itertools
import numbers
import warnings
from collections import Mapping as AbcMapping
import types
from .lib import py3, py3metafix


__VERSION__ = (0, 10, 2)


# Python3 support
if py3:
    import urllib.parse as urlparse
    str_types = (str, bytes)
    unicode = str
else:
    try:
        from future_builtins import map
    except ImportError:
        # Support for GAE runner
        from itertools import imap as map
    import urlparse
    str_types = (basestring,)

def _dd(value):
    if not hasattr(value, 'items'):
        return repr(value)
    return r"{%s}" % ', '.join("%r: %s" % (x[0], _dd(x[1])) for x in sorted(value.items(), key=lambda x: x[0]))


def deprecated(message):
    warnings.warn(message, DeprecationWarning)


"""
Trafaret is tiny library for data validation
It provides several primitives to validate complex data structures
Look at doctests for usage examples
"""

__all__ = (
    "DataError", "Trafaret", "Any", "Int", "String",
    "List", "Dict", "Or",  "And", "Null", "Float", "Enum", "Callable",
    "Call", "Forward", "Bool", "Type", "Subclass", "Mapping", "guard", "Key",
    "Tuple", "Atom", "Email", "URL",
)

_empty = object()
MAX_EMAIL_LEN = 254


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


class TrafaretMeta(type):
    """
    Metaclass for trafarets to make using "|" operator possible not only
    on instances but on classes

    >>> Int | String
    <Or(<Int>, <String>)>
    >>> Int | String | Null
    <Or(<Int>, <String>, <Null>)>
    >>> (Int >> (lambda v: v if v ** 2 > 15 else 0)).check(5)
    5
    """

    def __or__(cls, other):
        return cls() | other

    def __and__(cls, other):
        return cls() & other

    def __rshift__(cls, other):
        return cls() >> other


@py3metafix
class Trafaret(object):
    """
    Base class for trafarets, provides only one method for
    trafaret validation failure reporting
    """

    __metaclass__ = TrafaretMeta

    def check(self, value, convert=True):
        """
        Common logic. In subclasses you need to implement check_value or
        check_and_return.
        """
        if hasattr(self, 'check_value'):
            self.check_value(value)
            return self.converter(value) if convert else value
        if hasattr(self, 'check_and_return'):
            res_value = self.check_and_return(value)
            return self.converter(res_value) if convert else res_value
        cls = "%s.%s" % (type(self).__module__, type(self).__name__)
        raise NotImplementedError("You must implement check_value or"
                                  " check_and_return methods '%s'" % cls)

    def converter(self, value):
        """
        You can change converter with `>>` operator or append method
        """
        return value

    def _failure(self, error=None, value=_empty):
        """
        Shortcut method for raising validation error
        """
        raise DataError(error=error, value=value, trafaret=self)

    @staticmethod
    def _trafaret(trafaret):
        """
        Helper for complex trafarets, takes trafaret instance or class
        and returns trafaret instance
        """
        return ensure_trafaret(trafaret)

    def append(self, converter):
        """
        Appends new converter to list.
        """
        return And(self, converter, disable_old_check_convert=True)

    def __or__(self, other):
        return Or(self, other)

    def __and__(self, other):
        return And(self, other)

    def __rshift__(self, other):
        return And(self, other, disable_old_check_convert=True)

    def __call__(self, val):
        return self.check(val)


def ensure_trafaret(trafaret):
    """
    Helper for complex trafarets, takes trafaret instance or class
    and returns trafaret instance
    """
    if isinstance(trafaret, Trafaret) or inspect.isroutine(trafaret):
        return trafaret
    elif isinstance(trafaret, type):
        if issubclass(trafaret, Trafaret):
            return trafaret()
        else:
            return Type(trafaret)
    else:
        raise RuntimeError("%r should be instance or subclass"
                           " of Trafaret" % trafaret)

class TypeMeta(TrafaretMeta):

    def __getitem__(self, type_):
        return self(type_)


@py3metafix
class TypingTrafaret(Trafaret):
    """A trafaret used for instance type and class inheritance checks."""

    __metaclass__ = TypeMeta

    def __init__(self, type_):
        self.type_ = type_

    def check_value(self, value):
        if not self.typing_checker(value, self.type_):
            self._failure(self.failure_message % self.type_.__name__, value=value)

    def __repr__(self):
        return "<%s(%s)>" % (self.__class__.__name__, self.type_.__name__)


class Subclass(TypingTrafaret):
    """
    >>> Subclass(type)
    <Subclass(type)>
    >>> Subclass[type]
    <Subclass(type)>
    >>> s = Subclass[type]
    >>> s.check(type)
    <type 'type'>
    >>> extract_error(s, object)
    'value is not subclass of type'
    """

    typing_checker = issubclass
    failure_message = "value is not subclass of %s"


class Type(TypingTrafaret):
    """
    >>> Type(int)
    <Type(int)>
    >>> Type[int]
    <Type(int)>
    >>> c = Type[int]
    >>> c.check(1)
    1
    >>> extract_error(c, "foo")
    'value is not int'
    """

    typing_checker = isinstance
    failure_message = "value is not %s"


class Any(Trafaret):
    """
    >>> Any()
    <Any>
    >>> (Any() >> ignore).check(object())
    """

    def check_value(self, value):
        pass

    def __repr__(self):
        return "<Any>"


class OrMeta(TrafaretMeta):
    """
    Allows to use "<<" operator on Or class

    >>> Or << Int << String
    <Or(<Int>, <String>)>
    """

    def __lshift__(cls, other):
        return cls() << other


@py3metafix
class Or(Trafaret):
    """
    >>> nullString = Or(String, Null)
    >>> nullString
    <Or(<String>, <Null>)>
    >>> nullString.check(None)
    >>> nullString.check("test")
    'test'
    >>> extract_error(nullString, 1)
    {0: 'value is not a string', 1: 'value should be None'}
    """

    __metaclass__ = OrMeta
    __slots__ = ['trafarets']

    def __init__(self, *trafarets):
        self.trafarets = list(map(ensure_trafaret, trafarets))

    def check_and_return(self, value):
        errors = []
        for trafaret in self.trafarets:
            try:
                return trafaret.check(value)
            except DataError as e:
                errors.append(e)
        raise DataError(dict(enumerate(errors)), trafaret=self)

    def __lshift__(self, trafaret):
        self.trafarets.append(ensure_trafaret(trafaret))
        return self

    def __or__(self, trafaret):
        self << trafaret
        return self

    def __repr__(self):
        return "<Or(%s)>" % (", ".join(map(repr, self.trafarets)))


class And(Trafaret):
    """
    Will work over trafarets sequentially
    """
    __slots__ = ('trafaret', 'other', 'disable_old_check_convert')

    def __init__(self, trafaret, other, disable_old_check_convert=False):
        self.trafaret = trafaret
        self.other = other
        self.disable_old_check_convert = disable_old_check_convert

    def check_and_return(self, value):
        if isinstance(self.trafaret, Trafaret) and self.disable_old_check_convert:
            res = self.trafaret.check(value, convert=False)
        else:
            res = self.trafaret(value)
        if isinstance(res, DataError):
            raise DataError
        res = self.other(res)
        if isinstance(res, DataError):
            raise DataError
        return res

    # support old code for some deprecation period
    def allow_extra(self, *names, **kw):
        deprecated('Call allow_extra after >> or & operations is deprecated')
        self.trafaret = self.trafaret.allow_extra(*names, **kw)
        return self

    def ignore_extra(self, *names):
        deprecated('Call ignore_extra after >> or & operations is deprecated')
        self.trafaret = self.trafaret.ignore_extra(*names)
        return self

    def __repr__(self):
        return repr(self.trafaret)



class Null(Trafaret):
    """
    >>> Null()
    <Null>
    >>> Null().check(None)
    >>> extract_error(Null(), 1)
    'value should be None'
    """

    def check_value(self, value):
        if value is not None:
            self._failure("value should be None", value=value)

    def __repr__(self):
        return "<Null>"


class Bool(Trafaret):
    """
    >>> Bool()
    <Bool>
    >>> Bool().check(True)
    True
    >>> Bool().check(False)
    False
    >>> extract_error(Bool(), 1)
    'value should be True or False'
    """

    def check_value(self, value):
        if not isinstance(value, bool):
            self._failure("value should be True or False", value=value)

    def __repr__(self):
        return "<Bool>"


class StrBool(Trafaret):
    """
    >>> extract_error(StrBool(), 'aloha')
    "value can't be converted to Bool"
    >>> StrBool().check(1)
    True
    >>> StrBool().check(0)
    False
    >>> StrBool().check('y')
    True
    >>> StrBool().check('n')
    False
    >>> StrBool().check(None)
    False
    >>> StrBool().check('1')
    True
    >>> StrBool().check('0')
    False
    >>> StrBool().check('YeS')
    True
    >>> StrBool().check('No')
    False
    >>> StrBool().check(True)
    True
    >>> StrBool().check(False)
    False
    """

    convertable = ('t', 'true', 'false', 'y', 'n', 'yes', 'no', 'on',
                   '1', '0', 'none')

    def check_value(self, value):
        _value = str(value).strip().lower()
        if _value not in self.convertable:
            self._failure("value can't be converted to Bool", value=value)

    def converter(self, value):
        if value is None:
            return False
        _str = str(value).strip().lower()

        return _str in ('t', 'true', 'y', 'yes', 'on', '1')

    def __repr__(self):
        return "<StrBool>"


class NumberMeta(TrafaretMeta):
    """
    Allows slicing syntax for min and max arguments for
    number trafarets

    >>> Int[1:]
    <Int(gte=1)>
    >>> Int[1:10]
    <Int(gte=1, lte=10)>
    >>> Int[:10]
    <Int(lte=10)>
    >>> Float[1:]
    <Float(gte=1)>
    >>> Int > 3
    <Int(gt=3)>
    >>> 1 < (Float < 10)
    <Float(gt=1, lt=10)>
    >>> (Int > 5).check(10)
    10
    >>> extract_error(Int > 5, 1)
    'value should be greater than 5'
    >>> (Int < 3).check(1)
    1
    >>> extract_error(Int < 3, 3)
    'value should be less than 3'
    """

    def __getitem__(cls, slice_):
        return cls(gte=slice_.start, lte=slice_.stop)

    def __lt__(cls, lt):
        return cls(lt=lt)

    def __gt__(cls, gt):
        return cls(gt=gt)


@py3metafix
class Float(Trafaret):
    """
    >>> Float()
    <Float>
    >>> Float(gte=1)
    <Float(gte=1)>
    >>> Float(lte=10)
    <Float(lte=10)>
    >>> Float(gte=1, lte=10)
    <Float(gte=1, lte=10)>
    >>> Float().check(1.0)
    1.0
    >>> extract_error(Float(), 1 + 3j)
    'value is not float'
    >>> extract_error(Float(), 1)
    1.0
    >>> Float(gte=2).check(3.0)
    3.0
    >>> extract_error(Float(gte=2), 1.0)
    'value is less than 2'
    >>> Float(lte=10).check(5.0)
    5.0
    >>> extract_error(Float(lte=3), 5.0)
    'value is greater than 3'
    >>> Float().check("5.0")
    5.0
    """

    __metaclass__ = NumberMeta

    convertable = str_types + (numbers.Real,)
    value_type = float

    def __init__(self, gte=None, lte=None, gt=None, lt=None):
        self.gte = gte
        self.lte = lte
        self.gt = gt
        self.lt = lt

    def _converter(self, value):
        if not isinstance(value, self.convertable):
            self._failure('value is not %s' % self.value_type.__name__, value=value)
        try:
            return self.value_type(value)
        except ValueError:
            self._failure(
                "value can't be converted to %s" % self.value_type.__name__,
                value=value
            )

    def check_and_return(self, val):
        if not isinstance(val, self.value_type):
            value = self._converter(val)
        else:
            value = val
        if self.gte is not None and value < self.gte:
            self._failure("value is less than %s" % self.gte, value=val)
        if self.lte is not None and value > self.lte:
            self._failure("value is greater than %s" % self.lte, value=val)
        if self.lt is not None and value >= self.lt:
            self._failure("value should be less than %s" % self.lt, value=val)
        if self.gt is not None and value <= self.gt:
            self._failure("value should be greater than %s" % self.gt, value=val)
        return value

    def __lt__(self, lt):
        return type(self)(gte=self.gte, lte=self.lte, gt=self.gt, lt=lt)

    def __gt__(self, gt):
        return type(self)(gte=self.gte, lte=self.lte, gt=gt, lt=self.lt)

    def __repr__(self):
        r = "<%s" % type(self).__name__
        options = []
        for param in ("gte", "lte", "gt", "lt"):
            if getattr(self, param) is not None:
                options.append("%s=%s" % (param, getattr(self, param)))
        if options:
            r += "(%s)" % (", ".join(options))
        r += ">"
        return r


class Int(Float):
    """
    >>> Int()
    <Int>
    >>> Int().check(5)
    5
    >>> extract_error(Int(), 1.1)
    'value is not int'
    >>> extract_error(Int(), 1 + 1j)
    'value is not int'
    """

    value_type = int

    def _converter(self, value):
        if isinstance(value, float):
            if not value.is_integer():
                self._failure('value is not int', value=value)
        return super(Int, self)._converter(value)


class Atom(Trafaret):
    """
    >>> Atom('atom').check('atom')
    'atom'
    >>> extract_error(Atom('atom'), 'molecule')
    "value is not exactly 'atom'"
    """
    __slots__ = ['value']

    def __init__(self, value):
        self.value = value

    def check_value(self, value):
        if self.value != value:
            self._failure("value is not exactly '%s'" % self.value, value=value)


class RegexpRaw(Trafaret):
    """
    Check if given string match given regexp
    """
    __slots__ = ('regexp', 'raw_regexp')

    def __init__(self, regexp):
        self.regexp = re.compile(regexp) if isinstance(regexp, str_types) else regexp
        self.raw_regexp = self.regexp.pattern if self.regexp else None

    def check_and_return(self, value):
        if not isinstance(value, str_types):
            self._failure("value is not a string", value=value)
        match = self.regexp.match(value)
        if not match:
            self._failure('does not match pattern %s' % self.raw_regexp)
        return match

    def __repr__(self):
        return '<Regexp>'


class Regexp(RegexpRaw):
    def check_and_return(self, value):
        return super(Regexp, self).check_and_return(value).group()


class String(Trafaret):
    """
    >>> String()
    <String>
    >>> String(allow_blank=True)
    <String(blank)>
    >>> String().check("foo")
    'foo'
    >>> extract_error(String(), "")
    'blank value is not allowed'
    >>> String(allow_blank=True).check("")
    ''
    >>> extract_error(String(), 1)
    'value is not a string'
    >>> String(regex='\w+').check('wqerwqer')
    'wqerwqer'
    >>> String(allow_blank=True, regex='\w+').check('')
    ''
    >>> extract_error(String(regex='^\w+$'), 'wqe rwqer')
    "value does not match pattern: '^\\\\\\\\w+$'"
    >>> String(min_length=2, max_length=3).check('123')
    '123'
    >>> extract_error(String(min_length=2, max_length=6), '1')
    'String is shorter than 2 characters'
    >>> extract_error(String(min_length=2, max_length=6), '1234567')
    'String is longer than 6 characters'
    >>> String(min_length=2, max_length=6, allow_blank=True)
    Traceback (most recent call last):
    ...
    AssertionError: Either allow_blank or min_length should be specified, not both
    >>> String(min_length=0, max_length=6, allow_blank=True).check('123')
    '123'
    """

    def __init__(self, allow_blank=False, regex=None, min_length=None, max_length=None):
        assert not (allow_blank and min_length), \
            "Either allow_blank or min_length should be specified, not both"
        self.allow_blank = allow_blank
        self.regex = re.compile(regex) if isinstance(regex, str_types) else regex
        if self.regex is not None:
            deprecated('Deprecated, use Regexp or RegexpRaw instead')
        self.min_length = min_length
        self.max_length = max_length
        self._raw_regex = self.regex.pattern if self.regex else None

    def check_and_return(self, value):
        if not isinstance(value, str_types):
            self._failure("value is not a string", value=value)
        if not self.allow_blank and len(value) == 0:
            self._failure("blank value is not allowed", value=value)
        elif self.allow_blank and len(value) == 0:
            return value
        if self.min_length is not None and len(value) < self.min_length:
            self._failure('String is shorter than %s characters' % self.min_length, value=value)
        if self.max_length is not None and len(value) > self.max_length:
            self._failure('String is longer than %s characters' % self.max_length, value=value)
        if self.regex is not None:
            match = self.regex.match(value)
            if not match:
                self._failure("value does not match pattern: %s" % repr(self._raw_regex), value=value)
            return match
        return value

    def converter(self, value):
        if isinstance(value, str_types):
            return value
        return value.group()

    def __repr__(self):
        return "<String(blank)>" if self.allow_blank else "<String>"


class Email(String):
    """
    >>> Email().check('someone@example.net')
    'someone@example.net'
    >>> extract_error(Email(),'someone@example') # try without domain-part
    'value is not a valid email address'
    >>> str(Email().check('someone@пример.рф')) # try with `idna` encoding
    'someone@xn--e1afmkfd.xn--p1ai'
    >>> (Email() >> (lambda m: m.groupdict()['domain'])).check('someone@example.net')
    'example.net'
    >>> extract_error(Email(), 'foo')
    'value is not a valid email address'
    >>> extract_error(Email(), 'f' * 10000 + '@correct.domain.edu')
    'value is not a valid email address'
    >>> extract_error(Email(), 'f' * 248 + '@x.edu') == 'f' * 248 + '@x.edu'
    True
    """

    regex = re.compile(
        r"(?P<name>^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"' # quoted-string
        r')@(?P<domain>(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)$)'  # domain
        r'|\[(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\]$', re.IGNORECASE)  # literal form, ipv4 address (SMTP 4.1.3)

    def __init__(self, allow_blank=False):
        super(Email, self).__init__(allow_blank=allow_blank,
                                    regex=self.regex,
                                    max_length=MAX_EMAIL_LEN)

    def check_and_return(self, value):
        try:
            return super(Email, self).check_and_return(value)
        except DataError:
            if value and isinstance(value, str_types):
                if isinstance(value, bytes):
                    decoded = value.decode('utf-8')
                else:
                    decoded = value
            else:
                raise
            # Trivial case failed. Try for possible IDN domain-part
            if decoded and '@' in decoded:
                parts = decoded.split('@')
                try:
                    parts[-1] = parts[-1].encode('idna').decode('ascii')
                except UnicodeError:
                    pass
                else:
                    try:
                        return super(Email, self).check_and_return('@'.join(parts))
                    except DataError:
                        # Will fail with main error
                        pass
        self._failure('value is not a valid email address', value=value)

    def __repr__(self):
        return '<Email>'


class URL(String):
    """
    >>> URL().check('http://example.net/resource/?param=value#anchor')
    'http://example.net/resource/?param=value#anchor'
    >>> str(URL().check('http://пример.рф/resource/?param=value#anchor'))
    'http://xn--e1afmkfd.xn--p1ai/resource/?param=value#anchor'
    """

    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        r'(?:\S+(?::\S*)?@)?'  # user and password
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-_]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    min_length = None
    max_length = None

    def __init__(self, allow_blank=False):
        super(URL, self).__init__(allow_blank=allow_blank, regex=self.regex)

    def check_and_return(self, value):
        try:
            return super(URL, self).check_and_return(value)
        except DataError:
            # Trivial case failed. Try for possible IDN domain-part
            if value:
                if isinstance(value, bytes):
                    decoded = value.decode('utf-8')
                else:
                    decoded = value
                scheme, netloc, path, query, fragment = urlparse.urlsplit(decoded)
                try:
                    netloc = netloc.encode('idna').decode('ascii') # IDN -> ACE
                except UnicodeError: # invalid domain part
                    pass
                else:
                    url = urlparse.urlunsplit((scheme, netloc, path, query, fragment))
                    try:
                        return super(URL, self).check_and_return(url)
                    except DataError:
                        # Will fail with main error
                        pass
        self._failure('value is not URL', value=value)

    def __repr__(self):
        return '<URL>'


class IPv4(Regexp):
    """
    >>> IPv4().check('127.0.0.1')
    '127.0.0.1'
    """

    regex = re.compile(
        r'^((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])$',  # noqa
    )

    def __init__(self):
        super(IPv4, self).__init__(self.regex)

    def check_and_return(self, value):
        try:
            return super(IPv4, self).check_and_return(value)
        except DataError:
            self._failure('value is not IPv4 address')

    def __repr__(self):
        return '<IPv4>'


class IPv6(Regexp):
    """
    >>> IPv6().check('2001:0db8:0000:0042:0000:8a2e:0370:7334')
    '2001:0db8:0000:0042:0000:8a2e:0370:7334'
    """

    regex = re.compile(
        r'^('
        r'(::)|'
        r'(::[0-9a-f]{1,4})|'
        r'([0-9a-f]{1,4}:){7,7}[0-9a-f]{1,4}|'
        r'([0-9a-f]{1,4}:){1,7}:|'
        r'([0-9a-f]{1,4}:){1,6}:[0-9a-f]{1,4}|'
        r'([0-9a-f]{1,4}:){1,5}(:[0-9a-f]{1,4}){1,2}|'
        r'([0-9a-f]{1,4}:){1,4}(:[0-9a-f]{1,4}){1,3}|'
        r'([0-9a-f]{1,4}:){1,3}(:[0-9a-f]{1,4}){1,4}|'
        r'([0-9a-f]{1,4}:){1,2}(:[0-9a-f]{1,4}){1,5}|'
        r'[0-9a-f]{1,4}:((:[0-9a-f]{1,4}){1,6})|'
        r':((:[0-9a-f]{1,4}){1,7}:)|'
        r'fe80:(:[0-9a-f]{0,4}){0,4}%[0-9a-z]{1,}|'
        r'::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|'  # noqa
        r'([0-9a-f]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])'  # noqa
        r')$',
        re.IGNORECASE,
    )

    def __init__(self):
        super(IPv6, self).__init__(self.regex)

    def check_and_return(self, value):
        try:
            return super(IPv6, self).check_and_return(value)
        except DataError:
            self._failure('value is not IPv6 address')

    def __repr__(self):
        return '<IPv6>'


class SquareBracketsMeta(TrafaretMeta):
    """
    Allows usage of square brackets for List initialization

    >>> List[Int]
    <List(<Int>)>
    >>> List[Int, 1:]
    <List(min_length=1 | <Int>)>
    >>> List[:10, Int]
    <List(max_length=10 | <Int>)>
    >>> List[1:10]
    Traceback (most recent call last):
    ...
    RuntimeError: Trafaret is required for List initialization
    """

    def __getitem__(self, args):
        slice_ = None
        trafaret = None
        if not isinstance(args, tuple):
            args = (args, )
        for arg in args:
            if isinstance(arg, slice):
                slice_ = arg
            elif isinstance(arg, Trafaret) or issubclass(arg, Trafaret) \
                 or isinstance(arg, type):
                trafaret = arg
        if not trafaret:
            raise RuntimeError("Trafaret is required for List initialization")
        if slice_:
            return self(trafaret, min_length=slice_.start or 0,
                                  max_length=slice_.stop)
        return self(trafaret)


@py3metafix
class List(Trafaret):
    """
    >>> List(Int)
    <List(<Int>)>
    >>> List(Int, min_length=1)
    <List(min_length=1 | <Int>)>
    >>> List(Int, min_length=1, max_length=10)
    <List(min_length=1, max_length=10 | <Int>)>
    >>> extract_error(List(Int), 1)
    'value is not a list'
    >>> List(Int).check([1, 2, 3])
    [1, 2, 3]
    >>> List(String).check(["foo", "bar", "spam"])
    ['foo', 'bar', 'spam']
    >>> extract_error(List(Int), [1, 2, 1 + 3j])
    {2: 'value is not int'}
    >>> List(Int, min_length=1).check([1, 2, 3])
    [1, 2, 3]
    >>> extract_error(List(Int, min_length=1), [])
    'list length is less than 1'
    >>> List(Int, max_length=2).check([1, 2])
    [1, 2]
    >>> extract_error(List(Int, max_length=2), [1, 2, 3])
    'list length is greater than 2'
    >>> extract_error(List(Int), ["a"])
    {0: "value can't be converted to int"}
    """

    __metaclass__ = SquareBracketsMeta
    __slots__ = ['trafaret', 'min_length', 'max_length']

    def __init__(self, trafaret, min_length=0, max_length=None):
        self.trafaret = ensure_trafaret(trafaret)
        self.min_length = min_length
        self.max_length = max_length

    def check_and_return(self, value):
        if not isinstance(value, list):
            self._failure("value is not a list", value=value)
        if len(value) < self.min_length:
            self._failure("list length is less than %s" % self.min_length, value=value)
        if self.max_length is not None and len(value) > self.max_length:
            self._failure("list length is greater than %s" % self.max_length, value=value)
        lst = []
        errors = {}
        for index, item in enumerate(value):
            try:
                lst.append(self.trafaret.check(item))
            except DataError as err:
                errors[index] = err
        if errors:
            raise DataError(error=errors, trafaret=self)
        return lst

    def __repr__(self):
        r = "<List("
        options = []
        if self.min_length:
            options.append("min_length=%s" % self.min_length)
        if self.max_length:
            options.append("max_length=%s" % self.max_length)
        r += ", ".join(options)
        if options:
            r += " | "
        r += repr(self.trafaret)
        r += ")>"
        return r


class Tuple(Trafaret):
    """
    Tuple checker can be used to check fixed tuples, like (Int, Int, String).

    >>> t = Tuple(Int, Int, String)
    >>> t.check([3, 4, '5'])
    (3, 4, '5')
    >>> extract_error(t, [3, 4, 5])
    {2: 'value is not a string'}
    >>> t
    <Tuple(<Int>, <Int>, <String>)>
    """
    __slots__ = ['trafarets', 'length']

    def __init__(self, *args):
        self.trafarets = list(map(ensure_trafaret, args))
        self.length = len(self.trafarets)

    def check_and_return(self, value):
        try:
            value = tuple(value)
        except TypeError:
            self._failure('value must be convertable to tuple', value=value)
        if len(value) != self.length:
            self._failure('value must contain %s items' % self.length, value=value)
        result = []
        errors = {}
        for idx, (item, trafaret) in enumerate(zip(value, self.trafarets)):
            try:
                result.append(trafaret.check(item))
            except DataError as err:
                errors[idx] = err
        if errors:
            self._failure(errors, value=value)
        return tuple(result)

    def __repr__(self):
        return '<Tuple(' + ', '.join(repr(t) for t in self.trafarets) + ')>'


class Key(object):
    """
    Helper class for Dict.

    It gets ``name``, and provides method ``extract(data)`` that extract key value
    from data through mapping ``get`` method.
    Key `__call__` method yields ``(key name, Maybe(DataError), [touched keys])`` triples.

    You can redefine ``get_data(data, default)`` method in subclassed ``Key`` if you want to use something other
    then ``.get(...)`` method.

    Like this for the aiohttp MultiDict::

        class MDKey(t.Key):
            def get_data(data, default):
                return data.get_all(self.name, default)
    """
    __slots__ = ['name', 'to_name', 'default', 'optional', 'trafaret']

    def __init__(self, name, default=_empty, optional=False, to_name=None, trafaret=None):
        self.name = name
        self.to_name = to_name
        self.default = default
        self.optional = optional
        self.trafaret = trafaret or Any()

    def __call__(self, data):
        if self.name in data or self.default is not _empty:
            if callable(self.default):
                default = self.default()
            else:
                default = self.default
            yield (
                self.get_name(),
                catch_error(self.trafaret, self.get_data(data, default)),
                (self.name,)
            )
            return

        if not self.optional:
            yield self.name, DataError(error='is required'), (self.name,)

    def get_data(self, data, default):
        return data.get(self.name, default)

    def keys_names(self):
        yield self.name

    def set_trafaret(self, trafaret):
        self.trafaret = ensure_trafaret(trafaret)
        return self

    def __rshift__(self, name):
        self.to_name = name
        return self

    def get_name(self):
        return self.to_name or self.name

    def make_optional(self):
        self.optional = True

    def __repr__(self):
        return '<%s "%s"%s>' % (self.__class__.__name__, self.name,
           ' to "%s"' % self.to_name if getattr(self, 'to_name', False) else '')


class Dict(Trafaret):
    """
    >>> trafaret = Dict(foo=Int, bar=String) >> ignore
    >>> trafaret.check({"foo": 1, "bar": "spam"})
    >>> extract_error(trafaret, {"foo": 1, "bar": 2})
    {'bar': 'value is not a string'}
    >>> extract_error(trafaret, {"foo": 1})
    {'bar': 'is required'}
    >>> extract_error(trafaret, {"foo": 1, "bar": "spam", "eggs": None})
    {'eggs': 'eggs is not allowed key'}
    >>> trafaret.allow_extra("eggs")
    <Dict(extras=(eggs) | bar=<String>, foo=<Int>)>
    >>> trafaret.check({"foo": 1, "bar": "spam", "eggs": None})
    >>> trafaret.check({"foo": 1, "bar": "spam"})
    >>> extract_error(trafaret, {"foo": 1, "bar": "spam", "ham": 100})
    {'ham': 'ham is not allowed key'}
    >>> trafaret.allow_extra("*")
    <Dict(any, extras=(eggs) | bar=<String>, foo=<Int>)>
    >>> trafaret.check({"foo": 1, "bar": "spam", "ham": 100})
    >>> trafaret.check({"foo": 1, "bar": "spam", "ham": 100, "baz": None})
    >>> extract_error(trafaret, {"foo": 1, "ham": 100, "baz": None})
    {'bar': 'is required'}
    >>> trafaret = Dict({Key('bar', optional=True): String}, foo=Int)
    >>> trafaret.allow_extra("*")
    <Dict(any | bar=<String>, foo=<Int>)>
    >>> _dd(trafaret.check({"foo": 1, "ham": 100, "baz": None}))
    "{'baz': None, 'foo': 1, 'ham': 100}"
    >>> _dd(extract_error(trafaret, {"bar": 1, "ham": 100, "baz": None}))
    "{'bar': 'value is not a string', 'foo': 'is required'}"
    >>> extract_error(trafaret, {"foo": 1, "bar": 1, "ham": 100, "baz": None})
    {'bar': 'value is not a string'}
    >>> trafaret = Dict({Key('bar', default='nyanya') >> 'baz': String}, foo=Int)
    >>> _dd(trafaret.check({'foo': 4}))
    "{'baz': 'nyanya', 'foo': 4}"
    >>> _ = trafaret.ignore_extra('fooz')
    >>> _dd(trafaret.check({'foo': 4, 'fooz': 5}))
    "{'baz': 'nyanya', 'foo': 4}"
    >>> _ = trafaret.ignore_extra('*')
    >>> _dd(trafaret.check({'foo': 4, 'foor': 5}))
    "{'baz': 'nyanya', 'foo': 4}"
    """
    __slots__ = ['extras', 'extras_trafaret', 'allow_any', 'ignore', 'ignore_any', 'keys']

    def __init__(self, *args, **trafarets):
        if args and isinstance(args[0], AbcMapping):
            keys = args[0]
            args = args[1:]
        else:
            keys = {}
        if any(not callable(key) for key in args):
            raise RuntimeError('Keys in single attributes must be callables')

        # extra
        allow_extra = trafarets.pop('allow_extra', [])
        allow_extra_trafaret = trafarets.pop('allow_extra_trafaret', Any)
        self.extras_trafaret = ensure_trafaret(allow_extra_trafaret)
        self.allow_any = '*' in allow_extra
        self.extras = [name for name in allow_extra if name != '*']
        # ignore
        ignore_extra = trafarets.pop('ignore_extra', [])
        self.ignore_any = '*' in ignore_extra
        self.ignore = [name for name in ignore_extra if name != '*']

        self.keys = list(args)
        for key, trafaret in itertools.chain(trafarets.items(), keys.items()):
            key_ = Key(key) if isinstance(key, str_types) else key
            key_.set_trafaret(ensure_trafaret(trafaret))
            self.keys.append(key_)

    def allow_extra(self, *names, **kw):
        trafaret = kw.get('trafaret', Any)
        for name in names:
            if name == "*":
                self.allow_any = True
            else:
                self.extras.append(name)
        self.extras_trafaret = ensure_trafaret(trafaret)
        return self

    def ignore_extra(self, *names):
        for name in names:
            if name == "*":
                self.ignore_any = True
            else:
                self.ignore.append(name)
        return self

    def make_optional(self, *args):
        for key in self.keys:
            if key.name in args or '*' in args:
                key.make_optional()
        return self

    def check_and_return(self, value):
        if not isinstance(value, AbcMapping):
            self._failure("value is not a dict", value=value)
        collect = {}
        errors = {}
        touched_names = []
        for key in self.keys:
            if callable(key):
                for k, v, names in key(value):
                    if isinstance(v, DataError):
                        errors[k] = v
                    else:
                        collect[k] = v
                    touched_names.extend(names)
            else:
                deprecated('Old pop based Keys subclasses deprecated. See README')
                value_keys = set(value.keys())
                for k, v in key.pop(value):
                    if isinstance(v, DataError):
                        errors[k] = v
                    else:
                        collect[k] = v
                touched_names.extend(value_keys - set(value.keys()))

        if not self.ignore_any:
            for key in value:
                if key in touched_names:
                    continue
                if key in self.ignore:
                    continue
                if not self.allow_any and key not in self.extras:
                    errors[key] = DataError("%s is not allowed key" % key)
                elif key in collect:
                    errors[key] = DataError("%s key was shadowed" % key)
                else:
                    try:
                        collect[key] = self.extras_trafaret(value[key])
                    except DataError as de:
                        errors[key] = de
        if errors:
            raise DataError(error=errors, trafaret=self)
        return collect

    def keys_names(self):
        for key in self.keys:
            for k in key.keys_names():
                yield k

    def __repr__(self):
        r = "<Dict("
        options = []
        if self.allow_any:
            options.append("any")
        if self.ignore:
            options.append("ignore=(%s)" % (", ".join(self.ignore)))
        if self.extras:
            options.append("extras=(%s)" % (", ".join(self.extras)))
        r += ", ".join(options)
        if options:
            r += " | "
        options = []
        for key in sorted(self.keys, key=lambda k: k.name):
            options.append("%s=%r" % (key.name, key.trafaret))
        r += ", ".join(options)
        r += ")>"
        return r

    def merge(self, other):
        """
        Extends one Dict with other Dict Key`s or Key`s list,
        or dict instance supposed for Dict
        """
        if not isinstance(other, (Dict, list, dict)):
            raise TypeError('You must merge Dict only with Dict'
                            ' or list of Keys')
        if isinstance(other, dict):
            other = Dict(other)
        if isinstance(other, Dict):
            other_keys_names = other.keys_names()
            other_keys = other.keys
        else:
            other_keys_names = [
                key_name
                for key in other
                for key_name in key.keys_names()
            ]
            other_keys = other
        if set(self.keys_names()) & set(other_keys_names):
            raise ValueError('Merged dicts should have '
                            'no interlapping keys')
        if (
            set(key.get_name() for key in self.keys)
            & set(key.get_name() for key in other_keys)
        ):
            raise ValueError('Merged dicts should have '
                            'no interlapping keys to names')
        new_trafaret = self.__class__()
        new_trafaret.keys = self.keys + other_keys
        return new_trafaret

    __add__ = merge


def DictKeys(keys):
    """
    Checks if dict has all given keys

    :param keys:
    :type keys:

    >>> _dd(DictKeys(['a','b']).check({'a':1,'b':2,}))
    "{'a': 1, 'b': 2}"
    >>> extract_error(DictKeys(['a','b']), {'a':1,'b':2,'c':3,})
    {'c': 'c is not allowed key'}
    >>> extract_error(DictKeys(['key','key2']), {'key':'val'})
    {'key2': 'is required'}
    """
    def MissingKey(val):
        raise DataError('%s is not in Dict' % val)

    req = [(Key(key), Any) for key in keys]
    return Dict(dict(req))


class Mapping(Trafaret):
    """
    Mapping gets two trafarets as arguments, one for key and one for value,
    like `Mapping(t.Int, t.List(t.Str))`.
    """
    __slots__ = ['key', 'value']

    def __init__(self, key, value):
        self.key = ensure_trafaret(key)
        self.value = ensure_trafaret(value)

    def check_and_return(self, mapping):
        if not isinstance(mapping, dict):
            self._failure("value is not a dict", value=mapping)
        checked_mapping = {}
        errors = {}
        for key, value in mapping.items():
            pair_errors = {}
            try:
                checked_key = self.key.check(key)
            except DataError as err:
                pair_errors['key'] = err
            try:
                checked_value = self.value.check(value)
            except DataError as err:
                pair_errors['value'] = err
            if pair_errors:
                errors[key] = DataError(error=pair_errors)
            else:
                checked_mapping[checked_key] = checked_value
        if errors:
            raise DataError(error=errors, trafaret=self)
        return checked_mapping

    def __repr__(self):
        return "<Mapping(%r => %r)>" % (self.key, self.value)


class Enum(Trafaret):
    """
    >>> trafaret = Enum("foo", "bar", 1) >> ignore
    >>> trafaret
    <Enum('foo', 'bar', 1)>
    >>> trafaret.check("foo")
    >>> trafaret.check(1)
    >>> extract_error(trafaret, 2)
    "value doesn't match any variant"
    """
    __slots__ = ['variants']

    def __init__(self, *variants):
        self.variants = variants[:]

    def check_value(self, value):
        if value not in self.variants:
            self._failure("value doesn't match any variant", value=value)

    def __repr__(self):
        return "<Enum(%s)>" % (", ".join(map(repr, self.variants)))


class Callable(Trafaret):
    """
    >>> (Callable() >> ignore).check(lambda: 1)
    >>> extract_error(Callable(), 1)
    'value is not callable'
    """

    def check_value(self, value):
        if not callable(value):
            self._failure("value is not callable", value=value)

    def __repr__(self):
        return "<Callable>"


class Call(Trafaret):
    """
    >>> def validator(value):
    ...     if value != "foo":
    ...         return DataError("I want only foo!")
    ...     return 'foo'
    ...
    >>> trafaret = Call(validator)
    >>> trafaret
    <Call(validator)>
    >>> trafaret.check("foo")
    'foo'
    >>> extract_error(trafaret, "bar")
    'I want only foo!'
    """
    __slots__ = ['fn']

    def __init__(self, fn):
        if not callable(fn):
            raise RuntimeError("Call argument should be callable")
        if py3:
            argspec = inspect.getfullargspec(fn)
        else:
            argspec = inspect.getargspec(fn)
        if len(argspec.args) - len(argspec.defaults or []) > 1:
            raise RuntimeError("Call argument should be"
                               " one argument function")
        self.fn = fn

    def check_and_return(self, value):
        res = self.fn(value)
        if isinstance(res, DataError):
            raise res
        else:
            return res

    def __repr__(self):
        return "<Call(%s)>" % self.fn.__name__


class Forward(Trafaret):
    """
    >>> node = Forward()
    >>> node << Dict(name=String, children=List[node])
    >>> node
    <Forward(<Dict(children=<List(<recur>)>, name=<String>)>)>
    >>> node.check({"name": "foo", "children": []}) == {'children': [], 'name': 'foo'}
    True
    >>> extract_error(node, {"name": "foo", "children": [1]})
    {'children': {0: 'value is not a dict'}}
    >>> node.check({"name": "foo", "children": [ \
                        {"name": "bar", "children": []} \
                     ]}) == {'children': [{'children': [], 'name': 'bar'}], 'name': 'foo'}
    True
    >>> empty_node = Forward()
    >>> empty_node
    <Forward(None)>
    >>> extract_error(empty_node, 'something')
    'trafaret not set yet'
    """

    def __init__(self):
        self.trafaret = None
        self._recur_repr = False

    def __lshift__(self, trafaret):
        self.provide(trafaret)

    def provide(self, trafaret):
        if self.trafaret:
            raise RuntimeError("trafaret for Forward is already specified")
        self.trafaret = ensure_trafaret(trafaret)

    def check_and_return(self, value):
        if self.trafaret is None:
            self._failure('trafaret not set yet', value=value)
        return self.trafaret.check(value)

    def __repr__(self):
        # XXX not threadsafe
        if self._recur_repr:
            return "<recur>"
        self._recur_repr = True
        r = "<Forward(%r)>" % self.trafaret
        self._recur_repr = False
        return r


class GuardError(DataError):
    """
    Raised when guarded function gets invalid arguments,
    inherits error message from corresponding DataError
    """

    pass


def guard(trafaret=None, **kwargs):
    """
    Decorator for protecting function with trafarets

    >>> @guard(a=String, b=Int, c=String)
    ... def fn(a, b, c="default"):
    ...     '''docstring'''
    ...     return (a, b, c)
    ...
    >>> fn.__module__ = None
    >>> help(fn)
    Help on function fn:
    <BLANKLINE>
    fn(*args, **kwargs)
        guarded with <Dict(a=<String>, b=<Int>, c=<String>)>
    <BLANKLINE>
        docstring
    <BLANKLINE>
    >>> fn("foo", 1)
    ('foo', 1, 'default')
    >>> extract_error(fn, "foo", 1, 2)
    {'c': 'value is not a string'}
    >>> extract_error(fn, "foo")
    {'b': 'is required'}
    >>> g = guard(Dict())
    >>> c = Forward()
    >>> c << Dict(name=str, children=List[c])
    >>> g = guard(c)
    >>> g = guard(Int())
    Traceback (most recent call last):
    ...
    RuntimeError: trafaret should be instance of Dict or Forward
    """
    if trafaret and not isinstance(trafaret, Dict) and \
                    not isinstance(trafaret, Forward):
        raise RuntimeError("trafaret should be instance of Dict or Forward")
    elif trafaret and kwargs:
        raise RuntimeError("choose one way of initialization,"
                           " trafaret or kwargs")
    if not trafaret:
        trafaret = Dict(**kwargs)

    def wrapper(fn):
        if py3:
            argspec = inspect.getfullargspec(fn)
        else:
            argspec = inspect.getargspec(fn)

        @functools.wraps(fn)
        def decor(*args, **kwargs):
            fnargs = argspec.args
            if fnargs[0] in ['self', 'cls']:
                obj = args[0]
                fnargs = fnargs[1:]
                checkargs = args[1:]
            else:
                obj = None
                checkargs = args

            try:
                call_args = dict(
                    itertools.chain(zip(fnargs, checkargs), kwargs.items())
                )
                for name, default in zip(reversed(fnargs),
                                         reversed(argspec.defaults or ())):
                    if name not in call_args:
                        call_args[name] = default
                converted = trafaret.check(call_args)
            except DataError as err:
                raise GuardError(error=err.error)
            return fn(obj, **converted) if obj else fn(**converted)
        decor.__doc__ = "guarded with %r\n\n" % trafaret + (decor.__doc__ or "")
        return decor
    return wrapper


def ignore(val):
    """
    Stub to ignore value from trafaret
    Use it like:

    >>> a = Int >> ignore
    >>> a.check(7)
    """
    pass


def catch(checker, *a, **kw):
    """
    Helper for tests - catch error and return it as dict
    """

    try:
        if hasattr(checker, 'check'):
            return checker.check(*a, **kw)
        elif callable(checker):
            return checker(*a, **kw)
    except DataError as error:
        return error

catch_error = catch


def extract_error(checker, *a, **kw):
    """
    Helper for tests - catch error and return it as dict
    """

    res = catch_error(checker, *a, **kw)
    if isinstance(res, DataError):
        return res.as_dict()
    return res


class MissingContribModuleStub(types.ModuleType):
    """
    Preserves initial exception to be raised on module access
    """

    def __init__(self, entrypoint, orig):
        self.orig = orig
        self.entrypoint = entrypoint

    def __getattr__(self, item):
        raise self.orig

    def __call__(self, *args, **kwargs):
        raise self.orig

    @property
    def __name__(self):
        return self.entrypoint.name.lstrip('.')
