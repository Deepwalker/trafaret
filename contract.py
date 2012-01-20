# -*- coding: utf-8 -*-

import functools
import inspect
import re
import urlparse
import copy
import itertools

"""
Contract is tiny library for data validation
It provides several primitives to validate complex data structures
Look at doctests for usage examples
"""

__all__ = ("ContractValidationError", "Contract", "Any", "Int", "String",
           "List", "Dict", "Or", "Null", "Float", "Enum", "Callable"
           "Call", "Forward", "Bool", "Type", "Mapping", "guard", )


class ContractValidationError(TypeError):

    """
    Basic contract validation error
    """

    def __init__(self, msg, name=None):
        message = msg if not name else "%s: %s" % (name, msg)
        super(ContractValidationError, self).__init__(message)
        self.msg = msg
        self.name = name


class ContractMeta(type):

    """
    Metaclass for contracts to make using "|" operator possible not only
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

    def __rshift__(cls, other):
        return cls() >> other


class Contract(object):

    """
    Base class for contracts, provides only one method for
    contract validation failure reporting
    """

    __metaclass__ = ContractMeta

    def check(self, value):
        """
        Implement this method in Contract subclasses
        """
        if hasattr(self, '_check'):
            self._check(value)
            return self._convert(value)
        if hasattr(self, '_check_val'):
            return self._convert(self._check_val(value))
        cls = "%s.%s" % (type(self).__module__, type(self).__name__)
        raise NotImplementedError("method check is not implemented in"
                                  " '%s'" % cls)

    def converter(self, value):
        """
        You can change converter with `>>` operator
        """
        return value

    def _convert(self, value):
        val = value
        for converter in getattr(self, 'converters', [self.converter]):
            val = converter(value)
        return val

    def _failure(self, message):
        """
        Shortcut method for raising validation error
        """
        raise ContractValidationError(message)

    def _contract(self, contract):
        """
        Helper for complex contracts, takes contract instance or class
        and returns contract instance
        """
        if isinstance(contract, Contract):
            return contract
        elif issubclass(contract, Contract):
            return contract()
        elif isinstance(contract, type):
            return Type(contract)
        else:
            raise RuntimeError("%r should be instance or subclass"
                               " of Contract" % contract)

    def append(self, converter):
        """
        Appends new converter to list.
        """
        if hasattr(self, 'converters'):
            self.checkers.append(converter)
        else:
            self.converters = [converter]
        return self

    def __or__(self, other):
        return Or(self, other)

    def __rshift__(self, other):
        self.append(other)
        return self


class Type(Contract):

    """
    >>> Type(int)
    <Type(int)>
    >>> Type[int]
    <Type(int)>
    >>> c = Type[int]
    >>> c.check(1)
    1
    >>> c.check("foo")
    Traceback (most recent call last):
    ...
    ContractValidationError: value is not int
    """

    class __metaclass__(ContractMeta):

        def __getitem__(self, type_):
            return self(type_)

    def __init__(self, type_):
        self.type_ = type_

    def _check(self, value):
        if not isinstance(value, self.type_):
            self._failure("value is not %s" % self.type_.__name__)

    def __repr__(self):
        return "<Type(%s)>" % self.type_.__name__


class Any(Contract):

    """
    >>> Any()
    <Any>
    >>> (Any() >> ignore).check(object())
    """

    def _check(self, value):
        pass

    def __repr__(self):
        return "<Any>"


class OrMeta(ContractMeta):

    """
    Allows to use "<<" operator on Or class

    >>> Or << Int << String
    <Or(<Int>, <String>)>
    """

    def __lshift__(cls, other):
        return cls() << other


class Or(Contract):

    """
    >>> nullString = Or(String, Null)
    >>> nullString
    <Or(<String>, <Null>)>
    >>> nullString.check(None)
    >>> nullString.check("test")
    'test'
    >>> nullString.check(1)
    Traceback (most recent call last):
    ...
    ContractValidationError: no one contract matches: value is not string || value should be None
    """

    __metaclass__ = OrMeta

    def __init__(self, *contracts):
        self.contracts = map(self._contract, contracts)

    def _check_val(self, value):
        errors = []
        for contract in self.contracts:
            try:
                return contract.check(value)
            except ContractValidationError as e:
                errors.append(e)
        message = ("no one contract matches: %s" %
                   ' || '.join(e.message for e in errors))
        raise ContractValidationError(message)

    def __lshift__(self, contract):
        self.contracts.append(self._contract(contract))
        return self

    def __or__(self, contract):
        self << contract
        return self

    def __repr__(self):
        return "<Or(%s)>" % (", ".join(map(repr, self.contracts)))


class Null(Contract):

    """
    >>> Null()
    <Null>
    >>> Null().check(None)
    >>> Null().check(1)
    Traceback (most recent call last):
    ...
    ContractValidationError: value should be None
    """

    def _check(self, value):
        if value is not None:
            self._failure("value should be None")

    def __repr__(self):
        return "<Null>"


class Bool(Contract):

    """
    >>> Bool()
    <Bool>
    >>> Bool().check(True)
    True
    >>> Bool().check(False)
    False
    >>> Bool().check(1)
    Traceback (most recent call last):
    ...
    ContractValidationError: value should be True or False
    """

    def _check(self, value):
        if not isinstance(value, bool):
            self._failure("value should be True or False")

    def __repr__(self):
        return "<Bool>"


class NumberMeta(ContractMeta):

    """
    Allows slicing syntax for min and max arguments for
    number contracts

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
    >>> (Int > 5).check(1)
    Traceback (most recent call last):
    ...
    ContractValidationError: value should be greater than 5
    >>> (Int < 3).check(1)
    1
    >>> (Int < 3).check(3)
    Traceback (most recent call last):
    ...
    ContractValidationError: value should be less than 3
    """

    def __getitem__(self, slice_):
        return self(gte=slice_.start, lte=slice_.stop)

    def __lt__(self, lt):
        return self(lt=lt)

    def __gt__(self, gt):
        return self(gt=gt)


class Float(Contract):

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
    >>> Float().check(1)
    Traceback (most recent call last):
    ...
    ContractValidationError: value is not float
    >>> Float(gte=2).check(3.0)
    3.0
    >>> Float(gte=2).check(1.0)
    Traceback (most recent call last):
    ...
    ContractValidationError: value is less than 2
    >>> Float(lte=10).check(5.0)
    5.0
    >>> Float(lte=3).check(5.0)
    Traceback (most recent call last):
    ...
    ContractValidationError: value is greater than 3
    >>> Float().check("5.0")
    5.0
    """

    __metaclass__ = NumberMeta

    value_type = float

    def __init__(self, gte=None, lte=None, gt=None, lt=None):
        self.gte = gte
        self.lte = lte
        self.gt = gt
        self.lt = lt

    def _check_val(self, val):
        if not isinstance(val, self.value_type):
            if isinstance(val, basestring):
                try:
                    value = self.value_type(val)
                except ValueError:
                    self._failure("value cant be converted to %s" %
                            self.value_type.__name__)
            else:
                self._failure("value is not %s" % self.value_type.__name__)
        else:
            value = val
        if self.gte is not None and value < self.gte:
            self._failure("value is less than %s" % self.gte)
        if self.lte is not None and value > self.lte:
            self._failure("value is greater than %s" % self.lte)
        if self.lt is not None and value >= self.lt:
            self._failure("value should be less than %s" % self.lt)
        if self.gt is not None and value <= self.gt:
            self._failure("value should be greater than %s" % self.gt)
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
    >>> Int().check(1.1)
    Traceback (most recent call last):
    ...
    ContractValidationError: value is not int
    """

    value_type = int


class Atom(Contract):

    """
    >>> Atom('atom').check('atom')
    'atom'
    >>> Atom('atom').check('molecule')
    Traceback (most recent call last):
    ...
    ContractValidationError: value is not exactly 'atom'
    """

    def __init__(self, value):
        self.value = value

    def _check(self, value):
        if self.value != value:
            self._failure("value is not exactly '%s'" % self.value)


class String(Contract):

    """
    >>> String()
    <String>
    >>> String(allow_blank=True)
    <String(blank)>
    >>> String().check("foo")
    'foo'
    >>> String().check("")
    Traceback (most recent call last):
    ...
    ContractValidationError: blank value is not allowed
    >>> String(allow_blank=True).check("")
    ''
    >>> String().check(1)
    Traceback (most recent call last):
    ...
    ContractValidationError: value is not string
    >>> String(regex='\w+').check('wqerwqer')
    'wqerwqer'
    >>> String(regex='^\w+$').check('wqe rwqer')
    Traceback (most recent call last):
    ...
    ContractValidationError: value does not match pattern
    """

    def __init__(self, allow_blank=False, regex=None):
        self.allow_blank = allow_blank
        self.regex = re.compile(regex) if isinstance(regex, basestring) else regex

    def _check_val(self, value):
        if not isinstance(value, basestring):
            self._failure("value is not string")
        if not self.allow_blank and len(value) is 0:
            self._failure("blank value is not allowed")
        if self.regex is not None:
            match = self.regex.match(value)
            if not match:
                self._failure("value does not match pattern")
            return match
        return value

    def converter(self, value):
        if isinstance(value, basestring):
            return value
        return value.group()

    def __repr__(self):
        return "<String(blank)>" if self.allow_blank else "<String>"


class Email(String):

    """
    >>> Email().check('someone@example.net')
    'someone@example.net'
    >>> (Email() >> (lambda m: m.groupdict()['domain'])).check('someone@example.net')
    'example.net'
    """

    regex = re.compile(
        r"(?P<name>^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"' # quoted-string
        r')@(?P<domain>(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?$)'  # domain
        r'|\[(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\]$', re.IGNORECASE)  # literal form, ipv4 address (SMTP 4.1.3)

    def __init__(self, allow_blank=False):
        self.allow_blank = allow_blank

    def _check_val(self, value):
        try:
            return super(Email, self)._check_val(value)
        except ContractValidationError:
            # Trivial case failed. Try for possible IDN domain-part
            if value and u'@' in value:
                parts = value.split(u'@')
                try:
                    parts[-1] = parts[-1].encode('idna')
                except UnicodeError:
                    pass
                else:
                    return super(Email, self)._check_val(u'@'.join(parts))
        self._failure('value is not email')

    def __repr__(self):
        return '<Email>'


class URL(String):

    """
    >>> URL().check('http://example.net/resource/?param=value#anchor')
    'http://example.net/resource/?param=value#anchor'
    >>> URL().check('http://пример.рф/resource/?param=value#anchor')
    u'http://xn--e1afmkfd.xn--p1ai/resource/?param=value#anchor'
    """

    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    def __init__(self, allow_blank=False):
        self.allow_blank = allow_blank

    def _check_val(self, value):
        try:
            return super(URL, self)._check_val(value)
        except ContractValidationError:
            # Trivial case failed. Try for possible IDN domain-part
            if value:
                if isinstance(value, str):
                    decoded = value.decode('utf-8')
                else:
                    decoded = value
                scheme, netloc, path, query, fragment = urlparse.urlsplit(decoded)
                try:
                    netloc = netloc.encode('idna') # IDN -> ACE
                except UnicodeError: # invalid domain part
                    pass
                else:
                    url = urlparse.urlunsplit((scheme, netloc, path, query, fragment))
                    return super(URL, self)._check_val(url)
        self._failure('value is not URL')

    def __repr__(self):
        return '<URL>'


class SquareBracketsMeta(ContractMeta):

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
    RuntimeError: Contract is required for List initialization
    """

    def __getitem__(self, args):
        slice_ = None
        contract = None
        if not isinstance(args, tuple):
            args = (args, )
        for arg in args:
            if isinstance(arg, slice):
                slice_ = arg
            elif isinstance(arg, Contract) or issubclass(arg, Contract) \
                 or isinstance(arg, type):
                contract = arg
        if not contract:
            raise RuntimeError("Contract is required for List initialization")
        if slice_:
            return self(contract, min_length=slice_.start or 0,
                                  max_length=slice_.stop)
        return self(contract)


class List(Contract):

    """
    >>> List(Int)
    <List(<Int>)>
    >>> List(Int, min_length=1)
    <List(min_length=1 | <Int>)>
    >>> List(Int, min_length=1, max_length=10)
    <List(min_length=1, max_length=10 | <Int>)>
    >>> List(Int).check(1)
    Traceback (most recent call last):
    ...
    ContractValidationError: value is not list
    >>> List(Int).check([1, 2, 3])
    [1, 2, 3]
    >>> List(String).check(["foo", "bar", "spam"])
    ['foo', 'bar', 'spam']
    >>> List(Int).check([1, 2, 3.0])
    Traceback (most recent call last):
    ...
    ContractValidationError: 2: value is not int
    >>> List(Int, min_length=1).check([1, 2, 3])
    [1, 2, 3]
    >>> List(Int, min_length=1).check([])
    Traceback (most recent call last):
    ...
    ContractValidationError: list length is less than 1
    >>> List(Int, max_length=2).check([1, 2])
    [1, 2]
    >>> List(Int, max_length=2).check([1, 2, 3])
    Traceback (most recent call last):
    ...
    ContractValidationError: list length is greater than 2
    """

    __metaclass__ = SquareBracketsMeta

    def __init__(self, contract, min_length=0, max_length=None):
        self.contract = self._contract(contract)
        self.min_length = min_length
        self.max_length = max_length

    def _check_val(self, value):
        if not isinstance(value, list):
            self._failure("value is not list")
        if len(value) < self.min_length:
            self._failure("list length is less than %s" % self.min_length)
        if self.max_length is not None and len(value) > self.max_length:
            self._failure("list length is greater than %s" % self.max_length)
        lst = []
        for index, item in enumerate(value):
            try:
                lst.append(self.contract.check(item))
            except ContractValidationError as err:
                name = "%i.%s" % (index, err.name) if err.name else str(index)
                raise ContractValidationError(err.msg, name)
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
        r += repr(self.contract)
        r += ")>"
        return r


class Key(object):

    """
    Helper class for Dict.
    """

    def __init__(self, name, default=None, optional=False, to_name=None):
        self.name = name
        self.to_name = to_name
        self.default = default
        self.optional = optional
        self.contract = Any()

    def pop(self, data):
        if self.name not in data:
            if self.optional:
                raise StopIteration
            elif self.default is not None:
                pass
            else:
                raise ContractValidationError('is required')
        yield self.get_name(), data.pop(self.name, self.default)

    def set_contract(self, contract):
        self.contract = contract

    def __rshift__(self, name):
        self.to_name = name
        return self

    def get_name(self):
        return self.to_name or self.name

    def make_optional(self):
        self.optional = True
        self.default = None


class Dict(Contract):

    """
    >>> contract = Dict(foo=Int, bar=String) >> ignore
    >>> contract.check({"foo": 1, "bar": "spam"})
    >>> contract.check({"foo": 1, "bar": 2})
    Traceback (most recent call last):
    ...
    ContractValidationError: bar: value is not string
    >>> contract.check({"foo": 1})
    Traceback (most recent call last):
    ...
    ContractValidationError: bar: is required
    >>> contract.check({"foo": 1, "bar": "spam", "eggs": None})
    Traceback (most recent call last):
    ...
    ContractValidationError: eggs is not allowed key
    >>> contract.allow_extra("eggs")
    <Dict(extras=(eggs) | bar=<String>, foo=<Int>)>
    >>> contract.check({"foo": 1, "bar": "spam", "eggs": None})
    >>> contract.check({"foo": 1, "bar": "spam"})
    >>> contract.check({"foo": 1, "bar": "spam", "ham": 100})
    Traceback (most recent call last):
    ...
    ContractValidationError: ham is not allowed key
    >>> contract.allow_extra("*")
    <Dict(any, extras=(eggs) | bar=<String>, foo=<Int>)>
    >>> contract.check({"foo": 1, "bar": "spam", "ham": 100})
    >>> contract.check({"foo": 1, "bar": "spam", "ham": 100, "baz": None})
    >>> contract.check({"foo": 1, "ham": 100, "baz": None})
    Traceback (most recent call last):
    ...
    ContractValidationError: bar: is required
    >>> contract = Dict({Key('bar', optional=True): String}, foo=Int) >> ignore
    >>> contract.allow_extra("*")
    <Dict(any | bar=<String>, foo=<Int>)>
    >>> contract.check({"foo": 1, "ham": 100, "baz": None})
    >>> contract.check({"bar": 1, "ham": 100, "baz": None})
    Traceback (most recent call last):
    ...
    ContractValidationError: foo: is required
    >>> contract.check({"foo": 1, "bar": 1, "ham": 100, "baz": None})
    Traceback (most recent call last):
    ...
    ContractValidationError: bar: value is not string
    >>> contract = Dict({Key('bar', default='nyanya') >> 'baz': String}, foo=Int)
    >>> contract.check({'foo': 4})
    {'foo': 4, 'baz': 'nyanya'}
    """

    def __init__(self, keys={}, **contracts):
        self.extras = []
        self.allow_any = False
        self.keys = []
        for key, contract in itertools.chain(contracts.items(), keys.items()):
            key_ = key if isinstance(key, Key) else Key(key)
            key_.set_contract(self._contract(contract))
            self.keys.append(key_)

    def allow_extra(self, *names):
        for name in names:
            if name == "*":
                self.allow_any = True
            else:
                self.extras.append(name)
        return self

    def make_optional(self, *args):
        for key in self.keys:
            if key.name in args or '*' in args:
                key.make_optional()

    def _check_val(self, value):
        if not isinstance(value, dict):
            self._failure("value is not dict")
        data = copy.copy(value)
        collect = {}
        for key in self.keys:
            try:
                for k, v in key.pop(data):
                    collect[k] = key.contract.check(v)
            except ContractValidationError as err:
                name = "%s.%s" % (key.name, err.name) if err.name else key.name
                raise ContractValidationError(err.msg, name)
        for key in data:
            if not self.allow_any and key not in self.extras:
                self._failure("%s is not allowed key" % key)
            collect[key] = data
        return collect

    def __repr__(self):
        r = "<Dict("
        options = []
        if self.allow_any:
            options.append("any")
        if self.extras:
            options.append("extras=(%s)" % (", ".join(self.extras)))
        r += ", ".join(options)
        if options:
            r += " | "
        options = []
        for key in sorted(self.keys, key=lambda k: k.name):
            options.append("%s=%r" % (key.name, key.contract))
        r += ", ".join(options)
        r += ")>"
        return r


class Mapping(Contract):

    """
    >>> contract = Mapping(String, Int)
    >>> contract
    <Mapping(<String> => <Int>)>
    >>> contract.check({"foo": 1, "bar": 2})
    >>> contract.check({"foo": 1, "bar": None})
    Traceback (most recent call last):
    ...
    ContractValidationError: (value for key 'bar'): value is not int
    >>> contract.check({"foo": 1, 2: "bar"})
    Traceback (most recent call last):
    ...
    ContractValidationError: (key 2): value is not string
    """

    def __init__(self, key, value):
        self.key = self._contract(key)
        self.value = self._contract(value)

    def _check_val(self, mapping):
        checked_mapping = {}
        for key in mapping:
            value = mapping[key]
            try:
                checked_key = self.key.check(key)
            except ContractValidationError as err:
                raise ContractValidationError(err.msg, "(key %r)" % key)
            try:
                checked_value = self.value.check(value)
            except ContractValidationError as err:
                raise ContractValidationError(err.msg, "(value for key %r)" % key)
            checked_mapping[checked_key] = checked_value

    def __repr__(self):
        return "<Mapping(%r => %r)>" % (self.key, self.value)


class Enum(Contract):

    """
    >>> contract = Enum("foo", "bar", 1) >> ignore
    >>> contract
    <Enum('foo', 'bar', 1)>
    >>> contract.check("foo")
    >>> contract.check(1)
    >>> contract.check(2)
    Traceback (most recent call last):
    ...
    ContractValidationError: value doesn't match any variant
    """

    def __init__(self, *variants):
        self.variants = variants[:]

    def _check(self, value):
        if value not in self.variants:
            self._failure("value doesn't match any variant")

    def __repr__(self):
        return "<Enum(%s)>" % (", ".join(map(repr, self.variants)))


class Callable(Contract):

    """
    >>> (Callable() >> ignore).check(lambda: 1)
    >>> Callable().check(1)
    Traceback (most recent call last):
    ...
    ContractValidationError: value is not callable
    """

    def _check(self, value):
        if not callable(value):
            self._failure("value is not callable")

    def __repr__(self):
        return "<CallableC>"


class Call(Contract):

    """
    >>> def validator(value):
    ...     if value != "foo":
    ...         return "I want only foo!"
    ...
    >>> contract = Call(validator)
    >>> contract
    <CallC(validator)>
    >>> contract.check("foo")
    'foo'
    >>> contract.check("bar")
    Traceback (most recent call last):
    ...
    ContractValidationError: I want only foo!
    """

    def __init__(self, fn):
        if not callable(fn):
            raise RuntimeError("CallC argument should be callable")
        argspec = inspect.getargspec(fn)
        if len(argspec.args) - len(argspec.defaults or []) > 1:
            raise RuntimeError("CallC argument should be"
                               " one argument function")
        self.fn = fn

    def _check(self, value):
        error = self.fn(value)
        if error is not None:
            self._failure(error)

    def __repr__(self):
        return "<CallC(%s)>" % self.fn.__name__


class Forward(Contract):

    """
    >>> nodeC = Forward()
    >>> nodeC << Dict(name=String, children=List[nodeC])
    >>> nodeC
    <Forward(<Dict(children=<List(<recur>)>, name=<String>)>)>
    >>> nodeC.check({"name": "foo", "children": []})
    >>> nodeC.check({"name": "foo", "children": [1]})
    Traceback (most recent call last):
    ...
    ContractValidationError: children.0: value is not dict
    >>> nodeC.check({"name": "foo", "children": [ \
                        {"name": "bar", "children": []} \
                     ]})
    """

    def __init__(self):
        self.contract = None
        self._recur_repr = False

    def __lshift__(self, contract):
        if self.contract:
            raise RuntimeError("contract for Forward is already specified")
        self.contract = self._contract(contract)

    def check(self, value):
        self.contract.check(value)

    def __repr__(self):
        # XXX not threadsafe
        if self._recur_repr:
            return "<recur>"
        self._recur_repr = True
        r = "<Forward(%r)>" % self.contract
        self._recur_repr = False
        return r


class GuardValidationError(ContractValidationError):

    """
    Raised when guarded function gets invalid arguments,
    inherits error message from corresponding ContractValidationError
    """

    pass


def guard(contract=None, **kwargs):
    """
    Decorator for protecting function with contracts

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
    >>> fn("foo", 1, 2)
    Traceback (most recent call last):
    ...
    GuardValidationError: c: value is not string
    >>> fn("foo")
    Traceback (most recent call last):
    ...
    GuardValidationError: b: is required
    >>> g = guard(Dict())
    >>> c = Forward()
    >>> c << Dict(name=basestring, children=List[c])
    >>> g = guard(c)
    >>> g = guard(Int())
    Traceback (most recent call last):
    ...
    RuntimeError: contract should be instance of Dict or Forward
    """
    if contract and not isinstance(contract, Dict) and \
                    not isinstance(contract, Forward):
        raise RuntimeError("contract should be instance of Dict or Forward")
    elif contract and kwargs:
        raise RuntimeError("choose one way of initialization,"
                           " contract or kwargs")
    if not contract:
        contract = Dict(**kwargs)
    def wrapper(fn):
        argspec = inspect.getargspec(fn)
        @functools.wraps(fn)
        def decor(*args, **kwargs):
            fnargs = argspec.args
            if fnargs[0] == 'self':
                fnargs = fnargs[1:]
                checkargs = args[1:]
            else:
                checkargs = args

            try:
                call_args = dict(zip(fnargs, checkargs) + kwargs.items())
                for name, default in zip(reversed(fnargs),
                                         argspec.defaults or ()):
                    if name not in call_args:
                        call_args[name] = default
                contract.check(call_args)
            except ContractValidationError as err:
                raise GuardValidationError(unicode(err))
            return fn(*args, **kwargs)
        decor.__doc__ = "guarded with %r\n\n" % contract + (decor.__doc__ or "")
        return decor
    return wrapper


def ignore(val):
    '''
    Stub to ignore value from checker
    Use it like:

    >>> a = Int >> ignore
    >>> a.check(7)
    '''
    pass


if __name__ == "__main__":
    import doctest
    doctest.testmod()
