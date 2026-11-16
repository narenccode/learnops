# Release 0 demonstration script (T19 draft)

**Length:** about 10 minutes. **Needs:** a laptop, Python 3.12, no lab, no Moodle, no
BigBlueButton, no network after install. **Written against:** `origin/main` at `3abbc02`.

This script shows only what exists and works on `main`. It is **not** the PRD §E5 final
demonstration, which needs Releases 1 to 4 and fresh lab sites (see section 5). Every output below
was produced by running the command on 2026-11-16 (Windows, Python 3.12.5).

## 1. Set up (once)

```bash
git clone https://github.com/narenccode/learnops.git && cd learnops
python -m venv .venv
.venv/bin/pip install -r requirements-dev.txt        # Windows: .venv\Scripts\pip
```

Use `.venv/bin/python` below (Windows: `.venv\Scripts\python`).

## 2. Sequence

| Step | Minutes | What you show | Maps to |
|---|---|---|---|
| D1 | 2 | Contract examples validate against their schemas | PRD B.0 rule 1, E1, EXT-09 |
| D2 | 2 | A course package passes; a planted protected idnumber is caught | B1.4, EXT-09 |
| D3 | 2 | The lesson manifest schema rejects unsafe input | B6.3, C-08 |
| D4 | 2 | Media paths: unsafe paths refused, a relative path becomes a URL | B6.1, B6.4, C-08 |
| D5 | 1 | The B8.5 checker says the data set is PENDING | B8.5, decision 0004 |
| D6 | 1 | The full test suite and type check | E1 |

### D1. Contract examples validate

```bash
.venv/bin/python libs/contracts/validate_examples.py
```

Expected last line: `3 examples found, 2 schemas: 3 passed, 0 failed, 0 not validated; 0 problems found.`
Say: this runs in CI on every PR. It covers B1 and B6.3 only; other contracts have no schema on
`main`.

### D2. Course package, then a planted error

```python
from pathlib import Path
from libs.contracts import DirectorySource, validate_package
r = validate_package(DirectorySource(Path("contracts/examples/course-package.v1")))
print("ok:", r.ok, "errors:", len(r.errors), "not_checked:", len(r.not_checked))
```

Output: `ok: True errors: 0 not_checked: 8`.

Now copy the folder, change one `idnumber` (for example the first activity's) to `final-project`,
and run the same call on the copy. Output:

```
ok: False
 - sections[0].activities[0].idnumber: 'final-project' is a protected idnumber and cannot be used in a package.
```

Say: "8 not checked" is deliberate. The validator lists the rules it does **not** enforce, so "no
errors" is never read as "fully checked". Protected items are never generated or changed (CLAUDE.md §2.8).

### D3. Lesson manifest schema

```python
import json, jsonschema
s = json.load(open("contracts/lesson-manifest.v1.schema.json"))
d = json.load(open("contracts/examples/lesson-manifest.v1/single-track.json"))
v = jsonschema.Draft202012Validator(s)
print("valid example errors:", len(list(v.iter_errors(d))))            # 0
d["tracks"][0]["file"] = "../720p.mp4"
print("traversal rejected:", len(list(v.iter_errors(d))) > 0)          # True
d["tracks"][0]["file"] = "720p.mp4"
d["captions"] = [{"lang": "hi", "file": "captions.hi.vtt"}]
print("no English caption errors:", len(list(v.iter_errors(d))))       # 1
```

Say: B6.2 requires `captions.en.vtt`, so a manifest without an `en` caption is invalid (guide decision).

### D4. Media paths

```bash
PYTHONPATH=libs MEDIA_SIGNING=none MEDIA_BASE_URL=https://media.example.org .venv/bin/python
```

```python
from media_paths import validate_relative_path, create_media_signer, require_slug
for p in ["slides/001.jpg", "../720p.mp4", "%2e%2e/720p.mp4", "https://example.org/x.mp4"]:
    print(repr(p), validate_relative_path(p))
print(create_media_signer().sign("courses/ai-101/01-intro/01-welcome/720p.mp4"))
require_slug("../x", "cohort")
```

Output: `True`, `False`, `False`, `False`; then
`https://media.example.org/courses/ai-101/01-intro/01-welcome/720p.mp4`; then
`ValueError: cohort must be a slug: lowercase ASCII letters and digits separated by single hyphens (for example 'build-ai-assistant'), got '../x'`.

Say: only the `none` signer exists; `hmac` and `s3` give a configuration error. Media is stored as
relative paths only (PRD C-08). The URL host is a placeholder.

### D5. B8.5 data set is honestly PENDING

```bash
.venv/bin/python -m pytest -q libs/contracts/tests/test_b8_5_dataset.py::test_the_real_set_has_no_errors libs/contracts/tests/test_b8_5_dataset.py::test_the_real_status_is_true
```

Output: `2 passed`. Then open `testdata/README.md` lines 17-22.

Say clearly: the passing test proves the **placeholders are well formed and that PENDING is true**.
It does not show a recording, a consent line, a transcript, a word error rate or B8.5 acceptance.
None of those exists.

### D6. Whole suite

```bash
.venv/bin/python -m pytest -q -rs     # 2038 passed, 4 skipped (symlinks, on Windows)
.venv/bin/pip install mypy && .venv/bin/python -m mypy libs   # Success: no issues found in 30 source files
```

## 3. Requirement mapping

| Step | Requirement | Implementation | Test | PR | Status |
|---|---|---|---|---|---|
| D1 | B.0 rule 1, E1, EXT-09 | `libs/contracts/validate_examples.py`, `example_check.py` | `test_validate_examples.py`, `test_example_check.py` | #90, #102 | Merged (main) |
| D2 | B1.4, B1.1, EXT-09 | `libs/contracts/validate.py`, `course_rules.py`, `source.py` | `test_validate_course.py`, `test_validate_package.py` | #37, #48, #49 | Merged (main) |
| D3 | B6.3, B6.2, C-08 | `contracts/lesson-manifest.v1.schema.json` | `test_lesson_manifest_v1.py` | #32 | Merged (main) |
| D4 | B6.1 (validation only), B6.4, C-08 | `libs/media_paths/validation.py`, `signing.py` | `test_validation.py`, `test_signing.py` | #84, #86 | Merged (main). Path templates #85 open |
| D5 | B8.5, App-C 8 | `libs/contracts/tests/test_b8_5_dataset.py` | same | #82, #89, #99 | Checker merged; data **pending** |
| D6 | E1 | `.github/workflows/ci.yml` | whole suite | n/a | Merged (main); hosted run unconfirmed |

## 4. Rehearsal notes

- Do a dry run on the machine you will use. The venv install needs network once.
- On Windows without developer mode, four symlink tests skip. Say so if asked; do not call them passing.
- Do not open `docs/decisions/0004` and read the exception out as approved: its approval reference
  is PENDING.
- Questions you cannot answer from evidence: lab status, BigBlueButton behaviour, word error rate,
  Moodle 4.5 versus 5.3 results. Answer "not verified yet" and point to report section 6.

## 5. What this demonstration does not cover

PRD §E5 steps 1 to 6 are **not demonstrable**, because the code does not exist or needs a lab:

| E5 step | Needs | Status |
|---|---|---|
| 1 Course Studio, `.mbz` | Module 1, Release 2 | Not implemented |
| 2 Restore, checker, 5-role tests | Module 2, lab Moodle, Release 1 | Not implemented |
| 3 Lecture upload, BigBlueButton recording, captions, chapters, slide index, Moodle Page snippet | Module 4, Release 3, lab BBB | Not implemented; BBB **NOT VERIFIED** (open PRs #96, #97) |
| 4 Synthetic submissions drafted, graded, approved; grades in Moodle after release | Module 3, Release 4 | Not implemented; `moodle_ws` not on `main` |
| 5 Practice drafts (if Release 5 exists) | Release 5 | Not implemented |
| 6 G-1…G-10 with evidence; model comparison | All modules | No measurements exist. G-6 needs B8.5 data and a speech provider |
