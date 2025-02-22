"""
Tests for the files created by running mvdef with `dry_run=False`.
"""

from pytest import mark

from mvdef.core.text_diff import get_unidiff_text

from .helpers.cli_util import run_cmd
from .helpers.io import Write

__all__ = ["test_move"]


@mark.parametrize(
    "mv,cls_defs,stored_diffs",
    [
        (["A"], True, "fooA2bar_A"),
        (["foo"], False, "fooA2bar_foo"),
    ],
    indirect=["stored_diffs"],
)
@mark.parametrize("src,dst", [("fooA", "bar")], indirect=True)
def test_move(tmp_path, src, dst, mv, cls_defs, stored_diffs):
    """
    Test that a class 'A' or a funcdef 'foo' is moved correctly when not on 'dry run'
    (i.e. that actually moving matches the dry run result that just previews a move).
    """
    src_p, dst_p = Write.from_enums(src, dst, path=tmp_path).file_paths
    mover = run_cmd(src_p, dst_p, mv=mv, cls_defs=cls_defs).mover
    assert mover.src_diff.old_code == src.value
    assert mover.dst_diff.old_code == dst.value
    src_diff, dst_diff = (
        get_unidiff_text(a, b, filename=path.name)
        for content, path in [(src, src_p), (dst, dst_p)]
        for a_str, b_str in [(content.value, path.read_text())]
        for a, b in [
            tuple(
                lines.splitlines(keepends=True)
                for tup in [(a_str, b_str)]
                for lines in tup
            ),
        ]
    )
    assert (src_diff, dst_diff) == stored_diffs
