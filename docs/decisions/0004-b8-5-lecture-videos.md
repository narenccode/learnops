# B8.5 — Lecture Test Dataset

## Decision

The team will create its own lecture test dataset for Release 0.

- Record at least five short technical lectures in Indian English.
- Total recording duration: approximately 30 minutes. The acceptance threshold is a total of at least 1800 seconds.
- Speakers will speak naturally from an outline rather than read a script.
- Each speaker must provide their own written consent line.
- Transcripts will be typed manually or corrected from a model outside the speech-recognition comparison.
- Harshitha reviews lectures 01, 03, 04 and 05; Nagashree reviews lecture 02 (its speaker is Harshitha); acknowledged by the guide ([issue #186](https://github.com/narenccode/learnops/issues/186#issuecomment-7101984198)).
- Original recordings will remain private and outside Git.
- Approved transcripts will be published under Apache-2.0.

## Recording storage

Until lab storage is ready, recordings will remain on individual team members' computers in folders that are not synced to Google Drive, OneDrive or any other cloud service. Each team member checks that the folder (for example Documents or Desktop) is not being backed up to a cloud service.

Recordings must not be shared or committed to Git. They will be moved to lab storage when it becomes available. No link to any storage location is written in the repository.

## Consent statement

Each speaker must provide a consent line containing their name, date, and the following exact statement:

> used to test speech recognition; video stays in the lab; transcript published under Apache-2.0

Before a speaker writes their consent line, they are told that, until lab storage is ready, the recording stays on the computer of the team member who recorded it, in a folder that is not synced or backed up to a cloud service, and that it is moved to lab storage when that becomes available. They are also told that their name and consent line are public in this repository, and that if they withdraw, a withdrawal removes the name from the current files but older versions stay in Git history.

## Dataset completion criteria

The dataset is considered complete when:

- At least five lecture recordings are available.
- Total recording duration is approximately 30 minutes or more, that is, at least 1800 seconds.
- Reference transcripts have been prepared and reviewed.
- Required speaker consent lines are documented.

## Temporary exception: minimum total duration

The guide has approved, for now, that the current B8.5 dataset work does not need to reach the 1800 second total. This is a temporary exception, not a permanent removal of the requirement, and no other minimum is set in its place. The exception covers only the minimum total duration. Every recording's duration is still measured with `ffprobe` and recorded correctly, the other completion criteria still apply, and the dataset is not complete until they are met.

Approval reference: the guide confirmed it in his own words on issue #121 on 2026-11-20 ([comment](https://github.com/narenccode/learnops/issues/121#issuecomment-7053492287)). The date of the earlier approval is not recorded.

## Temporary exception: minimum number of lectures

The guide has approved, for now, that the interim demonstration and testing work may proceed with four lecture recordings instead of five, ideally from four different speakers. This is a temporary exception, not a permanent removal of the requirement: the dataset is not complete until five recordings exist, every other completion criterion still applies, and no other minimum is set in its place. The five-lecture minimum in PRD B8.5 and in the completion criteria above is unchanged.

Approval reference: the guide's own-words confirmation on issue #121 of 2026-11-20 ([comment](https://github.com/narenccode/learnops/issues/121#issuecomment-7053492287)), which covers both exceptions.

## Consent lines

One line per speaker, written by that speaker. A speaker who gives more than one lecture writes one line. The speaker takes the next free speaker number and writes their own name, the date (YYYY-MM-DD) and the exact statement above, in this form:

`- speaker-NN: <speaker's name>, <YYYY-MM-DD>: "used to test speech recognition; video stays in the lab; transcript published under Apache-2.0"`

Each lecture's row in the B8.5 inventory (`testdata/README.md`) points to its speaker's line as `0004` speaker-NN. Nobody writes a consent line for another person.

- speaker-01: Akshita, 2026-11-23: "used to test speech recognition; video stays in the lab; transcript published under Apache-2.0"
- speaker-02: Harshitha, 2026-11-23: "used to test speech recognition; video stays in the lab; transcript published under Apache-2.0"
- speaker-03: Nagashree V, 2026-11-23: "used to test speech recognition; video stays in the lab; transcript published under Apache-2.0"
- speaker-04: Shraddha, 2026-11-23: "used to test speech recognition; video stays in the lab; transcript published under Apache-2.0"

## How the transcripts were made

All five reference transcripts were typed by hand by the speaker of that lecture (statement of the owner, Student 4). No
model draft was used, so no model is recorded. Lecture 02 (speaker Harshitha) was checked by Nagashree V; the other four
were checked by Harshitha. The guide acknowledged this on 23 November 2026 (see the line above and the link there): nobody checks their own
transcript.
