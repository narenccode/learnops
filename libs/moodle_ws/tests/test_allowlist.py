"""The allow-list comes from the contract, and anything else is refused (B4 §2a, guide on Q1).

NOT shown here: that any function exists on Moodle 4.5 or 5.3 (lab check 1).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from moodle_ws import (
    AllowList,
    FunctionNotAllowed,
    MoodleClient,
    MoodleConfigError,
    NotSupported,
    SiteSettings,
    load_allowlist,
    messages,
)
from moodle_ws.allowlist import EXAMPLE_PATH, SCHEMA_PATH

from .fake_transport import FakeTransport


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


@pytest.mark.parametrize("function", contract_names())
def test_every_listed_read_or_flag_function_reaches_the_transport(
    function: str, settings: SiteSettings
) -> None:
    transport = FakeTransport()
    params = (
        {"workflowstate": "readyforrelease"} if function.endswith("save_grade") else {}
    )
    assert MoodleClient(settings, transport).call(function, params) == "scripted answer"
    assert [name for name, _ in transport.calls] == [function]


@pytest.mark.parametrize(
    "function",
    [
        "core_user_get_users",
        "MOD_ASSIGN_GET_ASSIGNMENTS",
        "Mod_assign_get_assignments",
        " mod_assign_get_assignments",
        "mod_assign_get_assignments ",
        "mod_assign_get_assignments\n",
        "mod_assign_get_assignment",
        "",
    ],
)
def test_anything_else_is_refused_before_the_transport(
    function: str, settings: SiteSettings
) -> None:
    transport = FakeTransport()
    with pytest.raises(FunctionNotAllowed):
        MoodleClient(settings, transport).call(function)
    assert transport.calls == []


def test_a_replacement_applies_only_to_its_version(
    tmp_path: Path, settings: SiteSettings
) -> None:
    listed = write_list(
        tmp_path / "list.json",
        [
            {
                "name": "mod_example_old",
                "parameters": [],
                "replacements": [{"moodle_version": "5.3", "name": "mod_example_new"}],
            }
        ],
    )
    allowlist = load_allowlist(listed)
    assert allowlist.resolve("mod_example_old", "4.5") == "mod_example_old"
    assert allowlist.resolve("mod_example_old", "5.3") == "mod_example_new"
    with pytest.raises(FunctionNotAllowed):
        allowlist.resolve("mod_example_new", "5.3")

    transport = FakeTransport()
    MoodleClient(settings, transport, allowlist).call("mod_example_old")
    assert transport.calls == [("mod_example_old", {})]


@pytest.mark.parametrize("version", ["5.0", "4.4", "", " 4.5", "4.5.0"])
def test_an_unsupported_version_is_refused(version: str) -> None:
    allowlist = load_allowlist()
    with pytest.raises(NotSupported, match="not a version B4 supports"):
        allowlist.resolve("core_course_get_contents", version)


def test_a_site_outside_the_supported_versions_never_reaches_the_transport(
    settings: SiteSettings,
) -> None:
    only_53 = AllowList(load_allowlist().functions, frozenset({"5.3"}))
    transport = FakeTransport()
    with pytest.raises(NotSupported):
        MoodleClient(settings, transport, only_53).call("core_course_get_contents")
    assert transport.calls == []


def test_supported_versions_come_from_the_schema() -> None:
    assert load_allowlist().moodle_versions == {"4.5", "5.3"}


def test_a_schema_without_a_version_list_fails_loudly(tmp_path: Path) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    del schema["$defs"]["function"]["properties"]["replacements"]
    changed = tmp_path / "schema.json"
    changed.write_text(json.dumps(schema), encoding="utf-8")
    with pytest.raises(MoodleConfigError, match="does not match its schema"):
        load_allowlist(schema_path=changed)


def test_empty_parameters_are_not_enforced(settings: SiteSettings) -> None:
    """Empty means "not yet determined" (B4 §2a), so any parameter still reaches the transport."""
    transport = FakeTransport()
    client = MoodleClient(settings, transport)
    client.call("core_course_get_contents", {"anything": 1})
    assert transport.calls == [("core_course_get_contents", {"anything": 1})]


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


# --- the refusal itself (B4 §2a: the library must refuse any other function) -----------------

VERSIONS = ("4.5", "5.3")


@pytest.mark.parametrize("version", VERSIONS)
@pytest.mark.parametrize(
    "function",
    [
        "core_user_get_users",  # a real Moodle function that B4 does not list
        "mod_assign_set_user_flags",  # the one the guide removed
        "totally_unknown",
        "",
    ],
)
def test_an_unlisted_function_is_refused_and_the_message_repeats_nothing(
    function: str, version: str
) -> None:
    assert function not in contract_names()
    with pytest.raises(FunctionNotAllowed) as caught:
        load_allowlist().resolve(function, version)
    # The message is the fixed text: it does not echo what the caller sent.
    assert str(caught.value) == messages.FUNCTION_NOT_ALLOWED
    if function:
        assert function not in str(caught.value)


@pytest.mark.parametrize("version", VERSIONS)
def test_every_listed_function_resolves_to_itself_on_both_versions(
    version: str,
) -> None:
    allowlist = load_allowlist()
    names = contract_names()
    assert names  # an empty list would make this test pass for the wrong reason
    for name in names:
        assert allowlist.resolve(name, version) == name


@pytest.mark.parametrize("version", VERSIONS)
@pytest.mark.parametrize(
    "variant",
    [
        lambda name: name.upper(),  # case
        lambda name: name.capitalize(),
        lambda name: f" {name}",  # spaces
        lambda name: f"{name} ",
        lambda name: name[:-1],  # a prefix of a listed name
        lambda name: f"{name}_x",  # a listed name with more after it
        lambda name: name.replace("_", "-"),
    ],
    ids=[
        "upper",
        "capitalised",
        "leading-space",
        "trailing-space",
        "prefix",
        "suffix",
        "hyphens",
    ],
)
def test_matching_is_exact(variant: Any, version: str) -> None:
    allowlist = load_allowlist()
    for name in contract_names():
        changed = variant(name)
        assert changed not in contract_names()
        with pytest.raises(FunctionNotAllowed):
            allowlist.resolve(changed, version)


def test_a_replacement_name_is_returned_only_for_its_own_version(
    tmp_path: Path,
) -> None:
    # The contract example lists no replacement today, so the case is built in a temporary list.
    listed = write_list(
        tmp_path / "list.json",
        [
            {
                "name": "mod_example_old",
                "parameters": [],
                "replacements": [{"moodle_version": "5.3", "name": "mod_example_new"}],
            },
            {"name": "mod_example_plain", "parameters": []},
        ],
    )
    allowlist = load_allowlist(listed)
    assert allowlist.resolve("mod_example_old", "5.3") == "mod_example_new"
    assert allowlist.resolve("mod_example_old", "4.5") == "mod_example_old"
    assert allowlist.resolve("mod_example_plain", "5.3") == "mod_example_plain"
    # The replacement is a name to send, not a second listed function.
    with pytest.raises(FunctionNotAllowed):
        allowlist.resolve("mod_example_new", "5.3")
