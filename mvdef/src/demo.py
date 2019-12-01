import ast
from pathlib import Path

def init(var_init):
    """
    Passing parameters into the demo to get directory of demo file (without sys.path).
    """
    assert "example_dir" in var_init, "Provide the location of the examples directory"
    example_dir = var_init['example_dir']
    init_parse(example_dir)

def init_parse(example_dir):
    with open(example_dir / "simple_program.py", "r") as f:
        eg_file = f.read()
        nodes = ast.parse(eg_file).body

    imports = [n for n in nodes if type(n) == ast.Import]
    funcdefs = [n for n in nodes if type(n) == ast.FunctionDef]

    move_list = ["show_line"]
