from dataclasses import dataclass
from typing import NamedTuple

import defopt

from .transfer import MvDef


@dataclass
class CLIResult:
    mover: MvDef | None
    diffs: tuple[str, str] | None = None


class DefoptFlags(NamedTuple):
    no_negated_flags: bool = True
    cli_options: str = "has_default"
    show_defaults: bool = False


def cli(*args, **kwargs) -> CLIResult | None:
    return_state = kwargs.pop("return_state", False)
    defopt_argv: list[str] | None = kwargs.pop("defopt_argv", None)
    force_defopt = defopt_argv is not None
    invoke_defopt = not (args or kwargs) or force_defopt
    if invoke_defopt:
        defopt_kwargs = DefoptFlags()._asdict()
        if force_defopt:
            defopt_kwargs["argv"] = defopt_argv
        mover = defopt.run(MvDef, **defopt_kwargs)
    else:
        mover = MvDef(*args, **kwargs)
    if unblocked := (mover.check_blocker is None):
        if mover.dry_run:
            diffs = mover.diffs(print_out=True)
        else:
            mover.move()
    if return_state:
        if unblocked and mover.dry_run:
            result = CLIResult(mover, diffs)
        else:
            result = CLIResult(mover)
    return result if return_state else None
