from .ast_util import ast_parse
from .backup import backup
from .colours import colour_str as colour
from .editor import transfer_mvdefs

__all__ = ["parse_transfer"]

# TODO: Move parse_example to AST once logic is figured out for the demo
def parse_transfer(
    src_p, dst_p, mvdefs, test_func=None, report=True, nochange=True, use_backup=True
):
    """
    Execute the transfer of function definitions and import statements, optionally
    (if test_func is specified) also calls that afterwards to confirm functionality
    remains intact.

    If test_func is specified, it must only use AssertionError (i.e. you are free
    to have the test_func call other functions, but it must catch any errors therein
    and only raise errors from assert statements). This is to simplify this step.
    My example would be to list one or more failing tests, then assert that this
    list is None, else raise an AssertionError of these tests' definition names
    (see example.test.test_demo⠶test_report for an example of such a function).

    If nochange is False, files will be changed in place (i.e. setting it
    to False is equivalent to setting the edit parameter to True).
      - Note: this was unimplemented...

    This parameter is used as a sanity check to prevent wasted computation,
    as if neither report is True nor nochange is False, there is nothing to do.
    """
    # Backs up source and target to a hidden file, restorable in case of error,
    # and creating a hidden placeholder if the target doesn't exist yet
    assert True in [report, not nochange], "Nothing to do"
    if test_func is not None:
        try:
            test_func.__call__()
        except AssertionError as e:
            raise RuntimeError(f"! {test_func} failed, aborting mvdef execution.")
    if use_backup:
        assert backup(src_p, dry_run=nochange)
        assert backup(dst_p, dry_run=nochange)
    # Create edit agendas from the parsed AST of source and destination files
    src_edits = ast_parse(src_p, mvdefs=mvdefs, report=report)
    assert src_edits is not None, "The src file did not return a processed AST"
    if report:
        print(f"⇒ Functions moving from {colour('light_gray', src_p)}: {mvdefs}")
    transfers = dict([["take", src_edits.get("move")], ["echo", src_edits.get("copy")]])
    # Create the destination file if it doesn't exist, and if this isn't a dry run
    dst_extant = dst_p.exists() and dst_p.is_file()
    if not dst_extant and not nochange:
        with open(dst_p, "w") as f:
            f.write("")
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
        return src_edits, dst_edits
    else:
        # Edit the files (no longer pass imports or defs, will recompute AST)
        transfer_mvdefs(src_p, dst_p, mvdefs, src_edits, dst_edits)
    if test_func is None:
        return src_edits, dst_edits
    else:
        try:
            test_func.__call__()
        except AssertionError as e:
            # TODO: implement backup restore
            print(
                f"! {test_func} failed, indicating changes made by mvdef broke the"
                + "program (if backups used, mvdefs will now attempt to restore)"
            )
            raise RuntimeError(e)
    return src_edits, dst_edits
