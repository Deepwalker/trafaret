# -*- coding: utf-8 -*-
import unittest
import pytest
import trafaret as t
from trafaret.lib import AbcMapping
from trafaret import catch_error, extract_error, DataError, guard
from trafaret.base import deprecated


class TestTrafaret(unittest.TestCase):
    def test_any(self):
        obj = {}
        trafaret = t.Trafaret()
        with self.assertRaises(NotImplementedError):
            self.assertEqual(
                trafaret.check(obj),
                obj
            )

    def test_ensure(self):
        with self.assertRaises(RuntimeError):
            t.ensure_trafaret(123)


class TestAnyTrafaret(unittest.TestCase):
    def test_any(self):
        obj = object()
        self.assertEqual(
            t.Any().check(obj),
            obj
        )


class TestAtomTrafaret(unittest.TestCase):
    def test_atom(self):
        res = t.Atom('atom').check('atom')
        self.assertEqual(res, 'atom')

        err = extract_error(t.Atom('atom'), 'molecule')
        self.assertEqual(err, "value is not exactly 'atom'")


class TestBoolTrafaret(unittest.TestCase):
    def test_bool(self):
        res = t.Bool().check(True)
        self.assertEqual(res, True)

        res = t.Bool().check(False)
        self.assertEqual(res, False)

        err = extract_error(t.Bool(), 1)
        self.assertEqual(err, 'value should be True or False')

    def test_repr(self):
        assert repr(t.Bool()) == '<Bool>'


class TestCallTrafaret(unittest.TestCase):
    def test_call(self):
        def validator(value):
            if value != "foo":
                return t.DataError("I want only foo!", code='i_wanna_foo')
            return 'foo'
        trafaret = t.Call(validator)
        res = trafaret.check("foo")
        self.assertEqual(res, 'foo')
        err = extract_error(trafaret, "bar")
        self.assertEqual(err, 'I want only foo!')


class TestCallableTrafaret(unittest.TestCase):
    def test_callable(self):
        t.Callable().check(lambda: 1)
        res = extract_error(t.Callable(), 1)
        self.assertEqual(res, 'value is not callable')


class TestBasics(unittest.TestCase):
    def test_callable(self):
        import functools
        to_int_10000 = functools.partial(int, '10000')
        trafaret = t.Regexp('2|10|16') & t.ToInt & t.Call(to_int_10000)
        self.assertEqual(trafaret('10'), 10000)

    def test_auto_call(self):
        import functools
        to_int_10000 = functools.partial(int, '10000')
        trafaret = t.Regexp('2|10|16') & t.ToInt & to_int_10000
        self.assertEqual(trafaret('10'), 10000)

    def test_class(self):
        class Tttt:
            def __call__(self, value, context=None):
                return context(value)
        trafaret = t.ToInt() & Tttt()
        self.assertEqual(trafaret(123, context=lambda v: v + 123), 246)

    def test_upper(self):
        trafaret = t.Regexp(r'\w+-\w+') & str.upper
        self.assertEqual(trafaret('abc-Abc'), 'ABC-ABC')


class TestDictTrafaret(unittest.TestCase):
    def test_base(self):
        trafaret = t.Dict(foo=t.ToInt, bar=t.String)
        trafaret.check({"foo": 1, "bar": u"spam"})
        res = t.extract_error(trafaret, {"foo": 1, "bar": 2})
        self.assertEqual(res, {'bar': 'value is not a string'})
        res = extract_error(trafaret, {"foo": 1})
        self.assertEqual(res, {'bar': 'is required'})
        res = extract_error(trafaret, {"foo": 1, "bar": u"spam", "eggs": None})
        self.assertEqual(res, {'eggs': 'eggs is not allowed key'})
        trafaret = trafaret.allow_extra("eggs")
        self.assertEqual(repr(trafaret), '<Dict(extras=(eggs) | <Key "bar" <String>>, <Key "foo" <ToInt>>)>')
        trafaret.check({"foo": 1, "bar": u"spam", "eggs": None})
        trafaret.check({"foo": 1, "bar": u"spam"})
        res = extract_error(trafaret, {"foo": 1, "bar": u"spam", "ham": 100})
        self.assertEqual(res, {'ham': 'ham is not allowed key'})
        trafaret = trafaret.allow_extra("*")
        trafaret.check({"foo": 1, "bar": u"spam", "ham": 100})
        trafaret.check({"foo": 1, "bar": u"spam", "ham": 100, "baz": None})
        res = extract_error(trafaret, {"foo": 1, "ham": 100, "baz": None})
        self.assertEqual(res, {'bar': 'is required'})

    def test_kwargs_extra(self):
        trafaret = t.Dict(t.Key('foo', trafaret=t.ToInt()), allow_extra=['eggs'])
        trafaret.check({"foo": 1, "eggs": None})
        trafaret.check({"foo": 1})
        with self.assertRaises(t.DataError):
            trafaret.check({"foo": 2, "marmalade": 5})

    def test_kwargs_ignore(self):
        trafaret = t.Dict(t.Key('foo', trafaret=t.ToInt()), ignore_extra=['eggs'])
        trafaret.check({"foo": 1, "eggs": None})
        trafaret.check({"foo": 1})
        with self.assertRaises(t.DataError):
            trafaret.check({"foo": 2, "marmalade": 5})

    def test_add_kwargs_ignore(self):
        first = t.Dict(
            t.Key('bar', trafaret=t.Int()), ignore_extra=['eggs']
        )
        second = t.Dict(t.Key('bar1', trafaret=t.Int()))
        third = first + second
        third.check({'bar': 4, 'bar1': 41})
        third.check({'bar': 4, 'bar1': 41, 'eggs': 'blabla'})

        first = t.Dict(
            t.Key('bar', trafaret=t.Int()),
        )
        second = t.Dict(t.Key('bar1', trafaret=t.Int()), ignore_extra=['eggs'])
        third = first + second
        third.check({'bar': 4, 'bar1': 41})
        third.check({'bar': 4, 'bar1': 41, 'eggs': 'blabla'})

    def test_add_kwargs_extra(self):
        first = t.Dict(
            t.Key('bar', trafaret=t.Int()), allow_extra=['eggs']
        )
        second = t.Dict(t.Key('bar1', trafaret=t.Int()))
        third = first + second
        third.check({"bar": 1, "bar1": 41, "eggs": None})
        third.check({"bar": 1, "bar1": 41})
        with self.assertRaises(t.DataError):
            third.check({"bar": 2, "bar1": 1, "marmalade": 5})

        first = t.Dict(t.Key('bar', trafaret=t.Int()))
        second = t.Dict(t.Key('bar1', trafaret=t.Int()), allow_extra=['eggs'])
        third = first + second
        third.check({"bar": 1, "bar1": 41, "eggs": None})
        third.check({"bar": 1, "bar1": 41})
        with self.assertRaises(t.DataError):
            third.check({"bar": 2, "bar1": 1, "marmalade": 5})

    def test_callable_key(self):
        def simple_key(value):
            yield 'simple', 'simple data', []

        trafaret = t.Dict(simple_key)
        res = trafaret.check({})
        self.assertEqual(res, {'simple': 'simple data'})

        trafaret = t.Dict({t.Key('key'): t.String}, simple_key)
        res = trafaret.check({'key': u'blabla'})
        self.assertEqual(res, {'key': u'blabla', 'simple': 'simple data'})


    def test_base2(self):
        trafaret = t.Dict({t.Key('bar', optional=True): t.String}, foo=t.ToInt)
        trafaret = trafaret.allow_extra('*')
        res = trafaret.check({"foo": 1, "ham": 100, "baz": None})
        self.assertEqual(res, {'baz': None, 'foo': 1, 'ham': 100})
        res = extract_error(trafaret, {"bar": 1, "ham": 100, "baz": None})
        self.assertEqual(res, {'bar': 'value is not a string', 'foo': 'is required'})
        res = extract_error(trafaret, {"foo": 1, "bar": 1, "ham": 100, "baz": None})
        self.assertEqual(res, {'bar': 'value is not a string'})

    def test_base3(self):
        trafaret = t.Dict({t.Key('bar', default=u'nyanya') >> 'baz': t.String}, foo=t.ToInt)
        res = trafaret.check({'foo': 4})
        self.assertEqual(res, {'baz': u'nyanya', 'foo': 4})

        trafaret = trafaret.allow_extra('*')
        res = extract_error(trafaret, {'baz': u'spam', 'foo': 4})
        self.assertEqual(res, {'baz': 'baz key was shadowed'})

        trafaret = trafaret.allow_extra('*', trafaret=t.String)
        res = extract_error(trafaret, {'baaz': 5, 'foo': 4})
        self.assertEqual(res, {'baaz': 'value is not a string'})
        res = trafaret({'baaz': u'strstr', 'foo':4})
        self.assertEqual(res, {'baaz': u'strstr', 'foo':4, 'baz': u'nyanya'})

        trafaret = trafaret.ignore_extra('fooz')
        res = trafaret.check({'foo': 4, 'fooz': 5})
        self.assertEqual(res, {'baz': u'nyanya', 'foo': 4})

        trafaret = trafaret.ignore_extra('*')
        res = trafaret.check({'foo': 4, 'foor': 5})
        self.assertEqual(res, {'baz': u'nyanya', 'foo': 4})

    def test_add(self):
        first = t.Dict({
            t.Key('bar', default=u'nyanya') >> 'baz': t.String},
            foo=t.ToInt)
        second = t.Dict({
            t.Key('bar1', default=u'nyanya') >> 'baz1': t.String},
            foo1=t.ToInt)
        third = first + second
        res = third.check({'foo': 4, 'foo1': 41})
        self.assertEqual(res, {'baz': u'nyanya', 'baz1': u'nyanya', 'foo': 4, 'foo1': 41})

    def test_bad_add_names(self):
        first = t.Dict({
            t.Key('bar', default='nyanya') >> 'baz': t.String},
            foo=t.ToInt)
        second = t.Dict({
            t.Key('bar1', default='nyanya') >> 'baz1': t.String},
            foo=t.ToInt)
        # will not raise any errors
        first + second

    def test_bad_add_to_names(self):
        first = t.Dict({
            t.Key('bar', default='nyanya') >> 'baz': t.String},
            foo=t.ToInt)
        second = t.Dict({
            t.Key('bar1', default='nyanya') >> 'baz': t.String},
            foo1=t.ToInt)
        # will not raise any errors
        first + second

    def test_add_to_names_list_of_keys(self):
        dct = t.Dict(key1=t.String)
        dct + [t.Key('a', trafaret=t.String())]

    def test_add_to_names_dict_of_keys(self):
        dct = t.Dict(key1=t.String)
        dct + {'a': t.String}

    def test_mapping_interface(self):
        trafaret = t.Dict({t.Key("foo"): t.String, t.Key("bar"): t.ToFloat})

        # class with mapping interface but not subclass of dict
        class Map(AbcMapping):

            def __init__(self, data, *a, **kw):
                super(Map, self).__init__(*a, **kw)
                self._data = data

            def __getitem__(self, key):
                return self._data[key]

            def __iter__(self):
                for x in self._data:
                    yield x

            def __len__(self):
                return len(self._data)

        trafaret.check(Map({"foo": u"xxx", "bar": 0.1}))

        res = extract_error(trafaret, object())
        self.assertEqual(res, "value is not a dict")

        res = extract_error(trafaret, Map({"foo": u"xxx"}))
        self.assertEqual(res, {'bar': 'is required'})

        res = extract_error(trafaret, Map({"foo": u"xxx", "bar": u'str'}))
        self.assertEqual(res, {'bar': "value can't be converted to float"})

    def test_keys_must_be_callable(self):
        with pytest.raises(RuntimeError) as exc_info:
            t.Dict(5)
        assert exc_info.value.args[0] == 'Keys in single attributes must be callables'

        with pytest.raises(RuntimeError) as exc_info:
            t.Dict({5: t.String})
        assert exc_info.value.args[0] == 'Non callable Keys are not supported'



class TestDictKeys(unittest.TestCase):

    def test_dict_keys(self):
        res = t.DictKeys(['a', 'b']).check({'a': 1, 'b': 2})
        self.assertEqual(res, {'a': 1, 'b': 2})
        res = extract_error(t.DictKeys(['a', 'b']), {'a': 1, 'b': 2, 'c': 3})
        self.assertEqual(res, {'c': 'c is not allowed key'})
        res = extract_error(t.DictKeys(['key', 'key2']), {'key': 'val'})
        self.assertEqual(res, {'key2': 'is required'})


class TestEnumTrafaret(unittest.TestCase):
    def test_enum(self):
        trafaret = t.Enum("foo", "bar", 1)
        self.assertEqual(repr(trafaret), "<Enum('foo', 'bar', 1)>")
        res = trafaret.check("foo")
        res = trafaret.check(1)
        res = extract_error(trafaret, 2)
        self.assertEqual(res, "value doesn't match any variant")



class TestToFloat(unittest.TestCase):
    def test_float_repr(self):
        res = t.ToFloat()
        self.assertEqual(repr(res), '<ToFloat>')
        res = t.ToFloat(gte=1)
        self.assertEqual(repr(res), '<ToFloat(gte=1)>')
        res = t.ToFloat(lte=10)
        self.assertEqual(repr(res), '<ToFloat(lte=10)>')
        res = t.ToFloat(gte=1, lte=10)
        self.assertEqual(repr(res), '<ToFloat(gte=1, lte=10)>')

    def test_float(self):
        res = t.ToFloat().check(1.0)
        self.assertEqual(res, 1.0)
        res = extract_error(t.ToFloat(), 1 + 3j)
        self.assertEqual(res, 'value is not float')
        res = extract_error(t.ToFloat(), 1)
        self.assertEqual(res, 1.0)
        res = t.ToFloat(gte=2).check(3.0)
        self.assertEqual(res, 3.0)
        res = extract_error(t.ToFloat(gte=2), 1.0)
        self.assertEqual(res, 'value is less than 2')
        res = t.ToFloat(lte=10).check(5.0)
        self.assertEqual(res, 5.0)
        res = extract_error(t.ToFloat(lte=3), 5.0)
        self.assertEqual(res, 'value is greater than 3')
        res = t.ToFloat().check("5.0")
        self.assertEqual(res, 5.0)

    def test_meta(self):
        assert repr(t.ToFloat() > 10) == '<ToFloat(gt=10)>'
        assert repr(t.ToFloat() >= 10) == '<ToFloat(gte=10)>'
        assert repr(t.ToFloat() < 10) == '<ToFloat(lt=10)>'
        assert repr(t.ToFloat() <= 10) == '<ToFloat(lte=10)>'



class TestForwardTrafaret(unittest.TestCase):

    def test_forward(self):
        node = t.Forward()
        node << t.Dict(name=t.String, children=t.List[node])
        self.assertEqual(
            repr(node),
            '<Forward(<Dict(<Key "children" <List(<recur>)>>, <Key "name" <String>>)>)>',
        )
        res = node.check({"name": u"foo", "children": []}) == {'children': [], 'name': u'foo'}
        self.assertEqual(res, True)
        res = extract_error(node, {"name": u"foo", "children": [1]})
        self.assertEqual(res, {'children': {0: 'value is not a dict'}})
        res = node.check({"name": u"foo", "children": [{"name": u"bar", "children": []}]})
        self.assertEqual(res, {'children': [{'children': [], 'name': u'bar'}], 'name': u'foo'})
        empty_node = t.Forward()
        self.assertEqual(repr(empty_node), '<Forward(None)>')
        res = extract_error(empty_node, 'something')
        self.assertEqual(res, 'trafaret not set yet')



class TestToIntTrafaret(unittest.TestCase):

    def test_int(self):
        res = repr(t.ToInt())
        self.assertEqual(res, '<ToInt>')
        res = t.ToInt().check(5)
        self.assertEqual(res, 5)
        res = extract_error(t.ToInt(), 1.1)
        self.assertEqual(res, 'value is not int')
        res = extract_error(t.ToInt(), 1 + 1j)
        self.assertEqual(res, 'value is not int')


class TestList(unittest.TestCase):

    def test_list_repr(self):
        res = t.List(t.ToInt)
        self.assertEqual(repr(res), '<List(<ToInt>)>')
        res = t.List(t.ToInt, min_length=1)
        self.assertEqual(repr(res), '<List(min_length=1 | <ToInt>)>')
        res = t.List(t.ToInt, min_length=1, max_length=10)
        self.assertEqual(repr(res), '<List(min_length=1, max_length=10 | <ToInt>)>')

    def test_list(self):
        res = extract_error(t.List(t.ToInt), 1)
        self.assertEqual(res, 'value is not a list')
        res = t.List(t.ToInt).check([1, 2, 3])
        self.assertEqual(res, [1, 2, 3])
        res = t.List(t.String).check([u"foo", u"bar", u"spam"])
        self.assertEqual(res, [u'foo', u'bar', u'spam'])
        res = extract_error(t.List(t.ToInt), [1, 2, 1 + 3j])
        self.assertEqual(res, {2: 'value is not int'})
        res = t.List(t.ToInt, min_length=1).check([1, 2, 3])
        self.assertEqual(res, [1, 2, 3])
        res = extract_error(t.List(t.ToInt, min_length=1), [])
        self.assertEqual(res, 'list length is less than 1')
        res = t.List(t.ToInt, max_length=2).check([1, 2])
        self.assertEqual(res, [1, 2])
        res = extract_error(t.List(t.ToInt, max_length=2), [1, 2, 3])
        self.assertEqual(res, 'list length is greater than 2')
        res = extract_error(t.List(t.ToInt), ["a"])
        self.assertEqual(res, {0: "value can't be converted to int"})

    def test_list_meta(self):
        res = t.List[t.ToInt]
        self.assertEqual(repr(res), '<List(<ToInt>)>')
        res = t.List[t.ToInt, 1:]
        self.assertEqual(repr(res), '<List(min_length=1 | <ToInt>)>')
        res = t.List[:10, t.ToInt]
        self.assertEqual(repr(res), '<List(max_length=10 | <ToInt>)>')
        with pytest.raises(RuntimeError) as exc_info:
            t.List[1:10]
        assert exc_info.value.args[0] == 'Trafaret is required for List initialization'


class TestMappingTrafaret(unittest.TestCase):

    def test_mapping(self):
        trafaret = t.Mapping(t.String, t.ToInt)
        self.assertEqual(repr(trafaret), '<Mapping(<String> => <ToInt>)>')
        res = trafaret.check({u"foo": 1, u"bar": 2})
        self.assertEqual(res, {u'bar': 2, u'foo': 1})
        res = extract_error(trafaret, {u"foo": 1, u"bar": None})
        self.assertEqual(res, {u'bar': {'value': 'value is not int'}})
        res = extract_error(trafaret, {u"foo": 1, 2: "bar"})
        self.assertEqual(res, {2: {'key': 'value is not a string', 'value': "value can't be converted to int"}})
        res = extract_error(trafaret.check, None)
        self.assertEqual(res, 'value is not a dict')


class TestNullTrafaret(unittest.TestCase):

    def test_null(self):
        res = t.Null()
        self.assertEqual(repr(res), '<Null>')
        res = t.Null().check(None)
        res = extract_error(t.Null(), 1)
        self.assertEqual(res, 'value should be None')


class TestOrNotToTest(unittest.TestCase):
    def test_or(self):
        nullString = t.Or(t.String, t.Null)
        self.assertEqual(repr(nullString), '<Or(<String>, <Null>)>')
        res = nullString.check(None)
        res = nullString.check(u"test")
        self.assertEqual(res, u'test')
        res = extract_error(nullString, 1)
        self.assertEqual(res, {0: 'value is not a string', 1: 'value should be None'})
        res = t.ToInt | t.String
        self.assertEqual(repr(res), '<Or(<ToInt>, <String>)>')

    def test_operator(self):
        check = t.String | t.ToInt
        self.assertEqual(check(u'a'), u'a')
        self.assertEqual(check(5), 5)


class TestAndTest(unittest.TestCase):
    def test_and(self):
        indeed_int = t.Atom('123') & int
        self.assertEqual(indeed_int('123'), 123) # fixed 0.8.0 error

    def test_raise_error(self):
        other = lambda v: DataError('other error', code='other_error')
        fail_other = t.Atom('a') & other
        res = extract_error(fail_other, 'a')
        self.assertEqual(res, 'other error')

        ttt = t.And(other, t.Any)
        res = extract_error(ttt, 45)
        self.assertEqual(res, 'other error')

    def test_repr(self):
        assert repr(t.Bool & t.Null) == '<And(<Bool>, <Null>)>'


class TestStrBoolTrafaret(unittest.TestCase):

    def test_str_bool(self):
        res = extract_error(t.StrBool(), 'aloha')
        self.assertEqual(res, "value can't be converted to Bool")
        res = t.StrBool().check(1)
        self.assertEqual(res, True)
        res = t.StrBool().check(0)
        self.assertEqual(res, False)
        res = t.StrBool().check('y')
        self.assertEqual(res, True)
        res = t.StrBool().check('n')
        self.assertEqual(res, False)
        res = t.StrBool().check(None)
        self.assertEqual(res, False)
        res = t.StrBool().check('1')
        self.assertEqual(res, True)
        res = t.StrBool().check('0')
        self.assertEqual(res, False)
        res = t.StrBool().check('YeS')
        self.assertEqual(res, True)
        res = t.StrBool().check('No')
        self.assertEqual(res, False)
        res = t.StrBool().check(True)
        self.assertEqual(res, True)
        res = t.StrBool().check(False)
        self.assertEqual(res, False)
        res = t.StrBool().check('on')
        self.assertEqual(res, True)
        res = t.StrBool().check('off')
        self.assertEqual(res, False)

    def test_bool(self):
        assert repr(t.StrBool()) == '<StrBool>'



class TestStringTrafaret(unittest.TestCase):

    def test_string(self):
        res = t.String()
        self.assertEqual(repr(res), '<String>')
        res = t.String(allow_blank=True)
        self.assertEqual(repr(res), '<String(blank)>')
        res = t.String().check(u"foo")
        self.assertEqual(res, u'foo')
        res = extract_error(t.String(), u"")
        self.assertEqual(res, 'blank value is not allowed')
        res = t.String(allow_blank=True).check(u"")
        self.assertEqual(res, u'')
        res = extract_error(t.String(), 1)
        self.assertEqual(res, 'value is not a string')
        res = t.String(min_length=2, max_length=3).check(u'123')
        self.assertEqual(res, u'123')
        res = extract_error(t.String(min_length=2, max_length=6), u'1')
        self.assertEqual(res, 'String is shorter than 2 characters')
        res = extract_error(t.String(min_length=2, max_length=6), u'1234567')
        self.assertEqual(res, 'String is longer than 6 characters')
        # TODO
        # res = String(min_length=2, max_length=6, allow_blank=True)
        # self.assertEqual(res, Traceback (most recent call last):
        #     ...
        #     AssertionError: Either allow_blank or min_length should be specified, not both
        res = t.String(min_length=0, max_length=6, allow_blank=True).check(u'123')
        self.assertEqual(res, u'123')


class TestBytesTrafaret(unittest.TestCase):

    def test_bytes(self):
        res = t.Bytes()
        self.assertEqual(repr(res), '<Bytes>')
        res = t.Bytes().check(b"foo")
        self.assertEqual(res, 'foo')
        res = t.Bytes()(b"")
        self.assertEqual(res, '')
        res = t.Bytes().check(b"")
        self.assertEqual(res, '')
        res = extract_error(t.Bytes(), 1)
        self.assertEqual(res, 'value is not a bytes')


class TestRegexpTrafaret(unittest.TestCase):
    def test_regexp(self):
        trafaret = t.Regexp('cat')
        self.assertEqual(trafaret('cat1212'), 'cat')

    def test_regexp_raw(self):
        trafaret = t.RegexpRaw('.*(cat).*')
        self.assertEqual(trafaret('cat1212').groups()[0], 'cat')

    def test_regexp_raw_error(self):
        trafaret = t.RegexpRaw('cat')
        res = catch_error(trafaret, 'dog')
        self.assertEqual(res.as_dict(value=True), 'does not match pattern cat, got \'dog\'')

        res = extract_error(trafaret, None)
        self.assertEqual(res, 'value is not a string')

    def test_repr(self):
        assert repr(t.RegexpRaw('.*(cat).*')) == '<Regexp ".*(cat).*">'


class TestTrafaretMeta(unittest.TestCase):
    def test_meta(self):
        res = (t.ToInt() >> (lambda x: x * 2) >> (lambda x: x * 3)).check(1)
        self.assertEqual(res, 6)
        res = (t.ToInt() >> float >> str).check(4)
        self.assertEqual(res, '4.0')
        res = t.ToInt | t.String
        self.assertEqual(repr(res), '<Or(<ToInt>, <String>)>')
        res = t.ToInt | t.String | t.Null
        self.assertEqual(repr(res), '<Or(<Or(<ToInt>, <String>)>, <Null>)>')
        res = (t.ToInt >> (lambda v: v if v ** 2 > 15 else 0)).check(5)
        self.assertEqual(res, 5)



class TestTupleTrafaret(unittest.TestCase):
    def test_tuple(self):
        tup = t.Tuple(t.ToInt, t.ToInt, t.String)
        self.assertEqual(repr(tup), '<Tuple(<ToInt>, <ToInt>, <String>)>')
        res = tup.check([3, 4, u'5'])
        self.assertEqual(res, (3, 4, u'5'))
        res = extract_error(tup, [3, 4, 5])
        self.assertEqual(res, {2: 'value is not a string'})
        res = extract_error(tup, 5)
        self.assertEqual(res, 'value must be convertable to tuple')
        res = extract_error(tup, [5])
        self.assertEqual(res, 'value must contain 3 items')


class TestTypeTrafaret(unittest.TestCase):

    def test_type(self):
        res = t.Type(int)
        self.assertEqual(repr(res), '<Type(int)>')
        c = t.Type[int]
        res = c.check(1)
        self.assertEqual(res, 1)
        res = extract_error(c, "foo")
        self.assertEqual(res, 'value is not int')


class TestSubclassTrafaret(unittest.TestCase):

    def test_subclass(self):
        res = t.Subclass(type)
        self.assertEqual(repr(res), '<Subclass(type)>')
        c = t.Subclass[type]

        class Type(type):
            pass

        res = c.check(Type)
        self.assertEqual(res, Type)
        res = extract_error(c, object)
        self.assertEqual(res, 'value is not subclass of type')


class TestOnErrorTrafaret(unittest.TestCase):
    def test_on_error(self):
        trafaret = t.OnError(t.Bool(), message='Changed message')
        res = trafaret(True)
        self.assertEqual(res, True)

    def test_on_error_ensured_trafaret(self):
        trafaret = t.OnError(t.Bool, message='Changed message')
        res = trafaret(False)
        self.assertEqual(res, False)

    def test_on_error_data_error(self):
        trafaret = t.OnError(t.Bool, message='Changed message')
        res = catch_error(trafaret, 'Trololo')
        self.assertEqual(res.as_dict(), 'Changed message')


def test_with_repr():
    ttt = t.WithRepr(t.String, '<Ttt>')
    assert repr(ttt) == '<Ttt>'


class TestGuard(unittest.TestCase):
    def test_keywords_only(self):
        @guard(a=t.ToInt)
        def fn(**kw):
            return kw
        self.assertEqual(fn(a='123'), {'a': 123})


def test_ignore():
    assert t.ignore(5) == None


def test_deprecated():
    deprecated('blabla')
