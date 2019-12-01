import ast

with open('parse_test.py', 'r') as f:
    testfile = f.read()
    nodes = ast.parse(testfile).body

imports = [n for n in nodes if type(n) == ast.Import]
funcdefs = [n for n in nodes if type(n) == ast.FunctionDef]

move_list = ['show_line']
