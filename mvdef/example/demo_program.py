import numpy as np
from numpy import arange, pi

import matplotlib.pyplot as plt


def show_line(n=None, suppress_display=False):
    if n is None:
        n = 4
    assert type(n) in (int, np.typeDict["int"]), f"n must be an integer, {n} is not"
    assert n > 0, "Please provide a positive integer, {n} is not"
    l = arange(0, n + 1)
    if suppress_display:
        return plt.plot(l)
    plt.plot(l)
    plt.show()
    return


def print_some_pi(n=None, suppress_print=False):
    if n is None:
        n = 2
    assert type(n) in (int, np.typeDict["int"]), f"n must be an integer, {n} is not"
    message = "hello world"
    output = f"{message}, {n} pi = {n * pi}"
    if suppress_print:
        return output
    print(output)
    return
