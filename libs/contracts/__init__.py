"""Shared contract library (PRD EXT-09): validators for the documents in `contracts/`.

Not to be confused with the repository folder `contracts/` (schemas and examples), which holds data,
not Python. Modules import this library; they never copy its code.

Public API: `validate_package` with `DirectorySource` (a package folder; `PackageSource` and
`FileState` describe any other source), `validate_course_document` (a parsed course.yaml),
`ValidationConfig`, `ConfigError`, `ValidationReport` and `Issue`. For the lesson files of PRD B6.2:
`validate_chapters`, `validate_slides`, `validate_cues`, `readable_cues`, `cue_is_required` and
`check_within_duration`.
"""

from .config import ConfigError, ValidationConfig
from .lesson_files import (
    check_within_duration,
    cue_is_required,
    readable_cues,
    validate_chapters,
    validate_cues,
    validate_slides,
)
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
    "check_within_duration",
    "cue_is_required",
    "readable_cues",
    "validate_chapters",
    "validate_course_document",
    "validate_cues",
    "validate_package",
    "validate_slides",
]
