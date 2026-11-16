#!/usr/bin/env python3
"""Read-only check of the lab BigBlueButton for PRD App-C item 4 (T17).

Calls only GET /api (version) and getRecordings. It never creates a meeting or a recording and
changes no configuration. Configuration comes from the environment: BBB_URL (API base, for
example https://<host>/bigbluebutton/) and BBB_SECRET. Neither is printed or written anywhere.
Output is a redacted JSON report: metadata key NAMES, format types, counts and booleans only.
No values, no playback URLs, no meeting or recording IDs (IDs are shown as a short hash).

Usage:  python verify_bbb.py [--out report.json] [--selftest]
Exit code: 0 all checks passed, 1 a check failed, 2 not configured / unreachable (PENDING).
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import http.client
import io
import json
import os
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

# Keys Moodle's mod_bigbluebuttonbn is expected to set (UNVERIFIED until this runs on the lab).
EXPECTED_MOODLE_KEYS = [
    "bbb-origin",
    "bbb-origin-tag",
    "bbb-origin-server-name",
    "bbb-context",
    "bbb-context-id",
    "bbb-context-label",
    "bbb-context-name",
    "bbb-recording-name",
]
PLACEHOLDERS = ("invalid", "CHANGE_ME")


def short(v: str) -> str:
    return hashlib.sha256(v.encode()).hexdigest()[:8]


def call(
    base: str, secret: str, action: str = "", query: str = "", algo: str = "sha256"
) -> ET.Element:
    url = base.rstrip("/") + "/api/" + action
    if action:
        cs = getattr(hashlib, algo)((action + query + secret).encode()).hexdigest()
        url += "?" + (query + "&" if query else "") + "checksum=" + cs
    with urllib.request.urlopen(url, timeout=15) as r:  # noqa: S310 (lab URL from env)
        return ET.fromstring(r.read())


def analyse_recordings(root: ET.Element) -> dict:
    recs = root.findall("./recordings/recording")
    out = {
        "returncode": root.findtext("returncode"),
        "recording_count": len(recs),
        "recordings": [],
    }
    for rec in recs:
        md = rec.find("metadata")
        meta = {c.tag: (c.text or "") for c in (md if md is not None else [])}
        fmts = [f.findtext("type") for f in rec.findall("./playback/format")]
        out["recordings"].append(
            {
                "id_hash": short(rec.findtext("recordID") or ""),
                "state": rec.findtext("state"),
                "published": rec.findtext("published"),
                "has_start_end_time": bool(
                    rec.findtext("startTime") and rec.findtext("endTime")
                ),
                "has_participants": rec.findtext("participants") is not None,
                "format_types": fmts,
                "has_video_format": "video" in fmts,
                "video_url_path_shape": _shape(rec, "video"),
                "metadata_keys": sorted(meta),
                "expected_moodle_keys_missing": [
                    k for k in EXPECTED_MOODLE_KEYS if not meta.get(k)
                ],
                "has_cohort_like_key": any("cohort" in k.lower() for k in meta),
            }
        )
    return out


def _shape(rec: ET.Element, fmt: str) -> str | None:
    for f in rec.findall("./playback/format"):
        if f.findtext("type") == fmt:
            p = urllib.parse.urlparse(f.findtext("url") or "")
            return (
                p.path.replace(rec.findtext("recordID") or "\0", "<recordID>") or None
            )
    return None


def valid_base_url(base: str) -> bool:
    """True only for an http(s) URL with a host. Never echoes the value."""
    try:
        p = urllib.parse.urlparse(base)
    except ValueError:
        return False
    return p.scheme in ("http", "https") and bool(p.netloc)


class _SyntheticHTTPError(http.client.HTTPException):
    """Test-only HTTPException subclass."""


def _http_exception_is_redacted() -> bool:
    """Offline: a stubbed urlopen raises HTTPExceptions with sensitive messages.

    main() must return the failure code 2, report only the class name, and leak the message
    neither to stdout nor to the --out report file. No network request is made.
    """
    sensitive = "SENSITIVE-https://labhost.test/api/?checksum=abc123-dummysecret"
    errors = [
        (_SyntheticHTTPError(sensitive), "_SyntheticHTTPError"),
        # IncompleteRead builds its message from the partial data, so put the text there.
        (http.client.IncompleteRead(sensitive.encode(), 5), "IncompleteRead"),
    ]
    env_keys = ("BBB_URL", "BBB_SECRET")
    saved_env = {k: os.environ.get(k) for k in env_keys}
    saved_urlopen, saved_argv = urllib.request.urlopen, sys.argv
    ok = True
    try:
        os.environ["BBB_URL"] = "https://labhost.test/bigbluebutton/"
        os.environ["BBB_SECRET"] = "dummysecret"
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "report.json")
            for exc, name in errors:

                def stub(*_a: object, _exc: BaseException = exc, **_k: object) -> None:
                    raise _exc

                urllib.request.urlopen = stub  # type: ignore[assignment]
                sys.argv = ["verify_bbb.py", "--out", out_path]
                buf = io.StringIO()
                try:
                    with contextlib.redirect_stdout(buf):
                        rc = main()
                except Exception:  # an escaping exception is the failure under test
                    return False
                with open(out_path, encoding="utf-8") as f:
                    report = f.read()
                combined = buf.getvalue() + report
                ok = (
                    ok
                    and rc == 2
                    and json.loads(report).get("error") == name
                    and "SENSITIVE" not in combined
                    and "labhost" not in combined
                    and "dummysecret" not in combined
                )
    finally:
        urllib.request.urlopen, sys.argv = saved_urlopen, saved_argv
        for k, v in saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return ok


def selftest() -> int:
    xml = """<response><returncode>SUCCESS</returncode><recordings><recording>
    <recordID>synthetic-1</recordID><state>published</state><published>true</published>
    <startTime>1</startTime><endTime>2</endTime><participants>0</participants>
    <metadata><bbb-origin>Moodle</bbb-origin><bbb-context-label>X</bbb-context-label></metadata>
    <playback><format><type>video</type><url>/video/synthetic-1/video-0.m4v</url></format></playback>
    </recording></recordings></response>"""
    r = analyse_recordings(ET.fromstring(xml))["recordings"][0]
    # Explicit checks, not `assert`, so they still run under `python -O`.
    if not (
        r["has_video_format"]
        and r["video_url_path_shape"] == "/video/<recordID>/video-0.m4v"
    ):
        print("selftest FAILED: video format / path shape", file=sys.stderr)
        return 1
    if not (
        "bbb-context-id" in r["expected_moodle_keys_missing"]
        and not r["has_cohort_like_key"]
    ):
        print("selftest FAILED: metadata key analysis", file=sys.stderr)
        return 1
    # URL validation: also exercised here so the new check is covered offline.
    good = valid_base_url("https://h.example/bigbluebutton/")
    bad = any(
        valid_base_url(u)
        for u in (
            "",
            "ftp://h.example/",
            "file:///etc/x",
            "h.example",
            "http://",
            "//h",
        )
    )
    if not good or bad:
        print("selftest FAILED: BBB_URL validation", file=sys.stderr)
        return 1
    if not _http_exception_is_redacted():
        print("selftest FAILED: HTTPException redaction", file=sys.stderr)
        return 1
    print("selftest OK (synthetic data only; proves the script logic, NOT the lab)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    base, secret = os.environ.get("BBB_URL", ""), os.environ.get("BBB_SECRET", "")
    rep: dict = {
        "configured": bool(
            base and secret and not any(p in base + secret for p in PLACEHOLDERS)
        )
    }
    code = 2
    if rep["configured"] and not valid_base_url(base):
        # Checked before any request. Fixed label only: never the URL, checksum or secret.
        rep["configured"] = False
        rep["error"] = "InvalidBaseUrl"
    if rep["configured"]:
        try:
            v = call(base, secret)
            rep["server_up"] = v.findtext("returncode") == "SUCCESS"
            rep["version"] = v.findtext("version")
            rep["bbb_version"] = v.findtext("bbbVersion")
            rec = analyse_recordings(call(base, secret, "getRecordings"))
            rep["recordings"] = rec
            rep["recording_api_ok"] = rec["returncode"] == "SUCCESS"
            rep["any_video_format"] = any(
                r["has_video_format"] for r in rec["recordings"]
            )
            code = 0 if rep["recording_api_ok"] and rep["any_video_format"] else 1
        except (
            urllib.error.URLError,
            http.client.HTTPException,  # e.g. IncompleteRead: not an OSError
            OSError,
            ET.ParseError,
            ValueError,
        ) as e:
            rep["error"] = type(e).__name__  # class only: messages may contain the URL
            rep["server_up"] = False
    text = json.dumps(rep, indent=2)
    print(text)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
