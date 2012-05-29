Changes
=======

2012-05-30
----------

Renamed methods to ``check_value`` and ``check_and_return``.
Added ``Tuple`` trafaret.

2012-05-28
----------

Fixed Dict(...).make_optional(...) method for a chaining support

2012-05-21
----------

Updated ``KeysSubSet`` errors propagation - now you can return error either
``{'a': DataError('message')}``, or ``DataError({'a': 'message'})``

2012-05-16
----------

Added ``__call__`` alias to ``check``.

2012-05-11
----------

Added ``visitor`` module.

2012-05-10
----------

Fixed ``Dict.allow_extra`` behaviour.

2012-04-12
----------

``Int`` will not convert not-rounded floats like 2.2

``Dict`` have ``.ignore_extra`` method, similar to ``.allow_extra``, but given keys
will not included to result dict. If you will provide ``*``, any extra will be ignored.
