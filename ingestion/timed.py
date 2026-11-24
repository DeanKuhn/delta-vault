"""Simple time decorator."""

import functools
import time


def timed(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        total = time.perf_counter() - start
        print(f"Function {func.__name__} took {total:.2f} seconds.")
        return result

    return wrapper
