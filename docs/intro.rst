Introducing
===========

Trafaret is validation library with support to convert data structures.
Sample usage:

.. code-block:: python

    import datetime
    import trafaret as t

    date = t.Dict(year=t.Int, month=t.Int, day=t.Int) & (lambda d: datetime.datetime(**d))

    def validate_date(data):
        try:
            return date.check(data), False
        except t.DataError as e:
            return False, e.as_dict()

    validate_date({'year': 2012, 'month': 1})
    # (False, {'day': 'is required'})

    validate_date({'year': 2012, 'month': 1, 'day': 12})
    # (datetime.datetime(2012, 1, 12, 0, 0), False)

``t.Dict`` creates new dict structure validator with three ``t.Int`` elements.
``&`` operation combines trafaret with other trafaret or with a function.

Types
-----


String
......

The ``String`` is base checker in trafaret which just test that value is string.
Also ``String`` has a lot of helpful modification like ``Email`` and ``Url``.

.. code-block:: python

    t.String().check('this is my string')
    # 'this is my string'

Options:

    - **allow_blank** *(boolean)* - indicates if string can be blank or not
    - **min_length** *(integer)* - validation for minimum length of receive string
    - **max_length** *(integer)* - validation for maximum length of receive string

The simple examples of usage:

.. code-block:: python

    t.String(allow_blank=True).check('')
    # ''
    t.String(min_length=1, max_length=10).check('no so long')
    # 'no so long'

``Email`` and ``URL`` just provide regular expressions and a bit of logic for
IDNA domains. Default converters return email and domain, but you will get re
match object in converter.

Email
~~~~~
This checker test that a received string is an valid email address.

.. code-block:: python

    t.Email.check('someone@example.net')
    # 'someone@example.net'

URL
~~~
This checker test that a received string is an valid URL address. This URL can
include get params and anchors.

.. code-block:: python

    t.URL.check('http://example.net/resource/?param=value#anchor')
    # 'http://example.net/resource/?param=value#anchor'

IPv4
~~~~
This checker test that a received string is IPv4 address.

.. code-block:: python

    t.IPv4.check('127.0.0.1')
    # '127.0.0.1'

IPv6
~~~~
This checker test that a received string is IPv6 address.

.. code-block:: python

    t.IPv6.check('2001:0db8:0000:0042:0000:8a2e:0370:7334')
    # '2001:0db8:0000:0042:0000:8a2e:0370:7334'

IP
~~
This checker test that a received string is IP address (IPv4 or IPv6).

.. code-block:: python

    t.IP.check('127.0.0.1')
    # '127.0.0.1'
    t.IP.check('2001:0db8:0000:0042:0000:8a2e:0370:7334')
    # '2001:0db8:0000:0042:0000:8a2e:0370:7334'

Regexp
......

The checker test that a received string match with given regexp. With this
Regexp you can write you own checker like Email or URL.

.. code-block:: python

    t.Regexp(regexp=r"\w{3}-\w{3}-\w{4}").check('544-343-7564')
    # '544-343-7564'

RegexpRaw
.........

With this checker you can use all ``re.match`` power to extract from strings dicts
and other higher level datastructures.

.. code-block:: python

    name_checker = t.RegexpRaw(r'^name=(\w+)$') >> (lambda m: m.groups()[0])
    name_checker.check('name=Jeff')
    # 'Jeff'

or more interesting example:

.. code-block:: python

    from datetime import datetime
    
    def to_datetime(m):
       return datetime(*[int(i) for i in m.groups()])
    
    date_checker = t.RegexpRaw(regexp='^year=(\d+), month=(\d+), day=(\d+)$') & to_datetime
    
    date_checker.check('year=2019, month=07, day=23')
    # datetime.datetime(2019, 7, 23, 0, 0)

Bytes
.....

Also if you want to check, is value bytes string or no you can use this checker.

.. code-block:: python

    t.Bytes().check(b'bytes string')

AnyString
.........

If you need to check value which can be string or bytes string, you can use
``AnyString``.

.. code-block:: python

    for item in ['string', b'bytes string']:
        print(t.AnyString().check(item))

    # string
    # b'bytes string'

FromBytes
.........

If you need to convert bytestring to ``utf-8`` or to the other standard you can use
this checker. If receive value can't be converted to standard then trafaret
raise an error. This often can be useful when receive value can be a ``string``
or a ``bytestring``.

.. code-block:: python

    unicode_or_utf16 = t.String | t.FromBytes(encoding='utf-16')
    
    unicode_or_utf16.check(b'\xff\xfet\x00r\x00a\x00f\x00a\x00r\x00e\x00t\x00')
    # 'trafaret'

    unicode_or_utf16.check('trafaret')
    # 'trafaret'

The default encoding is ``utf-8``.

.. code-block:: python

    t.FromBytes().check(b'trafaret')
    # 'trafaret'

Dict and Keys
.............

The ``Dict`` checker is needed to validate a dictionaries. For use ``Dict`` you
need to describe your dictionary as dictionary where instead of values are
checkers of this values.

.. code-block:: python

    login_validator = t.Dict({'username': t.String(max_length=10), 'email': t.Email}) 
    login_validator.check({'username': 'Misha', 'email': 'misha@gmail.com'})
    # {'username': 'Misha', 'email': 'misha@gmail.com'}

``Dict`` has a lot of helpful methods:

    - ``allow_extra`` - when you need to validate only a part of keys you can use allow_extra to allow to do that:

    .. code-block:: python

        data = {'username': 'Misha', 'age': 12, 'email': 'm@gmail.com', 'is_superuser': True}
        
        user_validator = t.Dict({'username': t.String, 'age': t.Int})
        
        # generate a new checker with allow any extra keys
        new_user_validator = user_validator.allow_extra('*')
        new_user_validator.check(data)
        # {'username': 'Misha', 'age': 12, 'email': 'm@gmail.com', 'is_superuser': True}

    Also if you want to allow only some concretical kyes you cat set them:

    .. code-block:: python

        user_validator.allow_extra('email', 'is_superuser')

    If when you need to specify type of extra keys you can use ``trafaret``
    keyword argument for that *(by default trafaret is Any)*:

    .. code-block:: python

        user_validator.allow_extra('email', 'is_superuser', trafaret=t.String)

    Also you can specify extra keys when you create your ``Dict`` checker:

    .. code-block:: python

        user_validator = t.Dict({'username': t.String, 'age': t.Int}, allow_extra=['*'])

    - ``ignore_extra`` - when you need to remove nececary data from result you can use it.
      This method has similar signature like in ``allow_extra``.

    .. code-block:: python

        data = {'username': 'Misha', 'age': 12, 'email': 'm@gmail.com', 'is_superuser': True}

        user_validator = t.Dict({'username': t.String, 'age': t.Int}).ignore_extra('*')
        user_validator.check(data)
        # {'username': 'Misha', 'age': 12}

    - ``merge`` - where argument can be other ``Dict``, dict like provided to ``Dict``,
      or list of ``Key`` s. Also provided as ``__add__``, so you can add ``Dict`` s, like ``dict1 + dict2``.
      
      This can be so useful when you have two large dictionaries with so similar structure.
      As example it possible when you do validation for create and update some
      instance whan for create instance you don't need `id` but for update do.

    .. code-block:: python

        user_create_validator = t.Dict({'username': t.String, 'age': t.Int})
        
        user_update_validator = user_create_validator + {'id': t.Int}
        user_update_validator.check({'username': 'misha', 'age': 12, 'id': 1})
        # {'username': 'misha', 'age': 12, 'id': 1}


Some time we need to change name of key in initial dictionary. For that
trafaret provides ``Key``. This can be very useful. As example when you receive
form from frontend with keys in camel case and you want to convert this keys to
snake case.

.. code-block:: python

    login_validator = t.Dict({t.Key('userName') >> 'user_name': t.String})
    login_validator.check({'userName': 'Misha'})
    # {'user_name': 'Misha'}

Also we can to receive input data like this:

.. code-block:: python

    data = {"title": "Glue", "authorFirstName": "Irvine", "authorLastName": "Welsh"}

and want to split data which connected with author and book. For that we can 
use ``fold``.

.. code-block:: python

    from trafaret.utils import fold
    
    book_validator = t.Dict({
        "title": t.String,
        t.Key('authorFirstName') >> 'author__first_name': t.String,
        t.Key('authorLastName') >> 'author__last_name': t.String,
    }) >> fold
    
    book_validator.check(data)
    # {'author': {'first_name': 'Irvine', 'last_name': 'Welsh'}, 'title': 'Glue'}

Key
~~~

Special class to create dict keys. Parameters are:

- `name` - key name
- `default` - default if key is not present
- `optional` - if True the key is optional
- `to_name` - allows to rename the key

Below you can to see a good example of usage all of these parameters:

.. code-block:: python

    import hashlib
    
    hash_md5 = lambda d: hashlib.md5(d.encode()).hexdigest()
    comma_to_list = lambda d: [s.strip() for s in d.split(',')]
    
    converter = t.Dict({
       t.Key('userNameFirst') >> 'name': t.String,
       t.Key('userNameSecond') >> 'second_name': t.String,
       t.Key('userPassword') >> 'password': hash_md5,
       t.Key('userEmail', optional=True, to_name='email'): t.String,
       t.Key('userTitle', default='Bachelor', to_name='title'): t.String,
       t.Key('userRoles', to_name='roles'): comma_to_list,
    })

We can rewrite it to:

.. code-block:: python

    converter = t.Dict(
       t.Key('userNameFirst', to_name='name', trafaret=t.String),
       t.Key('userNameSecond', to_name='second_name', trafaret=t.String),
       t.Key('userPassword', to_name='password', trafaret=hash_md5),
       t.Key('userEmail', optional=True, to_name='email', trafaret=t.String),
       t.Key('userTitle', default='Bachelor', to_name='title', trafaret=t.String),
       t.Key('userRoles', to_name='roles', trafaret=comma_to_list),
    )

It provides method ``__call__(self, data)`` that extract key value
from data through mapping ``get`` method.
Key ``__call__`` method yields ``(key name, Maybe(DataError), [touched
keys])`` triples.
You can redefine ``get_data(self, data, default)`` method in
subclassed ``Key`` if you want to use something other then
``.get(...)`` method. Like this for the `aiohttp
<http://aiohttp.readthedocs.io/>`_'s `MultiDict` class::

    class MDKey(t.Key):
        def get_data(data, default):
            return data.get_all(self.name, default)

    t.Dict({MDKey('users'): t.List(t.String)})

Moreover, instead of ``Key`` you can use any callable, say a function::

    def simple_key(value):
        yield 'simple', 'simple data', []

    check_args = t.Dict(simple_key)

DictKeys
~~~~~~~~

If you need to check just that dictionary has all given keys so ``DictKeys``
is a good approach for that.

.. code-block:: python

    t.DictKeys(['a', 'b']).check({'a': 1, 'b': 2})
    # {'a': 1, 'b': 2}

KeysSubset
~~~~~~~~~~

We have some example of enhanced ``Key`` in extras:

.. code-block:: python

    from trafaret.extras import KeysSubset

    cmp_pwds = lambda x: {
        'pwd': x['pwd'] if x.get('pwd') == x.get('pwd1') else DataError('Not equal')
    }

    d = Dict({KeysSubset('pwd', 'pwd1'): cmp_pwds, 'key1': String})

    d.check({'pwd': 'a', 'pwd1': 'a', 'key1': 'b'}).keys()
    # {'pwd': 'a', 'key1': 'b'}

Mapping
.......

This checker test that a received dictionary has current types of keys and
values.

.. code-block:: python

    t.Mapping(t.String, t.Int).check({"foo": 1, "bar": 2})
    # {'foo': 1, 'bar': 2}

Where a first argument is a type of keys and second is type of values.

Bool
....

The checker test that a received value is a boolean type.

.. code-block:: python
    
    t.Bool().check(True)
    # True

ToBool
......

If you need to check value that can be equivalent to a boolean type, you can use ``ToBool``.
**Letter case doesn't matter.**

Sample with all supported equivalents:

.. code-block:: python

    equivalents  = ('t', 'true', 'y', 'yes', 'on', '1',\
                    'false', 'n', 'no', 'off', '0', 'none')

    for value in equivalents:
      print("%s is %s" % (value, t.ToBool().check(value)))

    # t is True
    # true is True
    # y is True
    # yes is True
    # on is True
    # 1 is True
    # false is False
    # n is False
    # no is False
    # off is False
    # 0 is False
    # none is False

Also, function can take ``1`` and ``0`` as integers, ``booleans`` and ``None``.

.. code-block:: python

    t.ToBool().check(1)
    # True

    t.ToBool().check(False)
    # False

    t.ToBool().check(None)
    # False

Float
.....

Check if value is a float or can be converted to a float.
Supports ``lte``, ``gte``, ``lt``, ``gt`` parameters,
``<=``, ``>=``, ``<``, ``>`` operators and ``Float[0:10]`` slice notation:

.. code-block:: python

    t.Float(gt=3.5).check(4)
    # 4

    (t.Float >= 3.5).check(4)
    # 4

    t.Float[3.5:].check(4)
    # 4

ToFloat
.......

Similar to ``Float``, but converting to ``float``:

.. code-block:: python

    t.ToFloat(gte=3.5).check(4)
    # 4.0

ToDecimal
.........

Similar to ``ToFloat``, but converting to ``Decimal``:

.. code-block:: python

    from decimal import Decimal, ROUND_HALF_UP
    import trafaret as t

    validator = t.Dict({
        "name": t.String,
        "salary": t.ToDecimal(gt=0) & (
            lambda value: value.quantize(
                    Decimal('.0000'), rounding=ROUND_HALF_UP
                )
        ),
    })

    validator.check({"name": "Bob", "salary": "1000.0"})
    # {'name': 'Bob', 'salary': Decimal('1000.0000')}

    validator.check({"name": "Tom", "salary": 1000.0005})
    # {'name': 'Tom', 'salary': Decimal('1000.0005')}

    validator.check({"name": "Jay", "salary": 1000.00049})
    # {'name': 'Jay', 'salary': Decimal('1000.0005')}

    validator.check({"name": "Joe", "salary": -1000})
    # DataError: {'salary': DataError('value should be greater than 0')}

Int
...

Similar to ``Float``, but checking for ``int``:

.. code-block:: python

    t.Int(gt=3).check(4)
    # 4

ToInt
.....

Similar to ``Int``, but converting to ``int``:

.. code-block:: python

    import trafaret as t
    from yarl import URL

    query_validator = t.Dict({
        t.Key('node', default=0): t.ToInt(gte=0),
    })

    url = URL('https://www.amazon.com/b?node=18637575011')
    query_validator.check(url.query)
    # {'node': 18637575011}

    url = URL('https://www.amazon.com/b')
    query_validator.check(url.query)
    # {'node': 0}

    url = URL('https://www.amazon.com/b?node=-10')
    query_validator.check(url.query)
    # DataError: {'node': DataError('value is less than 0')}


Null
....

This checker test that a received value is ``None``. This checker is very
useful together with other checkers when you need to test that receive value
has some type or ``None``.

.. code-block:: python

    (t.Int | t.Null).check(5)
    # 5

    (t.Int | t.Null).check(None)
    # None

Any
...

This checker doesn't check anything. This is very often use in ``Dict`` to
test that some key exists in the dictionary, but doesn't care what type it is.

.. code-block:: python

    t.Dict({"value": t.Any}).check({"value": "123"})
    # {'value': '123'}

This is the same with ``allow_extra`` method in ``Dict``.

Type
....

Checks that data is instance of given class. Just instantiate it with any
class, like int, float, str. For instance:

.. code-block:: python

    t.Type(int).check(4)
    # 4


Atom
----

This checker test that a received value is equal with first argument.

.. code-block:: python

    t.Atom('this_key_must_be_this').check('this_key_must_be_this')
    # 'this_key_must_be_this'

This may be useful in ``Dict`` with ``Or`` statements to create
enumerations.

Date
....

Check that argument is an instance of ``datetime.date`` object::

    >>> t.Date().check("2019-07-25")
    '2019-07-25'
    >>> t.Date().check(date.today())
    datetime.date('2019-07-25')

You can easily specify the format for ``Date`` trafaret::

    >>> t.Date(format='%y-%m-%d')
    '<Date %y-%m-%d>'
    >>> t.Date(format='%y-%m-%d').check('00-01-01')
    '00-01-01'

ToDate
......

Behave like ``Date``, but also returns ``datetime.date`` object::

    >>> t.ToDate().check("2019-07-25")
    datetime.date('2019-07-25')
    >>> t.ToDate().check(datetime.now())
    datetime.date('2019-07-25')

DateTime
........

Similar to ``Date``, but checking for ``datetime.datetime`` object::

    >>> DateTime('%Y-%m-%d %H:%M').check("2019-07-25 21:45")
    '2019-07-25 21:45'
    >>> t.extract_error(t.DateTime(), date.today())
    'value `2019-09-22` cannot be converted to datetime'


ToDateTime
..........

Behave like ``DateTime``, but also returns ``datetime.datetime`` object::

    >>> DateTime('%Y-%m-%d %H:%M').check("2019-07-25 21:45")
    datetime.datetime(2019, 7, 25, 21, 45)


List
....

This checker test that a received value is a list of items with some type.

.. code-block:: python

    t.List(t.Int).check(range(100))
    # [0, 1, 2, ... 99]

    t.extract_error(t.List(t.Int).check(['a']))
    # {0: DataError("value can't be converted to int")}

Also if an item has possible two or three types you can use ``Or``.

.. code-block:: python

    t.List(t.ToInt | t.String).check(['1', 'test'])
    # [1, 'test']

Options:

    - **min_length** *(integer)* - validation for minimum length of receive list
    - **max_length** *(integer)* - validation for maximum length of receive list

The simple examples of usage:

.. code-block:: python

    t.List(t.Int, min_length=1, max_length=2).check(['1', '2'])
    # ['1', '2']


Iterable
........

This checker is the same with ``List`` but it don't raise error if received
value isn't instance of a ``list``.

.. code-block:: python

    my_data = (1, 2)

    try:
        t.List(t.Int, min_length=1, max_length=2).check(my_data)
    except t.DataError as e:
        print(e)    
    # value is not a list

    t.Iterable(t.Int, max_length=2).check(my_data)
    # [1, 2]


Tuple
.....

This checker test that a received value is a tuple of items with some type.

.. code-block:: python

    t.Tuple(t.ToInt, t.ToInt, t.String).check([3, 4, u'5'])
    # (3, 4, u'5')

Enum
....

This checker tests that given value is in the list of arguments passed to Enum. List of arguments can contain values of different types. 

Example:

.. code-block:: python

  t.Enum(1, 2, 'error').check(2)
  # 2

This checker can be used to validate user choice/input with predefined variants, for example defect severity in the bug tracking system.

Example:

.. code-block:: python

  user_choice = 'critical'
  severities = ('trivial', 'minor', 'major', 'critical')

  t.Enum(*severities).check(user_choice)
  # 'critical'


Callable
........

This checker test that a received value is callable.

.. code-block:: python

    t.Callable().check(lambda: 1)

Call
....

This checker receive custom function for validation and convert value. If value
is valid then function return converted value else raise ``DataError``.

.. code-block:: python

    def validator(value):
        """The custom validation function.""""
        if value != "foo":
            return t.DataError("I want only foo!", code='i_wanna_foo')
        return 'foo'
    
    t.Call(validator).check('foo')
    # 'foo'


Operations
----------

Or
..

You can combine checkers and for that you need to use ``Or``.
``Or`` takes other converters as arguments. The input is considered valid if one
of the converters succeed:

.. code-block:: python

    Or(t.Int, t.String).check('1')
    # 1

but the more popular way it is using ``|``

.. code-block:: python

    (t.Int | t.String).check('five')
    # 'five'

fold
....

We already talked about ``fold`` but let's see all features of this utils.

The parameters:

    - `prefix` - the prefix which need to remove
    - `delimeter` - the parameter which use for split to keys

The full example:

.. code-block:: python

    new_fold = lambda x: fold(x, 'data', '.')
    
    book_validator = t.Dict({
        "data.author.first_name": t.String,
        "data.author.last_name": t.String,
    }) >> new_fold
    
    book_validator.check({
       "data.author.first_name": 'Irvine',
       "data.author.last_name": 'Welsh',
    })
    # {'author': {'first_name': 'Irvine', 'last_name': 'Welsh'}}


subdict
.......

Very often when we do validation of the form we need to validate values which
depend on each other. As example it can be `password` and `second_password`.
For cases like this a trafaret has ``subdict``.

.. code-block:: python

    from trafaret.keys import subdict

    def check_passwords_equal(data):
        if data['password'] != data['password_confirm']:
            return t.DataError('Passwords are not equal')
        return data['password']
    
    passwords_key = subdict(
        'password',
        t.Key('password', trafaret=t.String(max_length=10)),
        t.Key('password_confirm', trafaret=t.String(max_length=10)),
        trafaret=check_passwords_equal,
    )
    
    signup_trafaret = t.Dict(
        t.Key('email', trafaret=t.Email),
        passwords_key,
    )
    
    signup_trafaret.check({
        "email": "m@gmail.com",
        "password": "111",
        "password_confirm": "111",
    }) 
    # {'email': 'm@gmail.com', 'password': '111'}

As you can see, `password` and `password_confirm` replaced to just password with value that ``check_passwords_equal`` return.

Other
-----

Forward
.......

This checker is container for any checker, that you can provide later.
To provide container use ``provide`` method or ``&`` operation:

.. code-block:: python

    node = t.Forward()
    node & t.Dict(name=t.String, children=t.List[node])

guard
.....

This is decorator for functions. You can validate and convert receive arguments.

.. code-block:: python

    @t.guard(user_name=t.String(max_length=10), age=t.ToInt, is_superuser=t.Bool)
    def create_user(user_name, age, is_superuser=False):
       # do some stuff
       ...
       return (user_name, age, is_superuser)

    create_user('Misha', '12')
    # ('Misha', 12, False)
    # convert age to integer


GuardError
~~~~~~~~~~

The `guard` raise ``GuardError`` error that base by ``DataError``.
