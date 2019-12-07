import ast
from pathlib import Path
from collections import OrderedDict
import builtins
from src.display import colour_str as colour
from asttokens import ASTTokens
from src.editor import edit_defs
from src.deprecations import pprint_def_names


def ast_parse(py_file, mv_list=[], report=True, edit=False, backup=True):
    """
    Build and arse the Abstract Syntax Tree (AST) of a Python file, and either return
    a report of what changes would be required to move the mv_list of funcdefs out
    of it, or a report of the imports and funcdefs in general if no mv_list is
    provided (taken to indicate that the file is the target funcdefs are moving to),
    or make changes to the file (either newly creating one if no such file exists,
    or editing in place according to the reported import statement differences).

    If the py_file doesn't exist, it's being newly created by the move and obviously
    no report can be made on it: it has no funcdefs and no import statements, so
    all the ones being moved will be newly created.

    mv_list should be given if the file is the source of moved functions, and left
    empty (defaulting to value of []) if the file is the destination to move them to.
    
    If report is True, returns a string describing the changes
    to be made (if False, nothing is returned).
    
    If edit is True, files will be changed in place (note that this function does
    not actually do the editing, it just returns the edit agenda and uses the edit
    parameter as a sanity check to prevent wasted computation if neither edit nor
    report is True).

    If backup is True, files will be changed in place by calling src.backup.backup
    (obviously, be careful switching this setting off if report is True, as any
    changes made cannot be restored afterwards from this backup file).
    """
    assert True in (edit, report), "Nothing to do"
    extant = py_file.exists() and py_file.is_file()
    if extant:
        with open(py_file, "r") as f:
            fc = f.read()
            # a = ast
            nodes = ast.parse(fc).body

        imports = [n for n in nodes if type(n) in [ast.Import, ast.ImportFrom]]
        defs = [n for n in nodes if type(n) == ast.FunctionDef]
        # return imports, funcdefs
        edit_agenda = process_imports(py_file, mv_list, defs, imports, report)

        if mv_list == [] and report:
            # The mv_list is empty if it was not passed in at all, i.e. this indicates
            # no files are to be moved from py_file, i.e. they are moving into py_file
            # extant is True so non_mvdef is just all funcdefs for the file
            print(f"⇒ No functions to move from {colour('light_gray', py_file)}")
        elif mv_list != [] and report:
            print(f"⇒ Functions moving from {colour('light_gray',py_file)}: {mv_list}")
        elif report:
            print(f"⇒ Functions moving to {colour('light_gray', py_file)}")
        return edit_agenda
    elif mv_list == [] and report:
        # not extant so file doesn't exist (cannot produce a parsed AST)
        # however mv_list is [] so file must be dst
        print(
            f"⇒ Functions will move to {colour('light_gray', py_file)}"
            + " (it's being created from them)"
        )
        return
    else:
        raise ValueError(f"Can't move {mv_list} from {py_file} – it doesn't exist!")
    return


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
            print(f"  {ld}: {imp_name_linedict[ld]}")
    return imp_name_linedict, imp_name_dict_list


def find_assigned_args(fd):
    """
    Produce a list of the names in a function definition `fd` which are created
    by assignment operations (as identified via the function definition's AST).
    """
    args_indiv = []  # Arguments assigned individually, e.g. x = 1
    args_multi = []  # Arguments assigned from a tuple, e.g. x, y = (1,2)
    for a in fd.body:
        if type(a) is ast.Assign:
            assert len(a.targets) == 1, "Expected 1 target per ast.Assign"
            if type(a.targets[0]) is ast.Name:
                args_indiv.append(a.targets[0].id)
            elif type(a.targets[0]) is ast.Tuple:
                args_multi.extend([x.id for x in a.targets[0].elts])
    assigned_args = args_indiv + args_multi
    return assigned_args


def get_nondef_names(unused, import_annos, report=True):
    imp_name_lines, imp_name_dicts = import_annos
    # nondef_names is a dictionary keyed by the unused names (which were imported)
    nondef_names = dict([(x, {}) for x in unused])
    unknowns = [n for n in unused if n not in imp_name_lines]
    assert unknowns == [], f"These names could not be sourced: {unknowns}"
    # mv_imp_refs is the subset of imp_name_lines for movable funcdef names
    # These refs will lead to import statements being copied and/or moved
    uu_imp_refs = dict([[n, imp_name_lines.get(n)] for n in unused])
    for k in uu_imp_refs:
        n = uu_imp_refs.get(k).get("n")
        d = imp_name_dicts[n]
        n_i = [list(d.keys()).index(x) for x in d if d[x] == k][0]
        assert n_i >= 0, f"Movable name {k} not found in import name dict"
        # Store index in case of multiple imports per import statement line
        uu_imp_refs.get(k)["n_i"] = n_i
        uu_name_entry = nondef_names.get(k)
        n = uu_imp_refs.get(k).get("n")
        uu_name_entry["n"] = n
        uu_name_entry["n_i"] = n_i
        uu_name_entry["line"] = uu_imp_refs.get(k).get("line")
        uu_name_entry["import"] = list(imp_name_dicts[n].keys())[n_i]
    return nondef_names


def get_def_names(func_list, funcdefs, import_annos, report=True):
    imp_name_lines, imp_name_dicts = import_annos
    def_names = dict([(x, {}) for x in func_list])
    for m in func_list:
        fd_names = set()
        assert m in [f.name for f in funcdefs], f"No function '{m}' is defined"
        fd = funcdefs[[f.name for f in funcdefs].index(m)]
        fd_params = [a.arg for a in fd.args.args]
        assigned_args = find_assigned_args(fd)
        for ast_statement in fd.body:
            for node in list(ast.walk(ast_statement)):
                if type(node) == ast.Name:
                    n_id = node.id
                    if n_id not in dir(builtins) + fd_params + assigned_args:
                        fd_names.add(n_id)
        def_names[m] = dict([(x, {}) for x in sorted(fd_names)])
        # All names successfully found and can finish if remaining names are
        # in the set of funcdef names, comparing them tothe import statements
        unknowns = [n for n in fd_names if n not in imp_name_lines]
        assert unknowns == [], f"These names could not be sourced: {unknowns}"
        # mv_imp_refs is the subset of imp_name_lines for movable funcdef names
        # These refs will lead to import statements being copied and/or moved
        mv_imp_refs = dict([(n, imp_name_lines.get(n)) for n in fd_names])
        for k in mv_imp_refs:
            n = mv_imp_refs.get(k).get("n")
            d = imp_name_dicts[n]
            n_i = [list(d.keys()).index(x) for x in d if d[x] == k][0]
            assert n_i >= 0, f"Movable name {k} not found in import name dict"
            # Store index in case of multiple imports per import statement line
            mv_imp_refs.get(k)["n_i"] = n_i
            fd_name_entry = def_names.get(m).get(k)
            n = mv_imp_refs.get(k).get("n")
            fd_name_entry["n"] = n
            fd_name_entry["n_i"] = n_i
            fd_name_entry["line"] = mv_imp_refs.get(k).get("line")
            fd_name_entry["import"] = list(imp_name_dicts[n].keys())[n_i]
    return def_names


def parse_mv_funcs(mv_list, funcdefs, imports, report=True, edit=False):
    """
    Produce a dictionary, `mvdef_names`, whose keys are the list of functions
    to move (i.e. the list `mv_list` becomes the list of keys of `mvdef_names`),
    and the value of which at each key (for a key `m` which indicates the name
    of one of the functions given in `mv_list` to move) is another dictionary,
    keyed by the full set of names used in that function (`m`) which rely upon
    import statements (i.e. are not builtin names nor passed as parameters to
    the function, nor assigned in the body of the function), and the value
    of which at each name is a final nested dictionary whose keys are always:
      n:      The [0-based] index of the name's source import statement in the
              AST list of all ast.Import and ast.ImportFrom.
      n_i:    The [0-based] index of the name's source import statement within
              the one or more names imported by the source import statement at
              index n (e.g. for `pi` in `from numpy import e, pi`, `n_i` = 1).
      line:   The [1-based] line number of the import statement as given in its
              corresponding AST entry, which indicates the line number of the
              `import` call, not [necessarily] that of the name (i.e. the name
              may not be located there in the file for multi-line imports).
      import: The path of the import statement, which may contain multiple
              parts conjoined by `.` (e.g. `matplotlib.pyplot`)
    
    I.e. the dictionary with entries accessed as `mvdef_names.get(m).get(k)`
    for `m` in `mv_list` and `k` in the subset of AST-identified imported names
    in the function with  if f.name not in mv_listname `m` in the list of
    function definitions `funcdefs`. This access is handed off to the helper
    function `get_def_names`.

    For the names that were imported but not used, the dictionary is not keyed
    by function (as there are no associated functions), and instead the entries
    are accessed as `nondef_names.get(k)` for `k` in `unused_names`. This access
    is handed off to the helper function `get_nondef_names`.
    """
    report_VERBOSE = False  # Silencing debug print statements
    import_annos = annotate_imports(imports, report=report)
    mvdef_names = get_def_names(mv_list, funcdefs, import_annos, report=report)
    if report_VERBOSE:
        print("mvdef names:")
        pprint_def_names(mvdef_names)
    # ------------------------------------------------------------------------ #
    # Next obtain nonmvdef_names
    nomv_list = [f.name for f in funcdefs if f.name not in mv_list]
    nonmvdef_names = get_def_names(nomv_list, funcdefs, import_annos, report=report)
    if report_VERBOSE:
        print("non-mvdef names:")
        pprint_def_names(nonmvdef_names)
    # ------------------------------------------------------------------------ #
    # Next obtain unused_names
    mv_set = set().union(*[mvdef_names.get(x).keys() for x in mvdef_names])
    nomv_set = set().union(*[nonmvdef_names.get(x).keys() for x in nonmvdef_names])
    unused_names = list(set(list(import_annos[0].keys())) - mv_set - nomv_set)
    nondef_names = get_nondef_names(unused_names, import_annos, report=report)
    if report_VERBOSE:
        print("non-def names (imported but not used in any function def):")
        pprint_def_names(nondef_names, no_funcdef_list=True)
    return mvdef_names, nonmvdef_names, nondef_names


def imp_subsets(mvdefs, nonmvdefs, report=True):
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
            "mv_imports: ",
            mv_imports,
            ", nonmv_imports: ",
            nonmv_imports,
            ", mutual_imports: ",
            mutual_imports,
            sep="",
        )
    all_defnames = set().union(*[mvdefs_names, nonmvdefs_names])
    all_imports = set().union(*[mv_imports, nonmv_imports, mutual_imports])
    assert sorted(all_defnames) == sorted(all_imports), "Defnames =/= import names"
    return mv_imports, nonmv_imports, mutual_imports


def describe_def_name_dict(name, name_dict):
    """
    Wrapper function that returns a string presenting the content of a dict entry
    with import statement indexes, line number, and import source path. These
    fields are instantiated within `get_def_names`, which in turn is assigned to
    the variable `mvdef_names` within `parse_mv_funcs`.
    
    The output of `parse_mv_funcs` gets passed to `construct_edit_agenda` by the
    wrapper function `process_imports`, and `construct_edit_agenda` iterates over
    the subsets within the output of `parse_mv_funcs`, at which stage it's
    necessary to produce a nice readable output, calling `describe_mvdef_name_dict`.
    """
    # Extract: import index; intra-import index; line number; import source
    n, n_i, ln, imp_src = [name_dict.get(x) for x in ["n", "n_i", "line", "import"]]
    desc = f"(import {n}:{n_i} on line {ln}) {name} ⇒ <{imp_src}>"
    return desc


def construct_edit_agenda(filepath, m_names, nm_names, rm_names, report=True):
    """
    First, given the lists of mvdef names (m_names) and non-mvdef names
    (nm_names), construct the subsets:

      mv_imps:  imported names used by the functions to move (only in mvdef_names),
      nm_imps:  imported names used by the functions not to move (only in
                nonmvdef_names),
      mu_imps:  imported names used by both the functions to move and the
                functions not to move (in both mvdef_names and nonmvdef_names)

    Potentially 'as a dry run' (if this is being called by process_imports and its
    parameter edit is False), report how to remove the import statements or statement
    sections which import mv_inames, do nothing to the import statements which import
    nonmv_inames, and copy the import statements which import mutual_inames (as both
    src and dst need them). The format of this reporting should be at the level of
    file changes, and as such the filepath is accessed (read only here) to provide
    process_imports the necessary 'edit agenda' to either report (if report is True)
    and/or carry out (if edit is True for process_imports).

    For clarity, note that this function does **not** edit anything itself, it just
    describes how it would be possible to carry out the required edits at the level
    of Python file changes.
    """
    edit_agenda = {"move": [], "keep": [], "copy": [], "lose": []}
    # mv_inames is mv_imports returned from imp_subsets, and so on
    mv_imps, nm_imps, mu_imps = imp_subsets(m_names, nm_names, report=report)
    # Iterate over each imported name, i, in the subset of import names to move
    for i in mv_imps:
        assert i in set().union(*[m_names.get(k) for k in m_names]), f"{i} not found"
        i_dict = [m_names.get(k) for k in m_names if i in m_names.get(k)][0].get(i)
        if report:
            i_dict_desc = describe_def_name_dict(i, i_dict)
            print(colour("green", f" ⇢ ⇢ ⇢ MOVE  ⇢ ⇢ ⇢ {i_dict_desc}"))
        edit_agenda.get("move").append({i: i_dict})
    for i in nm_imps:
        assert i in set().union(*[nm_names.get(k) for k in nm_names]), f"{i} not found"
        i_dict = [nm_names.get(k) for k in nm_names if i in nm_names.get(k)][0].get(i)
        if report:
            i_dict_desc = describe_def_name_dict(i, i_dict)
            print(colour("dark_gray", f"⇠ ⇠ ⇠  KEEP ⇠ ⇠ ⇠  {i_dict_desc}"))
        edit_agenda.get("keep").append({i: i_dict})
    for i in mu_imps:
        assert i in set().union(*[m_names.get(k) for k in m_names]), f"{i} not found"
        i_dict = [m_names.get(k) for k in m_names if i in m_names.get(k)][0].get(i)
        if report:
            i_dict_desc = describe_def_name_dict(i, i_dict)
            print(colour("light_blue", f"⇠⇢⇠⇢⇠⇢ COPY ⇠⇢⇠⇢⇠⇢ {i_dict_desc}"))
        edit_agenda.get("copy").append({i: i_dict})
    for i in rm_names:
        i_dict = rm_names.get(i)
        if report:
            i_dict_desc = describe_def_name_dict(i, i_dict)
            print(colour("red", f" ✘ ✘ ✘ LOSE ✘ ✘ ✘  {i_dict_desc}"))
        edit_agenda.get("lose").append({i: i_dict})
    return edit_agenda


def process_imports(fp, mv_list, defs, imports, report=True, edit=False):
    """
    Handle the hand-off to dedicated functions to go from the mv_list of functions
    to move, first deriving lists of imported names which belong to the mv_list and
    the non-mv_list functions (using `parse_mv_funcs`), then constructing an
    'edit agenda' (using `construct_edit_agenda`) which describes [and optionally
    reports] the changes to be made at the file level, in terms of move/keep/copy
    operations on individual import statements between the source and destination
    Python files.

      fp:       File path to the file to be processed
      mv_list:  List of functions to be moved
      defs:     List of all function definitions in the file
      report:   Whether to print a report during the program (default: True)
      edit:     Whether to change the file in place (default: False)
    """
    # mv_nmv_defs is a tuple of (mvdefs, nonmvdefs) returned from parse_mv_funcs
    mv_nmv_defs = parse_mv_funcs(mv_list, defs, imports, report=report, edit=edit)
    edit_agenda = construct_edit_agenda(fp, *mv_nmv_defs, report=report)
    return edit_agenda
