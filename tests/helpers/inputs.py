from enum import Enum

__all__ = ["FuncAndClsDefs"]


class FuncAndClsDefs(Enum):
    fooA = "x = 1\n\ndef foo():\n    print(1)\n\nclass A:\n    pass\n\ny = 2\n"
    bar = "def bar():\n    print(2)\n\na = 1\n"
    baz = "import json\n\n\ndef baz():\n    print(2)\n\n\nx = 1\n"
    log = (
        "import logging\n\n"
        "x = 1\n\n"
        "def err():\n"
        '    logging.error("Hello")\n'
        "\n\n"
        "def warn():\n"
        '    logging.warning("world")\n'
        "\n"
        "y = 2\n"
    )
    decoC = (
        "from dataclasses import dataclass\n\n"
        "x = 1\n\n\n"
        "@dataclass\nclass C:\n"
        "    c: int\n\n\n"
        "y = 2\n"
    )
    decoD = (
        "from dataclasses import dataclass\n\n\n"
        "@dataclass\nclass D:\n"
        "    d: int\n\n\n"
        "z = 3\n"
    )
    errorer = "from logging import error, info\n\n\ndef errorer():\n    error(1)"
