"""Fixtures for the package-validator tests."""

from __future__ import annotations

import copy
import shutil
from pathlib import Path

import pytest
import yaml

from .helpers import EXAMPLE_DIR, Doc


@pytest.fixture
def example_doc() -> Doc:
    """A fresh copy of the example course.yaml for each test, safe to edit."""
    loaded: Doc = yaml.safe_load((EXAMPLE_DIR / "course.yaml").read_text("utf-8"))
    return copy.deepcopy(loaded)


@pytest.fixture
def package_dir(tmp_path: Path) -> Path:
    """A fresh copy of the example package folder. Its parent is `tmp_path`, so a test can put
    a file outside the package."""
    target = tmp_path / "package"
    shutil.copytree(EXAMPLE_DIR, target)
    return target
