from enum import Enum

__all__ = ["FuncAndClsDefs"]


class FuncAndClsDefs(Enum):
    fooA = "x = 1\n\ndef foo():\n    print(1)\n\nclass A:\n    pass\ny = 2\n"
    bar = "def bar():\n    print(2)\na = 1\n"
    baz = "import json\n\n\ndef baz():\n    print(2)\n\n\nx = 1\n"
    solo_baz = ""
    deco = (
        "import random\n"
        "from functools import cache\n"
        "\n"
        "x = 1\n"
        "\n"
        "\n"
        "@cache\n"
        "def rando():\n"
        '    "Function that picks a random number only once."\n'
        "    return random.randint(0, 1000)\n"
        "\n"
        "\n"
        "class A:\n"
        "    pass\n"
        "\n"
        "\n"
        "y = 2"
    )
