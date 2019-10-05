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
    >>> date_checker = t.RegexpRaw(regexp='^year=(\d+), month=(\d+), day=(\d+)$') & to_datetime
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

If you need to convert bytestring to ``utf-8`` or to the other standard you can use
this checker. If receive value can't be converted to standard then trafaret
raise an error. This often can be useful when receive value can be a ``string``
or a ``bytestring``.

    >>> unicode_or_utf16 = t.String | t.FromBytes(encoding='utf-16')
    >>>
    >>> unicode_or_utf16.check(b'\xff\xfet\x00r\x00a\x00f\x00a\x00r\x00e\x00t\x00')
    'trafaret'
    >>> unicode_or_utf16.check('trafaret')
    'trafaret'

The default encoding is ``utf-8``.

    >>> t.FromBytes().check(b'trafaret')
    'trafaret'

Dict and Keys
.............

The ``Dict`` checker is needed to validate a dictionaries. For use ``Dict`` you
need to describe your dictionary as dictionary where instead of values are
checkers of this values.

    >>> login_validator = t.Dict({'username': t.String(max_length=10), 'email': t.Email}) 
    >>> login_validator.check({'username': 'Misha', 'email': 'misha@gmail.com'})
    {'username': 'Misha', 'email': 'misha@gmail.com'}

``Dict`` has a lot of helpful methods:

    - ``allow_extra`` - when you need to validate only a part of keys you can use allow_extra to allow to do that:

    >>> data = {'username': 'Misha', 'age': 12, 'email': 'm@gmail.com', 'is_superuser': True}
    >>>
    >>> user_validator = t.Dict({'username': t.String, 'age': t.Int})
    >>>
    >>> # generate a new checker with allow any extra keys
    >>> new_user_validator = user_validator.allow_extra('*')
    >>> new_user_validator.check(data)
    {'username': 'Misha', 'age': 12, 'email': 'm@gmail.com', 'is_superuser': True}

    Also if you want to allow only some concretical kyes you cat set them:

    >>> user_validator.allow_extra('email', 'is_superuser')

    If when you need to specify type of extra keys you can use ``trafaret``
    keyword argument for that *(by default trafaret is Any)*:

    >>> user_validator.allow_extra('email', 'is_superuser', trafaret=t.String)

    Also you can specify extra keys when you create your ``Dict`` checker:

    >>> user_validator = t.Dict({'username': t.String, 'age': t.Int}, allow_extra=['*'])

    - ``ignore_extra`` - when you need to remove nececary data from result you can use it.
      This method has similar signature like in ``allow_extra``.

    >>> data = {'username': 'Misha', 'age': 12, 'email': 'm@gmail.com', 'is_superuser': True}
    >>>
    >>> user_validator = t.Dict({'username': t.String, 'age': t.Int}).ignore_extra('*')
    >>> user_validator.check(data)
    {'username': 'Misha', 'age': 12}

    - ``merge`` - where argument can be other ``Dict``, dict like provided to ``Dict``,
      or list of ``Key`` s. Also provided as ``__add__``, so you can add ``Dict`` s, like ``dict1 + dict2``.
      
      This can be so useful when you have two large dictionaries with so similar structure.
      As example it possible when you do validation for create and update some
      instance whan for create instance you don't need `id` but for update do.

    >>> user_create_validator = t.Dict({'username': t.String, 'age': t.Int})
    >>>
    >>> user_update_validator = user_create_validator + {'id': t.Int}
    >>> user_update_validator.check({'username': 'misha', 'age': 12, 'id': 1})
    {'username': 'misha', 'age': 12, 'id': 1}


Some time we need to change name of key in initial dictionary. For that
trafaret provides ``Key``. This can be very useful. As example when you receive
form from frontend with keys in camel case and you want to convert this keys to
snake case.

    >>> login_validator = t.Dict({t.Key('userName') >> 'user_name': t.String})
    >>> login_validator.check({'userName': 'Misha'})
    {'user_name': 'Misha'}

Also we can to receive input data like this:

    >>> data = {"title": "Glue", "authorFirstName": "Irvine", "authorLastName": "Welsh"}

and want to split data which connected with author and book. For that we can 
use ``fold``.

    >>> from trafaret.utils import fold
    >>>
    >>> book_validator = t.Dict({
    >>>     "title": t.String,
    >>>     t.Key('authorFirstName') >> 'author__first_name': t.String,
    >>>     t.Key('authorLastName') >> 'author__last_name': t.String,
    >>> }) >> fold
    >>>
    >>> book_validator.check(data)
    {'author': {'first_name': 'Irvine', 'last_name': 'Welsh'}, 'title': 'Glue'}

Key
~~~

Special class to create dict keys. Parameters are:

- `name` - key name
- `default` - default if key is not present
- `optional` - if True the key is optional
- `to_name` - allows to rename the key

Below you can to see a good example of usage all of these parameters:

    >>> import hashlib
    >>>
    >>> hash_md5 = lambda d: hashlib.md5(d.encode()).hexdigest()
    >>> comma_to_list = lambda d: [s.strip() for s in d.split(',')]
    >>>
    >>> converter = t.Dict({
    >>>    t.Key('userNameFirst') >> 'name': t.String,
    >>>    t.Key('userNameSecond') >> 'second_name': t.String,
    >>>    t.Key('userPassword') >> 'password': hash_md5,
    >>>    t.Key('userEmail', optional=True, to_name='email'): t.String,
    >>>    t.Key('userTitle', default='Bachelor', to_name='title'): t.String,
    >>>    t.Key('userRoles', to_name='roles'): comma_to_list,
    >>> })

DictKeys
~~~~~~~~

If you need to check just that dictionary has all given keys so ``DictKeys``
is a good approach for that.

    >>> t.DictKeys(['a', 'b']).check({'a': 1, 'b': 2})
    {'a': 1, 'b': 2}

KeysSubset
~~~~~~~~~~

We have some example of enhanced ``Key`` in extras::

    >>> from trafaret.extras import KeysSubset
    >>> cmp_pwds = lambda x: {'pwd': x['pwd'] if x.get('pwd') == x.get('pwd1') else DataError('Not equal')}
    >>> d = Dict({KeysSubset('pwd', 'pwd1'): cmp_pwds, 'key1': String})
    >>> d.check({'pwd': 'a', 'pwd1': 'a', 'key1': 'b'}).keys()
    {'pwd': 'a', 'key1': 'b'}


Bool
....


StrBool
.......

Float
.....
Check if value is a float or can be converted to a float.
Supports ``lte``, ``gte``, ``lt``, ``gt`` parameters,
``<=``, ``>=``, ``<``, ``>`` operators and ``Float[0:10]`` slice notation::

    >>> t.Float(gt=3.5).check(4)
    4

    >>> (t.Float >= 3.5).check(4)
    4

    >>> t.Float[3.5:].check(4)
    4

ToFloat
.......
Similar to ``Float``, but converting to ``float``::

    >>> t.ToFloat(gte=3.5).check(4)
    4.0

ToDecimal
.........
Similar to ``ToFloat``, but converting to ``Decimal``::

    >>> from decimal import Decimal, ROUND_HALF_UP
    >>> import trafaret as t

    >>> validator = t.Dict({
    >>>     "name": t.String,
    >>>     "salary": t.ToDecimal(gt=0) & (
    >>>         lambda value: value.quantize(
                    Decimal('.0000'), rounding=ROUND_HALF_UP
                )
    >>>     ),
    >>> })

    >>> validator.check({"name": "Bob", "salary": "1000.0"})
    {'name': 'Bob', 'salary': Decimal('1000.0000')}

    >>> validator.check({"name": "Tom", "salary": 1000.0005})
    {'name': 'Tom', 'salary': Decimal('1000.0005')}

    >>> validator.check({"name": "Jay", "salary": 1000.00049})
    {'name': 'Jay', 'salary': Decimal('1000.0005')}

    >>> validator.check({"name": "Joe", "salary": -1000})
    DataError: {'salary': DataError('value should be greater than 0')}

Int
...
Similar to ``Float``, but checking for ``int``::

    >>> t.Int(gt=3).check(4)
    4

ToInt
.....
Similar to ``Int``, but converting to ``int``::

    >>> import trafaret as t
    >>> from yarl import URL

    >>> query_validator = t.Dict({
    >>>     t.Key('node', default=0): t.ToInt(gte=0),
    >>> })

    >>> url = URL('https://www.amazon.com/b?node=18637575011')
    >>> query_validator.check(url.query)
    {'node': 18637575011}

    >>> url = URL('https://www.amazon.com/b')
    >>> query_validator.check(url.query)
    {'node': 0}

    >>> url = URL('https://www.amazon.com/b?node=-10')
    >>> query_validator.check(url.query)
    DataError: {'node': DataError('value is less than 0')}


Null
....

This checker test that a received value is ``None``. This checker is very
useful together with other checkers when you need to test that receive value
has some type or ``None``.

    >>> (t.Int | t.Null).check(5)
    5
    >>> (t.Int | t.Null).check(None)

Any
...

This checker doesn't check anything. This is very often use in ``Dict`` to
test that some key exists in the dictionary, but doesn't care what type it is.

    >>> t.Dict({"value": t.Any}).check({"value": "123"})
    {'value': '123'}

This is the same with ``allow_extra`` method in ``Dict``.

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


Operations
----------

Or
..

You can combine checkers and for that you need to use ``Or``.
``Or`` takes other converters as arguments. The input is considered valid if one
of the converters succeed:

    >>> Or(t.Int, t.String).check('1')
    1

but the more popular way it is using ``|``

    >>> (t.Int | t.String).check('five')
    'five'

fold
....

We already talked about ``fold`` but let's see all features of this utils.

The parameters:

    - `prefix` - the prefix which need to remove
    - `delimeter` - the parameter which use for split to keys

The full example:

    >>> new_fold = lambda x: fold(x, 'data', '.')
    >>> 
    >>> book_validator = t.Dict({
    >>>     "data.author.first_name": t.String,
    >>>     "data.author.last_name": t.String,
    >>> }) >> new_fold
    >>>
    >>> book_validator.check({
    >>>    "data.author.first_name": 'Irvine',
    >>>    "data.author.last_name": 'Welsh',
    >>> })
    {'author': {'first_name': 'Irvine', 'last_name': 'Welsh'}}


subdict
.......

Very often when we do validation of the form we need to validate values which
depend on each other. As example it can be `password` and `second_password`.
For cases like this a trafaret has ``subdict``.

    >>> def check_passwords_equal(data):
    >>>     if data['password'] != data['password_confirm']:
    >>>         return t.DataError('Passwords are not equal')
    >>>     return data['password']
    >>>
    >>> passwords_key = subdict(
    >>>     'password',
    >>>     t.Key('password', trafaret=t.String(max_length=10)),
    >>>     t.Key('password_confirm', trafaret=t.String(max_length=10)),
    >>>     trafaret=check_passwords_equal,
    >>> )
    >>>
    >>> signup_trafaret = t.Dict(
    >>>     t.Key('email', trafaret=t.Email),
    >>>     passwords_key,
    >>> )
    >>>
    >>> signup_trafaret.check({
    >>>     "email": "m@gmail.com",
    >>>     "password": "111",
    >>>     "password_confirm": "111",
    >>> }) 
    {'email': 'm@gmail.com', 'password': '111'}


Other
-----

Forward
.......

This checker is container for any checker, that you can provide later.
To provide container use ``provide`` method or ``<<`` operation::

    >> node = t.Forward()
    >> node & t.Dict(name=t.String, children=t.List[node])

guard
.....

This is decorator for functions. You can validate and convert receive arguments.


    >>> @t.guard(user_name=t.String(max_length=10), age=t.ToInt, is_superuser=t.Bool)
    >>> def create_user(user_name, age, is_superuser=False):
    >>>    # do some stuff
    >>>    ...
    >>>    return (user_name, age, is_superuser)

    >>> create_user('Misha', '12')
    ('Misha', 12, False)
    >>> # convert age to integer


GuardError
~~~~~~~~~~

The `guard` raise ``GuardError`` error that base by ``DataError``.
