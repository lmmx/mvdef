from dataclasses import dataclass
from pathlib import Path

from .differ import Differ
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
    • verbose    whether to log anything                    bool (False)
    """

    src: Path
    dst: Path
    mv: list[str]
    dry_run: bool = False
    escalate: bool = False
    verbose: bool = False

    def log(self, msg):
        self.logger.info(msg)

    def __post_init__(self):
        self.logger = set_up_logging(__name__, verbose=self.verbose)
        self.log(self)
        differ_kwargs = {k: getattr(self, k) for k in ["mv", "escalate", "verbose"]}
        self.src_differ = Differ(self.src, dst=None, **differ_kwargs)
        self.dst_differ = Differ(self.src, dst=self.dst, **differ_kwargs)

    def check(self) -> CheckFailure | None:
        self.src_checker = parse_file(
            self.src, verbose=self.verbose, escalate=self.escalate, ensure_exists=True
        )
        if absent := (set(self.mv) - {f.name for f in self.src_checker.funcdefs}):
            msg = f"Definition{'s'[:len(absent)-1]} not in {self.src}: {absent}"
            return self.src_checker.fail(msg)
        elif self.dst.exists():
            self.dst_checker = parse_file(self.dst, verbose=self.verbose)
            if False:
                return self.src_checker.fail(msg)
        return None

    def diffs(self) -> tuple[str, str]:
        return self.src_differ.unidiff(), self.dst_differ.unidiff()

    def move(self) -> str | None:
        if self.dry_run:
            return None
        return self.execute_diffs()

    def execute_diffs(self) -> None:
        print("Executing...")
        return
