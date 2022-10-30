"""
Tests for definitions wrapped by one or more decorators.
"""
from pytest import mark

from .helpers.cli_util import get_mvdef_diffs
from .helpers.io import Write

__all__ = ["test_cache_decorated_func"]


@mark.parametrize(
    "mv,stored_diffs",
    [(["rando"], "deco2bar_rando")],
    indirect=["stored_diffs"],
)
@mark.parametrize("src,dst", [("deco", "bar")], indirect=True)
def test_functools_cache_deco_func(tmp_path, src, dst, mv, stored_diffs):
    """
    Test that a funcdef 'rando' is moved correctly, i.e. along with its decorator,
    which is a `functools.cache` function call decorator.
    """
    src_p, dst_p = Write.from_enums(src, dst, path=tmp_path).file_paths
    diffs = get_mvdef_diffs(src_p, dst_p, mv=mv, cls_defs=False, all_defs=False)
    assert diffs == stored_diffs
