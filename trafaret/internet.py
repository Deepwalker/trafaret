# -*- coding: utf-8 -*-

import re
from .regexp import Regexp
from .base import String, Bytes, OnError
from .lib import py3

if py3:
    import urllib.parse as urlparse
else:
    import urlparse


MAX_EMAIL_LEN = 254


EMAIL_REGEXP = re.compile(
    # dot-atom
    r"(?P<name>^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"
    # quoted-string
    r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"'
    # domain
    r')@(?P<domain>(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)$)'
    # literal form, ipv4 address (SMTP 4.1.3)
    r'|\[(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}\]$',
    re.IGNORECASE,
)


def email_idna_encode(value):
    if '@' in value:
        parts = value.split('@')
        try:
            parts[-1] = parts[-1].encode('idna').decode('ascii')
            return '@'.join(parts)
        except UnicodeError:
            pass
    return value


email_regexp_trafaret = OnError(Regexp(EMAIL_REGEXP), 'value is not a valid email address')
email_trafaret = email_regexp_trafaret | ((Bytes('utf-8') | String()) & email_idna_encode & email_regexp_trafaret)
Email = String(allow_blank=True) & OnError(
    String(max_length=MAX_EMAIL_LEN) & email_trafaret,
    'value is not a valid email address',
)


URL_REGEXP = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:\S+(?::\S*)?@)?'  # user and password
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-_]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$',
    re.IGNORECASE,
)
URLRegexp = Regexp(URL_REGEXP)


def decode_url_idna(value):
    try:
        scheme, netloc, path, query, fragment = urlparse.urlsplit(value)
        netloc = netloc.encode('idna').decode('ascii')  # IDN -> ACE
    except UnicodeError:  # invalid domain part
        pass
    else:
        return urlparse.urlunsplit((scheme, netloc, path, query, fragment))
    return value


URL = OnError(
    URLRegexp | ((Bytes('utf-8') | String()) & decode_url_idna & URLRegexp),
    'value is not URL',
)


IPv4 = OnError(
    Regexp(
        r'^((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])$',  # noqa
    ),
    'value is not IPv4 address',
)


IPv6 = OnError(
    Regexp(
        r'^('
        r'(::)|'
        r'(::[0-9a-f]{1,4})|'
        r'([0-9a-f]{1,4}:){7,7}[0-9a-f]{1,4}|'
        r'([0-9a-f]{1,4}:){1,7}:|'
        r'([0-9a-f]{1,4}:){1,6}:[0-9a-f]{1,4}|'
        r'([0-9a-f]{1,4}:){1,5}(:[0-9a-f]{1,4}){1,2}|'
        r'([0-9a-f]{1,4}:){1,4}(:[0-9a-f]{1,4}){1,3}|'
        r'([0-9a-f]{1,4}:){1,3}(:[0-9a-f]{1,4}){1,4}|'
        r'([0-9a-f]{1,4}:){1,2}(:[0-9a-f]{1,4}){1,5}|'
        r'[0-9a-f]{1,4}:((:[0-9a-f]{1,4}){1,6})|'
        r':((:[0-9a-f]{1,4}){1,7}:)|'
        r'fe80:(:[0-9a-f]{0,4}){0,4}%[0-9a-z]{1,}|'
        r'::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|'  # noqa
        r'([0-9a-f]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])'  # noqa
        r')$',
        re.IGNORECASE,
    ),
    'value is not IPv6 address',
)


IP = OnError(IPv4 | IPv6, 'value is not IP address')
