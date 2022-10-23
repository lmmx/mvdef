import ast
from pathlib import Path

from pyflakes import reporter

from .check import Checker

__all__ = ["parse", "parse_file"]


def parse(
    codestring, *, file: str | Path = "", verbose: bool = False, escalate: bool = False
) -> Checker | None:
    report = reporter._makeDefaultReporter()
    filename = str(file)
    try:
        tree = ast.parse(codestring, filename=filename)
    except SyntaxError as e:
        report.syntaxError(filename, e.args[0], e.lineno, e.offset, e.text)
    except Exception:
        report.unexpectedError(filename, "problem decoding source")
    else:
        w = Checker(tree, filename=filename, verbose=verbose, escalate=escalate)
        w.messages.sort(key=lambda m: m.lineno)
        if verbose:
            for m in w.messages:
                print(
                    f"• {type(m).__name__} {list(m.message_args)}",
                    f"L{m.lineno} col {m.col} in {filename or 'STDIN'}",
                )
        return w
    return None


def parse_file(
    file: Path, *, verbose=False, escalate=False, ensure_exists=True
) -> Checker | None:
    if ensure_exists:
        assert file.exists() and file.is_file(), f"{file} is not an existing file"
    return parse(file.read_text(), file=file, verbose=verbose, escalate=escalate)
