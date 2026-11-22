"""Keeps tokens and full URLs out of logs and errors (design §4.1, PRD OPS-04).

redact() replaces token values, not a named URL parameter: B4 does not yet say how a token is sent
(lab checks 1 and 10), so matching on a parameter name would be a guess. sanitize() also cuts every
URL down to scheme and host, because a full request URL must never be logged.
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from typing import Any, Final
from urllib.parse import quote, urlsplit

from . import messages
from .secrets import MASK, Token

_URL: Final = re.compile(r"[a-z][a-z0-9+.-]*://\S+", re.IGNORECASE)
MAX_DEPTH: Final = 32
_STANDARD_FIELDS: Final = frozenset(vars(logging.makeLogRecord({})))


def redact(text: str, tokens: Iterable[Token]) -> str:
    forms = {form for t in tokens for form in (t.reveal(), quote(t.reveal(), safe=""))}
    # Longest first, so a token inside a longer one cannot leave the rest of that one visible.
    for form in sorted(filter(None, forms), key=len, reverse=True):
        text = text.replace(form, MASK)
    return text


def safe_url(url: str) -> str:
    """Scheme and host only, the most of a request URL that may be logged."""
    try:
        parts = urlsplit(url)
        host = parts.hostname
    except ValueError:
        return MASK
    if not parts.scheme or not host:
        return MASK
    shown = f"[{host}]" if ":" in host else host
    return f"{parts.scheme}://{shown}"


def sanitize(text: str, tokens: Iterable[Token]) -> str:
    """Safe to log or show: URLs cut to scheme and host, then token values removed."""
    return redact(_URL.sub(lambda match: safe_url(match.group()), text), tokens)


def sanitize_value(
    value: Any, tokens: Iterable[Token], _path: frozenset[int] = frozenset()
) -> Any:
    """sanitize() through dicts, lists, tuples, sets and frozensets, keys included. Numbers, booleans
    and None pass. Everything else is masked, because its text cannot be trusted or checked: other
    objects, bytes, subclasses of plain types, a structure containing itself, and anything deeper
    than MAX_DEPTH."""
    kind = type(value)
    if kind is str:
        return sanitize(value, tokens)
    if kind in (bool, int, float, type(None)):
        return value
    if (
        kind not in (dict, list, tuple, set, frozenset)
        or id(value) in _path
        or len(_path) >= MAX_DEPTH
    ):
        return MASK
    path = _path | {id(value)}
    tokens = tuple(tokens)
    if kind is dict:
        return {
            sanitize_value(k, tokens, path): sanitize_value(v, tokens, path)
            for k, v in value.items()
        }
    cleaned = [sanitize_value(item, tokens, path) for item in value]
    return cleaned if kind is list else kind(cleaned)


def _message(record: logging.LogRecord) -> str:
    try:
        return record.getMessage()
    except (TypeError, ValueError):  # arguments that do not fit the format string
        return str(record.msg)


class RedactingFilter(logging.Filter):
    """Attach to a log handler. Cleans the message and any exception text before it is written."""

    def __init__(self, tokens: Iterable[Token]) -> None:
        super().__init__()
        self._tokens = tuple(tokens)

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            self._clean(record)
        except Exception:
            _discard(record)
        return True

    def _clean(self, record: logging.LogRecord) -> None:
        record.msg = sanitize(_message(record), self._tokens)
        record.args = None
        if record.exc_info:
            formatted = logging.Formatter().formatException(record.exc_info)
            record.exc_text = formatted
            record.exc_info = None
        # Every field, because structured logs (OPS-04) also write the `extra` fields.
        for name, value in vars(record).items():
            setattr(record, name, sanitize_value(value, self._tokens))


def _discard(record: logging.LogRecord) -> None:
    """Fail closed: a record that could not be cleaned keeps none of the caller's content."""
    record.msg = messages.LOG_NOT_CLEANED
    record.args = None
    record.exc_info = None
    record.exc_text = None
    record.stack_info = None
    for name in set(vars(record)) - _STANDARD_FIELDS:
        delattr(record, name)
