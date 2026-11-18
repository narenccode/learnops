"""Trusted, server-side tool routing.

The tool is chosen by the launch path (`/lti/launch/<tool>`), which is set in the Moodle tool
registration, and is checked against this fixed list. The destination always comes from
configuration; the browser never supplies a redirect URL.
"""

from __future__ import annotations

from enum import StrEnum


class Tool(StrEnum):
    VIDEO = "video"
    GRADING = "grading"


# Both baseline tools accept the two B3 v1 roles. Learner never reaches here: it is refused
# during verification (PRD EXT-07), and this check refuses it again if it ever did.
ALLOWED_ROLES: dict[Tool, frozenset[str]] = {
    Tool.VIDEO: frozenset({"mentor", "administrator"}),
    Tool.GRADING: frozenset({"mentor", "administrator"}),
}


def parse_tool(value: str) -> Tool | None:
    """Return the tool for an exact, known name, or None. No case folding or aliases."""
    try:
        return Tool(value)
    except ValueError:
        return None


def role_allowed(tool: Tool, role: str) -> bool:
    return role in ALLOWED_ROLES[tool]
