import ast
from asttokens import ASTTokens
import builtins
from pathlib import Path
from .agenda_util import pprint_agenda
from .deprecations import pprint_def_names
from .import_util import get_imported_name_sources, annotate_imports, imp_def_subsets

__all__ = ["ast_parse", "process_ast", "find_assigned_args", "get_extradef_names", "get_nondef_names", "get_def_names", "parse_mv_funcs"]

def ast_parse(fp, mvdefs=[], transfers={}, report=True):
    """
    Build and arse the Abstract Syntax Tree (AST) of a Python file, and either return
    a report of what changes would be required to move the mvdefs subset of all
    function definitions out of it, or a report of the imports and funcdefs in general
    if no mvdefs is provided (taken to indicate that the file is the target funcdefs
    are moving to), or make changes to the file (either newly creating one if no such
    file exists, or editing in place according to the reported import statement
    differences).

    If the Python file `fp` doesn't exist (which can be checked directly as it's a
    Path object), it's being newly created by the move and obviously no report can
    be made on it: it has no funcdefs and no import statements, so all the ones being
    moved will be newly created.

    mvdefs should be given if the file is the source of moved functions, and left
    empty (defaulting to value of []) if the file is the destination to move them to.
    
    If report is True, returns a string describing the changes
    to be made (if False, nothing is returned).
    
    If backup is True, files will be changed in place by calling mvdef.backup.backup
    (obviously, be careful switching this setting off if report is True, as any
    changes made cannot be restored afterwards from this backup file).
    """
    extant = fp.exists() and fp.is_file()
    if extant:
        with open(fp, "r") as f:
            fc = f.read()
            # a = ast
            trunk = ast.parse(fc).body

        # return imports, funcdefs
        edit_agenda = process_ast(fp, mvdefs, trunk, transfers, report)
        return edit_agenda
    elif mvdefs == []:
        # not extant so file doesn't exist (cannot produce a parsed AST)
        # however mvdefs is [] so file must be dst, return value of None
        return
    else:
        raise ValueError(f"Can't move {mvdefs} from {fp} – it doesn't exist!")
    return


def process_ast(fp, mvdefs, trunk, transfers={}, report=True):
    """
    Handle the hand-off to dedicated functions to go from the mvdefs of functions
    to move, first deriving lists of imported names which belong to the mvdefs and
    the non-mvdefs functions (using `parse_mv_funcs`), then constructing an
    'edit agenda' (using `process_ast`) which describes [and optionally
    reports] the changes to be made at the file level, in terms of move/keep/copy
    operations on individual import statements between the source and destination
    Python files.

      mvdefs:     List of functions to be moved
      trunk:      Tree body of the file's AST, which will be separated into
                  function definitions, import statements, and anything else.
      transfers:  List of transfers already determined to be made from the src
                  to the dst file (from the first call to ast_parse)
      report:     Whether to print a report during the program (default: True)

    -------------------------------------------------------------------------------
    
    First, given the lists of mvdef names (m_names) and non-mvdef names
    (nm_names), construct the subsets:

      mv_imps:  imported names used by the functions to move (only in mvdef_names),
      nm_imps:  imported names used by the functions not to move (only in
                nonmvdef_names),
      mu_imps:  imported names used by both the functions to move and the
                functions not to move (in both mvdef_names and nonmvdef_names)

    Potentially 'as a dry run' (if this is being called by process_ast and its
    parameter edit is False), report how to remove the import statements or statement
    sections which import mv_inames, do nothing to the import statements which import
    nonmv_inames, and copy the import statements which import mutual_inames (as both
    src and dst need them).

    Additionally, accept 'transfers' from a previously determined edit agenda,
    so as to "take" the "move" names, and "echo" the "copy" names (i.e. when
    receiving names marked by "move" and "copy", distinguish them to indicate
    they are being received by transfer [from src⇒dst file], for clarity).

    For clarity, note that this function does **not** edit anything itself, it just
    describes how it would be possible to carry out the required edits at the level
    of Python file changes.
    """
    # get_edit_agenda(m_names, nm_names, rm_names, transfers, report=True)
    m_names, nm_names, rm_names = parse_mv_funcs(mvdefs, trunk, report=report)
    imported_names = get_imported_name_sources(trunk, report=report)
    if report:
        print(f"• Determining edit agenda for {fp.name}:")
    agenda_categories = ["move", "keep", "copy", "lose", "take", "echo", "stay"]
    agenda = dict([(c, []) for c in agenda_categories])
    # mv_inames is mv_imports returned from imp_def_subsets, and so on
    mv_imps, nm_imps, mu_imps = imp_def_subsets(m_names, nm_names, report=report)
    # Iterate over each imported name, i, in the subset of import names to move
    for i in mv_imps:
        assert i in set().union(*[m_names.get(k) for k in m_names]), f"{i} not found"
        i_dict = [m_names.get(k) for k in m_names if i in m_names.get(k)][0].get(i)
        agenda.get("move").append({i: i_dict})
    for i in nm_imps:
        assert i in set().union(*[nm_names.get(k) for k in nm_names]), f"{i} not found"
        i_dict = [nm_names.get(k) for k in nm_names if i in nm_names.get(k)][0].get(i)
        agenda.get("keep").append({i: i_dict})
    for i in mu_imps:
        assert i in set().union(*[m_names.get(k) for k in m_names]), f"{i} not found"
        i_dict = [m_names.get(k) for k in m_names if i in m_names.get(k)][0].get(i)
        agenda.get("copy").append({i: i_dict})
    for i in rm_names:
        i_dict = rm_names.get(i)
        agenda.get("lose").append({i: i_dict})
    if transfers == {}:
        # Returning without transfers
        if report:
            pprint_agenda(agenda)
        return agenda
    # elif report:
    #    if len(agenda.get("lose")) > 0:
    #        print("• Resolving edit agenda conflicts:")
    # i is 'ready made' from a previous call to ast_parse, and just needs reporting
    for i in transfers.get("take"):
        k, i_dict = list(i.items())[0]
        agenda.get("take").append({k: i_dict})
    for i in transfers.get("echo"):
        k, i_dict = list(i.items())[0]
        agenda.get("echo").append({k: i_dict})
    # Resolve agenda conflicts: if any imports marked 'lose' are cancelled out
    # by any identically named imports marked 'take' or 'echo', change to 'stay'
    for i in agenda.get("lose"):
        k, i_dict = list(i.items())[0]
        imp_src = i_dict.get("import")
        if k in [list(x)[0] for x in agenda.get("take")]:
            t_i_dict = [x for x in agenda.get("take") if k in x][0].get(k)
            take_imp_src = t_i_dict.get("import")
            if imp_src != take_imp_src:
                continue
            # Deduplicate 'lose'/'take' k: replace both with 'stay'
            agenda.get("stay").append({k: i_dict})
            l_k_i = [list(x.values())[0] for x in agenda.get("lose")].index(i_dict)
            del agenda.get("lose")[l_k_i]
            t_k_i = [list(x.values())[0] for x in agenda.get("take")].index(t_i_dict)
            del agenda.get("take")[t_k_i]
        elif k in [list(x)[0] for x in agenda.get("echo")]:
            e_i_dict = [x for x in agenda.get("echo") if k in x][0].get(k)
            echo_imp_src = e_i_dict.get("import")
            if imp_src != echo_imp_src:
                continue
            # Deduplicate 'lose'/'echo' k: replace both with 'stay'
            agenda.get("stay").append({k: i_dict})
            l_k_i = [list(x.values())[0] for x in agenda.get("lose")].index(i_dict)
            del agenda.get("lose")[l_k_i]
            e_k_i = [list(x.values())[0] for x in agenda.get("echo")].index(e_i_dict)
            del agenda.get("echo")[e_k_i]
    # Resolve agenda conflicts: if any imports marked 'take' or 'echo' are cancelled
    # out by any identically named imports already present, change to 'stay'
    for i in agenda.get("take"):
        k, i_dict = list(i.items())[0]
        take_imp_src = i_dict.get("import")
        if k in imported_names:
            # Check the import source and asnames match
            imp_src = imported_names.get(k)[0]
            if imp_src != take_imp_src:
                # This means that the same name is being used by a different function
                raise ValueError(
                    f"Cannot move imported name '{k}', it is already "
                    + f"in use in {fp.name} ({take_imp_src} clashes with {imp_src})"
                )
                # (N.B. could rename automatically as future feature)
            # Otherwise there is simply a duplicate import statement, so the demand
            # to 'take' the imported name is already fulfilled.
            # Replace unnecessary 'take' with 'stay'
            agenda.get("stay").append({k: i_dict})
            t_k_i = [list(x.values())[0] for x in agenda.get("take")].index(i_dict)
            del agenda.get("take")[t_k_i]
    for i in agenda.get("echo"):
        k, i_dict = list(i.items())[0]
        echo_imp_src = i_dict.get("import")
        if k in imported_names:
            # Check the import source and asnames match
            imp_src = imported_names.get(k)[0]
            if imp_src != echo_imp_src:
                # This means that the same name is being used by a different function
                raise ValueError(
                    f"Cannot move imported name '{k}', it is already "
                    + f"in use in {fp.name} ({echo_imp_src} clashes with {imp_src})"
                )
                # (N.B. could rename automatically as future feature)
            # Otherwise there is simply a duplicate import statement, so the demand
            # to 'echo' the imported name is already fulfilled.
            # Replace unnecessary 'take' with 'stay'
            agenda.get("stay").append({k: i_dict})
            e_k_i = [list(x.values())[0] for x in agenda.get("echo")].index(i_dict)
            del agenda.get("echo")[e_k_i]
    if report:
        pprint_agenda(agenda)
    return agenda


def find_assigned_args(fd):
    """
    Produce a list of the names in a function definition `fd` which are created
    by assignment operations (as identified via the function definition's AST).
    """
    args_indiv = []  # Arguments assigned individually, e.g. x = 1
    args_multi = []  # Arguments assigned from a tuple, e.g. x, y = (1,2)
    for a in ast.walk(fd):
        if type(a) is ast.Assign:
            # Handle explicit assignments from use of the equals symbol
            assert len(a.targets) == 1, "Expected 1 target per ast.Assign"
            if type(a.targets[0]) is ast.Name:
                args_indiv.append(a.targets[0].id)
            elif type(a.targets[0]) is ast.Tuple:
                args_multi.extend([x.id for x in a.targets[0].elts])
        elif type(a) is ast.For:
            # Handle implicit assignments (ctx = Store) within for loops
            if type(a.target) is ast.Name:
                args_indiv.append(a.target.id)
            elif type(a.target) is ast.Tuple:
                for x in a.target.elts:
                    assert type(x) in [ast.Name, ast.Tuple], f"Unexpected target.elts"
                    if type(x) is ast.Name:
                        args_multi.append(x.id)
                    else:  # type(x) is ast.Tuple
                        for y in x.elts:
                            assert type(y) is ast.Name, f"Unexpected target.elts tuple"
                            args_multi.append(y.id)
            else:
                raise ValueError(f"{a.target} lacks the expected ast.Name statements")
        elif type(a) is ast.ListComp:
            # Handle implicit assignments within list comprehensions
            for g in a.generators:
                assert type(g) is ast.comprehension, f"{a} not ast.comprehension type"
                if type(g.target) is ast.Name:
                    args_indiv.append(g.target.id)
                elif type(g.target) is ast.Tuple:
                    args_multi.extend([x.id for x in g.target.elts])
                else:
                    raise ValueError(f"{g.target} lacks expected ast.Name statements")
        elif type(a) is ast.Lambda:
            if len(a.args.args) > 1:
                args_multi.extend([r.arg for r in a.args.args])
            else:
                assert len(a.args.args) == 1, "A lambda can't assign no names (can it?)"
                args_indiv.append(a.args.args[0].arg)
        elif type(a) is ast.NamedExpr:
            # This is the walrus operator `:=` added in Python 3.8
            assert type(a.target) is ast.Name, f"Expected a name for {a.target}"
            args_indiv.append(a.target.id)
            # I haven't seen a multiple assignment from a walrus operator, asked SO:
            # https://stackoverflow.com/q/59567172/2668831
    assigned_args = args_indiv + args_multi
    return assigned_args


def get_extradef_names(extra_nodes):
    """
    Return the names used in the AST trunk nodes which are outside of both function
    definitions and import statements, so as to distinguish the unused names from
    those which are just used outside of function definitions.
    """
    extradef_names = set()
    for node in extra_nodes:
        node_names = [x.id for x in list(ast.walk(node)) if type(x) is ast.Name]
        for n in node_names:
            extradef_names.add(n)
    return extradef_names


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


def get_def_names(func_list, funcdefs, import_annos, extradef_names, report=True):
    imp_name_lines, imp_name_dicts = import_annos
    def_names = dict([(x, {}) for x in func_list])
    for m in func_list:
        fd_names = set()
        assert m in [f.name for f in funcdefs], f"No function '{m}' is defined"
        fd = funcdefs[[f.name for f in funcdefs].index(m)]
        fd_ids = [f.name for f in funcdefs]
        fd_params = [a.arg for a in fd.args.args]
        assigned_args = find_assigned_args(fd)
        for ast_statement in fd.body:
            for node in list(ast.walk(ast_statement)):
                if type(node) == ast.Name:
                    n_id = node.id
                    if n_id not in dir(builtins) + fd_ids + fd_params + assigned_args:
                        if n_id not in extradef_names:
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


def parse_mv_funcs(mvdefs, trunk, report=True):
    """
    mvdefs:  the list of functions to move (string list of function names)
    trunk:   AST body for the file (via `ast.parse(fc).body`)
    report:  whether to print [minimal, readable] 'reporting' output

    Produce a dictionary, `mvdef_names`, whose keys are the list of functions
    to move (i.e. the list `mvdefs` becomes the list of keys of `mvdef_names`),
    and the value of which at each key (for a key `m` which indicates the name
    of one of the functions given in `mvdefs` to move) is another dictionary,
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
    for `m` in `mvdefs` and `k` in the subset of AST-identified imported names
    in the function with  if f.name not in mvdefs name `m` in the list of
    function definitions `defs`. This access is handed off to the helper
    function `get_def_names`.

    For the names that were imported but not used, the dictionary is not keyed
    by function (as there are no associated functions), and instead the entries
    are accessed as `nondef_names.get(k)` for `k` in `unused_names`. This access
    is handed off to the helper function `get_nondef_names`.
    """
    report_VERBOSE = False  # Silencing debug print statements
    import_types = [ast.Import, ast.ImportFrom]
    imports = [n for n in trunk if type(n) in import_types]
    defs = [n for n in trunk if type(n) == ast.FunctionDef]
    # Any nodes in the AST that aren't imports or defs are 'extra' (as in 'other')
    extra = [n for n in trunk if type(n) not in [*import_types, ast.FunctionDef]]
    # Omit names used outside of function definitions so as not to remove them
    extradefs = get_extradef_names(extra)
    if report_VERBOSE:
        print("extra:", extra)
    import_annos = annotate_imports(imports, report=report)
    mvdef_names = get_def_names(mvdefs, defs, import_annos, extradefs, report)
    if report_VERBOSE:
        print("mvdef names:")
        pprint_def_names(mvdef_names)
    # ------------------------------------------------------------------------ #
    # Next obtain nonmvdef_names
    nomvdefs = [f.name for f in defs if f.name not in mvdefs]
    nonmvdef_names = get_def_names(nomvdefs, defs, import_annos, extradefs, report)
    if report_VERBOSE:
        print("non-mvdef names:")
        pprint_def_names(nonmvdef_names)
    # ------------------------------------------------------------------------ #
    # Next obtain unused_names
    mv_set = set().union(*[mvdef_names.get(x).keys() for x in mvdef_names])
    nomv_set = set().union(*[nonmvdef_names.get(x).keys() for x in nonmvdef_names])
    unused_names = list(set(list(import_annos[0].keys())) - mv_set - nomv_set)
    nondefs = get_nondef_names(unused_names, import_annos, report=report)
    # undef_names contains only those names that are imported but never used
    undef_names = dict([(x, nondefs.get(x)) for x in nondefs if x not in extradefs])
    if report_VERBOSE:
        rint("non-def names (imported but not used in any function def):")
        pprint_def_names(nondefs, no_funcdef_list=True)
    return mvdef_names, nonmvdef_names, undef_names
