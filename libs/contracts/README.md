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

- `contracts/<name>.v<N>.schema.json` is matched with `contracts/examples/<name>.v<N>/`. Every
  top-level file in that folder is an example and must be `.json`, `.yaml` or `.yml`. Files in
  subfolders (B1's `weeks/*.md`) are supporting files: counted in the output, not validated here
  (`validate_package` checks B1 body files).
- Errors, never skipped: a schema with no example, an example folder or file with no schema, a
  `*.schema.json` without a `v<N>` version, an unsupported top-level file, an unreadable or invalid
  schema, an unreadable example (bad syntax, not UTF-8, several YAML documents, a duplicate key), and
  every schema error in an example (with its place and keyword). Finding no schema at all is also an
  error.
- YAML is validated exactly as PyYAML's safe loader parses it, so an unquoted date stays a date and
  B1 rejects it. Formats such as `date` are checked.
- The summary line counts every example file found: the top-level `.json`, `.yaml` and `.yml` files
  in each example folder, including orphan examples (a folder or a loose file in
  `contracts/examples/` that no schema matches) and examples whose schema could not be loaded. Those
  are reported as "not validated", separately from "passed" and "failed", so the three always add
  up to the total. Supporting files in example subfolders are not part of the example count.
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
