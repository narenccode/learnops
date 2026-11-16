import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
from build_lib import *
from build_lib import _fill_tf
from notes_data import notes_text

SRC = sys.argv[1]
OUT = sys.argv[2]
prs = Presentation(SRC)
S = list(prs.slides)
assert len(S) == 15

B = {"bold": True}


def R(t, **o):
    return (t, o)


# ---------------------------------------------------------------- 1 Title
s = S[0]
for sh in list(s.shapes):
    if sh.name == "Subtitle 2" and sh.top > 3_000_000 and sh.left > 1_000_000 and not sh.is_placeholder:
        sh._element.getparent().remove(sh._element)  # duplicate "Project Batch No" box
title_box = [sh for sh in s.shapes if sh.name.startswith("Google Shape;93")][0]
title_box.left, title_box.top, title_box.width, title_box.height = Inches(0.6), Inches(2.8), Inches(9.6), Inches(1.75)
_fill_tf(title_box.text_frame, [
    [R("Interim-Project Presentation", bold=True, size=22, color="000000")],
    [R("LearnOps", bold=True, size=30, color=RED)],
    [R("An AI-Assisted Toolkit for Course Authoring, Quality Assurance, Assessment and Video on Moodle",
       bold=True, size=15, color=RED)],
    [R("Project Batch No: [to be filled]", bold=True, size=15, color="000000")],
], 15, "000000", True, PP_ALIGN.CENTER, MSO_ANCHOR.TOP, 0.04, 2)
team = [sh for sh in s.shapes if sh.is_placeholder and sh.placeholder_format.type == 4][0]
team.left, team.top, team.width, team.height = Inches(0.45), Inches(4.85), Inches(5.3), Inches(1.9)
_fill_tf(team.text_frame, [
    [R("Team Details", bold=True, size=16, font=None)] if False else [R("Team Details", bold=True, size=16)],
    [R("Akshita (Akshita21-09), Reg. No. [__]", size=12, bold=True)],
    [R("Shraddha (shraddha0103), Reg. No. [__]", size=12, bold=True)],
    [R("Harshitha M M (Harshithamanjunatha), Reg. No. [__]", size=12, bold=True)],
    [R("Nagashree V (vnaags), Reg. No. [__]", size=12, bold=True)],
], 12, "000000", True, PP_ALIGN.LEFT, MSO_ANCHOR.TOP, 0.05, 2)
ment = [sh for sh in s.shapes if sh.name == "Text Box 9"][0]
ment.left, ment.top, ment.width, ment.height = Inches(5.9), Inches(4.85), Inches(4.7), Inches(1.9)
_fill_tf(ment.text_frame, [
    [R("Mentor", bold=True, size=16)],
    [R("[Dr/Mr/Mrs Faculty Name, to be filled]", bold=True, size=13)],
    [R("[Designation, to be filled]", size=12)],
    [R("Dept. of CSE, MSRUAS, Bengaluru", size=12)],
    [R("Module owners: Course Studio, Course Checker, Grading, Video", size=11, color=GREY)],
], 12, "000000", False, PP_ALIGN.LEFT, MSO_ANCHOR.TOP, 0.05, 2)

# ---------------------------------------------------------------- 2 Outline
s = S[1]
clear_slide(s)
set_title(s, "Outline")
items = [
    ("Introduction and problem statement", "3"),
    ("Literature survey and research gap", "4"),
    ("Objectives and objective-wise progress", "5"),
    ("Methodology and system architecture", "6"),
    ("Dataset and computing requirements", "7"),
    ("HPC lab requirement", "8"),
    ("Implementation evidence and results", "9"),
    ("Live demonstration", "10"),
    ("Remaining work, timeline and risks", "11"),
    ("SDG alignment and conclusion", "12-13"),
    ("References", "14"),
]
col_x = [0.7, 5.6]
for i, (t, n) in enumerate(items):
    c, r = divmod(i, 6)
    x, y = col_x[c], 1.45 + r * 0.82
    add_box(s, x, y, 0.62, 0.62, n, fill=PURPLE, line=None, size=13 if len(n) < 3 else 11, color=WHITE, bold=True,
            shape=MSO_SHAPE.OVAL, margin=0.0)
    add_text(s, x + 0.75, y, 3.9, 0.62, t, size=16, anchor=MSO_ANCHOR.MIDDLE)
add_text(s, 5.6 + 0.0, 1.45 + 5 * 0.82, 4.8, 0.62,
         [[R("One story: ", bold=True, color=PURPLE), R("problem, design, what is merged, what is in review, what remains.")]],
         size=13, color=INK, anchor=MSO_ANCHOR.MIDDLE)

# ---------------------------------------------------------------- 3 Introduction
s = S[2]
clear_slide(s)
set_title(s, "Introduction and approved problem statement", 24)
tag_banner(s, "Problem statement taken from PRD A2. Text of the approved proposal not supplied: confirm.")
add_text(s, 0.54, 1.33, 9.75, 0.62,
         [[R("LearnOps ", bold=True, color=PURPLE),
           R("is a set of open-source tools that work beside an unmodified Moodle 4.5 / 5.3 and BigBlueButton 3.0 "
             "to cut the time mentors spend on course creation, checking, grading and video.")]], size=12.5)
# three columns: problem -> limitations -> solution
cx = [0.54, 3.9, 7.26]
cw = 3.03
heads = ["Problem (PRD A2)", "Existing limitations (PRD baseline)", "LearnOps solution (intended)"]
fills = [GREY_BG, GREY_BG, BLUE_BG]
for i in range(3):
    add_box(s, cx[i], 2.0, cw, 0.36, heads[i], fill=PURPLE if i == 2 else GREY, line=None, size=11.5, color=WHITE,
            bold=True, shape=MSO_SHAPE.RECTANGLE)
colA = [
    "P1 Course creation is slow and error-prone",
    "P2 Course mistakes are found late",
    "P3 Grading project work takes hours",
    "P4 Videos are hard to upload and use",
    "P5 Learning stays passive",
]
colB = [
    "2-3 h to load one course by hand",
    "Restrictions and completion rules traced by hand",
    "About 10 min per submission, ~5 h per mentor per week for 30 learners",
    "No captions, chapters or index; manual upload",
    "15-40 min to build one practice activity, so rarely built",
]
colC = [
    [R("M1 Course Studio", bold=True), R(": course from a template, restore as .mbz")],
    [R("M2 Course Checker", bold=True), R(": rules, role tests, harness")],
    [R("M3 Grading Assistant", bold=True), R(": draft grades, mentor approves")],
    [R("M4 Video Pipeline", bold=True), R(": captions, chapters, resumable upload")],
    [R("Shared: ", bold=True), R("contracts, LTI 1.3, model interface")],
]
for i, col in enumerate((colA, colB, colC)):
    for j, t in enumerate(col):
        y = 2.43 + j * 0.62
        add_box(s, cx[i], y, cw, 0.56, [t] if isinstance(t, list) else t, fill=fills[i], line=None, size=10.5,
                align=PP_ALIGN.LEFT, shape=MSO_SHAPE.RECTANGLE, margin=0.08)
add_arrow(s, cx[0] + cw + 0.02, 3.9, cx[1] - 0.02, 3.9, color=PURPLE, w=2)
add_arrow(s, cx[1] + cw + 0.02, 3.9, cx[2] - 0.02, 3.9, color=PURPLE, w=2)
# relationship + status strip
add_box(s, 0.54, 5.6, 4.75, 1.15,
        [[R("How the modules relate", bold=True, color=PURPLE)],
         "Contracts B1-B8 fix the formats. A Studio course package is checked by the Checker, restored in Moodle, "
         "graded through Grading, with lectures turned into captioned lessons by Video."],
        fill=WHITE, line=PURPLE, size=10.5, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, margin=0.1)
add_box(s, 5.54, 5.6, 4.75, 1.15,
        [[R("Status today", bold=True, color=AMBER)],
         "Intended solution only. Merged: CI, contracts validator, B1, B6 manifest, media_paths. "
         "No module feature is implemented; targets are unmeasured."],
        fill=AMBER_BG, line=AMBER, size=10.5, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, margin=0.1)

# ---------------------------------------------------------------- 4 Literature
s = S[3]
clear_slide(s)
set_title(s, "Literature survey and identified research gap", 24)
tag_banner(s, "Survey incomplete. Only 1 source fully audited on main. Gap below is a hypothesis, not a finding.")
rows = [
    ["Module", "Existing approaches to survey (PRD C*.12)", "Verified so far", "Survey status"],
    ["Course Studio (S1)", "Moodle backup format, IMS Common Cartridge limits, course-as-code", "None on main", "Pending"],
    ["Course Checker (S2)", "Course-design quality, Moodle availability model, browser test automation", "None on main", "Pending"],
    ["Grading (S3)", "Automated assessment, LLM-as-grader studies, similarity detection", "6 sources listed in open PR #62, not re-opened for this deck", "Partial"],
    ["Video (S4)", "Indian-English ASR, lecture segmentation, summarisation, resumable upload", "Svarah (Javed et al., arXiv 2305.15760): 9.6 h, 117 speakers, 19 languages. Audited on main", "Partial (1 of 6+)"],
]
fl = {(1, 3): GREY_BG, (2, 3): GREY_BG, (3, 3): AMBER_BG, (4, 3): AMBER_BG}
add_table(s, 0.54, 1.38, 9.75, [1.5, 3.3, 3.5, 1.3], rows, size=10, row_h=0.62, fills=fl)
# flow
fx = [0.54, 3.06, 5.58, 8.1]
labs = [("Existing approaches", "Manual Moodle authoring, hand grading, uploaded video without captions (PRD A2 baseline)", GREY_BG, GREY),
        ("Limitations", "Slow, error-prone, no integrated quality gate, hard to scale for mentors", GREY_BG, GREY),
        ("Research gap (hypothesis)", "No open-source toolkit combining all four beside an unmodified Moodle. Not yet shown.", AMBER_BG, AMBER),
        ("LearnOps approach", "Contract-first modules, AI as draft only, mentor approval. Intended, not yet built.", BLUE_BG, PURPLE)]
for i, (h, t, bg, ln) in enumerate(labs):
    add_box(s, fx[i], 4.72, 2.19, 1.55,
            [[R(h, bold=True, color=ln, size=11.5)], R(t, size=10.5)], fill=bg, line=ln, dash=(i >= 2), size=10.5,
            align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, margin=0.1)
    if i < 3:
        add_arrow(s, fx[i] + 2.21, 5.5, fx[i + 1] - 0.02, 5.5, color=PURPLE, w=2)
add_text(s, 0.54, 6.35, 9.75, 0.4,
         "Svarah paper results are not LearnOps results; no LearnOps speech evaluation has been run. Source: docs/literature-video.md.",
         size=10, color=GREY, align=PP_ALIGN.LEFT)

# ---------------------------------------------------------------- 5 Objectives
s = S[4]
clear_slide(s)
set_title(s, "Approved objectives and objective-wise progress", 22)
tag_banner(s, "REQUIRES CONFIRMATION: approved proposal not supplied. Objectives below are provisional, from PRD goals G-1 to G-10.", size=10.5)
hdr = ["Objective (provisional) and owner", "Completed, on main", "Partial, in open PRs", "Pending", "Status", "Bloom"]
cwid = [2.15, 2.0, 2.1, 1.55, 0.95, 1.0]
rows5 = [
    (["O1 Course Studio, goal G-1 (R2)", "S1 Akshita"],
     "B1 schema + 5 examples (#23); package validator (#37, #48, #49); B8.1 README (#57)",
     "B7 H5P (#54); B8.2 course (#61); B1 amendments (#87, #94, #95, #101)",
     "Generator, editor, restore tests, B8.1 backup", "Partially completed", [1, 1, 0, 0]),
    (["O2 Course Checker + harness, G-2, G-3 (R1)", "S2 Shraddha"],
     "Contract-example validator chain; design skeleton",
     "B2 course model (#46); B3 LTI + ADR 0001 (#83)",
     "B8.3, rule engine, role tests, harness, lti library", "Partially completed", [0, 1, 0, 0]),
    (["O3 Grading + model interface, G-4, G-5, G-10 (R4)", "S3 Harshitha"],
     "Grading design and sandbox design (#18, #30), Draft; no code on main",
     "B4 (#27), B5 (#25) approved, awaiting owners; model_interface (#35); moodle_ws; B8.4 (#31), B8.6 (#33)",
     "Merge gate, grading features, comparison", "Blocked", [1, 1, 0, 0]),
    (["O4 Video pipeline, G-6 to G-8 (R3)", "S4 Nagashree"],
     "B6 manifest (#32); media_paths validate + sign (#84, #86); B8.5 checker (#82, #89, #99); lit S2 (#100)",
     "B6.2 (#93), templates (#85), speech ADR (#98), WER prep (#103), literature (#106)",
     "B8.5 consent + transcripts, upload, transcription", "Partially completed", [1, 1, 0, 0]),
]
y0 = 1.33
add_table(s, 0.54, y0, 9.75, cwid, [hdr] + [[r[0] if False else [[R(r[0][0], bold=True)], [R(r[0][1], color=PURPLE, bold=True)]],
                                            r[1], r[2], r[3], "", ""] for r in rows5],
          size=9.5, row_h=0.95, header_size=10)
# fix header row height and overlay chips
tbl = s.shapes[-1].table
tbl.rows[0].height = Inches(0.36)
for i in range(1, 5):
    tbl.rows[i].height = Inches(1.0)
ytop = y0 + 0.36
tw = sum(cwid)
xs = [0.54 + sum(cwid[:k]) / tw * 9.75 for k in range(7)]
for i, r in enumerate(rows5):
    cy = ytop + i * 1.0
    status_chip(s, xs[4] + 0.04, cy + 0.3, (xs[5] - xs[4]) - 0.08, 0.4, r[4], size=9)
    # Bloom chips L2 L4/L6 L3 L5  (state: 0 none, 1 partial)
    labels = ["L2", "L4+6", "L3", "L5"]
    state = [r[5][0], 1, r[5][1], 0]
    for k, (lab, st) in enumerate(zip(labels, state)):
        bx = xs[5] + 0.06 + (k % 2) * 0.44
        by = cy + 0.2 + (k // 2) * 0.32
        add_box(s, bx, by, 0.42, 0.26, lab, fill=AMBER if st else GREY_BG, line=None if st else GREY,
                size=8, color=WHITE if st else GREY, bold=True, margin=0.0, shape=MSO_SHAPE.RECTANGLE)
add_text(s, 0.54, 5.78, 9.75, 0.3, [[R("Status key: ", bold=True),
                                      R("Completed (none yet)  |  Partially completed  |  Pending  |  Blocked (awaiting cross-owner approval)")]], size=10)
add_text(s, 0.54, 6.08, 9.75, 0.7,
         [[R("Bloom (PRD App-B): ", bold=True),
           R("L2 survey, L4 analyse + L6 design (designs are Draft), L3 develop and integrate, L5 evaluate. Amber = partial, grey = not started. "
             "No L5 evaluation has run. S2: no survey found on main. Status judged on main; PR work is never counted as completed.")]],
         size=10, color=INK)

# ---------------------------------------------------------------- 6 Architecture
s = S[5]
clear_slide(s)
set_title(s, "Methodology and system architecture", 24)
G = dict(fill=GREEN_BG, line=GREEN)
A = dict(fill=AMBER_BG, line=AMBER, dash=True)
P = dict(fill=GREY_BG, line=GREY, dash=True)
X = dict(fill=BLUE_BG, line=PURPLE)
add_text(s, 0.4, 0.98, 1.4, 0.25, "1 Users", size=10, bold=True, color=PURPLE)
add_text(s, 1.95, 0.98, 1.7, 0.25, "2 Platforms", size=10, bold=True, color=PURPLE)
add_text(s, 3.85, 0.98, 1.5, 0.25, "3 Gateway", size=10, bold=True, color=PURPLE)
add_text(s, 5.5, 0.98, 2.3, 0.25, "4 LearnOps modules", size=10, bold=True, color=PURPLE)
add_text(s, 7.95, 0.98, 2.45, 0.25, "5 Shared libraries / services", size=10, bold=True, color=PURPLE)
# col1 actors
add_box(s, 0.4, 1.3, 1.35, 0.8, ["Mentor", "launches from course"], size=10, **X)
add_box(s, 0.4, 2.25, 1.35, 0.8, ["Administrator", "restores .mbz"], size=10, **X)
add_box(s, 0.4, 3.2, 1.35, 0.8, ["Learner", "refused by baseline tools"], size=10, **X)
# col2
add_box(s, 2.0, 1.3, 1.6, 1.75, [[R("Moodle 4.5 / 5.3", bold=True)], "Restore, web services, LTI tool registration"], size=10, **X)
add_box(s, 2.0, 3.2, 1.6, 1.0, [[R("BigBlueButton 3.0", bold=True)], "recordings via API, to M4 Video"], size=10, **X)
add_box(s, 2.0, 4.35, 1.6, 0.85, [[R("AI providers", bold=True)], "local (lab) or hosted, reached only via model interface"], size=10, **dict(P, line=GREY))
# col3
add_box(s, 3.85, 1.3, 1.4, 1.75, [[R("LTI 1.3 gateway", bold=True)], "lti library: ADR only in PR #83. Not built"], size=10, **P)
# col4 modules
mods = [("M1 Course Studio", "S1 · design Draft"), ("M2 Checker + harness", "S2 · design Draft"),
        ("M3 Grading assistant", "S3 · design Draft"), ("M4 Video pipeline", "S4 · design Draft")]
for i, (a, b) in enumerate(mods):
    add_box(s, 5.5, 1.3 + i * 0.97, 2.2, 0.85, [[R(a, bold=True)], b + ", no feature code"], size=10, **P)
# col5 shared
sh = [
    ("Merged", ["Contracts B1, B6 manifest + validator"], G),
    ("Merged", ["media_paths: validation + signing"], G),
    ("Open PRs", ["B2-B5, B6.2, B7; media_paths templates #85"], A),
    ("Open / draft", ["model_interface #35; moodle_ws PRs"], A),
    ("Planned", ["PostgreSQL 16 (schema per module)"], P),
    ("Planned", ["Job queue + worker containers"], P),
]
for i, (tag, txt, st) in enumerate(sh):
    add_box(s, 7.95, 1.3 + i * 0.66, 2.45, 0.58, [[R(txt[0], size=9.5)]], size=9.5, **st)
# arrows
add_arrow(s, 1.75, 1.7, 2.0, 1.7, PURPLE)
add_arrow(s, 1.75, 2.65, 2.0, 2.4, PURPLE)
add_arrow(s, 3.6, 2.15, 3.85, 2.15, PURPLE)
add_arrow(s, 5.25, 2.15, 5.5, 2.15, GREY, dash=True)
add_arrow(s, 7.7, 2.8, 7.95, 2.8, GREY, dash=True)
# bottom: CI + harness + flow note
add_box(s, 0.4, 5.38, 3.9, 0.62, [[R("CI on main (merged): ", bold=True), R("success at ecb4389; 2049 tests, mypy clean")]],
        size=10, **G)
add_box(s, 4.45, 5.38, 3.1, 0.62, [[R("Integration harness + role tests", bold=True)], "Playwright, not built"], size=10, **P)
add_box(s, 7.7, 5.38, 2.7, 0.62, [[R("Outputs: ", bold=True), R(".mbz, hidden grade drafts, media by relative path")]], size=9.5, **P)
legend(s, 0.4, 6.2)
add_text(s, 0.4, 6.42, 10, 0.4,
         "Flow: Mentor/Admin → Moodle → LTI 1.3 → modules → libraries/services → Moodle restore, web-services drafts, media store. "
         "Dashed = not yet running. Stack: Python 3.12, FastAPI, React + TypeScript, Docker Compose.",
         size=9.5, color=GREY)

# ---------------------------------------------------------------- 7 Datasets
s = S[6]
clear_slide(s)
set_title(s, "Dataset and computing requirements", 24)
tag_banner(s, "0 of 6 datasets complete. Status = origin/main at ecb4389 plus open PRs. Local-only work is not counted.", size=10.5)
hdr7 = ["Set", "Owner", "Purpose", "GitHub status", "Missing / dependency"]
rows7 = [
    hdr7,
    ["B8.1 Template course", "S1", "Restore tests with protected items", "Main: requirements README only (#57)", "No .mbz; needs lab Moodle"],
    ["B8.2 Sample course", "S1", "4-week fictional course per B1", "Open #61, changes requested", "B1 amendments settle first"],
    ["B8.3 Planted-error courses", "S2", "Checker detection (G-2)", "No PR found", "B8.2 + CK rule catalogue"],
    ["B8.4 Synthetic submissions", "S3", "Grading agreement (G-5)", "Open #31: 6 pilot, target 30+", "Mentor reference grades"],
    ["B8.5 Lecture videos", "S4", "WER and pipeline (G-6)", "Main: checker, tests, SHA-256 inventory, outlines, transcripts", "Title, speaker, duration, consent PENDING"],
    ["B8.6 Model comparison", "S3", "Model choice (G-10)", "Draft #33: 1 transcript", "Depends on B8.4, model_interface"],
]
fills7 = {(1, 3): AMBER_BG, (2, 3): AMBER_BG, (3, 3): GREY_BG, (4, 3): AMBER_BG, (5, 3): GREEN_BG, (6, 3): AMBER_BG}
add_table(s, 0.54, 1.38, 9.75, [1.65, 0.6, 1.9, 2.9, 2.3], rows7, size=10, row_h=0.56, fills=fills7)
add_box(s, 0.54, 5.52, 4.8, 1.25,
        [[R("Formats and validation", bold=True, color=PURPLE)],
         "Moodle .mbz, JSON (B1, B6), Markdown, media by relative path. CI validate_examples: 3 examples / 2 schemas. "
         "B8.5 checker with tests on main. Recordings are not stored in Git."],
        fill=WHITE, line=PURPLE, size=10, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, margin=0.1)
add_box(s, 5.49, 5.52, 4.8, 1.25,
        [[R("Computing", bold=True, color=PURPLE)],
         "Datasets need no GPU. B8.1 and role tests need a Moodle instance (lab unconfirmed). "
         "No sizes beyond PRD minimums: 30+ submissions, 5+ lectures, 30+ min."],
        fill=WHITE, line=PURPLE, size=10, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, margin=0.1)

# ---------------------------------------------------------------- 8 HPC
s = S[7]
clear_slide(s)
set_title(s, "HPC lab requirement details", 26)
tag_banner(s, "HPC / GPU is not required for Release 0. Lab VMs are specified in PRD A11 but not evidenced on GitHub.", size=10.5)
add_text(s, 0.54, 1.35, 4.9, 0.3, "Planned lab resources (PRD A11)", size=12, bold=True, color=PURPLE)
rows8 = [["VM", "Contents", "Evidence"],
         ["moodle45", "Moodle 4.5, PHP 8.3, PostgreSQL 16", "None"],
         ["moodle53", "Moodle 5.3, same stack", "None"],
         ["bbb", "BigBlueButton 3.0, video format", "None ('No lab access')"],
         ["tools", "Docker host for LearnOps services", "None"],
         ["AI services", "Local LLM + speech endpoints from guide", "None"]]
add_table(s, 0.54, 1.7, 4.9, [1.0, 2.4, 1.5], rows8, size=10, row_h=0.46, fills={(i, 2): GREY_BG for i in range(1, 6)})
add_text(s, 5.7, 1.35, 4.6, 0.3, "What is used and needed", size=12, bold=True, color=PURPLE)
add_box(s, 5.7, 1.7, 4.59, 1.1,
        [[R("Used so far", bold=True, color=GREEN)],
         "Developer machines (Python 3.12, Git, Claude Code) and GitHub CI. No GPU specification is claimed."],
        fill=GREEN_BG, line=GREEN, size=10.5, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, margin=0.1)
add_box(s, 5.7, 2.9, 4.59, 1.25,
        [[R("GPU / HPC need", bold=True, color=AMBER)],
         "None now: R0 is contracts, libraries, CI and data. PRD OPS-11: no module may require a local GPU. "
         "Whisper-family speech and small local models (R3, R4) may use lab GPUs or a hosted API."],
        fill=AMBER_BG, line=AMBER, size=10.5, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, margin=0.1)
add_box(s, 5.7, 4.25, 4.59, 1.0,
        [[R("Moodle compatibility", bold=True, color=PURPLE)],
         "Must work on 4.5 and 5.3. Web-service function checks (App-C item 1) need the lab: 0 of 10 App-C items done."],
        fill=BLUE_BG, line=PURPLE, size=10.5, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, margin=0.1)
add_box(s, 0.54, 4.95, 4.9, 1.8,
        [[R("External AI endpoints", bold=True, color=PURPLE)],
         "Reached only through the model interface (B5), local or hosted. Provider choice is configuration. "
         "No endpoint or key is in the repository; none has been called by a module yet."],
        fill=GREY_BG, line=GREY, dash=True, size=10.5, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, margin=0.1)
add_box(s, 5.7, 5.35, 4.59, 1.4,
        [[R("To confirm with the guide", bold=True, color="C62828")],
         "Lab VM and AI-endpoint access dates; GPU model if any; whether CI runners suffice for Playwright role tests."],
        fill=WHITE, line="C62828", size=10.5, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, margin=0.1)

# ---------------------------------------------------------------- 9 Evidence
s = S[8]
clear_slide(s)
set_title(s, "Implementation evidence and preliminary results", 22)
tiles = [("55 / 96", "PRs merged to main"), ("31", "open PRs (9 draft)"), ("2049", "tests passed, CI on main"),
         ("0 / 7", "contracts frozen")]
for i, (n, l) in enumerate(tiles):
    add_box(s, 0.54 + i * 2.46, 1.0, 2.3, 0.85, [[R(n, size=22, bold=True, color=PURPLE if i != 3 else "C62828")], R(l, size=10)],
            fill=BLUE_BG if i != 3 else "FDECEC", line=None, size=10, margin=0.04)
# chart
cd = CategoryChartData()
cd.categories = ["S1 Akshita", "S2 Shraddha", "S3 Harshitha", "S4 Nagashree"]
cd.add_series("Merged to main", (7, 4, 2, 10))
cd.add_series("Merged to stacked branch", (0, 1, 5, 0))
cd.add_series("Open", (6, 3, 9, 4))
cd.add_series("Draft", (0, 0, 3, 6))
cd.add_series("Closed unmerged", (1, 0, 0, 3))
gf = s.shapes.add_chart(XL_CHART_TYPE.BAR_STACKED, Inches(0.54), Inches(1.95), Inches(5.0), Inches(3.2), cd)
ch = gf.chart
ch.has_title = True
ch.chart_title.text_frame.text = "Student pull requests by status (64 PRs)"
ch.chart_title.text_frame.paragraphs[0].runs[0].font.size = Pt(11)
ch.chart_title.text_frame.paragraphs[0].runs[0].font.bold = True
ch.has_legend = True
ch.legend.position = XL_LEGEND_POSITION.BOTTOM
ch.legend.include_in_layout = False
ch.legend.font.size = Pt(9)
cols = [GREEN, "7BB77E", AMBER, "E3B04B", "9AA0AB"]
for ser, c in zip(ch.plots[0].series, cols):
    ser.format.fill.solid()
    ser.format.fill.fore_color.rgb = rgb(c)
pl = ch.plots[0]
pl.gap_width = 45
pl.has_data_labels = True
pl.data_labels.number_format = '0;;;'
pl.data_labels.number_format_is_linked = False
pl.data_labels.font.size = Pt(10)
pl.data_labels.font.color.rgb = rgb(WHITE)
pl.data_labels.position = XL_LABEL_POSITION.CENTER
ch.category_axis.tick_labels.font.size = Pt(10)
ch.category_axis.reverse_order = True
ch.value_axis.tick_labels.font.size = Pt(9)
ch.value_axis.has_major_gridlines = False
# right: A / B / C
add_box(s, 5.7, 1.95, 4.59, 1.05,
        [[R("A. Merged into main", bold=True, color=GREEN)],
         "CI + review bot; contracts validator; B1 schema; B6 manifest; media_paths validation + signing; B8.5 checker; 4 Draft designs"],
        fill=GREEN_BG, line=GREEN, size=9.5, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, margin=0.08)
add_box(s, 5.7, 3.07, 4.59, 1.05,
        [[R("B. Submitted, not merged", bold=True, color=AMBER)],
         "B2 #46, B3 #83, B4 #27, B5 #25, B7 #54, B6.2 #93, model_interface #35 (draft), moodle_ws, B8.2 #61, B8.4 #31, B8.6 #33 (draft)"],
        fill=AMBER_BG, line=AMBER, dash=True, size=9.5, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, margin=0.08)
add_box(s, 5.7, 4.19, 4.59, 0.96,
        [[R("C. Measured results (CI on main, ecb4389)", bold=True, color=PURPLE)],
         "Success. 2049 tests passed; mypy clean on 30 files; 3 examples validated against 2 schemas; 137 CI-script tests"],
        fill=BLUE_BG, line=PURPLE, size=9.5, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, margin=0.08)
add_text(s, 0.54, 5.3, 9.75, 1.5,
         [{"runs": [R("Collaboration: ", bold=True), R("131 reviews on others' PRs (S1 23, S2 29, S3 32, S4 47); guide merged 32 scaffolding PRs, students 23 to main.")], "bullet": True},
          {"runs": [R("Honest limits: ", bold=True), R("tests cover contracts, validators, libraries and CI scripts. No module feature, no deployment URL, no lab run.")], "bullet": True},
          {"runs": [R("Not mixed: ", bold=True), R("local uncommitted work (e.g. branch video/b6-media-paths) is excluded; PR numbers label non-main items.")], "bullet": True}],
         size=10.5, space_after=3)

# ---------------------------------------------------------------- 10 Demo
s = S[9]
clear_slide(s)
set_title(s, "Demonstration", 28)
tag_banner(s, "The demonstration is repository, contract-validation and CI evidence. No module feature is demonstrable yet.", size=10.5)
cw3 = 3.1
colsd = [
    ("From main (live)", GREEN, GREEN_BG, False, [
        "GitHub contribution and PR list",
        "CI run on main (ecb4389): 2049 tests",
        "validate_examples on B1 and manifest examples",
        "media_paths validation and signing tests"]),
    ("From an open PR branch (label it)", AMBER, AMBER_BG, True, [
        "#93 B6.2 contract examples",
        "#85 media_paths templates",
        "#35 model_interface (draft): fake provider tests",
        "Say clearly: not merged"]),
    ("Cannot be shown yet", GREY, GREY_BG, True, [
        "Studio building a course",
        "Checker catching planted errors",
        "Grading draft in Moodle",
        "Video captions; any deployment URL"]),
]
for i, (h, c, bg, dash, its) in enumerate(colsd):
    x = 0.54 + i * (cw3 + 0.225)
    add_box(s, x, 1.4, cw3, 0.4, h, fill=c, line=None, size=11, color=WHITE, bold=True, shape=MSO_SHAPE.RECTANGLE)
    add_box(s, x, 1.8, cw3, 2.3, [{"runs": [R(t)], "bullet": True} for t in its], fill=bg, line=c, dash=dash, size=11,
            align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, margin=0.12, space_after=5, shape=MSO_SHAPE.RECTANGLE)
add_text(s, 0.54, 4.3, 9.75, 0.3, "Suggested sequence (about 5 minutes)", size=12, bold=True, color=PURPLE)
steps = ["1 Repo and PR list", "2 CI run on main", "3 Contract validation", "4 media_paths tests", "5 One open PR, labelled"]
for i, t in enumerate(steps):
    x = 0.54 + i * 1.97
    add_box(s, x, 4.7, 1.75, 0.75, t, fill=PURPLE if i < 4 else AMBER, line=None, size=11, color=WHITE, bold=True,
            shape=MSO_SHAPE.CHEVRON if False else MSO_SHAPE.ROUNDED_RECTANGLE)
    if i < 4:
        add_arrow(s, x + 1.76, 5.08, x + 1.96, 5.08, GREY)
add_text(s, 0.54, 5.65, 9.75, 1.1,
         [{"runs": [R("Run from a fresh clone of main so local edits are not mixed in. Keep CI screenshots as a fallback.")], "bullet": True},
          {"runs": [R("Deployment: none. Justification: no module feature exists and the lab is unconfirmed (slide 8).")], "bullet": True}],
         size=11, space_after=3)

# ---------------------------------------------------------------- 11 Remaining
s = S[10]
clear_slide(s)
set_title(s, "Remaining work, timeline and risks", 24)
tag_banner(s, "PROPOSED timeline: relative weeks, not agreed deadlines. Confirm dates with the guide.", size=10.5)
hdr11 = ["Owner", "Weeks 1-2", "Weeks 3-4", "Weeks 5-8 (before final)"]
rows11 = [
    hdr11,
    ["S1 Akshita", "Settle Issue #65 and B1 amendments (#87, #94, #101); rework #54, #61", "B8.1 backup (needs lab); merge B8.2; studio literature", "Studio design to guide for approval"],
    ["S2 Shraddha", "Rework B2 #46; resolve B3 #83 and ADR 0001", "Validate B2 and B3 in CI; start lti library", "B8.3 planted errors; checker design approval"],
    ["S3 Harshitha", "Land approved B4 #27, B5 #25; cut open PR load (12)", "model_interface #35, moodle_ws stack; B8.4 to 30+", "B8.6; design #62 approval"],
    ["S4 Nagashree", "Merge #93, #85; fix ADR 0005/0006 clash; fix #96 and #97 checks", "B8.5 consent, durations, transcripts; speech ADR #98", "Literature 1 to 6+; WER prep; design approval"],
    ["Guide / all", "Contract review session", "Freeze contracts B1-B8", "Approve 4 designs; lab App-C 0 of 10"],
]
fl11 = {(5, c): BLUE_BG for c in range(4)}
add_table(s, 0.54, 1.38, 9.75, [1.25, 3.1, 2.8, 2.6], rows11, size=9.5, row_h=0.62, fills=fl11, header_size=10)
add_text(s, 0.54, 5.2, 4.7, 0.3, "Release 0 gates today", size=11.5, bold=True, color=PURPLE)
gates = [("0/7", "contracts frozen"), ("0/4", "designs approved"), ("0/6", "datasets done"), ("0/10", "App-C items")]
for i, (n, l) in enumerate(gates):
    add_box(s, 0.54 + i * 1.18, 5.52, 1.1, 0.85, [[R(n, size=16, bold=True, color="C62828")], R(l, size=9)],
            fill="FDECEC", line=None, size=9, margin=0.02)
add_text(s, 5.3, 5.2, 5.0, 0.3, "Main risks and dependencies", size=11.5, bold=True, color=PURPLE)
add_text(s, 5.3, 5.5, 5.0, 1.3,
         [{"runs": [R("Lab unconfirmed; blocks App-C, B8.1, role tests")], "bullet": True},
          {"runs": [R("Review throughput: S3 holds 12 open PRs")], "bullet": True},
          {"runs": [R("B1 / B2 drift (#65); ADR number clash")], "bullet": True},
          {"runs": [R("B8.5 needs real speaker consent")], "bullet": True}],
         size=10, space_after=1)
add_text(s, 0.54, 6.42, 4.7, 0.4, "Guidelines PDF lists 12-14 Nov 2026; audit date is 16 Nov. Confirm slot.", size=9, color=GREY)

# ---------------------------------------------------------------- 12 SDG
s = S[11]
clear_slide(s)
set_title(s, "Sustainable Development Goals (SDG) aligned to the project", 22)
tag_banner(s, "PROPOSED alignment: no approved SDG mapping found. Contributions are intended, not measured.", size=10.5)
add_box(s, 0.54, 1.45, 2.3, 2.3, [[R("SDG 4", size=30, bold=True, color=WHITE)], R("Quality Education", size=14, bold=True, color=WHITE),
                                  R("sdgs.un.org/goals/goal4", size=10, color=WHITE)],
        fill="C5192D", line=None, margin=0.1)
sdg = [
    ("Target 4.3", "Equal access to affordable, quality technical, vocational and tertiary education.",
     "Open-source tools lower the cost of running project-based Moodle courses. A checker aims to catch design errors before learners see them. Intended."),
    ("Target 4.4", "More youth and adults with relevant technical and vocational skills.",
     "Mentors spend less time on setup and grading so more project work can be supported. Targets (G-1, G-4) are unmeasured."),
    ("Target 4.5", "Equal access to education for the vulnerable, including persons with disabilities.",
     "Captions, chapters and low-data playback aim to make lectures usable. Captions are Release 3; low-data is an extension. Not built."),
]
for i, (t, d, j) in enumerate(sdg):
    y = 1.45 + i * 0.95
    add_box(s, 3.0, y, 1.15, 0.85, t, fill=PURPLE, line=None, size=11, color=WHITE, bold=True, shape=MSO_SHAPE.RECTANGLE)
    add_box(s, 4.15, y, 6.14, 0.85, [[R(d, bold=True)], R(j)], fill=GREY_BG, line=None, size=9.5, align=PP_ALIGN.LEFT,
            shape=MSO_SHAPE.RECTANGLE, margin=0.08)
add_box(s, 0.54, 4.45, 9.75, 1.0,
        [[R("Why only SDG 4", bold=True, color=PURPLE)],
         "Other goals would be weak links for a Moodle tooling project, so none is claimed. The two-line justification per target is above; "
         "target wording is shortened from the UN SDG site (sdgs.un.org/goals/goal4)."],
        fill=WHITE, line=PURPLE, size=10.5, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, margin=0.1)
add_box(s, 0.54, 5.6, 9.75, 0.75,
        "Team action: confirm the SDG mapping with the guide. No educational or accessibility impact has been measured.",
        fill=AMBER_BG, line=AMBER, size=10.5, color=AMBER, bold=True, align=PP_ALIGN.LEFT, margin=0.1)

# ---------------------------------------------------------------- 13 Conclusion
s = S[12]
clear_slide(s)
set_title(s, "Conclusion", 28)
add_box(s, 0.54, 1.1, 4.8, 1.15,
        [[R("Aim", bold=True, color=PURPLE)],
         "Cut mentor time on course creation, checking, grading and video, beside an unmodified Moodle, with measured targets."],
        fill=BLUE_BG, line=None, size=10.5, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, margin=0.1)
add_box(s, 5.49, 1.1, 4.8, 1.15,
        [[R("Next milestone", bold=True, color=PURPLE)],
         "Settle B1 / B2 (#65), merge approved contract PRs, then freeze contracts. Confirm lab access."],
        fill=BLUE_BG, line=None, size=10.5, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, margin=0.1)
add_box(s, 0.54, 2.38, 4.8, 2.0,
        [[R("Established in Release 0 (merged)", bold=True, color=GREEN)],
         {"runs": [R("CI, review bot and handbook on main")], "bullet": True},
         {"runs": [R("Contract validator, B1, B6 manifest")], "bullet": True},
         {"runs": [R("media_paths validation and signing")], "bullet": True},
         {"runs": [R("B8.5 checker; 131 student peer reviews")], "bullet": True}],
        fill=GREEN_BG, line=GREEN, size=10.5, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, margin=0.1)
add_box(s, 5.49, 2.38, 4.8, 2.0,
        [[R("Limitations", bold=True, color=AMBER)],
         {"runs": [R("No module feature or deployment yet")], "bullet": True},
         {"runs": [R("Lab unconfirmed; App-C 0 of 10")], "bullet": True},
         {"runs": [R("Literature survey incomplete")], "bullet": True},
         {"runs": [R("Approved objectives to be confirmed")], "bullet": True}],
        fill=AMBER_BG, line=AMBER, dash=True, size=10.5, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, margin=0.1)
add_text(s, 0.54, 4.5, 9.75, 0.3, "Release 0 readiness (PRD D1)", size=12, bold=True, color=PURPLE)
rd = [("0 of 7", "contracts frozen"), ("0 of 4", "designs approved"), ("1 of 5", "libraries functional"),
      ("0 of 6", "datasets complete"), ("0 of 10", "App-C verified")]
for i, (n, l) in enumerate(rd):
    add_box(s, 0.54 + i * 1.97, 4.85, 1.8, 0.95, [[R(n, size=18, bold=True, color="C62828")], R(l, size=10)],
            fill="FDECEC", line=None, size=10, margin=0.03)
add_box(s, 0.54, 5.95, 9.75, 0.8,
        "Honest assessment: the foundation is real and verified in CI, but Release 0 is not complete. Its exit criteria have not been met.",
        fill=PURPLE, line=None, size=12, color=WHITE, bold=True, margin=0.12, align=PP_ALIGN.LEFT)

# ---------------------------------------------------------------- 14 References
s = S[13]
clear_slide(s)
set_title(s, "References", 28)
refs = [
    "[1] LearnOps Product Requirements Document, v1.0 (draft). docs/PRD.md, https://github.com/narenccode/learnops",
    "[2] LearnOps, \"GETTING-STARTED.md,\" docs/, https://github.com/narenccode/learnops",
    "[3] narenccode/learnops, main branch at commit ecb4389, GitHub audit fetched 16 Nov 2026.",
    "[4] T. Javed et al., \"Svarah: Evaluating English ASR Systems on Indian Accents,\" arXiv:2305.15760, v1, May 2023. https://arxiv.org/abs/2305.15760 (audit: docs/literature-video.md)",
    "[5] Moodle Docs, https://docs.moodle.org ; Moodle Developer Resources, https://moodledev.io",
    "[6] 1EdTech, \"Learning Tools Interoperability (LTI) Core Specification 1.3,\" https://www.imsglobal.org/spec/lti/v1p3/",
    "[7] BigBlueButton Documentation, https://docs.bigbluebutton.org",
    "[8] United Nations, \"Goal 4: Quality Education,\" https://sdgs.un.org/goals/goal4",
    "[9] Approved project proposal: [not supplied; add reference].",
    "[10] Grading literature list (6 sources): in open PR #62, §12.1; not reproduced until merged and re-checked.",
]
add_text(s, 0.54, 1.1, 9.75, 5.6, [[R(r)] for r in refs], size=13, space_after=6)

# ---------------------------------------------------------------- 15 Thank you
s = S[14]
t = s.shapes.title
t.text_frame.paragraphs[0].runs[0].text = "Thank You"
p2 = t.text_frame.add_paragraph()
r = p2.add_run()
r.text = "Questions?"
r.font.size = Pt(28)
r.font.color.rgb = rgb(PURPLE)
r.font.bold = True
p2.alignment = PP_ALIGN.CENTER

# ---------------------------------------------------------------- notes
for i, sl in enumerate(S, 1):
    set_notes(sl, notes_text(i))

prs.save(OUT)
print("saved", OUT)
