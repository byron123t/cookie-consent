"""Function utilities."""

def memoize(func):
    """Note: Cache cleared everytime the function is re-defined. Usage: 
    @memoize
    def afunc(some_arg):
        return compute(some_arg)
    """
    cache = dict()

    def memoized_func(*args):
        if args in cache:
            return cache[args]
        result = func(*args)
        cache[args] = result
        return result

    return memoized_func
