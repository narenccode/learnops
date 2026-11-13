import pytest

from media_paths.signing import (
    DEFAULT_TTL_SECONDS,
    MediaSigner,
    MediaSigningConfigError,
    NoneSigner,
    create_media_signer,
)


def test_none_signer_builds_media_url() -> None:
    signer = NoneSigner(media_base_url="https://media.example.com")

    result = signer.sign("courses/python/01-basics/01-intro/720p.mp4")

    assert result == (
        "https://media.example.com/" "courses/python/01-basics/01-intro/720p.mp4"
    )


def test_none_signer_accepts_custom_ttl() -> None:
    signer = NoneSigner(media_base_url="https://media.example.com")

    result = signer.sign(
        "poster.jpg",
        ttl_seconds=600,
    )

    assert result == "https://media.example.com/poster.jpg"


def test_none_signer_removes_trailing_slash_from_base_url() -> None:
    signer = NoneSigner(media_base_url="https://media.example.com/")

    result = signer.sign("poster.jpg")

    assert result == "https://media.example.com/poster.jpg"


# --- MediaSigner interface (PRD B6.4) ------------------------------------------


def test_none_signer_implements_media_signer_interface() -> None:
    assert isinstance(NoneSigner("https://media.example.com"), MediaSigner)


def test_default_ttl_matches_prd_b6_4() -> None:
    assert DEFAULT_TTL_SECONDS == 3600


def test_none_signer_output_has_no_signature_or_expiry() -> None:
    # The "none" mode must not pretend to sign: no query string, no token.
    result = NoneSigner("https://media.example.com").sign("poster.jpg", ttl_seconds=60)

    assert "?" not in result
    assert "#" not in result


# --- Base URL validation -------------------------------------------------------


@pytest.mark.parametrize(
    ("base_url", "expected"),
    [
        ("https://media.example.com", "https://media.example.com/poster.jpg"),
        ("http://media.lab.invalid", "http://media.lab.invalid/poster.jpg"),
        ("https://media.example.com:8443", "https://media.example.com:8443/poster.jpg"),
        ("https://cdn.example.com/media", "https://cdn.example.com/media/poster.jpg"),
        ("https://cdn.example.com/media/", "https://cdn.example.com/media/poster.jpg"),
        ("https://cdn.example.com/media//", "https://cdn.example.com/media/poster.jpg"),
        ("HTTPS://media.example.com", "HTTPS://media.example.com/poster.jpg"),
        ("http://127.0.0.1:8080", "http://127.0.0.1:8080/poster.jpg"),
        ("http://[::1]:8080", "http://[::1]:8080/poster.jpg"),
    ],
)
def test_valid_base_urls_are_joined_with_a_single_slash(
    base_url: str, expected: str
) -> None:
    assert NoneSigner(base_url).sign("poster.jpg") == expected


@pytest.mark.parametrize(
    ("base_url", "message"),
    [
        ("ftp://media.example.com", "http:// or https://"),
        ("file:///srv/media", "http:// or https://"),
        ("javascript:alert(1)", "http:// or https://"),
        ("media.example.com", "http:// or https://"),
        ("//media.example.com", "http:// or https://"),
        ("", "http:// or https://"),
        ("https://", "host name"),
        ("https:///media", "host name"),
        ("https://:8080", "host name"),
        ("https://media.example.com:notaport", "invalid port"),
        ("https://media.example.com:99999", "invalid port"),
        ("https://media.example.com?x=1", "query string or fragment"),
        ("https://media.example.com/?", "query string or fragment"),
        ("https://media.example.com/#top", "query string or fragment"),
        ("https://user:pass@media.example.com", "user name or password"),
        ("https://media.example.com /x", "whitespace or control"),
        ("https://media.example.com\n", "whitespace or control"),
        ("https://media.example.com\x00", "whitespace or control"),
        # Regression: urlsplit's own "Invalid IPv6 URL" leaked through unexplained.
        ("http://[::1", "not a valid URL"),
        ("https://[media.example.com/media", "not a valid URL"),
    ],
)
def test_invalid_base_urls_are_rejected(base_url: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        NoneSigner(base_url)


def test_base_url_error_does_not_echo_credentials() -> None:
    with pytest.raises(ValueError) as error:
        NoneSigner("https://user:s3cret@media.example.com")

    assert "s3cret" not in str(error.value)


@pytest.mark.parametrize("base_url", [None, 1, b"https://media.example.com"])
def test_non_string_base_url_is_rejected(base_url: object) -> None:
    with pytest.raises(TypeError, match="media_base_url must be a string"):
        NoneSigner(base_url)  # type: ignore[arg-type]


# --- sign() inputs -------------------------------------------------------------


@pytest.mark.parametrize(
    ("relative_path", "expected"),
    [
        ("lesson name.mp4", None),
        (
            "courses/python/100%.mp4",
            "https://media.example.com/courses/python/100%25.mp4",
        ),
        ("ünï.mp4", "https://media.example.com/%C3%BCn%C3%AF.mp4"),
        # A colon is allowed by the contract; encoding it keeps "12:30.mp4"
        # from ever being read as a scheme or a port.
        ("slides/12:30.mp4", "https://media.example.com/slides/12%3A30.mp4"),
        # A literal "%2e%2e" folder name stays literal: "%" is encoded, so the
        # media host can never decode it into a ".." segment.
        (
            "courses/%2e%2e/720p.mp4",
            "https://media.example.com/courses/%252e%252e/720p.mp4",
        ),
    ],
)
def test_sign_percent_encodes_path_characters(
    relative_path: str, expected: str | None
) -> None:
    signer = NoneSigner("https://media.example.com")
    if expected is None:
        with pytest.raises(ValueError, match="safe relative media path"):
            signer.sign(relative_path)
    else:
        assert signer.sign(relative_path) == expected


@pytest.mark.parametrize(
    "relative_path",
    [
        "../../etc",
        "/etc/passwd",
        "https://example.com/video.mp4",
        "module/../secret",
        "module/video.mp4?token=x",
        "module/video.mp4#fragment",
        "module/video.mp4\n",
        "",
    ],
)
def test_sign_rejects_unsafe_relative_paths(relative_path: str) -> None:
    with pytest.raises(ValueError, match="safe relative media path"):
        NoneSigner("https://media.example.com").sign(relative_path)


@pytest.mark.parametrize("ttl", [True, False, 1.5, 3600.0, "3600", None])
def test_sign_rejects_non_integer_ttl(ttl: object) -> None:
    # Regression: True was accepted as ttl_seconds=1 because bool is an int.
    with pytest.raises(TypeError, match="ttl_seconds must be an integer"):
        NoneSigner("https://media.example.com").sign("poster.jpg", ttl)  # type: ignore[arg-type]


@pytest.mark.parametrize("ttl", [0, -1, -3600])
def test_sign_rejects_ttl_below_one(ttl: int) -> None:
    with pytest.raises(ValueError, match="ttl_seconds must be 1 or greater"):
        NoneSigner("https://media.example.com").sign("poster.jpg", ttl)


# --- create_media_signer() configuration ---------------------------------------

LAB_ENV = {"MEDIA_SIGNING": "none", "MEDIA_BASE_URL": "https://media.lab.invalid"}


def test_media_signing_none_returns_none_signer() -> None:
    signer = create_media_signer(LAB_ENV)

    assert isinstance(signer, NoneSigner)
    assert isinstance(signer, MediaSigner)
    assert signer.sign("poster.jpg") == "https://media.lab.invalid/poster.jpg"


def test_create_media_signer_reads_os_environ_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MEDIA_SIGNING", "none")
    monkeypatch.setenv("MEDIA_BASE_URL", "https://media.lab.invalid")

    assert isinstance(create_media_signer(), NoneSigner)


@pytest.mark.parametrize("mode", ["hmac", "s3"])
def test_planned_signing_modes_raise_not_implemented_config_error(mode: str) -> None:
    with pytest.raises(MediaSigningConfigError, match="not implemented yet"):
        create_media_signer({**LAB_ENV, "MEDIA_SIGNING": mode})


@pytest.mark.parametrize("mode", ["", "None", "NONE", " none", "plain", "true"])
def test_unknown_signing_modes_raise_config_error(mode: str) -> None:
    with pytest.raises(MediaSigningConfigError, match="not a known signing mode"):
        create_media_signer({**LAB_ENV, "MEDIA_SIGNING": mode})


def test_missing_media_signing_raises_config_error() -> None:
    with pytest.raises(MediaSigningConfigError, match="MEDIA_SIGNING is not set"):
        create_media_signer({"MEDIA_BASE_URL": "https://media.lab.invalid"})


@pytest.mark.parametrize(
    "env", [{"MEDIA_SIGNING": "none"}, {**LAB_ENV, "MEDIA_BASE_URL": ""}]
)
def test_missing_media_base_url_raises_config_error(env: dict[str, str]) -> None:
    with pytest.raises(MediaSigningConfigError, match="MEDIA_BASE_URL is not set"):
        create_media_signer(env)


def test_invalid_media_base_url_raises_config_error() -> None:
    with pytest.raises(MediaSigningConfigError, match="MEDIA_BASE_URL is invalid"):
        create_media_signer({**LAB_ENV, "MEDIA_BASE_URL": "ftp://media.lab.invalid"})


def test_config_error_is_a_value_error() -> None:
    assert issubclass(MediaSigningConfigError, ValueError)
