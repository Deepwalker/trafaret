Trafaret
========

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

This does not mean that ``Int`` will not
convert numbers to int, this mean that some checkers, like ``String`` with regular expression,
have special converters applied to  that can be overriden by your own.

Converters can be chained. You can raise ``DataError`` in converters.

Features
--------

Trafaret has very handy features, read below some samples.

Regex String
............

``String`` can work with regular expressions, and this givs you real power::

    >>> c = t.String(regex=r'^name=(\w+)$') >> (lambda m: m.groups()[0])
    >>> c.check('name=Jeff')
    'Jeff'

Some way you can use all re.Match power to extract from strings dicts and so on.


Dict and Key
............

``Dict`` get dict with keys and checkers, like  ``{'a': t.Int}``. But instead of string key
you can use ``Key`` class. And ``Key`` instance can rename given key name to something
else::

    >>> c = t.Dict(t.Key('uNJ') >> 'user_name': t.String})
    >>> c.check({'uNJ': 'Adam'})
    {'user_name': 'Adam'}

And we can do more with right converter::

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
-----------------------

Exception class that used in library. Exception hold errors in ``error`` attribute.
For simple checkers it will be just a string. For nested structures it will be `dict`
instance.

Trafaret
--------

Base class for checkers. Use it to make new checkers.
In derrived classes you need to implement `_check` or `_check_val`
methods. `_check_val` must return value, `_check` must return `None` on success.

You can implement `converter` method if you want to convert value somehow, but
want to make free for developer to apply his own converters to raw data. This
used to return strings instead of `Match` object in `String` trafaret.

Type
----

Checks that data is instance of given class.
Just instantitate it with any class, like int, float, str.
Sample::

    >>> Type(int).check(4)
    4

Any
---

Will match any element.

Or
--

Get other converters as args.
This samples are equivalent::

    >>> Or(t.Int, t.Null).check(None)
    None
    >>> (t.Int | t.Null).check(5)
    5

Null
----

Value must be `None`.

Bool
----
Check if value is boolean::

    >>> t.Bool.check(True)
    True

Float
-----
Check if value is float or can be converted to.
Supports ``lte``, ``gte``, ``lt``, ``gt`` parameters::

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

This may be useful in ``Dict`` in pair with ``Or`` statements.


String, Email, URL
------------------

Basicaly just check that arg is string.
Argument ``allow_blank`` indicates if string can be blank ot not.
If you will provide ``regex`` param - will return ``re.Match`` object.
Default converter will return ``match.group()`` result. You will get ``re.Match`` object
in converter.

``Email`` and ``URL`` just provide regular expressions and a bit of logic for IDNA domains.
Default converters return email and domain, but you will get ``re.Match`` in converter.

So, some examples to make things clear::

    >>> t.String().check('werwerwer')
    'werwerwer'
    >>> t.String(regex='^\s+$).check('   ')
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

Dict include named params. You can use for keys plain strings and ``Key`` instances.
In case you provide just string keys, they will converted to ``Key`` instances. Actual
checking proceeded in ``Key`` instance.

Methods:

``allow_extra(*names)`` : where ``names`` can be key names or ``*`` to allow any additional keys.

``make_optional(*names)`` : where ``names`` can be key names or ``*`` to make all options optional.

``ignore_extra(*names)``: where ``names`` are the names of the keys or ``*`` to exclude listed key names or all unspecified ones from the validation process and final result

Key
...

Special class to create dict keys. Parameters are:

    * name - key name
    * default - default if key is not present
    * optional - if True allow to not provide arg
    * to_name - instead of key name will be returned this key

You can provide ``to_name`` with ``>>`` operation::
    Key('javaStyleData') >> 'plain_cool_data'

KeysSubset
..........

Experimental feature, not stable API. Sometimes you need to make something with part of dict keys.
So you can::

    >>> join = (lambda d: {'name': ' '.join(d.values())})
    >>> Dict({KeysSubset('name', 'last'): join}).check({'name': 'Adam', 'last': 'Smith'})
    {'name': 'Smith Adam'}

As you can see you need to return dict from checker.

Error raise
...........

In ``Dict`` you can just return error from checkers or converters, there is need not to raise them.


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

This checker check that value one from provided. Like::
    >>> Enum(1, 2, 'error').check('2')
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
....................

Derived from DataError.
