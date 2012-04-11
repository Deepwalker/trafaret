Changes
=======

2012-04-12
----------

``Int`` will not convert not-rounded floats like 2.2

``Dict`` have ``.ignore_extra`` method, similar to ``.allow_extra``, but given keys
will not included to result dict. If you will provide ``*``, any extra will be ignored.
