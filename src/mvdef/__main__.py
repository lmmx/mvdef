from sys import argv
from pathlib import Path
from argparse import ArgumentParser
import argcomplete

from .demo import main as run_demo
from .cli import main as run_cli

argv = argv[1:] # omit the call to mvdef

def main():
    parser = ArgumentParser(
        description="Move function definitions and associated import"
        + " statements from one file to another within a library."
    )
    parser.add_argument("-t", "--test", action="store_true")
    parser.add_argument("-m", "--mvdef", action="append")
    parser.add_argument("--src", action="store")
    parser.add_argument("--dst", action="store")
    parser.add_argument("-r", "--report", action="store_true")
    parser.add_argument("-b", "--backup", action="store_true")
    parser.add_argument("-d", "--dry-run", action="store_true")

    argcomplete.autocomplete(parser)
    arg_l = parser.parse_args(argv)

    demo = arg_l.test
    mvdefs = arg_l.mvdef
    dry_run = arg_l.dry_run
    report = arg_l.report
    backup = arg_l.backup

    if demo:
        run_demo(mvdefs=["show_line"], dry_run=dry_run, report=True)
    else:
        src_path = Path(arg_l.src).absolute()
        dst_path = Path(arg_l.dst).absolute()
        run_cli(src_path, dst_path, mvdefs, dry_run, report, backup)

if __name__ == "__main__":
    main()
