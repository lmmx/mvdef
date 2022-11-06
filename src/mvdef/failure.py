from sys import stderr

from .error_handling.exceptions import CheckFailure

__all__ = ["FailableMixIn"]


class FailableMixIn:
    def err(self, msg) -> None:
        print(msg, file=stderr)

    def fail(self, msg, exc_info=None) -> CheckFailure | None:
        exc = CheckFailure(msg)
        if self.escalate:
            if exc_info is None:
                raise exc
            else:
                raise exc_info from exc
        else:
            self.err(msg)
            return exc
