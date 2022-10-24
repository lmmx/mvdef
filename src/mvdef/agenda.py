from dataclasses import dataclass, field
from pathlib import Path

from .parse import parse_file


@dataclass
class Agenda:
    targets: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.targeted = {}

    @property
    def empty(self) -> bool:
        return len(self.targets) == 0

    def bring(self, mv, *, src: Path) -> None:
        self.targets = mv
        for target in mv:
            raise NotImplementedError("Bring call paused")

    def remove(self, mv, *, src: Path) -> None:
        self.targets = mv
        for target in mv:
            raise NotImplementedError("Remove call paused")

    def diff(self) -> str:
        return f"{self.targeted}"
