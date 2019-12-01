import sys
from sys import argv
import ast
from pathlib import Path
import argparse

sys.path.insert(0, "mvdef")

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
        from src import demo
