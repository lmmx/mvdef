from dataclasses import KW_ONLY, dataclass
from pathlib import Path

from ..agenda import Agenda
from ..check import Checker

__all__ = ["Manifest"]


@dataclass
class Manifest:
    src: Path
    _: KW_ONLY
    matchers: list[str]
    source_ref: Checker
    dry_run: bool
    list: bool
    escalate: bool = False
    verbose: bool = False

    def __post_init__(self) -> None:
        self.agenda = Agenda(ref=self.source_ref, dest_ref=None)

    def populate_agenda(self) -> None:
        """
        Puts `matchers` (default `['*']`) on `Agenda.targeted.doc`
        without regex expansion.
        """
        self.agenda.document(self.matchers, src=self.src)

    def fill(self) -> str:
        if self.agenda.empty:
            self.populate_agenda()
        return self.agenda.manifest(dry_run=self.dry_run, as_list=self.list)
