Introducing trafaret
====================

Trafaret is validation library with support to convert data structures.
Sample usage::

    import datetime
    import trafaret as t

    date = t.Dict(year=t.Int, month=t.Int, day=t.Int) >> (lambda d: datetime.datetime(**d))
    assert date.check({'year': 2012, 'month': 1, 'day': 12}) == datetime.datetime(2012, 1, 12)

``t.Dict`` creates new dict structure validator with three ``t.Int`` elements.
``>>`` operation adds lambda function to the converters of given checker.
Some checkers have default converter, but when you use ``>>`` or ``.append``,
you disable default converter with your own.

This does not mean that ``Int`` will not convert numbers to integers,
this mean that some checkers, like ``String`` with regular expression,
have special converters applied them and can be overriden.

Converters can be chained. You can raise ``DataError`` in converters.

Features
--------

Trafaret has very handy features, read below some samples.

Regexp
......

``RegexpRow`` can work with regular expressions::

    >>> c = t.RegexpRow(r'^name=(\w+)$') >> (lambda m: m.groups()[0])
    >>> c.check('name=Jeff')
    'Jeff'

You can use all ``re.match`` power to extract from strings dicts and
other higher level datastructures.


Dict and Key
............

``Dict`` take as argument dictionaries with string keys and checkers
as value, like ``{'a': t.Int}``. But instead of a string key you can
use the ``Key`` class. A ``Key`` instance can rename the given key
name to something else::

    >>> c = t.Dict({t.Key('uNJ') >> 'user_name': t.String})
    >>> c.check({'uNJ': 'Adam'})
    {'user_name': 'Adam'}

And we can do more with the right converter::

    >>> from trafaret.utils import fold
    >>> c = t.Dict({t.Key('uNJ') >> 'user__name': t.String}) >> fold
    >>> c.check({'uNJ': 'Adam'})
    {'user': {'name': 'Adam'}}

We have some example of enhanced ``Key`` in extras::

    >>> from trafaret.extras import KeysSubset
    >>> cmp_pwds = lambda x: {'pwd': x['pwd'] if x.get('pwd') == x.get('pwd1') else DataError('Not equal')}
    >>> d = Dict({KeysSubset('pwd', 'pwd1'): cmp_pwds, 'key1': String})
    >>> d.check({'pwd': 'a', 'pwd1': 'a', 'key1': 'b'}).keys()
    {'pwd': 'a', 'key1': 'b'}

DataError
---------

Exception class that is used in the library. Exception hold errors in
``error`` attribute.  For simple checkers it will be just a
string. For nested structures it will be `dict` instance.

Trafaret
--------

Base class for checkers. Use it to create new checkers.  In derrived
classes you need to implement `_check` or `_check_val`
methods. `_check_val` must return a value, `_check` must return `None`
on success.

You can implement `converter` method if you want to convert value
somehow, that said you prolly want to make it possible for the
developer to apply their own converters to raw data. This used to
return strings instead of `re.Match` object in `String` trafaret.

Subclassing
-----------

For your own trafaret creation you need to subclass ``Trafaret`` class
and implement ``check_value`` or ``check_and_return``
methods. ``check_value`` can return nothing on success,
``check_and_return`` must return value. In case of failure you need to
raise ``DataError``.  You can use ``self._failure`` shortcut function
to do this.  Check library code for samples.

Type
----

Checks that data is instance of given class.  Just instantitate it
with any class, like `int`, `float`, `str`.  For instancce::

    >>> t.Type(int).check(4)
    4

Any
---

Will match any element.

Or
--

`Or` takes other converters as arguments. The input is considered
valid if one of the converters succeed::

    >>> Or(t.Int, t.Null).check(None)
    None
    >>> (t.Int | t.Null).check(5)
    5

Null
----

Value must be `None`.

Bool
----

Check if value is a boolean::

    >>> t.Bool().check(True)
    True

Float
-----

Check if value is a float or can be converted to a float. Supports
``lte``, ``gte``, ``lt``, ``gt`` parameters::

    >>> t.Float(gt=3.5).check(4)
    4

Int
---

Similar to ``Float``, but checking for int::

    >>> t.Int(gt=3).check(4)
    4

Atom
----

Value must be exactly equal to Atom first arg::

    >>> t.Atom('this_key_must_be_this').check('this_key_must_be_this')
    'this_key_must_be_this'

This may be useful in ``Dict`` with ``Or`` statements to create
enumerations.


String, Email, URL
------------------

Basicaly just check that argument is a string.

Argument ``allow_blank`` indicates if string can be blank or not.

If you provide a ``regex`` parameter - it will return ``re`` match
object.  Default converter will return ``match.group()`` result.

``Email`` and ``URL`` just provide regular expressions and a bit of
logic for IDNA domains.  Default converters return email and domain,
but you will get ``re`` match object in converter.

Here is some examples to make things clear::

    >>> t.String().check('werwerwer')
    'werwerwer'
    >>> t.String(regex='^\s+$').check('   ')
    '   '
    >>> t.String(regex='^name=(\w+)$').check('name=Jeff')
    'Jeff'

And one wild sample::

    >>> todt = lambda  m: datetime(*[int(i) for i in m.groups()])
    >>> (t.String(regex='^year=(\d+),month=(\d+),day=(\d+)$') >> todt).check('year=2011,month=07,day=23')
    datetime.datetime(2011, 7, 23, 0, 0)

List
----

Just List of elements of one type. In converter you will get list of converted elements.

Sample::

    >>> t.List(t.Int).check(range(100))
    [0, 1, 2, ... 99]
    >>> t.extract_error(t.List(t.Int).check(['a']))
    {0: 'value cant be converted to int'}

Dict
----

`Dict` include named parameters. You can use for keys plain strings
and ``Key`` instances.  In case you provide just string keys, they
will converted to ``Key`` instances. Actual checking proceeded with
``Key`` instance.

Methods:

- ``allow_extra(*names)`` : where ``names`` can be key names or ``*``
  to allow any additional keys.

- ``make_optional(*names)`` : where ``names`` can be key names or
  ``*`` to make all options optional.

- ``ignore_extra(*names)``: where ``names`` are the names of the keys
  or ``*`` to exclude listed key names or all unspecified ones from
  the validation process and final result

- ``merge(Dict|dict|[t.Key...])`` : where argument can be other
  ``Dict``, ``dict`` like provided to ``Dict``, or list of
  ``Key``s. Also provided as ``__add__``, so you can add ``Dict``s,
  like ``dict1 + dict2``.

Key
...

Special class to create dict keys. Parameters are:

- `name` - key name
- `default` - default if key is not present
- `optional` - if `True` the key is optional
- `to_name` - allows to rename the key

You can provide ``to_name`` with ``>>`` operation::
  
    Key('javaStyleData') >> 'plain_cool_data'

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


KeysSubset
..........

Experimental feature, not stable API. Sometimes you need to make
something with part of dict keys.  So you can::

    >>> join = (lambda d: {'name': ' '.join(d.values())})
    >>> Dict({KeysSubset('name', 'last'): join}).check({'name': 'Adam', 'last': 'Smith'})
    {'name': 'Smith Adam'}

As you can see you need to return a `dict` from checker.

Error raise
...........

In ``Dict`` you can just return error from checkers or converters,
there is need not to raise them.


Mapping
-------

Check both keys and values::

    >>> trafaret = Mapping(String, Int)
    >>> trafaret
    <Mapping(<String> => <Int>)>
    >>> trafaret.check({"foo": 1, "bar": 2})
    {'foo': 1, 'bar': 2}

Enum
----

Example::

  >>> Enum(1, 2, 'error').check(2)
  2

Callable
--------

Check if data is callable.

Call
----

Take a function that will be called in ``check``. Function must return value or ``DataError``.

Forward
-------

This checker is container for any checker, that you can provide later.
To provide container use ``provide`` method or ``<<`` operation::

    >> node = Forward()
    >> node << Dict(name=String, children=List[node])

guard
-----

Decorator for function::

    >>> @guard(a=String, b=Int, c=String)
    ... def fn(a, b, c="default"):
    ...     '''docstring'''
    ...     return (a, b, c)

GuardError
..........

Derived from ``DataError``.
