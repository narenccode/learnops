# Test data (PRD B8)

Record the source and the licence or consent for every data set here.

## B8.5 Lecture videos (owner: Student 4), PENDING

- **Where:** `b8-5-lecture-videos/` (folder layout, recording and hashing steps, and the
  completion checklist in its README). The inventory table below is the only list of lectures.
- **Status:** PENDING. No lecture has been recorded, no consent has been given and no transcript
  has been typed. The set is **not complete** and must not be used for any measurement yet.
- **Method (guide decision, recorded in `docs/decisions/0003-b8-5-lecture-videos.md`):**
  - at least **5** short technical lectures in **Indian English**, together approximately
    **30 minutes** of recording; the acceptance threshold is a total of at least **1800 s**;
  - recorded by the project team for this project (no faculty or NPTEL recordings); each
    speaker speaks naturally from an outline, not from a script;
  - every speaker writes one consent line (one per speaker, even for several lectures) with
    their own name, the date, and exactly this sentence: "used to test speech recognition; video stays in the lab; transcript published under Apache-2.0";
  - reference transcripts are typed by hand, or corrected by hand from a draft made by a model
    that is not part of our speech-to-text comparison; Harshitha (`Harshithamanjunatha`) checks
    every transcript.
- **Licence:** the published outlines and reference transcripts are Apache-2.0, like the
  repository. The recordings are not published and have no public licence.
- **Stays out of Git:** the video recordings, any audio extracted from them, and any unreviewed
  or model-made transcript draft. They are kept as described in "Original recording storage"
  below. Only outlines and reviewed reference transcripts are committed.
- **PRD note:** PRD §B8 still says "≥ 3 h total". The guide is changing it to 30 minutes; until
  that PRD change is merged, this set follows the guide's decision, not the current PRD text.

### Original recording storage

- Until the lab storage is ready, each original recording stays on the computer of the team
  member who recorded it, in a folder that is **not** synced to Google Drive, OneDrive or any
  other cloud service. Check that the folder (for example Documents or Desktop) is not being
  backed up to a cloud service.
- Keep recordings outside the repository folder. Do not share them.
- Move them to the lab storage when it becomes available.
- No link to any storage location is written in this repository.
- Tell each speaker about this interim storage before they write their consent line.

What Git ignores, as checked with `git check-ignore`: the root `.gitignore` ignores `*.mp4`,
`*.mov`, `*.mkv` and `*.webm` files and the folders `testdata/media/` and `testdata/downloads/`
anywhere in the repository, but **not** audio files (for example `.wav`, `.mp3` or `.m4a`) or
other video formats (for example `.avi`). Inside `testdata/b8-5-lecture-videos/` only, a folder
`.gitignore` ignores every file except `README.md`, `.gitignore`, `outline.md` and
`transcript.en.txt`.

### Inventory

Values are filled in only from the real recording, the speaker's own consent and the reviewed
transcript. `PENDING` means not known yet. The validation test added with this set
(`libs/contracts/tests/test_b8_5_dataset.py`) reads this table, so keep its structure fixed:

- the ten columns, in this order and with these exact header names;
- one row per lecture; the ID is `lecture-NN` (two digits);
- **Duration (s):** whole seconds (an integer), or `PENDING`;
- **Recording file:** the file name only (no folder, no URL), or `PENDING`;
- **SHA-256:** 64 lowercase hexadecimal characters, or `PENDING`;
- **Outline / Transcript:** paths relative to `testdata/`, in backticks;
- **Consent:** `PENDING` until the lecture's speaker has a consent line in the decision record,
  then `` `0003` speaker-NN `` (that speaker's line; several lectures may share it);
- **Transcript review:** `pending` until Harshitha has checked the transcript, then `checked`.

The **Status** line above says `PENDING` until every row is complete; then it says `COMPLETE`.
The test fails if the status says `COMPLETE` while anything is missing, and also if the data is
complete but the status still says `PENDING`.

| ID | Title | Speaker | Duration (s) | Recording file (lab only) | SHA-256 | Outline | Transcript | Consent | Transcript review |
|---|---|---|---|---|---|---|---|---|---|
| lecture-01 | PENDING | PENDING | PENDING | PENDING | PENDING | `b8-5-lecture-videos/lectures/lecture-01/outline.md` | `b8-5-lecture-videos/lectures/lecture-01/transcript.en.txt` | PENDING | pending |
| lecture-02 | PENDING | PENDING | PENDING | PENDING | PENDING | `b8-5-lecture-videos/lectures/lecture-02/outline.md` | `b8-5-lecture-videos/lectures/lecture-02/transcript.en.txt` | PENDING | pending |
| lecture-03 | PENDING | PENDING | PENDING | PENDING | PENDING | `b8-5-lecture-videos/lectures/lecture-03/outline.md` | `b8-5-lecture-videos/lectures/lecture-03/transcript.en.txt` | PENDING | pending |
| lecture-04 | PENDING | PENDING | PENDING | PENDING | PENDING | `b8-5-lecture-videos/lectures/lecture-04/outline.md` | `b8-5-lecture-videos/lectures/lecture-04/transcript.en.txt` | PENDING | pending |
| lecture-05 | PENDING | PENDING | PENDING | PENDING | PENDING | `b8-5-lecture-videos/lectures/lecture-05/outline.md` | `b8-5-lecture-videos/lectures/lecture-05/transcript.en.txt` | PENDING | pending |

**Total recorded duration:** PENDING

How the total is calculated: the sum of the `Duration (s)` column, where each duration is the
recording's length measured with `ffprobe` and rounded **down** to whole seconds (so the total is
never overstated). The set needs a total of at least 1800 s. Write it as `<seconds> s (<m> min <s> s)`,
for example `1834 s (30 min 34 s)`.
