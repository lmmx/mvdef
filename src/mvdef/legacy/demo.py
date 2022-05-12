from .__env__ import example_dir
from .example.test.test_demo import test_report as demotest
from .transfer import parse_transfer

__all__ = ["main"]


def main(mvdefs, into_paths, dry_run=True, report=True):
    if report:
        print("--------------RUNNING mvdef.demo⠶main()--------------")
    # Step 1: declare src and dst .py file paths and back up the files
    src_p, dst_p = (example_dir / f"{n}.py" for n in ["demo_program", "new_file"])
    src_parsed, dst_parsed = parse_transfer(
        mvdefs=mvdefs,
        into_paths=into_paths,
        src_p=src_p,
        dst_p=dst_p,
        report=report,
        nochange=dry_run,
        test_func=demotest,
    )
    if report:
        print("------------------COMPLETE--------------------------")
    return
