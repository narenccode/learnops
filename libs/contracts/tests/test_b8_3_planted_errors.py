"""B8.3 planted-error dataset: structure and consistency (PRD B8.3, C2.3, C2.7).

These tests check the DATASET and its expected-findings file only. They do NOT prove that the
Course Checker detects anything: no checker exists yet. Detection (PRD C2.7) is measured in
Release 1, when the checker runs on these variants.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from contracts import DirectorySource, validate_package

from .helpers import ROOT

B82 = ROOT / "testdata" / "b8-2-sample-course"
B83 = ROOT / "testdata" / "b8-3-planted-errors"
EXPECTED = B83 / "expected-findings.yaml"

CK_RULES = {f"CK-{n:02d}" for n in range(1, 14)}
STATUSES = {"built", "planned", "pending-lab"}
KINDS = {"package", "mbz"}
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
    return [v for v in _variants() if v["status"] == "built"]


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
    (ck12,) = [v for v in _variants() if v["rule"] == "CK-12"]
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
    folders = {p.name for p in B83.iterdir() if p.is_dir()} - OTHER_FOLDERS
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
