"""Grade values as exact numbers (B4 rule R9: exact numeric match after parsing, no tolerance).

Moodle returns a stored grade as text, for example "84.50000" (B4 §6a); the number of decimals is
not verified (lab check 13). Comparing text would call "84.5" and "84.50000" different, and
comparing floats can make two different decimals equal, so both sides become Decimal.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Final

# Plain decimal notation only: no sign other than "-", no exponent, no spaces, no "NaN".
_DECIMAL_TEXT: Final = re.compile(r"-?(?:\d+(?:\.\d*)?|\.\d+)")


def parse_grade(value: object) -> Decimal | None:
    """The value as an exact, finite Decimal, or None if it is not a plain number.

    bool is refused although Python treats it as an int: True is never a grade.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        # repr() gives the shortest text that reads back as the same float, so 0.1 is 0.1 and not
        # its binary expansion.
        text = repr(value)
    elif isinstance(value, str):
        text = value
    else:
        return None
    if not _DECIMAL_TEXT.fullmatch(text):
        return None
    try:
        number = Decimal(text)
    except InvalidOperation:
        # Not reachable after the pattern; kept so no parsing error can escape.
        return None
    return number if number.is_finite() else None


def grade_in_range(grade: object, max_grade: object) -> bool:
    """True if both parse and 0 <= grade <= max_grade (R9: checked before writing)."""
    number = parse_grade(grade)
    maximum = parse_grade(max_grade)
    if number is None or maximum is None or maximum < 0:
        return False
    return Decimal(0) <= number <= maximum
