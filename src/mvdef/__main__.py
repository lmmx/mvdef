from sys import path as syspath
from sys import argv
from pathlib import Path
from argparse import ArgumentParser
import argcomplete

# Put the absolute path to the module directory on the system PATH:
syspath.insert(0, str(Path(__file__).parent))

from mvdef.demo import main as run_demo
from mvdef.cli import main as run_cli

parser = ArgumentParser(
    description="Move function definitions and associated import"
    + " statements from one file to another within a library."
)
parser.add_argument("--demo", action="store_true")
parser.add_argument("-m", "--mvdef", action="append")
parser.add_argument("--src", action="store")
parser.add_argument("--dst", action="store")
parser.add_argument("-r", "--report", action="store_true")
parser.add_argument("-b", "--backup", action="store_true")
parser.add_argument("-d", "--dry-run", action="store_true")


if __name__ == "__main__":
    if argv[0].endswith("__main__.py"):
        argv = [a for a in argv if a != argv[0]]

argcomplete.autocomplete(parser)
arg_l = parser.parse_args(argv)

if not arg_l.demo:
    src_path = Path(arg_l.src).absolute()
    dst_path = Path(arg_l.dst).absolute()
    mvdefs = arg_l.mvdef
    dry_run = arg_l.dry_run
    report = arg_l.report
    backup = arg_l.backup
    run_cli(src_path, dst_path, mvdefs, dry_run, report, backup)
else:
    run_demo(mvdefs=["show_line"], dry_run=False, report=True)
