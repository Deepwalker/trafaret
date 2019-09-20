import pytest
import trafaret as t
import trafaret.lib as l


def test_with_context_caller():
    """Should not break"""
    l.with_context_caller(l.with_context_caller(lambda x: x))


def test_get_callable_args():
    class A(object):
        def __init__(self, a):
            return a

        def method(self, b):
            return b

    assert l.get_callable_args(A) == ['self', 'a']
    a = A(None)
    assert l.get_callable_args(a.method) == ['b']
    assert l.get_callable_args('a') == ()
