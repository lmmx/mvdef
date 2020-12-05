import ast
from asttokens import ASTTokens
import builtins
from pathlib import Path
from .agenda_util import pprint_agenda
from .deprecations import pprint_def_names
from .import_util import get_imported_name_sources, annotate_imports
from sys import stderr

__all__ = [
    "retrieve_ast_agenda",
    "process_ast",
    "find_assigned_args",
    "get_extradef_names",
    "get_nondef_names",
    "get_def_names",
    "parse_mv_funcs",
]


def retrieve_ast_agenda(linkfile, transfers=None):
    """
    Build and parse the Abstract Syntax Tree (AST) of a Python file, and either return
    a report of what changes would be required to move the mvdefs subset of all
    function definitions out of it, or a report of the imports and funcdefs in general
    if no `linkfile.mvdefs` is provided (taken to indicate that the file is the target funcdefs
    are moving to), or make changes to the file (either newly creating one if no such
    file exists, or editing in place according to the reported import statement
    differences).

    If the Python file `linkfile.path` doesn't exist (which can be checked directly as it's a
    Path object), it's being newly created by the move and obviously no report can
    be made on it: it has no funcdefs and no import statements, so all the ones being
    moved will be newly created.

    mvdefs should be given if the file is the source of moved functions, and left
    empty (default: `None` which --> `[]`) if the file is the destination to move them to.

    If `linkfile.report` is True, returns a string describing the changes
    to be made (if False, nothing is returned).

    If backup is True, files will be changed in place by calling `mvdef.backup.backup`
    (obviously, be careful switching this setting off if report is True, as any
    changes made cannot be restored afterwards from this backup file).
    """
    if linkfile.is_extant:
        with open(linkfile.path, "r") as f:
            fc = f.read()
            trunk = ast.parse(fc).body

        # print("Next running process_ast from retrieve_ast_agenda")
        linkfile.process_ast(trunk, transfers)  # sets linkfile.edits
    elif type(linkfile).__name__ == "DstFile":
        # An `isinstance` call would require a circular import, hence the __name__ check
        #
        # Not extant so file doesn't exist (cannot produce a parsed AST) however the
        # linkfile is the destination (no `mvdefs` to remove), so return None.
        # This will be picked up by the assert in SrcFile.validate_edits
        # (but skipped for DstFile.validate_edits)
        assert linkfile.mvdefs is None, "Unexpected mvdefs list for non-extant DstFile"
        linkfile.edits = None
    else:
        msg = f"Can't move {linkfile.mvdefs=} from {linkfile.path=} – it doesn't exist!"
        raise ValueError(msg)
    # print("Finished processing in retrieve_ast_agenda")


class EditAgenda(dict):
    def __init__(self):
        super().__init__({c: [] for c in self.categories})

    categories = ["move", "keep", "copy", "lose", "take", "echo", "stay"]

    def add_entry(self, category, key_val_pair):
        if category not in self.categories:
            raise ValueError(f"{category} is not a valid agenda category")
        entry = EditItem(*key_val_pair)
        self.get(category).append(entry)

    def remove_entry(self, category, entry_value):
        index_key = [list(x.values())[0] for x in self.get(category)].index(entry_value)
        del self.get(category)[index_key]

    def add_imports(self, imports, category, names):
        for i in imports:
            assert i in set().union(*[names.get(k) for k in names]), f"{i} not found"
            i_dict = [names.get(k) for k in names if i in names.get(k)][0].get(i)
            self.add_entry(category=category, key_val_pair=(i, i_dict))


class EditItem(dict):
    def __init__(self, key, value):
        super().__init__({key: value})

def process_ast(linkfile, trunk, transfers=None):
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

    First, given the lists of mvdef names (linkfile.mvdef_names) and non-mvdef names
    (linkfile.nonmvdef_names), construct the subsets:

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
    linkfile.parse_mv_funcs(trunk)  # sets: (mvdef_names, nonmvdef_names, undef_names)
    # as linkfile.mvdef_names, linkfile.nonmvdef_names, linkfile.undef_names
    imported_names = get_imported_name_sources(trunk, report=linkfile.report)
    if linkfile.report:
        print(f"• Determining edit agenda for {linkfile.path.name}:", file=stderr)
    linkfile.edits = EditAgenda()
    linkfile.imp_def_subsets()  # sets mv_imports, nonmv_imports, mutual_imports
    # Iterate over each imported name, i, in the subset of import names to move

    linkfile.edits.add_imports(linkfile.mv_imports, "move", linkfile.mvdef_names)
    linkfile.edits.add_imports(linkfile.nonmv_imports, "keep", linkfile.nonmvdef_names)
    linkfile.edits.add_imports(linkfile.mutual_imports, "copy", linkfile.mvdef_names)
    for i in linkfile.undef_names:
        i_dict = linkfile.undef_names.get(i)
        linkfile.edits.add_entry(category="lose", key_val_pair=(i, i_dict))
    if not transfers:
        # Returning without transfers if None (would also catch empty dict `{}`)
        if linkfile.report:
            pprint_agenda(linkfile.edits)
        return
    # elif linkfile.report:
    #    if len(linkfile.edits.get("lose")) > 0:
    #        print("• Resolving edit agenda conflicts:")
    # i is 'ready made' from a previous call to ast_parse, and just needs reporting
    for i in transfers.get("take"):
        k, i_dict = list(i.items())[0]
        linkfile.edits.add_entry(category="take", key_val_pair=(k, i_dict))
    for i in transfers.get("echo"):
        k, i_dict = list(i.items())[0]
        linkfile.edits.add_entry(category="echo", key_val_pair=(k, i_dict))
    # Resolve agenda conflicts: if any imports marked 'lose' are cancelled out
    # by any identically named imports marked 'take' or 'echo', change to 'stay'
    for i in linkfile.edits.get("lose"):
        k, i_dict = list(i.items())[0]
        imp_src = i_dict.get("import")
        if k in [list(x)[0] for x in linkfile.edits.get("take")]:
            t_i_dict = [x for x in linkfile.edits.get("take") if k in x][0].get(k)
            take_imp_src = t_i_dict.get("import")
            if imp_src != take_imp_src:
                continue
            # Deduplicate 'lose'/'take' k: replace both with 'stay'
            linkfile.edits.add_entry(category="stay", key_val_pair=(k, i_dict))
            linkfile.edits.remove_entry(category="lose", entry_value=i_dict)
            linkfile.edits.remove_entry(category="take", entry_value=t_i_dict)
        elif k in [list(x)[0] for x in linkfile.edits.get("echo")]:
            e_i_dict = [x for x in linkfile.edits.get("echo") if k in x][0].get(k)
            echo_imp_src = e_i_dict.get("import")
            if imp_src != echo_imp_src:
                continue
            # Deduplicate 'lose'/'echo' k: replace both with 'stay'
            linkfile.edits.add_entry(category="stay", key_val_pair=(k, i_dict))
            linkfile.edits.remove_entry(category="lose", entry_value=i_dict)
            linkfile.edits.remove_entry(category="echo", entry_value=e_i_dict)
    # Resolve agenda conflicts: if any imports marked 'take' or 'echo' are cancelled
    # out by any identically named imports already present, change to 'stay'
    for i in linkfile.edits.get("take"):
        k, i_dict = list(i.items())[0]
        take_imp_src = i_dict.get("import")
        if k in imported_names:
            # Check the import source and asnames match
            imp_src = imported_names.get(k)[0]
            if imp_src != take_imp_src:
                # This means that the same name is being used by a different function
                raise ValueError(
                    f"Cannot move imported name '{k}', it is already "
                    + f"in use in {linkfile.path.name} ({take_imp_src} clashes with {imp_src})"
                )
                # (N.B. could rename automatically as future feature)
            # Otherwise there is simply a duplicate import statement, so the demand
            # to 'take' the imported name is already fulfilled.
            # Replace unnecessary 'take' with 'stay'
            linkfile.edits.add_entry(category="stay", key_val_pair=(k, i_dict))
            linkfile.edits.remove_entry(category="take", entry_value=i_dict)
    for i in linkfile.edits.get("echo"):
        k, i_dict = list(i.items())[0]
        echo_imp_src = i_dict.get("import")
        if k in imported_names:
            # Check the import source and asnames match
            imp_src = imported_names.get(k)[0]
            if imp_src != echo_imp_src:
                # This means that the same name is being used by a different function
                raise ValueError(
                    f"Cannot move imported name '{k}', it is already "
                    + f"in use in {linkfile.path.name} ({echo_imp_src} clashes with {imp_src})"
                )
                # (N.B. could rename automatically as future feature)
            # Otherwise there is simply a duplicate import statement, so the demand
            # to 'echo' the imported name is already fulfilled.
            # Replace unnecessary 'echo' with 'stay'
            linkfile.edits.add_entry(category="stay", key_val_pair=(k, i_dict))
            linkfile.edits.remove_entry(category="echo", entry_value=i_dict)
    if linkfile.report:
        pprint_agenda(linkfile.edits)
    return


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
        elif type(a) in (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp):
            # Handle implicit assignments within comprehensions
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
        node_names = [x.id for x in ast.walk(node) if type(x) is ast.Name]
        for n in node_names:
            extradef_names.add(n)
    return extradef_names


def get_nondef_names(unused, import_annos, report=True):
    imp_name_lines, imp_name_dicts = import_annos
    nondef_names = NameDict(unused)  # dict keyed by the unused names
    if unknowns := [n for n in unused if n not in imp_name_lines]:
        raise ValueError(f"These names could not be sourced: {unknowns}")
    # mv_imp_refs is the subset of imp_name_lines for movable funcdef names
    # These refs will lead to import statements being copied and/or moved
    uu_imp_refs = {n: imp_name_lines.get(n) for n in unused}
    for k in uu_imp_refs:  # iterate over the unused imported names/asnames
        n = uu_imp_refs.get(k).get("n")
        d = imp_name_dicts[n]
        n_i = next(i for i, x in enumerate(d.values()) if x == k)
        assert n_i >= 0, f"Movable name {k} not found in import name dict"
        # Store index in case of multiple imports per import statement line
        uu_imp_refs.get(k)["n_i"] = n_i
        new_entry = {
            "n": uu_imp_refs.get(k).get("n"),
            "n_i": n_i,
            "line": uu_imp_refs.get(k).get("line"),
            "import": [*imp_name_dicts[n]][n_i],
        }
        nondef_names.add_entry(k, new_entry)
    return nondef_names


class NameDict(dict):
    def __init__(self, func_list):
        super().__init__({f: {} for f in func_list})

    def add_entry(self, def_name, def_name_info_dict):
        if self.get(def_name):
            raise ValueError(f"{self.get(def_name)=} already exists!")
        self[def_name] = def_name_info_dict

    def add_subentry(self, def_name, import_name, import_name_info_dict):
        if self.get(def_name).get(import_name):
            raise ValueError(f"{self.get(def_name).get(import_name)=} already exists!")
        self[def_name][import_name] = import_name_info_dict


class NameEntryDict(dict):
    # can only be used for `get_def_names`, the others are not consistent enough
    # even though they are dicts with the same keys...
    def __init__(self, names, values=None, sort=False):
        if values:
            if sort:
                raise NotImplementedError("Sorting not coded for key-val pairs")
            super().__init__(dict(zip(names, values)))
        else:
            if type(names) is dict:
                if sort:
                    raise NotImplementedError("Sorting not coded for dicts")
                super().__init__(names)  # simples
                return
            elif sort:
                names = sorted(names)
            super().__init__({n: {} for n in names})


def get_def_names(func_list, funcdefs, import_annos, extradef_names, report=True):
    imp_name_lines, imp_name_dicts = import_annos
    def_names = NameDict(func_list)
    for m in func_list:
        fd_names = set()
        if m not in [f.name for f in funcdefs]:
            raise NameError(f"No function '{m}' is defined")
        fd = funcdefs[[f.name for f in funcdefs].index(m)]
        fd_ids = [f.name for f in funcdefs]
        fd_params = [a.arg for a in fd.args.args]
        assigned_args = find_assigned_args(fd)
        for ast_statement in fd.body:
            for node in ast.walk(ast_statement):
                if type(node) == ast.Name:
                    n_id = node.id
                    if n_id not in dir(builtins) + fd_ids + fd_params + assigned_args:
                        if n_id not in extradef_names:
                            fd_names.add(n_id)
        def_names[m] = NameEntryDict(fd_names, sort=True)
        # All names successfully found and can finish if remaining names are
        # in the set of funcdef names, comparing them tothe import statements
        unknowns = [n for n in fd_names if n not in imp_name_lines]
        if unknowns:
            raise ValueError(f"These names could not be sourced: {unknowns}")
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
            n = mv_imp_refs.get(k).get("n")
            new_entry = NameEntryDict(
                {
                    "n": n,
                    "n_i": n_i,
                    "line": mv_imp_refs.get(k).get("line"),
                    "import": list(imp_name_dicts[n].keys())[n_i],
                }
            )
            def_names.add_subentry(m, k, new_entry)
    return def_names


class FuncDef(ast.FunctionDef):
    """
    Wrap `ast.FunctionDef` to permit recursive search for inner functions upon
    creation in `parse_mv_funcs`.
    """

    def __init__(self, funcdef):
        super().__init__(**vars(funcdef))
        self.check_for_inner_funcs()

    def check_for_inner_funcs(self):
        if not hasattr(self, "_inner_func_idx"):
            self.inner_func_idx = [
                i for i, n in enumerate(self.body) if isinstance(n, ast.FunctionDef)
            ]
        if self.has_inner_func:
            self.set_inner_funcs()

    @property
    def has_inner_func(self):
        return self.inner_func_idx is not []

    @property
    def inner_func_idx(self):
        return self._inner_func_idx

    @inner_func_idx.setter
    def inner_func_idx(self, idx):
        self._inner_func_idx = idx

    def set_inner_funcs(self):
        self.inner_funcs = [
            InnerFuncDef(self.body[i], self.name, (self.lineno, self.end_lineno))
            for i in self.inner_func_idx
        ]

    @property
    def inner_funcs(self):
        return self._inner_funcs

    @inner_funcs.setter
    def inner_funcs(self, funcdefs):
        self._inner_funcs = funcdefs


class InnerFuncDef(FuncDef):
    """
    Wrap `FuncDef` (in turn wrapping `ast.FunctionDef`) to store a reference to the
    parent funcdef's line range on an inner function.
    """

    def __init__(self, funcdef, parent_def_name, parent_def_line_range):
        super().__init__(funcdef)
        self.parent_def_name = parent_def_name
        self.parent_def_line_range = parent_def_line_range


def parse_mv_funcs(linkfile, trunk):
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
    mvdefs = linkfile.mvdefs
    if mvdefs is None:
        mvdefs = []
    report_VERBOSE = False  # Silencing debug print statements
    import_types = [ast.Import, ast.ImportFrom]
    imports = [n for n in trunk if type(n) in import_types]
    defs = [FuncDef(n) for n in trunk if type(n) is ast.FunctionDef]
    # Any nodes in the AST that aren't imports or defs are 'extra' (as in 'other')
    extra = [n for n in trunk if type(n) not in [*import_types, ast.FunctionDef]]
    # Omit names used outside of function definitions so as not to remove them
    extradefs = get_extradef_names(extra)
    if report_VERBOSE:
        print("extra:", extra, file=stderr)
    import_annos = annotate_imports(imports, report=linkfile.report)
    linkfile.mvdef_names = get_def_names(
        mvdefs, defs, import_annos, extradefs, linkfile.report
    )
    if report_VERBOSE:
        print("mvdef names:", file=stderr)
        pprint_def_names(linkfile.mvdef_names)
    # ------------------------------------------------------------------------ #
    # Next obtain nonmvdef_names
    nomvdefs = [f.name for f in defs if f.name not in mvdefs]
    linkfile.nonmvdef_names = get_def_names(
        nomvdefs, defs, import_annos, extradefs, linkfile.report
    )
    if report_VERBOSE:
        print("non-mvdef names:", file=stderr)
        pprint_def_names(nonmvdef_names)
    # ------------------------------------------------------------------------ #
    # Next obtain unused_names
    mv_set = set().union(
        *[linkfile.mvdef_names.get(x).keys() for x in linkfile.mvdef_names]
    )
    nomv_set = set().union(
        *[linkfile.nonmvdef_names.get(x).keys() for x in linkfile.nonmvdef_names]
    )
    unused_names = list(set(list(import_annos[0].keys())) - mv_set - nomv_set)
    nondefs = get_nondef_names(unused_names, import_annos, report=linkfile.report)
    # linkfile.undef_names contains only those names that are imported but never used
    linkfile.undef_names = dict(
        [(x, nondefs.get(x)) for x in nondefs if x not in extradefs]
    )
    if report_VERBOSE:
        print("non-def names (imported but not used in any function def):")
        pprint_def_names(nondefs, no_funcdef_list=True)
    return
