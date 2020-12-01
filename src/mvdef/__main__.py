from sys import argv
from pathlib import Path
from argparse import ArgumentParser
import argcomplete

from .demo import main as run_demo
from .cli import main as run_cli
from .transfer import parse_transfer, FileLink

argv = argv[1:] # omit the call to mvdef

def demo():
    """
    mvdef -d show_line mvdef/example/demo_program.py mvdef/example/new_file.py -rb
    """
    run_demo(mvdefs=["show_line"], dry_run=True, report=True)

DEBUG_STATE = True

def main():
    if "--demo" in argv:
        demo()
        return
    parser = ArgumentParser(
        description="Move function definitions and associated import"
        + " statements from one file to another within a library."
    )
    parser.add_argument("src")
    parser.add_argument("dst")
    #parser.add_argument("-t", "--test", action="store_true")
    parser.add_argument("-m", "--mv", action="append")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-b", "--backup", action="store_true")
    parser.add_argument("-d", "--dry-run", action="store_true")

    argcomplete.autocomplete(parser)
    arg_l = parser.parse_args(argv)

    #demo = arg_l.test
    mvdefs = arg_l.mv
    dry_run = arg_l.dry_run
    report = arg_l.verbose
    backup = arg_l.backup

    src_path = Path(arg_l.src).absolute()
    dst_path = Path(arg_l.dst).absolute()
    if DEBUG_STATE:
        print(f"RAN run_cli({src_path=}, {dst_path=}, {mvdefs=}, {dry_run=}, {report=}, {backup=}")
        print("This was equivalent to a parse_transfer call with result `pt_result`")
        global pt_result, link
        # N.B. nochange is an internal synonym for dry_run (i.e. its user-facing name)
        pt_result = parse_transfer(src_path, dst_path, mvdefs, None, report, dry_run, backup)
        # in turn pt_result is just a wrapper on
        link = FileLink(mvdefs, src_path, dst_path, report, dry_run, None, backup)
    else:
        run_cli(src_path, dst_path, mvdefs, dry_run, report, backup)
if __name__ == "__main__":
    main()
