from __future__ import annotations

from ast import AST
from functools import cache
from typing import Type

from pyflakes import checker
from pyflakes.messages import UnusedImport

from .failure import FailableMixIn

__all__ = ["Checker"]


class Checker(FailableMixIn, checker.Checker):
    verbose: bool
    escalate: bool
    target_cls: bool
    target_all: bool
    funcdefs: list[AST]
    classdefs: list[AST]
    alldefs: list[AST]
    imports: list[tuple[AST, checker.Importation | Type[checker.Importation]]]

    def __init__(self, *args, **kwargs):
        self.code = kwargs.pop("code")
        self.verbose = kwargs.pop("verbose", False)
        self.escalate = kwargs.pop("escalate", False)
        self.target_cls = kwargs.pop("cls_defs", False)
        self.target_all = kwargs.pop("all_defs", False)
        self.funcdefs = []
        self.classdefs = []
        self.alldefs = []
        self.imports = []
        super().__init__(*args, **kwargs)

    @property
    def target_defs(self) -> list[AST]:
        """Expand to classdefs or either in future"""
        if self.target_all:
            return self.alldefs
        else:
            return self.classdefs if self.target_cls else self.funcdefs

    def handleNode(self, node: AST | None, parent: AST) -> None:
        """Subclass override"""
        super().handleNode(node=node, parent=parent)
        if node is not None:
            setattr(node, "depth", self.get_ancestors(node, count=True))

    def CLASSDEF(self, node: AST) -> None:
        """Subclass override"""
        super().CLASSDEF(node=node)
        self.classdefs.append(node)
        self.alldefs.append(node)

    def FUNCTIONDEF(self, node: AST) -> None:
        """Subclass override"""
        super().FUNCTIONDEF(node=node)
        self.funcdefs.append(node)
        self.alldefs.append(node)

    def addBinding(self, node: AST, value) -> None:
        super().addBinding(node=node, value=value)
        if isinstance(value, checker.Importation):
            self.imports.append(value)

    def describe_node(self, node: AST) -> None:
        line_range = f"{node.lineno}-{node.end_lineno}"
        info = f"{type(node).__name__} {node.name!r} ({line_range=})"
        if self.verbose:
            print(f"{info} depth={node.depth} -> {node.returns.id}")

    def get_ancestors(self, node: AST, count: bool = False) -> int | list[AST]:
        ancestors = []
        while parent := self.getParent(node):
            if count and hasattr(node, "depth"):
                return node.depth + len(ancestors)
            ancestors.append(parent)
            if parent is self.root:
                return len(ancestors) if count else ancestors
            node = parent

    @cache
    def unused_imports(self) -> list[UnusedImport]:
        """
        Import strings (in `m.message_args[0]` for each `UnusedImport` message `m`):

        - "import a( as o)"           -> "a( as o)"
        - "from a import b( as o)"    -> "a.b( as o)"
        - "from a.b import c( as o)"  -> "a.b.c( as o)"
        - "from . import a( as o)"    -> ".a( as o)"
        - "from .a import b( as o)"   -> ".a.b( as o)"
        - "from .a.b import c( as o)" -> ".a.b.c( as o)"
        """
        imps = [m for m in self.messages if isinstance(m, UnusedImport)]
        return imps
