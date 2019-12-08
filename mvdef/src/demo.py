from src.__env__ import example_dir
from src.transfer import parse_transfer
from example.test.test_demo import test_report as demotest


def main(mvdefs, dry_run=True, report=True):
    print("--------------RUNNING src.demo⠶main()--------------")
    # Step 1: declare src and dst .py file paths and back up the files
    src_p, dst_p = (example_dir / f"{n}.py" for n in ["demo_program", "new_file"])
    src_parsed, dst_parsed = parse_transfer(
        src_p, dst_p, mvdefs=mvdefs, test_func=demotest, report=report, nochange=dry_run
    )
    print("------------------COMPLETE--------------------------")
    return
