"""B8.3 planted-error dataset: structure and consistency (PRD B8.3, C2.3, C2.7).

These tests check the DATASET and its expected-findings file only. They do NOT prove that the
Course Checker detects anything: no checker exists yet. Detection (PRD C2.7) is measured in
Release 1, when the checker runs on these variants.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml
from jsonschema import Draft202012Validator

from contracts import DirectorySource, validate_package

from .helpers import ROOT

B82 = ROOT / "testdata" / "b8-2-sample-course"
B83 = ROOT / "testdata" / "b8-3-planted-errors"
EXPECTED = B83 / "expected-findings.yaml"

CK_RULES = {f"CK-{n:02d}" for n in range(1, 14)}
STATUSES = {"built", "planned", "pending-lab"}
KINDS = {"package", "model", "mbz"}
SEVERITIES = {"error", "warning", "info"}
REQUIRED = (
    "id",
    "rule",
    "input_kind",
    "status",
    "path",
    "element",
    "planted_change",
    "expected",
    "reason",
    "also_expected",
    "notes",
)

# SHA-256 of each B8.2 file as merged by PR #61 (line endings normalised to LF). B8.2 is the
# clean baseline and must never change to make B8.3 easier.
B82_SHA256 = {
    "README.md": "db2e31d54938594179d8b271ee20d3eaf824fb20b4931a50b417f5e173c3928b",
    "package/course.yaml": "53e6b13698d878f420cdf5d35c58bbf1ea22c5e9a1b82157b5392837fdee4c75",
    "package/weeks/01-guide.md": "2a88beca9dafdc07b6cdba3ae070a17ea4e0158149d9281880d333581ef4471b",
    "package/weeks/01-task.md": "412bbdabd6c52bb9e3c120856d57d312f4a7b4a67ee7c8520da2b17aff1101cb",
    "package/weeks/02-guide.md": "bf80abd824481b04bed8b8c3382e64c17afd8a59870cedc0af88752c08409758",
    "package/weeks/02-task.md": "455b399cde189e7734c2b491a969e354616f2036d9da9483f92dc4802b45e2d0",
    "package/weeks/03-guide.md": "93bd245203293558a5561e4a222f6692fe4060006be3ecfffc5143c748a77f80",
    "package/weeks/03-task.md": "22a0e22dd0b77e1e602ee30c987469d5d48c172887f085c3e2114aadc3ed1dfc",
    "package/weeks/04-guide.md": "7e2970c969d23a1d5868b559435031fe0df5d3c6e270600b89a8cd3d11e2e56c",
    "package/weeks/04-task.md": "83ab26cb42821850effea9a41d9a9c94f1407b8b9d03e3eb31c424e8a1bc9447",
}

# Folders in B8.3 that belong to PR #118 (B1-validator variants, not CK rules).
OTHER_FOLDERS = {"missing-body", "duplicate-id", "protected-id", "invalid-mode"}


def _lf_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def _variants() -> list[dict[str, Any]]:
    data = yaml.safe_load(EXPECTED.read_text(encoding="utf-8"))
    variants: list[dict[str, Any]] = data["variants"]
    return variants


def _built() -> list[dict[str, Any]]:
    """Built package variants (each has a folder of its own)."""
    return [
        v
        for v in _variants()
        if v["status"] == "built" and v["input_kind"] == "package"
    ]


def _models() -> list[dict[str, Any]]:
    return [v for v in _variants() if v["input_kind"] == "model"]


def _files(root: Path) -> dict[str, bytes]:
    return {
        p.relative_to(root).as_posix(): _lf_bytes(p)
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_expected_findings_file_exists_and_parses() -> None:
    assert EXPECTED.is_file()
    assert yaml.safe_load(EXPECTED.read_text(encoding="utf-8"))["version"] == 1


@pytest.mark.parametrize("v", _variants(), ids=lambda v: v["id"])
def test_entry_is_complete_and_valid(v: dict[str, Any]) -> None:
    for field in REQUIRED:
        assert field in v, f"{v['id']}: missing field {field}"
    assert v["rule"] in CK_RULES
    assert v["expected"]["rule"] == v["rule"]
    assert v["expected"]["severity"] in SEVERITIES
    assert v["expected"]["element"] == v["element"]
    assert v["input_kind"] in KINDS
    assert v["status"] in STATUSES
    assert isinstance(v["also_expected"], list)
    assert set(v["also_expected"]) <= CK_RULES
    assert v["rule"] not in v["also_expected"]
    assert v["reason"].strip() and v["planted_change"].strip()
    # the id starts with the rule it exercises, so a variant's purpose is clear from its name
    assert v["id"].startswith(v["rule"].lower())


def test_mapping_is_provisional_until_confirmation_is_recorded() -> None:
    data = yaml.safe_load(EXPECTED.read_text(encoding="utf-8"))
    assert data["mapping_status"] in {"provisional", "confirmed"}
    if data["mapping_status"] == "confirmed":
        confirmation = data["confirmation"] or {}
        assert (
            confirmation.get("by")
            and confirmation.get("reference")
            and confirmation.get("date")
        )
    else:
        assert data["confirmation"] is None


def test_ck_12_is_not_asserted_until_body_media_extraction_is_decided() -> None:
    (ck12,) = [v for v in _variants() if v["id"] == "ck-12-full-url-media"]
    assert ck12["assertable"] is False
    assert "item 19" in ck12["notes"]


def test_ids_are_unique() -> None:
    ids = [v["id"] for v in _variants()]
    assert len(ids) == len(set(ids))


def test_every_ck_rule_has_at_least_one_variant() -> None:
    assert {v["rule"] for v in _variants()} == CK_RULES


def test_status_matches_input_kind() -> None:
    for v in _variants():
        if v["input_kind"] == "mbz":
            assert (
                v["status"] == "pending-lab"
            ), f"{v['id']}: no .mbz can exist without a lab"
            assert v["path"] is None
        if v["status"] == "planned":
            assert v["input_kind"] == "package"
            assert not (B83 / v["id"]).exists(), "a planned variant has no folder yet"


def test_every_variant_folder_has_an_entry_and_back() -> None:
    folders = {p.name for p in B83.iterdir() if p.is_dir()} - OTHER_FOLDERS - {"models"}
    assert folders == {v["id"] for v in _built()}


@pytest.mark.parametrize("v", _built(), ids=lambda v: v["id"])
def test_built_variant_changes_exactly_the_declared_file(v: dict[str, Any]) -> None:
    package = B83 / v["id"] / "package"
    assert package.is_dir()
    base = _files(B82 / "package")
    got = _files(package)
    assert got.keys() == base.keys(), "a built variant has the same files as B8.2"
    changed = sorted(name for name in base if got[name] != base[name])
    assert changed == [
        v["path"]
    ], "exactly one file differs from B8.2, and it is the declared one"


@pytest.mark.parametrize("v", _built(), ids=lambda v: v["id"])
def test_built_variant_is_a_valid_b1_package(v: dict[str, Any]) -> None:
    # A planted CK error must not be a B1 error: under the checker design (section 3.4) a package
    # failing B1 stops before any CK rule runs, so it could not exercise its own rule.
    report = validate_package(DirectorySource(B83 / v["id"] / "package"))
    assert report.ok, [e.message for e in report.errors]


def _text(variant: str, rel: str) -> str:
    return _lf_bytes(B83 / variant / "package" / rel).decode("utf-8")


def test_ck_02_change_is_the_one_declared() -> None:
    course = yaml.safe_load(_text("ck-02-completion-never-met", "course.yaml"))
    page = course["sections"][0]["activities"][0]
    assert page["type"] == "page"
    assert page["idnumber"] == "wk-01-guide"
    assert page["completion"] == "submit"


def test_ck_03_change_is_the_one_declared() -> None:
    assert "total_points: 120" in _text("ck-03-points-total-mismatch", "course.yaml")


def test_ck_09_change_is_the_one_declared() -> None:
    table = _text("ck-09-marking-table-sum", "weeks/02-task.md")
    points = [int(m) for m in re.findall(r"^\| [^|]+ \| (\d+) \|", table, re.MULTILINE)]
    assert sum(points) == 20  # the task stays worth 25 in course.yaml


def test_ck_12_url_is_in_the_source_file_only() -> None:
    # Source-level check only. It does NOT show that the URL reaches media_refs of the B2 model or
    # that a checker reports CK-12: that depends on checker design section 12 item 19 (open), so
    # the CK-12 expected finding is marked assertable: false.
    body = _text("ck-12-full-url-media", "weeks/01-guide.md")
    assert "https://example.invalid/diagram.png" in body


def test_b82_is_unchanged() -> None:
    got = {k: hashlib.sha256(v).hexdigest() for k, v in _files(B82).items()}
    assert got == B82_SHA256


SECRET = re.compile(
    r"(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|xox[bp]-[A-Za-z0-9-]{10,}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----|(?i:password|token|api[_-]?key)\s*[:=]\s*\S{6,})"
)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def test_no_secrets_or_learner_data() -> None:
    for p in B83.rglob("*"):
        if p.is_file():
            text = p.read_text(encoding="utf-8")
            assert not SECRET.search(text), f"possible secret in {p}"
            assert not EMAIL.search(text), f"email address in {p}"


def test_no_binary_files_without_a_recorded_source() -> None:
    # .mbz variants are PENDING MOODLE LAB: none may be committed here without a README record.
    assert not list(B83.rglob("*.mbz"))


# --- Course-model variants (B2). Built by make_models.py; not from a real Moodle backup. ---

MODELS = B83 / "models"
SCHEMA = ROOT / "contracts" / "course-model.v1.schema.json"


def _load_generator() -> Any:
    spec = importlib.util.spec_from_file_location("make_models", B83 / "make_models.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _model(name: str) -> dict[str, Any]:
    loaded: dict[str, Any] = json.loads(
        (MODELS / f"{name}.model.json").read_text("utf-8")
    )
    return loaded


def _activities(model: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {a["idnumber"]: a for s in model["sections"] for a in s["activities"]}


def test_model_files_are_exactly_what_the_generator_builds() -> None:
    assert _load_generator().main(["--check"]) == 0


def test_generator_dry_run_writes_nothing(tmp_path: Path) -> None:
    generator = _load_generator()
    generator.OUT = tmp_path / "out"
    assert generator.main(["--dry-run"]) == 0
    assert not generator.OUT.exists()


def test_every_model_entry_has_a_file_and_back() -> None:
    names = {p.name.removesuffix(".model.json") for p in MODELS.glob("*.model.json")}
    assert names == {v["id"] for v in _models()} | {"baseline"}
    for v in _models():
        assert v["status"] == "built"
        assert v["path"] == f"models/{v['id']}.model.json"
        assert v["id"].endswith("-model")


@pytest.mark.parametrize("name", ["baseline", *(v["id"] for v in _models())])
def test_model_is_a_valid_b2_course_model(name: str) -> None:
    schema = json.loads(SCHEMA.read_text("utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(_model(name)))
    assert not errors, [e.message for e in errors]


def _flat(node: Any, prefix: str = "") -> dict[str, Any]:
    """Every leaf of a JSON document as {"/a/0/b": value}. An empty dict or list is its own leaf."""
    if isinstance(node, dict) and node:
        items = node.items()
    elif isinstance(node, list) and node:
        items = enumerate(node)
    else:
        return {prefix: node}
    out: dict[str, Any] = {}
    for key, value in items:
        out.update(_flat(value, f"{prefix}/{key}"))
    return out


def _changed_paths(variant: str) -> set[str]:
    base, got = _flat(_model("baseline")), _flat(_model(variant))
    absent = object()
    return {
        k for k in base.keys() | got.keys() if base.get(k, absent) != got.get(k, absent)
    }


_AVAIL = "/sections/6/activities/0/availability"
# The ONLY paths each variant may change from the baseline. Paths use section and activity
# positions in the baseline. A new extra mutation fails test_model_variant_changes_only_its_paths.
ALLOWED_CHANGES: dict[str, set[str]] = {
    "ck-01-unreachable-by-past-date-model": {
        _AVAIL,  # null becomes the date condition: this leaf and the new keys below it
        f"{_AVAIL}/op",
        f"{_AVAIL}/showc/0",
        f"{_AVAIL}/c/0/type",
        f"{_AVAIL}/c/0/d",
        f"{_AVAIL}/c/0/t",
    },
    "ck-04-unlock-missing-activity-model": {"/sections/6/availability/c/0/cm"},
    # The baseline's week 3 already waits for the week 2 task, so one edit closes the cycle:
    # week 2 now waits for the week 3 task.
    "ck-05-circular-unlock-model": {"/sections/5/availability/c/0/cm"},
    "ck-06-duplicate-idnumber-model": {"/sections/5/activities/1/idnumber"},
    "ck-06-invalid-idnumber-model": {"/sections/4/activities/2/idnumber"},
    # Coupled on purpose: the marking table moves with the grade so CK-09 does not fire.
    "ck-07-protected-item-changed-model": {
        "/sections/3/activities/0/grade_item/max_grade",
        "/sections/3/activities/0/marking_table/points_total",
    },
    # One extra criterion appended: its three keys are the coupled paths.
    "ck-08-completion-criteria-missing-item-model": {
        "/course_completion/criteria/2/type",
        "/course_completion/criteria/2/cmid",
        "/course_completion/criteria/2/idnumber",
    },
    "ck-10-no-marking-workflow-model": {"/sections/4/activities/2/marking_workflow"},
    "ck-11-graded-practice-h5p-model": {
        "/sections/4/activities/1/grade_item",  # null becomes an object
        "/sections/4/activities/1/grade_item/max_grade",
    },
    "ck-12-full-url-media-model": {"/sections/4/activities/0/media_refs/0"},
    # Completion goes from automatic-on-submit to none, so the submit flag goes with it.
    "ck-13-unlock-without-completion-model": {
        "/sections/4/activities/2/completion/tracking",
        "/sections/4/activities/2/completion/submit",
    },
}


def test_every_model_variant_has_an_allowed_change_list() -> None:
    assert set(ALLOWED_CHANGES) == {v["id"] for v in _models()}


@pytest.mark.parametrize("variant", sorted(ALLOWED_CHANGES))
def test_model_variant_changes_only_its_paths(variant: str) -> None:
    assert _changed_paths(variant) == ALLOWED_CHANGES[variant]


def test_changed_path_check_catches_an_extra_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Negative control, on a copy: a stray edit to a variant must show up as an unlisted path.
    copy = tmp_path / "models"
    shutil.copytree(MODELS, copy)
    name = "ck-10-no-marking-workflow-model"
    data = json.loads((copy / f"{name}.model.json").read_text("utf-8"))
    data["course"]["total_points"] = 999
    (copy / f"{name}.model.json").write_text(json.dumps(data), "utf-8")
    monkeypatch.setattr(sys.modules[__name__], "MODELS", copy)
    assert _changed_paths(name) - ALLOWED_CHANGES[name] == {"/course/total_points"}


@pytest.mark.parametrize("v", _models(), ids=lambda v: v["id"])
def test_model_variant_differs_from_the_baseline(v: dict[str, Any]) -> None:
    assert _model(v["id"]) != _model("baseline")


def _cmids(model: dict[str, Any]) -> set[int]:
    return {a["cmid"] for a in _activities(model).values()}


def test_baseline_model_is_clean_on_the_facts_each_rule_reads() -> None:
    # Not a checker: it confirms the baseline holds nothing the 13 rules would report, so a
    # finding on a variant can only come from its one planted change.
    m = _model("baseline")
    acts = _activities(m)
    cmids = _cmids(m)
    assert len(acts) == len(list(a for s in m["sections"] for a in s["activities"]))
    for section in m["sections"]:
        for c in (section["availability"] or {}).get("c", []):
            target = acts_by_cmid(m)[c["cm"]]
            assert target["completion"]["tracking"] != "none"
    graded = sum((a["grade_item"] or {}).get("max_grade", 0) for a in acts.values())
    assert graded == m["course"]["total_points"]
    for a in acts.values():
        if a["type"] == "assignment":
            assert a["marking_workflow"] is True
            assert a["marking_table"]["points_total"] == a["grade_item"]["max_grade"]
        if a["type"] == "h5p":
            assert a["grade_item"] is None
        assert all(
            not r.startswith(("http://", "https://")) for r in a.get("media_refs", [])
        )
    for crit in m["course_completion"]["criteria"]:
        assert crit["cmid"] in cmids


def acts_by_cmid(model: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {a["cmid"]: a for a in _activities(model).values()}


def test_model_variants_plant_what_they_declare() -> None:
    def ids(m: dict[str, Any]) -> list[str]:
        return [a["idnumber"] for s in m["sections"] for a in s["activities"]]

    m = _model("ck-01-unreachable-by-past-date-model")
    (cond,) = _activities(m)["wk-03-guide"]["availability"]["c"]
    assert cond["type"] == "date" and cond["d"] == "<" and cond["t"] < 1700000000

    m = _model("ck-04-unlock-missing-activity-model")
    (sec,) = [s for s in m["sections"] if s["number"] == 6]
    assert sec["availability"]["c"][0]["cm"] not in _cmids(m)

    m = _model("ck-05-circular-unlock-model")
    by = {
        s["number"]: s["availability"]["c"][0]["cm"]
        for s in m["sections"]
        if s["availability"]
    }
    assert acts_by_cmid(m)[by[5]]["idnumber"] == "wk-03-task"
    assert acts_by_cmid(m)[by[6]]["idnumber"] == "wk-02-task"

    dup = ids(_model("ck-06-duplicate-idnumber-model"))
    assert dup.count("wk-01-task") == 2
    assert "Week 1 Task" in ids(_model("ck-06-invalid-idnumber-model"))

    m = _model("ck-07-protected-item-changed-model")
    assert _activities(m)["final-project"]["grade_item"]["max_grade"] == 80
    assert (
        _activities(_model("baseline"))["final-project"]["grade_item"]["max_grade"]
        == 100
    )

    m = _model("ck-08-completion-criteria-missing-item-model")
    assert any(c["cmid"] not in _cmids(m) for c in m["course_completion"]["criteria"])

    assert (
        _activities(_model("ck-10-no-marking-workflow-model"))["wk-01-task"][
            "marking_workflow"
        ]
        is False
    )
    assert _activities(_model("ck-11-graded-practice-h5p-model"))["wk-01-practice"][
        "grade_item"
    ] == {"max_grade": 10}
    refs = _activities(_model("ck-12-full-url-media-model"))["wk-01-guide"][
        "media_refs"
    ]
    assert refs == ["https://example.invalid/diagram.png"]

    m = _model("ck-13-unlock-without-completion-model")
    assert _activities(m)["wk-01-task"]["completion"]["tracking"] == "none"
    assert _activities(m)["wk-01-task"]["cmid"] == 112  # the cmid week 2 waits for
