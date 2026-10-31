# B8.5 — Lecture Test Dataset

## Decision

The team will create its own lecture test dataset for Release 0.

- Record at least five short technical lectures in Indian English.
- Total recording duration: approximately 30 minutes. The acceptance threshold is a total of at least 1800 seconds.
- Speakers will speak naturally from an outline rather than read a script.
- Each speaker must provide their own written consent line.
- Transcripts will be typed manually or corrected from a model outside the speech-recognition comparison.
- Harshitha will review the reference transcripts.
- Original recordings will remain private and outside Git.
- Approved transcripts will be published under Apache-2.0.

## Recording storage

Until lab storage is ready, recordings will remain on individual team members' computers in folders that are not synced to Google Drive, OneDrive or any other cloud service. Each team member checks that the folder (for example Documents or Desktop) is not being backed up to a cloud service.

Recordings must not be shared or committed to Git. They will be moved to lab storage when it becomes available. No link to any storage location is written in the repository.

## Consent statement

Each speaker must provide a consent line containing their name, date, and the following exact statement:

> used to test speech recognition; video stays in the lab; transcript published under Apache-2.0

Before a speaker writes their consent line, they are told that, until lab storage is ready, the recording stays on the computer of the team member who recorded it, in a folder that is not synced or backed up to a cloud service, and that it is moved to lab storage when that becomes available. They are also told that their name and consent line are public in this repository.

## Dataset completion criteria

The dataset is considered complete when:

- At least five lecture recordings are available.
- Total recording duration is approximately 30 minutes or more, that is, at least 1800 seconds.
- Reference transcripts have been prepared and reviewed.
- Required speaker consent lines are documented.

## Consent lines

One line per speaker, written by that speaker. A speaker who gives more than one lecture writes one line. The speaker takes the next free speaker number and writes their own name, the date (YYYY-MM-DD) and the exact statement above, in this form:

`- speaker-NN: <speaker's name>, <YYYY-MM-DD>: "used to test speech recognition; video stays in the lab; transcript published under Apache-2.0"`

Each lecture's row in the B8.5 inventory (`testdata/README.md`) points to its speaker's line as `0003` speaker-NN. Nobody writes a consent line for another person.

No consent lines yet.
