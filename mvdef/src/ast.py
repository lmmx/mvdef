import ast
from pathlib import Path


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
    assert move_list is not None, "Please pass a list of funcdef names as move_list"
    assert True in (edit, report), "Nothing to do"
    extant = py_file.exists() and py_file.is_file()
    if extant:
        with open(src_file, "r") as f:
            fc = f.read()
            nodes = ast.parse(fc).body

        imports = [n for n in nodes if type(n) == ast.Import]
        funcdefs = [n for n in nodes if type(n) == ast.FunctionDef]

    # TODO: now draw the rest of the owl (follow steps 5 to 9 of the README)
    return
