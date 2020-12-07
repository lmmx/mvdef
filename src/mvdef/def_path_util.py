from enum import Enum
from functools import partial


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


class FuncDefPathString:
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
        self.parse_from_string()  # sets .tokens and .parts

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
        self.tokens = []
        self.tokenise_from_string() # sets .tokens
        self.parse_from_tokens() # sets .parts

    def tokenise_from_string(self):
        parse_string_symbols = [*self.string]
        while parse_string_symbols:
            symbol = parse_string_symbols.pop(0)
            if parse_string_symbols:  # if any symbols left to pop
                next_symbol = parse_string_symbols[0]
                bigram = f"{symbol}{next_symbol}"
                if bigram in self.PathSepEnum._value2member_map_:
                    parse_string_symbols.pop(0)  # already stored as `next_symbol`
                    sep = self.PathSepEnum._value2member_map_.get(bigram)
                    self.tokens.append(sep)
                    continue  # don't try to parse 1st symbol after using it in 'bigram'
            if symbol in self.PathSepEnum._value2member_map_:
                sep = self.PathSepEnum._value2member_map_.get(symbol)
                self.tokens.append(sep)
            elif self.tokens and isinstance(self.tokens[-1], str):
                self.tokens[-1] += symbol
            else:  # either the first part or the last part was a separator so append
                self.tokens.append(symbol)

    def parse_from_tokens(self):
        if len(self.tokens) == 1:
            # Trivial case
            self.parts = [self.PathPartEnum.Func.value(*self.tokens)]
            return
        self.parts = []
        tokens = [*self.tokens]  # make a copy to destroy
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
