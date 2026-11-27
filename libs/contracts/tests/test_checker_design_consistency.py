"""Consistency checks for docs/design/checker.md (R0, Student 2 task 1).

These tests read the design document and the B8.3 expected findings. They prove that the text
agrees with itself and with the recorded decisions. They do NOT prove that a checker detects
anything: no checker exists yet (Release 1).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[3]
DESIGN = ROOT / "docs" / "design" / "checker.md"
EXPECTED = ROOT / "testdata" / "b8-3-planted-errors" / "expected-findings.yaml"


def _design() -> str:
    return DESIGN.read_text(encoding="utf-8")


def _section(text: str, start: str, end: str) -> str:
    i = text.index(start)
    return text[i : text.index(end, i)]


def test_design_is_not_approved() -> None:
    # Only the guide sets Approved (CLAUDE.md section 6a.2).
    status = re.search(r"^\*\*Status:\*\* (.*)$", _design(), re.MULTILINE)
    assert status is not None
    assert status.group(1).startswith("Draft")
    assert "Approved" not in status.group(1).replace("`Approved`", "")
    assert "- [ ] **Guide:**" in _design()


def test_moodle_5_3_only_no_second_site() -> None:
    text = _design()
    # Decision 0017: Moodle 5.3 only. 4.5 may appear only as history or as "not pursued".
    assert "CHECKER_MOODLE45_URL" not in text
    assert "4.5 and 5.3" not in text.replace("on 4.5 and 5.3** (§11.3;", "")
    assert "both supported Moodle versions" not in text
    assert "moodle45" not in text


def test_json_example_summary_matches_its_entries() -> None:
    block = re.search(
        r"```json\n(\{\n  \"checker_version.*?)\n```", _design(), re.DOTALL
    )
    assert block is not None
    report: dict[str, Any] = json.loads(block.group(1))
    errors = [f for f in report["findings"] if f["severity"] == "error"]
    assert report["summary"]["errors"] == len(errors)
    assert report["summary"]["not_checked"] == len(report["not_checked"])
    for entry in report["not_checked"]:
        # per rule and per item: every entry names its item (finding 4)
        assert set(entry["item"]) == {"section", "idnumber", "title"}, entry
        assert entry["reason"].strip()
    # one state only: no second status such as "cannot judge"
    assert "cannot judge" not in json.dumps(report)


def test_report_never_says_clean() -> None:
    summary = _section(
        _design(), "The CLI and web summary line", "With a CK-04 finding"
    )
    assert "0 errors, N not checked" in summary
    assert 'No report describes a result as "clean"' in summary


def test_ck_02_is_in_every_explained_by_list() -> None:
    text = _design()
    # Every list of explaining rules names CK-02 (review finding 2), except the guide's own
    # item 13 answer, which is quoted as given and followed by the CK-02 proposal.
    for line in text.splitlines():
        if "CK-04, CK-05" in line and "CK-13" in line:
            if line.startswith("| 13 |") or "names CK-04, CK-05 and CK-13" in line:
                continue
            assert "CK-02" in line, line[:120]


def test_ck_07_and_ck_08_boundary_is_written_down() -> None:
    text = _design()
    ck07 = next(r for r in text.splitlines() if r.startswith("| **CK-07**"))
    ck08 = next(r for r in text.splitlines() if r.startswith("| **CK-08**"))
    assert "by its `idnumber`" in ck07 and "never by its `cmid`" in ck07
    assert "No `cmid` is ever compared between two models" in ck07
    assert "left to CK-08" in ck07
    assert (
        "two findings with two causes" in ck07
    )  # the deleted-protected-activity exception
    assert "never resolved against the reference model" in ck08
    assert "same model" in ck08


def test_b4_is_not_claimed_to_supply_idnumbers() -> None:
    row = next(r for r in _design().splitlines() if r.startswith("| B4 "))
    assert "does not supply the section or activity `idnumber`" in row
    assert "comes only from a Course Studio package or a Moodle `.mbz`" in row


def test_ck_08_expected_reason_keeps_also_expected_empty() -> None:
    data = yaml.safe_load(EXPECTED.read_text(encoding="utf-8"))
    (ck08,) = [v for v in data["variants"] if v["rule"] == "CK-08"]
    assert ck08["also_expected"] == []
    assert "same (merged) course model" in ck08["reason"]
    assert "never against the B8.1 reference model" in ck08["reason"]
    assert "CK-07 leaves an unresolved criterion alone" in ck08["reason"]


def test_ck_02_variant_does_not_claim_an_explained_item() -> None:
    data = yaml.safe_load(EXPECTED.read_text(encoding="utf-8"))
    (ck02,) = [v for v in data["variants"] if v["rule"] == "CK-02"]
    assert "CK-01" not in ck02["also_expected"]
    assert "no item is listed as explained by CK-02" in ck02["notes"]


def test_pending_guide_items_are_marked_pending_not_decided() -> None:
    rows = {
        int(m.group(1)): r
        for r in _design().splitlines()
        if (m := re.match(r"\| (\d+) \|", r))
    }
    assert "pending guide confirmation" in rows[24]
    assert "Pending guide" in rows[26]
    # every row of the section 12 table is closed with a pipe, so the table renders
    for n, row in rows.items():
        assert row.rstrip().endswith("|"), n
