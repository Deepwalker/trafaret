# -*- coding: utf-8 -*-
import unittest
import trafaret as t
from collections import Mapping as AbcMapping
from trafaret import extract_error, ignore, DataError
from trafaret.extras import KeysSubset


class TestAnyTrafaret(unittest.TestCase):
    def test_any(self):
        self.assertEqual(
            (t.Any() >> ignore).check(object()),
            None
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


class TestCallTrafaret(unittest.TestCase):
    def test_call(self):
        def validator(value):
            if value != "foo":
                return t.DataError("I want only foo!")
            return 'foo'
        trafaret = t.Call(validator)
        res = trafaret.check("foo")
        self.assertEqual(res, 'foo')
        err = extract_error(trafaret, "bar")
        self.assertEqual(err, 'I want only foo!')


class TestCallableTrafaret(unittest.TestCase):
    def test_callable(self):
        (t.Callable() >> t.ignore).check(lambda: 1)
        res = extract_error(t.Callable(), 1)
        self.assertEqual(res, 'value is not callable')


class TestDictTrafaret(unittest.TestCase):
    def test_base(self):
        trafaret = t.Dict(foo=t.Int, bar=t.String) >> t.ignore
        trafaret.check({"foo": 1, "bar": "spam"})
        res = t.extract_error(trafaret, {"foo": 1, "bar": 2})
        self.assertEqual(res, {'bar': 'value is not a string'})
        res = extract_error(trafaret, {"foo": 1})
        self.assertEqual(res, {'bar': 'is required'})
        res = extract_error(trafaret, {"foo": 1, "bar": "spam", "eggs": None})
        self.assertEqual(res, {'eggs': 'eggs is not allowed key'})
        res = trafaret.allow_extra("eggs")
        self.assertEqual(repr(res), '<Dict(extras=(eggs) | bar=<String>, foo=<Int>)>')
        trafaret.check({"foo": 1, "bar": "spam", "eggs": None})
        trafaret.check({"foo": 1, "bar": "spam"})
        res = extract_error(trafaret, {"foo": 1, "bar": "spam", "ham": 100})
        self.assertEqual(res, {'ham': 'ham is not allowed key'})
        trafaret.allow_extra("*")
        trafaret.check({"foo": 1, "bar": "spam", "ham": 100})
        trafaret.check({"foo": 1, "bar": "spam", "ham": 100, "baz": None})
        res = extract_error(trafaret, {"foo": 1, "ham": 100, "baz": None})
        self.assertEqual(res, {'bar': 'is required'})

    def test_kwargs_extra(self):
        trafaret = t.Dict(t.Key('foo', trafaret=t.Int()), allow_extra=['eggs'])
        trafaret.check({"foo": 1, "eggs": None})
        trafaret.check({"foo": 1})
        with self.assertRaises(t.DataError):
            trafaret.check({"foo": 2, "marmalade": 5})

    def test_kwargs_ignore(self):
        trafaret = t.Dict(t.Key('foo', trafaret=t.Int()), ignore_extra=['eggs'])
        trafaret.check({"foo": 1, "eggs": None})
        trafaret.check({"foo": 1})
        with self.assertRaises(t.DataError):
            trafaret.check({"foo": 2, "marmalade": 5})

    def test_old_keys(self):
        class OldKey(object):
            def pop(self, value):
                data = value.pop('testkey')
                yield 'testkey', data

            def set_trafaret(self, trafaret):
                pass
        trafaret = t.Dict({
            OldKey(): t.Any
        })
        res = trafaret.check({'testkey': 123})
        self.assertEqual(res, {'testkey': 123})

    def test_callable_key(self):
        def simple_key(value):
            yield 'simple', 'simple data', []

        trafaret = t.Dict(simple_key)
        res = trafaret.check({})
        self.assertEqual(res, {'simple': 'simple data'})

        trafaret = t.Dict({t.Key('key'): t.String}, simple_key)
        res = trafaret.check({'key': 'blabla'})
        self.assertEqual(res, {'key': 'blabla', 'simple': 'simple data'})


    def test_base2(self):
        trafaret = t.Dict({t.Key('bar', optional=True): t.String}, foo=t.Int)
        trafaret.allow_extra('*')
        res = trafaret.check({"foo": 1, "ham": 100, "baz": None})
        self.assertEqual(res, {'baz': None, 'foo': 1, 'ham': 100})
        res = extract_error(trafaret, {"bar": 1, "ham": 100, "baz": None})
        self.assertEqual(res, {'bar': 'value is not a string', 'foo': 'is required'})
        res = extract_error(trafaret, {"foo": 1, "bar": 1, "ham": 100, "baz": None})
        self.assertEqual(res, {'bar': 'value is not a string'})

    def test_base3(self):
        trafaret = t.Dict({t.Key('bar', default='nyanya') >> 'baz': t.String}, foo=t.Int)
        res = trafaret.check({'foo': 4})
        self.assertEqual(res, {'baz': 'nyanya', 'foo': 4})

        trafaret.allow_extra('*')
        res = extract_error(trafaret, {'baz': 'spam', 'foo': 4})
        self.assertEqual(res, {'baz': 'baz key was shadowed'})

        trafaret.allow_extra('*', trafaret=t.String)
        res = extract_error(trafaret, {'baaz': 5, 'foo': 4})
        self.assertEqual(res, {'baaz': 'value is not a string'})
        res = trafaret({'baaz': 'strstr', 'foo':4})
        self.assertEqual(res, {'baaz': 'strstr', 'foo':4, 'baz': 'nyanya'})

        trafaret.ignore_extra('fooz')
        res = trafaret.check({'foo': 4, 'fooz': 5})
        self.assertEqual(res, {'baz': 'nyanya', 'foo': 4})

        trafaret.ignore_extra('*')
        res = trafaret.check({'foo': 4, 'foor': 5})
        self.assertEqual(res, {'baz': 'nyanya', 'foo': 4})

    def test_add(self):
        first = t.Dict({
            t.Key('bar', default='nyanya') >> 'baz': t.String},
            foo=t.Int)
        second = t.Dict({
            t.Key('bar1', default='nyanya') >> 'baz1': t.String},
            foo1=t.Int)
        third = first + second
        res = third.check({'foo': 4, 'foo1': 41})
        self.assertEqual(res, {'baz': 'nyanya', 'baz1': 'nyanya', 'foo': 4, 'foo1': 41})

    def test_bad_add_names(self):
        first = t.Dict({
            t.Key('bar', default='nyanya') >> 'baz': t.String},
            foo=t.Int)
        second = t.Dict({
            t.Key('bar1', default='nyanya') >> 'baz1': t.String},
            foo=t.Int)
        with self.assertRaises(ValueError):
            first + second

    def test_bad_add_to_names(self):
        first = t.Dict({
            t.Key('bar', default='nyanya') >> 'baz': t.String},
            foo=t.Int)
        second = t.Dict({
            t.Key('bar1', default='nyanya') >> 'baz': t.String},
            foo1=t.Int)
        with self.assertRaises(ValueError):
            first + second

    def test_add_to_names_list_of_keys(self):
        dct = t.Dict(key1=t.String)
        dct + [t.Key('a', trafaret=t.String())]

    def test_add_to_names_dict_of_keys(self):
        dct = t.Dict(key1=t.String)
        dct + {'a': t.String}

    def test_mapping_interface(self):
        trafaret = t.Dict({t.Key("foo"): t.String, t.Key("bar"): t.Float})

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

        trafaret.check(Map({"foo": "xxx", "bar": 0.1}))

        res = extract_error(trafaret, object())
        self.assertEqual(res, "value is not a dict")

        res = extract_error(trafaret, Map({"foo": "xxx"}))
        self.assertEqual(res, {'bar': 'is required'})

        res = extract_error(trafaret, Map({"foo": "xxx", "bar": 'str'}))
        self.assertEqual(res, {'bar': "value can't be converted to float"})




class TestDictKeys(unittest.TestCase):

    def test_dict_keys(self):
        res = t.DictKeys(['a', 'b']).check({'a': 1, 'b': 2})
        self.assertEqual(res, {'a': 1, 'b': 2})
        res = extract_error(t.DictKeys(['a', 'b']), {'a': 1, 'b': 2, 'c': 3})
        self.assertEqual(res, {'c': 'c is not allowed key'})
        res = extract_error(t.DictKeys(['key', 'key2']), {'key': 'val'})
        self.assertEqual(res, {'key2': 'is required'})


class TestEmailTrafaret(unittest.TestCase):
    def test_email(self):
        res = t.Email().check('someone@example.net')
        self.assertEqual(res, 'someone@example.net')
        res = extract_error(t.Email(),'someone@example') # try without domain-part
        self.assertEqual(res, 'value is not a valid email address')
        res = str(t.Email().check('someone@пример.рф')) # try with `idna` encoding
        self.assertEqual(res, 'someone@xn--e1afmkfd.xn--p1ai')
        res = (t.Email() >> (lambda m: m.groupdict()['domain'])).check('someone@example.net')
        self.assertEqual(res, 'example.net')
        res = extract_error(t.Email(), 'foo')
        self.assertEqual(res, 'value is not a valid email address')
        res = extract_error(t.Email(), 'f' * 10000 + '@correct.domain.edu')
        self.assertEqual(res, 'value is not a valid email address')
        res = extract_error(t.Email(), 'f' * 248 + '@x.edu') == 'f' * 248 + '@x.edu'
        self.assertEqual(res, True)
        res = extract_error(t.Email(), 123)
        self.assertEqual(res, 'value is not a string')


class TestEnumTrafaret(unittest.TestCase):
    def test_enum(self):
        trafaret = t.Enum("foo", "bar", 1) >> ignore
        self.assertEqual(repr(trafaret), "<Enum('foo', 'bar', 1)>")
        res = trafaret.check("foo")
        res = trafaret.check(1)
        res = extract_error(trafaret, 2)
        self.assertEqual(res, "value doesn't match any variant")



class TestFloat(unittest.TestCase):
    def test_float_repr(self):
        res = t.Float()
        self.assertEqual(repr(res), '<Float>')
        res = t.Float(gte=1)
        self.assertEqual(repr(res), '<Float(gte=1)>')
        res = t.Float(lte=10)
        self.assertEqual(repr(res), '<Float(lte=10)>')
        res = t.Float(gte=1, lte=10)
        self.assertEqual(repr(res), '<Float(gte=1, lte=10)>')

    def test_float(self):
        res = t.Float().check(1.0)
        self.assertEqual(res, 1.0)
        res = extract_error(t.Float(), 1 + 3j)
        self.assertEqual(res, 'value is not float')
        res = extract_error(t.Float(), 1)
        self.assertEqual(res, 1.0)
        res = t.Float(gte=2).check(3.0)
        self.assertEqual(res, 3.0)
        res = extract_error(t.Float(gte=2), 1.0)
        self.assertEqual(res, 'value is less than 2')
        res = t.Float(lte=10).check(5.0)
        self.assertEqual(res, 5.0)
        res = extract_error(t.Float(lte=3), 5.0)
        self.assertEqual(res, 'value is greater than 3')
        res = t.Float().check("5.0")
        self.assertEqual(res, 5.0)



class TestForwardTrafaret(unittest.TestCase):

    def test_forward(self):
        node = t.Forward()
        node << t.Dict(name=t.String, children=t.List[node])
        self.assertEqual(repr(node), '<Forward(<Dict(children=<List(<recur>)>, name=<String>)>)>')
        res = node.check({"name": "foo", "children": []}) == {'children': [], 'name': 'foo'}
        self.assertEqual(res, True)
        res = extract_error(node, {"name": "foo", "children": [1]})
        self.assertEqual(res, {'children': {0: 'value is not a dict'}})
        res = node.check({"name": "foo", "children": [{"name": "bar", "children": []}]})
        self.assertEqual(res, {'children': [{'children': [], 'name': 'bar'}], 'name': 'foo'})
        empty_node = t.Forward()
        self.assertEqual(repr(empty_node), '<Forward(None)>')
        res = extract_error(empty_node, 'something')
        self.assertEqual(res, 'trafaret not set yet')



class TestIntTrafaret(unittest.TestCase):

    def test_int(self):
        res = repr(t.Int())
        self.assertEqual(res, '<Int>')
        res = t.Int().check(5)
        self.assertEqual(res, 5)
        res = extract_error(t.Int(), 1.1)
        self.assertEqual(res, 'value is not int')
        res = extract_error(t.Int(), 1 + 1j)
        self.assertEqual(res, 'value is not int')


class TestKey(unittest.TestCase):
    def test_key(self):
        default = lambda: 1
        res = t.Key(name='test', default=default)
        self.assertEqual(repr(res), '<Key "test">')
        res = next(t.Key(name='test', default=default)({}))
        self.assertEqual(res, ('test', 1, ('test',)))
        res = next(t.Key(name='test', default=2)({}))
        self.assertEqual(res, ('test', 2, ('test',)))
        default = lambda: None
        res = next(t.Key(name='test', default=default)({}))
        self.assertEqual(res, ('test', None, ('test',)))
        res = next(t.Key(name='test', default=None)({}))
        self.assertEqual(res, ('test', None, ('test',)))
        # res = next(t.Key(name='test').pop({}))
        # self.assertEqual(res, ('test', DataError(is required)))
        res = list(t.Key(name='test', optional=True)({}))
        self.assertEqual(res, [])



class TestList(unittest.TestCase):

    def test_list_repr(self):
        res = t.List(t.Int)
        self.assertEqual(repr(res), '<List(<Int>)>')
        res = t.List(t.Int, min_length=1)
        self.assertEqual(repr(res), '<List(min_length=1 | <Int>)>')
        res = t.List(t.Int, min_length=1, max_length=10)
        self.assertEqual(repr(res), '<List(min_length=1, max_length=10 | <Int>)>')

    def test_list(self):
        res = extract_error(t.List(t.Int), 1)
        self.assertEqual(res, 'value is not a list')
        res = t.List(t.Int).check([1, 2, 3])
        self.assertEqual(res, [1, 2, 3])
        res = t.List(t.String).check(["foo", "bar", "spam"])
        self.assertEqual(res, ['foo', 'bar', 'spam'])
        res = extract_error(t.List(t.Int), [1, 2, 1 + 3j])
        self.assertEqual(res, {2: 'value is not int'})
        res = t.List(t.Int, min_length=1).check([1, 2, 3])
        self.assertEqual(res, [1, 2, 3])
        res = extract_error(t.List(t.Int, min_length=1), [])
        self.assertEqual(res, 'list length is less than 1')
        res = t.List(t.Int, max_length=2).check([1, 2])
        self.assertEqual(res, [1, 2])
        res = extract_error(t.List(t.Int, max_length=2), [1, 2, 3])
        self.assertEqual(res, 'list length is greater than 2')
        res = extract_error(t.List(t.Int), ["a"])
        self.assertEqual(res, {0: "value can't be converted to int"})

    def test_list_meta(self):
        res = t.List[t.Int]
        self.assertEqual(repr(res), '<List(<Int>)>')
        res = t.List[t.Int, 1:]
        self.assertEqual(repr(res), '<List(min_length=1 | <Int>)>')
        res = t.List[:10, t.Int]
        self.assertEqual(repr(res), '<List(max_length=10 | <Int>)>')
        # TODO
        # res = t.List[1:10]
        # self.assertEqual(res, Traceback (most recent call last):
        #     ...
        #     RuntimeError: Trafaret is required for List initialization


class TestMappingTrafaret(unittest.TestCase):

    def test_mapping(self):
        trafaret = t.Mapping(t.String, t.Int)
        self.assertEqual(repr(trafaret), '<Mapping(<String> => <Int>)>')
        res = trafaret.check({"foo": 1, "bar": 2})
        self.assertEqual(res, {'bar': 2, 'foo': 1})
        res = extract_error(trafaret, {"foo": 1, "bar": None})
        self.assertEqual(res, {'bar': {'value': 'value is not int'}})
        res = extract_error(trafaret, {"foo": 1, 2: "bar"})
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


class TestNumMeta(unittest.TestCase):

    def test_num_meta_repr(self):
        res = t.Int[1:]
        self.assertEqual(repr(res), '<Int(gte=1)>')
        res = t.Int[1:10]
        self.assertEqual(repr(res), '<Int(gte=1, lte=10)>')
        res = t.Int[:10]
        self.assertEqual(repr(res), '<Int(lte=10)>')
        res = t.Float[1:]
        self.assertEqual(repr(res), '<Float(gte=1)>')
        res = t.Int > 3
        self.assertEqual(repr(res), '<Int(gt=3)>')
        res = 1 < (t.Float < 10)
        self.assertEqual(repr(res), '<Float(gt=1, lt=10)>')

    def test_meta_res(self):
        res = (t.Int > 5).check(10)
        self.assertEqual(res, 10)
        res = extract_error(t.Int > 5, 1)
        self.assertEqual(res, 'value should be greater than 5')
        res = (t.Int < 3).check(1)
        self.assertEqual(res, 1)
        res = extract_error(t.Int < 3, 3)
        self.assertEqual(res, 'value should be less than 3')


class TestOrNotToTest(unittest.TestCase):
    def test_or(self):
        nullString = t.Or(t.String, t.Null)
        self.assertEqual(repr(nullString), '<Or(<String>, <Null>)>')
        res = nullString.check(None)
        res = nullString.check("test")
        self.assertEqual(res, 'test')
        res = extract_error(nullString, 1)
        self.assertEqual(res, {0: 'value is not a string', 1: 'value should be None'})
        res = t.Or << t.Int << t.String
        self.assertEqual(repr(res), '<Or(<Int>, <String>)>')

    def test_operator(self):
        check = t.String | t.Int
        self.assertEqual(check('a'), 'a')
        self.assertEqual(check(5), 5)


class TestAndTest(unittest.TestCase):
    def test_and(self):
        indeed_int = t.Atom('123') & int
        self.assertEqual(indeed_int('123'), 123) # fixed 0.8.0 error


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



class TestStringTrafaret(unittest.TestCase):

    def test_string(self):
        res = t.String()
        self.assertEqual(repr(res), '<String>')
        res = t.String(allow_blank=True)
        self.assertEqual(repr(res), '<String(blank)>')
        res = t.String().check("foo")
        self.assertEqual(res, 'foo')
        res = extract_error(t.String(), "")
        self.assertEqual(res, 'blank value is not allowed')
        res = t.String(allow_blank=True).check("")
        self.assertEqual(res, '')
        res = extract_error(t.String(), 1)
        self.assertEqual(res, 'value is not a string')
        res = t.String(regex='\w+').check('wqerwqer')
        self.assertEqual(res, 'wqerwqer')
        res = extract_error(t.String(regex='^\w+$'), 'wqe rwqer')
        self.assertEqual(res, "value does not match pattern: '^\\\\w+$'")
        res = t.String(min_length=2, max_length=3).check('123')
        self.assertEqual(res, '123')
        res = extract_error(t.String(min_length=2, max_length=6), '1')
        self.assertEqual(res, 'String is shorter than 2 characters')
        res = extract_error(t.String(min_length=2, max_length=6), '1234567')
        self.assertEqual(res, 'String is longer than 6 characters')
        # TODO
        # res = String(min_length=2, max_length=6, allow_blank=True)
        # self.assertEqual(res, Traceback (most recent call last):
        #     ...
        #     AssertionError: Either allow_blank or min_length should be specified, not both
        res = t.String(min_length=0, max_length=6, allow_blank=True).check('123')
        self.assertEqual(res, '123')

class TestRegexpTrafaret(unittest.TestCase):
    def test_regexp(self):
        trafaret = t.Regexp('cat')
        self.assertEqual(trafaret('cat1212'), 'cat')

    def test_regexp_raw(self):
        trafaret = t.RegexpRaw('.*(cat).*')
        self.assertEqual(trafaret('cat1212').groups()[0], 'cat')


class TestTrafaretMeta(unittest.TestCase):
    def test_meta(self):
        res = (t.Int() >> (lambda x: x * 2) >> (lambda x: x * 3)).check(1)
        self.assertEqual(res, 6)
        res = (t.Int() >> float >> str).check(4)
        self.assertEqual(res, '4.0')
        res = t.Int | t.String
        self.assertEqual(repr(res), '<Or(<Int>, <String>)>')
        res = t.Int | t.String | t.Null
        self.assertEqual(repr(res), '<Or(<Int>, <String>, <Null>)>')
        res = (t.Int >> (lambda v: v if v ** 2 > 15 else 0)).check(5)
        self.assertEqual(res, 5)



class TestTupleTrafaret(unittest.TestCase):
    def test_tuple(self):
        tup = t.Tuple(t.Int, t.Int, t.String)
        self.assertEqual(repr(tup), '<Tuple(<Int>, <Int>, <String>)>')
        res = tup.check([3, 4, '5'])
        self.assertEqual(res, (3, 4, '5'))
        res = extract_error(tup, [3, 4, 5])
        self.assertEqual(res, {2: 'value is not a string'})


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


class TestURLTrafaret(unittest.TestCase):

    def test_url(self):
        res = t.URL().check('http://example.net/resource/?param=value#anchor')
        self.assertEqual(res, 'http://example.net/resource/?param=value#anchor')

        res = str(t.URL().check('http://пример.рф/resource/?param=value#anchor'))
        self.assertEqual(res, 'http://xn--e1afmkfd.xn--p1ai/resource/?param=value#anchor')

        res = t.URL().check('http://example_underscore.net/resource/?param=value#anchor')
        self.assertEqual(res, 'http://example_underscore.net/resource/?param=value#anchor')

        res = str(t.URL().check('http://user@example.net/resource/?param=value#anchor'))
        self.assertEqual(res, 'http://user@example.net/resource/?param=value#anchor')

        res = str(t.URL().check('http://user:@example.net/resource/?param=value#anchor'))
        self.assertEqual(res, 'http://user:@example.net/resource/?param=value#anchor')

        res = str(t.URL().check('http://user:password@example.net/resource/?param=value#anchor'))
        self.assertEqual(res, 'http://user:password@example.net/resource/?param=value#anchor')


class TestIPv4Trafaret(unittest.TestCase):
    def setUp(self):
        self.valid_ips = (
            '127.0.0.1',
            '8.8.8.8',
            '192.168.1.1',
        )

        self.invalid_ips = (
            '32.64.128.256',
            '2001:0db8:0000:0042:0000:8a2e:0370:7334',
            '192.168.1.1 ',
        )

    def test_ipv4(self):
        ip = t.IPv4()

        for data in self.valid_ips:
            result = ip(data)

            self.assertEqual(result, data)

        for data in self.invalid_ips:
            with self.assertRaises(t.DataError):
                ip(data)


class TestIPv6Trafaret(unittest.TestCase):
    def setUp(self):
        self.valid_ips = (
            '2001:0db8:0000:0042:0000:8a2e:0370:7334',
            '2001:0Db8:0000:0042:0000:8A2e:0370:7334',
            '2001:cdba:0:0:0:0:3257:9652',
            '2001:cdba::3257:9652',
            'fe80::',
            '::',
            '::1',
            '2001:db8::',
            'ffaa::',
            '::ffff:255.255.255.0',
            '2001:db8:3:4::192.168.1.1',
            'fe80::1:2%en0',
        )

        self.invalid_ips = (
            '2001:0db8:z000:0042:0000:8a2e:0370:7334',
            '2001:cdba:0:0:::0:0:3257:9652',
            '2001:cdba::3257:::9652',
            '127.0.0.1',
            ':ffaa:'
        )

    def test_ipv6(self):
        ip = t.IPv6()

        for data in self.valid_ips:
            result = ip(data)

            self.assertEqual(result, data)

        for data in self.invalid_ips:
            with self.assertRaises(t.DataError):
                ip(data)


class TestKeysSubset(unittest.TestCase):
    def test_keys_subset(self):
        cmp_pwds = lambda x: {'pwd': x['pwd'] if x.get('pwd') == x.get('pwd1') else t.DataError('Not equal')}
        d = t.Dict({KeysSubset('pwd', 'pwd1'): cmp_pwds, 'key1': t.String})

        res = d.check({'pwd': 'a', 'pwd1': 'a', 'key1': 'b'}).keys()
        self.assertEqual(list(sorted(res)), ['key1', 'pwd'])

        res = extract_error(d.check, {'pwd': 'a', 'pwd1': 'c', 'key1': 'b'})
        self.assertEqual(res, {'pwd': 'Not equal'})

        res = extract_error(d.check, {'pwd': 'a', 'pwd1': None, 'key1': 'b'})
        self.assertEqual(res, {'pwd': 'Not equal'})

        get_values = (lambda d, keys: [d[k] for k in keys if k in d])
        join = (lambda d: {'name': ' '.join(get_values(d, ['name', 'last']))})
        res = t.Dict({KeysSubset('name', 'last'): join}).check({'name': 'Adam', 'last': 'Smith'})
        self.assertEqual(res, {'name': 'Adam Smith'})

        res = t.Dict({KeysSubset(): t.Dict({'a': t.Any})}).check({'a': 3})
        self.assertEqual(res, {'a': 3})


class TestDataError(unittest.TestCase):
    def test_dataerror_value(self):
        error = t.DataError(error='Wait for good value', value='BAD ONE')
        self.assertEqual(
            error.as_dict(),
            'Wait for good value'
        )
        self.assertEqual(
            error.as_dict(value=True),
            "Wait for good value, got 'BAD ONE'"
        )

    def test_nested_dataerror_value(self):
        error = t.DataError(error={0: t.DataError(error='Wait for good value', value='BAD ONE')})
        self.assertEqual(
            error.as_dict(),
            {0: 'Wait for good value'}
        )
        self.assertEqual(
            error.as_dict(value=True),
            {0: "Wait for good value, got 'BAD ONE'"}
        )


# res = @guard(a=String, b=Int, c=String)
#     def fn(a, b, c="default"):
#         '''docstring'''
#         return (a, b, c)
# res = fn.__module__ = None
# res = help(fn)
# self.assertEqual(res, Help on function fn:
#     <BLANKLINE>
#     fn(*args, **kwargs)
#         guarded with <Dict(a=<String>, b=<Int>, c=<String>)>
#     <BLANKLINE>
#         docstring
#     <BLANKLINE>
# **********************************************************************
# File "/Users/mkrivushin/w/trafaret/trafaret/__init__.py", line 1260, in trafaret.guard
# Failed example:
#     help(fn)
# Expected:
#     Help on function fn:
#     <BLANKLINE>
#     fn(*args, **kwargs)
#         guarded with <Dict(a=<String>, b=<Int>, c=<String>)>
#     <BLANKLINE>
#         docstring
#     <BLANKLINE>
# Got:
#     Help on function fn:
#     <BLANKLINE>
#     fn(a, b, c='default')
#         guarded with <Dict(a=<String>, b=<Int>, c=<String>)>
#     <BLANKLINE>
#         docstring
#     <BLANKLINE>
# res = fn("foo", 1)
# self.assertEqual(res, ('foo', 1, 'default')
# res = extract_error(fn, "foo", 1, 2)
# self.assertEqual(res, {'c': 'value is not a string'}
# res = extract_error(fn, "foo")
# self.assertEqual(res, {'b': 'is required'}
# res = g = guard(Dict())
# res = c = Forward()
# res = c << Dict(name=str, children=List[c])
# res = g = guard(c)
# res = g = guard(Int())
# self.assertEqual(res, Traceback (most recent call last):
#     ...
#     RuntimeError: trafaret should be instance of Dict or Forward
# res = a = Int >> ignore
# res = a.check(7)
# ***Test Failed*** 2 failures.



# res = _dd(fold({'a__a': 4}))
# self.assertEqual(res, "{'a': {'a': 4}}"
# res = _dd(fold({'a__a': 4, 'a__b': 5}))
# self.assertEqual(res, "{'a': {'a': 4, 'b': 5}}"
# res = _dd(fold({'a__1': 2, 'a__0': 1, 'a__2': 3}))
# self.assertEqual(res, "{'a': [1, 2, 3]}"
# res = _dd(fold({'form__a__b': 5, 'form__a__a': 4}, 'form'))
# self.assertEqual(res, "{'a': {'a': 4, 'b': 5}}"
# res = _dd(fold({'form__a__b': 5, 'form__a__a__0': 4, 'form__a__a__1': 7}, 'form'))
# self.assertEqual(res, "{'a': {'a': [4, 7], 'b': 5}}"
# res = repr(fold({'form__1__b': 5, 'form__0__a__0': 4, 'form__0__a__1': 7}, 'form'))
# self.assertEqual(res, "[{'a': [4, 7]}, {'b': 5}]"
# res = _dd(unfold({'a': 4, 'b': 5}))
# self.assertEqual(res, "{'a': 4, 'b': 5}"
# res = _dd(unfold({'a': [1, 2, 3]}))
# self.assertEqual(res, "{'a__0': 1, 'a__1': 2, 'a__2': 3}"
# res = _dd(unfold({'a': {'a': 4, 'b': 5}}))
# self.assertEqual(res, "{'a__a': 4, 'a__b': 5}"
# res = _dd(unfold({'a': {'a': 4, 'b': 5}}, 'form'))
# self.assertEqual(res, "{'form__a__a': 4, 'form__a__b': 5}"




# res = from trafaret import Int
# res = class A(object):
#         class B(object):
#             d = {'a': 'word'}
# res = dict((DeepKey('B.d.a') >> 'B_a').pop(A))
# self.assertEqual(res, {'B_a': 'word'}
# res = dict((DeepKey('c.B.d.a') >> 'B_a').pop({'c': A}))
# self.assertEqual(res, {'B_a': 'word'}
# res = dict((DeepKey('B.a') >> 'B_a').pop(A))
# self.assertEqual(res, {'B.a': DataError(Unexistent key)}
# res = dict(DeepKey('c.B.d.a', to_name='B_a', trafaret=Int()).pop({'c': A}))
# self.assertEqual(res, {'B_a': DataError(value can't be converted to int)}
