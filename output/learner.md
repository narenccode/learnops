# Learner: what went wrong, what fixed it, what to do next time

**For:** Nagashree V (`vnaags`), Video module owner. **Covers:** the first design document (PR #17, 25 Oct 2026) to the last merge (#198, #194, 23 Nov 2026).
**Status of this file:** a private learning record in the local `output` folder. It is not in Git and not a repository document.

**How to read it.** Each entry says what happened, how it was fixed, and the rule behind it. Reviewers and the guide caught most of these, and that is what the review process is for. **Some of the slips were made by the assistant working under your account** (for example in #105 and #198). They are marked "(assistant)", because the lesson is the same whoever types: you own what goes out under your name, so you check it. Every item comes from PR history, review comments, the guide's answers or CI results. I did not invent any. Where I am unsure of the reason, I say so.

---

## 1. The one-page version

1. **Evidence before words.** A document line must never run ahead of reviewed evidence. Most of the corrections below were a status, a count or a date that was wrong or stale.
2. **Build in the order the rules say.** Contracts, then design, then the guide's approval, then feature code. The demo (#129) needed an explicit guide exception because it came first.
3. **Small, built on `main`, one thing per PR.** Big PRs, stacked PRs and mixed content slowed every review.
4. **Verify what you cite.** References, PR states, dates and numbers are checked against the source, not remembered.
5. **After every merge, find the sentences that just became false.** Four separate refresh PRs (#154, #163, #198, #126) exist because the documents were not updated in the PR that changed the facts.
6. **A push cancels approvals.** Check state before pushing to an approved PR, and do not use "Update branch" casually.
7. **Say what is a statement and what is verified.** "The owner states" and "verified" are different words with different weight.

---

## 2. What happened, step by step

### 2.1 Design document (PRs #17, #24, #28, #29, #34, #140)
| What happened | Fix | Learning |
|---|---|---|
| Two revised drafts (#28, #29) were closed unmerged, and the design needed repeated updating (#24, #34) | A single complete draft with the guide's questions Q1 to Q16 (#140); the guide answered and the answers are recorded | **Put every open question to the guide in one numbered list**, each with the options and a recommendation. That produced all the decisions at once. Draft with question numbers from the start |
| Stale facts stayed in the draft (PR states, "open" PRs, counts) | Refreshed in #140 and again in #198 | A design document is a snapshot: **date every status table**, and mark old rows "historical" |
| Status gates: the design stays `Draft` until the guide sets `Approved` | Still pending | **Do not tick "I understand every section" until you have read all of it.** It is a personal statement |

### 2.2 Contracts and shared library (B6: #32, #38, #84, #85, #86, #93)
| What happened | Fix | Learning |
|---|---|---|
| The first combined media-path PR (#38) was closed; the work later went in as three small PRs (#84, #85, #86). I believe the split was the reason, but I did not check | Merged separately, one concern each | **One concern per PR** |
| #93 depended on another PR (#90): the guide set the merge order and asked for the `error_order` rename in #93 | #93 imported `error_order` after #90 merged | **Check dependencies before opening a PR** and say the order in its description. Shared helpers keep one name |
| The `awaiting-owners` label on #93 confused people | The guide explained the bot adds it to every contract PR | **Read the reviews on the head, not the label** |
| A contract lives in three places: schema, examples and PRD text | Done in #93 | Contract PRs change all of them together (PRD B.0) |

### 2.3 B8.5 lecture dataset (#43, #82, #89, #99, #104, #125, #126, #154, #169)
| What happened | Fix | Learning |
|---|---|---|
| The first dataset PR (#43) was closed | Rebuilt as a checker first (#82, #89), then evidence (#99) | Build the **checker and tests first**, then the data |
| Recording evidence was labelled too confidently, so a correction PR was needed (#126). Hash and duration values were written before they were measured; unverified hashes were removed and the placeholders put back (commits `9b94943`, `9c6d703`) | #154 recorded only the five `ffprobe`-measured durations | **Never fill a value you did not measure.** Leave `PENDING` and say why. The checker enforces this |
| Five short clips (338 s) were treated as the dataset. They were never accepted | Replaced by the five real lectures in #169 | **Say clearly which files are the official set**, in writing, early (audit gap G-8) |
| Consent lines were first sent in the wrong form: wrong sentence, wrong date, missing colon | You corrected them until they were exact, each speaker writing their own | **Copy the required sentence exactly**; consent is the speaker's own line, with a date. The test checks the form |
| Names, consent and transcripts are public by design (decisions 0011, 0004) | Speakers were told before writing | **Brief speakers first**, including that withdrawal removes the name from the current tree but Git history keeps earlier versions |
| #169's first review asked for three things: headings still said PENDING, the checklist was unticked, and how the transcripts were made was not stated | Fixed (`bddd28c`, `cde0205`) | After changing a status, **search the whole file for the old word** and state how each artefact was made |
| #169 was about 1,040 lines, over the 800 aim | Accepted with a file map | The guide allows a size exception only with a **reason and a file map** |
| Tests that expected PENDING failed when the set became COMPLETE | Tests and G-6 docs updated | If a test or doc says "still pending", **plan the follow-up** when the thing completes |

### 2.4 Lesson Processor demo (#117, #119, #129)
| What happened | Fix | Learning |
|---|---|---|
| The D4 paths demo (#117) was merged, then a revert (#119) was opened and closed | Kept #117 | Decide before merging; reverts add noise |
| #129 was a **Release 3 feature demo built before the design was approved**. Akshita's first change request asked for the guide's written decision | The guide granted a one-PR exception to `CLAUDE.md` §6a.2 and §7 item 7 (19 Nov) | **Ask the guide before building ahead of the gate.** An exception must be named, recorded and limited to one PR |
| The PR was 1,340 lines, later 1,396 | Allowed for that PR only, with a file map; the guide accepted the extra 56 lines | Size is a rule; exceptions need a file map and a stated number |
| The demo used `libx264`, a GPL encoder, against PRD C-11 | Decision 0013 records a narrow exception (demo only, separate process, nothing in `requirements.txt`) | **Check every licence, including for tools run as separate programs.** Record the decision where the licence is declared |
| Dependency questions: a Starlette advisory, the licence listing, where the pins go; the guide asked for one `jsonschema` pin and a stated reason if two | Pins and licences documented; one line in `requirements.txt` naming both users | **One pinned version per package, with its licence in a comment**; keep demo-only dependencies out of the root file |
| A dedicated CI job (`video-demo`) touched `ci.yml` and `.gitignore`, which are guide-owned | The guide approved those two files separately | **Say which files need the guide's approval** in the PR description |
| Merge conflict in `requirements.txt` after `main` moved | Merged `main` in (no rebase) and kept both sides' intent | Merge, never rebase or force-push, and explain the resolution in a comment |

### 2.5 Release 0 documents (#104, #105, #106, #154, #155, #156, #163, #198)
| What happened | Fix | Learning |
|---|---|---|
| #104 failed CI on end-of-file whitespace | Trimmed trailing blank lines | **Run `pre-commit` before pushing** |
| #105 and #163 had slips (assistant): a wrapped-line diff hid that `requirements.txt` changed, and an instruction was attributed to the wrong person (Harshitha caught both) | Corrected in follow-ups | **Read the full diff, not only the summary. Quote who said what, with the link** |
| The release documents named tasks (T7, T11, T13…) that no file defined | The documents now say so and map only to PRD requirements | Do not use labels the repository does not define |
| After #169 and #129 merged, the release documents still said B8.5 was PENDING and #129 was open. #198's first version fixed some but not all statements; Harshitha found more in `report.md` and `design/video.md` and asked for changes | A second push fixed every named row; she approved | **When fixing stale text, search the whole repository for each stale phrase** ("PENDING", "0 consent", "open, ready for review"), then re-read the changed files |
| Two PRs edited the same checklist lines (#194 and #198), so one became conflicted | Merged `main` into #194 and kept both rows | Merge the approved PR first; check which files two open PRs share |

### 2.6 Speech options ADR (#98)
| What happened | Fix | Learning |
|---|---|---|
| The ADR called PR #25 "open" after it had merged, and referred to other PRs as unmerged | The guide asked for a three-line fix; you also corrected #97, #85 and #93 references | **Check a PR's state on the day you cite it** |
| A record cannot move past PROPOSED without the lab facts (model, engine, hardware, retention, ffmpeg) | Still pending | **Ask early for what only the lab can supply**, and write down exactly what you need |

### 2.7 Literature survey (#100, #106, #194)
| What happened | Fix | Learning |
|---|---|---|
| AI-researched entries (P1 to P12) were first recorded as read by an AI assistant, not by you; they could not count | You opened and compared every source; #194 recorded it | `CLAUDE.md` §6a rule 5: **open every reference yourself.** Never count an AI-read source |
| Only 1 of 6 required sources was owner-verified for a long time | Reached 13 | Do the verification early, a few sources at a time |
| Some pages changed between reading and now (the IETF draft dates), and some pages could not be read in full (PDFs, a login wall) | Entries record what was seen and when | **Record the date you saw a page.** Say "not read" when it was not read |
| The survey count was met but the topic gaps were not | The file still says Draft and lists the gaps | **Meeting a number is not the same as covering the topic.** Say both |

---

## 3. Habits to build (the checklists)

### Before opening a PR
- [ ] Which requirement ID does this implement? Is it for the release I am on?
- [ ] Is the design `Approved`, or is this foundation work the guide allowed? If not, ask first.
- [ ] Built on `main`, not on another unmerged PR. One concern only.
- [ ] Under about 800 changed lines; if not, a reason and a file map in the description.
- [ ] Which files need the guide (`ci.yml`, `.gitignore`, contracts)? Say so.
- [ ] Licences checked for everything new, including tools run as separate programs.
- [ ] `pre-commit` and the module tests run locally; the output shown in the PR.
- [ ] Traceability and README updated; `.env.example` if configuration changed.

### Before saying "done" or "verified"
- [ ] Did I measure it, or am I repeating what someone told me? Label statements as statements.
- [ ] Did I read the whole diff, including wrapped lines and files I did not mean to change?
- [ ] Did I search for every old word or number that this change makes false?
- [ ] Do the headings, checklists, counts and dates agree in every file?

### Before pushing to an open PR
- [ ] Does it already have approvals? A push cancels them. Is it worth it?
- [ ] Merge `main` (never rebase or force-push), explain conflict choices in a comment.
- [ ] Do not click "Update branch" or "Enable auto-merge" unless the plan needs it. Merging is your own click.

### Before relying on a source
- [ ] Open it; check title, authors, date and version; write the date you saw it.
- [ ] A reference, PR state or date cited from memory is checked again.

---

## 4. Good habits you already showed (keep them)

- You asked the guide in one structured list (Q1 to Q16) and recorded every answer in the right place.
- You put the checker and tests before the data, and kept the placeholders honest (`PENDING`) until a value was measured.
- You took reviewer corrections quickly and fixed the cause, not just the comment (for example the headings and checklist in #169, the contradictions in #198).
- You refused to count AI-read sources and verified them yourself.
- You asked for consent lines from each speaker in their own words and held back publication until they arrived.
- You separated what belongs to other modules (checker, grading) from your own work.

---

## 5. Still open (so the next lessons are not repeated)

- The lab facts for ADR 0002 (#98), the App-C 9 lab check, and the lab `ffmpeg -version` line.
- The guide's answers on issue #186: the two `0001` decision records, WER for Release 0, the lecture 02 checker, and the B8.5 owner statements.
- The Checker owner's B6 reply.
- B8.6 chapter and summary inputs, and the peer box in the grading design.
- The Video design: read it all, then the owner box, then `In review`.
- Survey gaps: P12's WER section, P8's parameters, the P4 lead, and sources for segmentation, summarisation, normalisation, privacy and Moodle video embedding.
