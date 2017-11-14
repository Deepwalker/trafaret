import sys
import inspect


py3 = sys.version_info[0] == 3
py36 = sys.version_info >= (3, 6, 0)


if py3:
    getargspec = inspect.getfullargspec
else:
    getargspec = inspect.getargspec


_empty = object()


def py3metafix(cls):
    if not py3:
        return cls
    else:
        newcls = cls.__metaclass__(cls.__name__, (cls,), {})
        newcls.__doc__ = cls.__doc__
        return newcls


def call_with_context_if_support(callble, value, context):
    if not inspect.isfunction(callble) and hasattr(callble, '__call__'):
        callble = callble.__call__
    if 'context' in getargspec(callble).args:
        return callble(value, context=context)
    else:
        return callble(value)


def get_callable_argspec(callble):
    if inspect.isroutine(callble):
        return getargspec(callble)
    spec = getargspec(callble.__call__)
    # check if callble is bound method
    if hasattr(callble, '__self__'):
        spec.args.pop(0)  # remove `self` from args
    return spec
