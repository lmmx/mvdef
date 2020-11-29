import ast
from ast import Import as IType, ImportFrom as IFType
from astor import to_source
from asttokens import ASTTokens
from collections import OrderedDict
from .colours import colour_str as colour
from os import linesep as nl

__all__ = ["get_import_stmt_str", "multilinify_import_stmt_str", "colour_imp_stmt", "get_imported_name_sources", "get_module_srcs", "count_imported_names", "annotate_imports", "imp_def_subsets"]

def get_import_stmt_str(alias_list, import_src=None, max_linechars=88):
    """
    Construct an import statement by building an AST, convert it to source using
    astor.to_source, and then return the string.

      alias_list:     List of strings to use as ast.alias `name`, and optionally also
                      `asname entries. If only one name is listed per item in the
                      alias_list, the `asname` will be instantiated as None.
      import_src:     If provided, the import statement will be use the
                      `ast.ImportFrom` class, otherwise it will use `ast.Import`.
                      Relative imports are permitted for "import from" statements
                      (such as `from ..foo import bar`) however absolute imports
                      (such as `from foo import bar`) are recommended in PEP8.
      max_linechars:  Maximum linewidth, beyond which the import statement string will
                      be multilined with `multilinify_import_stmt_str`.
    """
    alias_obj_list = []
    assert type(alias_list) is list, "alias_list must be a list"
    for alias_pair in alias_list:
        if type(alias_pair) is str:
            alias_pair = [alias_pair]
        assert len(alias_pair) > 0, "Cannot import using an empty string"
        assert type(alias_pair[0]) is str, "Import alias name must be a string"
        if len(alias_pair) < 2:
            alias_pair.append(None)
        al = ast.alias(*alias_pair[0:2])
        alias_obj_list.append(al)
    if import_src is None:
        ast_imp_stmt = ast.Import(alias_obj_list)
    else:
        import_level = len(import_src) - len(import_src.lstrip("."))
        import_src = import_src.lstrip(".")
        ast_imp_stmt = ast.ImportFrom(import_src, alias_obj_list, level=import_level)
    import_stmt_str = to_source(ast.Module([ast_imp_stmt]))
    if len(import_stmt_str.rstrip(nl)) > max_linechars:
        return multilinify_import_stmt_str(import_stmt_str)
    else:
        return import_stmt_str


def multilinify_import_stmt_str(import_stmt_str, indent_spaces=4, trailing_comma=True):
    """
    Takes a single line import statement and turns it into a multiline string.
    Will raise a `ValueError` if given a multiline string (a newline at the end
    of the string is permitted).

    This function is written in expectation of the output of `get_import_stmt_str`,
    and is not intended to process all potential ways of writing an import statement.

        import_stmt_str:  String of Python code carrying out an import statement.
        indent_spaces:    Number of spaces to indent by in multiline format.
        trailing_comma:   Whether to add a trailing comma to the final alias in a
                          multiline list of import aliases (default: True)
    """
    import_stmt_str = import_stmt_str.rstrip(nl)
    n_nl = import_stmt_str.count(nl)
    if n_nl > 0:
        raise ValueError(f"{import_stmt_str} is not a single line string")
    imp_ast = ast.parse(import_stmt_str)
    assert type(imp_ast.body[0]) in [IType, IFType], "Not a valid import statement"
    tko = ASTTokens(import_stmt_str)
    first_tok = tko.tokens[0]
    import_tok = tko.find_token(first_tok, tok_type=1, tok_str="import")
    assert import_tok.type > 0, f"Unable to find import token in the given string"
    imp_preamble_str = import_stmt_str[: import_tok.endpos]
    post_import_tok = tko.tokens[import_tok.index + 1]
    imp_names_str = import_stmt_str[post_import_tok.startpos :]
    aliases = [(x.name, x.asname) for x in imp_ast.body[0].names]
    seen_comma_tok = None
    multiline_import_stmt_str = imp_preamble_str
    multiline_import_stmt_str += " (" + nl
    for al_i, (a_n, a_as) in enumerate(aliases):
        is_final_alias = al_i + 1 == len(aliases)
        if seen_comma_tok is None:
            # Get start of alias by either full name or first part of .-separated name
            al_n_tok = tko.find_token(import_tok, 1, tok_str=a_n.split(".")[0])
            assert al_n_tok.type > 0, f"Unable to find the token for {a_n}"
        else:
            al_n_tok = tko.find_token(seen_comma_tok, 1, tok_str=a_n.split(".")[0])
            assert al_n_tok.type > 0, f"Unable to find the token for {a_n}"
        al_startpos = al_n_tok.startpos
        if a_as is None:
            if is_final_alias:
                # There won't be a comma after this (it is the last import name token)
                al_endpos = al_n_tok.endpos
            else:
                comma_tok = tko.find_token(al_n_tok, tok_type=53, tok_str=",")
                if comma_tok.type == 0:
                    # Due to an error in asttokens, sometimes tok_type is given as 54
                    # although this should be an error (the failure tok_type is 0)
                    comma_tok = tko.find_token(al_n_tok, tok_type=54, tok_str=",")
                assert comma_tok.type > 0, f"Unable to find comma token"
                al_endpos = comma_tok.endpos
        else:
            al_as_tok = tko.find_token(al_n_tok, tok_type=1, tok_str=a_as)
            assert al_as_tok.type > 0, f"Unable to find the token for {a_as}"
            if is_final_alias:
                # There won't be a comma after this (it's the last import asname token)
                al_endpos = al_as_tok.endpos
            else:
                comma_tok = tko.find_token(al_as_tok, tok_type=53, tok_str=",")
                if comma_tok.type == 0:
                    # Due to an error in asttokens, sometimes tok_type is given as 54
                    # although this should be an error (the failure tok_type is 0)
                    comma_tok = tko.find_token(al_n_tok, tok_type=54, tok_str=",")
                assert comma_tok.type > 0, f"Unable to find comma token"
                al_endpos = comma_tok.endpos
        alias_chunk = import_stmt_str[al_startpos:al_endpos]
        if is_final_alias:
            if trailing_comma:
                alias_chunk += ","
        else:
            seen_comma_tok = comma_tok
        multiline_import_stmt_str += (" " * indent_spaces) + alias_chunk + nl
    # Finally, verify that the end of the tokenised string was reached
    assert al_endpos == tko.tokens[-1].endpos, "Did not tokenise to the end of string"
    # No need to further slice the input string, return the final result
    multiline_import_stmt_str += ")" + nl
    return multiline_import_stmt_str


def colour_imp_stmt(imp_stmt, lines):
    """
    Summary: get a string which when printed will show the separate parts of an
    import statement in different colours (preamble in blue, alias names in red,
    alias asnames in purple, the word "as" itself in yellow, commas between import
    aliases in light green, and post-matter (a bracket) in light red.

    For an import statement within an asttokens-annotated AST, which comes with
    all subnodes annotated with first and last token start/end positional information,
    access all the tokens corresponding to the import statement name(s) and asname(s).
    
    Do this using a list of lines (i.e. a list of strings, each of which is a line),
    the subset of which corresponding to the import statement `imp_stmt` are given
    by its `first_token.start` and `last_token.end` attributes (in each case, the
    attribute is a tuple of `(line, column)` numbers, and it is conventional to store
    these as a 1-based index, so to cross-reference to a 0-based index of the list
    of lines we decrement this value and store as `imp_startln` and `imp_endln`).
    The subset of lines corresponding to `imp_stmt` is then assigned as `nodelines`,
    and we join this into a single string as `nodestring`.

    Then a new ASTTokens object, `tko`, can be made by parsing `nodestring`, on which
    the `find_tokens` method provides access to each name/asname one at a time, when
    matched to the name/asname string. These name/asname strings are available
    within the `imp_stmt` object via its `names` attribute, which is a list of
    `ast.alias` class instances, each of which has both a `name` and `asname` attribute
    (the latter of which is `None` if no asname is given for the import name).

    `find_tokens` returns a token with attribute `type` of value `1` for a name (1 is
    the index of "NAME" in the `token.tok_name` dictionary), and `startpos`/`endpos`
    attributes (integers which indicate the string offsets within `nodestring`).

    These `startpos` integers are an efficient way to store this list of tokens
    (the "NAME" tokens corresponding to import statement alias names and asnames),
    and so even though it would be possible to store all tokens, I choose to simply
    re-access them with the `tko.get_token_from_offset(startpos)` method.

    At the moment, I only re-access these tokens to retrieve their `endpos` (end
    position offset), which is also an integer and could also be stored easily
    without much problem, however for the sake of clarity I prefer to re-access
    the entire token and not have to construct an arbitrary data structure for
    storing the start and end positions (which could get confusing).

    Lastly, I construct a colourful string representation of the import statement
    by using these start positions and re-retrieved end positions to pull out
    and modify (using the `mvdef.colours`⠶`colour_str` function) the names and asnames
    (names are coloured red, asnames are coloured purple), and use string slicing
    to swap the ranges that the names and asnames were in in the original
    `nodestring` for these colourful replacements.

    The end result, `modified_nodestring` is then returned, which will then
    display in colour on Linux and OSX (I don't think Windows supports ANSI codes,
    so I made `colour_str` only apply on these platforms).
    """
    assert "first_token" in imp_stmt.__dir__(), "Not an asttokens-annotated AST node"
    assert type(imp_stmt) in [IType, IFType], "Not an import statement"
    is_from = type(imp_stmt) is IFType
    imp_startln = imp_stmt.first_token.start[0] - 1  # Use 0-based line index
    imp_endln = imp_stmt.last_token.end[0] - 1  # to match list of lines
    nodelines = lines[imp_startln : (imp_endln + 1)]
    n_implines = len(nodelines)
    nodestring = "".join(nodelines)
    tko = ASTTokens(nodestring)
    new_nodelines = [list() for _ in range(n_implines)]
    # Subtract the import statement start position from the name or asname
    # token start position to get the offset, then use the offset to extract
    # a range of text from the re-parsed ASTTokens object for the nodestring
    # corresponding to the import name or asname in question.
    imp_startpos = imp_stmt.first_token.startpos
    alias_starts = []
    for alias in imp_stmt.names:
        al_n, al_as = alias.name, alias.asname
        # 1 is the key for "NAME" in Python's tokens.tok_name
        s = [tko.find_token(tko.tokens[0], 1, tok_str=al_n).startpos]
        if al_as is not None:
            s.append(tko.find_token(tko.tokens[0], 1, tok_str=al_as).startpos)
        alias_starts.append(s)
    assert len(alias_starts) > 0, "An import statement cannot import no names!"
    assert alias_starts[0][0] > 0, "An import statement cannot begin with a name!"
    modified_nodestring = ""
    # -------------------------------------------------------------------------
    # Now set up colour definitions for the modified import statement string
    name_colour, asname_colour = ["red", "purple"]
    pre_colour, post_colour = ["light_blue", "light_red"]
    as_string_colour = "yellow"
    comma_colour = "light_green"
    # -------------------------------------------------------------------------
    first_import_name_startpos = alias_starts[0][0]
    pre_str = nodestring[:first_import_name_startpos]
    modified_nodestring += colour(pre_colour, pre_str)
    seen_endpos = first_import_name_startpos
    # (Could add a try/except here to verify colours are in colour dict if modifiable)
    for al_i, alias_start_list in enumerate(alias_starts):
        for al_j, al_start in enumerate(alias_start_list):
            if seen_endpos < al_start:
                # There is an intervening string, append it to modified_nodestring
                intervening_str = nodestring[seen_endpos:al_start]
                if al_j > 0:
                    # This is the word "as", which comes between a name and an asname
                    modified_nodestring += colour(as_string_colour, intervening_str)
                else:
                    if al_i > 0:
                        assert "," in intervening_str, "Import aliases not comma-sep.?"
                        modified_nodestring += colour(comma_colour, intervening_str)
                    else:
                        modified_nodestring += intervening_str
            # Possible here to distinguish between names and asnames by al_j if needed
            is_asname = bool(al_j)  # al_j is 0 if name, 1 if asname
            name_tok = tko.get_token_from_offset(al_start)
            assert name_tok.type > 0, f"No import name at {al_start} in {nodestring}"
            al_endpos = name_tok.endpos
            imp_name = nodestring[al_start:al_endpos]
            cstr_colour = [name_colour, asname_colour][al_j]
            cstr = colour(cstr_colour, imp_name)
            modified_nodestring += cstr
            seen_endpos = al_endpos
    end_str = nodestring[seen_endpos:]
    modified_nodestring += colour(post_colour, end_str)
    return modified_nodestring


def get_imported_name_sources(trunk, report=True):
    import_types = [IType, IFType]
    imports = [n for n in trunk if type(n) in import_types]
    imp_name_lines, imp_name_dict_list = annotate_imports(imports, report=report)
    imported_names = {}
    for ld in imp_name_lines:
        ld_n = imp_name_lines.get(ld).get("n")
        line_n = imp_name_dict_list[ld_n]
        imp_src = [x for x in list(line_n.items()) if x[1] == ld][0]
        imported_names[ld] = imp_src
    return imported_names


def get_module_srcs(imports):
    ifr_srcs = []
    for imp in imports:
        if type(imp) == IFType:
            ifr_srcs.append(imp.module)
        else:
            ifr_srcs.append(None)
    return ifr_srcs


def count_imported_names(nodes):
    """
    Return an integer for a single node (0 if not an import statement),
    else return a list of integers for a list of AST nodes.
    """
    if type(nodes) is not list:
        if type(nodes) in [IType, IFType]:
            return len(nodes.names)
        else:
            assert ast.stmt in type(nodes).mro(), f"{nodes} is not an AST statement"
            return 0
    counts = []
    for node in nodes:
        if type(node) in [IType, IFType]:
            counts.append(len(node.names))
        else:
            assert ast.stmt in type(nodes).mro(), f"{nodes} is not an AST statement"
            counts.append(0)
    return counts


def annotate_imports(imports, report=True):
    """
    Produce two data structures from the list of import statements (the statements
    of type ast.Import and ast.ImportFrom in the source program's AST),
      imp_name_linedict:  A dictionary whose keys are all the names imported by the
                          program (i.e. the names which they are imported as: the
                          asname if one is used), and whose value for each name
                          is a dictionary of keys (`n`, `line`):
                            n:    [0-based] index of the import statement importing
                                  the name, over the set of all import statements.
                            line: [1-based] line number of the file of the import
                                  statement importing the name. Note that it may
                                  not correspond to the line number on which the
                                  name is given, only to the import function call.
      imp_name_dict_list: List of one OrderedDict per import statement, whose keys
                          are the full import path (with multi-part paths conjoined
                          by a period `.`) and the values of which are the names
                          that these import paths are imported as (either the asname
                          or else just the terminal part of the import path). The
                          OrderedDict preserves the per-line order of the imported
                          names.
    """
    report_VERBOSE = False  # Silencing debug print statements
    # This dictionary gives the import line it's on for cross-ref with either
    # the imports list above or the per-line imported_name_dict
    imp_name_linedict = dict()  # Stores all names and their asnames
    imp_name_dict_list = []  # Stores one OrderedDict per AST import statement
    for imp_no, imp_line in enumerate(imports):
        imp_name_dict = OrderedDict()
        for imported_names in imp_line.names:
            name, asname = imported_names.name, imported_names.asname
            if type(imp_line) == IFType:
                assert imp_line.level == 0, "I've only encountered level 0 imports"
                fullname = ".".join([imp_line.module, name])
            else:
                fullname = name
            if asname is None:
                imp_name_dict[fullname] = name
                # Store both which import in the list of imports it's in
                # and the line number it's found on in the parsed file
                imp_name_linedict[name] = {"n": imp_no, "line": imp_line.lineno}
            else:
                imp_name_dict[fullname] = asname
                imp_name_linedict[asname] = {"n": imp_no, "line": imp_line.lineno}
        imp_name_dict_list.append(imp_name_dict)
    # Ensure that they each got all the names
    assert len(imp_name_dict_list) == len(imports)
    assert sum([len(d) for d in imp_name_dict_list]) == len(imp_name_linedict)
    if report_VERBOSE:
        print("The import name line dict is:")
        for ld in imp_name_linedict:
            # print(f"  {ld}: {imp_name_linedict.get(ld)}")
            pass
        print("The import name dict list is:")
        for ln in imp_name_dict_list:
            print(ln)
    return imp_name_linedict, imp_name_dict_list


def imp_def_subsets(mvdefs, nonmvdefs, report=True):
    """
    Given the list of mvdef_names and nonmvdef_names, construct the subsets:
      mv_imports:      imported names used by the functions to move,
      nonmv_imports:   imported names used by the functions not to move,
      mutual_imports:  imported names used by both the functions to move and
                        the functions not to move
    """
    report_VERBOSE = False  # Silencing debug print statements
    mvdefs_names = set().union(*[list(mvdefs[x]) for x in mvdefs])
    nonmvdefs_names = set().union(*[list(nonmvdefs[x]) for x in nonmvdefs])
    mv_imports = mvdefs_names - nonmvdefs_names
    nonmv_imports = nonmvdefs_names - mvdefs_names
    mutual_imports = mvdefs_names.intersection(nonmvdefs_names)
    assert mv_imports.isdisjoint(nonmv_imports), "mv/nonmv_imports intersect!"
    assert mv_imports.isdisjoint(mutual_imports), "mv/mutual imports intersect!"
    assert nonmv_imports.isdisjoint(mutual_imports), "nonmv/mutual imports intersect!"
    if report_VERBOSE:
        print(
            f"mv_imports: {mv_imports}",
            f", nonmv_imports: {nonmv_imports}",
            f", mutual_imports: {mutual_imports}",
            sep="",
        )
    all_defnames = set().union(*[mvdefs_names, nonmvdefs_names])
    all_def_imports = set().union(*[mv_imports, nonmv_imports, mutual_imports])
    assert sorted(all_defnames) == sorted(all_def_imports), "Defnames =/= import names"
    return mv_imports, nonmv_imports, mutual_imports
