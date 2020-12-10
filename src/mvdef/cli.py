from .transfer import parse_transfer
from sys import stderr
from itertools import chain
import argparse

__all__ = ["main", "validate_into_flag"]


def validate_into_flag(parser, args, nonconsec_dest="into"):
    """
    Awkward handling procedure to raise an error if two consecutive flags are both
    `-i`/`--into`, i.e. if the pop-then-append operations will overwrite the previous
    one's.
    """
    opt_actions = parser._option_string_actions
    opts = {
        v.dest: [
            {o: [i for i, a in enumerate(args) if a == o]} for o in v.option_strings
        ]
        for v in opt_actions.values()
        if any(o in args for o in v.option_strings)
    }
    opt_i = {o: [] for o in opts}
    for k, v in opts.items():
        idx = [list(chain.from_iterable(i for d in v for i in d.values() if i))]
        opt_i.get(k).extend(*idx)

    flag_pos_i_sorted = sorted([*chain.from_iterable(v for v in opt_i.values())])
    dest_i = [flag_pos_i_sorted.index(a) for a in opt_i.get(nonconsec_dest)]
    invalid = [(dest_i[i] - dest_i[i - 1]) == 1 for i, _ in enumerate(dest_i) if i > 0]
    is_invalid = any(invalid)
    invalid_arg_i = [
        (dest_i[i - 1], dest_i[i])
        for i, _ in enumerate(dest_i)
        if i > 0
        if invalid[i - 1]
    ]
    invalid_arg_pos = [
        (flag_pos_i_sorted[a], flag_pos_i_sorted[b]) for (a, b) in invalid_arg_i
    ]
    invalid_arg_values = [tuple(args[a : b + 2]) for (a, b) in invalid_arg_pos]
    if is_invalid:
        raise argparse.ArgumentError(
            None,
            f"Consecutive '{nonconsec_dest}' flags {invalid_arg_values} are invalid."
            " Please pass -m/--mv then up to one -i/--into flag (never multiple).",
        )


class _MvAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        mv_items = getattr(namespace, self.dest, None)
        mv_items = argparse._copy_items(mv_items)
        mv_items.append(values)
        setattr(namespace, self.dest, mv_items)
        # Append a `None` to the list for the `into` dest of the parser namespace
        paired_items = getattr(namespace, self.paired_dest, None)
        paired_items = argparse._copy_items(paired_items)
        paired_items.append(None)
        setattr(namespace, self.paired_dest, paired_items)

    paired_dest = "into"


class _IntoAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        if nargs is not None:
            raise ValueError("nargs not allowed")
        super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest, None)
        items = argparse._copy_items(items)
        if items:
            items.pop()  # remove the last `None` appended by _MvAction
        else:
            raise argparse.ArgumentError(None,
                f"Cannot set '{option_string}={values}', "
                "as no function was given to apply it to "
                f"({option_string} was called before -m/--mv)"
            )
        items.append(values)
        setattr(namespace, self.dest, items)


def main(src_p, dst_p, mvdefs, into_paths, dry_run, report, backup):
    if report:
        print("--------------RUNNING mvdef.cli⠶main()--------------", file=stderr)
    src_parsed, dst_parsed = parse_transfer(
        src_p,
        dst_p,
        mvdefs,
        into_paths,
        test_func=None,
        report=report,
        nochange=dry_run,
        use_backup=backup,
    )
    if report:
        print("------------------COMPLETE--------------------------", file=stderr)
    return
