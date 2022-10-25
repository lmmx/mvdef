from dataclasses import dataclass, field
from difflib import unified_diff
from pathlib import Path

from .exceptions import AgendaFailure
from .parse import parse_file


@dataclass
class Agendum:
    name: str
    file: Path


@dataclass
class SourcedAgendum(Agendum):
    via: Path


@dataclass
class OrderOfBusiness:
    """What to cop vs. what to chop (move/copy vs. delete)"""

    cop: list[SourcedAgendum] = field(default_factory=list)
    chop: list[Agendum] = field(default_factory=list)

    def get_unidiff_text(self, a: list[str], b: list[str], filename: str) -> str:
        from_file, to_file = f"original/{filename}", f"fixed/{filename}"
        diff = unified_diff(a=a, b=b, fromfile=from_file, tofile=to_file)
        text = ""
        for line in diff:
            text += line
            # Work around missing newline (http://bugs.python.org/issue2142).
            if not line.endswith("\n"):
                text += "\n" + r"\ No newline at end of file" + "\n"
        return text

    def apply(self, input_text: str) -> str:
        return input_text + "foo\n"


class Agenda:
    targets: list[str]
    targeted: OrderOfBusiness

    def __init__(self) -> None:
        self.targets = []
        self.targeted = OrderOfBusiness()

    @property
    def empty(self) -> bool:
        return len(self.targets) == 0

    def no_clash(self, mv: list[str]) -> None:
        if clash := set(mv).intersection(self.targets):
            raise AgendaFailure(f"{clash=} - target{'s'[:len(clash)-1]} double booked")

    def intake(self, mv: list[str]) -> None:
        """Prepare to cop or chop (ensure no double bookings!)"""
        self.no_clash(mv)
        self.targets.extend(mv)

    def cop(self, agenda: list[SourcedAgendum]) -> None:
        self.intake([a.name for a in agenda])
        self.targeted.cop.extend(agenda)

    def chop(self, agenda: list[Agendum]) -> None:
        self.intake([a.name for a in agenda])
        self.targeted.chop.extend(agenda)

    def bring(self, mv: list[str], *, src: Path, dst: Path) -> None:
        self.cop([SourcedAgendum(name=target, file=dst, via=src) for target in mv])

    def remove(self, mv, *, src: Path) -> None:
        self.chop([Agendum(name=target, file=src) for target in mv])

    def simulate(self, input_text: str) -> str:
        filtered = self.targeted.apply(input_text)
        return filtered

    def unidiff(self, target_file: Path, old: str) -> str:
        """
        Unified diff from applying the `targeted` agenda to the target file. If the
        file does not exist yet, pass in an empty string for `old` to avoid reading it.
        """
        new = self.simulate(input_text=old)
        diff = self.targeted.get_unidiff_text(
            a=old.splitlines(keepends=True),
            b=new.splitlines(keepends=True),
            filename=target_file.name,
        )
        return diff
