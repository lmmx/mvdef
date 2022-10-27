from enum import Enum
from pathlib import Path

from pytest import mark

from mvdef.cli import cli

from .io import write_files

__all__ = ["test_create_named_tmp_files", "test_mvdef_simple_class_move"]


@mark.parametrize("a_cat,b_cat", [("aaa", "bbb")])
def test_create_named_tmp_files(tmp_path, a_cat, b_cat):
    a, b = ("a.txt", "b.txt")
    write_files([a, b], [a_cat, b_cat], path=tmp_path, len_check=True)


def get_mvdef_diffs(a: Path, b: Path, **mvdef_cli_args) -> tuple[str, str]:
    kwargs_with_defaults = {"dry_run": True, "escalate": True, **mvdef_cli_args}
    a_diff, b_diff = cli(a, b, return_diffs=True, **kwargs_with_defaults)
    return a_diff, b_diff


class FuncAndClsDefs(Enum):
    def_foo_cls_A = "x = 1\n\ndef foo():\n    print(1)\n\nclass A:\n    pass\ny = 2\n"
    def_bar = "def bar():\n    print(2)\na = 1\n"


class SrcDiffs(Enum):
    FooWithoutBar = (
        "--- original/foo.py\n+++ fixed/foo.py\n@@ -3,6 +3,5 @@\n def foo():\n"
        "     print(1)\n \n-class A:\n-    pass\n+\n y = 2\n"
    )


class DstDiffs(Enum):
    FooWithoutBar = (
        "--- original/bar.py\n+++ fixed/bar.py\n@@ -1,3 +1,7 @@\n def bar():\n"
        "     print(2)\n a = 1\n+\n+\n+class A:\n+    pass\n"
    )


@mark.parametrize(
    "mv,cls_defs",
    [
        (["A"], True),
        (["A", "A"], True),
        # (["foo"], False),
        # (["foo", "foo"], False),
    ],
)
@mark.parametrize("foo", [FuncAndClsDefs.def_foo_cls_A.value])
@mark.parametrize("bar", [FuncAndClsDefs.def_bar.value])
@mark.parametrize("src_diff", [SrcDiffs.FooWithoutBar.value])
@mark.parametrize("dst_diff", [DstDiffs.FooWithoutBar.value])
def test_mvdef_simple_class_move(tmp_path, mv, cls_defs, foo, bar, src_diff, dst_diff):
    """
    Test that a class 'A' is moved correctly, and that repeating it twice makes no
    difference to the result.
    """
    names = ("foo.py", "bar.py")
    foo_p, bar_p = write_files(names, [foo, bar], path=tmp_path, len_check=True)
    foo_diff, bar_diff = get_mvdef_diffs(a=foo_p, b=bar_p, mv=mv, cls_defs=cls_defs)
    assert foo_diff == src_diff
    assert bar_diff == dst_diff
