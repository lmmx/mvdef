import sys
from pathlib import Path

from mvdef.cli import MvDef, cli

__all__ = ["run_mvdef", "dry_run_mvdef", "get_mvdef_diffs", "mvdef_from_argv"]


def run_mvdef(a: Path, b: Path, **mvdef_cli_args) -> MvDef:
    kwargs_with_defaults = {"dry_run": False, "escalate": True, **mvdef_cli_args}
    run_result = cli(a, b, return_state=True, **kwargs_with_defaults)
    return run_result


def dry_run_mvdef(a: Path, b: Path, **mvdef_cli_args) -> MvDef:
    kwargs_with_defaults = {"dry_run": True, "escalate": True, **mvdef_cli_args}
    run_result = cli(a, b, return_state=True, **kwargs_with_defaults)
    return run_result


def get_mvdef_diffs(a: Path, b: Path, **mvdef_cli_args) -> tuple[str, str]:
    run_result = dry_run_mvdef(a=a, b=b, **mvdef_cli_args)
    a_diff, b_diff = run_result.diffs
    return a_diff, b_diff


def mvdef_from_argv(argv) -> None:
    sys_argv = sys.argv
    argv_0_pre = sys_argv[0]
    sys_argv[0] = "mvdef"  # Mock the entrypoint (otherwise first argv is pytest)
    cli(defopt_argv=argv)
    sys_argv[0] = argv_0_pre  # Put it back how you found it
