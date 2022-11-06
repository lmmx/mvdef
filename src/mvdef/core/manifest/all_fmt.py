from textwrap import indent

__all__ = ["format_all"]


def format_all(names: list[str], max_line_len: int = 88) -> str:
    _check_valid(names)
    template = "__all__ = [{}]"
    quoted_names = [repr(name).replace("'", '"') for name in names]
    sep = ", "
    mid = sep.join(quoted_names)
    if len(template.format(mid)) > max_line_len:
        multiline_mid = ",\n".join(quoted_names)
        mid_body = indent(multiline_mid, " " * 4)
        mid = f"\n{mid_body},\n"
    return template.format(mid)


def _check_valid(names: list[str]) -> None:
    if not isinstance(names, list):
        raise TypeError(f"Did not receive a list to format: {names=}")
    if not isinstance(next(iter(names), ""), str):
        raise TypeError(f"Did not receive a list of strings to format: {names=}")
