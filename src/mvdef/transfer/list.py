from dataclasses import dataclass, field
from pathlib import Path

from ..core.manifest.manifest import Manifest
from ..core.parse import parse_file
from ..error_handling.exceptions import CheckFailure
from .base import MvDefBase


@dataclass
class LsDef(MvDefBase):
    """
    List function definitions in a given file.

    Option     Description                                Type        Default
    —————————— —————————————————————————————————————————— ——————————— ———————
    • src        source file to list definitions from       Path        -
    • match      name regex to list from the source file    list[str]   ['*']
    • dry_run    whether to print the __all__ diff          bool        False
    • list       whether to print the list of names         bool        False
    • escalate   whether to raise an error upon failure     bool        False
    • cls_defs   whether to use only class definitions      bool        False
    • func_defs  whether to use only function definitions   bool        False
    • verbose    whether to log anything                    bool        False
    """

    src: Path
    match: list[str] = field(default_factory=lambda: ["*"])
    dry_run: bool = False
    list: bool = False
    escalate: bool = False
    cls_defs: bool = False
    func_defs: bool = False
    verbose: bool = False
    # Future idea: flag to show import usage map alongside each definition

    def __post_init__(self):
        super().__post_init__()
        kwargs = {k: getattr(self, k) for k in "dry_run list escalate verbose".split()}
        kwargs["source_ref"] = self.src_check
        self.src_manifest = Manifest(self.src, matchers=self.match, **kwargs)

    def check(self) -> CheckFailure | None:
        kwargs = {
            k: getattr(self, k) for k in "escalate verbose cls_defs func_defs".split()
        }
        try:
            self.src_check = parse_file(self.src, ensure_exists=True, **kwargs)
        except Exception as exc:
            self.src_check = None
            return self.fail("Failed to parse the src file", exc_info=exc)
        else:
            if self.src_check is None:
                return self.fail("Failed to parse the src file")
        return None

    def manif(self, print_out: bool = False) -> str:
        """
        Calls `Agenda.populate_agenda()` explicitly if not yet created,
        and returns a single diff string.
        """
        if self.src_manifest.agenda.empty:
            self.src_manifest.populate_agenda()
        src_manif = self.src_manifest.fill()
        if print_out:
            print(src_manif)
        return src_manif
