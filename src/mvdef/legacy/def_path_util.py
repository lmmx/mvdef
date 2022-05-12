# flake8: noqa
from enum import Enum

__all__ = [
    "TokenisedStr",
    "NullPathStr",
    "UntypedPathStr",
    "FuncDefPathStr",
    "InnerFuncDefPathStr",
    "ClassDefPathStr",
    "HigherOrderClassDefPathStr",
    "InnerClassDefPathStr",
    "MethodDefPathStr",
]


class PathPartStr(str):
    pass


class FuncPathPart(PathPartStr):
    part_type = "Func"


class InnerFuncPathPart(PathPartStr):
    part_type = "InnerFunc"


class ClassPathPart(PathPartStr):
    part_type = "Class"


class InnerClassPathPart(PathPartStr):
    part_type = "InnerClass"


class HigherOrderClassPathPart(PathPartStr):
    part_type = "HigherOrderClass"


class MethodPathPart(PathPartStr):
    part_type = "Method"


class DecoratorPathPart(PathPartStr):
    part_type = "Decorator"


class TokenisedStr:
    def __init__(self, path_string):
        self.string = path_string
        self.parse_from_string()  # sets ._tokens and .parts
        self.check_part_types()

    class PathSepEnum(Enum):
        "Path separator symbols (1 to 2 characters)"
        InnerFunc = ":"
        Method = "."
        InnerClass = "::"
        HigherOrderClass = ":::"
        Decorator = "@"
        # WildCard = "*"
        # MultiLevelWildCard = "**"

    class PathPartEnum(Enum):
        "Parts to parse tokens into"
        Func = FuncPathPart
        InnerFunc = InnerFuncPathPart
        Class = ClassPathPart
        InnerClass = InnerClassPathPart
        HigherOrderClass = HigherOrderClassPathPart
        Method = MethodPathPart
        Decorator = DecoratorPathPart

    class DefTypeToParentTypeEnum(Enum):
        "Duplicate of the enum in ast_util.py (TODO: refactor)"
        Method = "Class"
        InnerClass = "Class"
        InnerFunc = "Func"
        HigherOrderClass = "Func"

    def parse_from_string(self):
        self.tokenise_from_string()  # sets ._tokens
        self.parse_from_tokens()  # sets .parts

    def tokenise_from_string(self):
        self._tokens = []
        parse_string_symbols = [*self.string]
        all_separators = self.PathSepEnum._value2member_map_
        while parse_string_symbols:
            symbol = parse_string_symbols.pop(0)
            if len(parse_string_symbols) > 1:
                trigram = symbol + "".join(parse_string_symbols[:2])
                if trigram in all_separators:
                    sep = all_separators.get(trigram)
                    self._tokens.append(sep)
                    del parse_string_symbols[:2]  # pop two extra symbols
                    continue
            if parse_string_symbols:
                bigram = symbol + parse_string_symbols[0]
                if bigram in all_separators:
                    sep = all_separators.get(bigram)
                    self._tokens.append(sep)
                    parse_string_symbols.pop(0)  # pop extra symbol
                    continue
            if symbol in all_separators:
                sep = all_separators.get(symbol)
                self._tokens.append(sep)
            elif self._tokens and isinstance(self._tokens[-1], str):
                self._tokens[-1] += symbol
            else:  # either the first part, or the last part was a separator, so append
                self._tokens.append(symbol)

    def _trivial_parts_constructor(self):
        self.parts = [self.leaf_enum.value(*self._tokens)]

    def parse_from_tokens(self):
        if len(self._tokens) == 1:
            # Trivial case
            self._trivial_parts_constructor()  # allow override by UntypedPathStr
            return
        self.parts = []
        tokens = [*self._tokens]  # make a copy to destroy
        while tokens:
            tok = tokens.pop(0)
            if not self.parts:
                # the token is the first and must be a string
                assert type(tok) is str, "1st token should be string not separator"
                # must hold off on annotating whether class or funcdef until seeing sep
                next_tok = tokens.pop(0)  # look ahead (consume again)
                assert type(next_tok) is self.PathSepEnum, "2 unseparated string tokens"
                last_seen_sep = next_tok
                sep_type = next_tok.name
                if sep_type in [
                    "InnerFunc",
                    "HigherOrderClass",
                    "Decorator",
                ]:  # then tok 1 is a funcdef
                    tok_parsed = FuncPathPart(tok)
                elif sep_type in ["Method", "InnerClass"]:  # then tok 1 is a classdef
                    tok_parsed = ClassPathPart(tok)
                else:
                    msg = "Is this method up to date with enum?"
                    raise NotImplementedError(f"Didn't recognise '{sep_type}'. {msg}")
            elif tokens:
                # the token is not the first so must be an inner function or inner class
                if last_seen_sep:
                    assert type(tok) is str, f"Expected string after sep (got '{tok}')"
                    part_class = self.PathPartEnum._member_map_.get(
                        last_seen_sep.name
                    ).value
                    tok_parsed = part_class(tok)
                    last_seen_sep = None  # didn't look ahead, unset (only used on init)
                else:
                    # did not look ahead at the last step so must have the separator now
                    assert type(tok) is self.PathSepEnum, "2 unseparated string tokens"
                    part_class = self.PathPartEnum._member_map_.get(tok.name).value
                    next_tok = tokens.pop(0)
                    assert type(next_tok) is str, "Token should be string not separator"
                    tok_parsed = part_class(next_tok)
            else:
                # last token, so no look ahead at next token, so must have last_seen_sep
                assert type(tok) is str, "Expected final token to be a string"
                assert last_seen_sep, "Cannot assign a type to string without separator"
                part_class = self.PathPartEnum._member_map_.get(
                    last_seen_sep.name
                ).value
                tok_parsed = part_class(tok)
                last_seen_sep = None  # didn't look ahead, unset (only used on init)
            self.parts.append(tok_parsed)

    @property
    def _sep_tokens(self):
        return [t for t in self._tokens if type(t) is self.PathSepEnum]

    ### Helper functions used to check which type of path the FuncDefPath is
    @property
    def _supported_path_types(self):
        return ("InnerFunc", "Method", "InnerClass", "HigherOrderClass")

    @property
    def is_unsupported(self):
        a = any(t.name not in self._supported_path_types for t in self._sep_tokens)
        return a


class RootedMixin:
    @property
    def root_name(self):
        return self.parts[0]

    @property
    def root_type(self):
        return self.root_name.part_type


class LeafMixin(RootedMixin):
    @property
    def leaf_name(self):
        return self.parts[-1]

    @property
    def leaf_type(self):
        return self.leaf_name.part_type

    def leaf_check(self):
        return self.leaf_type == self.leaf_enum.name

    def check_part_types(self):
        msg = f"Leaf must be: {self.leaf_enum.name} (not {self.leaf_type})"
        assert self.leaf_check(), msg


class ParentedMixin(LeafMixin):
    @property
    def parent_name(self):
        return self.parts[-2]

    @property
    def parent_type(self):
        return self.parent_name.part_type

    def parent_check(self):
        if hasattr(self, "parent_type_name"):
            check = self.parent_type_name == self.parent_enum.name
        elif self.parent_type in self.DefTypeToParentTypeEnum._member_map_:
            check = (
                self.DefTypeToParentTypeEnum[self.parent_type].value
                == self.parent_enum.name
            )
        else:
            check = self.parent_type == self.parent_enum.name
        return check

    def check_part_types(self):
        super().check_part_types()
        msg = f"Parent must be: {self.parent_enum.name} (not {self.parent_type})"
        assert self.parent_check(), msg


class UntypedMixin:
    def check_part_types(self):
        pass

    class UntypedPathPart:
        def __init__(self, part_string):
            self.string = part_string
            self.part_type = None

    def _trivial_parts_constructor(self):
        self.parts = [self.UntypedPathPart(*self._tokens)]


class NullPathStr(TokenisedStr, UntypedMixin):
    "The empty path, used for moving into the global namespace."

    def __init__(self):
        super().__init__(path_string="")


class UntypedPathStr(UntypedMixin, TokenisedStr):
    """
    A path without type checks (only to be used when determining path type).
    """

    def check_part_types(self):
        pass


class FuncDefPathStr(TokenisedStr, LeafMixin):
    """
    A path denoting an AST path to a function (which may be nested as an inner function
    in a funcdef; or as a method in a classdef), or any further nesting therein
    (e.g. the inner function of an inner function, etc.).

    Subclasses should be used to indicate such nested classes, this class itself
    should only be instantiated for a 'top-level' funcdef, i.e. in the trunk of
    the AST.
    """

    @property
    def leaf_enum(self):
        return self.PathPartEnum.Func

    @property
    def is_ifunc_path_only(self):
        return all(t.name == "InnerFunc" for t in self._sep_tokens)


class InnerFuncDefPathStr(FuncDefPathStr, ParentedMixin):
    """
    A FuncDefPathStr in which both the leaf and the leaf's parent are funcdefs.
    This is checked on __init__.

    This class should be subclassed for checking against the (separate) ASTs used in
    either `ast_util` or `asttokens` (the first for generating the inner function
    indexes, the latter for line numbering associated with the AST nodes).
    """

    @property
    def parent_enum(self):
        return self.PathPartEnum.Func

    @property
    def leaf_enum(self):
        return self.PathPartEnum.InnerFunc


class ClassDefPathStr(TokenisedStr, LeafMixin):
    """
    A path denoting an AST path to a class (which may be nested as an inner class
    in a classdef; or as a higher order class in a funcdef), or
    any further nesting therein (e.g. the inner class of an inner class, etc.).
    Subclasses should be used to indicate such nested classes, this class itself
    should only be instantiated for a 'top-level' classdef, i.e. in the trunk of
    the AST.
    """

    @property
    def leaf_enum(self):
        return self.PathPartEnum.Class


class HigherOrderClassDefPathStr(ClassDefPathStr, ParentedMixin):
    """
    A ClassDefPathStr whose leaf is a classdef and whose leaf's parent is a funcdef.
    This is checked on __init__.

    This class should be subclassed for checking against the (separate) ASTs used in
    either `ast_util` or `asttokens`.
    """

    # fall through to ClassDefPathStr.__init__, setting .string, ._tokens and .parts
    def __init__(self, path_string):
        super().__init__(path_string)
        self.check_part_types()

    @property
    def parent_enum(self):
        return self.PathPartEnum.Func

    @property
    def leaf_enum(self):
        return self.PathPartEnum.HigherOrderClass


class InnerClassDefPathStr(ClassDefPathStr, ParentedMixin):
    """
    A ClassDefPathStr in which both the leaf and the leaf's parent are classdefs.
    This is checked on __init__.

    This class should be subclassed for checking against the (separate) ASTs used in
    either `ast_util` or `asttokens` (the first for generating the inner function
    indexes, the latter for line numbering associated with the AST nodes).
    """

    # fall through to ClassDefPathStr.__init__, setting .string, ._tokens and .parts
    def __init__(self, path_string):
        super().__init__(path_string)
        self.check_part_types()

    @property
    def parent_enum(self):
        return self.PathPartEnum.Class

    @property
    def leaf_enum(self):
        return self.PathPartEnum.InnerClass


class MethodDefPathStr(FuncDefPathStr, ParentedMixin):
    """
    A FuncDefPathStr whose leaf's parent is a class (and whose leaf is the method func).
    These are checked on __init__.

    This class should be subclassed for checking against the (separate) ASTs used in
    either `ast_util` or `asttokens` (the first for generating the inner function
    indexes, the latter for line numbering associated with the AST nodes).
    """

    # fall through to FuncDefPathStr.__init__, setting .string, ._tokens and .parts
    def __init__(self, path_string):
        super().__init__(path_string)
        self.check_part_types()

    @property
    def parent_enum(self):
        return self.PathPartEnum.Class

    @property
    def leaf_enum(self):
        return self.PathPartEnum.Method
