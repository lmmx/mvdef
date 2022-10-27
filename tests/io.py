from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

__all__ = ["Write"]


@dataclass
class Write:
    names: tuple[str, ...]
    contents: tuple[str, ...]
    path: Path
    len_check: bool = True

    @property
    def file_paths(self) -> tuple[Path, ...]:
        return tuple(self.path / name for name in self.names)

    def __post_init__(self) -> None:
        for file, content in zip(self.file_paths, self.contents):
            file.write_text(content)
            assert file.read_text() == content
        files_in_dir = list(self.path.iterdir())
        if self.len_check:
            assert len(files_in_dir) == len(self.names)
        return

    @classmethod
    def from_enums(
        cls,
        *enums: tuple[Enum, ...],
        path: Path,
        len_check: bool = len_check,
        suffix: str = ".py",
    ) -> Write:
        names = tuple(f"{e.name}{suffix}" for e in enums)
        contents = tuple(e.value for e in enums)
        return cls(names=names, contents=contents, path=path, len_check=len_check)
