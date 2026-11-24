"""Speaker notes for the 15 slides. Used for the PPTX notes pane and the DOCX."""

TITLES = [
    "Title",
    "Presentation outline",
    "Introduction and problem statement",
    "Literature survey and research gap",
    "Objectives and objective-wise progress",
    "Methodology and system architecture",
    "Dataset and computing requirements",
    "HPC lab requirement details",
    "Implementation evidence and preliminary results",
    "Demonstration",
    "Remaining work, timeline and risks",
    "Sustainable Development Goals",
    "Conclusion",
    "References",
    "Thank you",
]

# each: explain (list), details (list), qa (list of (q, a))
NOTES = {
1: dict(
    explain=["Introduce LearnOps as one platform built by four students, not four separate projects. Name each student, module and GitHub handle once.",
             "State that registration numbers, batch number and mentor details are placeholders in the file and must be filled in before the session."],
    details=["Title is the PRD title. The approved proposal title is not in the supplied material, so confirm it matches.",
             "Audit source: narenccode/learnops, main at ecb4389, fetched 2026-11-16."],
    qa=[("Is this title the approved proposal title?", "It is the title in PRD v1.0. We will confirm against the approved proposal and correct the slide if they differ."),
        ("Who is your guide?", "Read the mentor name from the title slide. The repository guide account is narenccode; the faculty mentor's name and designation are placeholders to be filled.")]),
2: dict(
    explain=["Walk through the eleven template headings and say that slides 9 and 11 carry the team progress and Release 0 status.",
             "Say up front that the story is: problem, design, what is merged, what is only in review, what remains."],
    details=["The outline follows the university template exactly; no slide was added or removed."],
    qa=[("Why is there no separate team slide?", "The template fixes 15 slides. Team progress is shown per objective on slide 5 and per student on slides 9 and 11.")]),
3: dict(
    explain=["LearnOps is a set of open-source tools that run beside an unmodified Moodle (4.5 and 5.3) and BigBlueButton 3.0 to cut mentor time on course creation, course checking, grading and video.",
             "Five problems P1 to P5 come from PRD A2. Each module answers a problem: Studio (P1, P5), Checker (P2), Grading (P3), Video (P4).",
             "Be explicit that the right-hand column is the intended solution. Nothing on this slide has been measured yet."],
    details=["Today's figures (2-3 h to load a course, about 10 min per submission) are PRD baselines, not our measurements.",
             "Constraint to mention: we never modify Moodle or BigBlueButton. We connect only through backups, web services, LTI 1.3, a browser for tests, and the BBB API.",
             "The approved problem statement text was not in the supplied files; slide uses PRD A2 and is marked accordingly."],
    qa=[("Why not write a Moodle plugin?", "PRD rule C-01: no modification of Moodle. Plugins would tie us to a Moodle version and break the 4.5 and 5.3 requirement. We integrate through supported interfaces."),
        ("Have any of the targets been reached?", "No. Targets such as 15-minute course loading are Release 2 goals. No module feature is implemented yet; Release 0 is foundation work.")]),
4: dict(
    explain=["Be direct: the literature survey is incomplete. One source is fully audited (Svarah), the grading list of six is in an unmerged pull request and was not re-opened for this deck, and Studio and Checker have no survey on main.",
             "The research gap shown is a hypothesis to be established by the survey, not a finding."],
    details=["Svarah (Javed et al., arXiv 2305.15760 v1): 9.6 hours, 117 speakers, 19 native languages, benchmark for English ASR on Indian accents. The audit notes that its 'Submitted to INTERSPEECH' line is not proof of publication.",
             "Published results are not LearnOps results. No LearnOps speech evaluation has been run.",
             "Survey topics per module come from PRD chapters C1.12 to C4.12 (Bloom level L2)."],
    qa=[("Where is your research gap?", "The working hypothesis is that no open-source toolkit combines these four functions beside an unmodified Moodle. We have not yet shown it; closing the survey is a pending task for each student."),
        ("Why only one verified source?", "Our rule is that each source is opened and checked before it is recorded, because AI tools invent citations. We prefer one verified source to six unchecked ones.")]),
5: dict(
    explain=["This is the objective matrix. The approved proposal was not available, so the four objectives are provisional: one per module, taken from the PRD goals and the module chapters. Say so.",
             "Read each row: owner, completed work on main, work in open pull requests, pending work, status, and the Bloom phases reached.",
             "Status is judged on main only. Work in a pull request is shown as partial, never completed."],
    details=["Bloom mapping per PRD Appendix B: Survey L2, Analyze L4, Design L6, Develop L3, Integrate L3, Evaluate L5.",
             "Merged to main: S1 7 PRs, S2 4, S3 2, S4 10. Merged only into stacked branches: S2 1, S3 5.",
             "Student 3's work is large but waits on cross-owner contract approval, hence Partial plus Blocked."],
    qa=[("Why do you call objective 3 blocked?", "B4 and B5 are approved by the reviewer but still wait for the other affected owners and the guide, and the model interface and web-services libraries are stacked behind them."),
        ("Why is nothing marked completed for evaluation (L5)?", "No measurement has been run on any module. The PRD targets are measured in later releases.")]),
6: dict(
    explain=["Follow the flow left to right: mentor or administrator, Moodle, LTI 1.3 gateway, the four modules, shared libraries and services, then outputs back to Moodle, grading and media.",
             "Explain the three line styles. Solid green is merged on main. Dashed amber is in an open or draft pull request. Dashed grey is planned or design only.",
             "Point out that the modules, LTI gateway, database, workers and harness are not yet built."],
    details=["Merged: CI, contract validator, B1 schema and examples, B6 lesson-manifest schema, media_paths validation and signing.",
             "Open PRs: B2, B3, B4, B5, B7, B6.2, media_paths templates (#85), model_interface (#35 draft), moodle_ws (#63, #76, #79, #80).",
             "Heavy work (transcoding, transcription, sandboxed checks) goes to worker containers through a job queue, never inside a web request (PRD OPS-10).",
             "Learner role launches are refused by baseline tools (EXT-07)."],
    qa=[("Why contracts first?", "Four people build four modules that must integrate. Fixing formats first (B1 to B8) lets each module be built and tested alone and avoids rework."),
        ("Is the model interface local or hosted?", "Both, behind one adapter (PRD B5). No module calls a provider directly. No provider is configured in the repository and no key is stored there."),
        ("How do you keep AI from affecting grades?", "AI output is always a draft. A mentor approves before anything is written to Moodle, and the tools never release grades (rule 5).")]),
7: dict(
    explain=["Six test-data sets B8.1 to B8.6, each with an owner and a purpose. None is complete.",
             "B8.5 is furthest along: validator, tests and an inventory with SHA-256 hashes are merged. Consent, duration and transcript review are still PENDING on main.",
             "Recordings are deliberately not stored in Git."],
    details=["PRD minimums: B8.4 at least 30 submissions (6 pilot so far); B8.5 at least 5 lectures and 30 minutes in total.",
             "ADR 0004 on main records a temporary exception to the 1800 s minimum for B8.5.",
             "Local-only changes (for example durations measured with ffprobe on a local branch) are not on GitHub and are not counted here."],
    qa=[("Why is B8.1 empty?", "A Moodle course backup needs a Moodle instance. The lab is not confirmed, so only the requirements README is on main."),
        ("How will you handle speaker consent for videos?", "Written consent or an openly licensed source, with the licence recorded in testdata/README.md. This is why B8.5 stays marked incomplete.")]),
8: dict(
    explain=["State the honest position: HPC or GPU is not required for Release 0 and the baseline.",
             "The lab VMs described in PRD A11 are not evidenced on GitHub. The BigBlueButton verification records say no lab access."],
    details=["PRD OPS-11: no module may require a local GPU; any provider can be a hosted API.",
             "Fine-tuning a small model on lab GPUs (F-4) is an extension idea, not part of the baseline.",
             "Resources actually used: developer machines and the repository's CI on GitHub. No GPU specification is claimed."],
    qa=[("Will you need GPUs later?", "Possibly for local speech-to-text and small language models in Releases 3 and 4. The guide provides lab AI endpoints; the design lets us use a hosted API instead."),
        ("What stops you now without the lab?", "App-C verification items, B8.1, the harness and browser role tests need real Moodle and BigBlueButton instances.")]),
9: dict(
    explain=["Three strong numbers: 55 of 96 pull requests merged to main; CI on main is green with 2049 tests; 0 of 7 contracts frozen.",
             "The chart shows pull-request status per student. Merged to a stacked branch is not merged to main.",
             "Separate the three groups: merged, submitted but not merged, and measured results."],
    details=["CI: workflow 'ci' on main at ecb4389 succeeded. 2049 tests passed, mypy clean on 30 source files, 3 contract examples validated against 2 schemas, plus 137 CI-script tests.",
             "PR totals: 96 (61 merged, of which 55 to main; 31 open, of which 9 draft; 4 closed unmerged). The guide merged 32, the students 23.",
             "Reviews on others' PRs: S1 23, S2 29, S3 32, S4 47.",
             "No deployment URL exists. The tools are not deployed because there is no module feature yet and no confirmed lab."],
    qa=[("Does 2049 tests mean the modules work?", "No. Most tests cover contracts, validators, libraries and CI scripts. No module feature is built, so no functional claim is made."),
        ("Is the commit history continuous?", "Merged work is spread over many PRs and reviewed by peers. Open PRs are shown separately and are not counted as done."),
        ("Why is the guide's merge count high?", "The guide built the CI, review bot, handbook and CODEOWNERS scaffolding.")]),
10: dict(
    explain=["The demonstration is repository, contract validation and CI evidence only. Say that plainly.",
             "Use the main branch for the main demo. If an open PR is shown, name the PR and say it is not merged."],
    details=["Suggested order: contribution and PR list, CI run on main, contract-example validation, media_paths validation tests, then one open PR branch.",
             "Run commands from a fresh clone of main so local uncommitted work is not mixed in.",
             "Have screenshots of the CI run ready in case the network fails."],
    qa=[("Can you show Course Studio generating a course?", "Not yet. Studio is a Release 2 deliverable. We can show its schema, validator and examples."),
        ("Is there a deployed URL?", "No. We explain why on slide 8 and slide 9: the lab is not confirmed and no module feature is built yet.")]),
11: dict(
    explain=["Each student has a lane. All dates are proposed estimates, not agreed deadlines.",
             "The Release 0 gates are the real remaining work: 0 of 7 contracts frozen, 0 of 4 designs approved, 0 of 6 datasets complete, 0 of 10 App-C items done, lab unconfirmed.",
             "The largest risks are the contract review gate and Student 3's 12 open pull requests."],
    details=["Issue #65 (section idnumber conflict between B1 and B2) must be settled before B1 can freeze.",
             "ADR number 0005 is used twice (#54 and #96 or #97), and #96 also uses 0006.",
             "#96 and #97 had a failing check in the latest status read.",
             "The guidelines PDF lists 12 to 14 November 2026 for interim presentations; the audit was fetched on 16 November 2026. Confirm the actual slot."],
    qa=[("Can Release 0 finish before the final evaluation?", "It depends on the contract reviews and on lab access. We have proposed an order of work; the dates need the guide's agreement."),
        ("What is the single biggest blocker?", "The rule that every affected owner and the guide approve each contract pull request. Most built work is waiting on that.")]),
12: dict(
    explain=["Only SDG 4 is claimed. The three targets are proposed by us and need the team's and guide's confirmation, since no approved alignment was found in the supplied files.",
             "All contributions are intended. No educational or accessibility impact has been measured."],
    details=["SDG 4: Quality Education. Targets 4.3, 4.4 and 4.5 are quoted in short form from the UN SDG site.",
             "We did not add other SDGs because the link would be weak."],
    qa=[("Why not SDG 9?", "It would be a stretch for a Moodle add-on toolkit. We prefer one defensible goal.")]),
13: dict(
    explain=["LearnOps aims to cut mentor time on four tasks, with measured targets.",
             "Release 0 has built a solid foundation but is not complete: no contract frozen, no design approved, no dataset complete, and the lab is unconfirmed.",
             "Next milestone: resolve B1 and B2 drift, merge approved contract PRs, then freeze."],
    details=["Established: CI, review workflow, B1, B6 manifest, contract validator, media_paths validation and signing, 55 merged PRs, 131 peer reviews by students."],
    qa=[("Is Release 0 complete?", "No. Its exit criteria are not met, and we say so."),
        ("What would you do first with two more weeks?", "Merge the approved contract pull requests and settle Issue #65 so the contracts can be frozen.")]),
14: dict(
    explain=["Only sources that have been opened are listed. Re-open each link before the session."],
    details=["Placeholders remain for the approved proposal. The grading literature list sits in PR #62 and is not reproduced here until it is merged and re-checked."],
    qa=[("Are all references verified?", "Svarah was audited against its PDF by the owner. Standards and documentation entries are official landing pages. Please check each link before presenting.")]),
15: dict(
    explain=["Thank the panel and invite questions."],
    details=["Keep the repository link and CI screenshot ready."],
    qa=[("Where can we see the work?", "github.com/narenccode/learnops, main branch.")]),
}


def notes_text(n):
    d = NOTES[n]
    parts = ["EXPLAIN:"] + ["- " + x for x in d["explain"]]
    parts += ["", "TECHNICAL DETAIL:"] + ["- " + x for x in d["details"]]
    parts += ["", "LIKELY QUESTIONS:"]
    for q, a in d["qa"]:
        parts += ["Q: " + q, "A: " + a]
    return "\n".join(parts)
