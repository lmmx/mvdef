import sys
from pathlib import Path
from typing import Union

from mvdef.cli import CLIResult, cli
from mvdef.transfer import CpDef, LsDef, MvDef

__all__ = [
    "mvcls",
    "run_cmd",
    "dry_run_cmd",
    "get_cmd_diffs",
    "get_manif",
    "cmd_from_argv",
]

MvClsT = Union[MvDef, CpDef, LsDef]


def mvcls(cp: bool, ls: bool) -> MvClsT:
    return LsDef if ls else (CpDef if cp else MvDef)


def run_cmd(
    a: Path, b: Path | None, *, cp_: bool = False, ls_: bool = False, **cli_args
) -> MvClsT:
    kwargs = {"return_state": True, "escalate": True, "dry_run": False, **cli_args}
    if b is None:
        assert ls_, "2nd path is needed unless using lsdef"
    run_result = cli(a, *([] if ls_ else [b]), MvCls=mvcls(cp=cp_, ls=ls_), **kwargs)
    return run_result


def dry_run_cmd(
    a: Path, b: Path | None, *, cp_: bool = False, ls_: bool = False, **cli_args
) -> CLIResult:
    return run_cmd(a, b, cp_=cp_, ls_=ls_, **{"dry_run": True, **cli_args})


def get_cmd_diffs(
    a: Path, b: Path, cp_: bool = False, **cmd_cli_args
) -> tuple[str, str] | str:
    run_result = dry_run_cmd(a=a, b=b, **cmd_cli_args)
    return run_result.diffs


def get_manif(a: Path, **cmd_cli_args) -> str:
    run_result = dry_run_cmd(a=a, b=None, ls_=True, **cmd_cli_args)
    return run_result.manif


def cmd_from_argv(argv, cp_: bool = False, ls_: bool = False) -> None:
    """Mock the entrypoint (otherwise first (i.e. 0'th) argv is pytest)."""
    argv_0 = sys.argv[0]
    sys.argv[0] = (MvCls := mvcls(cp=cp_, ls=ls_)).__name__.lower()
    cli(MvCls=MvCls, defopt_argv=argv)
    sys.argv[0] = argv_0  # Put it back how you found it
