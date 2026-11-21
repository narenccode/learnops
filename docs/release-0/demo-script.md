# Release 0 demonstration script (T19, revision 3)


**Length:** about 12 minutes. **Needs:** Python 3.12 and a POSIX shell (Git Bash on Windows). No
lab, no Moodle, no BigBlueButton, no AI or speech service, and no network after the install.
**Checked against:** `origin/main` at `5f3a794`. Every "Actual" result below was produced by running
the command on 2026-11-20 (Windows 11, Python 3.12.5), then compared with the hosted CI run on the
same commit (`docs/release-0/report.md` section 5). Revision 2 was checked at `3abbc02`; one result
changed (A2) and is marked.

This is **not** the PRD §E5 final demonstration, which needs Releases 1 to 4 and fresh lab sites.
Section 4 lists what is not demonstrable and why. The demo makes no claim about BigBlueButton, a
word error rate, B8.5 acceptance or Moodle (report section 9).

## 1. Part A: current executable demonstration

### Set up (once, from a clone of `main`)

```bash
git clone https://github.com/narenccode/learnops.git && cd learnops
python -m venv .venv && . .venv/bin/activate          # Windows Git Bash: . .venv/Scripts/activate
pip install -r requirements.txt -r requirements-dev.txt   # requirements.txt now holds tzdata, which the B2 checks need on Windows
export PYTHONPATH=.
```

| Step | Objective | Minutes |
|---|---|---|
| A1 | Contract examples validate against their schemas | 2 |
| A2 | A course package validates; planted errors are caught | 3 |
| A3 | The lesson manifest schema refuses unsafe input | 2 |
| A4 | Media paths: unsafe paths refused; a relative path becomes a URL | 2 |
| A5 | The B8.5 checker reports the data set honestly as PENDING | 1 |
| A6 | Whole test suite, type check | 2 |

### A1. Contract examples validate

- **Objective:** show that every contract example is checked against its schema (PRD B.0 rule 1, E1).
- **Command:** `python libs/contracts/validate_examples.py`
- **Expected:** every example passes, exit code 0.
- **Actual (verified):** `26 examples found, 10 schemas: 26 passed, 0 failed, 0 not validated; 0 problems found.` Exit 0. (Revision 2 showed 3 examples and 2 schemas.)
- **Implementation:** `libs/contracts/validate_examples.py`, `libs/contracts/example_check.py`.
- **Test:** `libs/contracts/tests/test_validate_examples.py`, `test_example_check.py`.
- **Evidence:** PRs #90, #92 and #102 (base `main`). #91 merged only into a stacked branch and was replaced by #102. CI runs this step on every PR.
- **Limitations:** ten schemas exist (B1 to B7 and the B6.2 file shapes); the contracts are not frozen. A dangling `$ref` that no example reaches is not found; `date` is checked, `date-time` is not.

### A2. Course package, then planted errors

- **Objective:** show that a valid B1 package passes and that a protected or duplicate idnumber is refused with its place and a clear message (B1.4, B1.2 rule 6).
- **Command:**

```bash
python - <<'EOF'
import shutil, tempfile
from pathlib import Path
from libs.contracts import DirectorySource, validate_package

src = Path("contracts/examples/course-package.v1")

def check(label, folder):
    r = validate_package(DirectorySource(folder))
    print(f"{label}: ok={r.ok} errors={len(r.errors)} not_checked={len(r.not_checked)}")
    for i in r.errors:
        print("  -", i.message)

check("example package", src)

def planted(old, new):
    tmp = Path(tempfile.mkdtemp()) / "pkg"
    shutil.copytree(src, tmp)
    f = tmp / "course.yaml"
    text = f.read_text(encoding="utf-8")
    assert text.count(old) == 1, old
    f.write_text(text.replace(old, new), encoding="utf-8")
    return tmp

check("planted protected idnumber", planted("idnumber: wk-01-guide", "idnumber: final-project"))
check("planted duplicate idnumber", planted("idnumber: wk-01-task", "idnumber: wk-01-guide"))
EOF
```

- **Expected:** the example passes; the protected idnumber fails with one error; the duplicate idnumber fails with the duplicate error, and also with an unlock error, because renaming `wk-01-task` breaks the week 2 unlock chain.
- **Actual (verified on 2026-11-20), exit 0 (the duplicate case had one error in revision 2; the unlock rule is newer):**

```
example package: ok=True errors=0 not_checked=8
planted protected idnumber: ok=False errors=1 not_checked=10
  - sections[0].activities[0].idnumber: 'final-project' is a protected idnumber and cannot be used in a package.
planted duplicate idnumber: ok=False errors=2 not_checked=8
  - sections[0].activities[1].idnumber: the idnumber 'wk-01-guide' is already used at sections[0].activities[0].idnumber. Idnumbers must be unique in the course.
  - sections[1].unlock.after: 'wk-01-task' is not a task (assignment) of the previous week (sections[0]).
```

- **Say:** "not_checked" is deliberate: the validator lists rules it does not enforce, so "no errors" is never read as "fully checked". In the protected-idnumber case it reports 10, because a schema error holds the idnumber rules back.
- **Implementation:** `libs/contracts/validate.py`, `course_rules.py`, `source.py`, `config.py`, `report.py`.
- **Test:** `test_validate_course.py`, `test_validate_package.py`, `test_config.py`, `test_report.py`, `test_course_package_v1.py`.
- **Evidence:** PRs #23, #37, #48, #49 (base `main`).
- **Limitations:** idnumber reuse across package versions is not checked (`idnumber_reuse_not_checked`). This is not FR-S-03 or FR-C-03; the checker rules need the B2 course model, which is merged (#46) but has no checker code yet. The B1 changes #87, #94 and #101 are merged.

### A3. Lesson manifest schema

- **Objective:** show the B6.3 schema refusing a traversal path, a percent-encoded path, a lesson without an English caption, and a manifest missing a required field.
- **Command:**

```bash
python - <<'EOF'
import copy, json
import jsonschema

schema = json.load(open("contracts/lesson-manifest.v1.schema.json", encoding="utf-8"))
good = json.load(open("contracts/examples/lesson-manifest.v1/single-track.json", encoding="utf-8"))
v = jsonschema.Draft202012Validator(schema)

def errors(doc):
    return sorted(e.json_path for e in v.iter_errors(doc))

print("example:", errors(good))
a = copy.deepcopy(good); a["tracks"][0]["file"] = "../720p.mp4"
print("traversal path:", errors(a))
b = copy.deepcopy(good); b["tracks"][0]["file"] = "%2e%2e/720p.mp4"
print("percent-encoded path:", errors(b))
c = copy.deepcopy(good); c["captions"] = [{"lang": "hi", "file": "captions.hi.vtt"}]
print("no English caption:", errors(c))
d = copy.deepcopy(good); del d["chapters"]
print("missing chapters:", errors(d))
EOF
```

- **Expected:** no error for the example; one error place for each broken copy.
- **Actual (verified), exit 0:**

```
example: []
traversal path: ['$.tracks[0].file']
percent-encoded path: ['$.tracks[0].file']
no English caption: ['$.captions']
missing chapters: ['$']
```

- **Implementation:** `contracts/lesson-manifest.v1.schema.json`; vectors in `contracts/test-vectors/relative-path.v1.json`.
- **Test:** `libs/contracts/tests/test_lesson_manifest_v1.py`.
- **Evidence:** PR #32 (base `main`, merged 2026-11-15).
- **Limitations:** structure only. The files a manifest names are not checked to exist (FR-V-08, Release 3). The shapes of `chapters.json`, `slides.json` and `cues.json` have schemas on `main` (#93, merged); this step does not exercise them. No `lesson.json` is produced by anything yet.

### A4. Media paths

- **Objective:** show the shared path rule and the `none` signer (B6.1, B6.4, C-08).
- **Command:**

```bash
PYTHONPATH=libs MEDIA_SIGNING=none MEDIA_BASE_URL=https://media.example.org python - <<'EOF'
from media_paths import create_media_signer, require_slug, validate_relative_path

for p in ["slides/001.jpg", "../720p.mp4", "%2e%2e/720p.mp4", "https://example.org/x.mp4", "a‮b.mp4", "ab.mp4"]:
    print(ascii(p), validate_relative_path(p))
print(create_media_signer().sign("courses/ai-101/01-intro/01-welcome/720p.mp4"))
try:
    create_media_signer().sign("../720p.mp4")
except ValueError as e:
    print("sign refused:", type(e).__name__)
try:
    require_slug("../x", "cohort")
except ValueError as e:
    print("slug refused:", e)
EOF
```

- **Expected:** safe relative path accepted; traversal, percent-encoding, URL and U+202E refused; U+E000 (private use) accepted; a plain media URL built.
- **Actual (verified), exit 0:**

```
'slides/001.jpg' True
'../720p.mp4' False
'%2e%2e/720p.mp4' False
'https://example.org/x.mp4' False
'a‮b.mp4' False
'ab.mp4' True
https://media.example.org/courses/ai-101/01-intro/01-welcome/720p.mp4
sign refused: ValueError
slug refused: cohort must be a slug: lowercase ASCII letters and digits separated by single hyphens (for example 'build-ai-assistant'), got '../x'
```

Optional second command (verified): `MEDIA_SIGNING=hmac MEDIA_BASE_URL=https://media.example.org python -c "from media_paths import create_media_signer; create_media_signer()"`
fails with `MediaSigningConfigError - MEDIA_SIGNING='hmac' is defined in PRD B6.4 but not implemented yet. Use 'none'.`
- **Implementation:** `libs/media_paths/validation.py`, `signing.py`.
- **Test:** `libs/media_paths/tests/test_validation.py`, `test_signing.py`.
- **Evidence:** PRs #84, #85 and #86 (base `main`).
- **Limitations:** the import is `media_paths`, not `libs.media_paths`, which is why `PYTHONPATH=libs` is set (`libs/media_paths/__init__.py` imports its own modules as `media_paths.signing`, so the package must be importable under that name). Only `none` is implemented. Path templates (B6.1 folder builder, merged in #85) are **not** shown here; they are in the D4 demo (section 6). The host is a placeholder.

### A5. B8.5 checker says PENDING

- **Objective:** show that the checker and its tests are real while the data set is honestly not complete.
- **Command:** `python -m pytest -q libs/contracts/tests/test_b8_5_dataset.py`, then `grep -n -m1 "Status" testdata/README.md` and `grep -n "No consent lines" docs/decisions/0004-b8-5-lecture-videos.md`.
- **Expected:** all pass; the two files say PENDING and "No consent lines yet".
- **Actual (verified):** `71 passed` (exit 0); `31:- **Status:** PENDING. Five local recording files were identified in earlier work (PR #99` (the Status line now says five local files are identified and hashed, none is accepted); `57:No consent lines yet.`
- **Implementation:** the checker lives in the test file `libs/contracts/tests/test_b8_5_dataset.py`.
- **Evidence:** PRs #82, #89 and #99 (base `main`).
- **Say clearly:** the passing tests prove that the committed placeholders are well formed and that PENDING is true. They do **not** show a recording, a consent line, a transcript, a word error rate or B8.5 acceptance. None of those is on `main`. Official B8.5 evidence is outside this PR (the audit PR #104, still open, reports on it).
- **Limitations:** decision 0004 records two temporary exceptions (no 1800 s total; four lectures instead of five for interim work), citing the guide's confirmation on issue #121 (PR #125). They are not waivers: the set is complete only with five consented lectures.

### A6. Whole suite and type check

- **Objective:** show the checks CI runs.
- **Commands:** `python -m pytest -q -rs`; `python -m pytest -q .github/scripts/tests`; `pip install mypy && python -m mypy libs`. (Without `requirements.txt` installed, 32 tests fail on Windows for want of `tzdata`.)
- **Expected:** all pass on Linux CI; on Windows one case-insensitivity test fails (see below).
- **Actual (verified locally):** `1 failed, 4103 passed, 5 skipped` (the skips are symbolic-link tests on a Windows host without developer mode). **The pytest run exits 1 locally** because `test_validate_examples.py::test_misnamed_schema_is_reported_with_its_path[Thing.v1.schema.json]` fails on this case-insensitive Windows filesystem (the test writes two files whose names differ only in case; it also failed in revision 2 and is not a repository defect). `88 passed` for the CI-script tests; `Success: no issues found in 56 source files`; both exit 0.
- **Hosted:** the `ci` workflow succeeded on the same commit (report section 5); the symbolic-link tests skipped locally run on Linux CI.
- **Limitations:** do not call the four local skips passing; the Linux CI run is their evidence.

## 2. Part B: not on `main` or not verified (do not demonstrate as working)

| Item | Why it is not demonstrated | Evidence and gap |
|---|---|---|
| `libs/moodle_ws` | Not on `main`; #73 to #78 merged only into stacked branches; #63, #76, #79, #80 open | No lab; App-C 1 not verified; not a Release 0 item after the PRD change |
| `libs/model_interface` skeleton | Open draft #35 (the B5 contract itself is merged, #25) | Partial FR-M-01 only; not Release 0 |
| WER tooling `libs/speech_eval` | Merged (#103), but its `official` mode is refused today | Synthetic tests only; not evidence of any speech model |
| BigBlueButton check script | On `main` (#96), but the records say NOT VERIFIED | No lab run |
| Lesson Processor demo | Open PR #129 (a demonstration, one-PR exception from the guide) | Not on `main`; FR-V-01, FR-V-03, FR-V-08 in part only |

## 3. Requirement mapping

| Step | Requirement | Implementation | Test | PR (base) | Class (report §1) |
|---|---|---|---|---|---|
| A1 | B.0 rule 1, E1, EXT-09 | `libs/contracts/validate_examples.py`, `example_check.py` | `test_validate_examples.py`, `test_example_check.py` | #90, #92, #102 (main) | 1 |
| A2 | B1.1, B1.2 rule 6 (half), B1.4, EXT-09 | `libs/contracts/validate.py`, `course_rules.py` | `test_validate_course.py`, `test_validate_package.py` | #23, #37, #48, #49 (main) | 1 |
| A3 | B6.3, C-08 | `contracts/lesson-manifest.v1.schema.json` | `test_lesson_manifest_v1.py` | #32 (main) | 1 |
| A4 | B6.1 (validation; templates are in D4), B6.4, C-08 | `libs/media_paths/validation.py`, `signing.py` | `test_validation.py`, `test_signing.py` | #84, #85, #86 (main) | 1 |
| A5 | B8.5, App-C 8 (checker only) | `test_b8_5_dataset.py` | same | #82, #89, #99, #125, #126 (main) | 1 (checker); data 5 |
| A6 | E1 | `.github/workflows/ci.yml` | whole suite | n/a | 1 |

## 4. Part C: not demonstrable (PRD §E5)

| E5 step | Needs | Status |
|---|---|---|
| 1 Course Studio writes the sample course; one `.mbz` | Module 1, Release 2 | Not implemented |
| 2 Restore on Moodle; checker 0 errors; five roles | Module 2, lab Moodle, Release 1 | Not implemented; no lab results |
| 3 Upload with interruption; BigBlueButton recording; captions, chapters, slide index; Moodle Page | Module 4, Release 3, lab BBB | Not implemented; BBB not verified (#96). The Lesson Processor demo (#129) shows only upload, 720p conversion, poster and a manifest, on localhost |
| 4 Synthetic submissions drafted, graded, approved; grades after release | Module 3, Release 4 | Not implemented |
| 5 Practice drafts (Release 5, if it exists) | Release 5 | Not implemented |
| 6 G-1 to G-10 with evidence; model comparison | All modules | No measurement exists; G-6 needs a complete B8.5 and a speech provider |

## 5. Rehearsal notes

- Run it once on the presenting machine first; the install needs network once.
- Questions you cannot answer from evidence: lab status, BigBlueButton, word error rate, Moodle
  4.5 versus 5.3 results. Say "not verified yet" and point to report sections 2 and 7.
- Describe the B8.5 exceptions (no 1800 s total; four lectures for interim work) as **temporary and recorded** by the guide's answer on issue #121, never as a completed set.
- #85 and #103 are on `main`. Do not present #35 (open draft) or #129 (open) as part of `main`.

## 5b. Part D: the evaluation demos that exist on `main` (issue #107)

These are separate from steps A1 to A6 and are verified on 2026-11-20 on `origin/main` `5f3a794`.

| Demo | Command | Actual (verified) | Source |
|---|---|---|---|
| D4 video paths | `PYTHONPATH=libs python -B modules/video/demo/paths_demo.py` | Exit 0; every check prints `[ok]`: paths (A), B6.1 templates (B), the `none` signer (C), manifest and folder (D) | `modules/video/demo/README.md`, PR #117 |
| D5 course input | `python scripts/demos/demo_d5_course_input.py` | Exit 0; "RESULT: OK, no errors in the B1 checks that ran (0 errors)", the planted errors are rejected, then `26 examples found, 10 schemas: 26 passed` | `docs/demos/d5-course-input.md`, PR #133 |

D1 (contracts checked by CI) is open as PR #118 (changes requested); D3 (grading) is draft PR #139;
D2 has no PR found. None of those is shown here. Neither D4 nor D5 is B8.5 evidence or a Release 0
acceptance result.

## 6. Provisional status

T19's own acceptance criteria were not found (report section 0). The guide's assistant said on
2026-11-19 to use the provisional criteria P1 to P6 as the working criteria and not to claim to
satisfy T19. This script meets only P2 and P3.

## 7. Validation record (local, 2026-11-20)

Windows 11, Python 3.12.5, fresh virtual environment from `requirements.txt` and
`requirements-dev.txt` plus `mypy`, worktree of `origin/main` `5f3a794` merged with this PR's files.
Local results only; hosted CI is in report section 5.

| Command | Exit | Result |
|---|---|---|
| `python libs/contracts/validate_examples.py` | 0 | 26 passed, 0 failed |
| `python -m pytest -q -rs` | 1 | 1 failed, 4103 passed, 5 skipped: the one failure is the Windows case-insensitive test named in A6; the skips are symbolic links |
| `python -m pytest -q .github/scripts/tests` | 0 | 88 passed |
| `python -m mypy libs` | 0 | no issues in 56 source files |
| `python -m pytest -q libs/contracts/tests/test_b8_5_dataset.py` | 0 | 71 passed |
| Demo steps A1 to A5, D4 and D5 | 0 each | outputs as shown above (A2: the duplicate case now has two errors) |
| Same suite without `requirements.txt` installed | 1 | 32 failed: the B2 time-zone checks need `tzdata`. Installed from `requirements.txt` (the CI job installs it), the suite passes |

`pre-commit` and the secret scan (gitleaks over the whole history) were **not run locally** for this
revision; hosted CI runs both (report section 5). No Markdown linter is configured in this repository.
