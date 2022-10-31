"""
Tests for definitions that require imports to be moved/copied.
"""
from pytest import mark, raises

from .helpers.cli_util import dry_run_mvdef, get_mvdef_diffs
from .helpers.io import Write

__all__ = ["test_module_import_copy"]


@mark.parametrize(
    "mv,stored_diffs",
    [(["err"], "errwarn0_err")],
    indirect=["stored_diffs"],
)
@mark.parametrize("src,dst", [("log", "solo_err")], indirect=True)
def test_module_import_copy(tmp_path, src, dst, mv, stored_diffs):
    """
    Test that a funcdef 'err' is moved correctly, i.e. along with its import,
    which is a `logging` stdlib module import (that gets copied over).

    Note: same format for `stored_diff` as `baz0_baz` in `diff_test.py`. Here,
    `errwarn0_err` means "src with `err` and `warn`, no dst, move `err`".
    """
    src_p, dst_p = Write.from_enums(src, dst, path=tmp_path).file_paths
    diffs = get_mvdef_diffs(src_p, dst_p, mv=mv, cls_defs=False, all_defs=False)
    assert diffs == stored_diffs


@mark.parametrize("mv", [["errorer"]])
@mark.parametrize("src,dst", [("errorer", "solo_errorer")], indirect=True)
@mark.parametrize("escalate", [True, False])
def test_module_import_stay_and_go(tmp_path, src, dst, escalate, mv):
    """
    Test that a funcdef 'errorer' is not moved, but raises an error instead,
    because it contains two `logging` stdlib module imports, only one of which
    will become unused after the definition is moved.

    Cutting an import while leaving another on the same line is not yet implemented.
    """
    src_p, dst_p = Write.from_enums(src, dst, path=tmp_path).file_paths
    mvdef_kwargs = dict(mv=mv, cls_defs=False, all_defs=False, escalate=escalate)
    with raises(NotImplementedError):
        dry_run_mvdef(a=src_p, b=dst_p, **mvdef_kwargs)
