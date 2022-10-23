from dataclasses import KW_ONLY, dataclass
from pathlib import Path


@dataclass
class Differ:
    src: Path
    _: KW_ONLY
    dst: Path | None
    mv: list[str]
    escalate: bool = False
    verbose: bool = False

    def unidiff(self) -> str:
        return ""
