from enum import Enum

__all__ = ["FuncDefPathString", "InnerFuncDefPathString", "ClassDefPathString", "MethodDefPathString"]

class PathPartStr(str):
    pass


#    def __new__(cls, string, part_type):
#        s = super().__new__(cls, string)
#        s.part_type = part_type
#        return s


class FuncPathPart(PathPartStr):
    part_type = "Func"


class InnerFuncPathPart(PathPartStr):
    part_type = "InnerFunc"


class ClassPathPart(PathPartStr):
    part_type = "Class"


class InnerClassPathPart(PathPartStr):
    part_type = "InnerClass"


class MethodPathPart(PathPartStr):
    part_type = "Method"


class DecoratorPathPart(PathPartStr):
    part_type = "Decorator"

class TokenisedString:
    def tokenise_from_string(self):
        self._tokens = []
        parse_string_symbols = [*self.string]
        while parse_string_symbols:
            symbol = parse_string_symbols.pop(0)
            if parse_string_symbols:  # if any symbols left to pop
                next_symbol = parse_string_symbols[0]
                bigram = f"{symbol}{next_symbol}"
                if bigram in self.PathSepEnum._value2member_map_:
                    parse_string_symbols.pop(0)  # already stored as `next_symbol`
                    sep = self.PathSepEnum._value2member_map_.get(bigram)
                    self._tokens.append(sep)
                    continue  # don't try to parse 1st symbol after using it in 'bigram'
            if symbol in self.PathSepEnum._value2member_map_:
                sep = self.PathSepEnum._value2member_map_.get(symbol)
                self._tokens.append(sep)
            elif self._tokens and isinstance(self._tokens[-1], str):
                self._tokens[-1] += symbol
            else:  # either the first part or the last part was a separator so append
                self._tokens.append(symbol)

    @property
    def _sep_tokens(self):
        return [t for t in self._tokens if type(t) is self.PathSepEnum]

class ClassDefPathString(TokenisedString):
    """
    A path denoting an AST path to a class (which may be nested as an inner class), or
    any nesting therein (e.g. the inner class of an inner class, etc.)

    E.g. `Foo::Bar` is an inner class `Bar` with parent global classdef `Foo`.
    """

    def __init__(self, path_string):
        self.string = path_string
        self.parse_from_string()  # sets ._tokens and .parts

    class PathSepEnum(Enum):
        "Path separator symbols (1 to 2 characters)"
        InnerFunc = ":"
        Method = "."
        InnerClass = "::"
        Decorator = "@"
        # WildCard = "*"
        # MultiLevelWildCard = "**"

    class PathPartEnum(Enum):
        "Parts to parse tokens into"
        Func = FuncPathPart
        InnerFunc = InnerFuncPathPart
        Class = ClassPathPart
        InnerClass = InnerClassPathPart
        Method = MethodPathPart
        Decorator = DecoratorPathPart

    def parse_from_string(self):
        self.tokenise_from_string() # sets ._tokens
        self.parse_from_tokens() # sets .parts

    def parse_from_tokens(self):
        if len(self._tokens) == 1:
            # Trivial case
            self.parts = [self.PathPartEnum.Func.value(*self._tokens)]
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
                if sep_type in ["InnerFunc", "Decorator"]:  # then tok 1 is a funcdef
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

class FuncDefPathString(TokenisedString):
    """
    A path denoting an AST path to a function (which may be nested as an inner function)
    or method (which may be nested within an inner class), or any combination
    therein (e.g. the inner function of a method of an inner class, etc.)

    E.g. `foo:bar` is an inner function `bar` with parent global funcdef `foo`,
    `Foo.bar` is a method `bar` on the global-scope classdef `Foo`,
    `Foo::Bar.baz` is a method `baz` on the inner class `Bar` within global-scope
    classdef `Foo`,
    `Foo::Bar.baz:bax` is an inner function `bax` on the `baz` method of inner class
    `Bar` within the global-scope classdef `Foo`.

    Additionally, `@` may be used to indicate a specific decorated version of either a
    function or a method (though initially this is intended for use to distinguish
    identically named methods with `@property`/`@DEFNAME.setter` decorators, and in this
    case it would be used as `foo@setter` to indicate the `def foo` with decorator
    `@foo.setter` rather than the `def foo` with decorator `@property`).
    """

    def __init__(self, path_string):
        self.string = path_string
        self.parse_from_string()  # sets ._tokens and .parts

    class PathSepEnum(Enum):
        "Path separator symbols (1 to 2 characters)"
        InnerFunc = ":"
        Method = "."
        InnerClass = "::"
        Decorator = "@"
        # WildCard = "*"
        # MultiLevelWildCard = "**"

    class PathPartEnum(Enum):
        "Parts to parse tokens into"
        Func = FuncPathPart
        InnerFunc = InnerFuncPathPart
        Class = ClassPathPart
        InnerClass = InnerClassPathPart
        Method = MethodPathPart
        Decorator = DecoratorPathPart

    def parse_from_string(self):
        self.tokenise_from_string() # sets ._tokens
        self.parse_from_tokens() # sets .parts

    def parse_from_tokens(self):
        if len(self._tokens) == 1:
            # Trivial case
            self.parts = [self.PathPartEnum.Func.value(*self._tokens)]
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
                if sep_type in ["InnerFunc", "Decorator"]:  # then tok 1 is a funcdef
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

    ### Helper functions used to check which type of path the FuncDefPath is
    @property
    def _supported_path_types(self):
        return ("InnerFunc", "Method")

    @property
    def is_supported_path(self):
        return all(t.name in self._supported_path_types for t in self._sep_tokens)

    @property
    def is_inner_func_path_only(self):
        return all(t.name == "InnerFunc" for t in self._sep_tokens)
    ###


class ClassDefPathString(TokenisedString):
    """
    A FuncDefPathString which has a top level class (known in advance, not checked)
    and any possible combination of node types below that*.
    *[TODO: confirm against finished implementation if this is the case]
    """
    # fall through to FuncDefPathString.__init__, setting .string, ._tokens and .parts
    def __init__(self, path_string):
        self.string = path_string
        self.parse_from_string()  # sets ._tokens and .parts

    @property
    def global_cls_name(self):
        return self.parts[0]
    
    class PathSepEnum(Enum):
        "Path separator symbols (1 to 2 characters)"
        InnerFunc = ":"
        Method = "."
        InnerClass = "::"
        Decorator = "@"
        # WildCard = "*"
        # MultiLevelWildCard = "**"

    class PathPartEnum(Enum):
        "Parts to parse tokens into"
        Func = FuncPathPart
        InnerFunc = InnerFuncPathPart
        Class = ClassPathPart
        InnerClass = InnerClassPathPart
        Method = MethodPathPart
        Decorator = DecoratorPathPart

    def parse_from_string(self):
        self.tokenise_from_string() # sets ._tokens
        self.parse_from_tokens() # sets .parts

    def parse_from_tokens(self):
        if len(self._tokens) == 1:
            # Trivial case
            self.parts = [self.PathPartEnum.Class.value(*self._tokens)]
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
                if sep_type in ["InnerFunc", "Decorator"]:  # then tok 1 is a funcdef
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
        return ("InnerFunc", "Method")

    @property
    def is_supported_path(self):
        return any(t.name not in self._supported_path_types for t in self._sep_tokens)

    @property
    def is_inner_func_path_only(self):
        return any(t.name != "InnerFunc" for t in self._sep_tokens)
    ###

class InnerClassDefPathString(ClassDefPathString):
    """
    A ClassDefPathString which has a top level funcdef, an 'intradef' inner func (these
    are checked on __init__), and potentially one or more inner functions below that.

    This class should be subclassed for checking against the (separate) ASTs used in
    either `ast_util` or `asttokens` (the first for generating the inner function
    indexes, the latter for line numbering associated with the AST nodes).
    """
    # fall through to ClassDefPathString.__init__, setting .string, ._tokens and .parts
    def __init__(self, path_string):
        super().__init__(path_string)
        assert self.global_def_name.part_type == "Class", "Path must begin with a class"
        assert self.innerclsdef_name.part_type == "InnerClass", "Path lacks an inner class"

    @property
    def global_def_name(self):
        return self.parts[0]
    
    @property
    def innerclsdef_name(self):
        return self.parts[1]

class MethodDefPathString(FuncDefPathString):
    """
    A FuncDefPathString which has a top level class, which contains a method (these
    are checked on __init__), and potentially one or more inner functions below that*.
    *[TODO: confirm against finished implementation if this is the case]

    This class should be subclassed for checking against the (separate) ASTs used in
    either `ast_util` or `asttokens` (the first for generating the inner function
    indexes, the latter for line numbering associated with the AST nodes).
    """
    # fall through to FuncDefPathString.__init__, setting .string, ._tokens and .parts
    def __init__(self, path_string):
        super().__init__(path_string)
        assert self.global_cls_name.part_type == "Class", "Path must begin with a class"
        assert self.methdef_name.part_type == "Method", "Path lacks a method"

    @property
    def global_cls_name(self):
        return self.parts[0]
    
    @property
    def methdef_name(self):
        return self.parts[1]

class InnerFuncDefPathString(FuncDefPathString):
    """
    A FuncDefPathString which has a top level funcdef, an 'intradef' inner func (these
    are checked on __init__), and potentially one or more inner functions below that.

    This class should be subclassed for checking against the (separate) ASTs used in
    either `ast_util` or `asttokens` (the first for generating the inner function
    indexes, the latter for line numbering associated with the AST nodes).
    """
    # fall through to FuncDefPathString.__init__, setting .string, ._tokens and .parts
    def __init__(self, path_string):
        super().__init__(path_string)
        assert self.global_def_name.part_type == "Func", "Path must begin with a func"
        assert self.intradef_name.part_type == "InnerFunc", "Path lacks an inner func"

    @property
    def global_def_name(self):
        return self.parts[0]
    
    @property
    def intradef_name(self):
        return self.parts[1]
