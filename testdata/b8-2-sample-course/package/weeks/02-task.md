# Week 2 task

Make your assistant answer from a document, and document how to use it. Your report is a short note
on the questions your assistant answers badly.

## How to submit

Submit online text with one label per line. Labels are not case-sensitive.

```text
Repository: <URL>
Demo: <URL>
Report: <your note>
```

`Repository` is the link to your code repository and `Demo` is the link to your running assistant.
`Report:` is followed by your report text, to the end of the submission. If there is no `Report:`
section, a file you upload named `report.md` or `report.txt` is your report.

The checks in the marking table read these parts: `http_ok:demo_url` reads `Demo`, `repo_clone`
reads `Repository`, and `word_count` reads your report.

<!-- marking-table v1 -->
| Criterion | Points | Full marks when | Check |
|---|---|---|---|
| Repository | 5 | The repository link clones | repo_clone |
| Document answers | 10 | Demo link opens and the assistant answers a question from the document | http_ok:demo_url |
| README | 5 | README has Setup and Usage sections | readme_sections:Setup,Usage |
| Weak answers | 5 | You name at least two questions the assistant answers badly and say why | — |
<!-- /marking-table -->
