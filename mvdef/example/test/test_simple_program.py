import numpy as np
from simple_program import show_line, print_some_pi

def test_show_line(n=None):
    if n is None: n = 4
    plot_output = show_line(n, suppress_display=True)
    assert type(plot_output) is list and len(plot_output) == 1
    l = plot_output[0]
    plot_path = l.get_path()
    ext = plot_path.get_extents()
    assert np.array_equal(ext.p0, np.array([0.0, 0.0]))
    assert np.array_equal(ext.p1, np.array([float(n), float(n)]))
    return True

def test_print_some_pi(n=None):
    if n is None: n = 2
    output = print_some_pi(n, suppress_print=True)
    assert output == 'hello world, 2 pi = 6.283185307179586'
    return True

assert test_show_line()
assert test_print_some_pi()
