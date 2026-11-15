# `libs/contracts`: shared contract validators (PRD EXT-09)

Validates documents against the contracts in the repository folder `contracts/`. Today it
validates the **B1 course package** (PRD B1). Modules import it; they never copy it.

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

## What is checked

The schema first (structure, B1.1). When `course.yaml` is valid, also:

| Check | PRD |
|---|---|
| `idnumber`s are unique within the package (sections and activities together) | B1.2 rule 6, first half |
| Extra protected idnumbers from `ValidationConfig`, in both modes | B1.4 |
| `validate_package` only: every `body` names a file inside the package folder (not missing, not a folder, no `..`, absolute path or link that leaves the folder). Only that the file exists is checked, never its content | B1.1 |

## What is not checked (always listed in `report.not_checked`)

One guide Page and one task Assignment per week, the unlock chain, the points total, completion
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

## Contract examples: `validate_examples.py` (PRD B.0 rule 1, E1)

A separate, repository-wide check that every contract example validates against its schema. CI
runs it on every pull request:

```
python libs/contracts/validate_examples.py [--check | --dry-run] [--contracts-dir PATH]
```

- **Schema names.** A schema must be named `<name>.v<N>.schema.json`: lowercase letters and digits
  separated by single hyphens, then `.v` and a version number without a leading zero (for example
  `course-package.v1.schema.json`). A `*.schema.json` file with any other name is reported as
  `misnamed_schema`, with its path and the correct form, and the run fails. It is never skipped, so a
  repository holding only misnamed schemas cannot pass. "No schema file at all" (`no_schemas`) is a
  different problem.
- **Example layouts.** Both are supported, alone or together; nothing has to be moved. For the
  schema `<name>.v<N>.schema.json` the examples are:
  - *folder:* every top-level `.json`, `.yaml` or `.yml` file in `contracts/examples/<name>.v<N>/`,
    for example `contracts/examples/course-package.v1/course.yaml`;
  - *flat:* every `contracts/examples/<name>.v<N>.<suffix>.json` (or `.yaml`, `.yml`), for example
    `contracts/examples/moodle-ws.v1.functions.json`. The suffix is one word of lowercase letters,
    digits and hyphens (`meta-local`).

  Matching is exact on `<name>.v<N>`, so `thing.v1` never takes the examples of `thing.v10`. In
  the output and in the summary, folder examples come first, then flat ones, each group sorted by
  name. A schema with no example in either layout is a `missing_example` problem.
- **Folder ownership.** Every top-level example file inside a contract's folder is validated
  against that folder's schema, whatever the file is called. A file that belongs to another
  contract must live in that contract's own folder or be a flat file named after it. The validator
  has no special cases. Files in subfolders (B1's `weeks/*.md`) are supporting files and are ignored
  by design (`validate_package` checks B1 body files); they are not listed in the output yet.
- Errors, each with a problem code and a `next:` hint:
  - `no_schemas`: no `*.schema.json` file at all;
  - `misnamed_schema`: a `*.schema.json` file not named `<name>.v<N>.schema.json`;
  - `missing_example`: a schema with no example in either layout;
  - `unreadable_schema` and `invalid_schema`: the schema is not JSON, or fails its meta-schema;
  - `unresolvable_reference`: a `$ref` that points at nothing, such as `#/$defs/missing`, or at
    another file (references to other files are not loaded);
  - `unreadable_example`: bad syntax, not UTF-8, several YAML documents or an impossible date;
  - `schema_violation`: one per schema error in an example, with its place and keyword.
- **Unusable schema.** When a schema cannot be used (`unreadable_schema`, `invalid_schema` or
  `unresolvable_reference`), each of its examples gets an `example_not_validated` problem and is
  counted as "not validated": neither passed nor failed, even if it was checked before the
  reference was reached. Problems found in those examples, such as an unreadable file, are not
  reported until the schema is fixed. A misnamed schema is different: it is not loaded at all, so
  its examples are not looked for or counted.
- Not checked yet: examples that no schema matches (for instance a flat file whose schema does not
  exist), other file types next to the examples, duplicate keys, and the non-standard JSON
  constants `NaN`, `Infinity` and `-Infinity`.
- YAML is validated exactly as PyYAML's safe loader parses it, so an unquoted date stays a date and
  B1 rejects it. Formats such as `date` are checked.
- The summary line counts every example found, including examples whose schema could not be
  loaded. Those are reported as "not validated", separately from "passed" and "failed", so the three
  always add up to the total. Supporting files are not counted.
- Exit codes: `0` when every example passes, `1` when any problem is found, `2` for a usage error or a
  missing contracts folder.
- The tool only reads files. `--check` (the default) and `--dry-run` do the same thing, and there is
  nothing to undo.
- It validates structure only. Course-level rules (B1.2) belong to `validate_package`, and CK rules
  belong to the checker.

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
