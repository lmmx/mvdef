import defopt

from .exceptions import MvDefException
from .transfer import MvDef


def cli():
    mover = defopt.run(MvDef, no_negated_flags=True, cli_options="has_default")
    blocker = mover.check()
    if blocker is None:
        moved = mover.move()
        if mover.dry_run:
            print(moved)
