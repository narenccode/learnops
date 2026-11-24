"""One token per site, from the environment only (B4 §1, guide on Q24)."""

from __future__ import annotations

from typing import Any

import pytest

from moodle_ws import MoodleConfigError, Site, SiteSettings, Token, load_site
from moodle_ws.config import ALLOW_PLAIN_HTTP_VARIABLE

URL = "https://site.invalid"
ENV = {
    "MOODLE45_URL": URL,
    "MOODLE45_WS_TOKEN": "made-up-45",
    "MOODLE53_URL": URL,
    "MOODLE53_WS_TOKEN": "made-up-53",
}


@pytest.mark.parametrize(
    ("site", "version", "value"),
    [(Site.MOODLE45, "4.5", "made-up-45"), (Site.MOODLE53, "5.3", "made-up-53")],
)
def test_each_site_has_its_own_token(site: Site, version: str, value: str) -> None:
    settings = load_site(site, ENV)
    assert settings.moodle_version == version
    assert settings.token.reveal() == value


def test_each_site_ignores_the_other_sites_token() -> None:
    environ = {key: value for key, value in ENV.items() if key != "MOODLE45_WS_TOKEN"}
    assert load_site(Site.MOODLE53, environ).token.reveal() == "made-up-53"
    with pytest.raises(MoodleConfigError, match="MOODLE45_WS_TOKEN"):
        load_site(Site.MOODLE45, environ)


def test_the_old_shared_variable_is_never_looked_up() -> None:
    class Recording(dict[str, str]):
        asked: set[str] = set()

        def get(self, key: str, default: Any = None) -> Any:
            self.asked.add(key)
            return super().get(key, default)

        def __getitem__(self, key: str) -> str:
            self.asked.add(key)
            return super().__getitem__(key)

    environ = Recording(ENV)
    load_site(Site.MOODLE45, environ)
    load_site(Site.MOODLE53, environ)
    assert "MOODLE_WS_TOKEN" not in Recording.asked
    # The lab-only http setting and the other site's token are read too; the old shared one never.
    assert Recording.asked == set(ENV) | {ALLOW_PLAIN_HTTP_VARIABLE}


def test_a_placeholder_url_is_refused_without_showing_the_token() -> None:
    with pytest.raises(MoodleConfigError, match="MOODLE45_URL") as caught:
        load_site(Site.MOODLE45, {**ENV, "MOODLE45_URL": "CHANGE_ME"})
    assert "made-up-45" not in str(caught.value)


def test_a_site_name_can_be_a_string() -> None:
    assert load_site("moodle53", ENV).site is Site.MOODLE53


def test_an_unknown_site_is_refused() -> None:
    with pytest.raises(MoodleConfigError, match="not a Moodle site") as caught:
        load_site("moodle40", ENV)
    assert caught.value.__context__ is None


def test_the_old_shared_variable_is_not_read() -> None:
    with pytest.raises(MoodleConfigError, match="MOODLE45_WS_TOKEN"):
        load_site(Site.MOODLE45, {"MOODLE45_URL": URL, "MOODLE_WS_TOKEN": "made-up"})


@pytest.mark.parametrize("variable", ["MOODLE45_URL", "MOODLE45_WS_TOKEN"])
def test_a_missing_setting_is_named(variable: str) -> None:
    environ = {key: value for key, value in ENV.items() if key != variable}
    with pytest.raises(MoodleConfigError, match=variable):
        load_site(Site.MOODLE45, environ)


@pytest.mark.parametrize("value", ["", "   "])
def test_a_blank_token_counts_as_missing(value: str) -> None:
    with pytest.raises(MoodleConfigError, match="not set"):
        load_site(Site.MOODLE45, {**ENV, "MOODLE45_WS_TOKEN": value})


def test_the_placeholder_is_refused() -> None:
    with pytest.raises(MoodleConfigError, match="placeholder"):
        load_site(Site.MOODLE45, {**ENV, "MOODLE45_WS_TOKEN": "CHANGE_ME"})


def test_the_environment_is_the_default_source(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in ENV.items():
        monkeypatch.setenv(name, value)
    assert load_site(Site.MOODLE45).token.reveal() == "made-up-45"


def test_a_configuration_error_never_shows_a_value() -> None:
    with pytest.raises(MoodleConfigError) as caught:
        load_site(Site.MOODLE45, {"MOODLE45_WS_TOKEN": "made-up-45"})
    assert "made-up-45" not in str(caught.value)


@pytest.mark.parametrize(
    "value", [None, 12345, b"made-up-bytes", ["made-up-list"], object()]
)
def test_a_token_must_be_a_string(value: Any) -> None:
    """A wrong type fails here with a clear error, not later as an AttributeError in SiteSettings."""
    with pytest.raises(MoodleConfigError) as caught:
        Token(value)
    assert "'token'" in str(caught.value)
    assert "made-up" not in str(caught.value)


def test_a_string_token_is_still_accepted() -> None:
    assert Token("made-up-45").reveal() == "made-up-45"


# --- site addresses are https (guide, #150, 22 Nov): a token must not travel unencrypted ---------

HTTP_URL = "http://site.invalid:8080"
HTTP_ENV = {**ENV, "MOODLE45_URL": HTTP_URL}


def test_a_plain_http_address_is_refused_and_not_repeated() -> None:
    with pytest.raises(MoodleConfigError, match="plain http") as caught:
        load_site(Site.MOODLE45, HTTP_ENV)
    text = str(caught.value)
    assert ALLOW_PLAIN_HTTP_VARIABLE in text  # says what to do
    assert "moodle45" in text
    assert HTTP_URL not in text and "made-up-45" not in text


@pytest.mark.parametrize(
    ("value", "allowed"),
    [
        ("true", True),
        ("TRUE", True),
        (" true ", True),
        ("1", False),
        ("yes", False),
        ("on", False),
        ("false", False),
        ("", False),
        ("truee", False),
    ],
)
def test_the_lab_only_setting_must_be_exactly_true(value: str, allowed: bool) -> None:
    environ = {**HTTP_ENV, ALLOW_PLAIN_HTTP_VARIABLE: value}
    if allowed:
        assert load_site(Site.MOODLE45, environ).url == HTTP_URL
    else:
        with pytest.raises(MoodleConfigError, match="plain http"):
            load_site(Site.MOODLE45, environ)


def test_the_lab_only_setting_does_not_touch_an_https_address() -> None:
    environ = {**ENV, ALLOW_PLAIN_HTTP_VARIABLE: "true"}
    assert load_site(Site.MOODLE45, environ).url == URL


def test_the_other_site_is_checked_on_its_own_address() -> None:
    # Only the 4.5 address is plain http; the 5.3 site loads without the setting.
    assert load_site(Site.MOODLE53, HTTP_ENV).url == URL


def test_settings_built_by_hand_refuse_plain_http_too() -> None:
    with pytest.raises(MoodleConfigError, match="plain http"):
        SiteSettings(Site.MOODLE45, "4.5", HTTP_URL, Token("made-up-45"))
    allowed = SiteSettings(
        Site.MOODLE45, "4.5", HTTP_URL, Token("made-up-45"), allow_plain_http=True
    )
    assert allowed.url == HTTP_URL


def test_the_flag_must_be_a_real_bool() -> None:
    flag: Any = "true"  # a string, not a bool: refused, so "true" cannot sneak in
    with pytest.raises(MoodleConfigError, match="'allow_plain_http'"):
        SiteSettings(Site.MOODLE45, "4.5", HTTP_URL, Token("t"), allow_plain_http=flag)


@pytest.mark.parametrize(
    "url",
    [
        "ftp://site.invalid",
        "http://user:pw@site.invalid",
        "http://site.invalid?x=1",
        "http://",
    ],
)
def test_the_lab_setting_never_makes_a_bad_address_valid(url: str) -> None:
    with pytest.raises(MoodleConfigError, match="'url'"):
        SiteSettings(Site.MOODLE45, "4.5", url, Token("t"), allow_plain_http=True)


# --- the same token on both sites is refused (design 4.1, guide #150, 22 Nov) --------------------

SAME = {**ENV, "MOODLE45_WS_TOKEN": "one-token", "MOODLE53_WS_TOKEN": "one-token"}


@pytest.mark.parametrize("site", [Site.MOODLE45, Site.MOODLE53])
def test_the_same_token_for_both_sites_is_refused_from_either_side(site: Site) -> None:
    with pytest.raises(MoodleConfigError, match="same token") as caught:
        load_site(site, SAME)
    text = str(caught.value)
    assert "MOODLE45_WS_TOKEN" in text and "MOODLE53_WS_TOKEN" in text
    assert "one-token" not in text  # the value is never shown


def test_the_same_token_after_trimming_is_still_the_same() -> None:
    environ = {**SAME, "MOODLE53_WS_TOKEN": "  one-token \t"}
    with pytest.raises(MoodleConfigError, match="same token"):
        load_site(Site.MOODLE45, environ)


@pytest.mark.parametrize(
    "other",
    [None, "", "   ", "CHANGE_ME"],
    ids=["missing", "empty", "blank", "placeholder"],
)
def test_an_unset_other_token_is_not_a_clash(other: str | None) -> None:
    environ = {k: v for k, v in SAME.items() if k != "MOODLE53_WS_TOKEN"}
    if other is not None:
        environ["MOODLE53_WS_TOKEN"] = other
    assert load_site(Site.MOODLE45, environ).token.reveal() == "one-token"


def test_two_different_tokens_still_load() -> None:
    assert load_site(Site.MOODLE45, ENV).token.reveal() == "made-up-45"
    assert load_site(Site.MOODLE53, ENV).token.reveal() == "made-up-53"


def test_a_placeholder_is_not_a_clash_with_itself() -> None:
    environ = {
        **ENV,
        "MOODLE45_WS_TOKEN": "CHANGE_ME",
        "MOODLE53_WS_TOKEN": "CHANGE_ME",
    }
    with pytest.raises(MoodleConfigError, match="placeholder"):
        load_site(Site.MOODLE45, environ)
