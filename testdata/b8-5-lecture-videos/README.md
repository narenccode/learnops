# B8.5 Lecture videos (owner: Student 4), PENDING

At least five short technical lectures in Indian English, approximately 30 minutes in total
(acceptance threshold: at least 1800 s), recorded by the project team for this project (no
faculty or NPTEL recordings). They are used to measure the caption word error rate of the video
pipeline (PRD G-6, App-C 7). The method is the guide's
decision in `docs/decisions/0003-b8-5-lecture-videos.md`. The inventory, one row per lecture, is
the B8.5 table in `testdata/README.md`.

**Status: PENDING.** No lecture has been recorded, no consent has been given and no transcript
has been typed. Every file under `lectures/` is a placeholder. Do not use this set for any
measurement.

## Folder layout

```
testdata/b8-5-lecture-videos/
  README.md
  .gitignore
  lectures/
    lecture-01/
      outline.md
      transcript.en.txt
    lecture-02/
      outline.md
      transcript.en.txt
    lecture-03/
      outline.md
      transcript.en.txt
    lecture-04/
      outline.md
      transcript.en.txt
    lecture-05/
      outline.md
      transcript.en.txt
```

The folder names are the lecture IDs used in the inventory table. Consent lines in the decision
record are per speaker (`speaker-NN`), not per lecture. An ID (`lecture-NN`) stays fixed even if the lecture's title changes.

## What is in Git and what is not

| Item | In Git? | Where |
|---|---|---|
| Outline the speaker talks from | Yes, Apache-2.0 | `lectures/<lecture-id>/outline.md` |
| Reference transcript, typed or corrected by hand and checked by Harshitha | Yes, Apache-2.0 | `lectures/<lecture-id>/transcript.en.txt` |
| Inventory: title, speaker, duration, recording file name, SHA-256, review status | Yes | `testdata/README.md`, B8.5 table |
| Speaker consent lines | Yes | `docs/decisions/0003-b8-5-lecture-videos.md`, `## Consent lines` |
| Video recordings | **No, never** | See "Where recordings are kept" |
| Audio extracted from a recording | **No, never** | See "Where recordings are kept" |
| Any unreviewed transcript draft | **No, never** | Outside Git |

Do not copy recordings or audio into the repository. The root `.gitignore` ignores `*.mp4`,
`*.mov`, `*.mkv` and `*.webm` files and the folders `testdata/media/` and `testdata/downloads/`.
It does **not** ignore audio files (for example `.wav` or `.mp3`) or other video formats (for
example `.avi`). The `.gitignore` in this folder therefore ignores every file here except
`README.md`, `.gitignore`, `lectures/<lecture-id>/outline.md` and
`lectures/<lecture-id>/transcript.en.txt`. It protects this folder only; it does not protect
recordings copied anywhere else in the repository.

## Where recordings are kept

- Until the lab storage is ready, each original recording stays on the computer of the team
  member who recorded it, in a folder that is **not** synced to Google Drive, OneDrive or any
  other cloud service. Check that the folder (for example Documents or Desktop) is not being
  backed up to a cloud service.
- Keep recordings outside the repository folder. Do not share them.
- Move them to the lab storage when it becomes available.
- No storage location, host name, share name, access link or credential is ever written into
  the repository.
- The inventory records only the recording's file name (no folder, no URL).
- Keep the original recording. If a recording is replaced, update the lecture's inventory row
  with the replacement's file name, duration and SHA-256, and say so in the PR.

## Measuring duration and SHA-256

Run these on the stored original recording, where it is kept (see above). `<recording file>` is
the file's real name.

Duration in whole seconds, rounded **down** (so the total is never overstated):

```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "<recording file>"
```

SHA-256, recorded as 64 lowercase hexadecimal characters:

```bash
sha256sum "<recording file>"
```

```powershell
(Get-FileHash -Algorithm SHA256 "<recording file>").Hash.ToLower()
```

Copy both values into the lecture's row in the B8.5 table in `testdata/README.md`. Whoever holds
the original recording can check it later by computing its SHA-256 again and comparing.

## Consent

Every speaker gives written consent before their transcript is published, as **one line per
speaker** in the `## Consent lines` section of `docs/decisions/0003-b8-5-lecture-videos.md`. A
speaker who gives several lectures writes one line. The speaker takes the next free speaker
number and writes their own name and the date (YYYY-MM-DD), with exactly this sentence:

> used to test speech recognition; video stays in the lab; transcript published under Apache-2.0

The line has this form:

```
- speaker-NN: <speaker's name>, <YYYY-MM-DD>: "used to test speech recognition; video stays in the lab; transcript published under Apache-2.0"
```

Each of the speaker's lectures then points to that line in the inventory's Consent column, as
`` `0003` speaker-NN ``; until then the Consent cell says `PENDING`. The name in the line must be
the same as in the inventory's Speaker column. Nobody writes consent for another person.

Before a speaker writes their line, tell them:

- that, until lab storage is ready, the recording stays on the computer of the team member who
  recorded it, in a folder that is not synced or backed up to a cloud service, and is moved to
  lab storage when that becomes available (see "Where recordings are kept");
- that their name and consent line are public in this repository.

## Outlines and transcripts

- **Outline:** written before the recording, as a short list of points. The speaker talks freely
  from it and does not read a prepared text.
- **Transcript:** word for word as spoken, as plain UTF-8 text. It is either typed by hand from
  the recording, or corrected by hand from a draft made by a model that is **not** part of our
  speech-to-text comparison. If a model draft is used, record which model in the PR and in the
  decision record; the draft itself is never committed. Detailed typing rules for the word
  error rate measurement (case, punctuation, fillers, numbers) are not fixed yet; they are
  decided with the first baseline run (App-C 7). Until then, type what is said, in the order it
  is said.
- **Check:** Harshitha (`Harshithamanjunatha`) checks each transcript against its recording. Only
  then does the inventory's Transcript review column change from `pending` to `checked`.

## Pending placeholders and completed entries

| | Pending placeholder | Completed entry |
|---|---|---|
| Inventory row | Title, Speaker, Duration (s), Recording file, SHA-256 and Consent say `PENDING`; review says `pending` | Real values from the recording and the speaker; Consent says `` `0003` speaker-NN ``; review says `checked` |
| `outline.md` | First line starts with `PENDING` | The speaker's outline; no `PENDING` line |
| `transcript.en.txt` | First line starts with `PENDING` | The checked reference transcript; no `PENDING` line |
| Consent line | Not written yet (no line for this speaker) | One line per speaker: their own name, the date (YYYY-MM-DD) and the exact sentence, in the form above |

A file or row that still contains a `PENDING` value is not part of the completed set and must not
be used for any measurement.

## Completion checklist

For each lecture (`lecture-01` … `lecture-05`):

- [ ] `lectures/<lecture-id>/outline.md` holds the speaker's outline (placeholder removed)
- [ ] The lecture is recorded and stored as described in "Where recordings are kept" (folder
      not synced or backed up to a cloud service; not shared)
- [ ] Inventory: title, speaker, Duration (s) and Recording file filled in
- [ ] Inventory: SHA-256 filled in
- [ ] The speaker was told about the interim storage, then wrote their own consent line (once per
      speaker); the inventory's Consent cell points to it as `` `0003` speaker-NN ``
- [ ] `lectures/<lecture-id>/transcript.en.txt` typed or corrected by hand (placeholder removed)
- [ ] Transcript checked by Harshitha; inventory says `checked`

For the set:

- [ ] At least five lectures complete
- [ ] Total recorded duration at least 1800 s (the acceptance threshold for "approximately
      30 minutes"), written on the inventory's total line
- [ ] Only then: the Status lines in `testdata/README.md` and in this README change from `PENDING`
      to `COMPLETE`
- [ ] The B8.5 validation test passes: `python -m pytest -q libs/contracts/tests/test_b8_5_dataset.py`
      (added in the same PR as this README)
- [ ] `git ls-files testdata/b8-5-lecture-videos` lists only `README.md`, `.gitignore`,
      `outline.md` and `transcript.en.txt` files

## Licence

The outlines and reference transcripts in this folder are licensed under Apache-2.0, as the
repository (see `LICENSE`). The recordings are not published and are not shared.
