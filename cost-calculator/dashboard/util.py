def dpath(d, *keys, **kwargs):
    '''
    We deal with a lot of deeply nested dicts from json. Some keys
    might or might not be present.  Given a sequence of keys, dpath
    pulls a value out of a path of nested dictionaries or, if the path
    doesnt exist, return a default value.
    '''
    default = None
    if 'default' in kwargs:
        default = kwargs['default']
    for key in keys:
        if key not in d:
            return default
        d = d[key]
    return d
