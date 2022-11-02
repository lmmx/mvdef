from enum import Enum

__all__ = ["SrcDiffs", "DstDiffs", "StoredStdErr"]


class SrcDiffs(Enum):
    fooA2bar_A = (
        "--- original/fooA.py\n"
        "+++ fixed/fooA.py\n"
        "@@ -3,7 +3,5 @@\n"
        " def foo():\n"
        "     print(1)\n"
        " \n"
        "-class A:\n"
        "-    pass\n"
        " \n"
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
    fooA2bar_Afoo = (
        "--- original/fooA.py\n"
        "+++ fixed/fooA.py\n"
        "@@ -1,9 +1,4 @@\n"
        " x = 1\n"
        " \n"
        "-def foo():\n"
        "-    print(1)\n"
        "-\n"
        "-class A:\n"
        "-    pass\n"
        " \n"
        " y = 2\n"
    )
    fooA2bar_fooA = (
        "--- original/fooA.py\n"
        "+++ fixed/fooA.py\n"
        "@@ -1,9 +1,4 @@\n"
        " x = 1\n"
        " \n"
        "-def foo():\n"
        "-    print(1)\n"
        "-\n"
        "-class A:\n"
        "-    pass\n"
        " \n"
        " y = 2\n"
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
    decoC2decoD_C = (
        "--- original/decoC.py\n"
        "+++ fixed/decoC.py\n"
        "@@ -1,11 +1,4 @@\n"
        "-from dataclasses import dataclass\n-\n"
        " x = 1\n \n \n"
        "-@dataclass\n-class C:\n"
        "-    c: int\n-\n-\n"
        " y = 2\n"
    )
    errwarn2_err = (
        "--- original/log.py\n+++ fixed/log.py\n@@ -1,9 +1,6 @@\n import logging\n \n"
        ' x = 1\n-\n-def err():\n-    logging.error("Hello")\n \n \n def warn():\n'
    )


class DstDiffs(Enum):
    fooA2bar_A = (
        "--- original/bar.py\n"
        "+++ fixed/bar.py\n"
        "@@ -2,3 +2,7 @@\n"
        "     print(2)\n \n"
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
        "@@ -2,3 +2,7 @@\n"
        "     print(2)\n \n"
        " a = 1\n"
        "+\n"
        "+\n"
        "+def foo():\n"
        "+    print(1)\n"
    )
    fooA2bar_fooA = (
        "--- original/bar.py\n"
        "+++ fixed/bar.py\n"
        "@@ -2,3 +2,11 @@\n"
        "     print(2)\n"
        " \n"
        " a = 1\n"
        "+\n"
        "+\n"
        "+def foo():\n"
        "+    print(1)\n"
        "+\n"
        "+\n"
        "+class A:\n"
        "+    pass\n"
    )
    fooA0bar_fooA = (
        "--- original/bar.py\n"
        "+++ fixed/bar.py\n"
        "@@ -2,3 +2,11 @@\n"
        "     print(2)\n"
        " \n"
        " a = 1\n"
        "+\n"
        "+\n"
        "+def foo():\n"
        "+    print(1)\n"
        "+\n"
        "+\n"
        "+class A:\n"
        "+    pass\n"
    )
    fooA0bar_Afoo = (
        "--- original/bar.py\n"
        "+++ fixed/bar.py\n"
        "@@ -2,3 +2,11 @@\n"
        "     print(2)\n"
        " \n"
        " a = 1\n"
        "+\n"
        "+\n"
        "+class A:\n"
        "+    pass\n"
        "+\n"
        "+\n"
        "+def foo():\n"
        "+    print(1)\n"
    )
    fooA2bar_Afoo = (
        "--- original/bar.py\n"
        "+++ fixed/bar.py\n"
        "@@ -2,3 +2,11 @@\n"
        "     print(2)\n \n"
        " a = 1\n"
        "+\n"
        "+\n"
        "+class A:\n"
        "+    pass\n"
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
    decoC2decoD_C = (
        "--- original/decoD.py\n+++ fixed/decoD.py\n"
        "@@ -7,3 +7,8 @@\n \n \n"
        " z = 3\n+\n+\n"
        "+@dataclass\n+class C:\n"
        "+    c: int\n"
    )
    errwarn0_err = (
        "--- original/solo_err.py\n+++ fixed/solo_err.py\n@@ -0,0 +1,4 @@\n"
        '+import logging\n+\n+def err():\n+    logging.error("Hello")\n'
    )


class StoredStdOut(Enum):
    MVDEF_HELP = (
        "usage: mvdef [-h] -m [MV ...] [-d] [-e] [-c] [-a] [-v] src dst\n"
        "\n"
        "\xa0\xa0Move function definitions from one file to another, moving/copying\n"
        "\xa0\xa0any necessary associated import statements along with them.\n"
        "\n"
        "\xa0 Option     Description                                Type (default)\n"
        "\xa0 —————————— —————————————————————————————————————————— ——————————————\n"
        "•\xa0src        source file to take definitions from       Path\n"
        "•\xa0dst        destination file (may not exist)           Path\n"
        "•\xa0mv         names to move from the source file         list of str\n"
        "•\xa0dry_run    whether to only preview the change diffs   bool (False)\n"
        "•\xa0escalate   whether to raise an error upon failure     bool (False)\n"
        "•\xa0cls_defs   whether to target only class definitions   bool (False)\n"
        "•\xa0all_defs   whether to target both class and funcdefs  bool (False)\n"
        "•\xa0verbose    whether to log anything                    bool (False)\n"
        "\n"
        "positional arguments:\n"
        "  src\n"
        "  dst\n"
        "\n"
        "options:\n"
        "  -h, --help            show this help message and exit\n"
        "  -m [MV ...], --mv [MV ...]\n"
        "  -d, --dry-run\n"
        "  -e, --escalate\n"
        "  -c, --cls-defs\n"
        "  -a, --all-defs\n"
        "  -v, --verbose\n"
    )
    CPDEF_HELP = (
        "usage: cpdef [-h] -m [MV ...] [-d] [-e] [-c] [-a] [-v] src dst\n"
        "\n"
        "\xa0\xa0Copy function definitions from one file to another, and any necessary\n"
        "\xa0\xa0associated import statements along with them.\n"
        "\n"
        "\xa0 Option     Description                                Type (default)\n"
        "\xa0 —————————— —————————————————————————————————————————— ——————————————\n"
        "•\xa0src        source file to copy definitions from       Path\n"
        "•\xa0dst        destination file (may not exist)           Path\n"
        "•\xa0mv         names to copy from the source file         list of str\n"
        "•\xa0dry_run    whether to only preview the change diffs   bool (False)\n"
        "•\xa0escalate   whether to raise an error upon failure     bool (False)\n"
        "•\xa0cls_defs   whether to target only class definitions   bool (False)\n"
        "•\xa0all_defs   whether to target both class and funcdefs  bool (False)\n"
        "•\xa0verbose    whether to log anything                    bool (False)\n"
        "\n"
        "positional arguments:\n"
        "  src\n"
        "  dst\n"
        "\n"
        "options:\n"
        "  -h, --help            show this help message and exit\n"
        "  -m [MV ...], --mv [MV ...]\n"
        "  -d, --dry-run\n"
        "  -e, --escalate\n"
        "  -c, --cls-defs\n"
        "  -a, --all-defs\n"
        "  -v, --verbose\n"
    )


class StoredStdErr(Enum):
    USAGE = (
        "usage: mvdef [-h] -m [MV ...] [-d] [-e] [-c] [-a] [-v] src dst\n"
        "mvdef: error: the following arguments are required: src, dst, -m/--mv\n"
    )
    REJECT_0_EQ_1 = "1:1: cannot assign to literal here. Maybe you meant '==' instead of '='?\n0 = 1\n^\n"
    PROBLEM_DECODING = " problem decoding source\n"
    TYPE_DECODING = "TypeError: compile() arg 1 must be a string, bytes or AST object\n"
