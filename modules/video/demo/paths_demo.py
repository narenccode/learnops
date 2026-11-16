"""D4 demo: video media paths (PRD B6.1, B6.3, B6.4; EXT-09, C-08).

Shows the existing `media_paths` library and the B6.3 manifest contract. It uses synthetic names
only, creates no files and calls no service. It does NOT show BigBlueButton recordings: that
source mapping and its lab verification are PENDING (see README.md in this folder).

Run from the repository root:  PYTHONPATH=libs python -B modules/video/demo/paths_demo.py
Every outcome is checked; the script exits 1 if anything differs from what is documented.
"""

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from media_paths import (
    DEFAULT_COURSE_LESSON_TEMPLATE,
    check_course_lesson_template,
    course_lesson_path,
    create_media_signer,
    live_class_path,
    validate_relative_path,
)

REPO = Path(__file__).resolve().parents[3]
# Placeholder host from .env.example. Full media URLs are never printed.
PLACEHOLDER_BASE = "https://media.lab.invalid"
failures: list[str] = []


def expect(label: str, ok: bool) -> None:
    """Record a failed expectation; print every line so the output reads as a script."""
    print(f"  [{'ok' if ok else 'UNEXPECTED'}] {label}")
    if not ok:
        failures.append(label)


def refusal(call: Callable[[], Any]) -> str | None:
    """Return the error message if the call is refused, None if it is accepted."""
    try:
        call()
    except (ValueError, TypeError) as error:
        return str(error)
    return None


def part_a() -> None:
    print("\nA. Validate relative paths (B6.3 rule, C-08)")
    cases = [
        ("slides/001.jpg", True, "plain relative path"),
        ("../720p.mp4", False, "parent traversal"),
        ("%2e%2e/720p.mp4", False, "encoded traversal (no '%' allowed anywhere)"),
        # Built from two parts so no full URL is written in this file. A leading URL scheme
        # ("https:") makes the path not relative.
        ("https:" + "/720p.mp4", False, "starts with a URL scheme, so not relative"),
    ]
    for path, valid, why in cases:
        expect(
            f"{path!r:34} valid={validate_relative_path(path)}  ({why})",
            validate_relative_path(path) is valid,
        )


def part_b() -> tuple[str, str]:
    print("\nB. Build paths from the B6.1 templates")
    lesson = course_lesson_path("build-ai-assistant", 1, "setup", 2, "install-python")
    live = live_class_path("build-ai-assistant", "spring-2027", 3, "rag-basics")
    print(f"  lesson folder: {lesson}")
    print(f"  live folder  : {live}")
    expect(
        "lesson folder is the B6.1 shape",
        lesson == "courses/build-ai-assistant/01-setup/02-install-python/",
    )
    expect(
        "live-class folder is the B6.1 shape",
        live == "courses/build-ai-assistant/live-spring-2027/03-rag-basics/",
    )

    bad_number = refusal(lambda: course_lesson_path("c", 1, "m", 100, "l"))
    bad_cohort = refusal(lambda: live_class_path("c", "Spring 27", 1, "t"))
    print(f"  lesson number 100 -> {bad_number}")
    print(f"  cohort 'Spring 27' -> {bad_cohort}")
    expect("lesson number outside 1-99 is refused", bad_number is not None)
    expect("cohort that is not a slug is refused", bad_cohort is not None)

    # Templates are checked once, when loaded (Guide decision recorded in PR #38).
    default_text = DEFAULT_COURSE_LESSON_TEMPLATE.text
    missing = refusal(
        lambda: check_course_lesson_template("courses/{course_slug}/{module_slug}/")
    )
    unknown = refusal(lambda: check_course_lesson_template(default_text + "{bogus}/"))
    print(f"  template without {{lesson_slug}} -> {missing}")
    print(f"  template with {{bogus}} -> {unknown}")
    expect(
        "template missing a required placeholder is refused",
        missing is not None and "lesson_slug" in missing,
    )
    expect(
        "template with an unknown placeholder is refused",
        unknown is not None and "bogus" in unknown,
    )
    return lesson, live


def part_c(lesson_folder: str) -> None:
    print("\nC. Release 0 signing: the 'none' signer (B6.4)")
    signer = create_media_signer(
        {"MEDIA_SIGNING": "none", "MEDIA_BASE_URL": PLACEHOLDER_BASE}
    )
    relative = lesson_folder + "720p.mp4"
    short = signer.sign(relative, ttl_seconds=60)
    long = signer.sign(relative, ttl_seconds=3600)
    print(f"  signed {relative!r}")
    print(
        f"  result = <media base URL> + {short.removeprefix(PLACEHOLDER_BASE)!r} (host not printed)"
    )
    expect(
        "result is the base URL plus the path",
        short == f"{PLACEHOLDER_BASE}/{relative}",
    )
    expect("unsigned: no query string, so no signature and no expiry", "?" not in short)
    expect(
        "ttl_seconds has no effect (60 s and 3600 s give the same result)",
        short == long,
    )
    expect(
        "an unsafe path is refused",
        refusal(lambda: signer.sign("../720p.mp4")) is not None,
    )
    hmac = refusal(
        lambda: create_media_signer(
            {"MEDIA_SIGNING": "hmac", "MEDIA_BASE_URL": PLACEHOLDER_BASE}
        )
    )
    print(f"  MEDIA_SIGNING=hmac -> {hmac}")
    expect(
        "hmac is not implemented; asking for it is a configuration error",
        hmac is not None and "not implemented" in hmac,
    )


def part_d(lesson_folder: str) -> None:
    print("\nD. Manifest (B6.3) and the lesson folder")
    schema = json.loads(
        (REPO / "contracts/lesson-manifest.v1.schema.json").read_text("utf-8")
    )
    path = REPO / "contracts/examples/lesson-manifest.v1/single-track.json"
    manifest = json.loads(path.read_text("utf-8"))
    errors = list(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(
            manifest
        )
    )
    expect(
        f"{path.name} validates against the schema ({len(errors)} errors)", not errors
    )

    # The folder in part B was built from hardcoded example values (module 1 "setup",
    # lesson 2 "install-python"). This only checks that those values are consistent with the
    # manifest example and the default layout. The library does not derive a folder from
    # lesson_id or validate that relationship (traceability: a separate pull request).
    expected = f"courses/{manifest['course_slug']}/{manifest['lesson_id']}/"
    print(f"  course_slug + lesson_id -> {expected}")
    expect(
        "hardcoded example values give courses/<course_slug>/<lesson_id>/ (consistency only)",
        lesson_folder == expected,
    )
    print(
        "  Note: the library does not derive the folder from lesson_id or check this link."
    )
    for track in manifest["tracks"]:
        full = lesson_folder + track["file"]
        print(f"  track {track['role']!r}: {full}")
        expect(
            f"track file is relative to the lesson folder and valid ({track['file']})",
            validate_relative_path(track["file"]) and validate_relative_path(full),
        )
    expect(
        'source.kind is "upload", the only source value the PRD and examples name',
        manifest["source"]["kind"] == "upload",
    )
    print(
        "  PENDING: BigBlueButton source value and recording metadata are not verified"
    )
    print(
        "  (App-C 4, FR-V-09: no lab run; see PR #96). Nothing is shown for them here."
    )


def main() -> int:
    print("LearnOps D4: video paths demo (synthetic data, no media, no services)")
    part_a()
    lesson, _live = part_b()
    part_c(lesson)
    part_d(lesson)
    if failures:
        print(f"\n{len(failures)} UNEXPECTED result(s):", *failures, sep="\n  - ")
        return 1
    print("\nAll expected outcomes observed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
