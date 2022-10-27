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
        """\
--- original/foo.py
+++ fixed/foo.py
@@ -3,6 +3,5 @@
 def foo():
     print(1)
 
-class A:
-    pass
+
 y = 2
"""
    ],
)
@mark.parametrize(
    "dst_diff",
    [
        """\
--- original/bar.py
+++ fixed/bar.py
@@ -1,3 +1,7 @@
 def bar():
     print(2)
 a = 1
+
+
+class A:
+    pass
"""
    ],
)
def test_mvdef_simple_class_move(tmp_path, foo, bar, src_diff, dst_diff):
    names = ("foo.py", "bar.py")
    foo_p, bar_p = write_files(names, [foo, bar], path=tmp_path, len_check=True)
    mvdef_cli_args = dict(mv=["A"], dry_run=True, escalate=True, cls_defs=True)
    foo_diff, bar_diff = cli(foo_p, bar_p, return_diffs=True, **mvdef_cli_args)
    assert foo_diff == src_diff
    assert bar_diff == dst_diff
