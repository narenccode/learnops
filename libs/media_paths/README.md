# Media Paths

Shared Python library for generating and validating LearnOps media paths and building media URLs.

## Requirements

- EXT-09 – the shared `media_paths` library: B6.1 media path templates and B6.4 media signing
  interface (`none` baseline implementation)
- C-08 – media is stored as relative paths

## Path generation

- `course_lesson_path(course_slug, module_number, module_slug, lesson_number, lesson_slug, template=DEFAULT_COURSE_LESSON_TEMPLATE)`
- `live_class_path(course_slug, cohort, number, topic_slug, template=DEFAULT_LIVE_CLASS_TEMPLATE)`

Default templates (PRD B6.1):

```text
courses/{course_slug}/{module_nn}-{module_slug}/{lesson_nn}-{lesson_slug}/
courses/{course_slug}/live-{cohort}/{nn}-{topic_slug}/
```

### Placeholders

A custom template may use only the placeholders of its own path type, by plain name:

| Path type | Placeholder | Filled from | Example |
|---|---|---|---|
| Course lesson | `{course_slug}` | `course_slug` | `build-ai-assistant` |
| | `{module_nn}` | `module_number`, zero-padded | `01` |
| | `{module_slug}` | `module_slug` | `setup` |
| | `{lesson_nn}` | `lesson_number`, zero-padded | `02` |
| | `{lesson_slug}` | `lesson_slug` | `install-python` |
| Live class | `{course_slug}` | `course_slug` | `build-ai-assistant` |
| | `{cohort}` | `cohort` | `batch-01` |
| | `{nn}` | `number`, zero-padded | `01` |
| | `{topic_slug}` | `topic_slug` | `python-introduction` |

Numbers are zero-padded to two digits.

### Loading a custom template

A custom template (for example `MEDIA_PATH_TEMPLATE`) is checked **once, when it is loaded**, not
on every call. Load it with `check_course_lesson_template(text)` or `check_live_class_template(text)`
and pass the result as `template=`:

```python
import os

from media_paths import check_course_lesson_template, course_lesson_path

template = check_course_lesson_template(os.environ["MEDIA_PATH_TEMPLATE"])  # at start-up
folder = course_lesson_path("python", 1, "basics", 2, "intro", template=template)
```

The path functions accept only a loaded `CourseLessonTemplate` / `LiveClassTemplate`; a plain
string raises `TypeError`. A template is rejected with a `ValueError` that names the problem if it:

- leaves out a placeholder that identifies the item: `{course_slug}`, `{module_slug}` and
  `{lesson_slug}` for lessons; `{course_slug}`, `{cohort}` and `{topic_slug}` for live classes.
  Without them two items could share one folder and overwrite each other. The number
  placeholders are optional;
- uses any other placeholder (including `{}`, `{0}`, `{name.attr}`, `{name[0]}`);
- has a format spec or conversion (`{module_nn:>3}`, `{course_slug!r}`);
- has unbalanced braces (write a literal brace as `{{` or `}}`);
- produces a path that is not a safe relative path (absolute, `..`, `//`, URL scheme, drive letter).

### Input rules

- Slugs and `cohort`: lowercase ASCII letters and digits separated by single hyphens (`2026-01`
  is a valid cohort).
- `module_number`, `lesson_number`, `number`: an `int` from 1 to 99 (`bool`, `float` and `str`
  are rejected).
- A wrong type raises `TypeError`; a wrong value raises `ValueError`.

## Validation

- `validate_slug(value) -> bool`: lowercase ASCII letters, digits and single hyphens.
- `validate_relative_path(value) -> bool`: the B6.3 contract's `relative_path` rule. Not empty;
  forward slashes only; no whitespace; no `?`, `#` or `\`; no URL scheme or drive letter at the
  start (`https:`, `C:`); not absolute; no empty, `.` or `..` segment. A colon elsewhere
  (`notes/b:c.md`, `12:30.mp4`) is allowed. Non-strings return `False`.
- **Open, waiting for the guide:** the library also rejects every character in Unicode category
  C, which the contract's pattern accepts:
  - Cc control characters: C0 controls such as NUL and ESC, DEL, and the C1 controls
    (U+0080–U+009F);
  - Cf format characters, such as zero-width space and joiner, bidi overrides, the byte order
    mark (BOM, U+FEFF) and the soft hyphen (U+00AD);
  - Co private-use characters;
  - Cs lone surrogates;
  - Cn unassigned code points, as defined by the Unicode version of the running Python (Python
    3.12 uses Unicode 15.0.0), so this set can change with the Python version.

  Control characters that count as whitespace (tab, newline, U+0085) are rejected by both. This
  stricter behaviour is not yet aligned with the B6.3 schema and is the one known difference from
  the contract.
- The shared contract vectors (`contracts/test-vectors/relative-path.v1.json`) arrive with PR #32;
  a test that runs them through this function is added once PR #32 is merged.

## Media signing (PRD B6.4)

`MediaSigner` is the interface: `sign(relative_path, ttl_seconds=3600) -> str`.

`create_media_signer()` is the single entry point. It reads `MEDIA_SIGNING` and `MEDIA_BASE_URL`
(see `.env.example`), or a mapping passed in for tests:

| `MEDIA_SIGNING` | Result |
|---|---|
| `none` | `NoneSigner(MEDIA_BASE_URL)` |
| `hmac`, `s3` | `MediaSigningConfigError`: named in PRD B6.4, not implemented yet |
| unset or anything else | `MediaSigningConfigError` |

```python
from media_paths import create_media_signer

signer = create_media_signer()  # MEDIA_SIGNING=none
url = signer.sign("courses/python/01-basics/01-intro/720p.mp4")
```

`NoneSigner` builds a plain URL: base URL + `/` + the percent-encoded relative path. **It adds no
signature and no expiry and provides no access control.** `ttl_seconds` is validated (an `int` of 1
or more) but not applied.

The base URL must be `http://` or `https://` with a host. A query string, fragment, user name or
password, whitespace, an invalid port or a malformed URL (for example unbalanced IPv6 brackets) is
rejected; trailing slashes are removed.

## Testing

Run from the repository root:

```bash
python -m pytest libs/media_paths/tests/ -v
```
