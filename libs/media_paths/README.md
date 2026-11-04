# Media Paths

Shared Python library for generating and validating LearnOps media paths and building media URLs.

## Requirements

- B6.1 – Media path templates
- B6.4 – Media signing interface (`none` baseline implementation)

## Path generation

The library provides two path-generation functions:

- `course_lesson_path()` – generates course lesson paths.
- `live_class_path()` – generates live-class paths.

Default templates:

```text
courses/{course_slug}/{module_nn}-{module_slug}/{lesson_nn}-{lesson_slug}/
courses/{course_slug}/live-{cohort}/{nn}-{topic_slug}/
```

Both functions accept a custom template. Numbers are zero-padded to at least two digits.

## Validation

- `validate_slug()` checks lowercase ASCII letters, digits, and single hyphens.
- `validate_relative_path()` rejects unsafe or non-relative media paths.

## Media signing

`NoneSigner` builds plain media URLs using an injected media base URL.

```python
from media_paths import NoneSigner

signer = NoneSigner("https://media.example.com")
url = signer.sign("courses/python/01-basics/01-intro/720p.mp4")
```

The `ttl_seconds` parameter is accepted for interface compatibility but is not applied by the `none` implementation. No signature or expiry is generated.

## Testing

Run from the repository root:

```bash
python -m pytest libs/media_paths/tests/ -v
```
