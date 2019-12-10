import ast
from astor import to_source
from asttokens import ASTTokens
from collections import OrderedDict
from src.colours import colour_str as colour


def get_import_stmt_str(alias_list, imp_src=None, max_linechars=88):
    """
    Construct an import statement by building an AST, convert it to source using
    astor.to_source, and then return the string.

      alias_list:   List of strings to use as ast.alias `name`, and optionally also
                    `asname entries. If only one name is listed per item in the
                    alias_list, the `asname` will be instantiated as None.
      imp_src:      If provided, the import statement will be use the
                    `ast.ImportFrom` class, otherwise it will use `ast.Import`.
                    Relative imports are permitted for "import from" statements
                    (such as `from ..foo import bar`) however absolute imports
                    (such as `from foo import bar`) are recommended in PEP8.

    I don't think it's possible to specify the line width?
    """
    alias_obj_list = []
    assert type(alias_list) is list, "alias_list must be a list"
    for alias_pair in alias_list:
        if type(alias_pair) is str:
            alias_pair = [alias_pair]
        assert len(alias_pair) > 0, "Cannot import using an empty string"
        assert type(alias_pair[0]) is str, "Import alias name must be a string"
        if len(alias_pair) < 2: alias_pair.append(None)
        al = ast.alias(*alias_pair[0:2])
        alias_obj_list.append(al)
    if imp_src is None:
        ast_import_stmt = ast.Import(alias_obj_list)
    else:
        import_level = len(imp_src) - len(imp_src.lstrip('.'))
        imp_src = imp_src.lstrip('.')
        ast_import_stmt = ast.ImportFrom(imp_src, alias_obj_list, level=import_level)
    import_stmt_str = to_source(ast.Module([ast_import_stmt]))
    return import_stmt_str


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
    and modify (using the `src.colours`⠶`colour_str` function) the names and asnames
    (names are coloured red, asnames are coloured purple), and use string slicing
    to swap the ranges that the names and asnames were in in the original
    `nodestring` for these colourful replacements.

    The end result, `modified_nodestring` is then returned, which will then
    display in colour on Linux and OSX (I don't think Windows supports ANSI codes,
    so I made `colour_str` only apply on these platforms).
    """
    assert 'first_token' in imp_stmt.__dir__(), "Not an asttokens-annotated AST node"
    assert type(imp_stmt) in [ast.Import, ast.ImportFrom], "Not an import statement"
    is_from = type(imp_stmt) is ast.ImportFrom
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
    import_types = [ast.Import, ast.ImportFrom]
    imports = [n for n in trunk if type(n) in import_types]
    imp_name_lines, imp_name_dict_list = annotate_imports(imports, report=report)
    imported_names = {}
    for ld in imp_name_lines:
        ld_n = imp_name_lines.get(ld).get("n")
        line_n = imp_name_dict_list[ld_n]
        imp_src = [x for x in list(line_n.items()) if x[1] == ld][0]
        imported_names[ld] = imp_src
    return imported_names


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
    report_VERBOSE = True  # Silencing debug print statements
    # This dictionary gives the import line it's on for cross-ref with either
    # the imports list above or the per-line imported_name_dict
    imp_name_linedict = dict()  # Stores all names and their asnames
    imp_name_dict_list = []  # Stores one OrderedDict per AST import statement
    for imp_no, imp_line in enumerate(imports):
        imp_name_dict = OrderedDict()
        for imported_names in imp_line.names:
            name, asname = imported_names.name, imported_names.asname
            if type(imp_line) == ast.ImportFrom:
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
