from difflib import unified_diff

__all__ = ["get_unidiff_text"]


def get_unidiff_text(a: list[str], b: list[str], filename: str) -> str:
    from_file, to_file = f"original/{filename}", f"fixed/{filename}"
    diff = unified_diff(a=a, b=b, fromfile=from_file, tofile=to_file)
    text = ""
    for line in diff:
        text += line
        # Work around missing newline (http://bugs.python.org/issue2142).
        if not line.endswith("\n"):
            text += "\n" + r"\ No newline at end of file" + "\n"
    return text
