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

The ``String`` is base checker in trafaret which just test that value is string.
Also ``String`` has a lot of helpful modification like ``Email`` and ``Url``.


    >>> t.String().check('this is my string')
    'this is my string'

Options:

    - **allow_blank** *(boolean)* - indicates if string can be blank or not
    - **min_length** *(integer)* - validation for minimum length of receive string
    - **max_length** *(integer)* - validation for maximum length of receive string

The simple examples of usage:

    >>> t.String(allow_blank=True).check('')
    ''
    >>> t.String(min_length=1, max_length=10).check('no so long')
    'no so long'

``Email`` and ``URL`` just provide regular expressions and a bit of logic for
IDNA domains. Default converters return email and domain, but you will get re
match object in converter.

Email
~~~~~
This checker test that a received string is an valid email address.

    >>> t.Email.check('someone@example.net')
    'someone@example.net'

URL
~~~
This checker test that a received string is an valid URL address. This URL can
include get params and anchors.

    >>> t.URL.check('http://example.net/resource/?param=value#anchor')
    'http://example.net/resource/?param=value#anchor'

IPv4
~~~~
This checker test that a received string is IPv4 address.

    >>> t.IPv4.check('127.0.0.1')
    '127.0.0.1'

IPv6
~~~~
This checker test that a received string is IPv6 address.


    >>> t.IPv6.check('2001:0db8:0000:0042:0000:8a2e:0370:7334')
    '2001:0db8:0000:0042:0000:8a2e:0370:7334'

IP
~~
This checker test that a received string is IP address (IPv4 or IPv6).

    >>> t.IP.check('127.0.0.1')
    '127.0.0.1'
    >>> t.IP.check('2001:0db8:0000:0042:0000:8a2e:0370:7334')
    '2001:0db8:0000:0042:0000:8a2e:0370:7334'

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
