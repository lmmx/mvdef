"""
Tests for the parsing module (file and codestring parsing).
"""
from pytest import mark, raises

from mvdef.parse import parse, parse_file

from .helpers.io import Write

__all__ = [
    "test_parse_successfully",
    "test_parse_syntax_error",
    "test_parse_type_error",
    "test_parse_file_error",
    "test_parse_file_deleted",
]


@mark.parametrize("src,dst", [("fooA", "bar")], indirect=True)
def test_parse_successfully(tmp_path, src, dst):
    """
    Test that a simple program can be parsed.
    """
    written = Write.from_enums(src, dst, path=tmp_path)
    src_parsed, dst_parsed = (
        parse(codestring=content, file=filename)
        for content, filename in zip(written.contents, written.names)
    )
    for parsed, filename in zip([src_parsed, dst_parsed], written.names):
        assert parsed.filename == filename
        assert parsed.target_all is False
        assert parsed.target_cls is False
        assert parsed.target_defs == parsed.funcdefs
    assert (src_parsed.code, dst_parsed.code) == written.contents
    assert [d.name for d in src_parsed.alldefs] == ["foo", "A"]
    assert [d.name for d in dst_parsed.alldefs] == ["bar"]
    assert [cd.name for cd in src_parsed.classdefs] == ["A"]
    assert dst_parsed.classdefs == []
    assert [fd.name for fd in src_parsed.funcdefs] == ["foo"]
    assert [fd.name for fd in dst_parsed.funcdefs] == ["bar"]


@mark.parametrize("escalate", [True, False])
@mark.parametrize("bad_content", ["0 = 1\n"])
@mark.parametrize("stored_error", ["REJECT_0_EQ_1"], indirect=["stored_error"])
@mark.parametrize("src,dst", [("fooA", "bar")], indirect=True)
def test_parse_syntax_error(
    capsys, tmp_path, escalate, bad_content, stored_error, src, dst
):
    """
    Test that a simple program with invalid syntax cannot be parsed, and that it
    produces an error message indicating the cause of the error in the code.

    Files are created to get their names in a standardised way, but `parse()` is used,
    not `parse_file()`, which is tested in `test_parse_file_error()` below.
    """
    written = Write.from_enums(src, dst, path=tmp_path)
    for filename in written.names:
        if escalate:
            with raises(SyntaxError):
                parsed = parse(codestring=bad_content, file=filename, escalate=escalate)
        else:
            parsed = parse(codestring=bad_content, file=filename, escalate=escalate)
            assert parsed is None
        captured = capsys.readouterr()
        stderr_cut = captured.err.split(":", 1)[1]
        assert stderr_cut == stored_error


@mark.parametrize("escalate", [True, False])
@mark.parametrize("bad_content", [0, ["0 = 1"]])
@mark.parametrize("stored_error", ["PROBLEM_DECODING"], indirect=["stored_error"])
@mark.parametrize("src,dst", [("fooA", "bar")], indirect=True)
def test_parse_type_error(
    capsys, tmp_path, escalate, bad_content, stored_error, src, dst
):
    """
    Test that passing an invalid type to `ast.parse` fails appropriately, and
    produces an error message indicating the cause of the error in the code.
    """
    written = Write.from_enums(src, dst, path=tmp_path)
    for filename in written.names:
        if escalate:
            with raises(TypeError):
                parsed = parse(codestring=bad_content, file=filename, escalate=escalate)
        else:
            parsed = parse(codestring=bad_content, file=filename, escalate=escalate)
            assert parsed is None
        captured = capsys.readouterr()
        stderr_cut = captured.err.split(":", 1)[1]
        assert stderr_cut == stored_error


@mark.parametrize("escalate", [True, False])
@mark.parametrize("bad_content", ["0 = 1\n"])
@mark.parametrize("stored_error", ["REJECT_0_EQ_1"], indirect=["stored_error"])
@mark.parametrize("src,dst", [("fooA", "bar")], indirect=True)
def test_parse_file_error(
    capsys, tmp_path, escalate, bad_content, stored_error, src, dst
):
    """
    Test that a simple program with invalid syntax cannot be parsed, and that it
    produces an error message indicating the cause of the error in the code.
    """
    written = Write.from_enums(src, dst, path=tmp_path)
    input_paths = written.file_paths
    for p in input_paths:
        p.write_text("0 = 1\n")
    for p in input_paths:
        if escalate:
            with raises(SyntaxError):
                parsed = parse_file(p, escalate=escalate)
        else:
            parsed = parse_file(p, escalate=escalate)
            assert parsed is None
        captured = capsys.readouterr()
        stderr_cut = captured.err.split(":", 1)[1]
        assert stderr_cut == stored_error


@mark.parametrize("escalate", [True, False])
@mark.parametrize("stored_error", ["REJECT_0_EQ_1"], indirect=["stored_error"])
@mark.parametrize("src,dst", [("fooA", "bar")], indirect=True)
def test_parse_file_deleted(capsys, tmp_path, escalate, stored_error, src, dst):
    """
    Test that an error is thrown as expected if the file was deleted, and that it
    produces an error message indicating this.
    """
    written = Write.from_enums(src, dst, path=tmp_path)
    input_paths = written.file_paths
    for p in input_paths:
        p.unlink()
    for p in input_paths:
        with raises(FileNotFoundError):
            parse_file(p, escalate=escalate)
        # TODO: fix #48
        # parsed = parse_file(p, escalate=escalate)
        # assert parsed is None
        # captured = capsys.readouterr()
        # stderr_cut = captured.err.split(":", 1)[1]
        # assert stderr_cut == ""  # stored_error
