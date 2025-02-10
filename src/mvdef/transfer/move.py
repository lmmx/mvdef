from dataclasses import dataclass
from pathlib import Path

from ..core.diff import Differ
from ..core.parse import parse, parse_file
from ..error_handling.exceptions import CheckFailure
from .base import MvDefBase

__all__ = ["MvDef"]


@dataclass
class MvDef(MvDefBase):
    """
    Move function definitions from one file to another, moving/copying
    any necessary associated import statements along with them.

    Option     Description                                Type        Default
    —————————— —————————————————————————————————————————— ——————————— ———————
    • src        source file to take definitions from       Path        -
    • dst        destination file (may not exist)           Path        -
    • mv         names to move from the source file         list[str]   -
    • dry_run    whether to only preview the change diffs   bool        False
    • escalate   whether to raise an error upon failure     bool        False
    • cls_defs   whether to use only class definitions      bool        False
    • func_defs  whether to use only function definitions   bool        False
    • verbose    whether to log anything                    bool        False
    """

    src: Path
    dst: Path
    mv: list[str]
    dry_run: bool = False
    escalate: bool = False
    cls_defs: bool = False
    func_defs: bool = False
    verbose: bool = False
    _copy_mode: bool = False

    diff_kw = ["mv"]

    @property
    def dst_diff_kwargs(self) -> dict:
        return {**self.src_diff_kwargs, "dst": self.dst, "dest_ref": self.dst_check}

    def __post_init__(self):
        super().__post_init__()
        self.src_diff = Differ(self.src, **self.src_diff_kwargs)
        self.dst_diff = Differ(self.src, **self.dst_diff_kwargs)

    def check(self) -> CheckFailure | None:
        kwargs = {
            k: getattr(self, k) for k in "escalate verbose cls_defs func_defs".split()
        }
        try:
            self.src_check = parse_file(self.src, ensure_exists=True, **kwargs)
        except Exception as exc:
            self.src_check = None
            return self.fail("Failed to parse the src file", exc_info=exc)
        else:
            if self.src_check is None:
                self.dst_check = None
                return self.fail("Failed to parse the src file")
        if absent := (set(self.mv) - {f.name for f in self.src_check.target_defs}):
            msg = f"Definition{'s'[: len(absent) - 1]} not in {self.src}: {absent}"
            self.dst_check = None
            return self.src_check.fail(msg)
        elif self.dst.exists():
            try:
                self.dst_check = parse_file(self.dst, **kwargs)
            except Exception as exc:
                self.dst_check = None
                return self.fail("Failed to parse the dst file", exc_info=exc)
            else:
                if self.dst_check is None:
                    return self.fail("Failed to parse the dst file")
        else:
            try:
                self.dst_check = parse("", file=self.dst, **kwargs)
            except Exception as exc:
                self.dst_check = None
                return self.fail(
                    "Failed to parse the dst file (which was mocked)",
                    exc_info=exc,
                )
        return None

    def diffs(self, print_out: bool = False) -> tuple[str, str]:
        """
        Calls `Agenda.populate_agenda()` implicitly by `Agenda.unidiff()` and returns 2
        diff strings for src and dst respectively. If only copying (not editing src),
        just populates the agenda and returns a single diff string.
        """
        if self._copy_mode and self.src_diff.agenda.empty:
            # Must populate the Agenda to set up associated Checker ("ref")... I think?
            self.src_diff.populate_agenda()
            src_unidiff = ""
        else:
            src_unidiff = self.src_diff.unidiff()
        dst_unidiff = self.dst_diff.unidiff()
        if print_out:
            for diff in filter(None, [src_unidiff, dst_unidiff]):
                print(diff)
        return dst_unidiff if self._copy_mode else src_unidiff, dst_unidiff

    def move(self) -> None:
        """Execute diffs"""
        if not self.dry_run:
            if not self._copy_mode:
                self.src_diff.execute()
            self.dst_diff.execute()
        return
