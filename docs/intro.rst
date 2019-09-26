Introducing
===========

Trafaret is validation library with support to convert data structures.
Sample usage::

    >>> import datetime
    >>> import trafaret as t

    >>> date = t.Dict(year=t.Int, month=t.Int, day=t.Int) >> (lambda d: datetime.datetime(**d))

    >>> def validate_date(data):
    >>>     try:
    >>>         return date.check(data), False
    >>>     except t.DataError as e:
    >>>         return False, e.as_dict()

    >>> validate_date({'year': 2012, 'month': 1}) 
    (False, {'day': 'is required'})

    >>> validate_date({'year': 2012, 'month': 1, 'day': 12})
    (datetime.datetime(2012, 1, 12, 0, 0), False)

``t.Dict`` creates new dict structure validator with three ``t.Int`` elements.
``>>`` operation adds lambda function to the converters of given checker.
Some checkers have default converter, but when you use ``>>`` or ``.append``,
you disable default converter with your own.

This does not mean that ``Int`` will not convert numbers to integers,
this mean that some checkers, like ``String`` with regular expression,
have special converters applied them and can be overridden.

Converters can be chained. You can raise ``DataError`` in converters.

Types
-----


String
......

- Email
- url
- IPv4
- IPv6
- IP


Regexp
......


AnyString
.........


Bytes
.....


Bytes
.....


FromBytes
.........


Bool
....


StrBool
.......

Float
.....


ToFloat
.......


ToDecemal
.........


Int
...


ToInt
.....


Null
....


Any
...


Type
....


Atom
....


List
....


Iterable
........


Tuple
.....


Mapping
.......


Enum
....


Callable
........


Call
....


Dict
....

- dict
- Key
- DictKeys


Operations
----------

And
...


Or
..


fold
....


split
.....


KeysSubset
..........


Other
_____


Forward
.......


Guard
.....


GuardError
..........
