import defopt

from .transfer import MvDef


def cli(*arg_override, **kwarg_override):
    return_diffs = kwarg_override.pop("return_diffs", False)  # simplifies testing
    if arg_override or kwarg_override:
        mover = MvDef(*arg_override, **kwarg_override)
    else:
        mover = defopt.run(
            MvDef, no_negated_flags=True, cli_options="has_default", show_defaults=False
        )
    if mover.check_blocker is None:
        if mover.dry_run:
            src_diff, dst_diff = mover.diffs()
            if src_diff:
                print(src_diff)
            if dst_diff:
                print(dst_diff)
            if return_diffs:
                return src_diff, dst_diff
        else:
            mover.move()
