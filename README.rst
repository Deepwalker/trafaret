Trafaret
========

Trafaret is validation library with support to convert data structures.
Sample of usage::

    import datetime
    import trafaret as t

    date = t.Dict(year=t.Int, month=t.Int, day=t.Int) >> (lambda d: datetime.datetime(**d))
    assert task.check({'year': 2012, 'month': 1, 'day': 12}) == datetime.datetime(2012, 1, 12)

``t.Dict`` creates new dict structure validator with three ``t.Int`` elements.
``>>`` operation adds lambda function to the converters of given checker.
Obviously every checker have any default converter, but when you use ``>>`` or ``.append``,
you disable default converter.

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

You can implement `converter` method, if you want to convert value somehow, but
want to make free for developer to apply his own converters to raw data.

Type
----

Just instantitate it with any class, like int, float, str::
    >>> Type(int).check(4)
    4

Any
---

Will match any element.

Or
--

Get other converters as args, and this samples are equivalent::
    >>> Or(t.Int, t.Null).check(None)
    None
    >>> (t.Int | t.Null).check(5)
    5

Null
----

Value must be `None`.

Simple checkers
---------------

``Bool``

``Float``

``Int``

``Atom`` - value must be exactly equal to Atom first arg - ``t.Atom('this_key_must_be_this')``.


String
------

``regex`` param - will return ``re.Match`` object. Default converter will return ``match.group()``.

``Email`` and ``URL`` just provide regular expressions and a bit of logic for IDNA domains.


List
----

Just List of elements of one type. In converter you will get ``list`` instance of converted elements.

Dict
----

Dict include named params. You can use for keys plain strings and ``Key`` instances.

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

Enum
----

This checker check that value one from provided. Like::
    >>> Enum(1, 2, 'error').check('2')
    2

Callable
--------

Call
----

Forward
-------

This checker is container for any checker, that you can provide later.
To provide container use ``provide`` method or ``<<`` operation::
    >> node = Forward()
    >> node << Dict(name=String, children=List[node])

guard
-----

Decorator

GuardValidationError
....................

Derived from DataError.
