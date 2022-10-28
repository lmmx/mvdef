from enum import Enum
from pathlib import Path

from pytest import fixture, mark, raises

from mvdef.cli import cli

from .io import Write

__all__ = [
    "test_create_named_tmp_files",
    "test_simple_move",
    "test_simple_move_deleted_file",
]


@mark.parametrize("a_cat,b_cat", [("aaa", "bbb")])
def test_create_named_tmp_files(tmp_path, a_cat, b_cat):
    a, b = ("a.txt", "b.txt")
    Write([a, b], [a_cat, b_cat], path=tmp_path, len_check=True)


def get_mvdef_diffs(a: Path, b: Path, **mvdef_cli_args) -> tuple[str, str]:
    kwargs_with_defaults = {"dry_run": True, "escalate": True, **mvdef_cli_args}
    a_diff, b_diff = cli(a, b, return_diffs=True, **kwargs_with_defaults)
    return a_diff, b_diff


class FuncAndClsDefs(Enum):
    fooA = "x = 1\n\ndef foo():\n    print(1)\n\nclass A:\n    pass\ny = 2\n"
    bar = "def bar():\n    print(2)\na = 1\n"
    baz = "import json\n\n\ndef baz():\n    print(2)\n\n\nx = 1\n"
    solo_baz = ""


class SrcDiffs(Enum):
    fooA2bar_A = (
        "--- original/fooA.py\n"
        "+++ fixed/fooA.py\n"
        "@@ -3,6 +3,5 @@\n"
        " def foo():\n"
        "     print(1)\n"
        " \n"
        "-class A:\n"
        "-    pass\n"
        "+\n"
        " y = 2\n"
    )
    fooA2bar_foo = (
        "--- original/fooA.py\n"
        "+++ fixed/fooA.py\n"
        "@@ -1,7 +1,5 @@\n"
        " x = 1\n"
        " \n"
        "-def foo():\n"
        "-    print(1)\n"
        " \n"
        " class A:\n"
        "     pass\n"
    )
    baz2_baz = (
        "--- original/baz.py\n"
        "+++ fixed/baz.py\n"
        "@@ -1,8 +1,4 @@\n"
        " import json\n"
        " \n"
        " \n"
        "-def baz():\n"
        "-    print(2)\n"
        "-\n"
        "-\n"
        " x = 1\n"
    )


class DstDiffs(Enum):
    fooA2bar_A = (
        "--- original/bar.py\n"
        "+++ fixed/bar.py\n"
        "@@ -1,3 +1,7 @@\n"
        " def bar():\n"
        "     print(2)\n"
        " a = 1\n"
        "+\n"
        "+\n"
        "+class A:\n"
        "+    pass\n"
    )
    fooA0bar_A = (
        "--- original/bar.py\n"
        "+++ fixed/bar.py\n"
        "@@ -0,0 +1,2 @@\n"
        "+class A:\n"
        "+    pass\n"
    )
    fooA2bar_foo = (
        "--- original/bar.py\n"
        "+++ fixed/bar.py\n"
        "@@ -1,3 +1,7 @@\n"
        " def bar():\n"
        "     print(2)\n"
        " a = 1\n"
        "+\n"
        "+\n"
        "+def foo():\n"
        "+    print(1)\n"
    )
    baz0_baz = (
        "--- original/solo_baz.py\n"
        "+++ fixed/solo_baz.py\n"
        "@@ -0,0 +1,2 @@\n"
        "+def baz():\n"
        "+    print(2)\n"
    )


@fixture(scope="function")
def src(request) -> tuple[str, str]:
    return FuncAndClsDefs[request.param]


@fixture(scope="function")
def dst(request) -> tuple[str, str]:
    dst_filename_stem = request.param
    return FuncAndClsDefs[dst_filename_stem]


@fixture(scope="function")
def stored_diffs(request) -> tuple[str, str]:
    """
    2 in the name means 'to an existing dst', e.g. x2y means 'move src=x to dst=y'.
    0 in the name means 'to a new dst', i.e. no change to src, so use the same diff,
    by replacing the 2 with a 0 when looking up the src file contents in the Enum.
    """
    src_name_key = request.param.replace("0", "2")
    dst_name_key = request.param
    return SrcDiffs[src_name_key].value, DstDiffs[dst_name_key].value


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
def test_simple_move(tmp_path, src, dst, mv, cls_defs, stored_diffs, all_defs, no_dst):
    """
    Test that a class 'A' or a funcdef 'foo' is moved correctly, and that repeating it
    twice makes no difference to the result, and ditto for switching the all_defs flag.
    """
    src, dst = Write.from_enums(src, dst, path=tmp_path, len_check=True).file_paths
    if no_dst:
        dst.unlink()
    diffs = get_mvdef_diffs(a=src, b=dst, mv=mv, cls_defs=cls_defs, all_defs=all_defs)
    assert diffs == stored_diffs


@mark.parametrize("all_defs", [True, False])
@mark.parametrize("mv,cls_defs", [(["A"], True), (["foo"], False)])
@mark.parametrize("src,dst", [("fooA", "bar")], indirect=True)
def test_simple_move_deleted_file(tmp_path, src, dst, mv, all_defs, cls_defs):
    """
    Test that a class 'A' or a funcdef 'foo' is moved correctly, and that repeating it
    twice makes no difference to the result, and ditto for switching the all_defs flag.
    """
    src, dst = Write.from_enums(src, dst, path=tmp_path, len_check=True).file_paths
    src.unlink()
    mvdef_kwargs = dict(mv=mv, cls_defs=cls_defs, all_defs=all_defs)
    with raises(FileNotFoundError):
        get_mvdef_diffs(a=src, b=dst, **mvdef_kwargs)


@mark.parametrize("all_defs", [True, False])
@mark.parametrize(
    "mv,cls_defs,no_dst,stored_diffs",
    [
        (["baz"], False, True, "baz0_baz"),
    ],
    indirect=["stored_diffs"],
)
@mark.parametrize("src,dst", [("baz", "solo_baz")], indirect=True)
def test_simple_move_no_dst(
    tmp_path, src, dst, mv, cls_defs, stored_diffs, all_defs, no_dst
):
    """
    Test that a class 'A' or a funcdef 'foo' is moved correctly, and that repeating it
    twice makes no difference to the result, and ditto for switching the all_defs flag.
    """
    src, dst = Write.from_enums(src, dst, path=tmp_path, len_check=True).file_paths
    if no_dst:
        dst.unlink()
    diffs = get_mvdef_diffs(a=src, b=dst, mv=mv, cls_defs=cls_defs, all_defs=all_defs)
    assert diffs == stored_diffs
