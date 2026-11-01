"""Fixtures for the package-validator tests."""

from __future__ import annotations

import copy

import pytest
import yaml

from .helpers import EXAMPLE_DIR, Doc


@pytest.fixture
def example_doc() -> Doc:
    """A fresh copy of the example course.yaml for each test, safe to edit."""
    loaded: Doc = yaml.safe_load((EXAMPLE_DIR / "course.yaml").read_text("utf-8"))
    return copy.deepcopy(loaded)
