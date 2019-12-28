from sys import path as syspath
from sys import argv
from pathlib import Path
from argparse import ArgumentParser

# Put the absolute path to the module directory on the system PATH:
syspath.insert(0, str(Path(__file__).parent))

from src.demo import main as run_demo

parser = ArgumentParser(
    description="Move function definitions and associated import"
    + " statements from one file to another within a library."
)
parser.add_argument("--demo", action="store_true")

if __name__ == "__main__":
    if argv[0].endswith("__main__.py"):
        argv = [a for a in argv if a != argv[0]]
arg_l = parser.parse_args(argv)

if "demo" in arg_l:
    if arg_l.demo:
        dry_run = False
        report = True
        run_demo(mvdefs=["show_line"], dry_run=dry_run, report=report)
