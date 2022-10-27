from pytest import mark

from mvdef.cli import cli

from .io import write_files

__all__ = ["test_create_named_tmp_files", "test_mvdef_simple_class_move"]


@mark.parametrize("a_cat,b_cat", [("aaa", "bbb")])
def test_create_named_tmp_files(tmp_path, a_cat, b_cat):
    a, b = ("a.txt", "b.txt")
    write_files([a, b], [a_cat, b_cat], path=tmp_path, len_check=True)


@mark.parametrize(
    "foo",
    ["x = 1\n\ndef foo():\n    print(1)\n\nclass A:\n    pass\ny = 2\n"],
)
@mark.parametrize(
    "bar",
    ["def bar():\n    print(2)\na = 1\n"],
)
@mark.parametrize(
    "src_diff",
    [
        "--- original/foo.py\n+++ fixed/foo.py\n@@ -3,6 +3,5 @@\n def foo():\n     print(1)\n \n-class A:\n-    pass\n+\n y = 2\n"
    ],
)
@mark.parametrize(
    "dst_diff",
    [
        "--- original/bar.py\n+++ fixed/bar.py\n@@ -1,3 +1,7 @@\n def bar():\n     print(2)\n a = 1\n+\n+\n+class A:\n+    pass\n"
    ],
)
def test_mvdef_simple_class_move(tmp_path, foo, bar, src_diff, dst_diff):
    names = ("foo.py", "bar.py")
    foo_p, bar_p = write_files(names, [foo, bar], path=tmp_path, len_check=True)
    mvdef_cli_args = dict(mv=["A"], dry_run=True, escalate=True, cls_defs=True)
    foo_diff, bar_diff = cli(foo_p, bar_p, return_diffs=True, **mvdef_cli_args)
    assert foo_diff == src_diff
    assert bar_diff == dst_diff
