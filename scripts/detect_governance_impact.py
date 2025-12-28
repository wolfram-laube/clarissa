#!/usr/bin/env python3
"""Detect governance-relevant changes in an MR (heuristic).

Uses GitLab MR changes API to look for tokens like 'RATE' in diffs.
Writes tests/governance/impact.md if impact detected.
"""
from __future__ import annotations
import json, os, sys, urllib.parse, urllib.request
from pathlib import Path
from typing import Any, Optional

def env(name: str, default: Optional[str] = None) -> str:
    v = os.getenv(name, default)
    if v is None or v == "":
        return default or ""
    return v

def api_request(method: str, url: str, token: str, data: Optional[dict] = None) -> Any:
    headers = {
        "PRIVATE-TOKEN": token,
        "Content-Type": "application/json",
        "User-Agent": "orsa-ci-governance-impact/1.0",
    }
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url=url, method=method, headers=headers, data=body)
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
        return json.loads(raw) if raw else None

def project_url(api: str, project_id: str, path: str) -> str:
    return f"{api}/projects/{urllib.parse.quote(project_id, safe='')}{path}"

def main() -> int:
    token = env("GITLAB_TOKEN")
    api = env("CI_API_V4_URL", "https://gitlab.com/api/v4")
    project_id = env("CI_PROJECT_ID")
    mr_iid = env("CI_MERGE_REQUEST_IID")
    if not token or not project_id or not mr_iid:
        return 0

    url = project_url(api, project_id, f"/merge_requests/{mr_iid}/changes")
    data = api_request("GET", url, token) or {}
    changes = data.get("changes") or []

    hit = False
    hits = []
    for ch in changes:
        diff = (ch.get("diff") or "")
        if "RATE" in diff:
            hit = True
            hits.append(ch.get("new_path") or ch.get("old_path") or "unknown")

    out_dir = Path(__file__).resolve().parents[1] / "tests" / "governance"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "impact.md"

    if hit:
        md = [
            "# Governance impact",
            "",
            "⚠️ This MR appears to touch governed parameters (heuristic: `RATE` token found in diffs).",
            "",
            "Files with hits:",
            *[f"- `{p}`" for p in hits[:50]],
            "",
            "If this is intentional, ensure human approval steps are followed before merge.",
            "",
        ]
        out_path.write_text("\n".join(md), encoding="utf-8")
    else:
        if out_path.exists():
            out_path.unlink()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
