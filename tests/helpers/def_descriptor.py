from __future__ import annotations

from dataclasses import dataclass

from .inputs import FuncAndClsDefs

__all__ = ["DefDesc"]


@dataclass
class DefDesc:
    """
    Storage after Enum lookup (protecting against common value misnaming)
    """

    name: str
    value: str

    @classmethod
    def lookup(cls, name: str) -> DefDesc:
        def_enum = FuncAndClsDefs[name]
        return cls(name=name, value=def_enum.value)
