# Evidence for decision 0005 (App-C item 4, task T17)

| File | What it is |
|---|---|
| `verify_bbb.py` | Read-only check of a BigBlueButton server. Reads `BBB_URL` and `BBB_SECRET` from the environment, never prints them, writes a redacted report. `--selftest` runs it on a synthetic response (proves the script, not the lab). |
| `run-2026-11-16-unconfigured.json` | Output of the one real run so far: the lab values were not configured (only the `.env.example` placeholders), so nothing was contacted. Exit code 2 = PENDING. |

Run it on a machine that can reach the lab BigBlueButton, with the real values in the
environment (not in a file in this repository):

```
python -I docs/decisions/evidence/0005-app-c-4-bbb/verify_bbb.py --out report.json
```

Do not commit `report.json` unless you have read it: it holds no values by design, but check.
