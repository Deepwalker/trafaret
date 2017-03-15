import sys


py3 = sys.version_info[0] == 3


def py3metafix(cls):
    if not py3:
        return cls
    else:
        newcls = cls.__metaclass__(cls.__name__, (cls,), {})
        newcls.__doc__ = cls.__doc__
        return newcls
