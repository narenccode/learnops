"""B5 model and speech interface contract (PRD B5.1-B5.4): the JSON Schema and its examples.

Structure only: docs/traceability.md lists what each test covers and what is not automated. Each
invalid case must fail at the expected place with the expected schema keyword, so a case cannot
pass for the wrong reason.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "contracts" / "model-interface.v1.schema.json"
EXAMPLES = ROOT / "contracts" / "examples"
# Flat layout, one file per case: contracts/examples/model-interface.v1.<case>.json (Student 2's
# validator convention). Invalid documents live in this file, never in the examples folder.
EXAMPLE_GLOB = "model-interface.v1.*.json"
SCHEMA_ID = "urn:learnops:contract:model-interface:v1"

# Each example file and the definition it is an instance of.
EXAMPLE_DEFS = {
    "model-interface.v1.meta-local.json": "model_result_meta",
    "model-interface.v1.meta-hosted.json": "model_result_meta",
    "model-interface.v1.meta-fake.json": "model_result_meta",
    "model-interface.v1.meta-unknown-usage.json": "model_result_meta",
    "model-interface.v1.transcript.json": "transcript",
    "model-interface.v1.transcript-unknown-cost.json": "transcript",
    "model-interface.v1.transcript-empty.json": "transcript",
    "model-interface.v1.transcript-empty-words.json": "transcript",
    "model-interface.v1.transcript-empty-text.json": "transcript",
    "model-interface.v1.transcript-chunked.json": "transcript",
}
TRANSCRIPT_EXAMPLES = sorted(
    n for n, kind in EXAMPLE_DEFS.items() if kind == "transcript"
)
META_EXAMPLES = sorted(
    n for n, kind in EXAMPLE_DEFS.items() if kind == "model_result_meta"
)

Doc = dict[str, Any]
Loc = tuple[str | int, ...]
DROP = object()

# Each kind of document: its definition, and the example a test case starts from.
KINDS = {
    "meta": ("model_result_meta", "model-interface.v1.meta-local.json"),
    "transcript": ("transcript", "model-interface.v1.transcript.json"),
}

# Places in the transcript example.
SEGMENT: Loc = ("segments", 0)
WORD: Loc = ("segments", 0, "words", 0)
TMETA: Loc = ("meta",)


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
    loc: Loc
    value: Any  # DROP removes the field instead
    at: Loc
    keyword: str

    def apply(self, doc: Doc) -> Doc:
        parent: Any = doc
        for key in self.loc[:-1]:
            parent = parent[key]
        if self.value is DROP:
            del parent[self.loc[-1]]
        else:
            parent[self.loc[-1]] = self.value
        return doc


def bad(name: str, loc: Loc, value: Any, keyword: str) -> Case:
    """Replace the value at loc; the schema must reject it at loc with keyword."""
    return Case(name, loc, value, loc, keyword)


def missing(name: str, loc: Loc) -> Case:
    """Remove the field at loc; the schema must report it as required on its parent."""
    return Case(name, loc, DROP, loc[:-1], "required")


def ok(name: str, loc: Loc, value: Any) -> Case:
    """Replace the value at loc; the schema must still accept the document."""
    return Case(name, loc, value, loc, "")


def params(meta_cases: list[Case], transcript_cases: list[Case]) -> list[Any]:
    """Every case once, as (kind, case), with the kind in its test id."""
    groups = (("meta", meta_cases), ("transcript", transcript_cases))
    return [
        pytest.param(k, c, id=f"{k}: {c.name}") for k, cases in groups for c in cases
    ]


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


def test_schema_is_a_valid_draft_2020_12_schema(schema: dict[str, Any]) -> None:
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == SCHEMA_ID
    Draft202012Validator.check_schema(schema)


def test_every_example_file_is_listed() -> None:
    assert sorted(p.name for p in EXAMPLES.glob(EXAMPLE_GLOB)) == sorted(EXAMPLE_DEFS)


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


def test_examples_cover_every_provider() -> None:
    providers = {load_example(name)["provider"] for name in META_EXAMPLES}
    assert providers == {"local", "hosted", "fake"}


def test_examples_show_known_and_unknown_usage() -> None:
    """Unknown usage is written as null, so a reader never mistakes it for 0."""
    metas = [load_example(name) for name in META_EXAMPLES]
    for field in ("input_tokens", "output_tokens", "cost_estimate"):
        values = [m[field] for m in metas]
        assert None in values, field
        assert any(isinstance(v, int | float) and v > 0 for v in values), field


def test_transcript_examples_show_known_and_unknown_cost() -> None:
    costs = [
        load_example(name)["meta"]["cost_estimate"] for name in TRANSCRIPT_EXAMPLES
    ]
    assert None in costs
    assert any(isinstance(c, int | float) for c in costs)


def test_examples_follow_the_cost_rule() -> None:
    """Guide (decision 0001): local has no billed cost and reports 0.0; unknown cost is null.

    So a local example never has null cost, and the unknown-usage example is all null, never 0.
    """
    metas = {name: load_example(name) for name in META_EXAMPLES}
    transcript_metas = {n: load_example(n)["meta"] for n in TRANSCRIPT_EXAMPLES}
    for name, meta in {**metas, **transcript_metas}.items():
        if meta["provider"] == "local":
            assert meta["cost_estimate"] == 0.0, name
    unknown = metas["model-interface.v1.meta-unknown-usage.json"]
    fields = ("input_tokens", "output_tokens", "cost_estimate")
    assert [unknown[f] for f in fields] == [None] * 3


def test_transcript_examples_cover_the_empty_cases() -> None:
    """Silent audio, a segment without word timings, and a segment without text (B5.4)."""
    docs = [load_example(name) for name in TRANSCRIPT_EXAMPLES]
    segments = [s for d in docs for s in d["segments"]]
    assert any(d["segments"] == [] for d in docs)
    assert any(s["words"] == [] and s["text"] for s in segments)
    assert any(s["text"] == "" for s in segments)


def test_chunked_example_keeps_times_from_the_start_of_the_audio() -> None:
    """Seconds from the start of the original audio, also after a chunk boundary (B5.4)."""
    doc = load_example("model-interface.v1.transcript-chunked.json")
    times = [t for s in doc["segments"] for t in (s["start"], s["end"])]
    assert min(times) > 1700 and max(times) <= doc["meta"]["duration_s"]


META_FIELDS = (
    "provider model input_tokens output_tokens latency_ms cost_estimate prompt_version"
)
META_MISSING = [missing(f"meta without {f}", (f,)) for f in META_FIELDS.split()]


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


def assert_rejected(registry: Registry[Any], kind: str, case: Case) -> None:
    definition, example = KINDS[kind]
    doc = case.apply(load_example(example))
    assert (case.at, case.keyword) in error_keys(
        def_validator(registry, definition), doc
    )


@pytest.mark.parametrize(("kind", "case"), params(META_MISSING, TRANSCRIPT_MISSING))
def test_missing_required_field_is_rejected(
    registry: Registry[Any], kind: str, case: Case
) -> None:
    assert_rejected(registry, kind, case)


META_BAD = [
    bad("provider is unknown", ("provider",), "other", "enum"),
    bad("provider has wrong case", ("provider",), "Local", "enum"),
    bad("provider is a number", ("provider",), 1, "enum"),
    bad("provider is null", ("provider",), None, "enum"),
    bad("provider is empty", ("provider",), "", "enum"),
    bad("model is empty", ("model",), "", "minLength"),
    bad("model is a number", ("model",), 7, "type"),
    bad("model is null", ("model",), None, "type"),
    bad("input_tokens is a string", ("input_tokens",), "812", "type"),
    bad("input_tokens is fractional", ("input_tokens",), 8.5, "type"),
    bad("input_tokens is negative", ("input_tokens",), -1, "minimum"),
    bad("input_tokens is boolean", ("input_tokens",), True, "type"),
    bad("output_tokens is negative", ("output_tokens",), -1, "minimum"),
    bad("output_tokens is a string", ("output_tokens",), "164", "type"),
    bad("output_tokens is fractional", ("output_tokens",), 1.5, "type"),
    bad("output_tokens is boolean", ("output_tokens",), False, "type"),
    bad("latency_ms is fractional", ("latency_ms",), 12.5, "type"),
    bad("latency_ms is negative", ("latency_ms",), -3, "minimum"),
    bad("latency_ms is null", ("latency_ms",), None, "type"),
    bad("cost_estimate is negative", ("cost_estimate",), -0.01, "minimum"),
    bad("cost_estimate is a string", ("cost_estimate",), "free", "type"),
    bad("cost_estimate is boolean", ("cost_estimate",), False, "type"),
    bad("prompt_version is empty", ("prompt_version",), "", "minLength"),
    bad("prompt_version is a number", ("prompt_version",), 1, "type"),
    bad("prompt_version is null", ("prompt_version",), None, "type"),
]


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
    bad("word is a string", WORD, "hello", "type"),
    bad("word is a number", WORD + ("word",), 1, "type"),
    bad("meta is a list", TMETA, [], "type"),
    bad("meta provider is unknown", TMETA + ("provider",), "cloud", "enum"),
    bad("meta model is empty", TMETA + ("model",), "", "minLength"),
    bad("duration_s is negative", TMETA + ("duration_s",), -6.0, "minimum"),
    bad("duration_s is a string", TMETA + ("duration_s",), "6", "type"),
    bad("duration_s is null", TMETA + ("duration_s",), None, "type"),
    bad("meta latency_ms is fractional", TMETA + ("latency_ms",), 1.5, "type"),
    bad("meta cost_estimate is negative", TMETA + ("cost_estimate",), -1, "minimum"),
    bad("meta cost_estimate is a string", TMETA + ("cost_estimate",), "0", "type"),
    bad("meta provider is null", TMETA + ("provider",), None, "enum"),
]


@pytest.mark.parametrize(("kind", "case"), params(META_BAD, TRANSCRIPT_BAD))
def test_wrong_type_or_value_is_rejected(
    registry: Registry[Any], kind: str, case: Case
) -> None:
    assert_rejected(registry, kind, case)


@pytest.mark.parametrize(
    "value", [[], "grade_draft/v1", None, 1, {}, {"provider": "local"}], ids=repr
)
def test_document_that_is_neither_kind_is_rejected(
    validator: Draft202012Validator, value: Any
) -> None:
    assert ((), "oneOf") in error_keys(validator, value)


def test_document_that_is_both_kinds_is_rejected(
    validator: Draft202012Validator,
) -> None:
    """Without a discriminator field, oneOf is what keeps the two kinds apart."""
    meta, transcript = (load_example(example) for _, example in KINDS.values())
    assert ((), "oneOf") in error_keys(validator, {**meta, **transcript})


META_ACCEPTED = [
    ok("unknown field in meta", ("future",), {"a": 1}),
    ok("zero tokens", ("output_tokens",), 0),
    ok("whole-number cost", ("cost_estimate",), 1),
    ok("zero cost (known to be free)", ("cost_estimate",), 0),
    ok("unknown cost is null", ("cost_estimate",), None),
    ok("unknown input_tokens is null", ("input_tokens",), None),
    ok("unknown output_tokens is null", ("output_tokens",), None),
    ok("hosted provider", ("provider",), "hosted"),
    ok("fake provider (tests only)", ("provider",), "fake"),
    ok("free-form prompt_version", ("prompt_version",), "2026-10-28"),
    # Q38 proposals: not part of v1 (guide); ignored like any unknown field, never required.
    ok("input_hash (Q38)", ("input_hash",), "sha256:0f1e2d"),
    ok("temperature (Q38)", ("temperature",), 0.2),
    ok("seed (Q38)", ("seed",), 7),
    ok("cost_known (Q38)", ("cost_known",), False),
]


TRANSCRIPT_ACCEPTED = [
    ok("unknown field at root", ("future",), 1),
    ok("unknown field in segment", SEGMENT + ("future",), "x"),
    ok("unknown field in word", WORD + ("future",), [1]),
    ok("unknown field in meta", TMETA + ("future",), True),
    ok("no segments (silent audio)", ("segments",), []),
    ok("segment with no words", SEGMENT + ("words",), []),
    ok("empty segment text", SEGMENT + ("text",), ""),
    ok("integer seconds", SEGMENT + ("start",), 0),
    ok("segment end equals start", SEGMENT + ("end",), 0.0),
    ok("hosted provider", TMETA + ("provider",), "hosted"),
    ok("fake provider (tests only)", TMETA + ("provider",), "fake"),
    ok("unknown cost is null", TMETA + ("cost_estimate",), None),
    ok("non-ASCII word", WORD + ("word",), "namaste—é"),
    # Student 4 proposal: not part of v1 (guide); ignored like any unknown field.
    ok("language in meta (proposal)", TMETA + ("language",), "en"),
]


@pytest.mark.parametrize(("kind", "case"), params(META_ACCEPTED, TRANSCRIPT_ACCEPTED))
def test_valid_variation_is_accepted(
    validator: Draft202012Validator, registry: Registry[Any], kind: str, case: Case
) -> None:
    definition, example = KINDS[kind]
    doc = case.apply(load_example(example))
    assert messages(def_validator(registry, definition), doc) == []
    assert messages(validator, doc) == []


def test_segment_ending_before_it_starts_passes_the_schema(
    validator: Draft202012Validator,
) -> None:
    """JSON Schema cannot compare two fields, so B5.4's end >= start is NOT a schema rule; library
    code enforces it."""
    transcript = load_example(KINDS["transcript"][1])
    transcript["segments"][0]["start"], transcript["segments"][0]["end"] = 2.4, 0.0
    assert messages(validator, transcript) == []
