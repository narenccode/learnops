# Grading assistant: literature survey (Release 0)

**Module:** Grading assistant (M3, `Harshithamanjunatha`).
**Requirement:** `docs/GETTING-STARTED.md` (the literature survey for your module: at least six sources, each
opened and verified) and PRD §C3.12. Survey, Bloom's level L2 (PRD App-B).
**Status:** the six sources and the owner's checklist below are carried over unchanged from
`docs/design/grading.md` §12.1, where they were recorded. They were moved to this file on 2026-11-19 by
copying the text; **no source was re-opened in the move.** The owner's verification is the one recorded in
the checklist.

`docs/GETTING-STARTED.md` allows a survey in `docs/design/<module>.md` §12 or in
`docs/literature-<module>.md`. This file uses the second option, like `docs/literature-studio.md` and
`docs/literature-video.md`. The design document now points here (its §12.1 and its question Q11).

**Reading the references.** Section numbers (§), question numbers (Q) and requirement or rule IDs (FR-G-xx,
R1, and so on) in the lines marked *Informs* refer to `docs/design/grading.md` and the PRD, not to this file.

Topics (GETTING-STARTED §6, PRD §C3.12): automated assessment, LLM-as-grader studies, code similarity detection. At least six sources, each opened and verified by the owner before it is cited (root `CLAUDE.md` §6a.5).

These sources inform this design; they do not decide anything in §12. Their results come from other settings, so they do not show how LearnOps will perform. Figures are the authors' own. Each entry says whether it reports **empirical findings**, a **review** of other studies, or a **proposed method**.

**How these were checked.** Every DOI was resolved in Crossref. ACM, Elsevier and IEEE pages could not be opened by the tool used, so the text read is the one named in each entry; where that is a preprint, the published version may differ. The owner has since checked all six against the original PDFs (checklist below).

**Automated assessment of programming assignments**

- **L1.** M. Messer, N. C. C. Brown, M. Kölling, M. Shi. "Automated Grading and Feedback Tools for Programming Education: A Systematic Review." *ACM Transactions on Computing Education* 24(1), 2024, 1–43. https://doi.org/10.1145/3636515. Text read: arXiv 2306.11722v2.
  *Review* of 121 papers, 2017 to 2021. 66 % assessed correctness only. Few tools assessed only readability or maintainability. Only 22 tools were evaluated against human assessors, and 84 % did not provide their evaluation dataset.
  *Informs:* drafting every criterion with evidence, not only machine-checkable ones (FR-G-03); keeping test set B8.4 in the repository; measuring agreement with a mentor (§11.2).

**LLM as a grader, compared with human evaluators**

- **L2.** R. Wang, J. Guo, C. Gao, G. Fan, C. Y. Chong, X. Xia. "Can LLMs Replace Human Evaluators? An Empirical Study of LLM-as-a-Judge in Software Engineering." *Proceedings of the ACM on Software Engineering* 2(ISSTA), 2025, 1955–1977. https://doi.org/10.1145/3728963. Text read: arXiv 2502.06193v3.
  *Empirical.* LLM scores compared with two human evaluators on 450 responses (code translation, generation, summarization). Output-based methods reached Pearson correlations of 81.32 and 68.51 on translation and generation, where the authors say they can be used standalone; for summarization they say these methods should not be used directly or alone. The task is not student grading.
  *Informs:* not assuming that agreement on one task carries over to another; reporting per-criterion agreement (§11.2); mentor approval of every draft (PRD C-09).
- **L3.** G. Crupi, R. Tufano, A. Velasco, A. Mastropaolo, D. Poshyvanyk, G. Bavota. "On the Effectiveness of LLM-as-a-Judge for Code Generation and Summarization." *IEEE Transactions on Software Engineering* 51(8), 2025, 2329–2345. https://doi.org/10.1109/TSE.2025.3586082. Text read: arXiv 2507.16587v1.
  *Empirical.* For code correctness, Cohen's kappa between GPT-4 and the ground truth was 0.21 for Java and 0.10 for Python (Table 2, automated CoT prompt), and for Java it misjudged 50 % of wrong implementations as correct. For content adequacy of summaries, Krippendorff's alpha with the median human rating was 0.58 (Java) and 0.63 (Python) with the zero-shot prompt (Table 5), against 0.81 and 0.69 among the human raters. The task is not student grading.
  *Informs:* letting machine checks, not the model, establish whether code works (FR-G-02, code-side rules in §4.3d); measuring mentor-to-mentor agreement as a baseline (Q47); the leniency measure in §11.2 (R2).
- **L4.** A. Piscitelli, M. De Rosa, V. Fuccella, G. Costagliola. "LLM-Based Rubric Grading for Programming Assignments: An Empirical Study." *Proceedings of the 18th International Conference on Computer Supported Education (CSEDU)*, vol. 3, SciTePress, 2026, 2039–2050. https://doi.org/10.5220/0015049400004021. Text read: publisher's page and PDF.
  *Empirical.* Three LLMs graded student submissions already graded by a teacher against a rubric. The best model reached Cohen's kappa 0.59. Specification Adherence and Design Autonomy showed larger discrepancies. The authors state the limits: 30 submissions and a single teacher.
  *Informs:* per-criterion agreement (§11.2); reporting a tolerance measure beside exact agreement (band, Q44); a second mentor (Q47). Its small sample means it supports these choices only weakly.

**Source-code similarity detection and fingerprinting**

- **L5.** M. Zakeri-Nasrabadi, S. Parsa, M. Ramezani, C. Roy, M. Ekhtiarzadeh. "A systematic literature review on source code similarity measurement and clone detection: Techniques, applications, and challenges." *Journal of Systems and Software* 204, 2023, article 111796. https://doi.org/10.1016/j.jss.2023.111796. Text read: arXiv 2306.16171.
  *Review* of 136 primary studies. Of 12 datasets found, only eight were publicly accessible. The authors name the lack of reliable datasets and of empirical evaluations among the main challenges.
  *Informs:* building our own similarity calibration set and not relying on a published threshold (§3.1, Q49).
- **L6.** S. Schleimer, D. S. Wilkerson, A. Aiken. "Winnowing: Local Algorithms for Document Fingerprinting." *Proceedings of the 2003 ACM SIGMOD International Conference on Management of Data*, 2003, 76–85. https://doi.org/10.1145/872757.872770. Text read: copy hosted by an author, https://sschleimer.warwick.ac.uk/Maths/winnowing.pdf. Crossref gives only the short title; the full title is on the paper's first page.
  *Proposed method*, with analysis and a report of experience. Matches at least as long as a guarantee threshold are detected and matches shorter than a noise threshold are not; in each window of k-gram hashes the minimum is selected, and the rightmost if tied. The density analysis assumes random data. The paper reports experience with MOSS (Measure Of Software Similarity), a service for detecting plagiarism in programming assignments.
  *Informs:* the fingerprints in §3.1, with `k` and the window as configuration. It does not set their values, and it offers no evidence about student work in LearnOps.

**Owner check (root `CLAUDE.md` §6a.5).** Open each source, confirm the reference and the figures quoted above, then tick it.

- [x] L1
- [x] L2
- [x] L3
- [x] L4
- [x] L5
- [x] L6

**Considered, not cited.** Xiong, Xiang and Zhou, "A Review of Source Code Plagiarism Detection Techniques for Programming Assignments" (ITME 2024, https://doi.org/10.1109/ITME63426.2024.00212): the record exists, but no abstract or text could be read, so what it says is unknown.
