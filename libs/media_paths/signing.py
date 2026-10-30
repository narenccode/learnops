from urllib.parse import quote, urlsplit

from libs.media_paths.validation import validate_relative_path


class NoneSigner:
    """Build plain media URLs without signatures or expiry."""

    def __init__(self, media_base_url: str) -> None:
        parsed_url = urlsplit(media_base_url)

        if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
            raise ValueError("media_base_url must be an absolute HTTP(S) URL")

        self.media_base_url = media_base_url.rstrip("/")

    def sign(
        self,
        relative_path: str,
        ttl_seconds: int = 3600,
    ) -> str:
        """Return a plain media URL; ttl_seconds is accepted but ignored."""
        if not validate_relative_path(relative_path):
            raise ValueError("relative_path must be a safe relative media path")

        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be greater than zero")

        encoded_path = quote(relative_path, safe="/")
        return f"{self.media_base_url}/{encoded_path}"
