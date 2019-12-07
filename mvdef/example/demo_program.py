import numpy as np
from numpy import arange, pi
import matplotlib.pyplot as plt
from os.path import (
    basename as aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa,
    sep as pathsep,
    islink,
)


def show_line(n=4, suppress_display=False):
    assert type(n) in (int, np.typeDict["int"]), f"n must be an integer, {n} is not"
    assert n > 0, "Please provide a positive integer, {n} is not"
    l = arange(0, n + 1)
    if suppress_display:
        return plt.plot(l)
    plt.plot(l)
    plt.show()
    return


def print_some_pi(n=2, suppress_print=False):
    assert type(n) in (int, np.typeDict["int"]), f"n must be an integer, {n} is not"
    message = f"hey{pathsep}hi"
    output = f"{message}, {n} pi = {n * pi}"
    if suppress_print:
        return output
    print(output)
    return
