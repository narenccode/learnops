# Media Paths

Shared Python library for generating and validating LearnOps media paths and building media URLs.

## Requirements

- B6.1 – Media path templates
- B6.4 – Media signing interface (`none` baseline implementation)

## Path generation

- `course_lesson_path(course_slug, module_number, module_slug, lesson_number, lesson_slug, template=...)`
- `live_class_path(course_slug, cohort, number, topic_slug, template=...)`

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

Numbers are zero-padded to at least two digits (`100` stays `100`). A template is rejected with a
`ValueError` that names the problem if it:

- uses any other placeholder (including `{}`, `{0}`, `{name.attr}`, `{name[0]}`);
- has a format spec or conversion (`{module_nn:>3}`, `{course_slug!r}`);
- has unbalanced braces (write a literal brace as `{{` or `}}`);
- produces a path that is not a safe relative path (absolute, `..`, `//`, URL).

### Input rules

- Slugs and `cohort`: lowercase ASCII letters and digits separated by single hyphens.
- `module_number`, `lesson_number`, `number`: an `int` of 1 or more (`bool`, `float` and `str`
  are rejected).
- A wrong type raises `TypeError`; a wrong value raises `ValueError`.

## Validation

- `validate_slug(value) -> bool`: lowercase ASCII letters, digits and single hyphens.
- `validate_relative_path(value) -> bool`: `/`-separated segments, none empty, `.` or `..`. Rejects
  absolute paths, `\`, `:` (schemes and drive letters), `?`, `#`, whitespace and control or format
  characters. Non-strings return `False`.

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
