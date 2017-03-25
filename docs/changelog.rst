Changelog
=========

2017-03-25 0.9.0
----------------

- added `And` trafaret and `&` shortcut operation.
- change `>>` behaviour. From now on Trafaret does not use self.converters and use `And` trafaret instead
- added `RegxpRaw` and `Regexp` trafarets. `RegexpRaw` returns re.Match object and `Regexp` returns match string.
- deprecate `String` `regex` argument in favor to `Regexp` and `RegexpRaw` usage
- `Dict` now takes `allow_extra`, `allow_extra_trafaret` and `ignore_extra` keyword arguments as preferred alternative to methods


0.8.1
-----

- added trafaret.constructor. Now you can use `construct` and `C` from this package.
