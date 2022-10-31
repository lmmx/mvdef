from __future__ import annotations

from ast import AST
from dataclasses import dataclass, field
from pathlib import Path

from pyflakes import checker

from .check import Checker
from .exceptions import AgendaFailure
from .log_utils import set_up_logging
from .parse import reparse
from .text_diff import get_unidiff_text
from .whitespace import normalise_whitespace

logger = set_up_logging(name=__name__)


@dataclass
class DepartingImport:
    bound: checker.Importation
    lineno: int
    end_lineno: int

    @property
    def rng(self) -> tuple[int, int]:
        return (self.lineno, self.end_lineno)

    @property
    def name(self) -> str:
        return self.bound.fullName


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


@dataclass(kw_only=True)
class NamedPatch(Patch):
    name: str


class Departure(NamedPatch):
    """A definition or importation leaving."""


class Arrival(NamedPatch):
    """A definition or importation arriving."""


@dataclass
class Editor:
    lines: str
    edits: list[Departure | Arrival]


@dataclass
class Cutter(Editor):
    spacing: int

    def __str__(self) -> str:
        lines = self.lines.splitlines(keepends=True)
        for departure in self.edits:
            lineno, end_lineno = departure.rng
            # NB AST line numbers are 1-based, list index is 0-based
            # Replace strings with None to indicate removal without altering index
            lines[lineno - 1 : end_lineno] = [None for _ in range(end_lineno - lineno)]
            logger.debug(f"Snipped {departure.rng}")
        normalised = normalise_whitespace(lines, spacing=self.spacing)
        return normalised


@dataclass
class Paster(Editor):
    ref: Checker
    spacing: int

    def __str__(self) -> str:
        hem = []
        ref_lines = self.ref.code.splitlines(keepends=True)
        for arrival in self.edits:
            lineno, end_lineno = arrival.rng
            # NB AST line numbers are 1-based, list index is 0-based
            addendum = "".join(ref_lines[lineno - 1 : end_lineno])
            logger.debug(f"Pasted {addendum}")
            hem.append(addendum)
        result = ("\n" * self.spacing).join(hem)
        return result


@dataclass
class OrderOfBusiness:
    """What to cop vs. what to chop (move/copy vs. delete)"""

    cop: list[SourcedAgendum] = field(default_factory=list)
    chop: list[Agendum] = field(default_factory=list)


class Agenda:
    targets: list[str]
    targeted: OrderOfBusiness
    spacing: int = 2  # Leave 2 lines between defs

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

    def get_def_node(self, target_name: str) -> AST:
        maybe_targets = [f for f in self.ref.target_defs if f.name == target_name]
        if len(maybe_targets) > 1:
            raise NotImplementedError("Not handled name ambiguity yet")
        else:
            node = maybe_targets.pop()
            return node

    def def_rng(self, target_name: str) -> tuple[int, int]:
        """
        Get the line range of a definition with the target name.
        """
        node = self.get_def_node(target_name=target_name)
        decos = node.decorator_list
        # Use the lineno of the first decorator, or of the node if it's undecorated
        start_lineno = (decos[0] if decos else node).lineno
        line_range = (start_lineno, node.end_lineno)
        return line_range

    def apply(self, input_text: str, imports: list[DepartingImport]) -> str:
        if imports:
            resting_imports = [
                imp
                for departure in imports
                for imp in self.original_ref.imports
                if imp.source.lineno == departure.lineno
                if imp is not departure.bound
            ]
            if resting_imports:
                raise NotImplementedError("Imports staying and going on same line")
        # Avoiding using a dict to permit import and defname overlap, but do need to
        # preserve unique names for each node type, so use these generator/listcomps:
        uniq_cops = [
            next(c for c in self.targeted.cop if c.name == n)
            for n in {c.name for c in self.targeted.cop}
        ]
        uniq_chops = [
            next(c for c in self.targeted.chop if c.name == n)
            for n in {c.name for c in self.targeted.chop}
        ]
        copped = [Arrival(name=n.name, rng=self.def_rng(n.name)) for n in uniq_cops]
        chopped = [Departure(name=n.name, rng=self.def_rng(n.name)) for n in uniq_chops]
        # Prune unused imports if passed"
        chopped.extend([Departure(name=imp.name, rng=imp.rng) for imp in imports])
        cut = Cutter(input_text, chopped, spacing=self.spacing)
        paste = Paster(input_text, copped, ref=self.ref, spacing=self.spacing)
        ends = [str(cut).rstrip("\n"), str(paste).rstrip("\n")]
        # Increment spacing by 1 to account for the stripped line ending
        inter_def_sep = "\n" * (self.spacing + 1)
        sewn = inter_def_sep.join(filter(None, ends)) + "\n"
        return sewn

    @property
    def is_src(self) -> bool:
        return self.dest_ref is None

    @property
    def original_ref(self) -> Checker:
        return self.ref if self.is_src else self.dest_ref

    def pre_simulate(self, input_text: str) -> str:
        """
        First pass, with no change to import statements.
        """
        filtered = self.apply(input_text, imports=[])
        return filtered

    def resimulate(self, input_text: str, imports: list[DepartingImport]) -> str:
        """
        Second pass if necessary to remove import statements that would not be used
        after moving the `mv` definition(s) out of the file.
        """
        filtered = self.apply(input_text, imports=imports)
        return filtered

    def recheck(self, input_text: str) -> Checker:
        """
        First pass, with no change to import statements.
        """
        return reparse(check=self.original_ref, input_text=input_text)

    def simulate(self, input_text: str) -> str:
        pre_sim = self.pre_simulate(input_text=input_text)
        if self.original_ref is None:
            return pre_sim
        recheck = self.recheck(pre_sim)
        unused_imports = self.compare_imports(recheck)
        if unused_imports:
            return self.resimulate(input_text, imports=unused_imports)
        else:
            return pre_sim

    def compare_imports(self, recheck: Checker) -> list[DepartingImport]:
        pre_uu_imports = self.original_ref.unused_imports()
        rec_uu_imports = recheck.unused_imports()
        if rec_uu_imports == pre_uu_imports:
            return []
        old_uu_names = [i.message_args[0] for i in pre_uu_imports]
        rec_uu_names = [i.message_args[0] for i in rec_uu_imports]
        lose_nameset = set(rec_uu_names).difference(old_uu_names)
        lose_uu_names = [n for n in rec_uu_names if n in lose_nameset]
        # lose_uu_imports = [
        #     i for i in rec_uu_imports if i.message_args[0] in lose_nameset
        # ]
        original_imports = self.original_ref.imports
        # original_import_names = [
        #     importation.fullName for importation in original_imports
        # ]
        if not lose_uu_names:
            return []
        # Full name is either the asname, the dotted qualpath, or just a name
        # and matches the message arg (expected/tested assumption)
        newly_unused_imports = [
            DepartingImport(
                imp, lineno=imp.source.lineno, end_lineno=imp.source.end_lineno
            )
            for imp in original_imports
            if imp.fullName in lose_uu_names
        ]
        assert len(lose_uu_names) == len(newly_unused_imports)
        logger.debug("Found unused imports: {newly_unused_imports}")
        return newly_unused_imports

    def unidiff(self, target_file: Path, is_src: bool) -> str:
        """
        Unified diff from applying the `targeted` agenda to the target file. If the
        file does not exist yet, pass in an empty string for `old` to avoid reading it.
        """
        old = self.ref.code if is_src else self.dest_ref.code
        new = self.simulate(input_text=old)
        diff = get_unidiff_text(
            a=old.splitlines(keepends=True),
            b=new.splitlines(keepends=True),
            filename=target_file.name,
        )
        return diff
