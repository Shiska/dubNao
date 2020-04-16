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

import importlib

for finder, name, ispkg in pkgutil.walk_packages(__path__):
    if not ispkg:
        module = importlib.import_module('.' + name, __name__)
        # someone said __all__ is used for documentation
        __all__.append(name)
        # # load the class inside each module 
        globals()[name] = getattr(module, name)