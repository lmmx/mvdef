from enum import Enum

__all__ = ["SrcDiffs", "DstDiffs"]


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
