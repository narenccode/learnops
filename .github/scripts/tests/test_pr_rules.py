import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pr_rules as r  # noqa: E402

CODEOWNERS = """
*                       @s2 @s1 @guide
/modules/studio/        @s1 @s2 @guide
/modules/checker/       @s2 @s1 @guide
/libs/contracts/        @s1 @s2 @guide
/contracts/             @s1 @s2 @guide
/docs/                  @s1 @s2 @guide
/docs/PRD.md            @guide
/CLAUDE.md              @guide
/.github/               @guide
"""
GOOD_BODY = (
    "## What\nAdds X.\n\n**Requirements:** FR-S-03\n**Release:** Release 2\n**Module:** studio\n\n"
    "- [x] Requirement IDs listed above\n"
)


def ctx(
    files, title="Add thing FR-S-03", body=GOOD_BODY, author="s1", added=None, **kw
):
    return r.Context(
        title=title,
        body=body,
        author=author,
        files={f: "A" for f in files},
        numstat={f: 10 for f in files},
        added=added or {},
        codeowners=CODEOWNERS,
        design_status=kw.get("design_status", {"studio": "Approved"}),
        prd_ids=kw.get("prd_ids", {"FR-S-03", "C-04"}),
    )


def levels(findings):
    return sorted(f.level for f in findings)


def test_clean_docs_pr_is_ready():
    f = r.evaluate(ctx(["docs/design/studio.md"]))
    assert r.verdict_of(f) == "ready-for-guide"


def test_feature_code_complete_pr_is_ready():
    files = [
        "modules/studio/app.py",
        "modules/studio/tests/test_app.py",
        "docs/traceability.md",
    ]
    assert r.verdict_of(r.evaluate(ctx(files))) == "ready-for-guide"


def test_contract_change_without_process_is_violation():
    f = r.evaluate(ctx(["contracts/course.schema.json"]))
    assert r.verdict_of(f) == "rule-violation"


def test_contract_change_with_process_needs_judgement():
    f = r.evaluate(
        ctx(
            ["contracts/course.schema.json"],
            body=GOOD_BODY + "\nUses /contract-change.",
        )
    )
    assert r.verdict_of(f) == "needs-judgement"


def test_guide_edit_of_prd_not_flagged():
    f = r.evaluate(ctx(["docs/PRD.md"], author="guide"))
    assert r.verdict_of(f) == "ready-for-guide"


def test_student_touching_guide_only_file_needs_judgement():
    f = r.evaluate(ctx([".github/workflows/ci.yml"]))
    assert r.verdict_of(f) == "needs-judgement"


def test_code_without_requirement_id_needs_rework():
    f = r.evaluate(
        ctx(
            [
                "modules/studio/app.py",
                "modules/studio/tests/t.py",
                "docs/traceability.md",
            ],
            title="Add thing",
            body="**Release:** 2\n**Module:** studio",
        )
    )
    assert r.verdict_of(f) == "needs-rework"


def test_unknown_requirement_id_needs_rework():
    f = r.evaluate(ctx(["docs/x.md"], title="Add FR-S-99"))
    assert "Not in the PRD" in " ".join(x.message for x in f)


def test_feature_code_before_design_approval_is_violation():
    files = [
        "modules/studio/app.py",
        "modules/studio/tests/t.py",
        "docs/traceability.md",
    ]
    f = r.evaluate(ctx(files, design_status={"studio": "Draft"}))
    assert r.verdict_of(f) == "rule-violation"


def test_release_0_foundation_claim_needs_judgement():
    files = [
        "modules/studio/app.py",
        "modules/studio/tests/t.py",
        "docs/traceability.md",
    ]
    f = r.evaluate(
        ctx(
            files,
            body=GOOD_BODY + "\nRelease 0 foundation.",
            design_status={"studio": "Draft"},
        )
    )
    assert r.verdict_of(f) == "needs-judgement"


def test_student_cannot_set_approved():
    f = r.evaluate(
        ctx(
            ["docs/design/studio.md"],
            added={"docs/design/studio.md": ["**Status:** Approved"]},
        )
    )
    assert r.verdict_of(f) == "rule-violation"


def test_missing_tests_and_traceability_need_rework():
    f = r.evaluate(ctx(["modules/studio/app.py"]))
    assert r.verdict_of(f) == "needs-rework"
    assert len([x for x in f if x.level == "rework"]) == 2


def test_secret_in_added_line_is_violation():
    fake = "sk-" + "a" * 30
    f = r.evaluate(ctx(["docs/x.md"], added={"docs/x.md": [f"key = {fake}"]}))
    assert r.verdict_of(f) == "rule-violation"


def test_env_file_is_violation_but_example_is_not():
    bad = r.evaluate(ctx([".env"], added={".env": ["X=1"]}))
    ok = r.evaluate(ctx([".env.example"], added={".env.example": ["X=changeme"]}))
    assert r.verdict_of(bad) == "rule-violation"
    assert "environment file" not in " ".join(x.message for x in ok)


def test_full_media_url_in_code_needs_rework():
    line = 'url = "https://cdn.example.org/v/lesson.mp4"'
    files = [
        "modules/studio/app.py",
        "modules/studio/tests/t.py",
        "docs/traceability.md",
    ]
    f = r.evaluate(ctx(files, added={"modules/studio/app.py": [line]}))
    assert r.verdict_of(f) == "needs-rework"


def test_other_modules_file_is_advice_only():
    f = r.evaluate(ctx(["modules/checker/x.md"]))
    assert [x.level for x in f] == ["advice"]


def test_oversize_pr_needs_rework_and_lockfile_ignored():
    c = ctx(["docs/a.md", "package-lock.json"])
    c.numstat = {"docs/a.md": 500, "package-lock.json": 9000}
    assert r.verdict_of(r.evaluate(c)) == "ready-for-guide"
    c.numstat["docs/a.md"] = 900
    assert r.verdict_of(r.evaluate(c)) == "needs-rework"


def test_malformed_and_unticked_boxes_are_advice():
    body = GOOD_BODY + "- []  broken\n- [ ] open\n"
    f = r.evaluate(ctx(["docs/x.md"], body=body))
    messages = " ".join(x.message for x in f)
    assert "malformed" in messages and "unticked" in messages
    assert r.verdict_of(f) == "ready-for-guide"


def test_template_comments_do_not_count_as_filled():
    body = "**Release:** <!-- e.g. Release 2 -->\n**Module:** <!-- studio -->"
    f = r.evaluate(ctx(["docs/x.md"], body=body))
    assert sum(1 for x in f if x.level == "advice") >= 2


def test_codeowners_last_match_and_guide_detection():
    rules = r.parse_codeowners(CODEOWNERS)
    assert r.owners_of(rules, "docs/PRD.md") == ["guide"]
    assert r.owners_of(rules, "docs/design/x.md") == ["s1", "s2", "guide"]
    assert r.owners_of(rules, "README.md") == ["s2", "s1", "guide"]
    assert r.guide_of(rules) == "guide"


def test_render_has_marker_and_sections():
    f = [r.Finding("violation", "bad", "PRD C-04"), r.Finding("advice", "meh")]
    text = r.render("rule-violation", f, "abcdef123")
    assert text.startswith(r.MARKER) and "Rule violation" in text and "abcdef1" in text


def test_post_comments_first_and_survives_label_failure(monkeypatch):
    calls = []

    def fake_gh(*args, check=True):
        calls.append(args)
        if args[:2] == ("api", "--paginate"):
            return ""
        if "labels[]=ready-for-guide" in args:
            raise RuntimeError("refused")
        return ""

    monkeypatch.setattr(r, "gh", fake_gh)
    r.post("o/r", 7, "ready-for-guide", "body")
    posted = [c for c in calls if c[0] == "api" and "body=body" in c]
    assert posted, "comment must be posted"
    assert calls.index(posted[0]) < next(
        i for i, c in enumerate(calls) if c[:2] == ("label", "create")
    )
    assert not any(c[:2] == ("pr", "edit") for c in calls)


def test_post_updates_existing_bot_comment(monkeypatch):
    calls = []

    def fake_gh(*args, check=True):
        calls.append(args)
        return "123\n" if args[:2] == ("api", "--paginate") else ""

    monkeypatch.setattr(r, "gh", fake_gh)
    r.post("o/r", 7, "needs-rework", "body")
    assert any("PATCH" in c and "repos/o/r/issues/comments/123" in c for c in calls)
    assert 'user.login == "github-actions[bot]"' in " ".join(calls[0])
