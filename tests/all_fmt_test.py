"""
Tests for the dry run diff of `__all__` assignments created in 'dry run' mode by
:func:`format_all()`.
"""
from pytest import mark

from mvdef.core.manifest.all_fmt import format_all

__all__ = ["test_format_short", "test_format_long"]


@mark.parametrize(
    "names",
    [
        [],
        ["A"],
        ["foo"],
        ["foo", "A"],
        ["abcdefghijklmnopqrstuvwxyz", "xxxxxxxxxxxxxxxxxxxxxxxxxx", "abcde", "xxxxx"],
    ],
)
def test_format_short(names):
    """
    Test that short/empty `__all__` assignments are correctly made on one line, using a
    simple version of the `format_all()` function (the part for short one-liners only).

    Test the upper limit using two 26-length strings plus two 5-length strings,
    comma-separated (x3) and each string-quoted (x4) for a line length of exactly 88:

        >>> assert 11 + 26*2 + 5*2 + 2*4 + 3*2 + 1 == 88
    """
    manif = format_all(names)
    all_pre = "__all__ = ["
    all_mid = ", ".join([f'"{name}"' for name in names])
    all_one_liner = all_pre + all_mid + "]"
    if len(all_mid) > (88):
        raise NotImplementedError("Multiline all is tested separately")
    assert manif == all_one_liner


@mark.parametrize(
    "names",
    [
        [*"abcdefghijklmnop"],
        ["Xabcdefghijklmnopqrstuvwxyz", "xxxxxxxxxxxxxxxxxxxxxxxxxx", "abcde", "xxxxx"],
    ],
)
def test_format_long(names):
    """
    Test that long `__all__` assignments are correctly split over multiple lines, using
    a simple version of the `format_all()` function (the part for multi-liners only).

    Test the lower limit by prepending one character ("X") to the name list that
    produces an exactly 88 character line from `test_format_short`.
    """
    manif = format_all(names)
    all_pre = "__all__ = [\n"
    all_mid = ",\n".join([f'    "{name}"' for name in names])
    all_multiliner = all_pre + all_mid + ",\n]"
    assert manif == all_multiliner
