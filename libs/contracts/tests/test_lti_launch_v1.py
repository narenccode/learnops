"""B3 LTI launch contract (PRD B3): the JSON Schema for the normalised launch result.

AUTOMATED here (structure only, by contracts/lti-launch.v1.schema.json):
  * the schema is a valid Draft 2020-12 schema;
  * every file in contracts/examples/lti-launch.v1/ validates, and the folder holds valid
    examples only (invalid cases live in this file, never in that folder);
  * the required fields, the message type, the two role values, non-empty strings, nullable
    optionals, and that unknown fields are accepted (PRD B.0, EXT-02).

NOT checked by the schema, so not tested here (the schema's $comment lists them): signature,
exp, aud, azp, iss, deployment, nonce and state checks, role-URI mapping and precedence,
session binding and expiry, course isolation. They belong to libs/lti, which does not exist yet.

Each invalid case must fail at the expected place with the expected schema keyword, so a case
cannot pass for the wrong reason.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "contracts" / "lti-launch.v1.schema.json"
EXAMPLE_DIR = ROOT / "contracts" / "examples" / "lti-launch.v1"

Doc = dict[str, Any]


def _schema() -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return loaded


def _validator() -> Draft202012Validator:
    return Draft202012Validator(_schema(), format_checker=FormatChecker())


def _example_files() -> list[Path]:
    return sorted(EXAMPLE_DIR.glob("*.json"))


@pytest.fixture
def mentor_doc() -> Doc:
    """A fresh copy of the Mentor example, safe to edit."""
    loaded: Doc = json.loads(
        (EXAMPLE_DIR / "instructor-mentor.json").read_text("utf-8")
    )
    return copy.deepcopy(loaded)


def test_schema_is_valid_draft_2020_12() -> None:
    schema = _schema()
    Draft202012Validator.check_schema(schema)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == "urn:learnops:contract:lti-launch:v1"


def test_examples_folder_has_the_required_examples() -> None:
    names = {p.name for p in _example_files()}
    assert {"instructor-mentor.json", "institution-administrator.json"} <= names


def test_examples_folder_holds_json_files_only() -> None:
    """CI validates every file there as valid, so nothing else may be in it."""
    assert [p for p in EXAMPLE_DIR.iterdir() if p.suffix != ".json"] == []


@pytest.mark.parametrize("path", _example_files(), ids=lambda p: p.name)
def test_every_example_is_valid(path: Path) -> None:
    errors = list(_validator().iter_errors(json.loads(path.read_text("utf-8"))))
    assert errors == [], [e.message for e in errors]


def test_unknown_fields_are_accepted(mentor_doc: Doc) -> None:
    mentor_doc["future_optional_field"] = "ignored by readers"
    mentor_doc["context"]["future_nested_field"] = 1
    assert _validator().is_valid(mentor_doc)


def test_optional_fields_may_be_absent_or_null(mentor_doc: Doc) -> None:
    for key in ("name", "email"):
        mentor_doc[key] = None
    del mentor_doc["context"]["title"]
    assert _validator().is_valid(mentor_doc)
    del mentor_doc["name"]
    del mentor_doc["email"]
    assert _validator().is_valid(mentor_doc)


@pytest.mark.parametrize("role", ["mentor", "administrator"])
def test_both_baseline_roles_are_accepted(mentor_doc: Doc, role: str) -> None:
    mentor_doc["role"] = role
    assert _validator().is_valid(mentor_doc)


def _set(path: tuple[str, ...], value: object) -> Callable[[Doc], None]:
    def apply(doc: Doc) -> None:
        target = doc
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value

    return apply


def _drop(path: tuple[str, ...]) -> Callable[[Doc], None]:
    def apply(doc: Doc) -> None:
        target = doc
        for key in path[:-1]:
            target = target[key]
        del target[path[-1]]

    return apply


# (case id, edit, JSON-pointer-like place of the error, schema keyword that must fail)
INVALID_CASES: list[tuple[str, Callable[[Doc], None], tuple[str, ...], str]] = [
    # role: learner is not a v1 value (Learner-only launches are refused before a baseline
    # session exists, PRD B3 and EXT-07; admitting it is open item OI-25 in ADR 0001)
    ("role-learner", _set(("role",), "learner"), ("role",), "enum"),
    ("role-unsupported", _set(("role",), "teacher"), ("role",), "enum"),
    ("role-wrong-case", _set(("role",), "Mentor"), ("role",), "enum"),
    ("role-not-a-string", _set(("role",), ["mentor"]), ("role",), "enum"),
    # required fields
    ("missing-iss", _drop(("iss",)), (), "required"),
    ("missing-sub", _drop(("sub",)), (), "required"),
    ("missing-deployment-id", _drop(("deployment_id",)), (), "required"),
    ("missing-message-type", _drop(("message_type",)), (), "required"),
    ("missing-role", _drop(("role",)), (), "required"),
    ("missing-context", _drop(("context",)), (), "required"),
    ("missing-context-id", _drop(("context", "id")), ("context",), "required"),
    ("missing-resource-link", _drop(("resource_link",)), (), "required"),
    (
        "missing-resource-link-id",
        _drop(("resource_link", "id")),
        ("resource_link",),
        "required",
    ),
    # message type: only LtiResourceLinkRequest in v1
    (
        "wrong-message-type",
        _set(("message_type",), "LtiDeepLinkingRequest"),
        ("message_type",),
        "const",
    ),
    # empty required strings
    ("empty-iss", _set(("iss",), ""), ("iss",), "minLength"),
    ("empty-sub", _set(("sub",), ""), ("sub",), "minLength"),
    (
        "empty-deployment-id",
        _set(("deployment_id",), ""),
        ("deployment_id",),
        "minLength",
    ),
    ("empty-context-id", _set(("context", "id"), ""), ("context", "id"), "minLength"),
    (
        "empty-resource-link-id",
        _set(("resource_link", "id"), ""),
        ("resource_link", "id"),
        "minLength",
    ),
    # empty optional strings (null is the "absent" value, an empty string is not)
    ("empty-name", _set(("name",), ""), ("name",), "minLength"),
    ("empty-email", _set(("email",), ""), ("email",), "minLength"),
    (
        "empty-context-title",
        _set(("context", "title"), ""),
        ("context", "title"),
        "minLength",
    ),
    # types
    ("numeric-sub", _set(("sub",), 1001), ("sub",), "type"),
    ("numeric-context-id", _set(("context", "id"), 42), ("context", "id"), "type"),
    ("context-not-an-object", _set(("context",), "42"), ("context",), "type"),
    (
        "resource-link-not-an-object",
        _set(("resource_link",), "link-7"),
        ("resource_link",),
        "type",
    ),
]


@pytest.mark.parametrize(
    ("edit", "place", "keyword"),
    [pytest.param(e, p, k, id=i) for i, e, p, k in INVALID_CASES],
)
def test_invalid_launch_result_is_rejected_at_the_right_place(
    mentor_doc: Doc, edit: Callable[[Doc], None], place: tuple[str, ...], keyword: str
) -> None:
    edit(mentor_doc)
    errors = list(_validator().iter_errors(mentor_doc))
    assert errors, "the invalid document was accepted"
    assert [(tuple(map(str, e.absolute_path)), e.validator) for e in errors] == [
        (place, keyword)
    ]


def test_every_required_field_has_a_missing_case() -> None:
    """If the schema gains a required field, this fails until a negative case is added."""
    covered = {i for i, _, _, _ in INVALID_CASES}
    required_top = _schema()["required"]
    for field in required_top:
        assert "missing-" + field.replace("_", "-") in covered, field
