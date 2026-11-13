"""Tokens and full URLs stay out of logs and errors (PRD SEC-03, C-06, OPS-04; design §4.1)."""

from __future__ import annotations

import copy
import logging
import pickle
import traceback
from collections.abc import Iterator
from dataclasses import asdict
from typing import Any

import pytest

from moodle_ws import (
    MoodleClient,
    MoodleError,
    MoodleUnreachable,
    RedactingFilter,
    SiteSettings,
    Token,
    TokenInvalid,
    UnexpectedResponse,
    redact,
    safe_url,
    sanitize,
    sanitize_value,
)

from .conftest import FAKE_TOKEN
from .fake_transport import FakeTransport

FUNCTION = "core_course_get_contents"
URL_WITH_TOKEN = f"https://site.invalid/some/path?key={FAKE_TOKEN}"
LEARNER_DATA = "made-up-learner-data"


def formatted(error: BaseException) -> str:
    return "".join(traceback.format_exception(error))


def test_a_token_never_prints_its_value() -> None:
    token = Token(FAKE_TOKEN)
    for text in (
        repr(token),
        str(token),
        f"{token}",
        f"{token!r}",
        f"{token:>40}",
        "%s" % token,
    ):
        assert FAKE_TOKEN not in text


@pytest.mark.parametrize(
    "text",
    [
        ascii(Token(FAKE_TOKEN)),
        "%r" % Token(FAKE_TOKEN),
        "{}".format(Token(FAKE_TOKEN)),
        "{!r}".format(Token(FAKE_TOKEN)),
        "{!s}".format(Token(FAKE_TOKEN)),
        format(Token(FAKE_TOKEN), ">30"),
    ],
)
def test_no_formatting_style_shows_the_value(text: str) -> None:
    assert FAKE_TOKEN not in text


def test_only_reveal_returns_the_value() -> None:
    assert Token(FAKE_TOKEN).reveal() == FAKE_TOKEN


def test_a_token_has_no_readable_attribute_dictionary() -> None:
    assert not hasattr(Token(FAKE_TOKEN), "__dict__")


def test_a_token_cannot_be_pickled(settings: SiteSettings) -> None:
    with pytest.raises(TypeError, match="cannot be pickled"):
        pickle.dumps(Token(FAKE_TOKEN))
    with pytest.raises(TypeError, match="cannot be pickled"):
        pickle.dumps(settings)


def test_a_copy_of_settings_keeps_the_token_masked(settings: SiteSettings) -> None:
    assert copy.deepcopy(settings).token.reveal() == FAKE_TOKEN
    assert copy.copy(settings.token).reveal() == FAKE_TOKEN
    assert FAKE_TOKEN not in repr(asdict(settings))


def test_printed_settings_never_show_the_token(settings: SiteSettings) -> None:
    assert FAKE_TOKEN not in repr(settings)
    assert FAKE_TOKEN not in str(settings)


def test_a_client_never_shows_the_token(settings: SiteSettings) -> None:
    assert FAKE_TOKEN not in repr(MoodleClient(settings, FakeTransport()))


def test_redact_replaces_every_occurrence() -> None:
    text = redact(f"{FAKE_TOKEN} and {FAKE_TOKEN}", [Token(FAKE_TOKEN)])
    assert text == "*** and ***"


def test_redact_covers_a_percent_encoded_token() -> None:
    assert redact("key=a%2Fb", [Token("a/b")]) == "key=***"


def test_sanitize_cuts_every_url_and_keeps_the_words_around_it() -> None:
    text = sanitize(f"first {URL_WITH_TOKEN} then HTTP://Other.invalid/x?y=1 end", [])
    assert text == "first https://site.invalid then http://other.invalid end"


def test_an_empty_token_changes_nothing() -> None:
    assert redact("plain text", [Token("")]) == "plain text"


def test_a_token_inside_a_longer_one_leaves_nothing_visible() -> None:
    short, long = "abc123", "abc123XYZ789"
    assert redact(long, [Token(short), Token(long)]) == "***"
    assert redact(long, [Token(long), Token(short)]) == "***"


def test_sanitize_value_cleans_every_level() -> None:
    value = {
        "url": URL_WITH_TOKEN,
        FAKE_TOKEN: [FAKE_TOKEN, (FAKE_TOKEN,), {"deep": {FAKE_TOKEN}}],
        "count": 3,
    }
    cleaned = sanitize_value(value, [Token(FAKE_TOKEN)])
    assert cleaned == {
        "url": "https://site.invalid",
        "***": ["***", ("***",), {"deep": {"***"}}],
        "count": 3,
    }


def test_sanitize_value_masks_other_objects() -> None:
    assert sanitize_value(object(), [Token(FAKE_TOKEN)]) == "***"


def test_sanitize_value_masks_a_structure_that_contains_itself() -> None:
    looped: list[Any] = [FAKE_TOKEN]
    looped.append(looped)
    assert sanitize_value(looped, [Token(FAKE_TOKEN)]) == ["***", "***"]


def test_redact_covers_every_token() -> None:
    assert redact("one two", [Token("one"), Token("two")]) == "*** ***"


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (URL_WITH_TOKEN, "https://site.invalid"),
        (f"https://user:{FAKE_TOKEN}@site.invalid/a#b", "https://site.invalid"),
        (f"not a url {FAKE_TOKEN}", "***"),
        ("", "***"),
        ("HTTPS://Site.Invalid:8443/a", "https://site.invalid"),
        ("https://[::1]:8443/a?b=c", "https://[::1]"),
        ("https://[bad/a", "***"),
        ("site.invalid/a?b=c", "***"),
        (f"//user:{FAKE_TOKEN}@site.invalid/a", "***"),
        (f"mailto:{FAKE_TOKEN}@site.invalid", "***"),
    ],
)
def test_safe_url_keeps_only_scheme_and_host(url: str, expected: str) -> None:
    assert safe_url(url) == expected


def test_a_transport_error_is_redacted(settings: SiteSettings) -> None:
    transport = FakeTransport(failure=TokenInvalid(f"rejected {FAKE_TOKEN}"))
    with pytest.raises(TokenInvalid) as caught:
        MoodleClient(settings, transport).call(FUNCTION)
    assert FAKE_TOKEN not in str(caught.value)


@pytest.mark.parametrize(
    ("failure", "expected"),
    [
        (OSError(URL_WITH_TOKEN), MoodleUnreachable),
        (TimeoutError(URL_WITH_TOKEN), MoodleUnreachable),
        (ValueError(URL_WITH_TOKEN), UnexpectedResponse),
        (TokenInvalid(URL_WITH_TOKEN), TokenInvalid),
    ],
)
def test_no_failure_keeps_the_original_exception(
    failure: Exception, expected: type[MoodleError], settings: SiteSettings
) -> None:
    with pytest.raises(expected) as caught:
        MoodleClient(settings, FakeTransport(failure=failure)).call(FUNCTION)
    error = caught.value
    assert error.__cause__ is None
    assert error.__context__ is None
    for text in (str(error), repr(error), formatted(error)):
        assert FAKE_TOKEN not in text
        assert "/some/path" not in text


def test_no_traceback_frame_holds_the_original_exception(
    settings: SiteSettings,
) -> None:
    failure = OSError(URL_WITH_TOKEN)
    with pytest.raises(MoodleUnreachable) as caught:
        MoodleClient(settings, FakeTransport(failure=failure)).call(FUNCTION)
    tb = caught.value.__traceback__
    frames = 0
    while tb is not None:
        if tb.tb_frame.f_code.co_filename.endswith("client.py"):
            frames += 1
            assert failure not in tb.tb_frame.f_locals.values()
        tb = tb.tb_next
    # call() delegates to _send(); every client frame is checked, however many there are.
    assert frames >= 1


def test_a_public_error_logged_without_a_filter_shows_no_token(
    settings: SiteSettings, caplog: pytest.LogCaptureFixture
) -> None:
    log = logging.getLogger("moodle_ws.tests.plain")
    with pytest.raises(TokenInvalid) as caught:
        MoodleClient(
            settings, FakeTransport(failure=TokenInvalid(URL_WITH_TOKEN))
        ).call(FUNCTION)
    log.error("call failed: %s", caught.value, exc_info=caught.value)
    assert "call failed" in caplog.text
    assert FAKE_TOKEN not in caplog.text
    assert "/some/path" not in caplog.text


def test_an_error_never_shows_the_parameters(settings: SiteSettings) -> None:
    transport = FakeTransport(failure=OSError("down"))
    with pytest.raises(MoodleUnreachable) as caught:
        MoodleClient(settings, transport).call(FUNCTION, {"learner": LEARNER_DATA})
    assert LEARNER_DATA not in formatted(caught.value)


@pytest.fixture
def logger(caplog: pytest.LogCaptureFixture) -> Iterator[logging.Logger]:
    """The filter is removed afterwards: caplog's handler is shared between tests, and a second
    filter would clean what a broken first one missed."""
    log = logging.getLogger("moodle_ws.tests")
    redacting = RedactingFilter([Token(FAKE_TOKEN)])
    caplog.handler.addFilter(redacting)
    caplog.set_level(logging.INFO, logger=log.name)
    yield log
    caplog.handler.removeFilter(redacting)


def test_the_filter_cleans_a_message_and_its_arguments(
    logger: logging.Logger, caplog: pytest.LogCaptureFixture
) -> None:
    logger.info("calling %s with %s", URL_WITH_TOKEN, {"key": FAKE_TOKEN})
    assert FAKE_TOKEN not in caplog.text
    assert "/some/path" not in caplog.text
    assert "calling https://site.invalid with" in caplog.text


def test_the_filter_cleans_a_logged_exception(
    logger: logging.Logger, caplog: pytest.LogCaptureFixture
) -> None:
    try:
        raise ValueError(URL_WITH_TOKEN)
    except ValueError:
        logger.exception("failed")
    assert FAKE_TOKEN not in caplog.text
    assert "/some/path" not in caplog.text
    assert "ValueError: https://site.invalid" in caplog.text
    assert caplog.records[-1].exc_info is None


def test_the_filter_survives_arguments_that_do_not_fit(
    logger: logging.Logger, caplog: pytest.LogCaptureFixture
) -> None:
    logger.info("only one %s", URL_WITH_TOKEN, FAKE_TOKEN)
    assert FAKE_TOKEN not in caplog.text
    assert "/some/path" not in caplog.text
    assert "only one" in caplog.text


def test_the_filter_cleans_extra_fields_used_by_structured_logs(
    logger: logging.Logger, caplog: pytest.LogCaptureFixture
) -> None:
    logger.info(
        "call",
        extra={
            "request_url": URL_WITH_TOKEN,
            "note": FAKE_TOKEN,
            "nested": {"a": [FAKE_TOKEN]},
        },
    )
    record = caplog.records[-1]
    assert record.__dict__["nested"] == {"a": ["***"]}
    assert record.__dict__["note"] == "***"
    assert record.__dict__["request_url"] == "https://site.invalid"


def test_the_filter_cleans_a_stack(
    logger: logging.Logger, caplog: pytest.LogCaptureFixture
) -> None:
    record = logger.makeRecord(
        logger.name, logging.INFO, __file__, 1, "message", (), None, sinfo=FAKE_TOKEN
    )
    caplog.handler.handle(record)
    assert FAKE_TOKEN not in caplog.text


def test_the_filter_cleans_preformatted_exception_text(
    logger: logging.Logger, caplog: pytest.LogCaptureFixture
) -> None:
    record = logger.makeRecord(
        logger.name, logging.INFO, __file__, 1, "message", (), None
    )
    record.exc_text = FAKE_TOKEN
    caplog.handler.handle(record)
    assert FAKE_TOKEN not in caplog.text
