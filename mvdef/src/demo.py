from pathlib import Path
from sys import path as pathvar
from src.ast import ast_parse
from src.backup import backup


# TODO: Move parse_example to AST once logic is figured out for the demo
def parse_example(src_p, dst_p, move_list, report=True, nochange=True):
    # Backs up source and target to a hidden file, restorable in case of error,
    # and creating a hidden placeholder if the target doesn't exist yet
    assert backup(src_p, dry_run=nochange)
    assert backup(dst_p, dry_run=nochange)
    src_parsed = ast_parse(src_p, move_list, report=report, edit=(not nochange))
    dst_parsed = ast_parse(dst_p, report=report, edit=(not nochange))
    return src_parsed, dst_parsed


# Initial setup
print("Demo initialised")
assert pathvar[0] == "mvdef"
example_dir = Path(pathvar[1]) / "mvdef" / "example"
assert example_dir.exists() and example_dir.is_dir()

mvdefs = ["show_line"]

# Step 1: declare src and dst .py file paths and back up the files
src_p, dst_p = (example_dir / f"{n}.py" for n in ["simple_program", "new_file"])
parse_example(src_p, dst_p, move_list=mvdefs, report=True, nochange=True)
