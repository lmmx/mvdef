from dataclasses import KW_ONLY, dataclass
from pathlib import Path

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
        self.agenda = Agenda(targets=self.mv)

    @property
    def is_src(self) -> bool:
        return self.dst is None

    def scan(self, src_checker: Checker, *, dst_checker: Checker | None = None) -> None:
        """
        Build the Agenda for a given source/destination file. Unless the agenda is for
        a destination file that doesn't exist yet, use the AST built when checking it.
        """
        targeted = []
        for target in self.agenda.targets:
            # TODO: restart here (comes from transfer:MvDef.diffs -> agenda:Agenda)
            possible_targets = [
                f for f in src_checker.target_defs if f.name in self.agenda.targets
            ]
            if len(possible_targets) > 1:
                raise NotImplementedError("Not handled name ambiguity yet")
            else:
                targeted_node = possible_targets.pop()
            self.agenda.targeted.update({target: targeted_node})

    def unidiff(self) -> str:
        if self.agenda.empty:
            if self.is_src:
                self.agenda.remove(self.mv, src=self.src)
            else:
                self.agenda.bring(self.mv, src=self.src)
        return self.agenda.diff()
