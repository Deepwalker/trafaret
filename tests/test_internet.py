import unittest
import trafaret as t
from trafaret import extract_error


class TestURLTrafaret(unittest.TestCase):

    def test_url(self):
        res = t.URL.check('http://example.net/resource/?param=value#anchor')
        self.assertEqual(res, 'http://example.net/resource/?param=value#anchor')

        res = str(t.URL.check('http://пример.рф/resource/?param=value#anchor'))
        self.assertEqual(res, 'http://xn--e1afmkfd.xn--p1ai/resource/?param=value#anchor')

        res = t.URL.check('http://example_underscore.net/resource/?param=value#anchor')
        self.assertEqual(res, 'http://example_underscore.net/resource/?param=value#anchor')

        res = str(t.URL.check('http://user@example.net/resource/?param=value#anchor'))
        self.assertEqual(res, 'http://user@example.net/resource/?param=value#anchor')

        res = str(t.URL.check('http://user:@example.net/resource/?param=value#anchor'))
        self.assertEqual(res, 'http://user:@example.net/resource/?param=value#anchor')

        res = str(t.URL.check('http://user:password@example.net/resource/?param=value#anchor'))
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
        ip = t.IPv4

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
        ip = t.IPv6

        for data in self.valid_ips:
            result = ip(data)

            self.assertEqual(result, data)

        for data in self.invalid_ips:
            with self.assertRaises(t.DataError):
                ip(data)


class TestEmailTrafaret(unittest.TestCase):
    def test_email(self):
        res = t.Email.check('someone@example.net')
        self.assertEqual(res, 'someone@example.net')
        res = extract_error(t.Email,'someone@example') # try without domain-part
        self.assertEqual(res, 'value is not a valid email address')
        res = str(t.Email.check('someone@пример.рф')) # try with `idna` encoding
        self.assertEqual(res, 'someone@xn--e1afmkfd.xn--p1ai')
        # res = (t.Email() >> (lambda m: m.groupdict()['domain'])).check('someone@example.net')
        # self.assertEqual(res, 'example.net')
        res = extract_error(t.Email, 'foo')
        self.assertEqual(res, 'value is not a valid email address')
        res = extract_error(t.Email, 'f' * 10000 + '@correct.domain.edu')
        self.assertEqual(res, 'value is not a valid email address')
        res = extract_error(t.Email, 'f' * 248 + '@x.edu') == 'f' * 248 + '@x.edu'
        self.assertEqual(res, True)
        res = extract_error(t.Email, 123)
        self.assertEqual(res, 'value is not a string')
