from __future__ import annotations

from ast import AST, unparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeVar

from pyflakes import checker

from .check import Checker
from .exceptions import AgendaFailure
from .log_utils import set_up_logging
from .parse import reparse
from .text_diff import get_unidiff_text
from .whitespace import normalise_whitespace

logger = set_up_logging(name=__name__)

Importation = TypeVar("Importation", bound=checker.Importation)


@dataclass
class SourcedUse:
    """
    Represents a usage of a name which is imported, occurring in a definition `target`
    (which is an AST node in src, the file the definition is being moved from).
    """

    name: str
    imports: list[Importation]
    target: AST


@dataclass
class MovingImport:
    bound: Importation


@dataclass
class DepartingImport(MovingImport):
    """
    An import statement being removed from src, by the deletion of a line range.
    """

    lineno: int
    end_lineno: int

    @property
    def rng(self) -> tuple[int, int]:
        return (self.lineno, self.end_lineno)

    @property
    def name(self) -> str:
        return self.bound.fullName


@dataclass
class ArrivingImport(MovingImport):
    """
    An import statement being added to dst, by the 'unparsing' of its AST node.
    """

    @property
    def source(self) -> AST:
        return self.bound.source

    def unparse(self) -> str:
        return unparse(self.source)


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
class ImportSpacing:
    gap: int
    first_import_lineno: int
    future_offset: int

    @classmethod
    def split_text(self, text: str, at: int):
        lines = text.splitlines(keepends=True)
        return "".join(lines[:at]), "".join(lines[at:])


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

    def unique_name_list(self, duplicates: list) -> list[str]:
        """
        Preserve unique names for each node type, in order of first appearance.
        """
        unique_names = list({d.name: None for d in duplicates})
        return [next(d for d in duplicates if d.name == n) for n in unique_names]

    @property
    def unique_cops(self) -> list[SourcedAgendum]:
        return self.unique_name_list(self.targeted.cop)

    @property
    def unique_chops(self) -> list[Agendum]:
        return self.unique_name_list(self.targeted.chop)

    def apply(
        self,
        input_text: str,
        *,
        imports_in: list[ArrivingImport],
        imports_out: list[DepartingImport],
        recheck: Checker | None = None,
    ) -> str:
        if imports_out:
            resting_imports = [
                imp
                for departure in imports_out
                for imp in self.original_ref.imports
                if imp.source.lineno == departure.lineno
                if imp is not departure.bound
            ]
            if resting_imports:
                raise NotImplementedError("Imports staying and going on same line")
        copped = [
            Arrival(name=n.name, rng=self.def_rng(n.name)) for n in self.unique_cops
        ]
        chopped = [
            Departure(name=n.name, rng=self.def_rng(n.name)) for n in self.unique_chops
        ]
        chopped.sort(key=lambda d: d.rng, reverse=True)
        sorted_chop_deps = chopped == sorted(chopped, key=lambda d: d.rng, reverse=True)
        assert sorted_chop_deps, f"Unsorted chop deps {chopped}"
        # Prune unused imports_out if passed"
        chopped_with_imports = chopped + [
            Departure(name=imp.name, rng=imp.rng) for imp in imports_out
        ]
        sorted_chop_imps = chopped_with_imports == sorted(
            chopped_with_imports, key=lambda d: d.rng, reverse=True
        )
        assert sorted_chop_imps, "Unsorted chop deps after appending imports"
        cut = Cutter(input_text, chopped_with_imports, spacing=self.spacing)
        paste = Paster(input_text, copped, ref=self.ref, spacing=self.spacing)
        ends = [str(cut).rstrip("\n"), str(paste).rstrip("\n")]
        # Increment spacing by 1 to account for the stripped line ending
        inter_def_sep = "\n" * (self.spacing + 1)
        sewn = inter_def_sep.join(filter(None, ends)) + "\n"
        if imports_in:
            done = self.sew_in_imports(imports=imports_in, text=sewn, recheck=recheck)
        else:
            done = sewn
        return done

    def sew_in_imports(
        self, imports: list[ArrivingImport], text: str, recheck: Checker = None
    ) -> str:
        """
        Leave sep of 2 lines if definitions go first, 1 line for anything else.
        """
        spacing = self.calculate_import_spacing(recheck=recheck)
        first = spacing.first_import_lineno
        # spacing.gap, spacing.first_import_lineno, spacing.future_offset
        start = first - 1 + spacing.future_offset if first else 0
        pre, suf = spacing.split_text(text, at=start)
        unparsed_imports = [imp.unparse() for imp in imports]
        pre_filtered = list(filter(None, pre))
        sewn = "\n".join(pre_filtered + unparsed_imports + [""] * spacing.gap) + suf
        return sewn

    def calculate_import_spacing(self, recheck: Checker) -> ImportSpacing:
        """
        A quick estimate of how big a gap to leave after the supplied import(s),
        returning the gap (0, 1, or 2) and the first import line number [0 if none].
        Also, if the gap is 1 (indicating import-first order), check if the first is the
        special `__future__.annotations` import (which must be left the first import).
        To do this thoroughly would presumably require interfacing with `isort`.
        """
        # TODO: use recheck's list of imports rather than the `original_ref` to
        # determine if defs/imports are in the file, to be spaced out against
        ref = recheck  # self.original_ref
        min_def_ln = min((d.lineno for d in ref.alldefs), default=0)
        min_imp_ln = min((i.source.lineno for i in ref.imports), default=0)
        # If the file is missing either definitions or imports, the min. will be 0.
        # Using or means that in this case, the other value would be used instead.
        # If there are *neither* definitions nor imports, the max. will be 0 too.
        min_lineno = min(min_def_ln, min_imp_ln) or max(min_def_ln, min_imp_ln)
        future_import_offset = 0
        if min_lineno == 0:
            # The file has no imports and no definitions (this is a null result)
            gap = 0
        elif min_imp_ln == min_lineno:
            # The file has imports before any definitions (this is a conclusive result)
            gap = 1
            # Check if first node line (which is an import) is __future__.annotations
            first_import = next(i for i in ref.imports if i.source.lineno == min_imp_ln)
            if first_import.fullName == "__future__.annotations":
                future_import_offset = 1  # Put import(s) after the future import
                # gap = 0  # Don't leave a gap (as it'd be after the future import)
        else:
            # The file has definitions before any imports (effectively starts with them)
            gap = 2
        spacing = ImportSpacing(
            gap=gap, first_import_lineno=min_imp_ln, future_offset=future_import_offset
        )
        return spacing

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
        filtered = self.apply(input_text, imports_in=[], imports_out=[])
        return filtered

    def resimulate(
        self,
        input_text: str,
        *,
        imports_in: list[ArrivingImport],
        imports_out: list[DepartingImport],
        recheck: Checker | None = None,
    ) -> str:
        """
        Second pass if necessary to remove import statements that would not be used
        after moving the `mv` definition(s) out of the file.
        """
        filtered = self.apply(
            input_text,
            imports_in=imports_in,
            imports_out=imports_out,
            recheck=recheck,
        )
        return filtered

    def recheck(self, input_text: str) -> Checker:
        """
        First pass, with no change to import statements.
        """
        if input_text == "x = 1\n\n\nclass A:\n\n\ny = 2\n":
            raise ValueError("WTF")
        return reparse(check=self.original_ref, input_text=input_text)

    def simulate(self, input_text: str) -> str:
        """
        This method has no side effects on the state of `self`.
        """
        pre_sim = self.pre_simulate(input_text=input_text)
        if self.original_ref is None:
            # (BUG?) No imports will be copped if dst is None (why?)
            return pre_sim
        # Note: recheck src for newly unused imports, and dst to gauge import spacing
        recheck = self.recheck(pre_sim)
        if self.is_src:
            unused_imports = self.compare_imports(recheck)
            if unused_imports:
                return self.resimulate(
                    input_text, imports_in=[], imports_out=unused_imports
                )
            else:
                return pre_sim
        else:
            import_uses = self.map_import_usage()
            if import_uses:
                dependent_imports = self.patch_dependents(uses=import_uses)
                return self.resimulate(
                    input_text,
                    imports_in=dependent_imports,
                    imports_out=[],
                    recheck=recheck,
                )
            else:
                return pre_sim

    def patch_dependents(self, uses: list[SourcedUse]) -> list[ArrivingImport]:
        """
        Patch any uses which depend on getting a new import. Turn the list of
        AST-sourced name binding uses into a list of patches to apply (prepend).
        Ensure not to patch any that are already present in the dst file.
        """
        dst_import_names = {imp.name for imp in self.original_ref.imports}
        arrivals = [
            ArrivingImport(bound=used_import)
            for use in uses
            for used_import in use.imports
            if use.name not in dst_import_names
        ]
        return arrivals

    def map_import_usage(self) -> list[SourcedUse]:
        """
        AST ancestor subtrees of the node where each source import was marked as being
        'used' (NB only one value: overwritten during walk, so it appears that we don't
        have access to all uses, only its last use).

        However! Since we access the `scopes` during the walk, if we know they have at
        least one use (`src_imp_name_trees`) we can look up all uses of the same name.

        This gets stored as `all_src_imp_name_trees`, and it tells us "what's above each
        usage node in the tree walked by `Checker`. We can match `self.ref.target_defs`
        to this 'ancestry' tree, to get all definition-scoped import uses (and which
        definitions they come from).

        Having obtained those uses, we need to compare them to the imports themselves.
        This takes us from `all_src_imp_name_trees` to `sourced_uses`.

        There are 2 possible ways we can cross-reference the uses to the imports:
          - chopped::Patch.rng <-> used_on_line_ranges::Patch.rng
          - imports::Importation.source <-> ref.import_uses::(scope, node)

        (1) Use line ranges [rejected: match AST nodes and unparse instead]

            >>> used_on_line_ranges = {
                    name: [
                        Patch((name_node.lineno, name_node.end_lineno))
                        for scope, name_node in use_list
                    ]
                    for name, use_list in self.ref.import_uses.items()
                }

        (2) Match use name ancestor to a moved definition (AST node). If an import use
        occurs within a moved definition, colocate its import alongside, into dst.
          - NB: we store in `used` the node which uses the name.
          - NB: we store in `imports` the `pyflakes.checker.Importation` "binding".

        This function is hardcoded to use `self.ref`, as we would never consider using
        `self.dst_ref` (which by definition does not contain the `target_defs` to move)
        or the `recheck` of src (which may have caused removal of used imports).
        """
        # TODO: also duplicate future annotations without asking?
        if self.ref.imports:
            src_imp_name_trees = [
                self.ref.get_ancestors(node)
                for src_imp in self.ref.imports
                if isinstance(src_imp.used, tuple)  # skip if `used` is a bool
                for name, node in [src_imp.used]  # (FunctionScope, ast.Name)
            ]
            if src_imp_name_trees:
                # access without checking type: always (FunctionScope, ast.Name)
                # here because we control how the import_uses list is populated
                all_src_imp_name_trees = {
                    name: [
                        self.ref.get_ancestors(name_node)
                        for (scope, name_node) in use_list
                    ]
                    for name, use_list in self.ref.import_uses.items()
                }
                cop_names = [c.name for c in self.unique_cops]
                target_defs_in_src_to_cop = list(map(self.get_def_node, cop_names))
                sourced_uses = [
                    SourcedUse(
                        name=imp_name,
                        imports=[imp for imp in self.ref.imports],  # (BUG) not filtered
                        target=mv_target_in_src,
                    )
                    for imp_name, tree_group in all_src_imp_name_trees.items()
                    for imp_ancestry in tree_group
                    if imp_name in [imp.name for imp in self.ref.imports]
                    if (
                        mv_target_in_src := next(
                            (
                                target_def
                                for target_def in target_defs_in_src_to_cop
                                if target_def in imp_ancestry
                            ),
                            None,
                        )
                    )
                    is not None
                ]
                # We could simply AST unparse the node, avoiding any need to
                # process multiple imports on the same line, though this would
                # lose any comments on the line(s). This will be incompatible with
                # isort ignore comments, but that's fine (for an initial solution).
            else:
                sourced_uses = []
        else:
            sourced_uses = []
        return sourced_uses

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
