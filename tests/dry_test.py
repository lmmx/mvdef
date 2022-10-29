"""
Tests for functionality besides the diffs generated in 'dry run' mode (which is tested
in the `diff_test.py` module).
"""
from pytest import mark, raises

from mvdef.exceptions import CheckFailure

from .helpers.cli_util import dry_run_mvdef
from .helpers.io import Write

__all__ = ["test_no_src", "test_bad_syntax"]


@mark.parametrize("del_dst_too", [True, False])
@mark.parametrize("mv,cls_defs", [(["A"], True), (["foo"], False)])
@mark.parametrize("src,dst", [("fooA", "bar")], indirect=True)
def test_no_src(tmp_path, src, dst, mv, cls_defs, del_dst_too):
    """
    Test that if a source file isn't there, it raises an error
    """
    src_p, dst_p = Write.from_enums(src, dst, path=tmp_path).file_paths
    src_p.unlink()
    if del_dst_too:
        dst_p.unlink()
    mvdef_kwargs = dict(mv=mv, cls_defs=cls_defs)
    with raises(FileNotFoundError):
        dry_run_mvdef(a=src_p, b=dst_p, **mvdef_kwargs)


@mark.parametrize("mv,cls_defs", [(["A"], True), (["foo"], False)])
@mark.parametrize("src,dst", [("fooA", "bar")], indirect=True)
@mark.parametrize("bad_src_or_dst", [True, False])
@mark.parametrize("escalate", [True, False])
@mark.parametrize("expected_msg", ["Failed to parse the {} file"])
def test_bad_syntax(
    tmp_path, src, dst, mv, cls_defs, bad_src_or_dst, escalate, expected_msg
):
    """
    Test that a SyntaxError is raised when the input file is just `0 = 1`.
    This test is a simplified and modified form of the `diff_test.py` module's
    `test_dry_mv_deleted_file` test. The src and dst are keys present on the
    corresponding enums (to easily set up the test), but their content is not used.
    """
    src_p, dst_p = Write.from_enums(src, dst, path=tmp_path).file_paths
    mvdef_kwargs = dict(mv=mv, cls_defs=cls_defs, all_defs=False, escalate=escalate)
    overwrite_path = src_p if bad_src_or_dst else dst_p
    overwrite_path.write_text("0 = 1\n")
    if escalate:
        with raises(SyntaxError):
            dry_run_mvdef(a=src_p, b=dst_p, **mvdef_kwargs)
    else:
        result = dry_run_mvdef(a=src_p, b=dst_p, **mvdef_kwargs)
        assert type(result.mover.check_blocker) is CheckFailure
        msg = expected_msg.format("src" if bad_src_or_dst else "dst")
        assert result.mover.check_blocker.args == (msg,)
