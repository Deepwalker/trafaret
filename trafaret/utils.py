"""
There will be small helpers to render forms with exist contracts for DRY.
"""
import collections
from itertools import groupby


def recursive_unfold(data, prefix='', delimeter='__'):

    def concat(prefix, value, delimeter):
        return (prefix + delimeter if prefix else '') + value

    def unfold_list(data, prefix, delimeter):
        i = 0
        for value in data:
            for pair in recursive_unfold(
                    value, concat(prefix, str(i), delimeter), delimeter):
                yield pair
            i += 1

    def unfold_dict(data, prefix, delimeter):
        for key, value in data.items():
            for pair in recursive_unfold(
                    value, concat(prefix, key, delimeter), delimeter):
                yield pair

    if isinstance(data, collections.Mapping):
        for pair in unfold_dict(data, prefix, delimeter):
            yield pair

    elif isinstance(data, (list, tuple)):
        for pair in unfold_list(data, prefix, delimeter):
            yield pair

    else:
        yield prefix, data


def unfold(data, prefix='', delimeter='__'):
    """
    >>> unfold({'a': 4, 'b': 5})
    {'a': 4, 'b': 5}
    >>> unfold({'a': [1, 2, 3]})
    {'a__1': 2, 'a__0': 1, 'a__2': 3}
    >>> unfold({'a': {'a': 4, 'b': 5}})
    {'a__a': 4, 'a__b': 5}
    >>> unfold({'a': {'a': 4, 'b': 5}}, 'form')
    {'form__a__b': 5, 'form__a__a': 4}
    """
    return dict(recursive_unfold(data, prefix, delimeter))


def fold(data, prefix='', delimeter='__'):
    """
    >>> fold({'a__a': 4, 'a__b': 5})
    {'a': {'a': 4, 'b': 5}}
    >>> fold({'a__1': 2, 'a__0': 1, 'a__2': 3})
    {'a': [1, 2, 3]}
    >>> fold({'form__a__b': 5, 'form__a__a': 4}, 'form')
    {'a': {'a': 4, 'b': 5}}
    >>> fold({'form__a__b': 5, 'form__a__a__0': 4, 'form__a__a__1': 7}, 'form')
    {'a': {'a': [4, 7], 'b': 5}}
    >>> fold({'form__1__b': 5, 'form__0__a__0': 4, 'form__0__a__1': 7}, 'form')
    [{'a': [4, 7]}, {'b': 5}]
    """
    def deep(data):
        if len(data) == 1:
            if data[0][0]:
                return {data[0][0][0]: data[0][1]}
            return data[0][1]

        collect = {}
        for key, group in groupby(data, lambda kv: kv[0][0]):
            nest_data = [(k[1:], v) for k, v in group]
            collect[key] = deep(nest_data)

        is_num = all(k.isdigit() for k in collect.keys())
        if is_num:
            return [i[1] for i in sorted(collect.items())]
        return collect

    data_ = [(key.split(delimeter), value)
                 for key, value in sorted(data.items())]
    result = deep(data_)
    return result[prefix] if prefix else result
