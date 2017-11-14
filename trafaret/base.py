# -*- coding: utf-8 -*-

import functools
import itertools
import numbers
import warnings
from collections import Mapping as AbcMapping
from .lib import (
    py3,
    py36,
    py3metafix,
    getargspec,
    get_callable_argspec,
    call_with_context_if_support,
    _empty,
)
from .dataerror import DataError


if py36:
    from .async import (
        TrafaretAsyncMixin,
        OrAsyncMixin,
        AndAsyncMixin,
        ListAsyncMixin,
        TupleAsyncMixin,
        MappingAsyncMixin,
        CallAsyncMixin,
        ForwardAsyncMixin,
        DictAsyncMixin,
        KeyAsyncMixin,
    )
else:
    class EmptyMixin(object):
        pass
    TrafaretAsyncMixin = EmptyMixin
    OrAsyncMixin = EmptyMixin
    AndAsyncMixin = EmptyMixin
    ListAsyncMixin = EmptyMixin
    TupleAsyncMixin = EmptyMixin
    MappingAsyncMixin = EmptyMixin
    CallAsyncMixin = EmptyMixin
    ForwardAsyncMixin = EmptyMixin
    DictAsyncMixin = EmptyMixin
    KeyAsyncMixin = EmptyMixin


# Python3 support
if py3:
    str_types = (str, bytes)
    unicode = str
    BYTES_TYPE = bytes
else:
    try:
        from future_builtins import map
    except ImportError:
        # Support for GAE runner
        from itertools import imap as map
    str_types = (basestring,)  # noqa
    BYTES_TYPE = str


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
class Trafaret(TrafaretAsyncMixin):
    """
    Base class for trafarets, provides only one method for
    trafaret validation failure reporting
    """

    __metaclass__ = TrafaretMeta

    def check(self, value, context=None):
        """
        Common logic. In subclasses you need to implement check_value or
        check_and_return.
        """
        if hasattr(self, 'transform'):
            return self.transform(value, context=context)
        elif hasattr(self, 'check_value'):
            self.check_value(value)
            return value
        elif hasattr(self, 'check_and_return'):
            return self.check_and_return(value)
        else:
            cls = "{}.{}".format(
                type(self).__module__,
                type(self).__name__,
            )
            raise NotImplementedError(
                "You must implement check_value or"
                " check_and_return methods '%s'" % cls
            )

    def _failure(self, error=None, value=_empty):
        """
        Shortcut method for raising validation error
        """
        raise DataError(error=error, value=value, trafaret=self)

    def append(self, other):
        """
        Appends new converter to list.
        """
        return And(self, other)

    def __or__(self, other):
        return Or(self, other)

    def __and__(self, other):
        return And(self, other)

    def __rshift__(self, other):
        return And(self, other)

    def __call__(self, val, context=None):
        return self.check(val, context=context)


class OnError(Trafaret):
    def __init__(self, trafaret, message):
        self.trafaret = ensure_trafaret(trafaret)
        self.message = message

    def transform(self, value, context=None):
        try:
            return self.trafaret(value, context=context)
        except DataError:
            raise DataError(self.message, value=value)


def ensure_trafaret(trafaret):
    """
    Helper for complex trafarets, takes trafaret instance or class
    and returns trafaret instance
    """
    if isinstance(trafaret, Trafaret):
        return trafaret
    elif isinstance(trafaret, type):
        if issubclass(trafaret, Trafaret):
            return trafaret()
        # str, int, float are classes, but its appropriate to use them
        # as trafaret functions
        return Call(lambda val: trafaret(val))
    elif callable(trafaret):
        return Call(trafaret)
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


@py3metafix
class Or(Trafaret, OrAsyncMixin):
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

    __slots__ = ['trafarets']

    def __init__(self, *trafarets):
        self.trafarets = list(map(ensure_trafaret, trafarets))

    def transform(self, value, context=None):
        errors = []
        for trafaret in self.trafarets:
            try:
                return trafaret(value, context=context)
            except DataError as e:
                errors.append(e)
        raise DataError(dict(enumerate(errors)), trafaret=self)

    def __repr__(self):
        return "<Or(%s)>" % (", ".join(map(repr, self.trafarets)))


class And(Trafaret, AndAsyncMixin):
    """
    Will work over trafarets sequentially
    """
    __slots__ = ('trafaret', 'other', 'disable_old_check_convert')

    def __init__(self, trafaret, other):
        self.trafaret = ensure_trafaret(trafaret)
        self.other = ensure_trafaret(other)

    def transform(self, value, context=None):
        res = self.trafaret(value, context=context)
        if isinstance(res, DataError):
            raise DataError
        res = self.other(res, context=context)
        if isinstance(res, DataError):
            raise res
        return res

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

    convertable = ('t', 'true', 'false', 'y', 'n', 'yes', 'no', 'on', 'off',
                   '1', '0', 'none')

    def check_and_return(self, value):
        _value = str(value).strip().lower()
        if _value not in self.convertable:
            self._failure("value can't be converted to Bool", value=value)
        return _value in ('t', 'true', 'y', 'yes', 'on', '1')

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
class FloatRaw(Trafaret):
    """
    Tests that value is a float or a string that is convertable to float.

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

    def _check(self, data):
        if not isinstance(data, self.value_type):
            value = self._converter(data)
        else:
            value = data
        if self.gte is not None and value < self.gte:
            self._failure("value is less than %s" % self.gte, value=data)
        if self.lte is not None and value > self.lte:
            self._failure("value is greater than %s" % self.lte, value=data)
        if self.lt is not None and value >= self.lt:
            self._failure("value should be less than %s" % self.lt, value=data)
        if self.gt is not None and value <= self.gt:
            self._failure("value should be greater than %s" % self.gt, value=data)
        return value

    def check_and_return(self, data):
        self._check(data)
        return data

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


class Float(FloatRaw):
    """Checks that value is a float.
    Or if value is a string converts this string to float
    """
    def check_and_return(self, data):
        return self._check(data)


class IntRaw(FloatRaw):
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
        return super(IntRaw, self)._converter(value)


class Int(IntRaw):
    def check_and_return(self, data):
        return self._check(data)


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

    def __init__(self, allow_blank=False, min_length=None, max_length=None):
        assert not (allow_blank and min_length), \
            "Either allow_blank or min_length should be specified, not both"
        self.allow_blank = allow_blank
        self.min_length = min_length
        self.max_length = max_length

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
        return value

    def __repr__(self):
        return "<String(blank)>" if self.allow_blank else "<String>"


class Bytes(Trafaret):
    def __init__(self, encoding='utf-8'):
        self.encoding = encoding

    def check_and_return(self, value):
        if not isinstance(value, BYTES_TYPE):
            self._failure('Value is not bytes', value=value)
        try:
            return value.decode(self.encoding)
        except UnicodeError:
            raise self._failure('value cannot be decoded with %s encoding' % self.encoding)


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
            elif (
                isinstance(arg, Trafaret)
                or issubclass(arg, Trafaret)
                or isinstance(arg, type)
            ):
                trafaret = arg
        if not trafaret:
            raise RuntimeError("Trafaret is required for List initialization")
        if slice_:
            return self(
                trafaret,
                min_length=slice_.start or 0,
                max_length=slice_.stop,
            )
        return self(trafaret)


@py3metafix
class List(Trafaret, ListAsyncMixin):
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

    def check_common(self, value):
        if not isinstance(value, list):
            self._failure("value is not a list", value=value)
        if len(value) < self.min_length:
            self._failure("list length is less than %s" % self.min_length, value=value)
        if self.max_length is not None and len(value) > self.max_length:
            self._failure("list length is greater than %s" % self.max_length, value=value)

    def transform(self, value, context=None):
        self.check_common(value)
        lst = []
        errors = {}
        for index, item in enumerate(value):
            try:
                lst.append(self.trafaret(item, context=context))
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


class Tuple(Trafaret, TupleAsyncMixin):
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

    def check_common(self, value):
        try:
            value = tuple(value)
        except TypeError:
            self._failure('value must be convertable to tuple', value=value)
        if len(value) != self.length:
            self._failure('value must contain %s items' % self.length, value=value)

    def transform(self, value, context=None):
        self.check_common(value)
        result = []
        errors = {}
        for idx, (item, trafaret) in enumerate(zip(value, self.trafarets)):
            try:
                result.append(trafaret(item, context=context))
            except DataError as err:
                errors[idx] = err
        if errors:
            self._failure(errors, value=value)
        return tuple(result)

    def __repr__(self):
        return '<Tuple(' + ', '.join(repr(t) for t in self.trafarets) + ')>'


class Key(KeyAsyncMixin):
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
        self.trafaret = ensure_trafaret(trafaret) if trafaret else Any()

    def __call__(self, data, context=None):
        if self.name in data or self.default is not _empty:
            if callable(self.default):
                default = self.default()
            else:
                default = self.default
            yield (
                self.get_name(),
                catch_error(self.trafaret, self.get_data(data, default), context=context),
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
        return '<%s "%s"%s>' % (
            self.__class__.__name__,
            self.name,
            ' to "%s"' % self.to_name if getattr(self, 'to_name', False) else '',
        )


class Dict(Trafaret, DictAsyncMixin):
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

    def transform(self, value, context=None):
        if not isinstance(value, AbcMapping):
            self._failure("value is not a dict", value=value)
        collect = {}
        errors = {}
        touched_names = []
        for key in self.keys:
            if not callable(key):
                raise ValueError('Non callable Keys are not supported')
            for k, v, names in call_with_context_if_support(key, value, context=context):
                if isinstance(v, DataError):
                    errors[k] = v
                else:
                    collect[k] = v
                touched_names.extend(names)

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
            raise ValueError(
                'Merged dicts should have no interlapping keys'
            )
        if (
            set(key.get_name() for key in self.keys)
            & set(key.get_name() for key in other_keys)
        ):
            raise ValueError(
                'Merged dicts should have no interlapping keys to names'
            )
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
    req = [(Key(key), Any) for key in keys]
    return Dict(dict(req))


class Mapping(Trafaret, MappingAsyncMixin):
    """
    Mapping gets two trafarets as arguments, one for key and one for value,
    like `Mapping(t.Int, t.List(t.Str))`.
    """
    __slots__ = ['key', 'value']

    def __init__(self, key, value):
        self.key = ensure_trafaret(key)
        self.value = ensure_trafaret(value)

    def transform(self, mapping, context=None):
        if not isinstance(mapping, AbcMapping):
            self._failure("value is not a dict", value=mapping)
        checked_mapping = {}
        errors = {}
        for key, value in mapping.items():
            pair_errors = {}
            try:
                checked_key = self.key(key, context=context)
            except DataError as err:
                pair_errors['key'] = err
            try:
                checked_value = self.value(value, context=context)
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


class Call(Trafaret, CallAsyncMixin):
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
        try:
            argspec = get_callable_argspec(fn)
        except TypeError:
            self.fn = fn
            self.supports_context = False
            return
        args = set(argspec.args)
        self.supports_context = 'context' in args
        if 'context' in args:
            args.remove('context')
        # if len(argspec.args) - len(argspec.defaults or []) > 1:
        #     raise RuntimeError(
        #         "Call argument should be one argument function"
        #     )
        self.fn = fn

    def transform(self, value, context=None):
        if self.supports_context:
            res = self.fn(value, context=context)
        else:
            res = self.fn(value)
        if isinstance(res, DataError):
            raise res
        else:
            return res

    def __repr__(self):
        return "<Call(%s)>" % self.fn.__name__


class Forward(Trafaret, ForwardAsyncMixin):
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

    def transform(self, value, context=None):
        if self.trafaret is None:
            self._failure('trafaret not set yet', value=value)
        return self.trafaret(value, context=context)

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
    if (
        trafaret
        and not isinstance(trafaret, Dict)
        and not isinstance(trafaret, Forward)
    ):
        raise RuntimeError("trafaret should be instance of Dict or Forward")
    elif trafaret and kwargs:
        raise RuntimeError("choose one way of initialization,"
                           " trafaret or kwargs")
    if not trafaret:
        trafaret = Dict(**kwargs)

    def wrapper(fn):
        argspec = getargspec(fn)

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
                converted = trafaret(call_args)
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
