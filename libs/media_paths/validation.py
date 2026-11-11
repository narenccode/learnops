import re
import unicodedata

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# Characters that turn a relative file path into something a URL parser or a
# filesystem reads differently: "\\" is a Windows separator, ":" starts a
# scheme ("https:") or a drive ("C:"), "?" and "#" start a query or fragment.
_FORBIDDEN_PATH_CHARS = frozenset("\\:?#")


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

    for char in path:
        if char in _FORBIDDEN_PATH_CHARS or char.isspace():
            return False
        # Unicode category "C*" covers control, format (e.g. bidi overrides),
        # surrogate, private-use and unassigned code points.
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


def require_positive_int(value: object, name: str) -> int:
    """Return the value if it is an int >= 1, otherwise raise a clear error."""
    # bool is a subclass of int in Python, so it must be excluded explicitly.
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer, got {type(value).__name__}")
    if value < 1:
        raise ValueError(f"{name} must be 1 or greater, got {value}")
    return value
