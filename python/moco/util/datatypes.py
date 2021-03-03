import collections
import six


class AttributeDict(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


def flatten(d, parent_key='', sep='.'):
    """Un-nest a dict 'd' by creating a flat dict with previous hierarchy separated with 'sep'"""
    items = []
    prefix = ''
    if parent_key is not '':
        prefix = str(parent_key) + sep
    for k, v in d.items():
        new_key = prefix + str(k)
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def unflatten(d, sep='.'):
    """Create a nested dict by replacing all occurrences of 'sep' with a new dict"""
    ud = {}
    for k, v in d.items():
        context = ud
        for sub_key in k.split(sep)[:-1]:
            if sub_key not in context:
                context[sub_key] = {}
            context = context[sub_key]
        context[k.split(sep)[-1]] = v
    return ud


def list_flatten(s):
    if not s:
        return s
    if isinstance(s[0], list):
        return list_flatten(s[0]) + list_flatten(s[1:])
    return s[:1] + list_flatten(s[1:])


def set_values(obj, data):
    for k, v in six.iteritems(data):
        if isinstance(v, collections.Iterable) or isinstance(v, collections.Mapping):
            set_values(getattr(obj, k), v)
        else:
            setattr(obj, k, v)


def update(d, u, allow_undefined=False):
    """
    Update a dict 'd' with the values from 'u', recursively
    If 'allow_undefined' is True, won't raise error if a key in 'u' doesn't exist in 'd'
    """
    for k, v in six.iteritems(u):
        if k not in d:
            if allow_undefined:
                d[k] = v
            continue
        if isinstance(v, collections.Mapping):
            d[k] = update(d[k], v, allow_undefined)
        else:
            try:
                # This special case for int allows for base conversion from strings, ie: "0xAB"
                if isinstance(d[k], int) and isinstance(v, six.string_types):
                    d[k] = int(v, 0)
                else:
                    d[k] = type(d[k])(v)
            except TypeError:
                d[k] = v
    return d
