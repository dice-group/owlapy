def MOVE(*args):
    """"Move" an imported class to the current module by setting the classes __module__ attribute.

    This is useful for documentation purposes to hide internal packages in sphinx.

    Args:
        args: List of classes to move.
    """
    from inspect import currentframe
    f = currentframe()
    f = f.f_back
    mod = f.f_globals['__name__']
    for cls in args:
        cls.__module__ = mod
