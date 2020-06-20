# -*- coding: utf-8 -*-
import enum
import pytest
import trafaret as t
from datetime import date, datetime
from trafaret.lib import AbcMapping
from trafaret import catch_error, extract_error, DataError, guard
from trafaret.base import deprecated


class TestTrafaret:
    def test_any(self):
        obj = {}
        trafaret = t.Trafaret()
        with pytest.raises(NotImplementedError):
            assert trafaret.check(obj) == obj
            assert trafaret.is_valid(obj)

    def test_ensure(self):
        with pytest.raises(RuntimeError):
            t.ensure_trafaret(123)

    def test_is_valid(self):
        string_trafaret = t.Float()
        assert string_trafaret.is_valid(1.5) == True
        assert string_trafaret.is_valid('foo') == False


class TestAnyTrafaret:
    def test_any(self):
        obj = object()
        assert t.Any().check(obj) == obj

    def test_repr(self):
        assert repr(t.Any()) == '<Any>'


class TestAtomTrafaret:
    def test_atom(self):
        res = t.Atom('atom').check('atom')
        assert res == 'atom'

        err = extract_error(t.Atom('atom'), 'molecule')
        assert err == "value doesn't match any variant"


class TestBoolTrafaret:
    @pytest.mark.parametrize('check_value, result', [
        (True, True),
        (False, False),
    ])
    def test_bool(self, check_value, result):
        res = t.Bool().check(check_value)
        assert res == result

    def test_extract_error(self):
        err = extract_error(t.Bool(), 1)
        assert err == 'value should be True or False'

    def test_repr(self):
        assert repr(t.Bool()) == '<Bool>'


class TestCallTrafaret:
    @staticmethod
    def validator(value):
        if value != "foo":
            return t.DataError("I want only foo!", code='i_wanna_foo')
        return 'foo'

    def test_call(self):
        trafaret = t.Call(self.validator)
        res = trafaret.check("foo")
        assert res == 'foo'
        err = extract_error(trafaret, "bar")
        assert err == 'I want only foo!'

    def test_repr(self):
        assert repr(t.Call(self.validator)) == '<Call(validator)>'

    def test_should_be_callable(self):
        with pytest.raises(RuntimeError):
            t.Call(5)


class TestCallableTrafaret:
    def test_callable(self):
        t.Callable().check(lambda: 1)
        res = extract_error(t.Callable(), 1)
        assert res == 'value is not callable'

    def test_repr(self):
        assert repr(t.Callable()) == '<Callable>'


class TestBasics:
    def test_callable(self):
        import functools
        to_int_10000 = functools.partial(int, '10000')
        trafaret = t.Regexp('2|10|16') & t.ToInt & t.Call(to_int_10000)
        assert trafaret('10') == 10000

    def test_auto_call(self):
        import functools
        to_int_10000 = functools.partial(int, '10000')
        trafaret = t.Regexp('2|10|16') & t.ToInt & to_int_10000
        assert trafaret('10') == 10000

    def test_class(self):
        class Tttt:
            def __call__(self, value, context=None):
                return context(value)
        trafaret = t.ToInt() & Tttt()
        assert trafaret(123, context=lambda v: v + 123) == 246

    def test_upper(self):
        trafaret = t.Regexp(r'\w+-\w+') & str.upper
        assert trafaret('abc-Abc') == 'ABC-ABC'


class TestDictTrafaret:
    def test_base(self):
        trafaret = t.Dict(foo=t.ToInt, bar=t.String)
        trafaret.check({"foo": 1, "bar": u"spam"})
        res = t.extract_error(trafaret, {"foo": 1, "bar": 2})
        assert res == {'bar': 'value is not a string'}
        res = extract_error(trafaret, {"foo": 1})
        assert res == {'bar': 'is required'}
        res = extract_error(trafaret, {"foo": 1, "bar": u"spam", "eggs": None})
        assert res == {'eggs': 'eggs is not allowed key'}
        trafaret = trafaret.allow_extra("eggs")
        trafaret.check({"foo": 1, "bar": u"spam", "eggs": None})
        trafaret.check({"foo": 1, "bar": u"spam"})
        res = extract_error(trafaret, {"foo": 1, "bar": u"spam", "ham": 100})
        assert res == {'ham': 'ham is not allowed key'}
        trafaret = trafaret.allow_extra("*")
        trafaret = trafaret.ignore_extra("a")
        trafaret.check({"foo": 1, "bar": u"spam", "ham": 100})
        trafaret.check({"foo": 1, "bar": u"spam", "ham": 100, "baz": None})
        res = extract_error(trafaret, {"foo": 1, "ham": 100, "baz": None})
        assert res == {'bar': 'is required'}

    def test_repr(self):
        trafaret = t.Dict(foo=t.ToInt, bar=t.String, allow_extra=['eggs'])
        assert repr(trafaret) == '<Dict(extras=(eggs) | <Key "bar" <String>>, <Key "foo" <ToInt>>)>'
        trafaret = trafaret.allow_extra('*')
        assert repr(trafaret) == '<Dict(any, extras=(eggs) | <Key "bar" <String>>, <Key "foo" <ToInt>>)>'
        trafaret = trafaret.ignore_extra("a")
        assert repr(trafaret) == '<Dict(any, ignore=(a), extras=(eggs) | <Key "bar" <String>>, <Key "foo" <ToInt>>)>'

    def test_key_shadowed(self):
        trafaret = t.Dict(t.Key('a', to_name='b', trafaret=t.Int))
        res = extract_error(trafaret, {'a': 5, 'b': 7})
        assert res == {'b': 'b key was shadowed'}

    def test_kwargs_extra(self):
        trafaret = t.Dict(t.Key('foo', trafaret=t.ToInt()), allow_extra=['eggs'])
        trafaret.check({"foo": 1, "eggs": None})
        trafaret.check({"foo": 1})
        with pytest.raises(t.DataError):
            trafaret.check({"foo": 2, "marmalade": 5})

    def test_kwargs_ignore(self):
        trafaret = t.Dict(t.Key('foo', trafaret=t.ToInt()), ignore_extra=['eggs'])
        trafaret.check({"foo": 1, "eggs": None})
        trafaret.check({"foo": 1})
        with pytest.raises(t.DataError):
            trafaret.check({"foo": 2, "marmalade": 5})

    def test_add_kwargs_ignore(self):
        first = t.Dict(
            t.Key('bar', trafaret=t.Int()), ignore_extra=['eggs']
        )
        second = t.Dict(
            t.Key('bar1', trafaret=t.Int())
        )
        third = first + second
        third.check({'bar': 4, 'bar1': 41})
        third.check({'bar': 4, 'bar1': 41, 'eggs': 'blabla'})

        first = t.Dict(
            t.Key('bar', trafaret=t.Int()),
        )
        second = t.Dict(
            t.Key('bar1', trafaret=t.Int()), ignore_extra=['eggs']
        )
        third = first + second
        third.check({'bar': 4, 'bar1': 41})
        third.check({'bar': 4, 'bar1': 41, 'eggs': 'blabla'})

    def test_add_kwargs_ignore_any(self):
        first = t.Dict(
            t.Key('bip', trafaret=t.String()), ignore_extra='*'
        )
        second = t.Dict(
            t.Key('bop', trafaret=t.Int())
        )

        third = first + second
        third.check({'bip': u'bam', 'bop': 17, 'matter': False})
        assert third.ignore_any

    def test_add_kwargs_extra(self):
        first = t.Dict(
            t.Key('bar', trafaret=t.Int()), allow_extra=['eggs']
        )
        second = t.Dict(t.Key('bar1', trafaret=t.Int()))
        third = first + second
        third.check({"bar": 1, "bar1": 41, "eggs": None})
        third.check({"bar": 1, "bar1": 41})
        with pytest.raises(t.DataError):
            third.check({"bar": 2, "bar1": 1, "marmalade": 5})

        first = t.Dict(t.Key('bar', trafaret=t.Int()))
        second = t.Dict(t.Key('bar1', trafaret=t.Int()), allow_extra=['eggs'])
        third = first + second
        third.check({"bar": 1, "bar1": 41, "eggs": None})
        third.check({"bar": 1, "bar1": 41})
        with pytest.raises(t.DataError):
            third.check({"bar": 2, "bar1": 1, "marmalade": 5})

    def test_callable_key(self):
        def simple_key(value):
            yield 'simple', 'simple data', []

        trafaret = t.Dict(simple_key)
        res = trafaret.check({})
        assert res == {'simple': 'simple data'}

        trafaret = t.Dict({t.Key('key'): t.String}, simple_key)
        res = trafaret.check({'key': u'blabla'})
        assert res == {'key': u'blabla', 'simple': 'simple data'}

    def test_base2(self):
        trafaret = t.Dict({t.Key('bar', optional=True): t.String}, foo=t.ToInt)
        trafaret = trafaret.allow_extra('*')
        res = trafaret.check({"foo": 1, "ham": 100, "baz": None})
        assert res == {'baz': None, 'foo': 1, 'ham': 100}
        res = extract_error(trafaret, {"bar": 1, "ham": 100, "baz": None})
        assert res == {'bar': 'value is not a string', 'foo': 'is required'}
        res = extract_error(trafaret, {"foo": 1, "bar": 1, "ham": 100, "baz": None})
        assert res == {'bar': 'value is not a string'}

    def test_base3(self):
        trafaret = t.Dict({t.Key('bar', default=u'nyanya') >> 'baz': t.String}, foo=t.ToInt)
        res = trafaret.check({'foo': 4})
        assert res == {'baz': u'nyanya', 'foo': 4}

        trafaret = trafaret.allow_extra('*')
        res = extract_error(trafaret, {'baz': u'spam', 'foo': 4})
        assert res == {'baz': 'baz key was shadowed'}

        trafaret = trafaret.allow_extra('*', trafaret=t.String)
        res = extract_error(trafaret, {'baaz': 5, 'foo': 4})
        assert res == {'baaz': 'value is not a string'}
        res = trafaret({'baaz': u'strstr', 'foo':4})
        assert res == {'baaz': u'strstr', 'foo':4, 'baz': u'nyanya'}

        trafaret = trafaret.ignore_extra('fooz')
        res = trafaret.check({'foo': 4, 'fooz': 5})
        assert res == {'baz': u'nyanya', 'foo': 4}

        trafaret = trafaret.ignore_extra('*')
        res = trafaret.check({'foo': 4, 'foor': 5})
        assert res == {'baz': u'nyanya', 'foo': 4}

    def test_add(self):
        first = t.Dict({
            t.Key('bar', default=u'nyanya') >> 'baz': t.String},
            foo=t.ToInt)
        second = t.Dict({
            t.Key('bar1', default=u'nyanya') >> 'baz1': t.String},
            foo1=t.ToInt)
        third = first + second
        res = third.check({'foo': 4, 'foo1': 41})
        assert res == {'baz': u'nyanya', 'baz1': u'nyanya', 'foo': 4, 'foo1': 41}

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

    def test_bad_args_add(self):
        dct = t.Dict(key1=t.String)
        with pytest.raises(TypeError):
            dct + 8

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
        assert res == "value is not a dict"

        res = extract_error(trafaret, Map({"foo": u"xxx"}))
        assert res == {'bar': 'is required'}

        res = extract_error(trafaret, Map({"foo": u"xxx", "bar": u'str'}))
        assert res == {'bar': "value can't be converted to float"}

    def test_keys_must_be_callable(self):
        with pytest.raises(RuntimeError) as exc_info:
            t.Dict(5)
        assert exc_info.value.args[0] == 'Keys in single attributes must be callables'

        with pytest.raises(RuntimeError) as exc_info:
            t.Dict({5: t.String})
        assert exc_info.value.args[0] == 'Non callable Keys are not supported'

    def test_clone(self):
        d = t.Dict(t.Key('a', t.Int), ignore_extra='*')
        newd = d.ignore_extra('a')
        assert newd.ignore_any is True
        assert newd.ignore == ['a']


class TestDictKeys:
    def test_dict_keys(self):
        res = t.DictKeys(['a', 'b']).check({'a': 1, 'b': 2})
        assert res == {'a': 1, 'b': 2}
        res = extract_error(t.DictKeys(['a', 'b']), {'a': 1, 'b': 2, 'c': 3})
        assert res == {'c': 'c is not allowed key'}
        res = extract_error(t.DictKeys(['key', 'key2']), {'key': 'val'})
        assert res == {'key2': 'is required'}


class TestEnumTrafaret:
    def test_enum(self):
        trafaret = t.Enum("foo", "bar", 1)
        trafaret.check("foo")
        trafaret.check(1)
        res = extract_error(trafaret, 2)
        assert res == "value doesn't match any variant"


class TestToEnum:
    def test_enum(self):
        class MyEnum(enum.Enum):
            foo = 3

        trafaret = t.ToEnum(MyEnum)
        assert trafaret.check(3) is MyEnum.foo

        res = extract_error(trafaret, 2)
        assert res == "not a valid value for <enum 'MyEnum'>"


class TestToFloat:
    def test_float(self):
        res = t.ToFloat().check(1.0)
        assert res == 1.0
        res = extract_error(t.ToFloat(), 1 + 3j)
        assert res == 'value is not float'
        res = extract_error(t.ToFloat(), 1)
        assert res == 1.0
        res = t.ToFloat(gte=2).check(3.0)
        assert res == 3.0
        res = extract_error(t.ToFloat(gte=2), 1.0)
        assert res == 'value is less than 2'
        res = t.ToFloat(lte=10).check(5.0)
        assert res == 5.0
        res = extract_error(t.ToFloat(lte=3), 5.0)
        assert res == 'value is greater than 3'
        res = t.ToFloat().check("5.0")
        assert res == 5.0

    def test_float_repr(self):
        res = t.ToFloat(gte=1)
        assert repr(res) == '<ToFloat(gte=1)>'
        res = t.ToFloat(lte=10)
        assert repr(res) == '<ToFloat(lte=10)>'
        res = t.ToFloat(gte=1, lte=10)
        assert repr(res) == '<ToFloat(gte=1, lte=10)>'
        res = t.ToFloat() > 10
        assert repr(res) == '<ToFloat(gt=10)>'
        res = t.ToFloat() >= 10
        assert repr(res) == '<ToFloat(gte=10)>'
        res = t.ToFloat() < 10
        assert repr(res) == '<ToFloat(lt=10)>'
        res = t.ToFloat() <= 10
        assert repr(res) == '<ToFloat(lte=10)>'

    def test_float_meta_repr(self):
        assert repr(t.ToFloat() > 10) == '<ToFloat(gt=10)>'
        assert repr(t.ToFloat() >= 10) == '<ToFloat(gte=10)>'
        assert repr(t.ToFloat() < 10) == '<ToFloat(lt=10)>'
        assert repr(t.ToFloat() <= 10) == '<ToFloat(lte=10)>'


class TestForwardTrafaret:
    def test_forward(self):
        node = t.Forward()
        res = extract_error(node, 'something')
        assert res == 'trafaret not set yet'
        node << t.Dict(name=t.String, children=t.List[node])
        assert node.check({"name": u"foo", "children": []}) == {'children': [], 'name': u'foo'}
        res = extract_error(node, {"name": u"foo", "children": [1]})
        assert res == {'children': {0: 'value is not a dict'}}
        res = node.check({"name": u"foo", "children": [{"name": u"bar", "children": []}]})
        assert res == {'children': [{'children': [], 'name': u'bar'}], 'name': u'foo'}

        with pytest.raises(RuntimeError):  # __rshift__ is not overridden
            node << t.Int()

    def test_repr(self):
        node = t.Forward()
        assert repr(node) == '<Forward(None)>'
        node << t.Dict(name=t.String, children=t.List[node])
        assert repr(node) == '<Forward(<Dict(<Key "children" <List(<recur>)>>, <Key "name" <String>>)>)>'


class TestToIntTrafaret:
    def test_int(self):
        res = t.ToInt().check(5)
        assert res == 5
        res = extract_error(t.ToInt(), 1.1)
        assert res == 'value is not int'
        res = extract_error(t.ToInt(), 1 + 1j)
        assert res == 'value is not int'

    def test_repr(self):
        assert repr(t.ToInt()) == '<ToInt>'


class TestList:
    def test_list(self):
        res = extract_error(t.List(t.ToInt), 1)
        assert res == 'value is not a list'
        res = t.List(t.ToInt).check([1, 2, 3])
        assert res == [1, 2, 3]
        res = t.List(t.String).check([u"foo", u"bar", u"spam"])
        assert res == [u'foo', u'bar', u'spam']
        res = extract_error(t.List(t.ToInt), [1, 2, 1 + 3j])
        assert res == {2: 'value is not int'}
        res = t.List(t.ToInt, min_length=1).check([1, 2, 3])
        assert res == [1, 2, 3]
        res = extract_error(t.List(t.ToInt, min_length=1), [])
        assert res == 'list length is less than 1'
        res = t.List(t.ToInt, max_length=2).check([1, 2])
        assert res == [1, 2]
        res = extract_error(t.List(t.ToInt, max_length=2), [1, 2, 3])
        assert res == 'list length is greater than 2'
        res = extract_error(t.List(t.ToInt), ["a"])
        assert res == {0: "value can't be converted to int"}

    def test_list_meta(self):
        with pytest.raises(RuntimeError) as exc_info:
            t.List[1:10]
        assert exc_info.value.args[0] == 'Trafaret is required for List initialization'

    def test_2_0_regression(self):
        t_request = t.Dict({
            t.Key('params', optional=True): t.Or(t.List(t.Any()), t.Mapping(t.AnyString(), t.Any())),
        })
        assert t_request.check({'params': {'aaa': 123}}) == {'params': {'aaa': 123}}

    def test_list_repr(self):
        res = t.List(t.ToInt)
        assert repr(res) == '<List(<ToInt>)>'
        res = t.List(t.ToInt, min_length=1)
        assert repr(res) == '<List(min_length=1 | <ToInt>)>'
        res = t.List(t.ToInt, min_length=1, max_length=10)
        assert repr(res) == '<List(min_length=1, max_length=10 | <ToInt>)>'
        res = t.List[t.ToInt]
        assert repr(res) == '<List(<ToInt>)>'
        res = t.List[t.ToInt, 1:]
        assert repr(res) == '<List(min_length=1 | <ToInt>)>'
        res = t.List[:10, t.ToInt]
        assert repr(res) == '<List(max_length=10 | <ToInt>)>'


class TestLiteralTrafaret:
    def test_literal(self):
        res = t.Literal('atom').check('atom')
        assert res == 'atom'

        trafaret = t.Literal("foo", "bar", 1)
        trafaret.check("foo")
        trafaret.check(1)
        res = extract_error(trafaret, 2)
        assert res == "value doesn't match any variant"

    def test_repr(self):
        trafaret = t.Literal("foo", "bar", 1)
        assert repr(trafaret), "<Literal('foo', 'bar', 1)>"


class TestIterableTrafaret:
    def test_iterable(self):
        res = extract_error(t.Iterable(t.ToInt), 1)
        assert res == 'value is not iterable'

    def test_repr(self):
        res = t.Iterable(t.ToInt)
        assert repr(res) == '<List(<ToInt>)>'
        res = t.Iterable(t.Int, min_length=0, max_length=10)
        assert repr(res) == '<List(max_length=10 | <Int>)>'
        res = t.Iterable(t.Int, min_length=1, max_length=10)
        assert repr(res) == '<List(min_length=1, max_length=10 | <Int>)>'


class TestMappingTrafaret:
    def test_mapping(self):
        trafaret = t.Mapping(t.String, t.ToInt)
        res = trafaret.check({u"foo": 1, u"bar": 2})
        assert res == {u'bar': 2, u'foo': 1}
        res = extract_error(trafaret, {u"foo": 1, u"bar": None})
        assert res == {u'bar': {'value': 'value is not int'}}
        res = extract_error(trafaret, {u"foo": 1, 2: "bar"})
        assert res == {2: {'key': 'value is not a string', 'value': "value can't be converted to int"}}
        res = extract_error(trafaret.check, None)
        assert res == 'value is not a dict'

    def test_repr(self):
        trafaret = t.Mapping(t.String, t.Int)
        assert repr(trafaret) == '<Mapping(<String> => <Int>)>'


class TestNullTrafaret:
    def test_null(self):
        res = t.Null().check(None)
        assert res is None
        res = extract_error(t.Null(), 1)
        assert res == 'value should be None'

    def test_repr(self):
        res = t.Null()
        assert repr(res) == '<Null>'


class TestOrNotToTest:
    def test_or(self):
        null_string = t.Or(t.String, t.Null)
        res = null_string.check(None)
        assert res is None
        res = null_string.check(u"test")
        assert res == u'test'
        res = extract_error(null_string, 1)
        assert res == {0: 'value is not a string', 1: 'value should be None'}

    def test_operator(self):
        check = t.String | t.ToInt
        assert check(u'a') == u'a'
        assert check(5) == 5

    def test_repr(self):
        null_string = t.Or(t.String, t.Null)
        assert repr(null_string) == '<Or(<String>, <Null>)>'
        res = t.ToInt | t.String
        assert repr(res) == '<Or(<ToInt>, <String>)>'


class TestAndTest:
    def test_and(self):
        indeed_int = t.Atom('123') & int
        assert indeed_int('123') == 123  # fixed 0.8.0 error

    def test_raise_error(self):
        other = lambda v: DataError('other error', code='other_error')
        fail_other = t.Atom('a') & other
        res = extract_error(fail_other, 'a')
        assert res == 'other error'

        ttt = t.And(other, t.Any)
        res = extract_error(ttt, 45)
        assert res == 'other error'

    def test_repr(self):
        assert repr(t.Bool & t.Null) == '<And(<Bool>, <Null>)>'


class TestToBoolTrafaret:
    @pytest.mark.parametrize('value, expected_result', [
        # True results
        ('t', True),
        ('true', True),
        ('y', True),
        ('yes', True),
        ('On', True),
        ('1', True),
        (1, True),
        (1.0, True),
        (True, True),
        # False results
        ('false', False),
        ('n', False),
        ('no', False),
        ('off', False),
        ('0', False),
        (0, False),
        (0.0, False),
        (False, False),
    ])
    def test_str_bool(self, value, expected_result):
        actual_result = t.ToBool().check(value)
        assert actual_result == expected_result

    def test_extract_error(self):
        res = extract_error(t.ToBool(), 'aloha')
        assert res == "value can't be converted to Bool"

    def test_repr(self):
        assert repr(t.ToBool()) == '<ToBool>'


class TestStringTrafaret:
    def test_string(self):
        res = t.String().check(u"foo")
        assert res == u'foo'
        res = extract_error(t.String(), u"")
        assert res == 'blank value is not allowed'
        res = t.String(allow_blank=True).check(u"")
        assert res == u''
        res = extract_error(t.String(), 1)
        assert res == 'value is not a string'
        res = t.String(min_length=2, max_length=3).check(u'123')
        assert res == u'123'
        res = extract_error(t.String(min_length=2, max_length=6), u'1')
        assert res == 'String is shorter than 2 characters'
        res = extract_error(t.String(min_length=2, max_length=6), u'1234567')
        assert res == 'String is longer than 6 characters'

        with pytest.raises(AssertionError) as exc_info:
            t.String(min_length=2, max_length=6, allow_blank=True)
        assert exc_info.value.args[0] == 'Either allow_blank or min_length should be specified, not both'

        res = t.String(min_length=0, max_length=6, allow_blank=True).check(u'123')
        assert res == u'123'

    def test_repr(self):
        res = t.String()
        assert repr(res) == '<String>'
        res = t.String(allow_blank=True)
        assert repr(res) == '<String(blank)>'


class TestDateTrafaret:
    def test_date(self):
        res = t.Date().check(date.today())
        assert res == date.today()
        now = datetime.now()
        res = t.Date().check(now)
        assert res == now
        res = t.Date().check("2019-07-25")
        assert res == '2019-07-25'
        res = extract_error(t.Date(), "25-07-2019")
        assert res == 'value does not match format %Y-%m-%d'
        res = extract_error(t.Date(), 1564077758)
        assert res == 'value cannot be converted to date'

    def test_to_date(self):
        res = t.ToDate().check("2019-07-25")
        assert res == date(year=2019, month=7, day=25)
        res = t.ToDate().check(datetime.now())
        assert res == date.today()

    def test_repr(self):
        date_repr, to_date_repr = t.Date(), t.ToDate()
        assert repr(date_repr) == '<Date %Y-%m-%d>'
        assert repr(to_date_repr) == '<ToDate %Y-%m-%d>'

        date_repr, to_date_repr = t.Date('%y-%m-%d'), t.ToDate('%y-%m-%d')
        assert repr(date_repr) == '<Date %y-%m-%d>'
        assert repr(to_date_repr) == '<ToDate %y-%m-%d>'


class TestDateTimeTrafaret:
    def test_datetime(self):
        now = datetime(year=2019, month=7, day=25, hour=21, minute=45)
        res = t.DateTime('%Y-%m-%d %H:%M').check(now)
        assert res == now
        res = t.DateTime('%Y-%m-%d %H:%M').check("2019-07-25 21:45")
        assert res == '2019-07-25 21:45'
        res = extract_error(t.DateTime(), "25-07-2019")
        assert res == 'value does not match format %Y-%m-%d %H:%M:%S'
        res = extract_error(t.DateTime(), 1564077758)
        assert res == 'value cannot be converted to datetime'

    def test_to_datetime(self):
        res = t.ToDateTime('%Y-%m-%d %H:%M').check("2019-07-25 21:45")
        assert res == datetime(year=2019, month=7, day=25, hour=21, minute=45)

    def test_repr(self):
        datetime_repr, to_datetime_repr = t.DateTime(), t.ToDateTime()
        assert repr(datetime_repr) == '<DateTime %Y-%m-%d %H:%M:%S>'
        assert repr(to_datetime_repr) == '<ToDateTime %Y-%m-%d %H:%M:%S>'

        datetime_repr, to_datetime_repr = t.DateTime('%Y-%m-%d %H:%M'), t.ToDateTime('%Y-%m-%d %H:%M')
        assert repr(datetime_repr) == '<DateTime %Y-%m-%d %H:%M>'
        assert repr(to_datetime_repr) == '<ToDateTime %Y-%m-%d %H:%M>'


class TestFromBytesTrafaret:
    def test_bytes(self):
        res = t.FromBytes().check(b"foo")
        assert res == 'foo'
        res = t.FromBytes()(b"")
        assert res == ''
        res = t.FromBytes().check(b"")
        assert res == ''
        res = extract_error(t.FromBytes(), 1)
        assert res == 'value is not a bytes'

    def test_repr(self):
        res = t.FromBytes()
        assert repr(res) == '<FromBytes>'


class TestRegexpTrafaret:
    def test_regexp(self):
        trafaret = t.Regexp('cat')
        assert trafaret('cat1212'), 'cat'

    def test_regexp_raw(self):
        trafaret = t.RegexpRaw('.*(cat).*')
        assert trafaret('cat1212').groups()[0] == 'cat'

    def test_regexp_raw_error(self):
        trafaret = t.RegexpRaw('cat')
        res = catch_error(trafaret, 'dog')
        assert res.as_dict(value=True) == 'does not match pattern cat, got \'dog\''

        res = extract_error(trafaret, None)
        assert res == 'value is not a string'

    def test_repr(self):
        assert repr(t.RegexpRaw('.*(cat).*')) == '<Regexp ".*(cat).*">'


class TestTrafaretMeta:
    def test_meta(self):
        res = (t.ToInt() >> (lambda x: x * 2) >> (lambda x: x * 3)).check(1)
        assert res == 6
        res = (t.ToInt() >> float >> str).check(4)
        assert res == '4.0'
        res = (t.ToInt >> (lambda v: v if v ** 2 > 15 else 0)).check(5)
        assert res == 5

    def test_repr(self):
        res = t.ToInt | t.String
        assert repr(res) == '<Or(<ToInt>, <String>)>'
        res = t.ToInt | t.String | t.Null
        assert repr(res) == '<Or(<Or(<ToInt>, <String>)>, <Null>)>'


class TestTupleTrafaret:
    def test_tuple(self):
        tup = t.Tuple(t.ToInt, t.ToInt, t.String)
        res = tup.check([3, 4, u'5'])
        assert res == (3, 4, u'5')
        res = extract_error(tup, [3, 4, 5])
        assert res == {2: 'value is not a string'}
        res = extract_error(tup, 5)
        assert res == 'value must be convertable to tuple'
        res = extract_error(tup, [5])
        assert res == 'value must contain 3 items'

    def test_repr(self):
        tup = t.Tuple(t.ToInt, t.ToInt, t.String)
        assert repr(tup) == '<Tuple(<ToInt>, <ToInt>, <String>)>'


class TestTypeTrafaret:
    def test_type(self):
        c = t.Type[int]
        res = c.check(1)
        assert res == 1
        res = extract_error(c, "foo")
        assert res == 'value is not int'

    def test_repr(self):
        res = t.Type(int)
        assert repr(res) == '<Type(int)>'


class TestSubclassTrafaret:
    def test_subclass(self):
        c = t.Subclass[type]

        class Type(type):
            pass

        res = c.check(Type)
        assert res == Type
        res = extract_error(c, object)
        assert res == 'value is not subclass of type'

    def test_repr(self):
        res = t.Subclass(type)
        assert repr(res) == '<Subclass(type)>'


class TestOnErrorTrafaret:
    def test_on_error(self):
        trafaret = t.OnError(t.Bool(), message='Changed message')
        res = trafaret(True)
        assert res is True

    def test_on_error_ensured_trafaret(self):
        trafaret = t.OnError(t.Bool, message='Changed message')
        res = trafaret(False)
        assert res is False

    def test_on_error_data_error(self):
        trafaret = t.OnError(t.Bool, message='Changed message')
        res = catch_error(trafaret, 'Trololo')
        assert res.as_dict() == 'Changed message'


def test_with_repr():
    ttt = t.WithRepr(t.String, '<Ttt>')
    assert repr(ttt) == '<Ttt>'


class TestGuard:
    def test_keywords_only(self):
        @guard(a=t.ToInt, b=t.AnyString)
        def fn(a, b='abba'):
            return {'a': a, 'b': b}
        assert fn(a='123') == {'a': 123, 'b': 'abba'}

        with pytest.raises(t.DataError) as exc_info:
            fn(a='bam')
        assert exc_info.value.as_dict() == {'a': 'value can\'t be converted to int'}

    def test_class_method(self):
        class A(object):
            @guard(a=t.ToInt)
            def fn(self, **kw):
                return kw
        a = A()
        assert a.fn(a='123') == {'a': 123}

    def test_args_checks(self):
        with pytest.raises(RuntimeError) as exc_info:
            @guard(123)
            def fn(**kw):
                return kw
        assert exc_info.value.args[0] == 'trafaret should be instance of Dict or Forward'

        with pytest.raises(RuntimeError) as exc_info:
            @guard(t.Dict(t.Key('a', trafaret=t.Bytes)), a=t.ToInt)
            def fn(**kw):
                return kw
        assert exc_info.value.args[0] == 'choose one way of initialization, trafaret or kwargs'


def test_ignore():
    assert t.ignore(5) is None


def test_deprecated():
    deprecated('blabla')
