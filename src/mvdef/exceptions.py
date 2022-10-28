__all__ = ["MvDefException", "CheckFailure", "AgendaFailure", "SrcNotFound"]


class MvDefException(Exception):
    """
    Base class for deliberate MvDef errors
    """


class CheckFailure(MvDefException):
    """MvDef: check failed"""


class AgendaFailure(MvDefException):
    """MvDef: agenda failed"""


class SrcNotFound(MvDefException, FileNotFoundError):
    """MvDef: source file doesn't exist."""
