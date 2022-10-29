from pathlib import Path

from mvdef.cli import MvDef, cli

__all__ = ["get_mvdef_diffs", "get_mvdef_mover"]


def get_mvdef_diffs(a: Path, b: Path, **mvdef_cli_args) -> tuple[str, str]:
    kwargs_with_defaults = {"dry_run": True, "escalate": True, **mvdef_cli_args}
    a_diff, b_diff = cli(a, b, return_state=True, **kwargs_with_defaults)
    return a_diff, b_diff


def get_mvdef_mover(a: Path, b: Path, **mvdef_cli_args) -> MvDef:
    kwargs_with_defaults = {"dry_run": False, "escalate": True, **mvdef_cli_args}
    mover = cli(a, b, return_state=True, **kwargs_with_defaults)
    return mover
