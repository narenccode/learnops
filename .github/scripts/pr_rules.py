#!/usr/bin/env python3
"""Rule checks for a LearnOps pull request (no AI, no network except the GitHub CLI).

Reads the PR from the Actions event file plus the git diff, applies the rules from CLAUDE.md §7 and
PRD §A7, and writes one verdict comment and one label to the PR. It never approves, merges or closes.

Trust: CODEOWNERS, the PRD and the design documents are read from the BASE branch, never from the
PR, so a pull request cannot loosen its own checks.

Local use (nothing is posted without --post):
    python .github/scripts/pr_rules.py --event event.json --base origin/main --head HEAD
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field

MARKER = "<!-- learnops-pr-review -->"
MODULES = ("studio", "checker", "grading", "video")
SIZE_LIMIT = 800  # added + deleted lines, lockfiles excluded
LOCKFILES = (
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
    "uv.lock",
)

VERDICTS = {
    "rule-violation": (
        "Rule violation",
        "b60205",
        "Breaks a non-negotiable rule: guide decides",
    ),
    "needs-rework": ("Needs rework", "d93f0b", "Fix the listed items, then push again"),
    "needs-judgement": (
        "Needs your judgement",
        "fbca04",
        "A call only the guide can make",
    ),
    "awaiting-peer": (
        "Waiting for the peer review",
        "c5def5",
        "Rules passed: one peer approval is next",
    ),
    "ready-to-merge": (
        "Ready to merge",
        "0e8a16",
        "Peer approved and the bot review passed: the author may squash-merge",
    ),
}

SECRET_PATTERNS = [
    (re.compile(r"sk-[A-Za-z0-9_\-]{20,}"), "an API key (sk-…)"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "an AWS access key"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "a private key"),
    (re.compile(r"ghp_[A-Za-z0-9]{30,}"), "a GitHub token"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,}"), "a Slack token"),
    (
        re.compile(
            r"(?i)\b(api[_-]?key|secret|password|token)\b\s*[:=]\s*['\"][^'\"\s]{12,}['\"]"
        ),
        "a hard-coded secret value",
    ),
]
PROTECTED_DIRS = ("/var/www/moodle", "/var/www/html", "/usr/share/bigbluebutton")
MEDIA_URL = re.compile(r"https?://\S+\.(?:mp4|m4v|webm|vtt|m3u8|mpd)\b", re.IGNORECASE)
REQ_ID = re.compile(
    r"\b(?:FR-[A-Z]{1,2}-\d{2}|OPS-\d{2}|SEC-\d{2}|EXT-\d{2}|UI-\d{2}|C-\d{2}|G-\d{1,2})\b"
)


@dataclass
class Finding:
    level: str  # violation | rework | judgement | advice
    message: str
    ref: str = ""


@dataclass
class Context:
    title: str
    body: str
    author: str
    files: dict[str, str]  # path -> A / M / D / R
    numstat: dict[str, int]  # path -> added + deleted lines
    added: dict[str, list[str]]  # path -> added lines
    codeowners: str
    design_status: dict[str, str | None] = field(default_factory=dict)
    prd_ids: set[str] = field(default_factory=set)


# ---------------------------------------------------------------- CODEOWNERS


def parse_codeowners(text: str) -> list[tuple[str, list[str]]]:
    rules = []
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            pattern, *owners = line.split()
            rules.append((pattern, [o.lstrip("@").lower() for o in owners]))
    return rules


def owners_of(rules: list[tuple[str, list[str]]], path: str) -> list[str]:
    """Owners of the last matching rule (GitHub semantics for the patterns we use)."""
    found: list[str] = []
    for pattern, owners in rules:
        if pattern == "*":
            found = owners
        elif pattern.endswith("/"):
            if ("/" + path).startswith(pattern):
                found = owners
        elif fnmatch.fnmatch("/" + path, pattern):
            found = owners
    return found


def guide_of(rules: list[tuple[str, list[str]]]) -> str:
    sole = owners_of(rules, "CLAUDE.md")
    return sole[0] if len(sole) == 1 else ""


# -------------------------------------------------------------------- rules


def module_of(path: str) -> str:
    parts = path.split("/")
    return parts[1] if parts[0] == "modules" and len(parts) > 2 else ""


def is_test(path: str) -> bool:
    return path.startswith("tests/") or "/tests/" in path


def is_feature_code(path: str) -> bool:
    if not module_of(path) or is_test(path):
        return False
    return not path.endswith(".md")


def evaluate(ctx: Context) -> list[Finding]:
    rules = parse_codeowners(ctx.codeowners)
    guide = guide_of(rules)
    author = ctx.author.lower()
    paths = sorted(ctx.files)
    text = f"{ctx.title}\n{ctx.body}"
    out: list[Finding] = []

    feature = [p for p in paths if is_feature_code(p)]
    lib_code = [p for p in paths if p.startswith("libs/") and not is_test(p)]
    code = feature + lib_code

    # Requirement IDs
    ids = set(REQ_ID.findall(text))
    if code and not ids:
        out.append(
            Finding(
                "rework",
                "No requirement ID in the title or description.",
                "CLAUDE.md §7.1",
            )
        )
    if ctx.prd_ids:
        unknown = sorted(i for i in ids if i not in ctx.prd_ids)
        if unknown:
            out.append(
                Finding(
                    "rework", f"Not in the PRD: {', '.join(unknown)}.", "PRD Part C"
                )
            )

    # Contracts and the PRD
    touched = [
        p
        for p in paths
        if p.startswith(("contracts/", "libs/contracts/")) or p == "docs/PRD.md"
    ]
    if touched and author != guide:
        if "contract-change" not in text.lower():
            out.append(
                Finding(
                    "violation",
                    "Contract or PRD change without the `/contract-change` process: "
                    + ", ".join(touched[:5]),
                    "PRD §B.0",
                )
            )
        else:
            out.append(
                Finding(
                    "judgement",
                    "Contract change: every affected owner and the guide must review "
                    "(GitHub only enforces one).",
                    "PRD §B.0",
                )
            )

    # Guide-only files touched by a student
    guarded = [
        p
        for p in paths
        if p not in touched and owners_of(rules, p) == [guide] and author != guide
    ]
    if guarded:
        out.append(
            Finding(
                "judgement",
                "Touches guide-only files: " + ", ".join(guarded[:6]),
                "CODEOWNERS",
            )
        )

    # Design document gate
    for module in sorted({module_of(p) for p in feature}):
        status = ctx.design_status.get(module)
        if status != "Approved":
            if "release 0" in text.lower():
                out.append(
                    Finding(
                        "judgement",
                        f"`{module}` code while its design document is "
                        f"`{status or 'missing'}`: guide must confirm this is Release 0 foundation work.",
                        "CLAUDE.md §6a",
                    )
                )
            else:
                out.append(
                    Finding(
                        "violation",
                        f"`{module}` feature code but docs/design/{module}.md is "
                        f"`{status or 'missing'}` on main (must be Approved).",
                        "CLAUDE.md §6a.2",
                    )
                )
    for path, lines in ctx.added.items():
        if (
            path.startswith("docs/design/")
            and author != guide
            and any(re.search(r"\*\*Status:\*\*\s*Approved", ln) for ln in lines)
        ):
            out.append(
                Finding(
                    "violation",
                    f"{path}: only the guide sets `Approved`.",
                    "CLAUDE.md §6a.2",
                )
            )

    # Tests and traceability for feature code
    if feature and not any(is_test(p) for p in paths):
        out.append(
            Finding(
                "rework",
                "Feature code without any test file in this PR.",
                "CLAUDE.md §7.2",
            )
        )
    if feature and "docs/traceability.md" not in ctx.files:
        out.append(
            Finding(
                "rework", "docs/traceability.md not updated.", "CLAUDE.md §7.3, PRD §E4"
            )
        )

    # Other modules' files
    others = sorted(
        p
        for p in paths
        if (module_of(p) or p.startswith("libs/"))
        and owners_of(rules, p)
        and owners_of(rules, p)[0] != author
        and author != guide
    )
    if others:
        out.append(
            Finding(
                "advice",
                "Changes files owned by someone else; list and explain them in the description: "
                + ", ".join(others[:6]),
                "CLAUDE.md §7.8",
            )
        )

    # Content scans on added lines
    for path, lines in ctx.added.items():
        name = path.rsplit("/", 1)[-1]
        if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
            out.append(
                Finding("violation", f"{path}: environment file committed.", "PRD C-04")
            )
        if path.startswith(".github/scripts/"):
            continue  # the detector's own patterns
        joined = "\n".join(lines)
        for pattern, label in SECRET_PATTERNS:
            if pattern.search(joined):
                out.append(
                    Finding(
                        "violation", f"{path}: looks like {label}.", "PRD C-04, SEC"
                    )
                )
                break
        if not path.endswith(".md") and any(d in joined for d in PROTECTED_DIRS):
            out.append(
                Finding(
                    "judgement",
                    f"{path}: mentions a Moodle/BBB install path; confirm nothing there is modified.",
                    "PRD C-01",
                )
            )
        if path.startswith(("modules/", "libs/", "contracts/")) and not is_test(path):
            if MEDIA_URL.search(joined):
                out.append(
                    Finding(
                        "rework",
                        f"{path}: full media URL; store relative paths only.",
                        "PRD C-08",
                    )
                )

    # Size
    total = sum(
        n for p, n in ctx.numstat.items() if p.rsplit("/", 1)[-1] not in LOCKFILES
    )
    if total > SIZE_LIMIT:
        out.append(
            Finding(
                "rework",
                f"{total} changed lines (limit {SIZE_LIMIT}). Split into smaller PRs.",
                "CLAUDE.md §8",
            )
        )

    # Description
    stripped = re.sub(r"<!--.*?-->", "", ctx.body, flags=re.DOTALL)
    if re.search(r"^\s*[-*]\s*(\[\]|\[ ?\](?!\s))", ctx.body, flags=re.MULTILINE):
        out.append(
            Finding(
                "advice", "A checklist box is malformed; it must be `- [ ]` or `- [x]`."
            )
        )
    unchecked = len(re.findall(r"^\s*[-*] \[ \]", stripped, flags=re.MULTILINE))
    if unchecked:
        out.append(
            Finding(
                "advice",
                f"{unchecked} checklist box(es) unticked: tick them or write N/A.",
            )
        )
    module_field = re.search(r"Module:(?:\*\*)?[ \t]*(\S+)", stripped)
    if not module_field or module_field.group(1).lower().strip(",") not in (
        *MODULES,
        "libs",
    ):
        out.append(
            Finding(
                "advice",
                "Fill in `Module:` (studio, checker, grading, video or libs).",
            )
        )
    if not re.search(r"Release:(?:\*\*)?[ \t]*\S", stripped):
        out.append(Finding("advice", "Fill in `Release:`."))
    return out


def verdict_of(findings: list[Finding]) -> str:
    levels = {f.level for f in findings}
    if "violation" in levels:
        return "rule-violation"
    if "rework" in levels:
        return "needs-rework"
    if "judgement" in levels:
        return "needs-judgement"
    return "ready-to-merge"


VERDICT_MARK = re.compile(r"<!-- verdict:([a-z-]+) -->")


def peer_of(rules: list[tuple[str, list[str]]], author: str) -> str:
    """The author's peer reviewer: second owner of the module or library the author owns."""
    for pattern, owners in rules:
        if pattern.startswith(("/modules/", "/libs/")) and len(owners) > 1:
            if owners[0] == author.lower():
                return owners[1]
    return ""


def next_step(verdict: str, peer: str = "") -> str:
    """One plain sentence telling the team what to do now (mentions are neutralised)."""
    who = f" (@​{peer})" if peer else ""
    return {
        "needs-rework": "Fix the items listed in the bot comment and push. The bot re-checks by itself.",
        "rule-violation": "Do not merge. The guide will decide.",
        "needs-judgement": "Do not merge. The guide will decide.",
        "awaiting-peer": f"Ask your peer reviewer{who} to review and approve. "
        "The AI review runs right after.",
        "ready-to-merge": "Squash-merge it.",
    }[verdict]


def render(
    verdict: str,
    findings: list[Finding],
    sha: str,
    intro: str = "",
    footer: str = "",
    step: str = "",
    help_url: str = "",
) -> str:
    title = VERDICTS[verdict][0]
    sections = [
        ("violation", "Rule violations (the guide decides: reject or rework)"),
        ("rework", "Fix before merging"),
        ("judgement", "Needs the guide's judgement"),
        ("advice", "Better ways to do it (advice)"),
        ("unverified", "Could not verify"),
    ]
    lines = [MARKER, f"### Automated review: **{title}**", ""]
    if step:
        lines += [f"**Next step:** {step}", ""]
    if intro:
        lines += [intro, ""]
    for level, heading in sections:
        items = [f for f in findings if f.level == level]
        if items:
            lines.append(f"**{heading}**")
            lines += [
                f"- {f.message}" + (f" _({f.ref})_" if f.ref else "") for f in items
            ]
            lines.append("")
    if not findings:
        lines += ["No problems found.", ""]
    lines.append(
        f"<sub>{footer or 'Rules only. Peer review is always required.'}</sub>"
    )
    lines.append(
        f"<sub>Checked commit `{sha[:7]}`; re-checked on every push, review or description edit.</sub>"
    )
    if help_url:
        lines.append(f"<sub>[How the review works]({help_url})</sub>")
    lines.append(f"<!-- verdict:{verdict} -->")
    return "\n".join(lines)


# ---------------------------------------------------------------------- git


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, encoding="utf-8"
    )
    if check and result.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout if result.returncode == 0 else ""


def collect(event: dict, base: str, head: str) -> Context:
    pr = event["pull_request"]
    span = f"{base}...{head}"
    files = {}
    for line in git("diff", "--name-status", "--no-renames", span).splitlines():
        status, _, path = line.partition("\t")
        files[path] = status
    numstat = {}
    for line in git("diff", "--numstat", "--no-renames", span).splitlines():
        a, d, path = line.split("\t", 2)
        numstat[path] = (int(a) if a.isdigit() else 0) + (int(d) if d.isdigit() else 0)
    added: dict[str, list[str]] = {}
    current = ""
    for line in git("diff", "-U0", "--no-color", "--no-renames", span).splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
            added[current] = []
        elif line.startswith("+") and not line.startswith("+++") and current:
            added[current].append(line[1:])
    status = {}
    for module in MODULES:
        doc = git("show", f"{base}:docs/design/{module}.md", check=False)
        found = re.search(r"\*\*Status:\*\*\s*([A-Za-z ]+)", doc)
        status[module] = found.group(1).strip() if found else None
    return Context(
        title=pr.get("title") or "",
        body=pr.get("body") or "",
        author=pr["user"]["login"],
        files=files,
        numstat=numstat,
        added=added,
        codeowners=git("show", f"{base}:.github/CODEOWNERS", check=False),
        design_status=status,
        prd_ids=set(REQ_ID.findall(git("show", f"{base}:docs/PRD.md", check=False))),
    )


# ------------------------------------------------------------------ posting


def gh(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["gh", *args], capture_output=True, text=True, encoding="utf-8"
    )
    if check and result.returncode:
        raise RuntimeError(f"gh {' '.join(args[:3])}: {result.stderr.strip()}")
    return result.stdout


BOT = "github-actions[bot]"


def find_bot_comment(repo: str, number: int) -> tuple[str, str]:
    """(comment id, body) of the bot's verdict comment, or ("", "")."""
    out = gh(
        "api",
        "--paginate",
        f"repos/{repo}/issues/{number}/comments",
        "--jq",
        f'.[] | select(.user.login == "{BOT}" and (.body | contains("{MARKER}"))) | {{id: .id, body: .body}}',
        check=False,
    )
    for line in out.splitlines():
        if line.strip():
            item = json.loads(line)
            return str(item["id"]), item["body"]
    return "", ""


def post(repo: str, number: int, verdict: str, body: str) -> None:
    """Comment first (the part that matters), then label; a label failure must not lose the comment."""
    comment_id, _ = find_bot_comment(repo, number)
    if comment_id:
        gh(
            "api",
            "-X",
            "PATCH",
            f"repos/{repo}/issues/comments/{comment_id}",
            "-f",
            f"body={body}",
        )
    else:
        gh("api", f"repos/{repo}/issues/{number}/comments", "-f", f"body={body}")
    try:
        for name, (_, color, description) in VERDICTS.items():
            gh(
                "label",
                "create",
                name,
                "--color",
                color,
                "--description",
                description,
                "--force",
                "--repo",
                repo,
                check=False,
            )
        for name in VERDICTS:
            if name != verdict:
                gh(
                    "api",
                    "-X",
                    "DELETE",
                    f"repos/{repo}/issues/{number}/labels/{name}",
                    check=False,
                )
        # REST, not `gh pr edit`: that uses GraphQL, which the Actions token can be refused.
        gh("api", f"repos/{repo}/issues/{number}/labels", "-f", f"labels[]={verdict}")
    except Exception as error:
        print(f"::warning::comment posted but the label failed: {error}")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--event", required=True, help="GitHub event JSON (pull_request)"
    )
    parser.add_argument("--base", help="base ref (default origin/<base branch>)")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument(
        "--post", action="store_true", help="write label and comment to the PR"
    )
    args = parser.parse_args()

    with open(args.event, encoding="utf-8") as handle:
        event = json.load(handle)
    pr = event["pull_request"]
    base = args.base or f"origin/{pr['base']['ref']}"
    try:
        ctx = collect(event, base, args.head)
        guide = guide_of(parse_codeowners(ctx.codeowners))
        if ctx.author.lower() == guide:
            print("Guide's own PR: no review comment.")
            return 0
        findings = evaluate(ctx)
        verdict = verdict_of(findings)
        body = render(
            verdict,
            findings,
            pr.get("head", {}).get("sha") or git("rev-parse", args.head).strip(),
        )
    except Exception as error:  # never block a PR because the checker failed
        print(f"::warning::pr_rules failed: {error}")
        return 0
    print(body)
    print(f"\nlabel: {verdict}")
    if args.post:
        try:
            post(event["repository"]["full_name"], pr["number"], verdict, body)
        except Exception as error:
            print(f"::warning::could not post the result: {error}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
