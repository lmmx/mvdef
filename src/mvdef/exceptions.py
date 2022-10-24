__all__ = ["MvDefException"]


class MvDefException(Exception):
    """
    Base class for deliberate MvDef errors
    """


class CheckFailure(MvDefException):
    """MvDef: check failed"""
