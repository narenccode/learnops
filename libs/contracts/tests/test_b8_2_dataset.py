"""B8.2 sample course: the dataset follows B1 (PRD B8.2, B1.2, B1.3, B1.4).

The shared validator checks the schema, unique idnumbers, protected idnumbers and that body files
exist. It does not yet check the other course rules (its `not_checked` list). These tests check
them for this one dataset only, so a change to the sample cannot break them unnoticed. They are
not a second validator: when the shared rules exist, these tests can shrink.

Nothing here needs Moodle. Restoring the sample, the checker result and the sections-only merge
are not tested here (see the dataset README: PENDING MOODLE LAB).
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

import pytest
import yaml

from contracts import DirectorySource, validate_package

from .helpers import ROOT, Doc

DATASET_DIR = ROOT / "testdata" / "b8-2-sample-course"
PACKAGE_DIR = DATASET_DIR / "package"

WEEKS = (1, 2, 3, 4)
POINTS_PER_TASK = 25
TOTAL_POINTS = 100

# The two default protected idnumbers (PRD B1.4).
DEFAULT_PROTECTED = frozenset({"final-project", "course-feedback"})

# PROPOSAL for test data, not a contract value. PRD B1.4 makes protected_section
# configurable and gives no default; the contract and the validator must never hard-code it.
WORKING_PROTECTED_SECTION = 7

# PRD C3.5 vocabulary: check name -> whether it takes an argument. B8.2 chooses not to use
# `command:` (the PRD says it reads "the course's check config", which B1 does not define).
CHECKS = {
    "repo_clone": False,
    "repo_file": True,
    "readme_sections": True,
    "command": True,
    "http_ok": True,
    "word_count": True,
}
MENTOR_ONLY = "—"
TABLE_HEADER = ["Criterion", "Points", "Full marks when", "Check"]
_TABLE = re.compile(
    r"<!-- marking-table v1 -->\n(.*?)\n<!-- /marking-table -->", re.DOTALL
)


# --- helpers ------------------------------------------------------------------------------


def _cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def check_problems(check: str) -> list[str]:
    """What is wrong with one Check cell (PRD B1.3, C3.5). An empty cell is allowed."""
    if check in ("", MENTOR_ONLY):
        return []
    problems: list[str] = []
    for part in check.split(";"):
        name, _, arg = part.strip().partition(":")
        if name not in CHECKS:
            problems.append(f"unknown check {name!r}")
        elif CHECKS[name] and not arg:
            problems.append(f"check {name!r} needs a value")
        elif not CHECKS[name] and arg:
            problems.append(f"check {name!r} takes no value")
        elif name == "word_count" and not arg.isdigit():
            problems.append("word_count needs a whole number")
    return problems


def table_problems(body: str, points: int) -> list[str]:
    """What is wrong with the marking table in an assignment body (PRD B1.3)."""
    tables = _TABLE.findall(body)
    if len(tables) != 1:
        return [f"expected one marking table, found {len(tables)}"]
    lines = tables[0].strip().splitlines()
    if len(lines) < 3 or _cells(lines[0]) != TABLE_HEADER:
        return ["header row is not Criterion | Points | Full marks when | Check"]
    problems: list[str] = []
    total = 0
    for line in lines[2:]:
        cells = _cells(line)
        if len(cells) != len(TABLE_HEADER) or not cells[1].isdigit():
            problems.append(f"bad row: {line}")
            continue
        total += int(cells[1])
        problems += check_problems(cells[3])
    if total != points:
        problems.append(f"rows add up to {total}, assignment has {points}")
    return problems


def collides(section_numbers: Iterable[int], protected_section: int) -> bool:
    """PRD B1.4: generated section numbers must not collide with the protected section."""
    return protected_section in set(section_numbers)


@pytest.fixture(scope="module")
def doc() -> Doc:
    loaded: Doc = yaml.safe_load((PACKAGE_DIR / "course.yaml").read_text("utf-8"))
    return loaded


def _section(doc: Doc, week: int) -> dict[str, Any]:
    section: dict[str, Any] = doc["sections"][week - 1]
    return section


def _activities(section: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = [
        a for a in section["activities"] if a["type"] == kind
    ]
    return found


def _body(activity: dict[str, Any]) -> str:
    return (PACKAGE_DIR / str(activity["body"])).read_text("utf-8")


# --- the package as a whole ---------------------------------------------------------------


def test_the_shared_validator_accepts_the_package() -> None:
    report = validate_package(DirectorySource(PACKAGE_DIR))
    assert report.ok, [issue.message for issue in report.errors]


def test_course_is_full_mode_with_a_total_of_100(doc: Doc) -> None:
    assert doc["schema"] == "learnops.course/v1"
    assert doc["course"]["mode"] == "full"
    assert doc["course"]["total_points"] == TOTAL_POINTS


def test_there_are_four_week_sections_numbered_1_to_4(doc: Doc) -> None:
    assert [s["number"] for s in doc["sections"]] == list(WEEKS)
    assert [s["idnumber"] for s in doc["sections"]] == [f"wk-0{n}" for n in WEEKS]


def test_idnumbers_are_the_week_pattern_and_never_protected(doc: Doc) -> None:
    ids = [s["idnumber"] for s in doc["sections"]]
    ids += [a["idnumber"] for s in doc["sections"] for a in s["activities"]]
    assert len(ids) == len(set(ids)) == 4 + 8
    assert all(re.fullmatch(r"wk-0[1-4](-guide|-task)?", i) for i in ids)
    assert not DEFAULT_PROTECTED & set(ids)


def test_no_protected_item_and_no_backup_file_is_in_the_dataset() -> None:
    assert list(DATASET_DIR.rglob("*.mbz")) == []
    text = "\n".join(
        p.read_text("utf-8") for p in PACKAGE_DIR.rglob("*") if p.is_file()
    )
    assert not any(f"idnumber: {name}" in text for name in DEFAULT_PROTECTED)


def test_bodies_hold_no_links(doc: Doc) -> None:
    for path in (PACKAGE_DIR / "weeks").glob("*.md"):
        assert not re.search(r"https?://|www\.", path.read_text("utf-8")), path.name


# --- B1.2: week structure, unlock chain, points -------------------------------------------


@pytest.mark.parametrize("week", WEEKS)
def test_week_has_one_guide_page_then_one_task_assignment(doc: Doc, week: int) -> None:
    section = _section(doc, week)
    assert [a["type"] for a in section["activities"]] == ["page", "assignment"]
    assert [a["idnumber"] for a in section["activities"]] == [
        f"wk-0{week}-guide",
        f"wk-0{week}-task",
    ]


@pytest.mark.parametrize("week", WEEKS)
def test_week_unlocks_when_the_previous_task_is_submitted(doc: Doc, week: int) -> None:
    after = _section(doc, week)["unlock"]["after"]
    if week == 1:
        assert after is None
        return
    assert after == f"wk-0{week - 1}-task"
    previous_task = _activities(_section(doc, week - 1), "assignment")[0]
    assert previous_task["idnumber"] == after
    assert previous_task["completion"] == "submit"


def test_each_task_is_worth_25_and_the_tasks_add_up_to_the_total(doc: Doc) -> None:
    tasks = [_activities(_section(doc, w), "assignment")[0] for w in WEEKS]
    assert [t["points"] for t in tasks] == [POINTS_PER_TASK] * len(WEEKS)
    assert sum(t["points"] for t in tasks) == doc["course"]["total_points"]


# --- B1.3: marking tables -----------------------------------------------------------------


@pytest.mark.parametrize("week", WEEKS)
def test_task_has_a_valid_marking_table(doc: Doc, week: int) -> None:
    task = _activities(_section(doc, week), "assignment")[0]
    assert table_problems(_body(task), task["points"]) == []


def test_the_sample_does_not_use_command_checks() -> None:
    for path in (PACKAGE_DIR / "weeks").glob("*-task.md"):
        assert "command:" not in path.read_text("utf-8"), path.name


def test_the_table_check_catches_the_mistakes_it_exists_for() -> None:
    good = (PACKAGE_DIR / "weeks" / "01-task.md").read_text("utf-8")
    assert table_problems(good, POINTS_PER_TASK) == []
    assert table_problems(good, POINTS_PER_TASK + 1)  # points do not add up
    assert table_problems(good.replace("http_ok:demo_url", "ping:demo_url"), 25)
    assert table_problems(good.replace("word_count:150", "word_count"), 25)
    assert table_problems("# no table here", 25)


# --- B1.4: protected section --------------------------------------------------------------


def test_week_numbers_do_not_collide_with_the_working_protected_section(
    doc: Doc,
) -> None:
    numbers = [s["number"] for s in doc["sections"]]
    assert not collides(numbers, WORKING_PROTECTED_SECTION)


def test_the_collision_check_would_catch_the_earlier_proposal_of_section_3(
    doc: Doc,
) -> None:
    # Negative control: with the protected section at 3 (the earlier B8.1 proposal) week 3 would
    # sit on it. This is why the proposal puts it after the weeks.
    numbers = [s["number"] for s in doc["sections"]]
    assert collides(numbers, 3)
