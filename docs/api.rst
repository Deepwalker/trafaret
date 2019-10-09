API
===

Trafaret
--------

Base class for checkers. Use it to create new checkers.  In derived
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