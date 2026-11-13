# Data map (PRD E6)

| Module | Data item | Stored where | Sent to | Kept for | Why |
|---|---|---|---|---|---|
| Repository tooling | Pull-request title, description and diff (public, test data only) | GitHub | DeepSeek API (third-party model provider; not under our control) | Per DeepSeek's retention terms | Automated PR review (`.github/workflows/pr-review.yml`) |
| Test data B8.5 (Video, Student 4) | Lecture video recordings and any audio extracted from them: the voice and face of real people (team members who speak) | Until lab storage is ready: the computer of the team member who recorded it, in a folder outside the repository that is not synced or backed up to any cloud service. Afterwards: moved to lab storage. Never in Git; no storage location or link is written in the repository (decision 0004) | Nobody: recordings are not shared (decision 0004). Which speech-to-text services process them for the measurement is **not decided** (question 4 below) | **Not decided** (questions 1 and 2 below) | Measure the caption word error rate on Indian-English lectures (PRD G-6, App-C 7; data set PRD B8.5) |
| Test data B8.5 (Video, Student 4) | Speaker's name and consent date, in the consent lines (`docs/decisions/0004-b8-5-lecture-videos.md`, `## Consent lines`) and the inventory's Speaker column (`testdata/README.md`) | This Git repository | Public: anyone who can read the repository. Speakers are told this before they write their line (decision 0004) | **Not decided** (question 3 below). Removing a name from the files later does not remove it from Git history | Record each speaker's own written consent (PRD B8.5, App-C 8) |
| Test data B8.5 (Video, Student 4) | Reference transcripts (the speaker's words as spoken) and outlines | This Git repository (`testdata/b8-5-lecture-videos/lectures/`) | Public, under Apache-2.0 (the consent sentence says so) | **Not decided** (question 3 below) | Reference text for the caption word error rate (PRD G-6) |
| Test data B8.5 (Video, Student 4) | Unreviewed transcript drafts, only if a model drafts a transcript | Outside Git (never committed) | The drafting model, if one is used; which model is recorded in the PR and the decision record | **Not decided** (question 1 below) | Starting point for a hand-corrected reference transcript |

### B8.5: open questions for the guide

The PRD, decision 0004 and the B8.5 READMEs do not answer these yet. No row above may claim an
answer until the guide decides, and the decision is recorded in `docs/decisions/`.

1. **Retention and deletion of recordings.** How long are recordings, extracted audio and any
   transcript drafts kept, and who deletes them, how and when? This covers both the copies on
   team members' computers after they move to lab storage, and the lab copies once the
   measurement is done or the project ends.
2. **Lab storage access.** Which lab storage is used, and who may access it? (Decision 0004 keeps
   the location itself out of the repository; this entry would describe who may access it, not
   where it is.)
3. **Names and transcripts in the repository.** How long are speaker names, consent lines and
   published transcripts kept, and what happens if a speaker withdraws consent, given that Git
   history keeps earlier versions?
4. **Processing services.** Which speech-to-text services (for example the lab AI services,
   PRD C-12) receive the recordings or their audio for the comparison, and do they keep them?
