import requests
import itertools
import os

LOGO = """
 _______ _______ __   __
|   _   |       |  |_|  |
|  |_|  |    ___|       |
|       |   | __|       |
|       |   ||  |       |
|   _   |   |_| | ||_|| |
|__| |__|_______|_|   |_|"""

# All the places to look for config files and json keys
AGM_PATH = os.path.expanduser("~/.agm")
KEYFILE_PATHS = [AGM_PATH]


def chunk_iter(iterable, n):
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, n))
        if not chunk:
            return
        yield chunk
