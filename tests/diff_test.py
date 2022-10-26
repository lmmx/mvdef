from pytest import mark

import mvdef

__all__ = ["create_named_tmp_files"]


@mark.parametrize("A,B", [("""aaa""", """bbb""")])
def test_create_named_tmp_files(tmp_path, A, B):
    foo, bar = (tmp_path / f for f in ("foo.txt", "bar.txt"))
    foo.write_text(A)
    bar.write_text(B)
    assert foo.read_text() == A
    assert bar.read_text() == B
    assert len([*tmp_path.iterdir()]) == 2
