import ast
from collections import OrderedDict


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
    report_VERBOSE = False  # Silencing debug print statements
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
            print(f"  {ld}: {imp_name_linedict.get(ld)}")
    return imp_name_linedict, imp_name_dict_list


def imp_def_subsets(mvdefs, nonmvdefs, report=True):
    """
    Given the list of mvdef_names and nonmvdef_names, construct the subsets:
      mv_imports:      imported names used by the functions to move,
      nonmv_imports:   imported names used by the functions not to move,
      mutual_imports:  imported names used by both the functions to move and
                        the functions not to move
    """
    report_VERBOSE = False # Silencing debug print statements
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
