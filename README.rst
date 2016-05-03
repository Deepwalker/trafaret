Trafaret
========

-----

|pypi_downloads| |pypi_version| |pypi_license|

-----


Read The Docs hosted documentation <http://trafaret.readthedocs.org/en/latest/>
or look to the docs/api/intro.rst for start.

Trafaret is rigid and powerful lib to work with foreign data, configs etc.
It provides simple way to check anything, and convert it accordingly to your needs.

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


.. |pypi_downloads| image:: https://img.shields.io/pypi/dm/trafaret.svg?style=flat-square
    :target: https://pypi.python.org/pypi/trafaret
    :alt: Downloads

.. |pypi_version| image:: https://img.shields.io/pypi/v/trafaret.svg?style=flat-square
    :target: https://pypi.python.org/pypi/trafaret
    :alt: Downloads

.. |pypi_license| image:: https://img.shields.io/pypi/l/trafaret.svg?style=flat-square
    :target: https://pypi.python.org/pypi/trafaret
    :alt: Downloads
