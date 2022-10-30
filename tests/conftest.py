"""
Fixtures to be used in tests without importing.
"""
from pytest import fixture

from .helpers.def_descriptor import DefDesc
from .helpers.expected import DstDiffs, SrcDiffs, StoredStdErr, StoredStdOut

__all__ = ["src", "dst", "stored_diffs", "stored_output", "stored_error"]


@fixture(scope="function")
def src(request) -> DefDesc:
    return DefDesc.lookup(name=request.param)


@fixture(scope="function")
def dst(request) -> DefDesc:
    name = request.param
    is_empty = name.startswith("solo_")
    return DefDesc(name=name, value="") if is_empty else DefDesc.lookup(name=name)


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


@fixture(scope="function")
def stored_output(request) -> str:
    """
    Get the STDOUT for a command (used for CLI tests).
    """
    return StoredStdOut[request.param].value


@fixture(scope="function")
def stored_error(request) -> str:
    """
    Get the STDERR for a command (used for CLI tests).
    """
    return StoredStdErr[request.param].value
