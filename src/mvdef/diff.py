from dataclasses import KW_ONLY, dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile

from .agenda import Agenda
from .check import Checker


@dataclass
class Differ:
    src: Path
    _: KW_ONLY
    dst: Path | None
    mv: list[str]
    escalate: bool = False
    verbose: bool = False

    def __post_init__(self) -> None:
        self.agenda = Agenda()

    @property
    def is_src(self) -> bool:
        return self.dst is None

    def populate_agenda(self) -> None:
        if self.is_src:
            self.agenda.remove(self.mv, src=self.src)
        else:
            self.agenda.bring(self.mv, src=self.src, dst=self.dst)

    def unidiff(self) -> str:
        if self.agenda.empty:
            self.populate_agenda()
        return self.agenda.unidiff(target_file=self.target_file, old=self.old_target())

    @property
    def target_file(self) -> Path:
        return self.src if self.is_src else self.dst

    def old_target(self) -> str:
        must_read = self.is_src or self.target_file.exists()
        old = self.target_file.read_text() if must_read else ""
        return old

    def execute(self) -> None:
        """
        See autoflake8, which uses rename (replace) with NamedTemporaryFile:
        https://github.com/fsouza/autoflake8/blob/main/autoflake8/fix.py#L668

        Also autoflake, which doesn't:
        https://github.com/PyCQA/autoflake/blob/main/autoflake.py#L970
        """
        after = self.agenda.simulate(input_text=self.old_target())
        with NamedTemporaryFile(delete=False, dir=self.target_file.parent) as output:
            tmp_path = Path(output.name)
            tmp_path.write_text(after)
        tmp_path.rename(self.target_file)
