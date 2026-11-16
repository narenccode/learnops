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
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

# Keys Moodle's mod_bigbluebuttonbn is expected to set (UNVERIFIED until this runs on the lab).
EXPECTED_MOODLE_KEYS = [
    "bbb-origin", "bbb-origin-tag", "bbb-origin-server-name", "bbb-context",
    "bbb-context-id", "bbb-context-label", "bbb-context-name", "bbb-recording-name",
]
PLACEHOLDERS = ("invalid", "CHANGE_ME")


def short(v: str) -> str:
    return hashlib.sha256(v.encode()).hexdigest()[:8]


def call(base: str, secret: str, action: str = "", query: str = "", algo: str = "sha256") -> ET.Element:
    url = base.rstrip("/") + "/api/" + action
    if action:
        cs = getattr(hashlib, algo)((action + query + secret).encode()).hexdigest()
        url += "?" + (query + "&" if query else "") + "checksum=" + cs
    with urllib.request.urlopen(url, timeout=15) as r:  # noqa: S310 (lab URL from env)
        return ET.fromstring(r.read())


def analyse_recordings(root: ET.Element) -> dict:
    recs = root.findall("./recordings/recording")
    out = {"returncode": root.findtext("returncode"), "recording_count": len(recs), "recordings": []}
    for rec in recs:
        md = rec.find("metadata")
        meta = {c.tag: (c.text or "") for c in (md if md is not None else [])}
        fmts = [f.findtext("type") for f in rec.findall("./playback/format")]
        out["recordings"].append({
            "id_hash": short(rec.findtext("recordID") or ""),
            "state": rec.findtext("state"),
            "published": rec.findtext("published"),
            "has_start_end_time": bool(rec.findtext("startTime") and rec.findtext("endTime")),
            "has_participants": rec.findtext("participants") is not None,
            "format_types": fmts,
            "has_video_format": "video" in fmts,
            "video_url_path_shape": _shape(rec, "video"),
            "metadata_keys": sorted(meta),
            "expected_moodle_keys_missing": [k for k in EXPECTED_MOODLE_KEYS if not meta.get(k)],
            "has_cohort_like_key": any("cohort" in k.lower() for k in meta),
        })
    return out


def _shape(rec: ET.Element, fmt: str) -> str | None:
    for f in rec.findall("./playback/format"):
        if f.findtext("type") == fmt:
            p = urllib.parse.urlparse(f.findtext("url") or "")
            return p.path.replace(rec.findtext("recordID") or "\0", "<recordID>") or None
    return None


def selftest() -> int:
    xml = """<response><returncode>SUCCESS</returncode><recordings><recording>
    <recordID>synthetic-1</recordID><state>published</state><published>true</published>
    <startTime>1</startTime><endTime>2</endTime><participants>0</participants>
    <metadata><bbb-origin>Moodle</bbb-origin><bbb-context-label>X</bbb-context-label></metadata>
    <playback><format><type>video</type><url>https://h.example/video/synthetic-1/video-0.m4v</url></format></playback>
    </recording></recordings></response>"""
    r = analyse_recordings(ET.fromstring(xml))["recordings"][0]
    assert r["has_video_format"] and r["video_url_path_shape"] == "/video/<recordID>/video-0.m4v"
    assert "bbb-context-id" in r["expected_moodle_keys_missing"] and not r["has_cohort_like_key"]
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
    rep: dict = {"configured": bool(base and secret and not any(p in base + secret for p in PLACEHOLDERS))}
    code = 2
    if rep["configured"]:
        try:
            v = call(base, secret)
            rep["server_up"] = v.findtext("returncode") == "SUCCESS"
            rep["version"] = v.findtext("version")
            rep["bbb_version"] = v.findtext("bbbVersion")
            rec = analyse_recordings(call(base, secret, "getRecordings"))
            rep["recordings"] = rec
            rep["recording_api_ok"] = rec["returncode"] == "SUCCESS"
            rep["any_video_format"] = any(r["has_video_format"] for r in rec["recordings"])
            code = 0 if rep["recording_api_ok"] and rep["any_video_format"] else 1
        except (urllib.error.URLError, OSError, ET.ParseError) as e:
            rep["error"] = type(e).__name__  # class only: messages may contain the URL
            rep["server_up"] = False
    text = json.dumps(rep, indent=2)
    print(text)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text + "\n")
    return code


if __name__ == "__main__":
    sys.exit(main())
