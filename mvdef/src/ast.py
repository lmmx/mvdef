import ast
from pathlib import Path
from collections import OrderedDict
import builtins


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
    if report:
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


def get_def_names(func_list, funcdefs, import_annos, report=True, edit=False):
    imp_name_lines, imp_name_dicts = import_annos
    def_names = dict(zip(func_list, [{}] * len(func_list)))
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
        def_names[m] = dict(zip(sorted(fd_names), [{} for x in range(len(fd_names))]))
        # All names successfully found and can finish if remaining names are
        # in the set of funcdef names, comparing them tothe import statements
        unknowns = [n for n in fd_names if n not in imp_name_lines]
        assert unknowns == [], f"These names could not be sourced: {unknowns}"
        # mv_imp_refs is the subset of imp_name_lines for movable funcdef names
        # These refs will lead to import statements being copied and/or moved
        mv_imp_refs = dict([[n, imp_name_lines.get(n)] for n in fd_names])
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
        # if report:
        #    print(f"The names in {m} are: {fd_names}")
        if edit:
            # Go do the file editing
            pass
    return def_names


def pprint_def_names(def_names):
    for n in def_names:
        print(f"  {n}:::" + "{")
        for m in def_names.get(n):
            print(f"    {m}: {def_names.get(n)[m]}")
        print("  }")


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
    
    I.e. the dictionary `mvdef_names[m][k]` for `m` in `mv_list` and `k` in the
    subset of AST-identified imported names in the function with  if f.name not in mv_listname `m` in
    the list of function definitions `funcdefs`.
    """
    imp_annos = annotate_imports(imports, report=report)
    mvdef_names = get_def_names(mv_list, funcdefs, imp_annos, report, edit)
    if report:
        print("mvdef names:")
        pprint_def_names(mvdef_names)
    # -------------------------------------------------------------------------#
    # Next obtain nonmvdef_names
    nomv_list = [f.name for f in funcdefs if f.name not in mv_list]
    nonmvdef_names = get_def_names(nomv_list, funcdefs, imp_annos, report, edit)
    if report:
        print("non-mvdef names:")
        pprint_def_names(nonmvdef_names)
    return mvdef_names, nonmvdef_names


def ast_parse(py_file, mv_list=[], report=False, edit=False, backup=True):
    """
    Parse the Abstract Syntax Tree (AST) of a Python file, and either return a
    report of what changes would be required to move the mv_list of funcdefs out
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
    
    If edit is True, files will be changed in place.

    If backup is True, files will be changed in place by calling src.backup.backup
    (obviously, be careful switching this setting off if report is True, as any
    changes made cannot be restored afterwards from this backup file).
    """
    assert True in (edit, report), "Nothing to do"
    extant = py_file.exists() and py_file.is_file()
    if extant:
        with open(py_file, "r") as f:
            fc = f.read()
            nodes = ast.parse(fc).body

        imports = [n for n in nodes if type(n) in [ast.Import, ast.ImportFrom]]
        defs = [n for n in nodes if type(n) == ast.FunctionDef]
        # return imports, funcdefs

        if mv_list == [] and report:
            # The mv_list is empty if it was not passed in at all, i.e. this indicates
            # no files are to be moved from py_file, i.e. they are moving into py_file
            # extant is True so non_mvdef is just all funcdefs for the file
            print(f"⇒ No functions to move from {py_file}")
        elif mv_list != [] and report:
            print(f"⇒ Functions moving from {py_file}: {mv_list}")
        elif report:
            print(f"⇒ No functions moving from {py_file} (presumably going to it)")

        mvdefs, nonmvdefs = parse_mv_funcs(mv_list, defs, imports, report, edit)
        mvdefs_names = set().union(*[list(mvdefs[x]) for x in mvdefs])
        nonmvdefs_names = set().union(*[list(nonmvdefs[x]) for x in nonmvdefs])
        mv_imports = mvdefs_names - nonmvdefs_names
        nonmv_imports = nonmvdefs_names - mvdefs_names
        mutual_imports = mvdefs_names.intersection(nonmvdefs_names)
        print("mv_imports:", mv_imports)
        print("nonmv_imports:", nonmv_imports)
        print("mutual_imports:", mutual_imports)
    elif mv_list == [] and report:
        print(f"⇒ No functions moving from {py_file} (it's being created from them)")
    return

def spare_mvdef_func():
    """
    Wrote this on a misunderstanding of what mvdef_import should be, but might reuse
    this code for editing the entries(?) so hang onto it for access to the AST in case
    I want to look at line numbers again(?) Otherwise throw this code away when ready.
    """
    fd_info = mvdefs.get(fd)
    print(f"fd_info: {fd_info}")
    for name in fd_info:
        print(f"name: {name}")
        fdn_info = fd_info.get(name)
        fdn_n = fdn_info.get("n")
        fdn_ni = fdn_info.get("n_i")
        print(f"fdn_info: {fdn_info}")
        print(f"imports[n={fdn_n}]: {imports[fdn_n]}")
        if len(imports[fdn_n].names) > 1:
            tupname = imports[fdn_n].names[fdn_ni]
            print(f"imports[n={fdn_n}].names[n_i={fdn_ni}]: {tupname}")
            print(f"⇒⇒⇒ {tupname.name} as {tupname.asname}")
