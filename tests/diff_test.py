"""
Tests for the diffs created in 'dry run' mode by :meth:`Agenda.simulate()`.
"""
from pytest import mark

from .helpers.cli_util import get_mvdef_diffs
from .helpers.io import Write

__all__ = [
    "test_create_files",
    "test_dry_mv",
    "test_dry_mv_no_dst",
]


@mark.parametrize("a_cat,b_cat", [("aaa", "bbb")])
def test_create_files(tmp_path, a_cat, b_cat):
    a, b = ("a.txt", "b.txt")
    Write([a, b], [a_cat, b_cat], path=tmp_path, len_check=True)


@mark.parametrize("all_defs", [True, False])
@mark.parametrize(
    "mv,cls_defs,no_dst,stored_diffs",
    [
        (["A"], True, False, "fooA2bar_A"),
        (["A"], True, True, "fooA0bar_A"),
        (["A", "A"], True, False, "fooA2bar_A"),
        (["foo"], False, False, "fooA2bar_foo"),
        (["foo", "foo"], False, False, "fooA2bar_foo"),
    ],
    indirect=["stored_diffs"],
)
@mark.parametrize("src,dst", [("fooA", "bar")], indirect=True)
def test_dry_mv(tmp_path, src, dst, mv, cls_defs, stored_diffs, all_defs, no_dst):
    """
    Test that a class 'A' or a funcdef 'foo' is moved correctly, and that repeating it
    twice makes no difference to the result, and ditto for switching the all_defs flag.
    """
    src_p, dst_p = Write.from_enums(src, dst, path=tmp_path).file_paths
    if no_dst:
        dst_p.unlink()
    diffs = get_mvdef_diffs(src_p, dst_p, mv=mv, cls_defs=cls_defs, all_defs=all_defs)
    assert diffs == stored_diffs


@mark.parametrize("all_defs", [True, False])
@mark.parametrize(
    "mv,cls_defs,no_dst,stored_diffs",
    [
        (["baz"], False, True, "baz0_baz"),
    ],
    indirect=["stored_diffs"],
)
@mark.parametrize("src,dst", [("baz", "solo_baz")], indirect=True)
def test_dry_mv_no_dst(
    tmp_path, src, dst, mv, cls_defs, stored_diffs, all_defs, no_dst
):
    """
    Test that a class 'A' or a funcdef 'foo' is moved correctly, and that repeating it
    twice makes no difference to the result, and ditto for switching the all_defs flag.
    """
    src_p, dst_p = Write.from_enums(src, dst, path=tmp_path, len_check=True).file_paths
    if no_dst:
        dst_p.unlink()
    diffs = get_mvdef_diffs(src_p, dst_p, mv=mv, cls_defs=cls_defs, all_defs=all_defs)
    assert diffs == stored_diffs
