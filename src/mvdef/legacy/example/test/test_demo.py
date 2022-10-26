# flake8: noqa
import textwrap as tw
from os.path import sep
from sys import stderr

from ..demo_program import pprint_dict, print_some_url


def test_pprint_dict(d={"foo": 1, "bar": 2}):
    pprint_output = pprint_dict(d, return_string=True)
    assert pprint_output == "{'foo': 1, 'bar': 2}"
    return True


def test_print_some_url(url="https://spin.systems"):
    output = print_some_url(url, return_string=True)
    assert output == "hello//human, welcome to spin.systems"
    return True


def get_test_failures():
    exceptions = []
    try:
        test_pprint_dict()
    except AssertionError as e:
        msg = "Test failed: pprint_dict"
        exceptions.append(AssertionError(msg))
    try:
        test_print_some_url()
    except AssertionError as e:
        msg = "Test failed: print_some_url"
        exceptions.append(AssertionError(msg))
    return exceptions if exceptions else None


def list_failing_tests():
    """
    Returns None if no failing tests, otherwise returns a list of
    the names of the functions whose tests failed (N.B. not the name
    of the functions doing the testing, but the ones they test).
    """
    exceptions = get_test_failures()
    if exceptions:
        failed_funcs = []
        for e in exceptions:
            e_msg = getattr(e, "message", str(e))
            if e_msg.startswith("Test failed:"):
                fail_func = e_msg.split(":")[1][1:]
                failed_funcs.append(fail_func)
        return failed_funcs


def test_report(verbose=True):
    """
    Give an error if any tests are failing, otherwise return None.
    """
    failing = list_failing_tests()
    assert failing is None, f"Tests failed for {failing}"
    if verbose:
        print("✔ All tests pass", file=stderr)
    return
