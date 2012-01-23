"""
There will be small helpers to render forms with exist contracts for DRY.
"""
import collections


def concat(prefix, value, delimeter):
    return (prefix + delimeter if prefix else '') + value


def recursive_unfold(data, prefix='', delimeter='__'):

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
    """
    def pairdict_to_list(data):
        return [i[1] for i in sorted(data.items())]

    def deep(keys, value, result, prefix):
        result_ = result[prefix] if prefix is not None else result
        if len(keys) > 1:
            prefix_, key_ = keys[0], keys[1:]
            if prefix_ not in result_:
                result_[prefix_] = {}
            return deep(key_, value, result_, prefix_)

        key = keys[0]
        if key.isdigit():
            if result_ == {}:
                result[prefix] = [value]
            elif isinstance(result_, list):
                result_.append(value)
            else:
                raise ValueError('You cant mix digit only keys and usual')
        else:
            result_[keys[0]] = value

    result = {}
    for key, value in sorted(data.items()):
        deep(key.split(delimeter), value, result, None)
    return result[prefix] if prefix else result
