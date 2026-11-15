import re
from bisect import bisect_right

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# The rule below is the B6.3 contract's `$defs/relative_path` pattern
# (contracts/lesson-manifest.v1.schema.json, PR #32), which the guide made the
# single source of truth for both (PR #38, 2026-11-08). Keep them identical.
#
# Characters a URL parser or a filesystem reads differently: "\\" is a Windows
# separator, "?" and "#" start a query or fragment. "%" is rejected anywhere
# (guide decision on PR #32, 2026-11-15): the 'none' signer appends the path to
# the media base URL, and layers that decode a path, once or more, could turn
# any encoded form (%2e, %252e, %25%32%65, ...) into a dot or separator.
# Rejecting the sign covers every depth; our paths have no use for a literal %.
_FORBIDDEN_PATH_CHARS = frozenset("\\?#%")

# A URL scheme ("https:", "s3:") or a drive letter ("C:") at the very start.
# A colon anywhere else ("notes/b:c.md") or after a leading digit ("12:30.mp4")
# is an ordinary file-name character, as in the contract.
_SCHEME_OR_DRIVE_PREFIX = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:")

# Guide decision (PR #38): reject Unicode category Cc (control characters) and the
# complete category Cf (format characters: bidi controls such as U+061C and U+202E,
# zero-width characters, the BOM, the soft hyphen). Co (private use), Cs
# (surrogates) and Cn (unassigned) are not rejected as categories.
#
# The ranges are written out, not read from unicodedata at run time, so that a
# Python upgrade with a newer Unicode table cannot change the rule silently. They
# are copied from the Unicode Character Database, version UNICODE_VERSION:
# https://www.unicode.org/Public/15.0.0/ucd/extracted/DerivedGeneralCategory.txt
# The B6.3 `$defs/relative_path` pattern lists the same ranges (PR #32). A test
# compares these tables with the running Python and fails if they differ.
UNICODE_VERSION = "15.0.0"

CC_RANGES: tuple[tuple[int, int], ...] = (
    (0x0000, 0x001F),  # C0 controls
    (0x007F, 0x009F),  # DEL and C1 controls
)

CF_RANGES: tuple[tuple[int, int], ...] = (
    (0x00AD, 0x00AD),  # SOFT HYPHEN
    (0x0600, 0x0605),  # ARABIC NUMBER SIGN..ARABIC NUMBER MARK ABOVE
    (0x061C, 0x061C),  # ARABIC LETTER MARK
    (0x06DD, 0x06DD),  # ARABIC END OF AYAH
    (0x070F, 0x070F),  # SYRIAC ABBREVIATION MARK
    (0x0890, 0x0891),  # ARABIC POUND MARK ABOVE..ARABIC PIASTRE MARK ABOVE
    (0x08E2, 0x08E2),  # ARABIC DISPUTED END OF AYAH
    (0x180E, 0x180E),  # MONGOLIAN VOWEL SEPARATOR
    (0x200B, 0x200F),  # ZERO WIDTH SPACE..RIGHT-TO-LEFT MARK
    (0x202A, 0x202E),  # LEFT-TO-RIGHT EMBEDDING..RIGHT-TO-LEFT OVERRIDE
    (0x2060, 0x2064),  # WORD JOINER..INVISIBLE PLUS
    (0x2066, 0x206F),  # LEFT-TO-RIGHT ISOLATE..NOMINAL DIGIT SHAPES
    (0xFEFF, 0xFEFF),  # ZERO WIDTH NO-BREAK SPACE (BOM)
    (0xFFF9, 0xFFFB),  # INTERLINEAR ANNOTATION ANCHOR..TERMINATOR
    (0x110BD, 0x110BD),  # KAITHI NUMBER SIGN
    (0x110CD, 0x110CD),  # KAITHI NUMBER SIGN ABOVE
    (0x13430, 0x1343F),  # EGYPTIAN HIEROGLYPH VERTICAL JOINER..END WALLED ENCLOSURE
    (0x1BCA0, 0x1BCA3),  # SHORTHAND FORMAT LETTER OVERLAP..SHORTHAND FORMAT UP STEP
    (0x1D173, 0x1D17A),  # MUSICAL SYMBOL BEGIN BEAM..MUSICAL SYMBOL END PHRASE
    (0xE0001, 0xE0001),  # LANGUAGE TAG
    (0xE0020, 0xE007F),  # TAG SPACE..CANCEL TAG
)

_FORBIDDEN_RANGES = tuple(sorted(CC_RANGES + CF_RANGES))
_FORBIDDEN_STARTS = tuple(start for start, _ in _FORBIDDEN_RANGES)


def _is_control_or_format(char: str) -> bool:
    # The ranges are sorted and do not overlap, so only the range starting at or
    # before this code point can contain it.
    code_point = ord(char)
    index = bisect_right(_FORBIDDEN_STARTS, code_point) - 1
    return index >= 0 and code_point <= _FORBIDDEN_RANGES[index][1]


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
        if _is_control_or_format(char):
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
