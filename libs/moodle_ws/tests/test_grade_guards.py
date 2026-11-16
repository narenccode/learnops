"""Client guards for grade writes (B4 §3, §3a R2 and R9): no direct grade write.

MoodleClient.call() runs the draft rule and the attempt and grade guards on mod_assign_save_grade
and then refuses it. The receipt path (WriteReceipt, _issue_receipt, _send_checked_write) is
removed, because a caller could import it and skip the write checks (the guide on PR #76, 15 Nov:
close the bypass in code). The only sender is the single-use closure MoodleClient.write_draft_grade
creates for one run of every check and the read-back (test_grade_write.py).
"""

from __future__ import annotations

import inspect
import re
from collections.abc import Iterator, Mapping
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import moodle_ws
import moodle_ws.client
import moodle_ws.grade_write
from moodle_ws import (
    GradeWriteNotAllowed,
    MoodleClient,
    MoodleUnreachable,
    Site,
    SiteSettings,
    WorkflowStateNotAllowed,
    grade_in_range,
    parse_grade,
)
from moodle_ws.messages import WRITE_NEEDS_HELPER

from .conftest import VALID_WRITE
from .fake_transport import FakeTransport
from .source_fake import SourceFakeMoodle

SAVE = "mod_assign_save_grade"


ROOT = Path(__file__).resolve().parents[3]


LIBRARY = ROOT / "libs" / "moodle_ws"


# Private client internals that reach, or could reach, the transport. No module outside the
# library may use them.
PRIVATE_NAMES = re.compile(r"\._transport\b|\._send\(|\b_copy_params\b")


REMOVED_NAMES = (
    "WriteReceipt",
    "_RECEIPT_SEAL",
    "_issue_receipt",
    "_send_checked_write",
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


# --- the guards still give their own reason on a direct call -----------------------------------


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
def test_a_direct_call_reports_the_guards_reason_not_the_direct_write_refusal(
    change: dict[str, Any], error: type[Exception], settings: SiteSettings
) -> None:
    transport = FakeTransport()
    with pytest.raises(error) as caught:
        MoodleClient(settings, transport).call(SAVE, {**VALID_WRITE, **change})
    assert str(caught.value) != WRITE_NEEDS_HELPER
    assert transport.calls == []


# --- the receipt bypass is closed in code ------------------------------------------------------


@pytest.mark.parametrize("name", REMOVED_NAMES)
def test_the_receipt_path_no_longer_exists(name: str) -> None:
    for module in (moodle_ws, moodle_ws.client, moodle_ws.grade_write):
        assert not hasattr(module, name)
    assert not hasattr(MoodleClient, name)


@pytest.mark.parametrize(
    "params",
    [
        pytest.param(VALID_WRITE, id="valid"),
        pytest.param({**VALID_WRITE, "note": "anything"}, id="extra parameter"),
    ],
)
def test_the_clients_internal_send_refuses_a_grade_write_too(
    params: dict[str, Any], settings: SiteSettings
) -> None:
    """The one internal method that reaches the transport refuses a grade write itself, so calling
    it directly, skipping call(), sends nothing either."""
    transport = FakeTransport()
    with pytest.raises(GradeWriteNotAllowed) as caught:
        MoodleClient(settings, transport)._send(SAVE, dict(params))
    assert str(caught.value) == WRITE_NEEDS_HELPER
    assert transport.calls == []


def test_the_library_reaches_the_transport_in_one_place_only() -> None:
    """Every transport call goes through MoodleClient._send, which refuses a grade write."""
    places = {
        path.name: len(
            re.findall(r"\._transport\.call\(", path.read_text(encoding="utf-8"))
        )
        for path in LIBRARY.glob("*.py")
    }
    assert {name: count for name, count in places.items() if count} == {"client.py": 2}
    assert "._transport.call(" in inspect.getsource(MoodleClient._send)
    assert "._transport.call(" in inspect.getsource(MoodleClient.write_draft_grade)


def test_the_internal_send_cannot_stand_in_for_the_guarded_sender(
    settings: SiteSettings,
) -> None:
    """_checked_write runs every check and then calls the sender it is given. Given anything built
    from the client's internals instead of write_draft_grade's own sender, nothing is sent."""
    moodle = SourceFakeMoodle("4.5")  # an unlocked state, so every check passes
    client = MoodleClient(settings, moodle)

    def internal(values: Mapping[str, Any]) -> Any:
        return client._send(SAVE, dict(values))

    with pytest.raises(GradeWriteNotAllowed):
        moodle_ws.grade_write._checked_write(client, VALID_WRITE, 100, internal)
    assert moodle.count(SAVE) == 0
    assert moodle.grade is None


def test_the_guarded_sender_works_once(
    settings: SiteSettings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If the write logic ever called its sender twice, the second call is refused (R8, R11)."""
    transport = FakeTransport()
    outcomes: list[str] = []

    def twice(
        client: Any, params: Mapping[str, Any], max_grade: object, send: Any
    ) -> Any:
        send(params)
        try:
            send(params)
        except GradeWriteNotAllowed as error:
            outcomes.append(str(error))
        return None

    monkeypatch.setattr(moodle_ws.grade_write, "_checked_write", twice)
    MoodleClient(settings, transport).write_draft_grade(VALID_WRITE, 100)
    assert outcomes == [WRITE_NEEDS_HELPER]
    assert [name for name, _ in transport.calls] == [SAVE]


def test_the_guarded_sender_is_used_up_even_if_the_send_fails(
    settings: SiteSettings, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R11: a write whose answer is lost is never sent again, not even by the same sender."""
    transport = FakeTransport(failure=TimeoutError("lost"))
    outcomes: list[str] = []

    def retry_after_a_failure(
        client: Any, params: Mapping[str, Any], max_grade: object, send: Any
    ) -> Any:
        # A raw TimeoutError from the transport becomes the library's own MoodleUnreachable.
        with pytest.raises(MoodleUnreachable):
            send(params)
        transport.failure = None
        try:
            send(params)
        except GradeWriteNotAllowed as error:
            outcomes.append(str(error))
        return None

    monkeypatch.setattr(moodle_ws.grade_write, "_checked_write", retry_after_a_failure)
    MoodleClient(settings, transport).write_draft_grade(VALID_WRITE, 100)
    assert outcomes == [WRITE_NEEDS_HELPER]
    assert len(transport.calls) == 1


# --- nobody else uses the client's internals ---------------------------------------------------


def python_files_outside_the_library() -> Iterator[Path]:
    for path in ROOT.rglob("*.py"):
        parts = set(path.relative_to(ROOT).parts)
        if parts & {".venv", "node_modules", ".git"} or LIBRARY in path.parents:
            continue
        yield path


def test_no_module_outside_the_library_uses_the_clients_internals() -> None:
    offenders = [
        str(path.relative_to(ROOT))
        for path in python_files_outside_the_library()
        if PRIVATE_NAMES.search(path.read_text(encoding="utf-8", errors="replace"))
    ]
    assert offenders == []
