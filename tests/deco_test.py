"""
Tests for definitions wrapped by one or more decorators.
"""
from pytest import mark

from .helpers.cli_util import get_mvdef_diffs
from .helpers.io import Write

__all__ = ["test_functools_cache_deco_func"]


@mark.parametrize(
    "mv,stored_diffs",
    [(["C"], "decoC2decoD_C")],
    indirect=["stored_diffs"],
)
@mark.parametrize("src,dst", [("decoC", "decoD")], indirect=True)
def test_functools_dataclass_deco_func(tmp_path, src, dst, mv, stored_diffs):
    """
    Test that a classdef 'C' is moved correctly, i.e. along with its decorator,
    which is a `dataclasses.dataclass` function call decorator.
    """
    # Note: this would be better done as absolute content not diff!
    src_p, dst_p = Write.from_enums(src, dst, path=tmp_path).file_paths
    diffs = get_mvdef_diffs(src_p, dst_p, mv=mv, cls_defs=True, all_defs=False)
    assert diffs == stored_diffs
