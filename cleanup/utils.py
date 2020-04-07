import functools
import logging
import time
from datetime import timedelta

LOGGER = logging.getLogger(__name__)


def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        res = func(*args, **kwargs)
        print(f'Finished {func.__name__!r} in {timedelta(seconds=time.perf_counter() - start)}')
        return res
    return wrapper
