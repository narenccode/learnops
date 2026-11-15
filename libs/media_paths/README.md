# Media Paths

Shared Python library for validating LearnOps media paths.

## Requirements

- EXT-09: the shared `media_paths` library
- C-08: media is stored as relative paths

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
