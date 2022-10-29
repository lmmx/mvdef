from sys import stderr

from .exceptions import CheckFailure

__all__ = ["FailableMixIn"]


class FailableMixIn:
    def err(self, msg) -> None:
        print(msg, file=stderr)

    def fail(self, msg) -> CheckFailure | None:
        exc = CheckFailure(msg)
        if self.escalate:
            raise exc
        else:
            self.err(msg)
            return exc
