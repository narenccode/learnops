"""Schemas of the test-only example_echo task (prompts/example_echo/v1.md)."""

from __future__ import annotations

from typing import Any, Final

ECHO_INPUT: Final[dict[str, Any]] = {
    "type": "object",
    "required": ["text"],
    "properties": {"text": {"type": "string"}},
    "additionalProperties": False,
}
ECHO_OUTPUT: Final[dict[str, Any]] = {
    "type": "object",
    "required": ["echo"],
    "properties": {"echo": {"type": "string"}},
    "additionalProperties": False,
}
