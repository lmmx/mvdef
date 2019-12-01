import sys
from sys import argv
import ast
from pathlib import Path
import argparse

lib_dir = Path(__file__).resolve().parents[1]  # 'Top level', containing README
assert lib_dir.exists() and lib_dir.is_dir()
module_dir = lib_dir / "mvdef"  # Module below top level (containing this file)
assert module_dir.exists() and module_dir.is_dir()
example_dir = module_dir / "example"
assert example_dir.exists() and example_dir.is_dir()

sys.path.insert(0, "mvdef")

parser = argparse.ArgumentParser(
    description="Move function definitions and associated import statements from one file to another within a library."
)
parser.add_argument("--demo", action="store_true")

if argv[0].endswith(".py"):
    argv = list(reversed(argv))
    argv.pop()
    argv = list(reversed(argv))

arg_l = parser.parse_args(argv)

if "demo" in arg_l:
    if arg_l.demo:
        print("Demo will run")
        from src import demo

        demo.init({"example_dir": Path(example_dir)})
