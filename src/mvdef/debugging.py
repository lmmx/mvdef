from functools import partial
from pprint import pprint

pprint = partial(pprint, sort_dicts=False)

def debug_here():
    return pprint
