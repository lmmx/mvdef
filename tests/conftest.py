from pytest import fixture

from .helpers.expected import DstDiffs, SrcDiffs
from .helpers.inputs import FuncAndClsDefs

__all__ = ["src", "dst", "stored_diffs"]


@fixture(scope="function")
def src(request) -> tuple[str, str]:
    return FuncAndClsDefs[request.param]


@fixture(scope="function")
def dst(request) -> tuple[str, str]:
    dst_filename_stem = request.param
    return FuncAndClsDefs[dst_filename_stem]


@fixture(scope="function")
def stored_diffs(request) -> tuple[str, str]:
    """
    2 in the name means 'to an existing dst', e.g. x2y means 'move src=x to dst=y'.
    0 in the name means 'to a new dst', i.e. no change to src, so use the same diff,
    by replacing the 2 with a 0 when looking up the src file contents in the Enum.
    """
    src_name_key = request.param.replace("0", "2")
    dst_name_key = request.param
    return SrcDiffs[src_name_key].value, DstDiffs[dst_name_key].value
