"""The service-account token (PRD SEC-03, C-06).

Wrapped so that printing, logging or formatting a settings object can never show the value. Only a
transport calls reveal(). Pickling is refused, because a pickle would carry the raw value into a job
payload or a file. Copying returns the same object, so dataclass helpers still work.
"""

from __future__ import annotations

from typing import Any, Final, NoReturn, Self

from . import messages

MASK: Final = "***"


class Token:
    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        self._value = value

    def reveal(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"Token({MASK})"

    def __str__(self) -> str:
        return MASK

    def __format__(self, format_spec: str) -> str:
        return MASK

    def __reduce__(self) -> NoReturn:
        raise TypeError(messages.TOKEN_NOT_PICKLABLE)

    def __copy__(self) -> Self:
        return self

    def __deepcopy__(self, memo: dict[int, Any]) -> Self:
        return self
