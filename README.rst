Trafaret
========

|circleci_build| |gitter_chat| |pypi_version| |pypi_license|

Ultimate transformation library that supports validation, contexts and ``aiohttp``.

Trafaret is rigid and powerful lib to work with foreign data, configs etc.
It provides simple way to check anything, and convert it accordingly to your needs.

It has shortcut syntax and ability to express anything that you can code:

.. code-block:: python

    >>> from trafaret.constructor import construct
    >>> validator = construct({'a': int, 'b': [str]})
    >>> validator({'a': 5, 'b': ['lorem', 'ipsum']})
    {'a': 5, 'b': ['lorem', 'ipsum']}

    >>> validator({'a': 5, 'b': ['gorky', 9]})
    Traceback (most recent call last):
      File "<console>", line 1, in <module>
      File "/Users/mkrivushin/w/trafaret/trafaret/__init__.py", line 204, in __call__
        return self.check(val)
      File "/Users/mkrivushin/w/trafaret/trafaret/__init__.py", line 144, in check
        return self._convert(self.check_and_return(value))
      File "/Users/mkrivushin/w/trafaret/trafaret/__init__.py", line 1105, in check_and_return
        raise DataError(error=errors, trafaret=self)
    trafaret.DataError: {'b': DataError({1: DataError(value is not a string)})}


Read The Docs hosted documentation http://trafaret.readthedocs.org/en/latest/
or look to the `docs/intro.rst`_ for start.

Trafaret can even generate Trafarets instances to build transformators from json,
like in json schema implementation `Trafaret Schema <https://github.com/Deepwalker/trafaret_schema>`_


New
---

2.0.2
=====
- construct for `int` and `float` will use `ToInt` and `ToFloat`

2.0.0
=====

- ``WithRepr`` – use it to return custom representation, like ``<Email>``
- Strip a lot from dict, like ``keys()``
- Trafarets are not mutable
- DataError has new ``code`` attribute, self.failure has ``code`` argument
- OnError has ``code`` argument too
- New ``DataError.to_struct`` method that returns errors in more consistent way
- ``String``, ``AnyString``, ``Bytes``, ``FromBytes(encoding=utf-8)``
- ``Int``, ``ToInt``, ``Float``, ``ToFloat``
- ``ToDecimal``
- ``Iterable`` that acts like a ``List``, but works with any iterable
- New ``Date``, ``ToDate`` and ``DateTime``, ``ToDateTime`` trafarets
- ``StrBool`` trafaret renamed to ``ToBool``
- ``Visitor`` trafaret was deleted
- Test coverage

1.x.x
=====

* converters and ``convert=False`` are deleted in favor of ``And`` and ``&``
* ``String`` parameter ``regex`` deleted in favor of ``Regexp`` and ``RegexpRaw`` usage
* new ``OnError`` to customize error message
* ``context=something`` argument for ``__call__`` and ``check`` Trafaret methods.
  Supported by ``Or``, ``And``, ``Forward`` etc.
* new customizable method ``transform`` like ``change_and_return`` but takes ``context=`` arg
* new ``trafaret_instance.async_check`` method that works with ``await``

Doc
---

For simple example what can be done:

.. code-block:: python

    import datetime
    import trafaret as t

    date = t.Dict(year=t.Int, month=t.Int, day=t.Int) >> (lambda d: datetime.datetime(**d))
    assert date.check({'year': 2012, 'month': 1, 'day': 12}) == datetime.datetime(2012, 1, 12)

Work with regex:

.. code-block:: python

    >>> c = t.RegexpRaw(r'^name=(\w+)$') >> (lambda m: m.group(1))
    >>> c.check('name=Jeff')
    'Jeff'

Rename dict keys:

.. code-block:: python

    >>> c = t.Dict({(t.Key('uNJ') >> 'user_name'): t.String})
    >>> c.check({'uNJ': 'Adam'})
    {'user_name': 'Adam'}

``Arrow`` date checking:

.. code-block:: python

    import arrow

    def check_datetime(str):
        try:
            return arrow.get(str).naive
        except arrow.parser.ParserError:
            return t.DataError('value is not in proper date/time format')

Yes, you can write trafarets that simple.


Related projects
----------------

`Trafaret Config <https://github.com/tailhook/trafaret-config>`_

`Trafaret Validator <https://github.com/Lex0ne/trafaret_validator>`_


.. _docs/intro.rst: docs/intro.rst

.. |circleci_build| image:: https://circleci.com/gh/Deepwalker/trafaret.svg?style=shield
    :target: https://circleci.com/gh/Deepwalker/trafaret
    :alt: Build status @ Circle CI

.. |gitter_chat| image:: https://badges.gitter.im/Deepwalker/trafaret.svg
    :target: https://gitter.im/Deepwalker/trafaret
    :alt: Gitter Chat

.. |pypi_version| image:: https://img.shields.io/pypi/v/trafaret.svg?style=flat-square
    :target: https://pypi.org/p/trafaret
    :alt: Latest release

.. |pypi_license| image:: https://img.shields.io/pypi/l/trafaret.svg?style=flat-square
    :target: https://pypi.python.org/pypi/trafaret
    :alt: BSD license
