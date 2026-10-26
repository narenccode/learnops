"""B5 model and speech interface contract (PRD B5.1-B5.4): the JSON Schema and its examples.

AUTOMATED here (structure only, by contracts/model-interface.v1.schema.json):
  * the schema is a valid Draft 2020-12 schema;
  * every example validates, both against the whole schema and against its own definition;
  * the fields PRD B5.1 names for result.meta and B5.4 names for transcript.segments,
    words and transcript.meta are required, with their types, minimums and the provider enum;
  * unknown fields are accepted (PRD B.0, EXT-02);
  * a document that is neither a meta record nor a transcript is rejected.

NOT automated here, and therefore NOT claimed as enforced (the schema's $comment lists them):
  * result.data matches the task's output_schema (B5.1);
  * one retry on invalid output, then a clear error (B5.2);
  * provider and model chosen by environment variables, keys only from the environment (B5.2);
  * versioned prompt files and logging meta to shared.model_calls without learner content (B5.3);
  * end >= start, and segments in time order (B5.4).
These belong to libs/model_interface, which does not exist yet.

Each invalid case below must fail at the expected place with the expected schema keyword, so a
case cannot pass for the wrong reason.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "contracts" / "model-interface.v1.schema.json"
EXAMPLES = ROOT / "contracts" / "examples" / "model-interface.v1"
SCHEMA_ID = "urn:learnops:contract:model-interface:v1"

# Each example file and the definition it is an instance of.
EXAMPLE_DEFS = {
    "model-result-meta.local.json": "model_result_meta",
    "model-result-meta.hosted.json": "model_result_meta",
    "transcript.json": "transcript",
}

Doc = dict[str, Any]
Loc = tuple[str | int, ...]
Edit = Callable[[Doc], None]

# Places in the transcript example.
SEGMENT: Loc = ("segments", 0)
WORD: Loc = ("segments", 0, "words", 0)
TMETA: Loc = ("meta",)


# --- helpers -------------------------------------------------------------------------------


def _parent(doc: Doc, loc: Loc) -> Any:
    node: Any = doc
    for key in loc[:-1]:
        node = node[key]
    return node


def set_at(loc: Loc, value: Any) -> Edit:
    def edit(doc: Doc) -> None:
        _parent(doc, loc)[loc[-1]] = value

    return edit


def drop_at(loc: Loc) -> Edit:
    def edit(doc: Doc) -> None:
        del _parent(doc, loc)[loc[-1]]

    return edit


def error_keys(validator: Draft202012Validator, instance: Any) -> set[tuple[Loc, str]]:
    """(where, which schema keyword) for every error, so a test can name the exact failure."""
    return {
        (tuple(e.absolute_path), str(e.validator))
        for e in validator.iter_errors(instance)
    }


def messages(validator: Draft202012Validator, instance: Any) -> list[str]:
    return [e.message for e in validator.iter_errors(instance)]


def load_example(name: str) -> Doc:
    loaded: Doc = json.loads((EXAMPLES / name).read_text(encoding="utf-8"))
    return loaded


@dataclass(frozen=True)
class Case:
    name: str
    edit: Edit
    at: Loc
    keyword: str


def bad(name: str, loc: Loc, value: Any, keyword: str) -> Case:
    """Replace the value at loc; the schema must reject it at loc with keyword."""
    return Case(name, set_at(loc, value), loc, keyword)


def missing(name: str, loc: Loc) -> Case:
    """Remove the field at loc; the schema must report it as required on its parent."""
    return Case(name, drop_at(loc), loc[:-1], "required")


def params(cases: list[Case]) -> list[Any]:
    return [pytest.param(c, id=c.name) for c in cases]


# --- fixtures ------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def schema() -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return loaded


@pytest.fixture(scope="module")
def validator(schema: dict[str, Any]) -> Draft202012Validator:
    return Draft202012Validator(schema)


@pytest.fixture(scope="module")
def registry(schema: dict[str, Any]) -> Registry[Any]:
    resource: Resource[Any] = Resource.from_contents(schema)
    loaded: Registry[Any] = Registry().with_resource(SCHEMA_ID, resource)
    return loaded


def def_validator(registry: Registry[Any], name: str) -> Draft202012Validator:
    """Validates against one definition, so errors point at that definition's fields."""
    return Draft202012Validator(
        {"$ref": f"{SCHEMA_ID}#/$defs/{name}"}, registry=registry
    )


@pytest.fixture(scope="module")
def meta_validator(registry: Registry[Any]) -> Draft202012Validator:
    return def_validator(registry, "model_result_meta")


@pytest.fixture(scope="module")
def transcript_validator(registry: Registry[Any]) -> Draft202012Validator:
    return def_validator(registry, "transcript")


@pytest.fixture
def meta() -> Doc:
    return copy.deepcopy(load_example("model-result-meta.local.json"))


@pytest.fixture
def transcript() -> Doc:
    return copy.deepcopy(load_example("transcript.json"))


# --- the schema and the examples -----------------------------------------------------------


def test_schema_is_a_valid_draft_2020_12_schema(schema: dict[str, Any]) -> None:
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == SCHEMA_ID
    Draft202012Validator.check_schema(schema)


def test_every_example_file_is_listed() -> None:
    assert sorted(p.name for p in EXAMPLES.glob("*.json")) == sorted(EXAMPLE_DEFS)


@pytest.mark.parametrize("name", sorted(EXAMPLE_DEFS))
def test_example_is_valid_against_the_whole_schema(
    validator: Draft202012Validator, name: str
) -> None:
    assert messages(validator, load_example(name)) == []


@pytest.mark.parametrize("name", sorted(EXAMPLE_DEFS))
def test_example_is_valid_against_its_definition(
    registry: Registry[Any], name: str
) -> None:
    check = def_validator(registry, EXAMPLE_DEFS[name])
    assert messages(check, load_example(name)) == []


def test_examples_cover_both_providers() -> None:
    providers = {
        load_example(name)["provider"]
        for name, kind in EXAMPLE_DEFS.items()
        if kind == "model_result_meta"
    }
    assert providers == {"local", "hosted"}


# --- invalid: required fields --------------------------------------------------------------

META_FIELDS = (
    "provider",
    "model",
    "input_tokens",
    "output_tokens",
    "latency_ms",
    "cost_estimate",
    "prompt_version",
)
META_MISSING = [missing(f"meta without {f}", (f,)) for f in META_FIELDS]


@pytest.mark.parametrize("case", params(META_MISSING))
def test_meta_missing_required_field_is_rejected(
    meta_validator: Draft202012Validator, meta: Doc, case: Case
) -> None:
    case.edit(meta)
    assert (case.at, case.keyword) in error_keys(meta_validator, meta)


TRANSCRIPT_MISSING = [
    missing("transcript without segments", ("segments",)),
    missing("transcript without meta", TMETA),
    missing("segment without start", SEGMENT + ("start",)),
    missing("segment without end", SEGMENT + ("end",)),
    missing("segment without text", SEGMENT + ("text",)),
    missing("segment without words", SEGMENT + ("words",)),
    missing("word without start", WORD + ("start",)),
    missing("word without end", WORD + ("end",)),
    missing("word without word", WORD + ("word",)),
    *[
        missing(f"transcript meta without {f}", TMETA + (f,))
        for f in ("provider", "model", "duration_s", "latency_ms", "cost_estimate")
    ],
]


@pytest.mark.parametrize("case", params(TRANSCRIPT_MISSING))
def test_transcript_missing_required_field_is_rejected(
    transcript_validator: Draft202012Validator, transcript: Doc, case: Case
) -> None:
    case.edit(transcript)
    assert (case.at, case.keyword) in error_keys(transcript_validator, transcript)


# --- invalid: wrong types, values and enums ------------------------------------------------

META_BAD = [
    bad("provider is unknown", ("provider",), "other", "enum"),
    bad("provider has wrong case", ("provider",), "Local", "enum"),
    bad("provider is a number", ("provider",), 1, "enum"),
    bad("provider fake is not in v1", ("provider",), "fake", "enum"),
    bad("model is empty", ("model",), "", "minLength"),
    bad("model is a number", ("model",), 7, "type"),
    bad("input_tokens is a string", ("input_tokens",), "812", "type"),
    bad("input_tokens is fractional", ("input_tokens",), 8.5, "type"),
    bad("input_tokens is negative", ("input_tokens",), -1, "minimum"),
    bad("input_tokens is boolean", ("input_tokens",), True, "type"),
    bad("input_tokens is null", ("input_tokens",), None, "type"),
    bad("output_tokens is negative", ("output_tokens",), -1, "minimum"),
    bad("output_tokens is a string", ("output_tokens",), "164", "type"),
    bad("latency_ms is fractional", ("latency_ms",), 12.5, "type"),
    bad("latency_ms is negative", ("latency_ms",), -3, "minimum"),
    bad("cost_estimate is negative", ("cost_estimate",), -0.01, "minimum"),
    bad("cost_estimate is a string", ("cost_estimate",), "free", "type"),
    bad("cost_estimate is null", ("cost_estimate",), None, "type"),
    bad("prompt_version is empty", ("prompt_version",), "", "minLength"),
    bad("prompt_version is a number", ("prompt_version",), 1, "type"),
]


@pytest.mark.parametrize("case", params(META_BAD))
def test_meta_wrong_type_or_value_is_rejected(
    meta_validator: Draft202012Validator, meta: Doc, case: Case
) -> None:
    case.edit(meta)
    assert (case.at, case.keyword) in error_keys(meta_validator, meta)


TRANSCRIPT_BAD = [
    bad("segments is an object", ("segments",), {}, "type"),
    bad("segment is a string", SEGMENT, "hello", "type"),
    bad("segment start is a string", SEGMENT + ("start",), "0.0", "type"),
    bad("segment start is negative", SEGMENT + ("start",), -0.5, "minimum"),
    bad("segment end is null", SEGMENT + ("end",), None, "type"),
    bad("segment text is a number", SEGMENT + ("text",), 5, "type"),
    bad("words is a string", SEGMENT + ("words",), "Welcome", "type"),
    bad("word start is negative", WORD + ("start",), -1, "minimum"),
    bad("word end is a string", WORD + ("end",), "0.6", "type"),
    bad("word is empty", WORD + ("word",), "", "minLength"),
    bad("word is a number", WORD + ("word",), 1, "type"),
    bad("meta is a list", TMETA, [], "type"),
    bad("meta provider is unknown", TMETA + ("provider",), "cloud", "enum"),
    bad("meta model is empty", TMETA + ("model",), "", "minLength"),
    bad("duration_s is negative", TMETA + ("duration_s",), -6.0, "minimum"),
    bad("duration_s is a string", TMETA + ("duration_s",), "6", "type"),
    bad("meta latency_ms is fractional", TMETA + ("latency_ms",), 1.5, "type"),
    bad("meta cost_estimate is negative", TMETA + ("cost_estimate",), -1, "minimum"),
]


@pytest.mark.parametrize("case", params(TRANSCRIPT_BAD))
def test_transcript_wrong_type_or_value_is_rejected(
    transcript_validator: Draft202012Validator, transcript: Doc, case: Case
) -> None:
    case.edit(transcript)
    assert (case.at, case.keyword) in error_keys(transcript_validator, transcript)


@pytest.mark.parametrize(
    "value",
    [[], "grade_draft/v1", None, 1, {}, {"provider": "local"}],
    ids=repr,
)
def test_document_that_is_neither_kind_is_rejected(
    validator: Draft202012Validator, value: Any
) -> None:
    assert ((), "oneOf") in error_keys(validator, value)


# --- valid variations: the schema must NOT reject these ------------------------------------


@dataclass(frozen=True)
class Accepted:
    name: str
    edit: Edit


META_ACCEPTED = [
    Accepted("unknown field in meta", set_at(("future",), {"a": 1})),
    Accepted("zero tokens", set_at(("output_tokens",), 0)),
    Accepted("whole-number cost", set_at(("cost_estimate",), 1)),
    Accepted("hosted provider", set_at(("provider",), "hosted")),
]


@pytest.mark.parametrize("case", [pytest.param(a, id=a.name) for a in META_ACCEPTED])
def test_meta_valid_variation_is_accepted(
    validator: Draft202012Validator,
    meta_validator: Draft202012Validator,
    meta: Doc,
    case: Accepted,
) -> None:
    case.edit(meta)
    assert messages(meta_validator, meta) == []
    assert messages(validator, meta) == []


TRANSCRIPT_ACCEPTED = [
    Accepted("unknown field at root", set_at(("future",), 1)),
    Accepted("unknown field in segment", set_at(SEGMENT + ("future",), "x")),
    Accepted("unknown field in word", set_at(WORD + ("future",), [1])),
    Accepted("unknown field in meta", set_at(TMETA + ("future",), True)),
    Accepted("no segments (silent audio)", set_at(("segments",), [])),
    Accepted("segment with no words", set_at(SEGMENT + ("words",), [])),
    Accepted("empty segment text", set_at(SEGMENT + ("text",), "")),
    Accepted("integer seconds", set_at(SEGMENT + ("start",), 0)),
    Accepted("hosted provider", set_at(TMETA + ("provider",), "hosted")),
    Accepted("non-ASCII word", set_at(WORD + ("word",), "namaste—é")),
]


@pytest.mark.parametrize(
    "case", [pytest.param(a, id=a.name) for a in TRANSCRIPT_ACCEPTED]
)
def test_transcript_valid_variation_is_accepted(
    validator: Draft202012Validator,
    transcript_validator: Draft202012Validator,
    transcript: Doc,
    case: Accepted,
) -> None:
    case.edit(transcript)
    assert messages(transcript_validator, transcript) == []
    assert messages(validator, transcript) == []
