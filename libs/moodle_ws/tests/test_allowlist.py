"""The allow-list comes from the contract, and anything else is refused (B4 §2a, guide on Q1).

NOT shown here: that any function exists on Moodle 4.5 or 5.3 (lab check 1).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from moodle_ws import (
    MoodleConfigError,
    NotSupported,
    load_allowlist,
)
from moodle_ws.allowlist import EXAMPLE_PATH, SCHEMA_PATH


def contract_names() -> list[str]:
    document = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
    return [entry["name"] for entry in document["functions"]]


def write_list(path: Path, functions: list[dict[str, Any]]) -> Path:
    path.write_text(
        json.dumps({"schema": "learnops.moodle-ws/v1", "functions": functions}),
        encoding="utf-8",
    )
    return path


def test_the_list_equals_the_contract_example() -> None:
    names = contract_names()
    assert len(names) == 8
    assert set(load_allowlist().functions) == set(names)


@pytest.mark.parametrize("version", ["5.0", "4.4", "", " 4.5", "4.5.0"])
def test_an_unsupported_version_is_refused(version: str) -> None:
    allowlist = load_allowlist()
    with pytest.raises(NotSupported, match="not a version B4 supports"):
        allowlist.resolve("core_course_get_contents", version)


def test_supported_versions_come_from_the_schema() -> None:
    assert load_allowlist().moodle_versions == {"4.5", "5.3"}


def test_a_schema_without_a_version_list_fails_loudly(tmp_path: Path) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    del schema["$defs"]["function"]["properties"]["replacements"]
    changed = tmp_path / "schema.json"
    changed.write_text(json.dumps(schema), encoding="utf-8")
    with pytest.raises(MoodleConfigError, match="does not match its schema"):
        load_allowlist(schema_path=changed)


def test_a_missing_file_fails_loudly(tmp_path: Path) -> None:
    with pytest.raises(MoodleConfigError, match="could not be read") as caught:
        load_allowlist(tmp_path / "absent.json")
    assert caught.value.__context__ is None


def test_a_broken_file_fails_loudly(tmp_path: Path) -> None:
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    with pytest.raises(MoodleConfigError, match="could not be read"):
        load_allowlist(broken)


def test_a_file_that_breaks_the_schema_fails_loudly(tmp_path: Path) -> None:
    listed = write_list(tmp_path / "list.json", [{"name": "mod_example"}])
    with pytest.raises(MoodleConfigError, match="does not match its schema"):
        load_allowlist(listed)


def test_a_verification_field_is_refused_by_the_schema(tmp_path: Path) -> None:
    listed = write_list(
        tmp_path / "list.json",
        [{"name": "mod_example", "parameters": [], "verified": True}],
    )
    with pytest.raises(MoodleConfigError, match="does not match its schema"):
        load_allowlist(listed)


def test_a_duplicate_fails_loudly(tmp_path: Path) -> None:
    entry = {"name": "mod_example", "parameters": []}
    listed = write_list(tmp_path / "list.json", [entry, entry])
    with pytest.raises(MoodleConfigError, match="twice"):
        load_allowlist(listed)


def test_the_list_cannot_be_changed_after_loading() -> None:
    functions: Any = load_allowlist().functions
    with pytest.raises(TypeError):
        functions["core_user_get_users"] = {}
