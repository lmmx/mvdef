"""
Tests for CLI functionality besides output correctness (tested in other modules).
"""

from pytest import mark, raises

from .helpers.cli_util import cmd_from_argv
from .helpers.subproc_util import subproc_cmd_from_argv


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
        cmd_from_argv(argv)
    captured = capsys.readouterr()
    assert captured.err == stored_error


@mark.parametrize("subproc", [True, False])
@mark.parametrize(
    "argv,stored_output",
    [(["-h"], "MVDEF_HELP")],
    indirect=["stored_output"],
)
def test_mvdef_help_message(capsys, subproc, argv, stored_output):
    """
    Test that the help text is produced on calling `mvdef` with `-h`.
    """
    if subproc:
        proc = subproc_cmd_from_argv(argv)
        assert proc.returncode == 0
        assert proc.stdout.decode() == stored_output
    else:
        with raises(SystemExit):
            cmd_from_argv(argv)
        captured = capsys.readouterr()
        assert captured.out == stored_output


@mark.parametrize("subproc", [True, False])
@mark.parametrize(
    "argv,stored_output",
    [(["-h"], "CPDEF_HELP")],
    indirect=["stored_output"],
)
def test_cpdef_help_message(capsys, subproc, argv, stored_output):
    """
    Test that the help text is produced on calling `cpdef` with `-h`.
    """
    if subproc:
        proc = subproc_cmd_from_argv(argv, cp_=True)
        assert proc.returncode == 0
        assert proc.stdout.decode() == stored_output
    else:
        with raises(SystemExit):
            cmd_from_argv(argv, cp_=True)
        captured = capsys.readouterr()
        assert captured.out == stored_output


@mark.parametrize("subproc", [True, False])
@mark.parametrize(
    "argv,stored_output",
    [(["-h"], "LSDEF_HELP")],
    indirect=["stored_output"],
)
def test_lsdef_help_message(capsys, subproc, argv, stored_output):
    """
    Test that the help text is produced on calling `cpdef` with `-h`.
    """
    if subproc:
        proc = subproc_cmd_from_argv(argv, ls_=True)
        assert proc.returncode == 0
        assert proc.stdout.decode() == stored_output
    else:
        with raises(SystemExit):
            cmd_from_argv(argv, ls_=True)
        captured = capsys.readouterr()
        assert captured.out == stored_output
