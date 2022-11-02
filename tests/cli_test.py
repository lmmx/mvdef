"""
Tests for CLI functionality besides output correctness (tested in other modules).
"""
from pytest import mark, raises

from .helpers.cli_util import mvdef_from_argv


@mark.parametrize(
    "argv,stored_error",
    [([], "USAGE")],
    indirect=["stored_error"],
)
def test_usage_error(capsys, argv, stored_error):
    """
    Test that the usage text is produced on calling with no arguments.
    """
    with raises(SystemExit):
        mvdef_from_argv(argv)
    captured = capsys.readouterr()
    assert captured.err == stored_error


@mark.parametrize(
    "argv,stored_output",
    [(["-h"], "MVDEF_HELP")],
    indirect=["stored_output"],
)
def test_mvdef_help_message(capsys, argv, stored_output):
    """
    Test that the help text is produced on calling `mvdef` with `-h`.
    """
    with raises(SystemExit):
        mvdef_from_argv(argv)
    captured = capsys.readouterr()
    assert captured.out == stored_output


@mark.parametrize(
    "argv,stored_output",
    [(["-h"], "CPDEF_HELP")],
    indirect=["stored_output"],
)
def test_cpdef_help_message(capsys, argv, stored_output):
    """
    Test that the help text is produced on calling `cpdef` with `-h`.
    """
    with raises(SystemExit):
        mvdef_from_argv(argv, use_cpdef=True)
    captured = capsys.readouterr()
    assert captured.out == stored_output
