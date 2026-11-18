# Release 0 demonstration script (T19, revision 2)

> **Update 2026-11-18 (the facts below are stale where they conflict):** PR #96 was **merged** on 2026-11-16 (approved by Harshithamanjunatha, Shraddha and Akshita21-09) and is the carrier of decisions `0005`/`0006` and `verify_bbb.py`. PR #97 was **closed as superseded by #96**: its ADR, README and run record are identical to `main`, its older `verify_bbb.py` is replaced by #96's, and its traceability section is already on `main`. The `0005` numbering collision therefore no longer exists. App-C 4 is **still NOT VERIFIED**: no lab observation exists, so nothing here is a PASS.

**Length:** about 12 minutes. **Needs:** Python 3.12 and a POSIX shell (Git Bash on Windows). No
lab, no Moodle, no BigBlueButton, no AI or speech service, and no network after the install.
**Checked against:** `origin/main` at `3abbc02`. Every "Actual" result below was produced by running
the command on 2026-11-16 (Windows 11, Python 3.12.5), then compared with the hosted CI run on the
same commit (`docs/release-0/report.md` section 5).

This is **not** the PRD §E5 final demonstration, which needs Releases 1 to 4 and fresh lab sites.
Section 4 lists what is not demonstrable and why. The demo makes no claim about BigBlueButton, a
word error rate, B8.5 acceptance or Moodle (report section 9).

## 1. Part A: current executable demonstration

### Set up (once, from a clone of `main`)

```bash
git clone https://github.com/narenccode/learnops.git && cd learnops
python -m venv .venv && . .venv/bin/activate          # Windows Git Bash: . .venv/Scripts/activate
pip install -r requirements-dev.txt
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
- **Expected:** three examples pass, exit code 0.
- **Actual (verified):** `3 examples found, 2 schemas: 3 passed, 0 failed, 0 not validated; 0 problems found.` Exit 0.
- **Implementation:** `libs/contracts/validate_examples.py`, `libs/contracts/example_check.py`.
- **Test:** `libs/contracts/tests/test_validate_examples.py`, `test_example_check.py`.
- **Evidence:** PRs #90 and #102 (base `main`). #91 merged only into a stacked branch and was replaced by #102. CI runs this step on every PR.
- **Limitations:** only B1 and B6.3 have schemas on `main`. A dangling `$ref` that no example reaches is not found; `date` is checked, `date-time` is not.

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

- **Expected:** the example passes; each planted package fails with one error.
- **Actual (verified), exit 0:**

```
example package: ok=True errors=0 not_checked=8
planted protected idnumber: ok=False errors=1 not_checked=10
  - sections[0].activities[0].idnumber: 'final-project' is a protected idnumber and cannot be used in a package.
planted duplicate idnumber: ok=False errors=1 not_checked=8
  - sections[0].activities[1].idnumber: the idnumber 'wk-01-guide' is already used at sections[0].activities[0].idnumber. Idnumbers must be unique in the course.
```

- **Say:** "not_checked" is deliberate: the validator lists rules it does not enforce, so "no errors" is never read as "fully checked". In the protected-idnumber case it reports 10, because a schema error holds the idnumber rules back.
- **Implementation:** `libs/contracts/validate.py`, `course_rules.py`, `source.py`, `config.py`, `report.py`.
- **Test:** `test_validate_course.py`, `test_validate_package.py`, `test_config.py`, `test_report.py`, `test_course_package_v1.py`.
- **Evidence:** PRs #23, #37, #48, #49 (base `main`).
- **Limitations:** idnumber reuse across package versions is not checked (`idnumber_reuse_not_checked`). This is not FR-S-03 or FR-C-03; the checker rules need the B2 course model, which is an open PR (#46). Several B1 changes are open (#87, #94, #101).

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
- **Limitations:** structure only. The files a manifest names are not checked to exist (FR-V-08, Release 3). The shapes of `chapters.json`, `slides.json` and `cues.json` have no schema on `main` (open #93). No `lesson.json` is produced by anything yet.

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
- **Evidence:** PRs #84 and #86 (base `main`).
- **Limitations:** the import is `media_paths`, not `libs.media_paths`, which is why `PYTHONPATH=libs` is set (`libs/media_paths/__init__.py` imports its own modules as `media_paths.signing`, so the package must be importable under that name). Only `none` is implemented. Path templates (B6.1 folder builder) are open PR #85 and are **not** shown. The host is a placeholder.

### A5. B8.5 checker says PENDING

- **Objective:** show that the checker and its tests are real while the data set is honestly not complete.
- **Command:** `python -m pytest -q libs/contracts/tests/test_b8_5_dataset.py`, then `grep -n -m1 "Status" testdata/README.md` and `grep -n "No consent lines" docs/decisions/0004-b8-5-lecture-videos.md`.
- **Expected:** all pass; the two files say PENDING and "No consent lines yet".
- **Actual (verified):** `71 passed` (exit 0); `21:- **Status:** PENDING. No lecture has been recorded, no consent has been given and no transcript`; `53:No consent lines yet.`
- **Implementation:** the checker lives in the test file `libs/contracts/tests/test_b8_5_dataset.py`.
- **Evidence:** PRs #82, #89 and #99 (base `main`).
- **Say clearly:** the passing tests prove that the committed placeholders are well formed and that PENDING is true. They do **not** show a recording, a consent line, a transcript, a word error rate or B8.5 acceptance. None of those is on `main`. Official B8.5 evidence is outside this PR (the open audit PR #104 reports on it).
- **Limitations:** the temporary 1800 s exception in decision 0004 has no approval reference.

### A6. Whole suite and type check

- **Objective:** show the checks CI runs.
- **Commands:** `python -m pytest -q -rs`; `python -m pytest -q .github/scripts/tests`; `pip install mypy && python -m mypy libs`.
- **Expected:** all pass.
- **Actual (verified locally):** `2038 passed, 4 skipped` (the skips are symbolic-link tests on a Windows host without developer mode); `137 passed`; `Success: no issues found in 30 source files`. All exit 0.
- **Hosted:** CI on the same commit reported `2042 passed` and "All three symlink tests passed" (report section 5).
- **Limitations:** do not call the four local skips passing; the Linux CI run is their evidence.

## 2. Part B: implemented but unverified (do not demonstrate as working)

| Item | Why it is not demonstrated | Evidence and gap |
|---|---|---|
| Path templates (B6.1 folder builder) | Open PR #85, not on `main` | Review state: approved, `needs-judgement` |
| `libs/moodle_ws` | Not on `main`; #73 to #78 merged only into stacked branches | No lab; App-C 1 not verified |
| `libs/model_interface` skeleton | Open draft #35, stacked on #25 | Partial FR-M-01 only |
| WER tooling `libs/speech_eval` | Open draft #103; its `official` mode is refused | Synthetic tests only; not evidence of any speech model |
| BigBlueButton check script | Open #96, #97, records say NOT VERIFIED | No lab run |

## 3. Requirement mapping

| Step | Requirement | Implementation | Test | PR (base) | Class (report §1) |
|---|---|---|---|---|---|
| A1 | B.0 rule 1, E1, EXT-09 | `libs/contracts/validate_examples.py`, `example_check.py` | `test_validate_examples.py`, `test_example_check.py` | #90, #102 (main) | 1 |
| A2 | B1.1, B1.2 rule 6 (half), B1.4, EXT-09 | `libs/contracts/validate.py`, `course_rules.py` | `test_validate_course.py`, `test_validate_package.py` | #23, #37, #48, #49 (main) | 1 |
| A3 | B6.2, B6.3, C-08 | `contracts/lesson-manifest.v1.schema.json` | `test_lesson_manifest_v1.py` | #32 (main) | 1 |
| A4 | B6.1 (validation only), B6.4, C-08 | `libs/media_paths/validation.py`, `signing.py` | `test_validation.py`, `test_signing.py` | #84, #86 (main) | 1 |
| A5 | B8.5, App-C 8 (checker only) | `test_b8_5_dataset.py` | same | #82, #89, #99 (main) | 1 (checker); data 5 |
| A6 | E1 | `.github/workflows/ci.yml` | whole suite | n/a | 1 |

## 4. Part C: not demonstrable (PRD §E5)

| E5 step | Needs | Status |
|---|---|---|
| 1 Course Studio writes the sample course; one `.mbz` | Module 1, Release 2 | Not implemented |
| 2 Restore on Moodle; checker 0 errors; five roles | Module 2, lab Moodle, Release 1 | Not implemented; no lab results |
| 3 Upload with interruption; BigBlueButton recording; captions, chapters, slide index; Moodle Page | Module 4, Release 3, lab BBB | Not implemented; BBB not verified (#96, #97) |
| 4 Synthetic submissions drafted, graded, approved; grades after release | Module 3, Release 4 | Not implemented |
| 5 Practice drafts (Release 5, if it exists) | Release 5 | Not implemented |
| 6 G-1 to G-10 with evidence; model comparison | All modules | No measurement exists; G-6 needs a complete B8.5 and a speech provider |

## 5. Rehearsal notes

- Run it once on the presenting machine first; the install needs network once.
- Questions you cannot answer from evidence: lab status, BigBlueButton, word error rate, Moodle
  4.5 versus 5.3 results. Say "not verified yet" and point to report sections 2 and 7.
- Do not describe the B8.5 1800 s exception as approved.
- Do not present #85, #103 or #35 code as part of `main`.

## 6. Provisional status

T19's own acceptance criteria were not found (report section 0). This script meets only the
provisional criteria P2 and P3.

## 7. Validation record (local, 2026-11-16)

Windows 11, Python 3.12.5, fresh virtual environment from `requirements-dev.txt` plus `mypy` and
`pre-commit`, clean worktree of `origin/main` plus this PR's three files. Local results only;
hosted CI is in report section 5.

| Command | Exit | Result |
|---|---|---|
| `SKIP=no-commit-to-branch,gitleaks pre-commit run --all-files` | 0 | All hooks passed (check yaml, check json, end of files, trailing whitespace, large files, private key, ruff, ruff-format). `gitleaks` and `no-commit-to-branch` were skipped by the `SKIP` setting |
| `python libs/contracts/validate_examples.py` | 0 | 3 passed, 0 failed |
| `python -m pytest -q -rs` | 0 | 2038 passed, 4 skipped (symbolic links) |
| `python -m pytest -q .github/scripts/tests` | 0 | 137 passed |
| `python -m mypy libs` | 0 | no issues in 30 source files |
| `python -m pytest -q libs/contracts/tests/test_b8_5_dataset.py` | 0 | 71 passed |
| Demo steps A1 to A5 | 0 each | outputs as shown above |

No Markdown linter is configured in this repository, so none was run; the pre-commit hooks above
are the documentation checks. The secret scan (gitleaks over the whole history) was **not run
locally**; hosted CI ran it successfully on `3abbc02`.
