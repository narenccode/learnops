"""Shared contract library (PRD EXT-09): validators for the documents in `contracts/`.

Not to be confused with the repository folder `contracts/` (schemas and examples), which holds data,
not Python. Modules import this library; they never copy its code.

Public API: `validate_package`, `validate_course_document`, `ValidationConfig`, `ValidationReport`,
`Issue`, and the package sources `DirectorySource` / `PackageSource` / `FileState`.
"""

from .config import ConfigError, ValidationConfig
from .report import Issue, ValidationReport
from .source import DirectorySource, FileState, PackageSource
from .validate import validate_course_document, validate_package

__all__ = [
    "ConfigError",
    "DirectorySource",
    "FileState",
    "Issue",
    "PackageSource",
    "ValidationConfig",
    "ValidationReport",
    "validate_course_document",
    "validate_package",
]
