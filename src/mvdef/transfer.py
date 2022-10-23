from dataclasses import dataclass
from pathlib import Path

from .log_utils import set_up_logging
from .parse import parse_file


@dataclass
class MvDef:
    """
    Move function definitions from one file to another, moving/copying
    associated import statements along with them.

    - src: source file to take definitions from
    - dst: destination file (may not exist)
    - mv: names to move from the source file (default: [])
    - backup: whether to create a backup with the suffix `.bak` (default: False)
    - dry_run: whether to only preview the changes (default: False)
    - escalate: whether to raise an error upon failure (default: False)
    - verbose: whether to log anything (default: False)
    """

    src: Path
    dst: Path
    mv: list[str]
    backup: bool = False
    dry_run: bool = False
    escalate: bool = False
    verbose: bool = False

    def log(self, msg):
        self.logger.info(msg)

    def __post_init__(self):
        self.logger = set_up_logging(__name__, verbose=self.verbose)
        self.log(self)

    def check(self) -> None:
        self.src_checker = parse_file(
            self.src, verbose=self.verbose, escalate=self.escalate, ensure_exists=True
        )
        if absent := (set(self.mv) - {f.name for f in self.src_checker.funcdefs}):
            msg = f"Definition{'s'[:len(absent)-1]} not in {self.src}: {absent}"
            self.src_checker.fail(msg)
            # implicit return
        elif self.dst.exists():
            self.dst_checker = parse_file(self.dst, verbose=self.verbose)
