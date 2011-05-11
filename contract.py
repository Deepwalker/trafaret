# -*- coding: utf-8 -*-

"""
Contract is tiny library for data validation
It provides several primitives to validate complex data structures
Look at doctests for usage examples
"""

__all__ = ("ContractValidationError", "Contract", "AnyC", "IntC", "StringC",
            "ListC", "DictC", "OrC", "NullC", "FloatC", "EnumC", )


class ContractValidationError(Exception):
    pass


class Contract(object):
    
    """
    Base class for contracts, provides only one method for
    contract validation failure reporting
    """
    
    def check(self, value):
        """
        Implement this method in Contract subclasses
        """
        cls = "%s.%s" % (type(self).__module__, type(self).__name__)
        raise NotImplementedError("method check is not implemented in"
                                  " '%s'" % cls)
    
    def failure(self, message):
        raise ContractValidationError(message)


class AnyC(Contract):
    
    """
    >>> AnyC()
    <AnyC>
    >>> AnyC().check(object())
    """
    
    def check(self, value):
        pass
    
    def __repr__(self):
        return "<AnyC>"


class OrC(Contract):
    
    """
    >>> nullString = OrC(StringC(), NullC())
    >>> nullString
    <OrC(<StringC>, <NullC>)>
    >>> nullString.check(None)
    >>> nullString.check("test")
    >>> nullString.check(1)
    Traceback (most recent call last):
    ...
    ContractValidationError: no one contract matches
    """
    
    def __init__(self, *contracts):
        self.contracts = contracts
    
    def check(self, value):
        for contract in self.contracts:
            try:
                contract.check(value)
            except ContractValidationError:
                pass
            else:
                return
        self.failure("no one contract matches")

    def __repr__(self):
        return "<OrC(%s)>" % (", ".join(map(repr, self.contracts)))


class NullC(Contract):
    
    """
    >>> NullC()
    <NullC>
    >>> NullC().check(None)
    >>> NullC().check(1)
    Traceback (most recent call last):
    ...
    ContractValidationError: value should be None
    """
    
    def check(self, value):
        if value is not None:
            self.failure("value should be None")
    
    def __repr__(self):
        return "<NullC>"


class IntC(Contract):
    
    """
    >>> IntC()
    <IntC>
    >>> IntC(min_=1)
    <IntC(min=1)>
    >>> IntC(max_=10)
    <IntC(max=10)>
    >>> IntC(min_=1, max_=10)
    <IntC(min=1, max=10)>
    >>> IntC().check("foo")
    Traceback (most recent call last):
    ...
    ContractValidationError: value is not int
    >>> IntC(min_=1).check(1)
    >>> IntC(min_=2).check(1)
    Traceback (most recent call last):
    ...
    ContractValidationError: value is less than 2
    >>> IntC(max_=10).check(5)
    >>> IntC(max_=3).check(5)
    Traceback (most recent call last):
    ...
    ContractValidationError: value is greater than 3
    """
    
    def __init__(self, min_=None, max_=None):
        self.min = min_
        self.max = max_
    
    def check(self, value):
        if not isinstance(value, int):
            self.failure("value is not int")
        if self.min is not None and value < self.min:
            self.failure("value is less than %s" % self.min)
        if self.max is not None and value > self.max:
            self.failure("value is greater than %s" % self.max)
    
    def __repr__(self):
        r = "<IntC"
        options = []
        if self.min is not None:
            options.append("min=%s" % self.min)
        if self.max is not None:
            options.append("max=%s" % self.max)
        if options:
            r += "(%s)" % (", ".join(options))
        r += ">"
        return r


class FloatC(Contract):
    
    """
    >>> FloatC()
    <FloatC>
    >>> FloatC(min_=1)
    <FloatC(min=1)>
    >>> FloatC(max_=10)
    <FloatC(max=10)>
    >>> FloatC(min_=1, max_=10)
    <FloatC(min=1, max=10)>
    >>> FloatC().check(1.0)
    >>> FloatC().check(1)
    Traceback (most recent call last):
    ...
    ContractValidationError: value is not float
    >>> FloatC(min_=2).check(3.0)
    >>> FloatC(min_=2).check(1.0)
    Traceback (most recent call last):
    ...
    ContractValidationError: value is less than 2
    >>> FloatC(max_=10).check(5.0)
    >>> FloatC(max_=3).check(5.0)
    Traceback (most recent call last):
    ...
    ContractValidationError: value is greater than 3
    """
    
    def __init__(self, min_=None, max_=None):
        self.min = min_
        self.max = max_
    
    def check(self, value):
        if not isinstance(value, float):
            self.failure("value is not float")
        if self.min is not None and value < self.min:
            self.failure("value is less than %s" % self.min)
        if self.max is not None and value > self.max:
            self.failure("value is greater than %s" % self.max)

    def __repr__(self):
        r = "<FloatC"
        options = []
        if self.min is not None:
            options.append("min=%s" % self.min)
        if self.max is not None:
            options.append("max=%s" % self.max)
        if options:
            r += "(%s)" % (", ".join(options))
        r += ">"
        return r


class StringC(Contract):
    
    """
    >>> StringC()
    <StringC>
    >>> StringC(allow_blank=True)
    <StringC(blank)>
    >>> StringC().check("foo")
    >>> StringC().check("")
    Traceback (most recent call last):
    ...
    ContractValidationError: blank value is not allowed
    >>> StringC(allow_blank=True).check("")
    >>> StringC().check(1)
    Traceback (most recent call last):
    ...
    ContractValidationError: value is not string
    """
    
    def __init__(self, allow_blank=False):
        self.allow_blank = allow_blank
    
    def check(self, value):
        if not isinstance(value, basestring):
            self.failure("value is not string")
        if not self.allow_blank and len(value) is 0:
            self.failure("blank value is not allowed")
    
    def __repr__(self):
        return "<StringC(blank)>" if self.allow_blank else "<StringC>"


class ListC(Contract):
    
    """
    >>> ListC(IntC())
    <ListC(<IntC>)>
    >>> ListC(IntC(), min_length=1)
    <ListC(min_length=1 | <IntC>)>
    >>> ListC(IntC(), min_length=1, max_length=10)
    <ListC(min_length=1, max_length=10 | <IntC>)>
    >>> ListC(IntC()).check(1)
    Traceback (most recent call last):
    ...
    ContractValidationError: value is not list
    >>> ListC(IntC()).check([1, 2, 3])
    >>> ListC(StringC()).check(["foo", "bar", "spam"])
    >>> ListC(IntC()).check([1, 2, 3.0])
    Traceback (most recent call last):
    ...
    ContractValidationError: value is not int
    >>> ListC(IntC(), min_length=1).check([1, 2, 3])
    >>> ListC(IntC(), min_length=1).check([])
    Traceback (most recent call last):
    ...
    ContractValidationError: list length is less than 1
    >>> ListC(IntC(), max_length=2).check([1, 2])
    >>> ListC(IntC(), max_length=2).check([1, 2, 3])
    Traceback (most recent call last):
    ...
    ContractValidationError: list length is greater than 2
    """
    
    def __init__(self, contract, min_length=0, max_length=None):
        self.contract = contract
        self.min_length = min_length
        self.max_length = max_length
    
    def check(self, value):
        if not isinstance(value, list):
            self.failure("value is not list")
        if len(value) < self.min_length:
            self.failure("list length is less than %s" % self.min_length)
        if self.max_length is not None and len(value) > self.max_length:
            self.failure("list length is greater than %s" % self.max_length)
        for item in value:
            self.contract.check(item)
    
    def __repr__(self):
        r = "<ListC("
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


class DictC(Contract):
    
    """
    >>> contract = DictC(foo=IntC(), bar=StringC())
    >>> contract.check({"foo": 1, "bar": "spam"})
    >>> contract.check({"foo": 1, "bar": 2})
    Traceback (most recent call last):
    ...
    ContractValidationError: value is not string
    >>> contract.check({"foo": 1})
    Traceback (most recent call last):
    ...
    ContractValidationError: bar is required
    >>> contract.check({"foo": 1, "bar": "spam", "eggs": None})
    Traceback (most recent call last):
    ...
    ContractValidationError: eggs is not allowed key
    >>> contract.allow_extra("eggs")
    <DictC(extras=(eggs) | bar=<StringC>, foo=<IntC>)>
    >>> contract.check({"foo": 1, "bar": "spam", "eggs": None})
    >>> contract.check({"foo": 1, "bar": "spam"})
    >>> contract.check({"foo": 1, "bar": "spam", "ham": 100})
    Traceback (most recent call last):
    ...
    ContractValidationError: ham is not allowed key
    >>> contract.allow_extra("*")
    <DictC(any, extras=(eggs) | bar=<StringC>, foo=<IntC>)>
    >>> contract.check({"foo": 1, "bar": "spam", "ham": 100})
    >>> contract.check({"foo": 1, "bar": "spam", "ham": 100, "baz": None})
    >>> contract.check({"foo": 1, "ham": 100, "baz": None})
    Traceback (most recent call last):
    ...
    ContractValidationError: bar is required
    >>> contract.allow_optionals("bar")
    <DictC(any, extras=(eggs), optionals=(bar) | bar=<StringC>, foo=<IntC>)>
    >>> contract.check({"foo": 1, "ham": 100, "baz": None})
    >>> contract.check({"bar": 1, "ham": 100, "baz": None})
    Traceback (most recent call last):
    ...
    ContractValidationError: foo is required
    >>> contract.check({"foo": 1, "bar": 1, "ham": 100, "baz": None})
    Traceback (most recent call last):
    ...
    ContractValidationError: value is not string
    """
    
    def __init__(self, **contracts):
        self.optionals = []
        self.extras = []
        self.allow_any = False
        self.contracts = contracts
    
    def allow_extra(self, *names):
        for name in names:
            if name == "*":
                self.allow_any = True
            else:
                self.extras.append(name)
        return self
    
    def allow_optionals(self, *names):
        for name in names:
            if name == "*":
                self.optionals = self.contracts.keys()
            else:
                self.optionals.append(name)
        return self
    
    def check(self, value):
        if not isinstance(value, dict):
            self.failure("value is not dict")
        self.check_presence(value)
        map(self.check_item, value.items())
    
    def check_presence(self, value):
        for key in self.contracts:
            if key not in self.optionals and key not in value:
                self.failure("%s is required" % key)
    
    def check_item(self, item):
        key, value = item
        if key in self.contracts:
            self.contracts[key].check(value)
        elif not self.allow_any and key not in self.extras:
            self.failure("%s is not allowed key" % key)
    
    def __repr__(self):
        r = "<DictC("
        options = []
        if self.allow_any:
            options.append("any")
        if self.extras:
            options.append("extras=(%s)" % (", ".join(self.extras)))
        if self.optionals:
            options.append("optionals=(%s)" % (", ".join(self.optionals)))
        r += ", ".join(options)
        if options:
            r += " | "
        options = []
        for key in sorted(self.contracts.keys()):
            options.append("%s=%r" % (key, self.contracts[key]))
        r += ", ".join(options)
        r += ")>"
        return r


class EnumC(Contract):
    
    """
    >>> contract = EnumC("foo", "bar", 1)
    >>> contract
    <EnumC('foo', 'bar', 1)>
    >>> contract.check("foo")
    >>> contract.check(1)
    >>> contract.check(2)
    Traceback (most recent call last):
    ...
    ContractValidationError: value doesn't match any variant
    """
    
    def __init__(self, *variants):
        self.variants = variants[:]
    
    def check(self, value):
        if value not in self.variants:
            self.failure("value doesn't match any variant")
    
    def __repr__(self):
        return "<EnumC(%s)>" % (", ".join(map(repr, self.variants)))
