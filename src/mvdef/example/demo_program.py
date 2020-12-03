import functools as ft
from pprint import pprint, pformat
import urllib.request as req
from os.path import (
    basename as bname,
    sep as pathsep,
    islink,
)


def pprint_dict(d, return_string=True):
    dict_pprint = ft.partial(pprint, sort_dicts=False)
    dict_pprint(d)  # trivial use of a partial function
    if return_string:
        dict_pformat = ft.partial(pformat, sort_dicts=False)
        return dict_pformat(d)


def print_some_url(url, return_string=True):
    message = f"hello{pathsep*2}human"
    loc = req.urlsplit(url).netloc
    output = f"{message}, welcome to {loc}"
    print(output)
    if return_string:
        return output
