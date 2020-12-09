from .transfer import parse_transfer
from sys import stderr
import argparse

__all__ = ["_MvAction", "_IntoAction", "main"]

class _MvAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        mv_items = getattr(namespace, self.dest, None)
        mv_items = argparse._copy_items(mv_items)
        mv_items.append(values)
        setattr(namespace, self.dest, mv_items)
        # Append a `None` to the list for the `into` dest of the parser namespace
        paired_items = getattr(namespace, self.paired_dest, None)
        paired_items = argparse._copy_items(paired_items)
        paired_items.append(None)
        setattr(namespace, self.paired_dest, paired_items)

    paired_dest = "into"

class _IntoAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest, None)
        items = argparse._copy_items(items)
        items.pop() # remove the last `None` appended by _MvAction
        items.append(values)
        setattr(namespace, self.dest, items)

def main(src_p, dst_p, mvdefs, dry_run, report, backup):
    if report:
        print("--------------RUNNING mvdef.cli⠶main()--------------", file=stderr)
    src_parsed, dst_parsed = parse_transfer(
        src_p,
        dst_p,
        mvdefs,
        test_func=None,
        report=report,
        nochange=dry_run,
        use_backup=backup,
    )
    if report:
        print("------------------COMPLETE--------------------------", file=stderr)
    return
