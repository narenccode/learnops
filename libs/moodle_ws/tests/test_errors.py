"""One error family with stable codes (design §4.1, §10.2; library documentation, Q37)."""

from __future__ import annotations

import inspect
import string
import traceback

import pytest

import moodle_ws
from moodle_ws import (
    FunctionNotAllowed,
    InvalidParameters,
    MoodleConfigError,
    MoodleError,
    MoodleUnreachable,
    NotSupported,
    PermissionDenied,
    TokenInvalid,
    UnexpectedResponse,
    WorkflowStateNotAllowed,
    load_site,
    messages,
)

from .conftest import FAKE_TOKEN

CLASSES: list[type[MoodleError]] = [
    MoodleUnreachable,
    TokenInvalid,
    PermissionDenied,
    UnexpectedResponse,
    NotSupported,
    FunctionNotAllowed,
    WorkflowStateNotAllowed,
    MoodleConfigError,
    InvalidParameters,
]


MESSAGES = {
    name: value
    for name, value in vars(messages).items()
    if name.isupper() and isinstance(value, str) and not name.startswith("_")
}
SAFE_FIELDS = {
    "function",
    "state",
    "variable",
    "site",
    "allowed",
    "file",
    "field",
}
UNSAFE_VALUE = "https://site.invalid/private/path"


def fields(template: str) -> set[str]:
    return {name for _, name, _, _ in string.Formatter().parse(template) if name}


@pytest.mark.parametrize("error", CLASSES)
def test_every_error_derives_from_the_base(error: type[MoodleError]) -> None:
    assert issubclass(error, MoodleError)
    assert error is not MoodleError


@pytest.mark.parametrize("error", CLASSES)
def test_an_error_keeps_its_message_and_class_attributes(
    error: type[MoodleError],
) -> None:
    built = error("What happened. What to do next.")
    assert str(built) == "What happened. What to do next."
    assert built.args == ("What happened. What to do next.",)
    assert isinstance(built.code, str) and built.code
    assert isinstance(built.retryable, bool)


def test_the_base_is_not_retryable() -> None:
    assert MoodleError.retryable is False


def test_messages_are_found() -> None:
    assert len(MESSAGES) >= 13


@pytest.mark.parametrize("name", list(MESSAGES))
def test_a_message_says_what_happened_then_what_to_do(name: str) -> None:
    """UI-05: at least two sentences, ending as a sentence."""
    text = MESSAGES[name].format(**dict.fromkeys(fields(MESSAGES[name]), "value"))
    assert text.endswith(".")
    assert text.count(". ") >= 1


@pytest.mark.parametrize("name", list(MESSAGES))
def test_a_message_has_only_safe_fields_and_no_url(name: str) -> None:
    assert fields(MESSAGES[name]) <= SAFE_FIELDS
    assert "://" not in MESSAGES[name]


def visible(error: BaseException) -> str:
    """Everything a person or a log could see of an error."""
    return " ".join((str(error), repr(error), *traceback.format_exception(error)))


@pytest.mark.parametrize(
    "name", ["FUNCTION_NOT_ALLOWED", "VERSION_NOT_SUPPORTED", "UNKNOWN_SITE"]
)
def test_a_refusal_message_has_no_place_for_the_refused_value(name: str) -> None:
    assert fields(MESSAGES[name]) <= {"allowed"}


@pytest.mark.parametrize("value", [FAKE_TOKEN, UNSAFE_VALUE, "moodle40"])
def test_a_refused_site_is_not_repeated(value: str) -> None:
    with pytest.raises(MoodleConfigError) as caught:
        load_site(value, {})
    assert value not in visible(caught.value)
    assert "moodle45, moodle53" in str(caught.value)


def test_a_setting_equal_to_a_token_is_not_repeated() -> None:
    with pytest.raises(MoodleConfigError) as caught:
        load_site("moodle45", {"MOODLE45_WS_TOKEN": FAKE_TOKEN})
    assert FAKE_TOKEN not in visible(caught.value)
    assert "MOODLE45_URL" in str(caught.value)


def test_every_error_is_listed_here() -> None:
    public = {
        item
        for _, item in inspect.getmembers(moodle_ws, inspect.isclass)
        if issubclass(item, MoodleError) and item is not MoodleError
    }
    assert public == set(CLASSES)


def test_codes_are_unique() -> None:
    assert len({error.code for error in CLASSES}) == len(CLASSES)


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (MoodleUnreachable, "moodle_unreachable"),
        (TokenInvalid, "token_invalid"),
        (PermissionDenied, "permission_denied"),
        (UnexpectedResponse, "unexpected_response"),
    ],
)
def test_codes_match_the_design_failure_table(
    error: type[MoodleError], code: str
) -> None:
    assert error.code == code


def test_only_an_unreachable_moodle_is_worth_retrying() -> None:
    assert [error for error in CLASSES if error.retryable] == [MoodleUnreachable]
