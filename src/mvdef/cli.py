import defopt

from .exceptions import MvDefException
from .transfer import MvDef


def cli():
    mover = defopt.run(MvDef, no_negated_flags=True, cli_options="has_default")
    mover.check()
