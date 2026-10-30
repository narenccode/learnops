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

`validate_course_document(doc)` does the same for an already-parsed `course.yaml`; it reads no
files, so it cannot check body files.

`report.ok` is true when there are no errors. It does **not** mean everything was checked:
read `report.not_checked`.

## What is checked

The schema first (structure, B1.1). When the structure is valid, also:

| Check | PRD |
|---|---|
| `idnumber`s are unique in the course (sections and activities together) | B1.2 rule 6 |
| Extra protected idnumbers from `ValidationConfig`, in both modes | B1.4 |
| In `full` mode, assignment `points` add up to `total_points` (default 100) | B1.2 rule 3 |
| Every `body` is a file inside the package (no `..`, absolute path or outside link) | B1.1 |

## What is not checked (always listed in `report.not_checked`)

One guide Page and one task Assignment per week, the unlock chain, the marking table, the Check
vocabulary and `protected_section`. Their ownership or details are still open (see
`docs/design/studio.md` §12 and `docs/design/grading.md` Q39). In a `sections-only` package the
points total is not checked either. Also outside this library: marking workflow (CK-10),
completion tracking (CK-13), and "never reused for a different activity", which needs the
previous package version (Course Studio).

The checker's rules (CK-01…CK-13) work on the course model (B2) and stay in Module 2.

## Configuration

`ValidationConfig` is the only input besides the package. The library reads no environment
variables: the caller reads its own settings (for example Course Studio's protected idnumbers) and
passes them in. An invalid idnumber raises `ConfigError`.

## Tests

```
python -m pytest libs -q
ruff check libs && ruff format --check libs
mypy --strict libs
```

Two tests that create symbolic links are skipped on Windows without developer mode.
