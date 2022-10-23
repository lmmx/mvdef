import defopt

from .exceptions import MvDefException
from .transfer import MvDef


def cli():
    mover = defopt.run(
        MvDef, no_negated_flags=True, cli_options="has_default", show_defaults=False
    )
    blocker = mover.check()
    if blocker is None:
        if mover.dry_run:
            src_diff, dst_diff = mover.diffs()
            print(src_diff)
            print(dst_diff)
        else:
            mover.move()
