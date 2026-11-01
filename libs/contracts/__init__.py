"""Shared contract library (PRD EXT-09): validators for the documents in `contracts/`.

Not to be confused with the repository folder `contracts/` (schemas and examples), which holds data,
not Python. Modules import this library; they never copy its code.

Public API: `validate_course_document`, `ValidationReport` and `Issue`.
"""

from .report import Issue, ValidationReport
from .validate import validate_course_document

__all__ = [
    "Issue",
    "ValidationReport",
    "validate_course_document",
]
