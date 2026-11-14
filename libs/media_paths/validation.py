import re
import unicodedata

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# The rule below is the B6.3 contract's `$defs/relative_path` pattern
# (contracts/lesson-manifest.v1.schema.json, PR #32), which the guide made the
# single source of truth for both (PR #38, 2026-11-08). Keep them identical.
#
# Characters a URL parser or a filesystem reads differently: "\\" is a Windows
# separator, "?" and "#" start a query or fragment.
_FORBIDDEN_PATH_CHARS = frozenset("\\?#")

# A URL scheme ("https:", "s3:") or a drive letter ("C:") at the very start.
# A colon anywhere else ("notes/b:c.md") or after a leading digit ("12:30.mp4")
# is an ordinary file-name character, as in the contract.
_SCHEME_OR_DRIVE_PREFIX = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:")


def validate_slug(slug: object) -> bool:
    """Check whether a slug uses lowercase ASCII letters, digits and single hyphens."""
    return isinstance(slug, str) and SLUG_PATTERN.fullmatch(slug) is not None


def validate_relative_path(path: object) -> bool:
    """Check whether a path is a safe relative POSIX-style media path (PRD C-08).

    Each "/"-separated segment must be non-empty and must not be "." or "..",
    so traversal is rejected segment by segment rather than by prefix checks.
    """
    if not isinstance(path, str) or not path:
        return False

    if _SCHEME_OR_DRIVE_PREFIX.match(path):
        return False

    for char in path:
        if char in _FORBIDDEN_PATH_CHARS or char.isspace():
            return False
        # OPEN, waiting for the guide: this is stricter than the contract.
        # Unicode category "C*" (control, format such as bidi overrides,
        # surrogate, private-use, unassigned) is rejected here, as the PR #38
        # review asked, but the B6.3 pattern accepts these characters. Keep or
        # drop it only together with the contract.
        if unicodedata.category(char).startswith("C"):
            return False

    # A leading "/" (absolute path) produces an empty first segment.
    return all(segment not in ("", ".", "..") for segment in path.split("/"))


def require_slug(value: object, name: str) -> str:
    """Return the value if it is a valid slug, otherwise raise a clear error."""
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string, got {type(value).__name__}")
    if not validate_slug(value):
        raise ValueError(
            f"{name} must be a slug: lowercase ASCII letters and digits "
            f"separated by single hyphens (for example 'build-ai-assistant'), "
            f"got {value!r}"
        )
    return value


def _require_int(value: object, name: str) -> int:
    # bool is a subclass of int in Python, so it must be excluded explicitly.
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer, got {type(value).__name__}")
    return value


def require_positive_int(value: object, name: str) -> int:
    """Return the value if it is an int >= 1, otherwise raise a clear error."""
    number = _require_int(value, name)
    if number < 1:
        raise ValueError(f"{name} must be 1 or greater, got {number}")
    return number


def require_int_in_range(value: object, name: str, minimum: int, maximum: int) -> int:
    """Return the value if it is an int in [minimum, maximum], else raise."""
    number = _require_int(value, name)
    if not minimum <= number <= maximum:
        raise ValueError(
            f"{name} must be between {minimum} and {maximum}, got {number}"
        )
    return number
