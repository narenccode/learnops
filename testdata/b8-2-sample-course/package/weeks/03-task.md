# Week 3 task

Show that you tested your assistant and made it better. Your report is a short account of the two
(or more) weak answers you fixed and what you changed for each.

## How to submit

Submit online text with one label per line. Labels are not case-sensitive.

```text
Repository: <URL>
Demo: <URL>
Report: <your account>
```

`Repository` is the link to your code repository and `Demo` is the link to your running assistant.
`Report:` is followed by your report text, to the end of the submission. If there is no `Report:`
section, a file you upload named `report.md` or `report.txt` is your report.

The checks in the marking table read these parts: `http_ok:demo_url` reads `Demo`, `repo_clone`
reads `Repository`, and `word_count` reads your report.

<!-- marking-table v1 -->
| Criterion | Points | Full marks when | Check |
|---|---|---|---|
| Test list | 8 | A `TESTS.md` file lists at least five questions with the expected answer | repo_file:TESTS.md |
| Demo still works | 7 | Demo link opens and the assistant answers one of the listed questions | http_ok:demo_url |
| Fixes | 10 | You fix at least two weak answers and explain each change | — |
<!-- /marking-table -->
