from dataclasses import dataclass

from .move import MvDef

__all__ = ["CpDef"]


@dataclass
class CpDef(MvDef):
    """
      Copy function definitions from one file to another, and any necessary
      associated import statements along with them.

      Option     Description                                Type        Default
      —————————— —————————————————————————————————————————— ——————————— ———————
    • src        source file to copy definitions from       Path        -
    • dst        destination file (may not exist)           Path        -
    • mv         names to copy from the source file         list[str]   -
    • dry_run    whether to only preview the change diffs   bool        False
    • escalate   whether to raise an error upon failure     bool        False
    • cls_defs   whether to target only class definitions   bool        False
    • all_defs   whether to target both class & funcdefs    bool        False
    • verbose    whether to log anything                    bool        False
    """

    _copy_mode: bool = True

    def diffs(self, print_out: bool = False) -> str:
        """
        Calls `Agenda.populate_agenda()` explicitly for the src file, and implicitly for
        the dst file by `Agenda.unidiff()`, and returns a single diff string for dst.
        """
        # Necessary to populate the Agenda to set up its Checker (becomes `source_ref`)
        if self.src_diff.agenda.empty:
            self.src_diff.populate_agenda()
        dst_unidiff = self.dst_diff.unidiff()
        if print_out:
            print(dst_unidiff)
        return dst_unidiff
