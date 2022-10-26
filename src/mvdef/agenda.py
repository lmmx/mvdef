from dataclasses import dataclass, field
from difflib import unified_diff
from pathlib import Path

from .check import Checker
from .exceptions import AgendaFailure
from .log_utils import set_up_logging

logger = set_up_logging(name=__name__)


@dataclass
class Agendum:
    name: str
    file: Path


@dataclass
class SourcedAgendum(Agendum):
    via: Path


@dataclass
class Patch:
    rng: tuple[int, int]


@dataclass
class Editor:
    lines: str
    edits: dict[str, Patch]


class Cutter(Editor):
    def __str__(self) -> str:
        return self.lines  # Not implemented yet


@dataclass
class Paster(Editor):
    ref: Checker

    def __str__(self) -> str:
        hem = []
        ref_lines = self.ref.code.splitlines(keepends=True)
        for name, edit in self.edits.items():
            lineno, end_lineno = edit.rng
            addendum = "".join(ref_lines[lineno - 1 : end_lineno])
            logger.debug(f"Pasted {addendum}")
            hem.append(addendum)
        def_sep = "\n\n\n"
        result = def_sep.join([""] + hem)
        return result


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


class Agenda:
    targets: list[str]
    targeted: OrderOfBusiness

    def __init__(self, ref: Checker, dest_ref: Checker | None) -> None:
        self.ref = ref
        self.dest_ref = dest_ref
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

    def apply(self, input_text: str) -> str:
        copped = {}
        chopped = {}
        for target in self.targeted.cop:
            maybe_targets = [f for f in self.ref.target_defs if f.name == target.name]
            if len(maybe_targets) > 1:
                raise NotImplementedError("Not handled name ambiguity yet")
            else:
                node = maybe_targets.pop()
                copped.update({target.name: Patch(rng=(node.lineno, node.end_lineno))})
        cut = Cutter(input_text, chopped)
        paste = Paster(input_text, copped, ref=self.ref)
        sewn = str(cut) + str(paste)
        return sewn

    def simulate(self, input_text: str) -> str:
        filtered = self.apply(input_text)
        return filtered

    def unidiff(self, target_file: Path, is_src: bool) -> str:
        """
        Unified diff from applying the `targeted` agenda to the target file. If the
        file does not exist yet, pass in an empty string for `old` to avoid reading it.
        """
        old = self.ref.code if is_src else self.dest_ref.code
        print(f"Sim. {is_src=}")
        new = self.simulate(input_text=old)
        diff = self.targeted.get_unidiff_text(
            a=old.splitlines(keepends=True),
            b=new.splitlines(keepends=True),
            filename=target_file.name,
        )
        return diff
