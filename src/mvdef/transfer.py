from dataclasses import dataclass
from pathlib import Path

from .diff import Differ
from .exceptions import CheckFailure
from .failure import FailableMixIn
from .log_utils import set_up_logging
from .parse import parse, parse_file

__all__ = ["MvDef", "CpDef"]


@dataclass
class MvDef(FailableMixIn):
    """
      Move function definitions from one file to another, moving/copying
      any necessary associated import statements along with them.

      Option     Description                                Type (default)
      —————————— —————————————————————————————————————————— ——————————————
    • src        source file to take definitions from       Path
    • dst        destination file (may not exist)           Path
    • mv         names to move from the source file         list of str
    • dry_run    whether to only preview the change diffs   bool (False)
    • escalate   whether to raise an error upon failure     bool (False)
    • cls_defs   whether to target only class definitions   bool (False)
    • all_defs   whether to target both class and funcdefs  bool (False)
    • verbose    whether to log anything                    bool (False)
    """

    src: Path
    dst: Path
    mv: list[str]
    dry_run: bool = False
    escalate: bool = False
    cls_defs: bool = False
    all_defs: bool = False
    verbose: bool = False
    _copy_mode: bool = False

    def log(self, msg):
        self.logger.info(msg)

    def __post_init__(self):
        self.logger = set_up_logging(__name__, verbose=self.verbose)
        self.log(self)
        self.check_blocker = self.check()
        diff_kwargs = {k: getattr(self, k) for k in ["mv", "escalate", "verbose"]}
        if self.check_blocker:
            # check() can exit before setting a Checker as attribute (ugly: please fix)
            # (Possibly) this amounts to a try/else block around the `check()` call?
            if not hasattr(self, "src_check"):
                setattr(self, "src_check", None)
            if not hasattr(self, "dst_check"):
                setattr(self, "dst_check", None)
        diff_kwargs["source_ref"] = self.src_check
        self.src_diff = Differ(self.src, **diff_kwargs)
        diff_kwargs["dst"] = self.dst
        diff_kwargs["dest_ref"] = self.dst_check
        self.dst_diff = Differ(self.src, **diff_kwargs)

    def check(self) -> CheckFailure | None:
        kwargs = {
            k: getattr(self, k) for k in "escalate verbose cls_defs all_defs".split()
        }
        src_check = parse_file(self.src, ensure_exists=True, **kwargs)
        if src_check is None:
            return self.fail("Failed to parse the src file")
        self.src_check = src_check
        if absent := (set(self.mv) - {f.name for f in self.src_check.target_defs}):
            msg = f"Definition{'s'[:len(absent)-1]} not in {self.src}: {absent}"
            return self.src_check.fail(msg)
        elif self.dst.exists():
            dst_check = parse_file(self.dst, **kwargs)
            if dst_check is None:
                return self.fail("Failed to parse the dst file")
            self.dst_check = dst_check
        else:
            self.dst_check = parse("", file=self.dst, **kwargs)
        return None

    def diffs(self, print_out: bool = False) -> tuple[str, str] | str:
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


@dataclass
class CpDef(MvDef):
    """
      Copy function definitions from one file to another, and any necessary
      associated import statements along with them.

      Option     Description                                Type (default)
      —————————— —————————————————————————————————————————— ——————————————
    • src        source file to copy definitions from       Path
    • dst        destination file (may not exist)           Path
    • mv         names to copy from the source file         list of str
    • dry_run    whether to only preview the change diffs   bool (False)
    • escalate   whether to raise an error upon failure     bool (False)
    • cls_defs   whether to target only class definitions   bool (False)
    • all_defs   whether to target both class and funcdefs  bool (False)
    • verbose    whether to log anything                    bool (False)
    """

    _copy_mode: bool = True
