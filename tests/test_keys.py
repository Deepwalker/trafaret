import unittest
import trafaret as t
from trafaret.extras import KeysSubset
from trafaret.visitor import DeepKey
from trafaret.keys import subdict
from trafaret import catch_error, extract_error, DataError


class TestKey(unittest.TestCase):
    def test_key(self):
        default = lambda: 1
        res = t.Key(name='test', default=default)
        self.assertEqual(repr(res), '<Key "test" <Any>>')
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

    def test_key_return_original_name_on_error(self):
        res = list(t.Key(name='test', to_name='tost', trafaret=t.Int())({'test': 'a'}))[0]
        assert res[0] == 'test'  # must be original key name
        assert isinstance(res[1], DataError)


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


class TestDeepKey(unittest.TestCase):
    def test_fetch_value_by_path(self):
        class A(object):
            class B(object):
                d = {'a': 'word'}

        res = dict((DeepKey('B.d.a') >> 'B_a').pop(A))
        self.assertEqual(res, {'B_a': 'word'})


class TestSubdict(unittest.TestCase):
    def test_subdict_sample(self):
        def check_passwords_equal(data):
            if data['password'] != data['password_confirm']:
                return t.DataError('Passwords are not equal')
            return data['password']

        check_password = t.String()
        passwords_key = subdict(
            'password',
            t.Key('password', trafaret=check_password),
            t.Key('password_confirm', trafaret=check_password),
            trafaret=check_passwords_equal,
        )

        signup_trafaret = t.Dict(
            t.Key('email', trafaret=t.Email),
            passwords_key,
        )

        res = signup_trafaret({'email': 'me@gmail.com', 'password': 'qwerty', 'password_confirm': 'qwerty'})
        assert res == {'email': 'me@gmail.com', 'password': 'qwerty'}

        res = catch_error(signup_trafaret, {'email': 'me@gmail.com', 'password': 'qwerty', 'password_confirm': 'not qwerty'})
        assert res.as_dict() == {'password': 'Passwords are not equal'}

        res = catch_error(signup_trafaret, {'email': 'me@gmail.com', 'password': 'qwerty'})
        assert res.as_dict() == {'password_confirm': 'is required'}
