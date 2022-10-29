from pathlib import Path

from mvdef.cli import MvDef, cli

__all__ = ["get_mvdef_run", "get_mvdef_dry_run", "get_mvdef_diffs"]


def get_mvdef_run(a: Path, b: Path, **mvdef_cli_args) -> MvDef:
    kwargs_with_defaults = {"dry_run": False, "escalate": True, **mvdef_cli_args}
    run_result = cli(a, b, return_state=True, **kwargs_with_defaults)
    return run_result


def get_mvdef_dry_run(a: Path, b: Path, **mvdef_cli_args) -> MvDef:
    kwargs_with_defaults = {"dry_run": True, "escalate": True, **mvdef_cli_args}
    run_result = cli(a, b, return_state=True, **kwargs_with_defaults)
    return run_result


def get_mvdef_diffs(a: Path, b: Path, **mvdef_cli_args) -> tuple[str, str]:
    run_result = get_mvdef_dry_run(a=a, b=b, **mvdef_cli_args)
    a_diff, b_diff = run_result.diffs
    return a_diff, b_diff
