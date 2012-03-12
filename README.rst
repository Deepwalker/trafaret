Trafaret
========

Trafaret is validation library with support to convert data structures.
Sample of usage::

    import datetime
    import trafaret as t

    date = t.Dict(year=t.Int, month=t.Int, day=t.Int) >> (lambda d: datetime.datetime(**d))
    assert date.check({'year': 2012, 'month': 1, 'day': 12}) == datetime.datetime(2012, 1, 12)

``t.Dict`` creates new dict structure validator with three ``t.Int`` elements.
``>>`` operation adds lambda function to the converters of given checker.
Obviously every checker has some default converter, but when you use ``>>`` or ``.append``,
you disable default converter with your own.
Converters can be chained. You can raise DataError in converters.

Features
--------

Trafaret has very handy features, read below some samples.

Regex String
............

``String`` can work with regular expressions, and this give you real power::

    >>> c = t.String(regex=r'name=(\w+)') >> (lambda m: m.groups()[0])
    >>> c.check('name=Jeff')
    'Jeff'

Some way you can use all re.Match power to extract from strings dicts and so on.


Dict and Key
............

``Dict`` get dict with ``Key`` as keys (it can be strings but will be converted to ``Key``).
And ``Key`` is powerfull conception - it pops from original dict needed keys. Basic ``Key``
pop only one key, but it then can yield it with different name::


    >>> from trafaret.utils import fold
    >>> c = t.Dict({t.Key('uNJ') >> 'user__name': t.String}) >> fold
    >>> c.check({'uNJ': 'Adam'})
    {'user': {'name': 'Adam'}}

We have some example of enhanced ``Key`` in extras::

    >>> from trafaret.extras import KeysSubset
    >>> cmp_pwds = lambda x: {'pwd': x['pwd'] if x.get('pwd') == x.get('pwd1') else DataError('Not equal')}
    >>> d = Dict({KeysSubset(['pwd', 'pwd1']): cmp_pwds, 'key1': String})
    >>> d.check({'pwd': 'a', 'pwd1': 'a', 'key1': 'b'}).keys()
    {'pwd': 'a', 'key1': 'b'}

DataError
-----------------------

Exception class that used in library. Exception hold errors in ``error`` attribute.
For simple checkers it will be just a string. For nested structures it will be `dict`
instance.

Trafaret
--------

Base class for trafarets. Use it to make new trafarets.
In derrived classes you need to implement `_check` or `_check_val`
methods. `_check_val` must return value, `_check` must return `None` on success.

You can implement `converter` method if you want to convert value somehow, but
want to make free for developer to apply his own converters to raw data. This
used to return strings instead of `Match` object in `String` trafaret.

Type
----

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

Simple checkers
---------------

``Bool`` - ``t.Bool.check(True)``

``Float`` - try convert from other types to float

``Int`` - try convert from other types to int

``Atom`` - value must be exactly equal to Atom first arg - ``t.Atom('this_key_must_be_this')``.


String
------

Basicaly just check that arg is string.
Argument ``allow_blank`` indicates if string can be blank ot not.
If you will provide ``regex`` param - will return ``re.Match`` object.
Default converter will return ``match.group()`` result. You will get ``re.Match`` object
in converter.

``Email`` and ``URL`` just provide regular expressions and a bit of logic for IDNA domains.
Default converters return email and domain, but you will get ``re.Match`` in converter.


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

Key
...

Special class to create dict keys. Parameters are:

    * name - key name
    * default - default if key is not present
    * optional - if True allow to not provide arg
    * to_name - instead of key name will be returned this key

You can provide ``to_name`` with ``>>`` operation::
    Key('javaStyleData') >> 'plain_cool_data'


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
