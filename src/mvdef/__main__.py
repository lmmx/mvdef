from sys import argv, stderr
from pathlib import Path
from argparse import ArgumentParser
import argcomplete

from .demo import main as run_demo
from .cli import main as run_cli, _MvAction, _IntoAction, validate_into_flag
from .transfer import parse_transfer, FileLink

prog, *argv = argv  # excise the call to mvdef as prog
USE_CALL_PATH = False
if not USE_CALL_PATH:
    prog = "mvdef" # overwrite the full call path with just 'mvdef'


def demo():
    """
    mvdef -d pprint_dict mvdef/example/demo_program.py mvdef/example/new_file.py -rb
    """
    run_demo(mvdefs=["pprint_dict"], into_paths=[None], dry_run=True, report=True)


def main():
    DEBUGGING_MODE = False
    HIDE_TRACEBACKS = True
    if "--demo" in argv:
        demo()
        return
    elif "--debug" in argv:
        argv.remove("--debug")
        DEBUGGING_MODE = True
    if "--show-tracebacks" in argv:
        argv.remove("--show-tracebacks")
        HIDE_TRACEBACKS = False

    parser = ArgumentParser(
        description="Move function definitions and associated import"
        + " statements from one file to another within a library.",
        prog=prog
    )
    parser.add_argument("src")
    parser.add_argument("dst")
    parser.add_argument("-m", "--mv", action=_MvAction)
    parser.add_argument("-i", "--into", action=_IntoAction)
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("-b", "--backup", action="store_true")
    parser.add_argument("-d", "--dry-run", action="store_true")

    if any(f in argv for f in ["-i", "--into"]):
        validate_into_flag(parser, argv)

    argcomplete.autocomplete(parser)
    arg_l = parser.parse_args(argv)  # pass explicitly to allow above debug override

    mvdefs = arg_l.mv
    into_paths = arg_l.into
    dry_run = arg_l.dry_run
    report = arg_l.verbose
    backup = arg_l.backup

    src_path = Path(arg_l.src).absolute()
    dst_path = Path(arg_l.dst).absolute()
    try:
        if DEBUGGING_MODE:
            global link
            link = FileLink(mvdefs, into_paths, src_path, dst_path, report, dry_run, None, backup)
            # Raise any error encountered when building the AST
            if isinstance(link.src.edits, Exception):
                global src_err_link
                src_err_link = link
                raise link.src.edits
            elif isinstance(link.dst.edits, Exception):
                global dst_err_link
                dst_err_link = link
                raise link.dst.edits
            print(
                f"An equivalent `link` to that computed in `run_cli({src_path=}, "
                "{dst_path=}, {mvdefs=}, {into_paths=}, {dry_run=}, {report=}, {backup=}` has been added "
                "to the global namespace.",
                file=stderr,
            )
        else:
            run_cli(src_path, dst_path, mvdefs, into_paths, dry_run, report, backup)
    except Exception as e:
        if HIDE_TRACEBACKS:
            print(f"{type(e).__name__} ⠶ {e}")
        else:
            raise e


if __name__ == "__main__":
    main()
