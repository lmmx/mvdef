from pathlib import Path

from mvdef.cli import cli

__all__ = ["get_mvdef_diffs"]


def get_mvdef_diffs(a: Path, b: Path, **mvdef_cli_args) -> tuple[str, str]:
    kwargs_with_defaults = {"dry_run": True, "escalate": True, **mvdef_cli_args}
    a_diff, b_diff = cli(a, b, return_diffs=True, **kwargs_with_defaults)
    return a_diff, b_diff
