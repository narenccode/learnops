# Media Paths

Shared Python library for generating and validating LearnOps media paths.

## Requirements

- EXT-09: the shared `media_paths` library, including the B6.1 media path templates
- C-08: media is stored as relative paths

## Path generation

- `course_lesson_path(course_slug, module_number, module_slug, lesson_number, lesson_slug, template=DEFAULT_COURSE_LESSON_TEMPLATE)`
- `live_class_path(course_slug, cohort, number, topic_slug, template=DEFAULT_LIVE_CLASS_TEMPLATE)`

Default templates (PRD B6.1):

```text
courses/{course_slug}/{module_nn}-{module_slug}/{lesson_nn}-{lesson_slug}/
courses/{course_slug}/live-{cohort}/{nn}-{topic_slug}/
```

A custom template may use only the placeholders of the default template of its own path type,
by plain name. `{module_nn}`, `{lesson_nn}` and `{nn}` are filled from `module_number`,
`lesson_number` and `number`, zero-padded to two digits. Slugs and `cohort` are lowercase ASCII
letters and digits separated by single hyphens (`2026-01` is a valid cohort); numbers are an `int`
from 1 to 99 (`bool`, `float` and `str` are rejected). A wrong type raises `TypeError`; a wrong
value raises `ValueError`.

### Loading a custom template

A custom template (for example `MEDIA_PATH_TEMPLATE`) is checked **once, when it is loaded**.
Load it with `check_course_lesson_template(text)` or `check_live_class_template(text)`, pass the
result as `template=`, and add a file name with `posixpath.join`, checking the result:

```python
import os
import posixpath

from media_paths import check_course_lesson_template, course_lesson_path, validate_relative_path

template = check_course_lesson_template(os.environ["MEDIA_PATH_TEMPLATE"])  # at start-up
folder = course_lesson_path("python", 1, "basics", 2, "intro", template=template)
path = posixpath.join(folder, "720p.mp4")  # not folder + "/" + "720p.mp4"
assert validate_relative_path(path)
```

The defaults end with `/`; a custom template need not (no rule on this has been decided).
`posixpath.join` handles both. `folder + "/" + "720p.mp4"` gives `.../intro//720p.mp4` for the
defaults (an empty segment, rejected by `validate_relative_path`); `folder + "720p.mp4"` gives
`.../intro720p.mp4` for a custom folder without a trailing `/`.

The path functions accept only a loaded `CourseLessonTemplate` / `LiveClassTemplate`; a plain
string raises `TypeError`. A template is rejected with a `ValueError` that names the problem if it:

- leaves out a placeholder that identifies the item (lessons: `{course_slug}`, `{module_slug}`,
  `{lesson_slug}`; live classes: `{course_slug}`, `{cohort}`, `{topic_slug}`), so two items
  could share one folder. Number placeholders are optional;
- puts two of those in one path segment, such as `{course_slug}{module_slug}/` (guide decision:
  `ab` + `c` and `a` + `bc` would share a folder). A number may share it (`{module_nn}-{module_slug}`);
- uses any other placeholder (`{}`, `{0}`, `{name.attr}`, `{name[0]}`), has a format spec or
  conversion (`{module_nn:>3}`) or unbalanced braces (use `{{` or `}}`), or produces a path that
  is not a safe relative path (see Validation below).

**Custom templates can collide.** Nothing checks the two templates against each other, so the
library does **not** prevent a lesson and a live class from getting the same folder (no rule on
this has been decided). The defaults cannot collide (a lesson's module segment starts with two
digits, a live-class segment with `live-`), but custom templates can, in either direction. Keep
the two types apart yourself.

- Custom lesson template `courses/{course_slug}/{module_slug}/{lesson_slug}/`, `module_slug` =
  `live-batch-01`, `lesson_slug` = `01-recap`: `courses/python/live-batch-01/01-recap/`, the
  default live-class folder for cohort `batch-01`, number 1, topic `recap`.
- Custom live-class template `courses/{course_slug}/{cohort}/{nn}-{topic_slug}/`, `cohort` =
  `01-basics`, number 2, topic `intro`: `courses/python/01-basics/02-intro/`, the default lesson
  folder for module 1 `basics`, lesson 2 `intro`.

## Validation

- `validate_slug(value) -> bool`: lowercase ASCII letters, digits and single hyphens.
- `validate_relative_path(value) -> bool`: the B6.3 contract's `$defs/relative_path` rule
  (`contracts/lesson-manifest.v1.schema.json`), one rule for both (guide decision). Not empty;
  forward slashes only; no whitespace; no `?`, `#` or `\`; no URL scheme or drive letter at the
  start (`https:`, `C:`); not absolute; no empty, `.` or `..` segment. A colon elsewhere
  (`notes/b:c.md`, `12:30.mp4`) is allowed. A first segment that starts with letters and a colon
  looks like a scheme and is rejected, for example `intro:part1.mp4` (`notes/intro:part1.mp4` is
  allowed). Non-strings return `False`.
- No `%` anywhere (guide decision): the B6.4 `none` signer appends the path to the media base
  URL, and a layer that decodes it, once or more, could turn an encoded form (`%2e`, `%252e`,
  `%25%32%65`, ...) into a dot or separator. Rejecting the sign covers every encoding depth; paths
  are built from slugs and fixed names, so a literal `%` has no use.
- No control or format character: every character in Unicode category **Cc**
  (U+0000–U+001F, U+007F–U+009F) and in the complete category **Cf** of Unicode 15.0.0 is
  rejected. Cf includes the bidi controls (U+061C, U+200E–U+200F, U+202A–U+202E,
  U+2066–U+2069), zero-width characters, the byte order mark (U+FEFF), the soft hyphen (U+00AD)
  and U+0600–U+0605, U+06DD. Private-use (Co), surrogate (Cs) and unassigned (Cn) code points
  are **not** rejected as categories. A valid path can therefore contain a lone surrogate (for
  example `"a\ud800.mp4"`), and encoding it with `path.encode("utf-8")` raises
  `UnicodeEncodeError`. A caller that writes a path to disk, JSON or a URL must handle that error.
- The Cc and Cf ranges are an explicit table in `validation.py` (`CC_RANGES`, `CF_RANGES`),
  copied from the Unicode Character Database 15.0.0
  ([`DerivedGeneralCategory.txt`](https://www.unicode.org/Public/15.0.0/ucd/extracted/DerivedGeneralCategory.txt)),
  the same table as the schema pattern. Validation does not read `unicodedata` at run time, so a
  Python upgrade cannot change the rule silently. A test compares the table with the running
  Python's Unicode database and **fails** if the Unicode version or the Cc/Cf sets differ
  (Python 3.12 uses 15.0.0). Do not edit the table to make it pass: a new Unicode version is a
  contract change (PRD B.0) for this library and the B6.3 schema pattern together.
- Not enforced in v1 (guide decision): Windows reserved names (such as `CON`), Unicode
  normalization, and a maximum length (paths are built from bounded slugs, and the store
  enforces its own limits).
- Tests run every shared vector in `contracts/test-vectors/relative-path.v1.json` through this
  function, and compare it with the schema pattern on every Unicode code point.

The module also has helpers that raise a clear error instead of returning `False`:
`require_slug(value, name)`, `require_positive_int(value, name)` and
`require_int_in_range(value, name, minimum, maximum)`. A wrong type raises `TypeError` (`bool` is
not accepted as an integer); a wrong value raises `ValueError`.

## Testing

Run from the repository root:

```bash
python -m pytest libs/media_paths/tests/ -v
```
