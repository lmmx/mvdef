import ast
from pathlib import Path
from collections import OrderedDict
import builtins


def annotate_imports(imports, report=True):
    """
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
        print("The import name dicts are:")
        for nd in imp_name_dict_list:
            print(nd)
        print()
        print(f"The import name line dict is:\n{imp_name_linedict}")
    return imp_name_linedict, imp_name_dict_list


def ast_parse(py_file, move_list=[], report=False, edit=False, backup=True):
    """
    Parse the Abstract Syntax Tree (AST) of a Python file, and either return a
    report of what changes would be required to move the move_list of funcdefs out
    of it, or a report of the imports and funcdefs in general if no move_list is
    provided (taken to indicate that the file is the target funcdefs are moving to),
    or make changes to the file (either newly creating one if no such file exists,
    or editing in place according to the reported import statement differences).

    If the py_file doesn't exist, it's being newly created by the move and obviously
    no report can be made on it: it has no funcdefs and no import statements, so
    all the ones being moved will be newly created.

    move_list should be given if the file is the source of moved functions, and left
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
        funcdefs = [n for n in nodes if type(n) == ast.FunctionDef]
        # return imports, funcdefs

        imp_name_lines, imp_name_dicts = annotate_imports(imports, report=report)

        if move_list != []:
            mv_list_namesets = dict(zip(move_list, [{}] * len(move_list)))
            for m in move_list:
                fd_names = set()
                assert m in [f.name for f in funcdefs], f"No function '{m}' is defined"
                fd = funcdefs[[f.name for f in funcdefs].index(m)]
                fd_params = [a.arg for a in fd.args.args]
                arg_assmts = [a for a in fd.body if type(a) is ast.Assign]
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
                for ast_statement in fd.body:
                    for node in list(ast.walk(ast_statement)):
                        if type(node) == ast.Name:
                            n_id = node.id
                            if n_id not in dir(builtins) + fd_params + assigned_args:
                                fd_names.add(n_id)
                mv_list_namesets[m] = dict(
                    zip(sorted(fd_names), [{} for x in range(len(fd_names))])
                )
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
                    k_i = [list(d.keys()).index(x) for x in d if d[x] == k][0]
                    assert k_i >= 0, f"Movable name {k} not found in import name dict"
                    # Store index in case of multiple imports per import statement line
                    mv_imp_refs.get(k)["k_i"] = k_i
                    fd_name_entry = mv_list_namesets.get(m).get(k)
                    fd_name_entry["n"] = mv_imp_refs.get(k).get("n")
                    fd_name_entry["k_i"] = k_i
                    fd_name_entry["line"] = mv_imp_refs.get(k).get("line")
                if report:
                    print(f"The names in {m} are: {fd_names}")
                if edit:
                    # Go do the file editing
                    pass
            if report:
                print("In summary, mv_list_namesets are:")
                for mln in mv_list_namesets:
                    print(mln, mv_list_namesets.get(m))
        else:
            # No files are to be moved from py_file, i.e. they are moving into py_file
            mvdef = []
            # extant is True so non_mvdef is just all funcdefs for the file
            nonmvdef = [f.name for f in funcdefs]
            if report:
                print(f"No functions to move from {py_file}")
    return
