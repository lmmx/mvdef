import numpy as np
from example.demo_program import show_line, print_some_pi
from os.path import sep


def test_show_line(n=4):
    plot_output = show_line(n, suppress_display=True)
    assert type(plot_output) is list and len(plot_output) == 1
    l = plot_output[0]
    plot_path = l.get_path()
    ext = plot_path.get_extents()
    assert np.array_equal(ext.p0, np.array([0.0, 0.0]))
    assert np.array_equal(ext.p1, np.array([float(n), float(n)]))
    return True


def test_print_some_pi(n=2):
    output = print_some_pi(n, suppress_print=True)
    assert output == sep.join(["hey", "hi"]) + ", 2 pi = 6.283185307179586"
    return True


def get_test_failures():
    exceptions = []
    try:
        assert test_show_line(), "Test failed: show_line"
    except AssertionError as e:
        exceptions.append(e)
    try:
        assert test_print_some_pi(), "Test failed: print_some_pi"
    except AssertionError as e:
        exceptions.append(e)
    if exceptions is []:
        return None
    else:
        return exceptions


def list_failing_tests():
    """
    Returns None if no failing tests, otherwise returns a list of
    the names of the functions whose tests failed (N.B. not the name
    of the functions doing the testing, but the ones they test).
    """
    exceptions = get_test_failures()
    if exceptions == []:
        return
    else:
        failed_funcs = []
        for e in exceptions:
            if e.startswith("Test failed:"):
                fail_func = e.split(":")[1][1:]
                failed_funcs.append(fail_func)
        return failed_funcs


def test_report(verbose=True):
    """
    Give an error if any tests are failing, otherwise return None.
    """
    failing = list_failing_tests()
    assert failing is None, f"Tests failed for {failing}"
    if verbose:
        print("✔ All tests pass")
    return
