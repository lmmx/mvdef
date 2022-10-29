from pytest import mark

from mvdef.text_diff import get_unidiff_text

from .helpers.cli_util import get_mvdef_mover
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
    mover = get_mvdef_mover(src_p, dst_p, mv=mv, cls_defs=cls_defs)
    src_diff, dst_diff = (
        get_unidiff_text(content.value, path.read_text(), filename=path.name)
        for content, path in [(src, src_p), (dst, dst_p)]
    )
    assert src_diff, dst_diff == stored_diffs
