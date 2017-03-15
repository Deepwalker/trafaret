Trafaret
========

-----

|circleci_build| |pypi_version| |pypi_license|

-----


Read The Docs hosted documentation <http://trafaret.readthedocs.org/en/latest/>
or look to the docs/api/intro.rst for start.

Trafaret is rigid and powerful lib to work with foreign data, configs etc.
It provides simple way to check anything, and convert it accordingly to your needs.

It have shortcut syntax and ability to express anything that you can code:

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

For simple example what can be done:

.. code-block:: python

    import datetime
    import trafaret as t

    date = t.Dict(year=t.Int, month=t.Int, day=t.Int) >> (lambda d: datetime.datetime(**d))
    assert date.check({'year': 2012, 'month': 1, 'day': 12}) == datetime.datetime(2012, 1, 12)

Work with regex:

.. code-block:: python

    >>> c = t.String(regex=r'^name=(\w+)$') >> (lambda m: m.groups()[0])
    >>> c.check('name=Jeff')
    'Jeff'

Rename dict keys:

.. code-block:: python

    >>> c = t.Dict(t.Key('uNJ') >> 'user_name': t.String})
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


.. |circleci_build| image:: https://circleci.com/gh/Deepwalker/trafaret.svg?style=shield
    :target: https://pypi.python.org/pypi/trafaret
    :alt: Build status

.. |pypi_version| image:: https://img.shields.io/pypi/v/trafaret.svg?style=flat-square
    :target: https://pypi.python.org/pypi/trafaret
    :alt: Downloads

.. |pypi_license| image:: https://img.shields.io/pypi/l/trafaret.svg?style=flat-square
    :target: https://pypi.python.org/pypi/trafaret
    :alt: Downloads
