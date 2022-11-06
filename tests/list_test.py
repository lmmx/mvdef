"""
Tests for the diffs created in 'dry run' mode by :meth:`Agenda.simulate()`.
"""
from pytest import mark, raises

from .helpers.cli_util import get_manif
from .helpers.io import Write

__all__ = ["test_ls_list"]


@mark.parametrize("lst", [True, False])
@mark.parametrize("dry_run", [True, False])
@mark.parametrize("all_defs", [True, False])
@mark.parametrize("cls_defs", [True, False])
@mark.parametrize(
    "src,all_names_in_order,def_ls,cls_ls",
    [
        ("fooA", ["foo", "A"], ["foo"], ["A"]),
        ("bar", None, None, []),
        ("baz", None, None, []),
        ("log", ["err", "warn"], None, []),
        ("decoC", ["C"], [], None),
        ("decoD", ["D"], [], None),
        ("errorer", ["errorer"], None, []),
        ("one_func_all", ["hello"], None, []),
        ("many_func_all", [*map("hello{}".format, range(8))], None, []),
    ],
    indirect=["src"],
)
def test_ls_list(
    tmp_path, def_ls, cls_ls, src, cls_defs, all_defs, all_names_in_order, dry_run, lst
):
    """
    Test that a class 'A' or a funcdef 'foo' is moved correctly, and that repeating it
    twice makes no difference to the result, and ditto for switching the all_defs flag.

    None values for all_names_in_order default to a singleton list of the filename.
    None values for either cls_ls or def_ls defaults to `all_names_in_order`.
    """
    assert not (def_ls is cls_ls is None), "Cannot auto-set both cls_ls and def_ls"
    all_names_in_order = all_names_in_order or [src.name]
    def_ls = all_names_in_order if def_ls is None else def_ls
    cls_ls = all_names_in_order if cls_ls is None else cls_ls
    expected_ls = cls_ls if cls_defs else def_ls
    src_p, *_ = Write.from_enums(src, path=tmp_path).file_paths
    ls_kwargs = dict(cls_defs=cls_defs, all_defs=all_defs, dry_run=dry_run, list=lst)
    expected = all_names_in_order if all_defs else expected_ls
    if lst or dry_run:
        manif = get_manif(src_p, match=["*"], **ls_kwargs)
    else:
        with raises(NotImplementedError):
            manif = get_manif(src_p, match=["*"], **ls_kwargs)
        return
    if lst:
        check = manif.splitlines() == expected
        assert check
    elif dry_run:
        # Simple version of the `format_all()` function, for short one-liners only
        all_pre = "__all__ = ["
        all_mid = ", ".join([f'"{name}"' for name in expected])
        all_together = all_pre + all_mid + "]"
        if len(all_together) > (88):
            all_pre += "\n"
            all_mid = ",\n".join([f'    "{name}"' for name in expected])
            all_together = all_pre + all_mid + ",\n]"
        expected_all = all_together
        check = manif == expected_all
        assert check
