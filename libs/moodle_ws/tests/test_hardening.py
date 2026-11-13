"""Regressions for the audit fixes: unusual values, hand-built settings and log records.

Every refusal must happen before the transport is touched, and nothing in the error, its repr, its
traceback or a log record may show the fake token.
"""

from __future__ import annotations

import logging
import traceback
from collections.abc import Iterator, Mapping
from dataclasses import replace
from typing import Any

import pytest

from moodle_ws import (
    InvalidParameters,
    MoodleClient,
    MoodleConfigError,
    MoodleError,
    RedactingFilter,
    Site,
    SiteSettings,
    Token,
    WorkflowStateNotAllowed,
    load_site,
    sanitize_value,
)
from moodle_ws.messages import INVALID_PARAMETERS, LOG_NOT_CLEANED

from .conftest import FAKE_TOKEN, FAKE_URL
from .fake_transport import FakeTransport

READ = "core_course_get_contents"
SAVE_GRADE = "mod_assign_save_grade"
LIMIT = 32


def visible(error: BaseException) -> str:
    return " ".join((str(error), repr(error), *traceback.format_exception(error)))


def nested(levels: int, kind: type = dict) -> Any:
    """`levels` containers, one inside the other."""
    value: Any = "leaf"
    for _ in range(levels):
        value = {"a": value} if kind is dict else [value]
    return value


class PrintsReleased:
    def __str__(self) -> str:
        return "released"

    __repr__ = __str__

    def __eq__(self, other: object) -> bool:
        return True

    def __hash__(self) -> int:
        return 1


class TextSubclass(str):
    pass


class DictSubclass(dict[str, Any]):
    pass


class ListSubclass(list[Any]):
    pass


class HoldsToken:
    def __str__(self) -> str:
        return FAKE_TOKEN


class CopyRunsCode:
    def __deepcopy__(self, memo: dict[int, Any]) -> str:
        raise AssertionError("copying must not run an object's own code")


class ChangesBetweenReads(Mapping[str, Any]):
    """A grade write whose key "a" shows a safe value on the first read and `released`
    afterwards."""

    def __init__(self) -> None:
        self.reads = 0

    def __getitem__(self, key: str) -> str:
        if key == "workflowstate":
            return "readyforrelease"
        self.reads += 1
        return "safe" if self.reads == 1 else "released"

    def __iter__(self) -> Iterator[str]:
        return iter(["workflowstate", "a"])

    def __len__(self) -> int:
        return 2


class FailsWhenRead(Mapping[str, Any]):
    def __getitem__(self, key: str) -> str:
        raise ValueError(FAKE_TOKEN)

    def __iter__(self) -> Iterator[str]:
        return iter(["a"])

    def __len__(self) -> int:
        return 1


# Unusual values, on every kind of function


UNSUPPORTED = [
    pytest.param(b"released", id="bytes"),
    pytest.param(bytearray(b"released"), id="bytearray"),
    pytest.param(PrintsReleased(), id="object printing released"),
    pytest.param((item for item in ["released"]), id="generator"),
    pytest.param(iter(["released"]), id="iterator"),
    pytest.param(TextSubclass("released"), id="str subclass"),
    pytest.param(DictSubclass(a="released"), id="dict subclass"),
    pytest.param(ListSubclass(["released"]), id="list subclass"),
    pytest.param(HoldsToken(), id="object holding the token"),
    pytest.param(CopyRunsCode(), id="object with its own deepcopy"),
    pytest.param(object(), id="plain object"),
    pytest.param(lambda: "released", id="function"),
    pytest.param(memoryview(b"released"), id="memoryview"),
]


@pytest.mark.parametrize("value", UNSUPPORTED)
@pytest.mark.parametrize("function", [READ, SAVE_GRADE])
def test_an_unusual_value_is_refused_on_every_function(
    function: str, value: Any, settings: SiteSettings
) -> None:
    transport = FakeTransport()
    params = {"workflowstate": "readyforrelease", "a": value}
    with pytest.raises(InvalidParameters) as caught:
        MoodleClient(settings, transport).call(function, params)
    assert transport.calls == []
    assert str(caught.value) == INVALID_PARAMETERS
    assert FAKE_TOKEN not in visible(caught.value)


@pytest.mark.parametrize(
    "wrap",
    [
        lambda v: {"a": {"b": v}},
        lambda v: {"a": [v]},
        lambda v: {"a": (v,)},
    ],
    ids=["in a dict", "in a list", "in a tuple"],
)
def test_an_unusual_value_is_refused_when_nested(
    wrap: Any, settings: SiteSettings
) -> None:
    transport = FakeTransport()
    with pytest.raises(InvalidParameters):
        MoodleClient(settings, transport).call(READ, wrap(b"released"))
    assert transport.calls == []


@pytest.mark.parametrize("key", [PrintsReleased(), b"released", (1, 2), None, 1.5])
def test_an_unusual_key_is_refused(key: Any, settings: SiteSettings) -> None:
    transport = FakeTransport()
    with pytest.raises(InvalidParameters):
        MoodleClient(settings, transport).call(READ, {"a": {key: 1}})
    assert transport.calls == []


@pytest.mark.parametrize(
    "params",
    [
        {"released": 1},
        {"a": {"RELEASED": 1}},
        {"a": [{" released ": 1}]},
    ],
)
def test_a_key_named_released_is_refused_on_the_write_function(
    params: dict[str, Any], settings: SiteSettings
) -> None:
    transport = FakeTransport()
    values = {"workflowstate": "readyforrelease", **params}
    with pytest.raises(WorkflowStateNotAllowed):
        MoodleClient(settings, transport).call(SAVE_GRADE, values)
    assert transport.calls == []


def test_read_functions_may_use_the_word_as_a_key(settings: SiteSettings) -> None:
    transport = FakeTransport()
    MoodleClient(settings, transport).call(READ, {"released": "released"})
    assert len(transport.calls) == 1


def test_plain_values_all_reach_the_transport(settings: SiteSettings) -> None:
    params = {
        "text": "x",
        "number": 1,
        "fraction": 1.5,
        "flag": True,
        "nothing": None,
        "list": [1, "a"],
        "tuple": (1,),
        "set": {1},
        "frozenset": frozenset({1}),
        "dict": {"a": 1, 2: "b"},
    }
    transport = FakeTransport()
    MoodleClient(settings, transport).call(READ, params)
    assert transport.calls == [(READ, params)]


# Parameters must be a mapping


@pytest.mark.parametrize("params", ["abc", 5, [("a", 1)], b"x", ("a",), object()])
def test_params_that_are_not_a_mapping_are_refused(
    params: Any, settings: SiteSettings
) -> None:
    transport = FakeTransport()
    with pytest.raises(InvalidParameters) as caught:
        MoodleClient(settings, transport).call(READ, params)
    assert isinstance(caught.value, MoodleError)
    assert caught.value.retryable is False
    assert transport.calls == []


def test_an_object_that_only_looks_like_a_mapping_is_refused(
    settings: SiteSettings,
) -> None:
    class HasItems:
        def items(self) -> list[tuple[str, str]]:
            return [("a", "b")]

    transport = FakeTransport()
    with pytest.raises(InvalidParameters):
        MoodleClient(settings, transport).call(READ, HasItems())  # type: ignore[arg-type]
    assert transport.calls == []


def test_a_mapping_that_fails_when_read_is_refused_safely(
    settings: SiteSettings,
) -> None:
    transport = FakeTransport()
    with pytest.raises(InvalidParameters) as caught:
        MoodleClient(settings, transport).call(READ, FailsWhenRead())
    assert caught.value.__context__ is None
    assert caught.value.__cause__ is None
    assert FAKE_TOKEN not in visible(caught.value)
    assert transport.calls == []


def test_a_mapping_is_read_once_so_it_cannot_change_after_the_check(
    settings: SiteSettings,
) -> None:
    transport = FakeTransport()
    MoodleClient(settings, transport).call(SAVE_GRADE, ChangesBetweenReads())
    assert transport.calls == [
        (SAVE_GRADE, {"workflowstate": "readyforrelease", "a": "safe"})
    ]


def test_no_params_means_an_empty_mapping(settings: SiteSettings) -> None:
    transport = FakeTransport()
    MoodleClient(settings, transport).call(READ)
    assert transport.calls == [(READ, {})]


# Nested values are private to the transport


class ChangingTransport(FakeTransport):
    def call(
        self, settings: SiteSettings, function: str, params: Mapping[str, Any]
    ) -> Any:
        params["nested"]["key"] = "changed"
        params["items"].append("changed")
        params["sets"].add("changed")
        params["deep"][0]["key"] = "changed"
        return None


def test_a_transport_cannot_change_nested_values(settings: SiteSettings) -> None:
    params = {
        "nested": {"key": "kept"},
        "items": ["kept"],
        "sets": {"kept"},
        "deep": ({"key": "kept"},),
    }
    MoodleClient(settings, ChangingTransport()).call(READ, params)
    assert params == {
        "nested": {"key": "kept"},
        "items": ["kept"],
        "sets": {"kept"},
        "deep": ({"key": "kept"},),
    }


def test_the_caller_cannot_change_what_the_transport_kept(
    settings: SiteSettings,
) -> None:
    held = ["readyforrelease"]
    transport = FakeTransport()
    MoodleClient(settings, transport).call(READ, {"held": held})
    held.append("released")
    assert transport.calls[0][1] == {"held": ["readyforrelease"]}


# The depth limit, at its boundary


@pytest.mark.parametrize("kind", [dict, list])
def test_the_deepest_allowed_nesting_is_accepted(
    kind: type, settings: SiteSettings
) -> None:
    transport = FakeTransport()
    params = {"a": nested(LIMIT - 1, kind)}  # the top mapping is level 1
    MoodleClient(settings, transport).call(READ, params)
    assert transport.calls == [(READ, params)]


@pytest.mark.parametrize("levels", [LIMIT, 3000])
@pytest.mark.parametrize("kind", [dict, list])
def test_nesting_past_the_limit_is_refused(
    levels: int, kind: type, settings: SiteSettings
) -> None:
    transport = FakeTransport()
    with pytest.raises(InvalidParameters):
        MoodleClient(settings, transport).call(READ, {"a": nested(levels, kind)})
    assert transport.calls == []


def test_released_at_the_deepest_level_is_found(settings: SiteSettings) -> None:
    value: Any = "released"
    for _ in range(LIMIT - 1):
        value = [value]
    transport = FakeTransport()
    with pytest.raises(WorkflowStateNotAllowed):
        MoodleClient(settings, transport).call(SAVE_GRADE, {"a": value})
    assert transport.calls == []


def test_the_same_object_twice_is_not_a_loop(settings: SiteSettings) -> None:
    shared = ["x"]
    transport = FakeTransport()
    MoodleClient(settings, transport).call(READ, {"a": shared, "b": shared})
    assert transport.calls == [(READ, {"a": ["x"], "b": ["x"]})]


# Site settings built by hand


def test_good_settings_are_accepted(settings: SiteSettings) -> None:
    assert settings.site is Site.MOODLE45


@pytest.mark.parametrize(
    "site", ["moodle45", "moodle99", None, 45, FAKE_TOKEN], ids=repr
)
def test_a_site_that_is_not_a_site_is_refused(site: Any) -> None:
    with pytest.raises(MoodleConfigError, match="'site'") as caught:
        SiteSettings(site, "4.5", FAKE_URL, Token(FAKE_TOKEN))
    assert FAKE_TOKEN not in visible(caught.value)


@pytest.mark.parametrize(
    ("site", "version"),
    [
        (Site.MOODLE45, "5.3"),
        (Site.MOODLE53, "4.5"),
        (Site.MOODLE45, "5.0"),
        (Site.MOODLE45, ""),
        (Site.MOODLE45, 4.5),
    ],
)
def test_a_version_that_does_not_match_the_site_is_refused(
    site: Site, version: Any
) -> None:
    with pytest.raises(MoodleConfigError, match="'moodle_version'"):
        SiteSettings(site, version, FAKE_URL, Token(FAKE_TOKEN))


@pytest.mark.parametrize(
    "token",
    [Token(""), Token("   "), Token("CHANGE_ME"), FAKE_TOKEN, None],
    ids=["empty", "blank", "placeholder", "plain text", "none"],
)
def test_a_bad_token_is_refused(token: Any) -> None:
    with pytest.raises(MoodleConfigError, match="'token'") as caught:
        SiteSettings(Site.MOODLE45, "4.5", FAKE_URL, token)
    assert FAKE_TOKEN not in visible(caught.value)


BAD_URLS = [
    pytest.param(f"https://user:{FAKE_TOKEN}@site.invalid", id="user and password"),
    pytest.param(f"https://{FAKE_TOKEN}@site.invalid", id="user only"),
    pytest.param(f"https://site.invalid/a?x={FAKE_TOKEN}", id="query"),
    pytest.param("https://site.invalid/?", id="empty query"),
    pytest.param(f"https://site.invalid/a#{FAKE_TOKEN}", id="fragment"),
    pytest.param("https://site.invalid/#", id="empty fragment"),
    pytest.param("https://site .invalid", id="space"),
    pytest.param("https://site.invalid/a\n", id="trailing newline"),
    pytest.param("\thttps://site.invalid", id="tab"),
    pytest.param("https://", id="missing host"),
    pytest.param("https:///path", id="missing host with a path"),
    pytest.param("site.invalid", id="no scheme"),
    pytest.param("ftp://site.invalid", id="other scheme"),
    pytest.param("https://[bad", id="malformed host"),
    pytest.param("https://site.invalid:99999", id="malformed port"),
    pytest.param("", id="empty"),
    pytest.param(None, id="none"),
]


@pytest.mark.parametrize("url", BAD_URLS)
def test_a_bad_url_is_refused_without_being_repeated(url: Any) -> None:
    with pytest.raises(MoodleConfigError, match="'url'") as caught:
        SiteSettings(Site.MOODLE45, "4.5", url, Token("different"))
    assert FAKE_TOKEN not in visible(caught.value)


@pytest.mark.parametrize(
    "url",
    ["https://site.invalid", "http://site.invalid:8080", "https://site.invalid/moodle"],
)
def test_a_plain_site_address_is_accepted(url: str) -> None:
    assert SiteSettings(Site.MOODLE45, "4.5", url, Token(FAKE_TOKEN)).url == url


def test_load_site_applies_the_same_url_rule() -> None:
    environ = {
        "MOODLE45_URL": f"https://user:{FAKE_TOKEN}@site.invalid",
        "MOODLE45_WS_TOKEN": "made-up",
    }
    with pytest.raises(MoodleConfigError, match="'url'") as caught:
        load_site(Site.MOODLE45, environ)
    assert FAKE_TOKEN not in visible(caught.value)


def test_replace_cannot_skip_the_checks(settings: SiteSettings) -> None:
    with pytest.raises(MoodleConfigError):
        replace(settings, moodle_version="5.3")


def test_repr_shows_neither_the_url_nor_the_token(settings: SiteSettings) -> None:
    for text in (repr(settings), str(settings), f"{settings}"):
        assert FAKE_URL not in text
        assert FAKE_TOKEN not in text
    assert "moodle45" in repr(settings)


# The client constructor


@pytest.mark.parametrize("site", ["moodle45", Site.MOODLE45, None, 1])
def test_a_client_without_settings_is_refused_when_built(site: Any) -> None:
    with pytest.raises(MoodleConfigError, match="needs site settings"):
        MoodleClient(site, FakeTransport())


@pytest.mark.parametrize("transport", [None, "transport", object(), 1])
def test_a_client_without_a_transport_is_refused_when_built(
    transport: Any, settings: SiteSettings
) -> None:
    with pytest.raises(MoodleConfigError, match="needs a transport"):
        MoodleClient(settings, transport)


def test_a_transport_whose_call_is_not_callable_is_refused(
    settings: SiteSettings,
) -> None:
    class NotCallable:
        call = "not a method"

    with pytest.raises(MoodleConfigError, match="needs a transport"):
        MoodleClient(settings, NotCallable())  # type: ignore[arg-type]


@pytest.mark.parametrize("allowlist", [{}, [], "all", object()])
def test_a_bad_allowlist_is_refused_when_built(
    allowlist: Any, settings: SiteSettings
) -> None:
    with pytest.raises(MoodleConfigError, match="needs an AllowList"):
        MoodleClient(settings, FakeTransport(), allowlist)


# Sanitizing and logging


TOKENS = [Token(FAKE_TOKEN)]


def test_a_frozenset_stays_hashable_inside_a_set() -> None:
    cleaned = sanitize_value({frozenset({FAKE_TOKEN})}, TOKENS)
    assert cleaned == {frozenset({"***"})}


def test_a_frozenset_can_be_a_dict_key() -> None:
    assert sanitize_value({frozenset({"a"}): 1}, TOKENS) == {frozenset({"a"}): 1}


@pytest.mark.parametrize(
    "value",
    [
        b"bytes " + FAKE_TOKEN.encode(),
        bytearray(FAKE_TOKEN.encode()),
        HoldsToken(),
        ValueError(FAKE_TOKEN),
        TextSubclass(FAKE_TOKEN),
        DictSubclass(a=FAKE_TOKEN),
    ],
    ids=["bytes", "bytearray", "object", "exception", "str subclass", "dict subclass"],
)
def test_a_value_that_cannot_be_checked_is_masked(value: Any) -> None:
    assert sanitize_value(value, TOKENS) == "***"
    assert sanitize_value({"a": [value]}, TOKENS) == {"a": ["***"]}


def test_a_subclass_of_text_is_masked_even_when_it_looks_harmless() -> None:
    assert sanitize_value(TextSubclass("plain words"), TOKENS) == "***"


@pytest.mark.parametrize("value", [1, 1.5, True, None])
def test_plain_numbers_are_kept(value: Any) -> None:
    assert sanitize_value(value, TOKENS) is value


def test_sanitizing_stops_at_the_depth_limit() -> None:
    allowed = sanitize_value(nested(LIMIT, list), TOKENS)
    for _ in range(LIMIT):
        allowed = allowed[0]
    assert allowed == "leaf"

    masked = sanitize_value(nested(LIMIT + 1, list), TOKENS)
    for _ in range(LIMIT):
        masked = masked[0]
    assert masked == "***"


@pytest.mark.parametrize("kind", [dict, list])
def test_very_deep_data_does_not_crash_sanitizing(kind: type) -> None:
    value = nested(3000, kind)
    value = {"token": FAKE_TOKEN, "deep": value}
    assert FAKE_TOKEN not in repr(sanitize_value(value, TOKENS))


def record_with(**extra: Any) -> logging.LogRecord:
    record = logging.LogRecord("n", logging.INFO, "file", 1, "message", None, None)
    record.__dict__.update(extra)
    return record


def test_the_filter_handles_a_frozenset_inside_a_set() -> None:
    record = record_with(values={frozenset({FAKE_TOKEN})})
    assert RedactingFilter(TOKENS).filter(record) is True
    assert FAKE_TOKEN not in repr(vars(record))


def test_the_filter_handles_very_deep_extra_fields() -> None:
    record = record_with(deep=nested(3000))
    assert RedactingFilter(TOKENS).filter(record) is True


def test_the_filter_masks_an_exception_in_extra_fields() -> None:
    record = record_with(failure=ValueError(FAKE_TOKEN))
    RedactingFilter(TOKENS).filter(record)
    assert record.__dict__["failure"] == "***"


def test_the_filter_does_not_repeat_arguments_that_do_not_fit() -> None:
    record = logging.LogRecord(
        "n", logging.INFO, "file", 1, "%s %s", (FAKE_TOKEN,), None
    )
    RedactingFilter(TOKENS).filter(record)
    assert FAKE_TOKEN not in str(record.msg)
    assert record.args is None


def test_the_filter_drops_arguments_that_do_not_fit() -> None:
    record = logging.LogRecord(
        "n", logging.INFO, "file", 1, "%s %s", ("learner parameter",), None
    )
    RedactingFilter(TOKENS).filter(record)
    assert "learner parameter" not in str(record.msg)


class Unprintable:
    def __str__(self) -> str:
        raise RuntimeError(FAKE_TOKEN)


def test_a_record_that_cannot_be_cleaned_is_replaced_and_never_raises() -> None:
    record = logging.LogRecord("n", logging.INFO, "file", 1, Unprintable(), None, None)
    record.__dict__["secret_field"] = FAKE_TOKEN
    record.exc_text = FAKE_TOKEN
    record.stack_info = FAKE_TOKEN
    assert RedactingFilter(TOKENS).filter(record) is True
    assert record.msg == LOG_NOT_CLEANED
    assert record.args is None
    assert record.exc_text is None
    assert record.stack_info is None
    assert "secret_field" not in vars(record)
    assert FAKE_TOKEN not in repr(vars(record))


def test_a_discarded_record_can_still_be_written() -> None:
    record = logging.LogRecord("n", logging.INFO, "file", 1, Unprintable(), None, None)
    RedactingFilter(TOKENS).filter(record)
    assert logging.Formatter().format(record) == LOG_NOT_CLEANED
