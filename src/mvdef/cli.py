import defopt

from .transfer import MvDef


def cli():
    defopt.run(MvDef, no_negated_flags=True, cli_options="has_default")
