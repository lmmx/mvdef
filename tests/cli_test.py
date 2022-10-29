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
    Test that the help text is produced on calling with `-h`, and the usage when calling
    with no arguments.
    """
    with raises(SystemExit):
        mvdef_from_argv(argv)
    captured = capsys.readouterr()
    assert captured.err == stored_error


@mark.parametrize(
    "argv,stored_output",
    [(["-h"], "HELP")],
    indirect=["stored_output"],
)
def test_help_message(capsys, argv, stored_output):
    """
    Test that the help text is produced on calling with `-h`, and the usage when calling
    with no arguments.
    """
    # diffs = get_mvdef_diffs(src_p, dst_p, mv=mv, cls_defs=cls_defs, all_defs=all_defs)
    # assert diffs == stored_diffs
    with raises(SystemExit):
        mvdef_from_argv(argv)
    captured = capsys.readouterr()
    assert captured.out == stored_output
