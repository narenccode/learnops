from libs.media_paths.signing import NoneSigner


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
