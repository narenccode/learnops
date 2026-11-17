# `libs/contracts`: shared contract validators (PRD EXT-09)

Validates documents against the contracts in the repository folder `contracts/`. Today it
validates the **B1 course package** (PRD B1) and the **B2 course model** (PRD B2). Modules import it; they never copy it.

Not to be confused with `contracts/` at the repository root, which holds schemas and examples
(data), not Python.

## Using it

```python
from pathlib import Path
from contracts import DirectorySource, ValidationConfig, validate_package

config = ValidationConfig(protected_idnumbers=frozenset({"capstone-gate"}))  # optional
report = validate_package(DirectorySource(Path("my-course")), config=config)

for issue in report.errors:        # what is wrong, where, and what to do next
    print(issue.location, issue.message, issue.fix_hint)
for issue in report.not_checked:   # rules that did not run
    print(issue.code, issue.message)
```

`validate_course_document(doc)` does the same for an already-parsed `course.yaml`. It reads no
files, so it cannot check body files and lists them as not checked.

`report.ok` is true when there are no errors. It does **not** mean everything was checked: read
`report.not_checked`.

## Validating a B2 course model

```python
from contracts import validate_course_model

report = validate_course_model(model)   # a parsed course-model JSON document
```

`validate_course_model(doc)` checks the document against the B2 schema
(`contracts/course-model.v1.schema.json`) and, when `source.timezone` is a non-empty string,
that Python's `zoneinfo.ZoneInfo` resolves it (a schema cannot check a name). It returns the
same `ValidationReport`; its issues use rule `B2`. A missing, null, empty or non-text timezone
is left to the schema's rules, so it is reported once. It reads no files and no environment
variables, and does not raise on a malformed document.

It does **not** run the checker's rules CK-01 to CK-13: they belong to the checker module. For
this function `report.not_checked` is always empty, and that does **not** mean those rules
passed, only that this library holds no pending B2 rules. `report.ok` means the structure and
the time zone are valid, nothing more.

## What is checked

The schema first (structure, B1.1). When `course.yaml` is valid, also:

| Check | PRD |
|---|---|
| `idnumber`s are unique within the package (sections and activities together) | B1.2 rule 6, first half |
| Extra protected idnumbers from `ValidationConfig`, in both modes | B1.4 |
| Unlock rule by mode, in document order (the section number, `idnumber` and title are not read; an absent `unlock` equals both fields null). Full: the first section must have `after` null; every later section needs `after` naming the single assignment of the section just before it, and that section must hold exactly one assignment. Sections-only: every listed section, a single one included, needs `after`. It may name a template activity that is not in the package, and a name that matches nothing after the merge is the checker's CK-04; it must not name an activity of its own section or a later one. Cycles across sections are the checker's CK-05. Section-level `cm = -1` in `availability.py` resolves strictly before the section | B1.2 rule 2 |
| B2 course model: `validate_course_model(doc)` (see above) runs the B2 schema and the `zoneinfo` check, and is separate from `validate_package`. The pieces for the future builder are `timezone_issues(model)`, which checks `source.timezone` with `zoneinfo`, and `site_timezone(os.environ)` reads `SITE_TIMEZONE` with no default and raises `ConfigError` when it is missing or invalid | B2 |
| `validate_package` only: every `body` names a file inside the package folder (not missing, not a folder, no `..`, absolute path or link that leaves the folder). Only that the file exists is checked, never its content | B1.1 |

## Lesson files: chapters, slides, cues (PRD B6.2)

```python
from contracts import validate_chapters, validate_slides, validate_cues, check_within_duration

report = validate_cues(json.loads(Path("cues.json").read_text("utf-8")))  # a parsed JSON array
```

`validate_chapters`, `validate_slides` and `validate_cues` check a parsed file against its schema
(`contracts/<name>.v1.schema.json`) and return the same report as above. Chapters also get the rules a
schema cannot express: `end` after `start`, ascending order, no overlap (gaps are allowed). A cue with
a type in the track-role slug form that the contract does not list is valid; `readable_cues` returns what a v1 reader acts on
and `cue_is_required` tells whether a cue can be skipped. `check_within_duration(duration_s, ...)` is
the consumer-level rule that no time is after `duration_s` of `lesson.json`: the schemas do not do it.
Not checked (listed in `report.not_checked`): that the files named exist, that an `h5p` ref is a real
activity, that a `url` is allowed by the player.

## What is not checked (always listed in `report.not_checked`)

One guide Page and one task Assignment per week, the points total, completion
on unlock activities, an idnumber never reused across package versions, the marking table, the
Check vocabulary and `protected_section`. Their ownership or details are still open (see
`docs/design/studio.md` §12, `docs/design/grading.md` Q39 and the pull requests of this
library). The body files are also listed when the validator did not check them: for a parsed
document, or for a package whose `course.yaml` has errors. Marking workflow (CK-10) is not a
package field.

The checker's rules (CK-01…CK-13) work on the course model (B2) and stay in Module 2.

## Known limits

- **A folder only.** A zip is unpacked by Course Studio (with its own size and path checks, SEC-05)
  before it is validated. `PackageSource` is the small interface another source would implement.
- **Duplicate keys and size.** PyYAML keeps the last of two equal keys in `course.yaml` and the
  library sets no size limit. The caller limits what it accepts.
- **Links can change during validation (TOCTOU).** `DirectorySource` checks that a path stays
  inside the package folder and reads the file in separate steps. It does not guard against a
  link being swapped between the two. A change like that, made by someone else or by another
  process while validation runs, could point a read outside the folder. The check is not a
  security boundary against a package that is being modified while it is validated. The caller
  should validate a private copy that nothing else can change, such as the unpacked upload
  (Course Studio, SEC-05). Whether this library needs its own protection is an open question
  for the guide.
- **Letter case.** On Windows and macOS a body named `Weeks/01.md` finds `weeks/01.md`; on Linux it
  does not. Run the validation on Linux (the CI does) before trusting a package.
- **Repository checkout.** The schema is found two folders above this library, so it works from a
  checkout of the repository, not from a copy of `libs/` alone.

## Contract examples: the engine, `example_check.py` (PRD B.0 rule 1, E1)

`check_schema_examples(schema_path, schema_rel, examples)` loads one JSON Schema and checks a list
of example files (`.json`, `.yaml`, `.yml`) against it. It only reads files. Content it cannot use
is returned as a `Problem` instead of being raised, in a `SchemaCheck` with the problems (code,
message, `next:` hint, example and schema) and the examples that passed and failed. "Reported, not
raised" is not "everything is checked": read the limits below.

- **Problems:** `unreadable_schema` (bad JSON, not UTF-8, nested too deeply to read),
  `invalid_schema` (fails its meta-schema, a `$schema` that is not a string, nested too deeply to
  check), `unresolvable_reference` (a `$ref` that points at nothing, or at another file, which is
  not loaded), `unreadable_example` (bad syntax, not UTF-8, several YAML documents, impossible
  date, nested too deeply to read or to check against the schema) and `schema_violation` (one per
  error, with place and keyword, in a fixed order: list positions compare as numbers, so
  `items[2]` comes before `items[10]`).
- **Unusable schema.** When the schema is unreadable, invalid or has an unresolvable `$ref`, every
  example of that schema is reported as `example_not_validated`: neither passed nor failed, even if
  it was checked before the reference was reached. Problems inside those examples appear once the
  schema is fixed.
- **Limits.**
  - **A `$ref` is resolved only when an example reaches it.** A dangling reference in a branch
    that no example uses (an optional property, one arm of `oneOf`) is not found, so a schema can
    pass with a broken `$ref` that a later example would hit. `unresolvable_reference` means "an
    example reached a reference that cannot be resolved", not "the schema has no dangling
    reference".
  - **Formats.** With the pinned `jsonschema` and no optional format packages, these formats are
    checked: `date`, `email`, `idn-email`, `ipv4`, `ipv6`, `regex`, `time`, `uuid`. These are
    **not** checked, so any string passes: `date-time`, `duration`, `hostname`, `idn-hostname`,
    `iri`, `iri-reference`, `json-pointer`, `relative-json-pointer`, `uri`, `uri-reference`,
    `uri-template`. For example `completed_at` in `lesson-manifest.v1` is a `date-time`, so a wrong
    value in a B6 example is not caught. Checking more formats means adding a pinned package
    (CLAUDE.md §2.10), which is not done here.
  - **Time and memory are not bounded.** A huge file or a pathological regular expression can
    still exhaust them.
- YAML is parsed exactly as PyYAML's safe loader does, so an unquoted date stays a date and B1
  rejects it.
- Used by `validate_examples.py`, which finds the schemas and their examples (next section).

## Contract examples: `validate_examples.py` (PRD B.0 rule 1, E1)

A separate, repository-wide check that every contract example validates against its schema. CI
runs it on every pull request:

```
python libs/contracts/validate_examples.py [--check | --dry-run] [--contracts-dir PATH]
```

- **Schema names.** A schema must be named `<name>.v<N>.schema.json`: lowercase letters and digits
  separated by single hyphens, then `.v` and a version number without a leading zero (for example
  `course-package.v1.schema.json`). Any other `*.schema.json` file is reported as
  `misnamed_schema`, with its path and the correct form, and the run fails. It is never skipped, so
  a repository holding only misnamed schemas cannot pass. A misnamed schema is not loaded, so its
  examples are not looked for or counted. "No schema file at all" (`no_schemas`) is a different
  problem.
- **Pairing.** `contracts/<name>.v<N>.schema.json` has two kinds of example, alone or together:
  - *folder:* the top-level `.json`, `.yaml` and `.yml` files of `contracts/examples/<name>.v<N>/`
    (for example `course-package.v1/course.yaml`);
  - *flat:* `contracts/examples/<name>.v<N>.<suffix>.json` (or `.yaml`, `.yml`), with a one-word
    suffix such as `moodle-ws.v1.functions.json`.

  Matching is exact, so `thing.v1` never takes the examples of `thing.v10`. **Extensions are
  matched in any case in both layouts** (`A.JSON`); the stem and the suffix word must be lower
  case. Folder examples are listed first, then flat ones, each sorted by name. Every top-level
  file in a contract's folder is validated against that folder's schema, with no special cases. Files in subfolders (B1's
  `weeks/*.md`) are supporting files and are ignored (`validate_package` checks them).
- **Problems found here**, each with a `next:` hint: `no_schemas` (no `*.schema.json` file at all),
  `misnamed_schema` and `missing_example` (a schema with no example in either layout). Everything inside a schema or
  an example is reported by the engine (see above), including `unresolvable_reference`.
- **Links.** A symbolic link is followed whatever it points at, even a file outside `contracts/`,
  and the example is reported under the link's own path. Nothing is written, but the target's
  parse and schema errors (each cut to 300 characters) reach the CI log. `validate_package` (B1)
  refuses links that leave its package folder; this tool does not.
- The summary counts every example found, so passed, failed and not validated (the examples of an
  unusable schema) always add up to it.
- Not checked yet: examples that no schema matches (orphans such as `moodle-ws.v1.json` are skipped
  and the run can still exit 0), other file types next to the examples, duplicate keys, and `NaN`,
  `Infinity` and `-Infinity`. On #68 the guide set orphans, unsupported files, duplicate keys and
  strict JSON as a later pull request: they are not in this stack.
- Exit codes: `0` when every example passes, `1` when any problem is found, `2` for a usage error
  or a missing contracts folder. The tool only reads files: `--check` (the default) and
  `--dry-run` do the same, and there is nothing to undo.
- It validates structure only. Course-level rules (B1.2) belong to `validate_package`, and CK
  rules belong to the checker.

## Configuration

`ValidationConfig` is the only input besides the package. The library reads no environment
variables: the caller reads its own settings (for example Course Studio's protected idnumbers) and
passes them in. An invalid idnumber, or a `config` that is not a `ValidationConfig`, raises
`ConfigError`.

## Tests

```
python -m pytest libs -q
ruff check libs && ruff format --check libs
mypy --strict libs
```

Three tests that create symbolic links are skipped where the system does not allow links (Windows
without developer mode). They run on the Linux CI.
