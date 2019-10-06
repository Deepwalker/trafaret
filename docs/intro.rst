Introducing
===========

Trafaret is validation library with support to convert data structures.
Sample usage::

    >>> import datetime
    >>> import trafaret as t

    >>> date = t.Dict(year=t.Int, month=t.Int, day=t.Int) & (lambda d: datetime.datetime(**d))

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
``&`` operation combines trafaret with other trafaret or with a function.

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

The checker test that a received string match with given regexp. With this
Regexp you can write you own checker like Email or URL.

    >>> t.Regexp(regexp=r"\w{3}-\w{3}-\w{4}").check('544-343-7564')
    '544-343-7564'

RegexpRaw
.........

With this checker you can use all ``re.match`` power to extract from strings dicts
and other higher level datastructures.

    >>> name_checker = t.RegexpRaw(r'^name=(\w+)$') >> (lambda m: m.groups()[0])
    >>> name_checker.check('name=Jeff')
    'Jeff'

or more interesting example:

    >>> from datetime import datetime
    >>>
    >>> def to_datetime(m):
    >>>    return datetime(*[int(i) for i in m.groups()])
    >>>
    >>> date_checker = t.RegexpRaw(regexp='^year=(\d+), month=(\d+), day=(\d+)$') >> to_datetime
    >>>
    >>> date_checker.check('year=2019, month=07, day=23')
    datetime.datetime(2019, 7, 23, 0, 0)

Bytes
.....

Also if you want to check, is value bytes string or no you can use this checker.

    >>> t.Bytes().check(b'bytes string')

AnyString
.........

If you need to check value which can be string or bytes string, you can use
``AnyString``.

    >>> for item in ['string', b'bytes string']:
    >>>     print(t.AnyString().check(item))
    string
    b'bytes string'

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

This checker tests that given value is in the list of arguments passed to Enum. List of arguments can contain values of different types. 

Example::

  >>> t.Enum(1, 2, 'error').check(2)
  2

This checker can be used to validate user choice/input with predefined variants, for example defect severity in the bug tracking system.

Example::

  >>> user_choice = 'critical'
  >>> severities = ('trivial', 'minor', 'major', 'critical')
  >>> t.Enum(*severities).check(user_choice)
  'critical'


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
-----


Forward
.......


Guard
.....


GuardError
..........
