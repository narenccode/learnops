import re
from pathlib import PurePosixPath


SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate_slug(slug: str) -> bool:
    """Check whether a slug uses lowercase ASCII letters, digits and single hyphens."""
    return bool(SLUG_PATTERN.fullmatch(slug))


def validate_relative_path(path: str) -> bool:
    """Check whether a path is a safe relative POSIX-style media path."""
    if not path or "\\" in path:
        return False

    if path.startswith("/") or "://" in path:
        return False

    if any(char.isspace() for char in path):
        return False

    parts = path.split("/")

    if any(part in ("", ".", "..") for part in parts):
        return False

    if re.match(r"^[a-zA-Z]:", parts[0]):
        return False

    return PurePosixPath(path).is_relative_to(PurePosixPath("."))
