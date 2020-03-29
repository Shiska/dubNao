import logging

def logMe(level = logging.DEBUG):
    def decorator(func):
        def wrapper(*args, **kwargs):
            # # print(func.__name__, flush = True)
            logging.log(level, func.__name__)

            return func(*args, **kwargs)

        return wrapper
    return decorator

import pkgutil

__all__ = []

for loader, name, is_pkg in  pkgutil.walk_packages(__path__):
    if not is_pkg:
        __all__.append(name)
        # load the class inside each module 
        globals()[name] = getattr(loader.find_module(name).load_module(name), name)