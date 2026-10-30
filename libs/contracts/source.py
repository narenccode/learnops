"""Where a package's files come from. A folder today; the validator only needs these two calls."""

from __future__ import annotations

import enum
from pathlib import Path
from typing import Protocol


class FileState(enum.Enum):
    OK = "ok"
    MISSING = "missing"
    NOT_A_FILE = "not_a_file"
    OUTSIDE_PACKAGE = "outside_package"


class PackageSource(Protocol):
    def file_state(self, rel: str) -> FileState:
        """State of the file at a package-relative path, without reading it."""
        ...

    def read_text(self, rel: str) -> str:
        """The UTF-8 text of a file; FileNotFoundError unless `file_state` is OK."""
        ...


class DirectorySource:
    """A package stored in a folder. Nothing outside the folder is ever read, including through
    `..`, absolute paths or symbolic links."""

    def __init__(self, root: Path) -> None:
        self._root = Path(root).resolve()

    def file_state(self, rel: str) -> FileState:
        try:
            resolved = (self._root / rel).resolve()
        except (OSError, ValueError):
            return FileState.MISSING
        if not resolved.is_relative_to(self._root):
            return FileState.OUTSIDE_PACKAGE
        if not resolved.exists():
            return FileState.MISSING
        if not resolved.is_file():
            return FileState.NOT_A_FILE
        return FileState.OK

    def read_text(self, rel: str) -> str:
        if self.file_state(rel) is not FileState.OK:
            raise FileNotFoundError(rel)
        return (self._root / rel).resolve().read_text(encoding="utf-8")
