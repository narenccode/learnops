"""B8.6 model comparison set (PRD B8, FR-M-03): the PROVISIONAL format, rubric and first input.

The set lives in testdata/b8-6-model-comparison/. Its format and rubric are a Release 0 proposal
by Student 3, not agreed (see that folder's README, "Open decisions").

AUTOMATED here:
  * the manifest, rubric and expected-chapters schemas are valid Draft 2020-12 schemas, and the
    manifest, the rubric and every expected chapters file validate;
  * ids are unique; every item's input exists; every input, source note and expected file exists;
    pending and placeholder items carry no input or expected output;
  * a provisional set marks every input and item provisional and keeps the rubric unfrozen; a
    final set needs a frozen rubric, every ready item reviewed, and no pending or placeholder item;
  * an expected summary is non-empty and its file carries the PROVISIONAL / NOT REVIEWED label
    while it is not reviewed;
  * the transcript has the PRD B5.4 shape; times are seconds >= 0, every segment and word ends at
    or after its start, words lie inside their segment, segments are in time order and lie within
    duration_s (the last two are this set's authoring rules, not B5 guarantees);
  * the transcript validates against contracts/model-interface.v1.schema.json when that file
    exists (B5, PR #25); otherwise that one test is SKIPPED with the reason;
  * expected chapters are ordered, do not overlap, have end > start, lie within the transcript and
    start on a segment boundary (authoring rules);
  * the rubric lists the four FR-M-03 measures, covers every non-grading task in the manifest and
    has at least one review level that counts as wrong;
  * results/ holds no results; synthetic-data guards: reserved .invalid hosts only, no email
    address, text files of at most 64 KiB.

NOT automated, and therefore NOT claimed:
  * that any expected output is correct or reviewed (none is reviewed; open decision O2);
  * the rubric's content (every definition is proposed or open, Q48), set size, or Q12 inputs;
  * grading-draft and practice items (pending and placeholder); any model run or result.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
SET_DIR = ROOT / "testdata" / "b8-6-model-comparison"
SCHEMA_DIR = SET_DIR / "schemas"
B5_SCHEMA = ROOT / "contracts" / "model-interface.v1.schema.json"

SCHEMA_NAMES = ("manifest", "rubric", "chapters")
FR_M_03_MEASURES = {
    "wrong_answer_rate",
    "agreement",
    "mentor_review_time",
    "cost_per_task",
}
NOT_REVIEWED_LABEL = "PROVISIONAL, NOT REVIEWED"
MAX_FILE_BYTES = 64 * 1024

Doc = dict[str, Any]


# --- helpers -------------------------------------------------------------------------------


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_schema(name: str) -> Doc:
    loaded: Doc = load_json(SCHEMA_DIR / f"{name}.schema.json")
    return loaded


def errors(validator: Draft202012Validator, instance: Any) -> list[str]:
    return [
        f"{list(e.absolute_path)}: {e.message}" for e in validator.iter_errors(instance)
    ]


def is_seconds(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool) and value >= 0


def b5_shape_problems(transcript: Any) -> list[str]:
    """The PRD B5.4 shape, checked here because the B5 schema is not on main yet."""
    problems: list[str] = []
    if not isinstance(transcript, dict) or set(transcript) < {"segments", "meta"}:
        return ["transcript needs 'segments' and 'meta'"]
    meta = transcript["meta"]
    for field in ("provider", "model", "duration_s", "latency_ms", "cost_estimate"):
        if field not in meta:
            problems.append(f"meta.{field} missing")
    for i, seg in enumerate(transcript["segments"]):
        for field in ("start", "end", "text", "words"):
            if field not in seg:
                problems.append(f"segments[{i}].{field} missing")
        if not (is_seconds(seg.get("start")) and is_seconds(seg.get("end"))):
            problems.append(f"segments[{i}] start/end are not seconds >= 0")
        if not isinstance(seg.get("text"), str):
            problems.append(f"segments[{i}].text is not a string")
        for j, word in enumerate(seg.get("words", [])):
            if set(word) < {"start", "end", "word"} or not word["word"]:
                problems.append(
                    f"segments[{i}].words[{j}] needs start, end and a non-empty word"
                )
            elif not (is_seconds(word["start"]) and is_seconds(word["end"])):
                problems.append(
                    f"segments[{i}].words[{j}] start/end are not seconds >= 0"
                )
    return problems


def transcript_time_problems(transcript: Doc) -> list[str]:
    problems: list[str] = []
    duration = transcript["meta"]["duration_s"]
    previous_end = 0.0
    for i, seg in enumerate(transcript["segments"]):
        if seg["end"] < seg["start"]:
            problems.append(f"segments[{i}] ends before it starts")
        if seg["start"] < previous_end:
            problems.append(f"segments[{i}] starts before the previous segment ends")
        if seg["end"] > duration:
            problems.append(f"segments[{i}] ends after duration_s")
        for j, word in enumerate(seg["words"]):
            if word["end"] < word["start"]:
                problems.append(f"segments[{i}].words[{j}] ends before it starts")
            if word["start"] < seg["start"] or word["end"] > seg["end"]:
                problems.append(f"segments[{i}].words[{j}] lies outside its segment")
        previous_end = seg["end"]
    return problems


def chapter_problems(chapters: list[Doc], transcript: Doc) -> list[str]:
    problems: list[str] = []
    duration = transcript["meta"]["duration_s"]
    boundaries = {seg["start"] for seg in transcript["segments"]}
    previous_end = 0.0
    for i, chapter in enumerate(chapters):
        if chapter["end"] <= chapter["start"]:
            problems.append(f"chapter {i} does not end after it starts")
        if chapter["start"] < previous_end:
            problems.append(
                f"chapter {i} overlaps the previous chapter or is out of order"
            )
        if chapter["end"] > duration:
            problems.append(f"chapter {i} ends after the transcript")
        if chapter["start"] not in boundaries:
            problems.append(f"chapter {i} does not start on a segment boundary")
        previous_end = chapter["end"]
    return problems


# --- fixtures ------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def validators() -> dict[str, Draft202012Validator]:
    return {name: Draft202012Validator(load_schema(name)) for name in SCHEMA_NAMES}


@pytest.fixture(scope="module")
def manifest() -> Doc:
    loaded: Doc = load_yaml(SET_DIR / "manifest.yaml")
    return loaded


@pytest.fixture(scope="module")
def rubric() -> Doc:
    loaded: Doc = load_yaml(SET_DIR / "rubric.yaml")
    return loaded


@pytest.fixture(scope="module")
def inputs(manifest: Doc) -> dict[str, Doc]:
    return {i["id"]: i for i in manifest["inputs"]}


def ready_items(kind: str) -> list[Doc]:
    items: list[Doc] = load_yaml(SET_DIR / "manifest.yaml")["items"]
    return [i for i in items if i["task"] == kind and i["status"] == "ready"]


def transcript_inputs() -> list[str]:
    inputs: list[Doc] = load_yaml(SET_DIR / "manifest.yaml")["inputs"]
    return [i["path"] for i in inputs if i["kind"] == "transcript"]


# --- schemas and documents -----------------------------------------------------------------


@pytest.mark.parametrize("name", SCHEMA_NAMES)
def test_schema_is_a_valid_draft_2020_12_schema(name: str) -> None:
    Draft202012Validator.check_schema(load_schema(name))


def test_manifest_and_rubric_are_valid(
    validators: dict[str, Draft202012Validator], manifest: Doc, rubric: Doc
) -> None:
    assert errors(validators["manifest"], manifest) == []
    assert errors(validators["rubric"], rubric) == []


def test_ids_are_unique_and_references_resolve(
    manifest: Doc, inputs: dict[str, Doc]
) -> None:
    item_ids = [i["id"] for i in manifest["items"]]
    assert len(item_ids) == len(set(item_ids))
    assert len(inputs) == len(manifest["inputs"])
    for item in manifest["items"]:
        if "input" in item:
            assert item["input"] in inputs, item["id"]
        if "expected" in item:
            assert (SET_DIR / item["expected"]).is_file(), item["id"]
            assert Path(item["expected"]).parts[:2] == ("expected", item["id"]), item[
                "id"
            ]
    for source in inputs.values():
        assert (SET_DIR / source["path"]).is_file(), source["id"]
        assert (SET_DIR / source["source_note"]).is_file(), source["id"]


def test_pending_and_placeholder_items_have_no_content(
    validators: dict[str, Draft202012Validator],
) -> None:
    # The schema must refuse a placeholder that carries an expected output.
    item = {
        "id": "pr-001",
        "task": "practice",
        "status": "placeholder",
        "provisional": True,
        "depends_on": ["Q12"],
        "expected": "expected/pr-001/questions.json",
    }
    doc = load_yaml(SET_DIR / "manifest.yaml")
    doc["items"] = [item]
    assert errors(validators["manifest"], doc) != []


# --- provisional labelling and review status -----------------------------------------------


def test_status_rules(manifest: Doc, rubric: Doc) -> None:
    items = manifest["items"]
    if manifest["status"] == "provisional":
        assert all(i["provisional"] for i in manifest["inputs"])
        assert all(i["provisional"] for i in items)
        assert rubric["frozen"] is False
    else:
        assert rubric["frozen"] is True and rubric["status"] == "final"
        assert all(i["status"] == "ready" for i in items)
        assert all(i["expected_review"]["status"] == "reviewed" for i in items)


def test_reviewed_needs_a_reviewer(validators: dict[str, Draft202012Validator]) -> None:
    doc = load_yaml(SET_DIR / "manifest.yaml")
    doc["items"][0]["expected_review"] = {"status": "reviewed"}
    assert errors(validators["manifest"], doc) != []


@pytest.mark.parametrize("item", ready_items("summary"), ids=lambda i: str(i["id"]))
def test_expected_summary_is_labelled_until_reviewed(item: Doc) -> None:
    text = (SET_DIR / item["expected"]).read_text(encoding="utf-8")
    body = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL).strip()
    assert body, "summary body is empty"
    if item["expected_review"]["status"] == "not_reviewed":
        assert NOT_REVIEWED_LABEL in text.splitlines()[0]


# --- transcript and chapters ---------------------------------------------------------------


@pytest.mark.parametrize("path", transcript_inputs())
def test_transcript_has_the_prd_b5_4_shape_and_consistent_times(path: str) -> None:
    transcript = load_json(SET_DIR / path)
    assert b5_shape_problems(transcript) == []
    assert transcript_time_problems(transcript) == []


@pytest.mark.parametrize("path", transcript_inputs())
def test_transcript_validates_against_the_b5_contract(path: str) -> None:
    if not B5_SCHEMA.is_file():
        pytest.skip(
            "contracts/model-interface.v1.schema.json is not on this branch (B5, PR #25)"
        )
    validator = Draft202012Validator(load_json(B5_SCHEMA))
    assert errors(validator, load_json(SET_DIR / path)) == []


def test_time_checks_catch_bad_transcripts() -> None:
    transcript = load_json(SET_DIR / transcript_inputs()[0])
    transcript["segments"][1]["end"] = transcript["segments"][1]["start"] - 1
    assert transcript_time_problems(transcript) != []
    del transcript["segments"][0]["words"]
    assert b5_shape_problems(transcript) != []


@pytest.mark.parametrize("item", ready_items("chapters"), ids=lambda i: str(i["id"]))
def test_expected_chapters_are_valid_and_fit_the_transcript(
    item: Doc, validators: dict[str, Draft202012Validator], inputs: dict[str, Doc]
) -> None:
    chapters = load_json(SET_DIR / item["expected"])
    assert errors(validators["chapters"], chapters) == []
    transcript = load_json(SET_DIR / inputs[item["input"]]["path"])
    assert chapter_problems(chapters, transcript) == []


def test_chapter_checks_catch_overlap(inputs: dict[str, Doc]) -> None:
    transcript = load_json(SET_DIR / inputs["t001"]["path"])
    chapters = [
        {"start": 0.0, "end": 60.0, "title": "a"},
        {"start": 52.0, "end": 70.0, "title": "b"},
    ]
    assert any("overlaps" in p for p in chapter_problems(chapters, transcript))


# --- rubric and results --------------------------------------------------------------------


def test_rubric_covers_the_measures_and_tasks(rubric: Doc, manifest: Doc) -> None:
    assert {m["id"] for m in rubric["measures"]} >= FR_M_03_MEASURES
    output_tasks = {i["task"] for i in manifest["items"]} - {"grade_draft"}
    assert output_tasks <= set(rubric["output_review"]["applies_to"])
    assert any(level["counts_as_wrong"] for level in rubric["output_review"]["levels"])


def test_no_results_are_claimed() -> None:
    files = [p.name for p in (SET_DIR / "results").rglob("*") if p.is_file()]
    assert files == ["README.md"]


# --- synthetic-data guards -----------------------------------------------------------------

URL = re.compile(r"\bhttps?://([^/\s\"'`)>\]]+)")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9.-]+")


def test_files_are_small_text_with_no_real_hosts_or_email_addresses() -> None:
    for path in sorted(p for p in SET_DIR.rglob("*") if p.is_file()):
        assert path.stat().st_size <= MAX_FILE_BYTES, path
        text = path.read_text(encoding="utf-8")
        if (
            path.parent != SCHEMA_DIR
        ):  # "$schema" URLs name the JSON Schema dialect, not data
            for host in URL.findall(text):
                assert host.endswith(".invalid"), (path, host)
        assert EMAIL.findall(text) == [], path
