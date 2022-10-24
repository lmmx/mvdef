from dataclasses import dataclass
from pathlib import Path

from .diff import Differ
from .exceptions import CheckFailure
from .log_utils import set_up_logging
from .parse import parse_file


@dataclass
class MvDef:
    """
      Move function definitions from one file to another, moving/copying
      associated import statements along with them.

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

    def log(self, msg):
        self.logger.info(msg)

    def __post_init__(self):
        self.logger = set_up_logging(__name__, verbose=self.verbose)
        self.log(self)
        diff_kwargs = {k: getattr(self, k) for k in ["mv", "escalate", "verbose"]}
        self.src_diff = Differ(self.src, dst=None, **diff_kwargs)
        self.dst_diff = Differ(self.src, dst=self.dst, **diff_kwargs)

    def check(self) -> CheckFailure | None:
        kwargs = {
            k: getattr(self, k) for k in "escalate verbose cls_defs all_defs".split()
        }
        self.src_check = parse_file(self.src, ensure_exists=True, **kwargs)
        if absent := (set(self.mv) - {f.name for f in self.src_check.target_defs}):
            msg = f"Definition{'s'[:len(absent)-1]} not in {self.src}: {absent}"
            return self.src_check.fail(msg)
        elif self.dst.exists():
            self.dst_check = parse_file(self.dst, **kwargs)
            if False:
                return self.src_check.fail(msg)
        return None

    def diffs(self) -> tuple[str, str]:
        self.src_diff.scan(self.src_check)
        self.dst_diff.scan(self.src_check, dst_check=self.dst_check)
        # Once scanned, the edit agenda can be built, but it is not until
        # the `Differ.unidiff()` method is called
        self.src_diff.populate_agenda()
        self.dst_diff.populate_agenda()
        src_unidiff = self.src_diff.unidiff()
        dst_unidiff = self.dst_diff.unidiff()
        return src_unidiff, dst_unidiff

    def move(self) -> str | None:
        if self.dry_run:
            return None
        return self.execute_diffs()

    def execute_diffs(self) -> None:
        print("Executing...")
        return
