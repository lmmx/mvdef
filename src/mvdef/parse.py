import ast
from pathlib import Path

from pyflakes import reporter

from .check import Checker
from .exceptions import SrcNotFound

__all__ = ["parse", "parse_file", "reparse"]


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
        if kwargs.get("escalate", False):
            raise
    except Exception:
        report.unexpectedError(filename, "problem decoding source")
        if kwargs.get("escalate", False):
            raise
    else:
        w = Checker(tree, code=codestring, filename=filename, verbose=verbose, **kwargs)
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
        if not file.exists() and file.is_file():
            raise SrcNotFound(f"{file} is not an existing file")
    return parse(file.read_text(), file=file, verbose=verbose, **kwargs)


def reparse(check: Checker, input_text: str) -> Checker:
    """
    Parse new text with the settings from an existing parsed result (a `Checker` object).

    Create a new Checker with the same settings as the current instaance, but change
    the input file contents (equivalent to overwriting the file and parsing it again).
    """
    check_settings = {
        "verbose": check.verbose,
        "escalate": check.escalate,
        "cls_defs": check.target_cls,
        "all_defs": check.target_all,
    }
    # if input_text == "x = 1\n\n\nclass A:\n\n\ny = 2\n":
    #     raise ValueError("WTF")
    return parse(input_text, file=check.filename, **check_settings)
