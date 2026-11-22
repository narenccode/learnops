# Data map (PRD E6)

| Module | Data item | Stored where | Sent to | Kept for | Why |
|---|---|---|---|---|---|
| Repository tooling | Pull-request title, description and diff (public, test data only) | GitHub | DeepSeek API (third-party model provider; not under our control) | Per DeepSeek's retention terms | Automated PR review (`.github/workflows/pr-review.yml`) |
| Video pipeline (M4) | Uploader's LTI `sub` (lesson manifest `source.uploaded_by`, PRD B6.3): a pseudonymous identifier, personal data that LTI provides (SEC-06) | The manifest (`lesson.json`) inside the published lesson folder, in the media store (B6.2, FR-V-12) | No third party; read by the LearnOps modules that read the B6.3 manifest | Kept with that folder; the folder is never deleted automatically; the CLI removes lessons older than a configured age only after confirmation, default off (FR-V-15); on reprocessing the previous outputs stay until the new ones are complete (FR-V-11), and their later removal is not specified | Records which LTI user uploaded the lesson's source (B6.3 `source`) |
| Test data B8.5 (Video, Student 4) | Lecture video recordings and any audio extracted from them: the voice and face of real people (team members who speak) | Until lab storage is ready: the computer of the team member who recorded it, in a folder outside the repository that is not synced or backed up to any cloud service. Afterwards: moved to lab storage, which only the team and the guide may reach, with no public link (decision 0011). Never in Git; no storage location or link is written in the repository (decision 0004) | Nobody: recordings are not shared (decision 0004). Only the lab endpoint inside the lab receives the audio for the measurement; no hosted service (decision 0011). What the endpoint keeps is **not recorded yet** (decision 0002); it is deleted after the run | Until the last measurement that uses B8.5 is recorded, including the caption word error rate for the Release 3 acceptance (PRD C4.7); then the person who recorded deletes their local copies and Student 4 deletes the lab copies and scratch files, and the deletion is recorded in the evidence; if the project ends first, delete then (decision 0011) | Measure the caption word error rate on Indian-English lectures (PRD G-6, App-C 7; data set PRD B8.5) |
| Test data B8.5 (Video, Student 4) | Speaker's name and consent date, in the consent lines (`docs/decisions/0004-b8-5-lecture-videos.md`, `## Consent lines`) and the inventory's Speaker column (`testdata/README.md`) | This Git repository | Public: anyone who can read the repository. Speakers are told this before they write their line (decision 0004) | Stays in the repository as the public consent record. If a speaker withdraws, the name is removed from the current tree and the withdrawal is recorded; Git history keeps the earlier version and is not rewritten (decision 0011) | Record each speaker's own written consent (PRD B8.5, App-C 8) |
| Test data B8.5 (Video, Student 4) | Reference transcripts (the speaker's words as spoken) and outlines | This Git repository (`testdata/b8-5-lecture-videos/lectures/`) | Public, under Apache-2.0 (the consent sentence says so) | Stays in the repository as the public consent record; on withdrawal the speaker's transcript is removed from the current tree and the withdrawal is recorded; Git history is not rewritten (decision 0011) | Reference text for the caption word error rate (PRD G-6) |
| Test data B8.5 (Video, Student 4) | Unreviewed transcript drafts, only if a model drafts a transcript | Outside Git (never committed) | The drafting model, if one is used; which model is recorded in the PR and the decision record. No hosted service receives B8.5 audio (decision 0011) | Only until the last measurement that uses B8.5 is recorded (including the Release 3 acceptance measurement), then deleted (decision 0011) | Starting point for a hand-corrected reference transcript |

### B8.5: the four questions, answered by decision 0011

The guide answered these on 2026-11-19 and confirmed them, with two amendments, on 2026-11-20; the answers are recorded in
`docs/decisions/0011-b8-5-data-handling.md`; the rows above follow that record.

1. **Retention and deletion of recordings:** kept until the last measurement that uses B8.5 is
   recorded, including the Release 3 caption word error rate (PRD C4.7); then the recorder deletes local copies, Student 4 deletes lab copies and
   scratch files, and the deletion is recorded in the evidence.
2. **Lab storage access:** only the team and the guide; no public link; the location stays out of
   the repository.
3. **Names and transcripts in the repository:** they stay as the public consent record; a withdrawal
   removes the speaker from the current tree, is recorded, and Git history is not rewritten.
4. **Processing services:** only the lab endpoint inside the lab; no hosted service; what it keeps is
   recorded (not yet) and deleted after the run.
