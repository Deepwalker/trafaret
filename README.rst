Contract
========

Contract is validation library with support to convertors.

ContractValidationError
-----------------------

Exception class that used in library.

Contract
--------

Base class for contracts. Use it to make new contracts.
In derrived classes you need to implement `_check` or `_check_val`
methods. `_check_val` must return value, `_check` must return `None`.

You can implement `converter` method, if you want to convert value somehow, but
want to make free for developer to apply his own converters to raw data.

Type
----

Just instantitate it with any class, like int, float, str.

Any
---

Will match any element.

Or
--

Get other converters as args.

Null
----

Value must be `None`.

Simple checkers
---------------

``Bool``
``Float``
``Int``
``Atom``


String
------

regex param - will be returned re.Match object. Default converter will return match.group().

``Email`` and ``URL`` just provide regular expressions and a bit of logic for IDNA.


List
----

Key
---

Dict
----

Mapping
-------

Enum
----

Callable
--------

Call
----

Forward
-------

GuardValidationError
--------------------

