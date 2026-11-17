"""Make `media_paths` (libs/) and `lesson_processor` importable without installing anything."""

import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]
for extra in (REPO / "libs", REPO / "modules" / "video" / "demo"):
    if str(extra) not in sys.path:
        sys.path.insert(0, str(extra))

from lesson_processor import processor  # noqa: E402

needs_ffmpeg = pytest.mark.skipif(
    not processor.ffmpeg_available(), reason="ffmpeg/ffprobe not installed"
)


@pytest.fixture(scope="session")
def synthetic_video(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """A 3-second 640x360 test-pattern video with a sine tone. Generated, never committed."""
    if not processor.ffmpeg_available():
        pytest.skip("ffmpeg/ffprobe not installed")
    path = tmp_path_factory.mktemp("media") / "sample.mp4"
    subprocess.run(
        [
            processor.find_tool("ffmpeg"), "-v", "error", "-y",
            "-f", "lavfi", "-i", "testsrc=size=640x360:rate=25:duration=3",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(path),
        ],
        check=True,
    )  # fmt: skip
    return path
