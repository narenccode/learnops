"""Reading availability JSON and resolving `cm = -1` (guide-confirmed, still provisional until
verified on Moodle 4.5 and 5.3). The inner form is Moodle's and is not described by a schema, so
these tests only show that conditions are found by type, in any order, and that -1 follows the
guide's rule. Reporting an unresolved -1 as CK-04 belongs to the checker and is not tested here.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from contracts.availability import (
    PREVIOUS_ACTIVITY,
    conditions_of_type,
    resolve_previous_cmid,
)

ROOT = Path(__file__).resolve().parents[3]
FROM_PACKAGE = ROOT / "contracts" / "examples" / "course-model.v1" / "from-package.json"

Doc = dict[str, Any]
# from-package.json: week 1 = guide (cmid 1, none), task (2, automatic); week 2 = guide (3, none),
# task (4, automatic).


@pytest.fixture
def model() -> Doc:
    loaded: Doc = json.loads(FROM_PACKAGE.read_text(encoding="utf-8"))
    return copy.deepcopy(loaded)


def set_tracking(model: Doc, tracking: dict[tuple[int, int], str]) -> None:
    for (s, a), value in tracking.items():
        model["sections"][s]["activities"][a]["completion"]["tracking"] = value


# --- conditions are found by type, not by position -----------------------------------------


def test_conditions_are_found_by_type(model: Doc) -> None:
    availability = model["sections"][1]["availability"]
    assert conditions_of_type(availability, "completion") == [
        {"type": "completion", "cm": 2, "e": 1}
    ]
    assert [c["t"] for c in conditions_of_type(availability, "date")] == [1770575400]


def test_condition_order_does_not_change_the_interpretation(model: Doc) -> None:
    availability = model["sections"][1]["availability"]
    reversed_ = copy.deepcopy(availability)
    reversed_["c"].reverse()
    reversed_["showc"].reverse()
    for kind in ("completion", "date"):
        assert conditions_of_type(reversed_, kind) == conditions_of_type(
            availability, kind
        )


def test_nested_groups_are_searched_and_unknown_shapes_are_ignored() -> None:
    availability = {
        "op": "&",
        "c": [{"op": "|", "c": [{"type": "completion", "cm": 7}]}, "odd", 3, {}],
    }
    assert conditions_of_type(availability, "completion") == [
        {"type": "completion", "cm": 7}
    ]
    assert conditions_of_type(None, "completion") == []
    assert conditions_of_type({"odd": "shape"}, "date") == []


# --- cm = -1: the nearest earlier activity with manual or automatic tracking ---------------


def test_previous_activity_marker_is_minus_one() -> None:
    assert PREVIOUS_ACTIVITY == -1


def test_minus_one_resolves_to_the_previous_tracked_activity(model: Doc) -> None:
    set_tracking(model, {(1, 0): "manual"})
    # Holder: week 2 task. Its neighbour before it, the week 2 guide (cmid 3), is tracked.
    assert resolve_previous_cmid(model, 1, 1) == 3


def test_minus_one_skips_activities_without_tracking(model: Doc) -> None:
    # Holder: week 2 task. The guide before it has no tracking, so the week 1 task (2) is used.
    assert resolve_previous_cmid(model, 1, 1) == 2


def test_minus_one_takes_the_nearest_not_the_first_tracked_activity(
    model: Doc,
) -> None:
    set_tracking(model, {(0, 0): "automatic", (1, 0): "manual"})
    assert resolve_previous_cmid(model, 1, 1) == 3


def test_minus_one_with_no_eligible_earlier_activity_cannot_be_met(
    model: Doc,
) -> None:
    assert resolve_previous_cmid(model, 0, 0) is None  # nothing is earlier
    assert (
        resolve_previous_cmid(model, 0, 1) is None
    )  # the only earlier one is untracked
    set_tracking(model, {(0, 1): "none"})
    assert resolve_previous_cmid(model, 1, 1) is None  # earlier ones all untracked


def test_a_later_activity_is_never_a_candidate(model: Doc) -> None:
    set_tracking(model, {(1, 1): "automatic", (1, 0): "none", (0, 1): "none"})
    assert resolve_previous_cmid(model, 1, 0) is None


def test_a_section_rule_has_the_same_semantics_as_an_activity_rule(model: Doc) -> None:
    # Week 2's own availability is read from just before its first activity.
    assert resolve_previous_cmid(model, 1) == 2
    assert resolve_previous_cmid(model, 0) is None


def test_course_order_is_list_order_not_section_number(model: Doc) -> None:
    model["sections"][0]["number"], model["sections"][1]["number"] = 2, 1
    assert resolve_previous_cmid(model, 1, 1) == 2


# --- holder indices outside the model are refused, never resolved to another activity -------


@pytest.mark.parametrize(
    ("section_index", "activity_index"),
    [
        (-1, None),  # negative section
        (-1, 0),
        (2, None),  # one past the last section (the model has 2)
        (5, 0),  # far beyond the end
        (0, -1),  # negative activity
        (1, 2),  # one past the last activity of week 2 (it has 2)
        (0, 9),  # far beyond the end
    ],
)
def test_a_holder_outside_the_model_is_refused(
    model: Doc, section_index: int, activity_index: int | None
) -> None:
    with pytest.raises(ValueError, match="outside"):
        resolve_previous_cmid(model, section_index, activity_index)


def test_an_empty_section_is_a_valid_section_holder_but_has_no_activity_holder(
    model: Doc,
) -> None:
    model["sections"][1]["activities"] = []
    assert resolve_previous_cmid(model, 1) == 2
    with pytest.raises(ValueError, match="outside section 1"):
        resolve_previous_cmid(model, 1, 0)


def test_the_error_names_the_bad_index_and_the_size_of_the_model(model: Doc) -> None:
    with pytest.raises(ValueError, match=r"section_index 7 .* 2 section\(s\)"):
        resolve_previous_cmid(model, 7)


# --- decision 3: a section's -1 is read strictly before the section ---------------------------


def test_a_section_rule_never_resolves_to_an_activity_inside_the_same_section(
    model: Doc,
) -> None:
    # Only week 2's own activities are tracked: nothing before week 2 can satisfy its -1.
    set_tracking(
        model, {(0, 0): "none", (0, 1): "none", (1, 0): "automatic", (1, 1): "manual"}
    )
    assert resolve_previous_cmid(model, 1) is None


def test_a_section_rule_resolves_to_the_last_tracked_activity_of_the_section_before(
    model: Doc,
) -> None:
    set_tracking(
        model, {(0, 0): "manual", (0, 1): "none", (1, 0): "automatic", (1, 1): "manual"}
    )
    assert (
        resolve_previous_cmid(model, 1) == 1
    )  # week 1's guide, the last tracked one before


def test_the_first_section_has_no_earlier_activity(model: Doc) -> None:
    set_tracking(model, {(0, 0): "manual", (0, 1): "automatic"})
    assert resolve_previous_cmid(model, 0) is None


def test_an_out_of_range_holder_never_returns_the_last_tracked_activity(
    model: Doc,
) -> None:
    # The old bounds bug: an index past the end walked the whole course and returned the last
    # tracked activity (cmid 4) instead of failing.
    assert resolve_previous_cmid(model, 1, 1) == 2
    for holder in ((1, 2), (1, 99), (9, None), (-1, None)):
        with pytest.raises(ValueError):
            resolve_previous_cmid(model, *holder)
