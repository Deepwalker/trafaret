# -*- coding: utf-8 -*-
import pytest
import trafaret as t
from trafaret import extract_error


@pytest.fixture()
def valid_ips_v4():
    return (
        '127.0.0.1',
        '8.8.8.8',
        '192.168.1.1',
    )


@pytest.fixture()
def invalid_ips_v4():
    return (
        '32.64.128.256',
        '2001:0db8:0000:0042:0000:8a2e:0370:7334',
        '192.168.1.1 ',
    )


@pytest.fixture()
def valid_ips_v6():
    return (
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


@pytest.fixture()
def invalid_ips_v6():
    return (
        '2001:0db8:z000:0042:0000:8a2e:0370:7334',
        '2001:cdba:0:0:::0:0:3257:9652',
        '2001:cdba::3257:::9652',
        '127.0.0.1',
        ':ffaa:'
    )


class TestURLTrafaret:
    def test_url(self):
        res = t.URL.check('http://example.net/resource/?param=value#anchor')
        assert res == 'http://example.net/resource/?param=value#anchor'

        res = str(t.URL.check('http://пример.рф/resource/?param=value#anchor'))
        assert res == 'http://xn--e1afmkfd.xn--p1ai/resource/?param=value#anchor'

        res = t.URL.check('http://example_underscore.net/resource/?param=value#anchor')
        assert res == 'http://example_underscore.net/resource/?param=value#anchor'

        res = str(t.URL.check('http://user@example.net/resource/?param=value#anchor'))
        assert res == 'http://user@example.net/resource/?param=value#anchor'

        res = str(t.URL.check('http://user:@example.net/resource/?param=value#anchor'))
        assert res == 'http://user:@example.net/resource/?param=value#anchor'

        res = str(t.URL.check('http://user:password@example.net/resource/?param=value#anchor'))
        assert res == 'http://user:password@example.net/resource/?param=value#anchor'

    def test_bad_str(self):
        with pytest.raises(t.DataError):
            t.URL.check(b'http://\xd0\xbf\xd1\x80\xd0\xb8\xd0\xbc\xd0\xb5\xd1\x80.\xd1\xd1\x84')


class TestEmailTrafaret:
    def test_email(self):
        res = t.Email.check('someone@example.net')
        assert res == 'someone@example.net'
        res = extract_error(t.Email, 'someone@example')  # try without domain-part
        assert res == 'value is not a valid email address'
        res = str(t.Email.check('someone@пример.рф')) # try with `idna` encoding
        assert res == 'someone@xn--e1afmkfd.xn--p1ai'
        # res = (t.Email() >> (lambda m: m.groupdict()['domain'])).check('someone@example.net')
        # assert res == 'example.net'
        res = extract_error(t.Email, 'foo')
        assert res == 'value is not a valid email address'
        res = extract_error(t.Email, 'f' * 10000 + '@correct.domain.edu')
        assert res == 'value is not a valid email address'
        res = extract_error(t.Email, 'f' * 248 + '@x.edu') == 'f' * 248 + '@x.edu'
        assert res == True
        res = extract_error(t.Email, 123)
        assert res == 'value is not a string'

    def test_bad_str(self):
        with pytest.raises(t.DataError):
            t.Email.check(b'ahha@\xd0\xbf\xd1\x80\xd0\xb8\xd0\xbc\xd0\xb5\xd1\x80.\xd1\xd1\x84')


class TestHexTrafaret:
    def test_email(self):
        res = t.Hex().check('bbd3ec7776d5684d87')
        assert res == 'bbd3ec7776d5684d87'
        res = t.Hex().check('47CCB8AEEC972')
        assert res == '47ccb8aeec972'
        res = extract_error(t.Hex(), 'apple')
        assert res == 'does not match pattern ^[0-9a-f]*$'
        res = extract_error(t.Hex(), '')
        assert res == 'blank value is not allowed'
        res = t.Hex(allow_blank=True).check('')
        assert res == ''
        res = t.Hex(min_length=2, max_length=3).check('12a')
        assert res == '12a'
        res = extract_error(t.Hex(min_length=2, max_length=6), '1')
        assert res == 'String is shorter than 2 characters'
        res = extract_error(t.Hex(min_length=2, max_length=6), '1234567')
        assert res == 'String is longer than 6 characters'

        res = t.Hex(min_length=0, max_length=6, allow_blank=True).check('abc')
        assert res == 'abc'

    def test_repr(self):
        res = t.Hex()
        assert repr(res) == '<Hex>'


class TestURLSafeTrafaret:
    def test_email(self):
        res = t.URLSafe().check('sB3ny_Vmu-C')
        assert res == 'sB3ny_Vmu-C'
        res = extract_error(t.URLSafe(), 'app/le')
        assert res == 'does not match pattern ^[0-9A-Za-z-_]*$'
        res = extract_error(t.URLSafe(), '')
        assert res == 'blank value is not allowed'
        res = t.URLSafe(allow_blank=True).check('')
        assert res == ''
        res = t.URLSafe(min_length=2, max_length=3).check('1-z')
        assert res == '1-z'
        res = extract_error(t.URLSafe(min_length=2, max_length=6), '_')
        assert res == 'String is shorter than 2 characters'
        res = extract_error(t.URLSafe(min_length=2, max_length=6), '1234567')
        assert res == 'String is longer than 6 characters'

        res = t.URLSafe(min_length=0, max_length=6, allow_blank=True).check('a_c')
        assert res == 'a_c'

    def test_repr(self):
        res = t.URLSafe()
        assert repr(res) == '<URLSafe>'


def test_ipv4(valid_ips_v4, invalid_ips_v4):
    ip = t.IPv4

    for data in valid_ips_v4:
        result = ip(data)
        assert result == data

    for data in invalid_ips_v4:
        with pytest.raises(t.DataError):
            ip(data)


def test_ipv6(valid_ips_v6, invalid_ips_v6):
    ip = t.IPv6

    for data in valid_ips_v6:
        result = ip(data)
        assert result == data

    for data in invalid_ips_v6:
        with pytest.raises(t.DataError):
            ip(data)
