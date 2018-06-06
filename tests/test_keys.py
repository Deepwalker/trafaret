import unittest
import trafaret as t
from trafaret.keys import (
    KeysSubset,
    subdict,
    xor_key,
    confirm_key,
)
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

        res = d.check({'pwd': u'a', 'pwd1': u'a', 'key1': u'b'}).keys()
        self.assertEqual(list(sorted(res)), [u'key1', u'pwd'])

        res = extract_error(d.check, {'pwd': u'a', 'pwd1': u'c', 'key1': u'b'})
        self.assertEqual(res, {'pwd': 'Not equal'})

        res = extract_error(d.check, {'pwd': u'a', 'pwd1': None, 'key1': u'b'})
        self.assertEqual(res, {'pwd': 'Not equal'})

        get_values = (lambda d, keys: [d[k] for k in keys if k in d])
        join = (lambda d: {'name': u' '.join(get_values(d, ['name', 'last']))})
        res = t.Dict({KeysSubset('name', 'last'): join}).check({'name': u'Adam', 'last': u'Smith'})
        self.assertEqual(res, {'name': u'Adam Smith'})

        bad_res = lambda d: t.DataError({'error key': u'bad res'})
        trafaret = t.Dict({KeysSubset('name', 'last'): bad_res})
        res = extract_error(trafaret, {'name': u'Adam', 'last': u'Smith'})
        res = {'error key': 'bad res'}


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

        res = signup_trafaret({'email': u'me@gmail.com', 'password': u'qwerty', 'password_confirm': u'qwerty'})
        assert res == {'email': u'me@gmail.com', 'password': u'qwerty'}

        res = catch_error(signup_trafaret, {'email': u'me@gmail.com', 'password': u'qwerty', 'password_confirm': u'not qwerty'})
        assert res.as_dict() == {'password': 'Passwords are not equal'}

        res = catch_error(signup_trafaret, {'email': u'me@gmail.com', 'password': u'qwerty'})
        assert res.as_dict() == {'password_confirm': 'is required'}


class TestXorKey(unittest.TestCase):
    def test_xor_key(self):
        trafaret = t.Dict(xor_key('name', 'nick', t.String()))

        res = trafaret({'name': u'Nickolay'})
        assert res == {'name': u'Nickolay'}

        res = catch_error(trafaret, {'name': u'Nickolay', 'nick': u'Sveta'})
        assert res.as_dict() == {
            'name': 'correct only if nick is not defined',
            'nick': 'correct only if name is not defined',
        }
        res = catch_error(trafaret, {})
        assert res.as_dict() == {
            'name': 'is required if nick is not defined',
            'nick': 'is required if name is not defined',
        }


class TestConfirmKey(unittest.TestCase):
    def test_confirm_key(self):
        trafaret = t.Dict(confirm_key('password', 'password_confirm', t.String()))

        res = trafaret({'password': u'qwerty', 'password_confirm': u'qwerty'})
        assert res == {'password': u'qwerty', 'password_confirm': u'qwerty'}

        res = catch_error(trafaret, {'password_confirm': u'qwerty'})
        assert res.as_dict() == {'password': 'is required'}

        res = catch_error(trafaret, {'password': u'qwerty'})
        assert res.as_dict() == {'password_confirm': 'is required'}

        res = catch_error(trafaret, {'password': u'qwerty', 'password_confirm': u'not qwerty'})
        assert res.as_dict() == {'password_confirm': 'must be equal to password'}
