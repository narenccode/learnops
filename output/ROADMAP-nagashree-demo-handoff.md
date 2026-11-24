# Handoff roadmap (updated): the live part of Nagashree's demo tasks

For: the person running the live rehearsal in the lab for Nagashree (with Claude Code as the helper).
Sources: `PLAN-demo-grading.md`, `docs/demos/h4-h6-live.md` on branch `demo/h2-grading-tier1` (draft PR #139), issue #112 "Daily check-in".

## 0. Status: what is already done

| Task | Status |
|---|---|
| N1 Re-review of PR #80 | **Done.** Approved at `314da58`; verdict posted in #112. |
| N2 Secrets check | **Done (offline, fake token).** The token appeared in no output, log or `--out` file. An `--out` path inside the repository is refused (exit 2). 137 demo tests passed; the 31 read-only refusal tests passed. |
| N3 Rehearsal, Tier 1 | **Done.** Clean clone of `8f49675`, all 6 cases as expected. |
| N3 Rehearsal, Tiers 2 and 3 offline | **Done.** |
| N4 Timing, offline | **Done** (table in section 3). |
| `Rehearsal done` post in #112 | **Posted** (offline only). |
| **N3 and N4, Tiers 2 and 3 LIVE** | **OPEN. This is your job.** |

You do not need to repeat the offline work. Run it again only if something looks wrong.

## 1. Hard rules (read first)

1. **The token is a secret.** Never put it in chat with Claude, #112, a PR, a file, a log or a screenshot. Set it only as an environment variable in your own terminal (`MOODLE53_WS_TOKEN`). Run the live commands yourself and paste only the output, after checking it does not contain the token.
2. **Never write or release a grade.** If any output shows a grade being sent, stop and tell Harshitha.
3. **Live steps run on the lab network, in person.**
4. **Test data only.** No real learner data.
5. **Do not push to anyone's branch and do not merge anything.** You only read and run.
6. **Do not change the library to make a step pass.** A live difference from the fake is a *finding*, not a failure.
7. When you post in #112, say "run by <your name> for Nagashree".

## 2. Before you start: what must be true

| Condition | Where to check |
|---|---|
| Shraddha posted **"Lab ready"** in #112 (service name and function list) | #112 |
| Akshita posted **"Test course ready"** with the course id, the two assignment ids and each learner's username and state | #112 |
| You have the token **directly from Harshitha** (never from #112). Ask her to set it in your shell or hand it to you directly. | Harshitha |
| You are on the lab network, in person | |

If either lab post is missing when the lab opens, ask in #112 who is waiting for what. If the lab cannot be reached, report "live not rehearsed" and stop. The plan accepts a Tier 1 only demo, said plainly.

## 3. Baseline: what offline looked like (to compare with live)

Clean clone `8f49675`, Python 3.12.5, fake Moodle 5.3.

| Run | Result | Time |
|---|---|---|
| Tier 1 | 6 of 6 cases as expected, exit 0, last line `OFFLINE: against the Moodle 5.3 fake, not a live run` | 1.7 s |
| Tier 2 `--offline` | 6 steps ran, 0 findings, `mod_assign_save_grade` refused with "nothing was sent", exit 0 | 0.6 s |
| Tier 3 `--offline` | A would write (stopped by the read-only connection), B refused (R3), D refused (workflow off), C "would write" plus one FINDING, exit 0 | 0.8 s |

Live runs will be slower because they call the lab over the network. Record the real numbers.

## 4. Setup on the lab machine

```bash
git clone https://github.com/narenccode/learnops.git learnops-rehearsal
cd learnops-rehearsal
git checkout demo/h2-grading-tier1
python --version        # needs 3.12
python -m pip install -r requirements-dev.txt
```

On Windows with the project's virtual environment, use `.venv/Scripts/python.exe` in place of `python`.

Set the two variables **in your own terminal, for this session only** (never in a file):

- PowerShell: `$env:MOODLE53_URL = "<lab site address>"` and `$env:MOODLE53_WS_TOKEN = "<token from Harshitha>"`
- bash: `export MOODLE53_URL="<lab site address>"` and `export MOODLE53_WS_TOKEN="<token from Harshitha>"`

Create two small config files **outside the repository** (for example in your documents folder), using the course id from Akshita's post:

```yaml
# h4.yaml and h6.yaml
course_id: <id>
learners:        # only if the usernames are not learner-a to learner-d
  A: <username>
  B: <username>
  C: <username>
  D: <username>
```

Cheap safety check first: `python scripts/demos/demo_h4_live_read.py --config <h4.yaml> --dry-run` makes no call and only checks the settings are set.

## 5. Tier 2 live (time it)

```bash
python scripts/demos/demo_h4_live_read.py --config D:/notes/h4.yaml --out D:/notes/h4-output.json
```

Expected, in order:

1. A call with the token works. `mod_assign_save_grade` is refused with "nothing was sent".
2. Course contents: Assignment 1 and Assignment 2.
3. Enrolled users: 4 students plus the service account's own enrolment.
4. Settings: grading type point, maximum grade 10. Assignment 1 marking workflow **ON**, Assignment 2 **OFF**.
5. Submissions and status per learner: A submitted and not graded; B submitted and ready for release; C draft; D submitted on Assignment 2.
6. One file downloaded: file name and byte count only.

Last line: `LIVE: read-only run. Nothing was written to Moodle.` Exit 0 means every step ran. Anything that differs from the fake is a finding to write down: it still exits 0. A step that fails is shown, and the other steps still run.

## 6. Tier 3 live (time it)

```bash
python scripts/demos/demo_h6_dry_run.py --config D:/notes/h6.yaml --out D:/notes/h6-output.json
```

| Case | Expected |
|---|---|
| A: Assignment 1, submitted, no grade, workflow on | `WOULD WRITE readyforrelease: allowed`, "write attempt: stopped by the read-only connection" |
| B: submitted, already Ready for release with a grade | `REFUSED: locked (R3)` |
| D: Assignment 2, workflow off, submitted | `REFUSED: workflow off` |
| C: draft, not submitted | Print what the library says. Do not predict it. Offline it said "would write" plus a FINDING (the library decides from the grading state only). |

"WOULD WRITE" counts only if the write attempt reached, and was stopped by, the read-only connection. A line that says `UNEXPECTED` is a failure: record it.
If the library cannot stop before sending: do not change it. Say so in #112 and show Tiers 1 and 2 only.

## 7. Things to watch on the first live run

The read-only connection's real HTTP code runs against a real site for the first time. Look for:

- http versus https problems, or a refused redirect (the connection refuses redirects on purpose, because one could carry the token elsewhere);
- Moodle's error text differing from the fake's;
- a read refused for missing rights: tell Shraddha. She adds the one capability and writes it down (lab check 9);
- field names or values that differ from the fake (finding, not failure).

## 8. Using Claude Code as the helper

Safe to ask Claude: "help me read this output", "write the results table", "draft the #112 post". Do **not** let it run live commands with the real token, and never paste the token into the chat. Check any output for the token before pasting.

## 9. After the runs

- Keep the `--out` files **outside the repository**. Never commit them.
- Unset the variables or close the shell.
- Shraddha deletes the token and disables the service account after the demo.

## 10. Report to post in #112

```
Live rehearsal done (run by <name> for Nagashree): <what failed, or "nothing failed">.
Tier 2 live: <seconds>, <one line>. Tier 3 live: <seconds>, <one line>.
Expected results matched: <A / B / D yes or no>. Case C, the library says: <text>.
Findings (live differs from the fake): <list or "none">.
Steps that did not work from the instructions alone: <list or "none">.
Nothing was written to Moodle. Token not shown anywhere: <yes>.
```

If the lab was not available: "Live not rehearsed: <reason>. Tier 1 and offline Tiers 2 and 3 were rehearsed earlier."

## 11. Decision table

| If | Then |
|---|---|
| "Lab ready" or "Test course ready" is missing | Ask in #112 who is waiting for what. Do not guess ids. |
| Lab cannot be reached | Report "live not rehearsed". Tier 1 only. |
| A read is refused for missing rights | Tell Shraddha; she adds one capability and writes it down |
| Library cannot stop before sending | Tiers 1 and 2 only. Do not change the library. |
| Token appears anywhere | Stop. Tell Harshitha and Shraddha. The token must be replaced. |
| Anything writes or releases a grade | Stop immediately and tell Harshitha |
| Live answer differs from the fake | A finding. Add it to the results table. |

## 12. Done means

Tier 2 and Tier 3 ran live, with the expected results (or the differences written down as findings), timings recorded, nothing written to Moodle, the token shown nowhere, and the report posted in #112.
