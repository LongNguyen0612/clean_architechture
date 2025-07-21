from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Literal

from result import Err as ResultError
from result import Ok as ResultOk
from result import Result, is_err, is_ok


class Err(ResultError):
    def is_err(self) -> Literal[True]:
        return True

    def is_ok(self) -> Literal[False]:
        return False


class Ok(ResultOk):
    def is_err(self) -> Literal[False]:
        return False

    def is_ok(self) -> Literal[True]:
        return True


@dataclass(frozen=True, kw_only=True)
class Error:
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    code: str
    message: str
    reason: str | dict | Exception | Error = ""
    retryable: bool = False

    def to_dict(self):
        return {
            "error_code": self.code,
            "message": self.message,
            "error_id": self.id,
            "reason": self.reason,
        }

    def public(self):
        return {
            "error_code": self.code,
            "message": self.message,
            "error_id": self.id,
        }

    def __repr__(self):
        return f"Error(message={self.message}, id={self.id}, code={self.code}, reason={self.reason})"


class Return:
    @staticmethod
    def ok(value) -> Ok:
        return Ok(value)

    @staticmethod
    def err(error: Error) -> Err:
        return Err(error)


__all__ = ["Result", "Error", "Err", "Ok", "is_err", "is_ok", "Return"]