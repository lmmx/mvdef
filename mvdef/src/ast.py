import ast
from pathlib import Path

def ast_parse(src_file, report=False, make_changes=False, backup=True):
    """
    If report is True, returns a string describing the changes
    to be made (if False, nothing is returned).
    If make_changes is True, files will be changed in place.
    If backup is True, files will be changed in place (be careful switching this off!)
    """
    assert True in (make_changes, return_report), "Nothing to do"
    with open(src_file, "r") as f:
        fc = f.read()
        nodes = ast.parse(fc).body

    imports = [n for n in nodes if type(n) == ast.Import]
    funcdefs = [n for n in nodes if type(n) == ast.FunctionDef]

    move_list = ["show_line"]

    # TODO: follow steps 5 to 9 of the README
    return
