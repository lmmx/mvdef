from mvdef.transfer import parse_transfer


def main(src_p, dst_p, mvdefs, dry_run, report, backup):
    if report:
        print("--------------RUNNING mvdef.cli⠶main()--------------")
    src_parsed, dst_parsed = parse_transfer(
        src_p,
        dst_p,
        mvdefs,
        test_func=None,
        report=report,
        nochange=dry_run,
        use_backup=backup,
    )
    if report:
        print("------------------COMPLETE--------------------------")
    return
