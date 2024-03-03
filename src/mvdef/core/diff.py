"""Diff two files (in a way that can be applied as a patch)."""
from dataclasses import KW_ONLY, dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

from .agenda import Agenda
from .check import Checker

__all__ = ["Differ"]


@dataclass
class Differ:
    """Dataclass storing the source (and potentially destination) of symbols.

    Importantly, the symbol names are stored as a list `mv`.
    """

    src: Path
    _: KW_ONLY
    mv: list[str]
    source_ref: Checker
    dst: Path | None = None
    dest_ref: Checker | None = None
    escalate: bool = False
    verbose: bool = False

    def __post_init__(self) -> None:
        self.agenda = Agenda(ref=self.source_ref, dest_ref=self.dest_ref)

    @property
    def is_src(self) -> bool:
        """Check if the `dst` is `None` (indicating this is a source of symbols)."""
        return self.dst is None

    def populate_agenda(self) -> None:
        """Call `Agenda.remove` or `Agenda.bring` with the `mv` list."""
        if self.is_src:
            self.agenda.remove(self.mv, src=self.src)
        else:
            self.agenda.bring(self.mv, src=self.src, dst=self.dst)

    def unidiff(self) -> str:
        """The unified diff of the agenda (if `agenda` is empty, populates it first)."""
        if self.agenda.empty:
            self.populate_agenda()
        return self.agenda.unidiff(target_file=self.target_file, is_src=self.is_src)

    @property
    def target_file(self) -> Path:
        """The `src` or `dst` depending on `is_src`."""
        return self.src if self.is_src else self.dst

    @property
    def old_code(self) -> str:
        """The source of the source or dest ref, depending on if `is_src`."""
        return self.source_ref.code if self.is_src else self.dest_ref.code

    def execute(self) -> None:
        """
        See autoflake8, which uses rename (replace) with NamedTemporaryFile:
        https://github.com/fsouza/autoflake8/blob/main/autoflake8/fix.py#L668

        Also autoflake, which doesn't:
        https://github.com/PyCQA/autoflake/blob/main/autoflake.py#L970
        """
        if self.agenda.empty:
            self.populate_agenda()
        before = self.old_code
        after = self.agenda.simulate(input_text=before)
        with NamedTemporaryFile(delete=False, dir=self.target_file.parent) as output:
            tmp_path = Path(output.name)
            tmp_path.write_text(after)
        tmp_path.rename(self.target_file)
        return
