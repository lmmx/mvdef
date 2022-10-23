from dataclasses import dataclass
from pathlib import Path


@dataclass
class MvDef:
    """
    Move function definitions from one file to another, moving/copying
    associated import statements along with them.
    """

    src: Path
    dst: Path
    mv: list[str]
    backup: bool = False
    dry_run: bool = False

    def __post_init__(self) -> None:
        print("Hello world")
