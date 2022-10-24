__all__ = ["MvDefException", "CheckFailure", "AgendaFailure"]


class MvDefException(Exception):
    """
    Base class for deliberate MvDef errors
    """


class CheckFailure(MvDefException):
    """MvDef: check failed"""


class AgendaFailure(MvDefException):
    """MvDef: agenda failed"""
