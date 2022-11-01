"""
Tests for the diffs created in 'dry run' mode by :meth:`Agenda.simulate()`.
"""
from pytest import mark, raises

from mvdef.exceptions import CheckFailure

from .helpers.cli_util import dry_run_mvdef, get_mvdef_diffs
from .helpers.io import Write

__all__ = [
    "test_create_files",
    "test_dry_mv_basic",
    "test_dry_mv_multidef_not_all_defs",
    "test_dry_mv_multidef_all_defs",
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
def test_dry_mv_basic(tmp_path, src, dst, mv, cls_defs, stored_diffs, all_defs, no_dst):
    """
    Test that a class 'A' or a funcdef 'foo' is moved correctly, and that repeating it
    twice makes no difference to the result, and ditto for switching the all_defs flag.
    """
    src_p, dst_p = Write.from_enums(src, dst, path=tmp_path).file_paths
    if no_dst:
        dst_p.unlink()
    diffs = get_mvdef_diffs(src_p, dst_p, mv=mv, cls_defs=cls_defs, all_defs=all_defs)
    assert diffs == stored_diffs


@mark.parametrize("all_defs", [False])
@mark.parametrize("cls_defs", [True, False])
@mark.parametrize("mv", [["foo", "A"], ["A", "foo"]])
@mark.parametrize(
    "src,dst,stored_diffs", [("fooA", "bar", "fooA2bar_fooA")], indirect=True
)
def test_dry_mv_multidef_not_all_defs(
    tmp_path,
    src,
    dst,
    mv,
    all_defs,
    cls_defs,
    stored_diffs,
):
    """
    Test that if a class 'A' and a funcdef 'foo' are moved without the `all_defs`
    flag, a `CheckFailure` error is raised.
    """
    src_p, dst_p = Write.from_enums(src, dst, path=tmp_path).file_paths
    with raises(CheckFailure):
        dry_run_mvdef(src_p, dst_p, mv=mv, cls_defs=cls_defs, all_defs=all_defs)


@mark.parametrize("cls_defs", [True, False])
@mark.parametrize(
    "mv,no_dst,stored_diffs",
    [
        (["foo", "A"], True, "fooA0bar_fooA"),
        (["foo", "A"], False, "fooA2bar_fooA"),
        (["A", "foo"], True, "fooA0bar_Afoo"),
        (["A", "foo"], False, "fooA2bar_Afoo"),
    ],
    indirect=["stored_diffs"],
)
@mark.parametrize(
    "src,dst",
    [("fooA", "bar")],
    indirect=True,
)
def test_dry_mv_multidef_all_defs(
    tmp_path, src, dst, mv, no_dst, stored_diffs, cls_defs
):
    """
    Test that a class 'A' and a funcdef 'foo' are moved correctly (in the
    same order as in `mv`), and that switching the `cls_defs` flag makes
    no difference to the result.
    """
    src_p, dst_p = Write.from_enums(src, dst, path=tmp_path).file_paths
    mvdef_kwargs = dict(mv=mv, cls_defs=cls_defs, all_defs=True)
    diffs = get_mvdef_diffs(src_p, dst_p, **mvdef_kwargs)
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
