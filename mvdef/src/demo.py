from sys import path as syspath
from src.ast import ast_parse
from src.backup import backup
from src.__env__ import example_dir
from example.test.test_demo_program import test_report

# TODO: Move parse_example to AST once logic is figured out for the demo
def parse_example(src_p, dst_p, move_list, report=True, nochange=True):
    # Backs up source and target to a hidden file, restorable in case of error,
    # and creating a hidden placeholder if the target doesn't exist yet
    assert backup(src_p, dry_run=nochange)
    assert backup(dst_p, dry_run=nochange)
    src_parsed = ast_parse(src_p, move_list, report=report, edit=(not nochange))
    dst_parsed = ast_parse(dst_p, report=report, edit=(not nochange))
    return src_parsed, dst_parsed

def main(mvdefs, dry_run=True, report=True):
    print("--------------RUNNING src.demo⠶main()--------------")
    try:
        test_report()
    except AssertionError as e:
        raise RuntimeError("The tests do not pass for the example file.")

    # Step 1: declare src and dst .py file paths and back up the files
    src_p, dst_p = (example_dir / f"{n}.py" for n in ["demo_program", "new_file"])
    src_parsed, dst_parsed = parse_example(
        src_p, dst_p, move_list=mvdefs, report=report, nochange=dry_run
    )
    if dst_parsed is None:
        dst_parsed = "(Dst will take all src_parsed imports and funcdefs)"
    # src imports, src_funcdefs = src_parsed
    src_ret = src_parsed
    if type(dst_parsed) is str:
        if report: print(dst_parsed)
    else:
        dst_imports, dst_funcdefs = dst_parsed
    if dry_run:
        print("DRY RUN: No files have been modified, skipping tests.")
    else:
        try:
            test_report()
        except AssertionError as e:
            print(f"!!! The demo broke the example !!!")
            raise RuntimeError(e)
    print("------------------COMPLETE--------------------------")
    return
