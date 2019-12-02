import sys
from sys import argv
import ast
from pathlib import Path
import argparse

sys.path.insert(0, "mvdef")

import src

parser = argparse.ArgumentParser(
    description="Move function definitions and associated import statements"
    + " from one file to another within a library."
)
parser.add_argument("--demo", action="store_true")

if argv[0].endswith("__main__.py"):
    argv = [a for a in argv if a != argv[0]]
arg_l = parser.parse_args(argv)

if "demo" in arg_l:
    if arg_l.demo:
        print("Demo will run")
        from src.demo import src_parsed, dst_parsed

        #src_imports, src_funcdefs = src_parsed
        src_ret = src_parsed
        if type(dst_parsed) is str:
            print(dst_parsed)
        else:
            dst_imports, dst_funcdefs = dst_parsed
