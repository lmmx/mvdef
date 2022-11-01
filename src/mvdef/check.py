from __future__ import annotations

import ast
import os
from ast import AST
from functools import cache
from typing import Type

import pyflakes
from pyflakes import checker
from pyflakes.checker import (
    Annotation,
    Builtin,
    ClassScope,
    DetectClassScopedMagic,
    GeneratorScope,
    Importation,
    StarImportation,
    getNodeName,
)
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
    imports: list[tuple[AST, Importation | Type[Importation]]]
    import_uses: dict[str, list[tuple[AST, Importation | Type[Importation]]]]

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
        self.import_uses = {}
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

    def handleNodeLoad(self, node):
        used_set = []  # Note: not used, but would help if re-assignment is an issue
        # https://github.com/PyCQA/pyflakes/blob/
        # 853cce91634cbddff01cc16313b5467be1e95c54/pyflakes/checker.py#L1073-L1094
        # ------------- start of copied part (L1073-L1094)
        if not (name := getNodeName(node)):
            return
        in_generators, importStarred = None, None
        # try enclosing function scopes and global scope
        for scope in self.scopeStack[-1::-1]:
            if isinstance(scope, ClassScope):
                if name == "__class__":
                    return
                elif in_generators is False:
                    # only generators used in a class scope can access the names of the
                    # class. this is skipped during the first iteration
                    continue
            binding = scope.get(name, None)
            if isinstance(binding, Annotation) and not self._in_postponed_annotation:
                scope[name].used = True
                continue
            if name == "print" and isinstance(binding, Builtin):
                parent = self.getParent(node)
                if isinstance(parent, ast.BinOp) and isinstance(parent.op, ast.RShift):
                    self.report(pyflakes.messages.InvalidPrintSyntax, node)
            try:
                scope[name].used = (self.scope, node)
                # if the name of SubImportation is same as alias of other Importation
                # and the alias is used, SubImportation also should be marked as used.
                n = scope[name]
                self.import_uses.setdefault(name, [])
                self.import_uses[name].append((self.scope, node))
                used_set.append(name)
                if isinstance(n, Importation) and n._has_alias():
                    try:
                        scope[n.fullName].used = (self.scope, node)
                        self.import_uses.setdefault(n.fullName, [])
                        self.import_uses[n.fullName].append((self.scope, node))
                        used_set.append(n.fullName)
                    except KeyError:
                        pass
            except KeyError:
                pass
            else:
                return
            importStarred = importStarred or scope.importStarred
            if in_generators is not False:
                in_generators = isinstance(scope, GeneratorScope)
        if importStarred:
            from_list = []
            for scope in self.scopeStack[-1::-1]:
                for binding in scope.values():
                    if isinstance(binding, StarImportation):
                        # mark '*' imports as used for each scope
                        binding.used = (self.scope, node)
                        self.import_uses.setdefault(binding.fullName, [])
                        self.import_uses[binding.fullName].append((self.scope, node))
                        used_set.append(binding.fullName)
                        from_list.append(binding.fullName)
            # report * usage, with a list of possible sources
            from_list = ", ".join(sorted(from_list))
            self.report(pyflakes.messages.ImportStarUsage, node, name, from_list)
            return
        if name == "__path__" and os.path.basename(self.filename) == "__init__.py":
            # the special name __path__ is valid only in packages
            return
        if name in DetectClassScopedMagic.names and isinstance(self.scope, ClassScope):
            return
        # protected with a NameError handler?
        if "NameError" not in self.exceptHandlers[-1]:
            self.report(pyflakes.messages.UndefinedName, node, name)
        # super().handleNodeLoad(node)
