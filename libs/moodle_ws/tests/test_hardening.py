"""Regressions for the audit fixes: unusual values, hand-built settings and log records.

Every refusal must happen before the transport is touched, and nothing in the error, its repr, its
traceback or a log record may show the fake token.
"""

from __future__ import annotations

import logging
import traceback
from dataclasses import replace
from typing import Any

import pytest

from moodle_ws import (
    MoodleConfigError,
    RedactingFilter,
    Site,
    SiteSettings,
    Token,
    load_site,
    sanitize_value,
)
from moodle_ws.messages import LOG_NOT_CLEANED

from .conftest import FAKE_TOKEN, FAKE_URL

LIMIT = 32


def visible(error: BaseException) -> str:
    return " ".join((str(error), repr(error), *traceback.format_exception(error)))


def nested(levels: int, kind: type = dict) -> Any:
    """`levels` containers, one inside the other."""
    value: Any = "leaf"
    for _ in range(levels):
        value = {"a": value} if kind is dict else [value]
    return value


class TextSubclass(str):
    pass


class DictSubclass(dict[str, Any]):
    pass


class HoldsToken:
    def __str__(self) -> str:
        return FAKE_TOKEN


# Unusual values, on every kind of function


# Parameters must be a mapping


# Nested values are private to the transport


# The depth limit, at its boundary


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
