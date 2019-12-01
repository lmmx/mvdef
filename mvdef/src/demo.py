from pathlib import Path
from sys import path as pathvar
from src.ast import ast_parse

def parse_example(program_path):
    parsed = ast_parse(program_path, return_report=True)
    return parsed

print("Demo initialised")
assert pathvar[0] == 'mvdef'
example_dir = Path(pathvar[1]) / 'mvdef' / 'example'
assert example_dir.exists() and example_dir.is_dir()
init_parse(example_dir / "simple_program.py")
