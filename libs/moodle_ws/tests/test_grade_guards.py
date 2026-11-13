"""Client guards for grade writes (B4 §3, §3a R2 and R9): no direct grade write.

MoodleClient.call() runs the draft rule and the attempt and grade guards on mod_assign_save_grade
and then refuses it. Only a sealed, single-use WriteReceipt can send one, and the guards run again
on that path. The guarded helper that issues receipts (maximum grade, locked state, marking
workflow, read-back) is added in a later PR; until then no grade write can be sent at all.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from moodle_ws import (
    GradeWriteNotAllowed,
    MoodleClient,
    Site,
    SiteSettings,
    WorkflowStateNotAllowed,
    grade_in_range,
    parse_grade,
)
from moodle_ws.client import WriteReceipt, _issue_receipt
from moodle_ws.messages import WRITE_NEEDS_HELPER

from .conftest import VALID_WRITE, send_checked
from .fake_transport import FakeTransport

SAVE = "mod_assign_save_grade"


ROOT = Path(__file__).resolve().parents[3]


PRIVATE_NAMES = re.compile(
    r"\b(_issue_receipt|_send_checked_write|_RECEIPT_SEAL|WriteReceipt)\b"
)


# --- a direct call never sends a grade write -------------------------------------------------


@pytest.mark.parametrize("version", ["4.5", "5.3"])
@pytest.mark.parametrize(
    "change",
    [
        pytest.param({}, id="valid in every other way"),
        pytest.param({"grade": 1000}, id="above any maximum"),
        pytest.param({"grade": 0}, id="zero"),
        pytest.param({"note": "anything"}, id="extra parameter"),
    ],
)
def test_a_direct_call_never_sends_a_grade_write(
    version: str, change: dict[str, Any], settings: SiteSettings
) -> None:
    """No maximum, locked-state or marking-workflow check can run inside call(), so a direct
    grade write is refused after the guards, on both versions, and nothing reaches Moodle."""
    if version == "5.3":
        settings = replace(settings, site=Site.MOODLE53, moodle_version="5.3")
    transport = FakeTransport()
    with pytest.raises(GradeWriteNotAllowed) as caught:
        MoodleClient(settings, transport).call(SAVE, {**VALID_WRITE, **change})
    assert str(caught.value) == WRITE_NEEDS_HELPER
    assert transport.calls == []


def test_a_direct_call_still_runs_the_other_guards_first(
    settings: SiteSettings,
) -> None:
    """The specific reason is still reported: the guards are not skipped by the refusal."""
    transport = FakeTransport()
    client = MoodleClient(settings, transport)
    with pytest.raises(WorkflowStateNotAllowed):
        client.call(SAVE, {**VALID_WRITE, "workflowstate": "released"})
    with pytest.raises(GradeWriteNotAllowed, match="never -1"):
        client.call(SAVE, {**VALID_WRITE, "attemptnumber": -1})
    assert transport.calls == []


# --- R2: explicit attempt, never -1 -----------------------------------------------------------


@pytest.mark.parametrize("attempt", [-1, -2, None, True, 1.0, "0"])
def test_r2_call_refuses_a_write_without_an_explicit_attempt(
    attempt: Any, settings: SiteSettings
) -> None:
    transport = FakeTransport()
    with pytest.raises(GradeWriteNotAllowed, match="never -1"):
        MoodleClient(settings, transport).call(
            SAVE, {**VALID_WRITE, "attemptnumber": attempt}
        )
    assert transport.calls == []


def test_r2_call_refuses_a_write_with_no_attempt_at_all(settings: SiteSettings) -> None:
    transport = FakeTransport()
    params = {k: v for k, v in VALID_WRITE.items() if k != "attemptnumber"}
    with pytest.raises(GradeWriteNotAllowed):
        MoodleClient(settings, transport).call(SAVE, params)
    assert transport.calls == []


# --- R9: grades as exact numbers; plain non-negative numbers only -----------------------------


@pytest.mark.parametrize(
    ("stored", "sent", "equal"),
    [
        ("84.50000", 84.5, True),
        ("84.50000", "84.5", True),
        ("85.00000", 85, True),
        ("0.10000", 0.1, True),
        ("84.49999", 84.5, False),
        ("84.50001", 84.5, False),
        ("84.5", 84.50001, False),
    ],
)
def test_r9_grades_are_compared_as_exact_numbers(
    stored: str, sent: Any, equal: bool
) -> None:
    assert (parse_grade(stored) == parse_grade(sent)) is equal


@pytest.mark.parametrize(
    "value",
    ["", " 84.5", "84.5 ", "1e2", "NaN", "Infinity", "+5", "84,5", True, None, [1]],
)
def test_r9_only_plain_numbers_parse(value: Any) -> None:
    assert parse_grade(value) is None


def test_r9_parsing_is_exact_not_float() -> None:
    assert parse_grade("84.50000") == Decimal("84.5")
    assert parse_grade(0.1) == Decimal("0.1")


@pytest.mark.parametrize("grade", [0, 100, "100.00000", 99.99999])
def test_r9_the_range_includes_both_ends(grade: Any) -> None:
    assert grade_in_range(grade, 100)


@pytest.mark.parametrize("maximum", [None, "", "abc", -1, True])
def test_r9_an_unknown_maximum_refuses_the_write(maximum: Any) -> None:
    assert not grade_in_range(50, maximum)


def test_r9_call_refuses_a_grade_that_is_not_a_plain_number(
    settings: SiteSettings,
) -> None:
    for grade in (-1, "abc", None, True, "1e2"):
        transport = FakeTransport()
        with pytest.raises(GradeWriteNotAllowed):
            MoodleClient(settings, transport).call(
                SAVE, {**VALID_WRITE, "grade": grade}
            )
        assert transport.calls == []


# --- the receipt cannot be forged, reused or moved ---------------------------------------------


def test_a_receipt_cannot_be_built_without_the_seal(settings: SiteSettings) -> None:
    client = MoodleClient(settings, FakeTransport())
    with pytest.raises(GradeWriteNotAllowed):
        WriteReceipt(object(), client, dict(VALID_WRITE))


def test_a_receipt_works_once(settings: SiteSettings) -> None:
    transport = FakeTransport()
    client = MoodleClient(settings, transport)
    receipt = _issue_receipt(client, VALID_WRITE)
    client._send_checked_write(receipt)
    with pytest.raises(GradeWriteNotAllowed):
        client._send_checked_write(receipt)
    assert len(transport.calls) == 1


def test_a_receipt_is_used_up_even_if_the_send_fails(settings: SiteSettings) -> None:
    """R11: a write whose answer is lost is never sent again, not even with the same receipt."""
    transport = FakeTransport(failure=TimeoutError("lost"))
    client = MoodleClient(settings, transport)
    receipt = _issue_receipt(client, VALID_WRITE)
    with pytest.raises(Exception):
        client._send_checked_write(receipt)
    transport.failure = None
    with pytest.raises(GradeWriteNotAllowed):
        client._send_checked_write(receipt)
    assert len(transport.calls) == 1


def test_a_receipt_belongs_to_one_client(settings: SiteSettings) -> None:
    first, second = FakeTransport(), FakeTransport()
    receipt = _issue_receipt(MoodleClient(settings, first), VALID_WRITE)
    with pytest.raises(GradeWriteNotAllowed):
        MoodleClient(settings, second)._send_checked_write(receipt)
    assert first.calls == [] and second.calls == []


@pytest.mark.parametrize("fake", [None, object(), {"_params": VALID_WRITE}])
def test_only_a_real_receipt_is_accepted(fake: Any, settings: SiteSettings) -> None:
    transport = FakeTransport()
    with pytest.raises(GradeWriteNotAllowed):
        MoodleClient(settings, transport)._send_checked_write(fake)
    assert transport.calls == []


# --- the guards still run on the receipt path --------------------------------------------------


@pytest.mark.parametrize(
    ("change", "error"),
    [
        ({"attemptnumber": -1}, GradeWriteNotAllowed),
        ({"attemptnumber": None}, GradeWriteNotAllowed),
        ({"grade": -1}, GradeWriteNotAllowed),
        ({"grade": "NaN"}, GradeWriteNotAllowed),
        ({"workflowstate": "released"}, WorkflowStateNotAllowed),
        ({"note": {"deep": "released"}}, WorkflowStateNotAllowed),
    ],
)
def test_the_receipt_path_still_runs_the_attempt_grade_and_draft_guards(
    change: dict[str, Any], error: type[Exception], settings: SiteSettings
) -> None:
    transport = FakeTransport()
    with pytest.raises(error):
        send_checked(MoodleClient(settings, transport), {**VALID_WRITE, **change})
    assert transport.calls == []


def test_what_is_sent_is_the_receipts_copy(settings: SiteSettings) -> None:
    transport = FakeTransport()
    client = MoodleClient(settings, transport)
    params = dict(VALID_WRITE)
    receipt = _issue_receipt(client, params)
    params["grade"] = 1000
    client._send_checked_write(receipt)
    assert transport.calls == [(SAVE, VALID_WRITE)]


# --- nobody else uses the private write path ---------------------------------------------------


def python_files_outside_the_library() -> Iterator[Path]:
    library = ROOT / "libs" / "moodle_ws"
    for path in ROOT.rglob("*.py"):
        parts = set(path.relative_to(ROOT).parts)
        if parts & {".venv", "node_modules", ".git"} or library in path.parents:
            continue
        yield path


def test_no_module_outside_the_library_uses_the_private_write_path() -> None:
    offenders = [
        str(path.relative_to(ROOT))
        for path in python_files_outside_the_library()
        if PRIVATE_NAMES.search(path.read_text(encoding="utf-8", errors="replace"))
    ]
    assert offenders == []


def test_inside_the_library_only_the_client_issues_or_sends_receipts() -> None:
    """Until the guarded write helper exists, nothing in the library issues a receipt."""
    library = ROOT / "libs" / "moodle_ws"
    users = sorted(
        path.name
        for path in library.glob("*.py")
        if re.search(
            r"\b(_issue_receipt|_send_checked_write)\(",
            path.read_text(encoding="utf-8"),
        )
    )
    assert users == ["client.py"]
