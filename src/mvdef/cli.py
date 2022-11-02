from dataclasses import dataclass
from typing import NamedTuple

import defopt

from .transfer import CpDef, MvDef


@dataclass
class CLIResult:
    mover: MvDef | CpDef | None
    diffs: tuple[str, str] | None = None


class DefoptFlags(NamedTuple):
    no_negated_flags: bool = True
    cli_options: str = "has_default"
    show_defaults: bool = False


def cli(*args, **kwargs) -> CLIResult | None:
    return_state = kwargs.pop("return_state", False)
    MvCls = kwargs.pop("MvCls", MvDef)
    defopt_argv: list[str] | None = kwargs.pop("defopt_argv", None)
    force_defopt = defopt_argv is not None
    # Use defopt if no kw/args (i.e. using argv) or if testing the CLI (mimicking argv)
    invoke_defopt = not (args or kwargs) or force_defopt
    if invoke_defopt:
        defopt_kwargs = DefoptFlags()._asdict()
        if force_defopt:
            defopt_kwargs["argv"] = defopt_argv
        mover = defopt.run(MvCls, **defopt_kwargs)
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


def cli_move(*args, **kwargs) -> CLIResult | None:
    return cli(MvCls=MvDef, *args, **kwargs)


def cli_copy(*args, **kwargs) -> CLIResult | None:
    return cli(MvCls=CpDef, *args, **kwargs)
