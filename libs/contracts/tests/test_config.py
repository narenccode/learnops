"""The settings object `ValidationConfig` (PRD B1.4: protected idnumbers a site adds).

It must refuse anything that is not a collection of valid idnumbers, with a `ConfigError` that
says what to fix, and it must hold its own immutable copy of what it was given.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Iterator
from typing import Any

import pytest

from contracts import ConfigError, ValidationConfig


def build(value: Any) -> ValidationConfig:
    """Build a config from any value, so that tests can pass wrong types on purpose."""
    return ValidationConfig(protected_idnumbers=value)


def _generator() -> Iterator[str]:
    yield "capstone-gate"


# --- valid input -----------------------------------------------------------------------------


def test_default_configuration_adds_no_protected_idnumbers() -> None:
    assert ValidationConfig().protected_idnumbers == frozenset()


def test_several_configured_ids_are_kept_and_the_same_id_twice_counts_once() -> None:
    config = build(["capstone-gate", "pilot-gate", "wk-99", "pilot-gate"])
    assert config.protected_idnumbers == {"capstone-gate", "pilot-gate", "wk-99"}


@pytest.mark.parametrize(
    "given",
    [frozenset({"capstone-gate"}), {"capstone-gate"}, ["capstone-gate"], _generator()],
    ids=["frozenset", "set", "list", "generator"],
)
def test_any_collection_of_idnumbers_is_stored_as_a_frozenset(given: Any) -> None:
    stored = build(given).protected_idnumbers
    assert type(stored) is frozenset
    assert stored == {"capstone-gate"}


# --- immutability ----------------------------------------------------------------------------


def test_the_configuration_cannot_be_changed_after_creation() -> None:
    config = ValidationConfig(["capstone-gate"])
    with pytest.raises(dataclasses.FrozenInstanceError):
        config.protected_idnumbers = frozenset()  # type: ignore[misc]


def test_changing_the_callers_collection_later_does_not_change_the_configuration() -> (
    None
):
    as_set, as_list = {"capstone-gate"}, ["capstone-gate"]
    configs = [build(as_set), build(as_list)]
    as_set.add("sneaky-gate")
    as_list.append("sneaky-gate")
    assert all(c.protected_idnumbers == {"capstone-gate"} for c in configs)


def test_equal_configurations_are_equal_and_hash_alike_whatever_they_were_built_from() -> (
    None
):
    one, other = build({"a-b", "c-d"}), build(["c-d", "a-b"])
    assert one == other and hash(one) == hash(other)


# --- invalid input ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad", ["", "Final Project", "a_b", "-a", "a-", "é", "a\n", "a b"]
)
def test_a_configured_idnumber_must_be_a_valid_idnumber(bad: str) -> None:
    with pytest.raises(ConfigError):
        build([bad])


def test_a_bad_idnumber_message_names_the_value_and_what_to_do() -> None:
    # With several bad values the first in sorted order is named, whatever order they came in.
    with pytest.raises(ConfigError) as error:
        build(["z_z", "Bad_Id", "ok-id"])
    assert "Bad_Id" in str(error.value) and "lowercase" in str(error.value)
    assert "z_z" not in str(error.value)


@pytest.mark.parametrize(
    ("given", "named"),
    [
        ("capstone-gate", "single string"),
        ("ab", "single string"),  # would otherwise protect "a" and "b"
        ("final-project,course-feedback", "single string"),  # an unsplit setting
        ("", "single string"),
        (b"capstone-gate", "single string"),
        (None, "not None"),
        (1, "type int"),
        (True, "type bool"),
        ({"capstone-gate": True}, "type dict"),  # would be read as its keys
    ],
    ids=repr,
)
def test_something_that_is_not_a_collection_of_idnumbers_is_refused(
    given: Any, named: str
) -> None:
    with pytest.raises(ConfigError) as error:
        build(given)
    assert "collection" in str(error.value) and named in str(error.value)


@pytest.mark.parametrize(
    "member", [1, None, b"capstone-gate", ("capstone-gate",), True], ids=repr
)
def test_a_member_that_is_not_text_is_refused(member: Any) -> None:
    with pytest.raises(ConfigError, match="not text"):
        build(["capstone-gate", member])
    # Also next to a bad idnumber: a ConfigError, not a TypeError from sorting mixed types.
    with pytest.raises(ConfigError):
        build([member, "Bad_Id"])
