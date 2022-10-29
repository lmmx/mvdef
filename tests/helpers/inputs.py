from enum import Enum

__all__ = ["FuncAndClsDefs"]


class FuncAndClsDefs(Enum):
    fooA = "x = 1\n\ndef foo():\n    print(1)\n\nclass A:\n    pass\ny = 2\n"
    bar = "def bar():\n    print(2)\na = 1\n"
    baz = "import json\n\n\ndef baz():\n    print(2)\n\n\nx = 1\n"
    solo_baz = ""
