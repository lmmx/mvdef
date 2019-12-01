import ast
from pathlib import Path
# from __main__ import lib_dir, example_dir

with open(example_dir / 'simple_program.py', 'r') as f:
    testfile = f.read()
    nodes = ast.parse(testfile).body

imports = [n for n in nodes if type(n) == ast.Import]
funcdefs = [n for n in nodes if type(n) == ast.FunctionDef]

move_list = ['show_line']
