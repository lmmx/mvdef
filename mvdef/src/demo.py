from sys import path as syspath
from src.ast_util import ast_parse
from src.backup import backup
from src.__env__ import example_dir
from src.display import colour_str as colour
from example.test.test_demo_program import test_report

# TODO: Move parse_example to AST once logic is figured out for the demo
def parse_example(src_p, dst_p, mvdefs, report=True, nochange=True):
    """
    If nochange is False, files will be changed in place (i.e. setting it
    to False is equivalent to setting the edit parameter to True).
      - Note: this was unimplemented...

    This parameter is used as a sanity check to prevent wasted computation,
    as if neither report is True nor nochange is False, there is nothing to do.
    """
    # Backs up source and target to a hidden file, restorable in case of error,
    # and creating a hidden placeholder if the target doesn't exist yet
    assert True in [report, not nochange], "Nothing to do"
    assert backup(src_p, dry_run=nochange)
    assert backup(dst_p, dry_run=nochange)
    # Create edit agendas from the parsed AST of source and destination files
    src_edits = ast_parse(src_p, mvdefs=mvdefs, report=report)
    assert src_edits is not None, "The src file did not return a processed AST"
    if report:
        print(f"⇒ Functions moving from {colour('light_gray', src_p)}: {mvdefs}")
    transfers = dict([["take", src_edits.get("move")], ["echo", src_edits.get("copy")]])
    dst_edits = ast_parse(dst_p, transfers=transfers, report=report)
    if dst_edits is None:
        # There is no destination file (it will be created)
        if report:
            print(
                f"⇒ Functions will move to {colour('light_gray', dst_p)}"
                + " (it's being created from them)"
            )
    else:
        if report:
            print(f"⇒ Functions will move to {colour('light_gray', dst_p)}")
    if nochange:
        print("DRY RUN: No files have been modified, skipping tests.")
    else:
        try:
            test_report()
        except AssertionError as e:
            print(f"!!! The demo broke the example !!!")
            raise RuntimeError(e)
    return src_edits, dst_edits

def main(mvdefs, dry_run=True, report=True):
    print("--------------RUNNING src.demo⠶main()--------------")
    try:
        test_report()
    except AssertionError as e:
        raise RuntimeError("The tests do not pass for the example file.")

    # Step 1: declare src and dst .py file paths and back up the files
    src_p, dst_p = (example_dir / f"{n}.py" for n in ["demo_program", "new_file"])
    src_parsed, dst_parsed = parse_example(
        src_p, dst_p, mvdefs=mvdefs, report=report, nochange=dry_run
    )
    print("------------------COMPLETE--------------------------")
    return
