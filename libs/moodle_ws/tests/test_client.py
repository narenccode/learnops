"""The draft rule (B4 §3, module rule 1) and the shape of the client.

NOT shown here: how Moodle treats any workflow state (lab checks 1, 4 and 5).
"""

from __future__ import annotations

import socket
from collections.abc import Mapping
from dataclasses import replace
from types import MappingProxyType
from typing import Any, cast

import pytest

from moodle_ws import (
    AllowList,
    FunctionNotAllowed,
    InvalidParameters,
    MoodleClient,
    MoodleError,
    MoodleUnreachable,
    NotSupported,
    PermissionDenied,
    Site,
    SiteSettings,
    TokenInvalid,
    UnexpectedResponse,
    WorkflowStateNotAllowed,
    create_client,
    load_allowlist,
)

from .conftest import FAKE_TOKEN, VALID_WRITE, send_checked
from .fake_transport import FakeTransport

SAVE_GRADE = "mod_assign_save_grade"
SET_USER_FLAGS = "mod_assign_set_user_flags"


def test_a_checked_grade_write_with_readyforrelease_is_sent(
    settings: SiteSettings,
) -> None:
    transport = FakeTransport()
    send_checked(MoodleClient(settings, transport), VALID_WRITE)
    assert transport.calls == [(SAVE_GRADE, VALID_WRITE)]


@pytest.mark.parametrize(
    "params",
    [
        None,
        {},
        {"workflowstate": "released"},
        {"workflowstate": "RELEASED"},
        {"workflowstate": " released "},
        {"workflowstate": "readyforrelease "},
        {"workflowstate": "inmarking"},
        {"workflowstate": ""},
        {"workflowstate": None},
        {"workflowstate": ["readyforrelease"]},
    ],
)
def test_a_grade_write_that_breaks_the_draft_rule_is_refused(
    params: dict[str, Any] | None, settings: SiteSettings
) -> None:
    transport = FakeTransport()
    with pytest.raises(WorkflowStateNotAllowed):
        MoodleClient(settings, transport).call(SAVE_GRADE, params)
    assert transport.calls == []


def test_released_gets_its_own_message(settings: SiteSettings) -> None:
    with pytest.raises(WorkflowStateNotAllowed, match="never releases grades"):
        MoodleClient(settings, FakeTransport()).call(
            SAVE_GRADE, {"workflowstate": "released"}
        )


@pytest.mark.parametrize(
    "other",
    ["the code was released on Friday", {"deep": ["not released yet"]}],
)
def test_a_sentence_containing_the_word_is_allowed(
    other: Any, settings: SiteSettings
) -> None:
    transport = FakeTransport()
    params = {**VALID_WRITE, "note": other}
    send_checked(MoodleClient(settings, transport), params)
    assert len(transport.calls) == 1


NESTED_RELEASED = [
    pytest.param({"a": "released"}, id="top level"),
    pytest.param({"a": {"b": ["x", "Released"]}}, id="nested dict and list"),
    pytest.param({"a": ("released",)}, id="tuple"),
    pytest.param({"a": {"released"}}, id="set"),
    pytest.param({"a": [[[{"b": " released "}]]]}, id="deep and padded"),
]


@pytest.mark.parametrize("params", NESTED_RELEASED)
def test_released_is_refused_at_any_depth_on_the_write_function(
    params: dict[str, Any], settings: SiteSettings
) -> None:
    transport = FakeTransport()
    values = {**VALID_WRITE, **params}
    with pytest.raises(WorkflowStateNotAllowed, match="never releases grades"):
        MoodleClient(settings, transport).call(SAVE_GRADE, values)
    assert transport.calls == []


def test_set_user_flags_is_refused_even_if_an_allow_list_lists_it(
    settings: SiteSettings,
) -> None:
    """Guide's B4 findings (PR #64): removed from B4. The client refuses it by name, even with
    an allow-list that lists it, as this branch's contract file still does before the rebase onto
    #64. The test builds that list itself, so it passes on either base."""
    base = load_allowlist()
    listed = AllowList(
        MappingProxyType({**base.functions, SET_USER_FLAGS: MappingProxyType({})}),
        base.moodle_versions,
    )
    transport = FakeTransport()
    with pytest.raises(FunctionNotAllowed):
        MoodleClient(settings, transport, listed).call(
            SET_USER_FLAGS, {"workflowstate": "readyforrelease"}
        )
    assert transport.calls == []


def test_set_user_flags_is_refused_by_the_contract_allow_list(
    settings: SiteSettings,
) -> None:
    """Guide's B4 findings (PR #64): mod_assign_set_user_flags is no longer in B4."""
    transport = FakeTransport()
    with pytest.raises(FunctionNotAllowed):
        MoodleClient(settings, transport).call(
            SET_USER_FLAGS, {"workflowstate": "readyforrelease"}
        )
    assert transport.calls == []


def test_a_structure_that_contains_itself_does_not_hang(
    settings: SiteSettings,
) -> None:
    looped: list[Any] = ["x"]
    looped.append(looped)
    transport = FakeTransport()
    with pytest.raises(InvalidParameters):
        MoodleClient(settings, transport).call(SAVE_GRADE, {"a": looped})
    assert transport.calls == []


def test_read_functions_are_not_touched_by_the_draft_rule(
    settings: SiteSettings,
) -> None:
    transport = FakeTransport()
    MoodleClient(settings, transport).call(
        "mod_assign_get_assignments", {"note": "released"}
    )
    assert len(transport.calls) == 1


def test_the_answer_is_returned_unchanged(settings: SiteSettings) -> None:
    answer = {"opaque": ["value"]}
    client = MoodleClient(settings, FakeTransport(answer=answer))
    assert client.call("core_course_get_contents") is answer


def test_the_caller_cannot_change_what_was_sent(settings: SiteSettings) -> None:
    transport = FakeTransport()
    params = dict(VALID_WRITE)
    send_checked(MoodleClient(settings, transport), params)
    params["workflowstate"] = "released"
    assert transport.calls[0][1] == VALID_WRITE


def test_a_transport_cannot_change_the_callers_parameters(
    settings: SiteSettings,
) -> None:
    class ChangingTransport(FakeTransport):
        def call(
            self, settings: SiteSettings, function: str, params: Mapping[str, Any]
        ) -> Any:
            cast(dict[str, Any], params)["added"] = "by the transport"

    params = {"note": "kept"}
    MoodleClient(settings, ChangingTransport()).call("core_course_get_contents", params)
    assert params == {"note": "kept"}


def test_a_refused_call_never_reaches_the_transport(settings: SiteSettings) -> None:
    transport = FakeTransport()
    client = MoodleClient(settings, transport)
    with pytest.raises(FunctionNotAllowed):
        client.call("core_user_get_users")
    only_53 = AllowList(load_allowlist().functions, frozenset({"5.3"}))
    with pytest.raises(NotSupported):
        MoodleClient(settings, transport, only_53).call("core_course_get_contents")
    assert transport.calls == []


class CustomError(MoodleError):
    """A transport's own class, whose constructor does not take one message."""

    code = "custom_transport_error"

    def __init__(self, first: str, second: str) -> None:
        super().__init__(first, second)
        self.raw = second


@pytest.mark.parametrize(
    "error",
    [
        MoodleUnreachable,
        TokenInvalid,
        PermissionDenied,
        UnexpectedResponse,
        NotSupported,
    ],
)
def test_a_known_error_keeps_its_class_with_a_fixed_message(
    error: type[MoodleError], settings: SiteSettings
) -> None:
    raw = f"failed {FAKE_TOKEN} at https://site.invalid/path with secret-parameter"
    transport = FakeTransport(failure=error(raw))
    with pytest.raises(error) as caught:
        MoodleClient(settings, transport).call("core_course_get_contents")
    assert type(caught.value) is error
    assert caught.value.code == error.code
    assert "moodle45" in str(caught.value)
    for hidden in (FAKE_TOKEN, "/path", "secret-parameter"):
        assert hidden not in str(caught.value)
        assert hidden not in repr(caught.value)
    assert caught.value.__cause__ is None
    assert caught.value.__context__ is None


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (MoodleUnreachable, "did not answer"),
        (TokenInvalid, "rejected the service token"),
        (PermissionDenied, "cannot do this"),
        (NotSupported, "does not support this"),
        (UnexpectedResponse, "could not be understood"),
    ],
)
def test_each_error_class_has_its_own_fixed_message(
    error: type[MoodleError], expected: str, settings: SiteSettings
) -> None:
    transport = FakeTransport(failure=error("raw"))
    with pytest.raises(error, match=expected):
        MoodleClient(settings, transport).call("core_course_get_contents")


def test_a_replacement_name_is_what_the_transport_receives(
    settings: SiteSettings,
) -> None:
    allowlist = AllowList(
        MappingProxyType({"mod_example_old": {"5.3": "mod_example_new"}}),
        frozenset({"4.5", "5.3"}),
    )
    transport = FakeTransport()
    site = replace(settings, site=Site.MOODLE53, moodle_version="5.3")
    MoodleClient(site, transport, allowlist).call("mod_example_old")
    assert transport.calls == [("mod_example_new", {})]


def test_a_custom_error_class_is_kept_without_its_raw_values(
    settings: SiteSettings,
) -> None:
    transport = FakeTransport(failure=CustomError("one", FAKE_TOKEN))
    with pytest.raises(CustomError) as caught:
        MoodleClient(settings, transport).call("core_course_get_contents")
    assert not hasattr(caught.value, "raw")
    assert FAKE_TOKEN not in repr(caught.value)
    assert caught.value.__context__ is None


def test_a_test_cannot_open_a_network_connection() -> None:
    with pytest.raises(AssertionError, match="tried to open a socket"):
        socket.socket()


def test_there_is_no_real_transport_yet() -> None:
    with pytest.raises(NotSupported, match="No real Moodle transport"):
        create_client(Site.MOODLE45)


def test_create_client_builds_a_working_client_from_the_environment() -> None:
    environ = {
        "MOODLE53_URL": "https://site.invalid",
        "MOODLE53_WS_TOKEN": "made-up-value",
    }
    transport = FakeTransport()
    client = create_client("moodle53", transport, environ)
    assert client.call("core_course_get_contents") == "scripted answer"
