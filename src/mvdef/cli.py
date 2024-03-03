"""Command line interface components."""
from dataclasses import KW_ONLY, dataclass
from typing import NamedTuple

import defopt

from .transfer import CpDef, LsDef, MvDef


@dataclass
class CLIResult:
    """The result of a CLI call."""

    mover: MvDef | CpDef | None
    _: KW_ONLY
    diffs: tuple[str, str] | None = None  # MvDef | CpDef
    manif: str | None = None  # LsDef


class DefoptFlags(NamedTuple):
    """The flags to pass to defopt (as kwargs)."""

    no_negated_flags: bool = True
    cli_options: str = "has_default"
    show_defaults: bool = False


def cli(*args, **kwargs) -> CLIResult | None:
    """A wrapper used for all CLIs."""
    MvCls = kwargs.pop("MvCls")
    ls = MvCls is LsDef
    return_state = kwargs.pop("return_state", False)
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
        mover = MvCls(*args, **kwargs)
    if unblocked := (mover.check_blocker is None):
        if ls:
            manif = mover.manif(print_out=True)
        else:
            if mover.dry_run:
                diffs = mover.diffs(print_out=True)
            else:
                mover.move()
    if return_state:
        result = CLIResult(mover)
        if unblocked:
            if ls:
                result.manif = manif
            elif mover.dry_run:
                result.diffs = diffs
    return result if return_state else None


def cli_move(*args, **kwargs) -> CLIResult | None:
    """Move symbols."""
    return cli(MvCls=MvDef, *args, **kwargs)


def cli_copy(*args, **kwargs) -> CLIResult | None:
    """Copy symbols."""
    return cli(MvCls=CpDef, *args, **kwargs)


def cli_list(*args, **kwargs) -> CLIResult | None:
    """List symbols."""
    return cli(MvCls=LsDef, *args, **kwargs)
