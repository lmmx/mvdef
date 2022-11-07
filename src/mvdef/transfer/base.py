from dataclasses import dataclass

from ..core.check import Checker
from ..error_handling.exceptions import CheckFailure
from ..failure import FailableMixIn
from ..log_utils import set_up_logging

__all__ = ["MvDefBase"]


@dataclass  # TODO: delete this (don't think it's needed)
class MvDefBase(FailableMixIn):
    """
    Common methods (allowing LsDef to have a different signature to MvDef/CpDef)

    Implementation note: :attr:`_check_kw` and :attr:`_diff_kw` are stored as class
    attributes (by virtue of being un-type annotated, due to how dataclasses work).
    They are single-underscore prefixed to avoid name clash with the properties of the
    same [but unprefixed] names.
    """

    # Do not type annotate (see docstring)
    check_kw = ["cls_defs", "func_defs"]
    diff_kw = ["escalate", "verbose"]

    def __post_init__(self):
        self.logger = set_up_logging(__name__, verbose=self.verbose)
        self.log(self)
        if self.cls_defs and self.func_defs:
            # Internally these must mean "only", so flip both (before parsing in check)
            self.cls_defs, self.func_defs = False, False
        self.check_blocker = self.check()

    @property
    def all_defs(self) -> bool:
        """If neither exclusively classdefs or exclusively funcdefs, use both."""
        return not (self.cls_defs or self.func_defs)

    @classmethod
    def clsvar_fetch(cls, name: str) -> list[bool]:
        """
        Fetch the sum list of the named classvar on all ancestors, by walking the MRO
        down to `MvDefBase`, skipping any classes without the classvar explicitly set.
        """
        cls_name = getattr(cls, name)
        if is_not_base_cls := (super().__thisclass__ is not cls):
            parent_cls_name = getattr((parent_cls := cls.mro()[1]), name)
            add = [] if cls_name == parent_cls_name else cls_name  # skip if falls thru
            result = parent_cls.clsvar_fetch(name=name) + add
        return result if is_not_base_cls else cls_name

    def _kwargify(self, classvar_name: str) -> dict:
        kw_flag_names = self.clsvar_fetch(classvar_name)
        return {flag_name: getattr(self, flag_name) for flag_name in kw_flag_names}

    def src_kwargs(self, classvar_name: str) -> dict[str, bool | Checker]:
        return {**self._kwargify(classvar_name), "source_ref": self.src_check}

    @property
    def check_kwargs(self) -> dict[str, bool | Checker]:
        return self.src_kwargs("check_kw")

    @property
    def src_diff_kwargs(self) -> dict[str, bool | Checker]:
        return self.src_kwargs("diff_kw")

    def log(self, msg):
        self.logger.info(msg)

    def check(self) -> CheckFailure | None:
        """
        Returns None if check succeeds, or returns the `CheckFailure` for the first
        blocker found upon checking that the file parses correctly (the function will
        raise errors rather than returning them in 'escalate' mode, to help debugging).
        """
        raise NotImplementedError("Implemented on subclass")
