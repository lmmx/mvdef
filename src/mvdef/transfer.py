from dataclasses import dataclass
from pathlib import Path

from .exceptions import CheckFailure
from .log_utils import set_up_logging
from .parse import parse_file


@dataclass
class MvDef:
    """
    Move function definitions from one file to another, moving/copying
    associated import statements along with them.

    - src       source file to take definitions from
    - dst       destination file (may not exist)
    - mv        names to move from the source file      (default: [])
    - dry_run   whether to only preview the changes     (default: False)
    - escalate  whether to raise an error upon failure  (default: False)
    - verbose   whether to log anything                 (default: False)
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
        diff_kwargs = dict(dry_run=self.dry_run, verbose=self.verbose)
        self.src_diff = DiffBuilder(src=self.src, **diff_kwargs)
        self.dst_diff = DiffBuilder(dst=self.dst, **diff_kwargs)

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

    def move(self) -> str | None:
        self.build_diffs()
        if self.dry_run:
            return self.diff_builder.diffs
        else:
            return self.execute_diffs()

    def build_diffs(self) -> None:
        self.diff_builder = DiffBuilder()
        return

    def execute_diffs(self) -> None:
        if self.diff_builder is None:
            return self.src_checker.fail("Diff not built for execution")
        print("Executing...")
        return
