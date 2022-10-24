import ast
from pathlib import Path

from pyflakes import reporter

from .check import Checker

__all__ = ["parse", "parse_file"]


def parse(
    codestring, *, file: str | Path = "", verbose: bool = False, **kwargs
) -> Checker | None:
    """
    kwargs::{escalate: bool = False, target_cls: bool = False, target_all: bool = False}
    """
    report = reporter._makeDefaultReporter()
    filename = str(file)
    try:
        tree = ast.parse(codestring, filename=filename)
    except SyntaxError as e:
        report.syntaxError(filename, e.args[0], e.lineno, e.offset, e.text)
    except Exception:
        report.unexpectedError(filename, "problem decoding source")
    else:
        w = Checker(tree, filename=filename, verbose=verbose, **kwargs)
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
    file: Path, *, verbose=False, ensure_exists=True, **kwargs
) -> Checker | None:
    if ensure_exists:
        assert file.exists() and file.is_file(), f"{file} is not an existing file"
    return parse(file.read_text(), file=file, verbose=verbose, **kwargs)
