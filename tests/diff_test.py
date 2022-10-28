from enum import Enum
from pathlib import Path

from pytest import fixture, mark

from mvdef.cli import cli

from .io import Write

__all__ = ["test_create_named_tmp_files", "test_mvdef_simple_class_move"]


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


class SrcDiffs(Enum):
    fooA2bar_A = (
        "--- original/fooA.py\n+++ fixed/fooA.py\n@@ -3,6 +3,5 @@\n def foo():\n"
        "     print(1)\n \n-class A:\n-    pass\n+\n y = 2\n"
    )
    fooA2bar_foo = (
        "--- original/fooA.py\n+++ fixed/fooA.py\n@@ -1,7 +1,5 @@\n x = 1\n \n"
        "-def foo():\n-    print(1)\n \n class A:\n     pass\n"
    )


class DstDiffs(Enum):
    fooA2bar_A = (
        "--- original/bar.py\n+++ fixed/bar.py\n@@ -1,3 +1,7 @@\n def bar():\n"
        "     print(2)\n a = 1\n+\n+\n+class A:\n+    pass\n"
    )
    fooA2bar_foo = (
        "--- original/bar.py\n+++ fixed/bar.py\n@@ -1,3 +1,7 @@\n def bar():\n"
        "     print(2)\n a = 1\n+\n+\n+def foo():\n+    print(1)\n"
    )


@fixture(scope="function")
def src(request) -> tuple[str, str]:
    return FuncAndClsDefs[request.param]


dst = src  # Clone with another name


@fixture(scope="function")
def stored_diffs(request) -> tuple[str, str]:
    return SrcDiffs[request.param].value, DstDiffs[request.param].value


@mark.parametrize("all_defs", [True, False])
@mark.parametrize(
    "mv,cls_defs,stored_diffs",
    [
        (["A"], True, "fooA2bar_A"),
        (["A", "A"], True, "fooA2bar_A"),
        (["foo"], False, "fooA2bar_foo"),
        (["foo", "foo"], False, "fooA2bar_foo"),
    ],
    indirect=["stored_diffs"],
)
@mark.parametrize("src,dst", [("fooA", "bar")], indirect=True)
def test_simple_move(tmp_path, src, dst, mv, all_defs, cls_defs, stored_diffs):
    """
    Test that a class 'A' or a funcdef 'foo' is moved correctly, and that repeating it
    twice makes no difference to the result, and ditto for switching the all_defs flag.
    """
    src, dst = Write.from_enums(src, dst, path=tmp_path, len_check=True).file_paths
    diffs = get_mvdef_diffs(a=src, b=dst, mv=mv, cls_defs=cls_defs, all_defs=all_defs)
    assert diffs == stored_diffs
