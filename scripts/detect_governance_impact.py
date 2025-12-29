#!/usr/bin/env python3
"""Detect governance-relevant changes in an MR (heuristic).

Uses GitLab MR changes API to look for tokens like 'RATE' in diffs.
Always writes tests/governance/impact.md (skipped / no impact / impact).
Never fails the pipeline due to missing/invalid token or transient API errors.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Optional


def env(name: str, default: Optional[str] = None) -> str:
    v = os.getenv(name, default)
    if v is None or v == "":
        return default or ""
    return v


def write_report(lines: list[str]) -> None:
    out_dir = Path(__file__).resolve().parents[1] / "tests" / "governance"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "impact.md"
    out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def api_request(method: str, url: str, token: str, data: Optional[dict] = None) -> Any:
    headers = {
        "PRIVATE-TOKEN": token,
        "Content-Type": "application/json",
        "User-Agent": "clarissa-ci-governance-impact/1.0",
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

    # If not running in MR context or no token available: write a non-blocking report.
    if not project_id or not mr_iid:
        write_report(
            [
                "# Governance impact",
                "",
                "ℹ️ Skipped: not running in a merge request pipeline (missing `CI_MERGE_REQUEST_IID`).",
                "",
            ]
        )
        return 0

    if not token:
        write_report(
            [
                "# Governance impact",
                "",
                "ℹ️ Skipped: missing `GITLAB_TOKEN` in CI variables.",
                "",
                "Tip: Set a non-protected CI/CD variable `GITLAB_TOKEN` if you want API-backed detection.",
                "",
            ]
        )
        return 0

    url = project_url(api, project_id, f"/merge_requests/{mr_iid}/changes")

    try:
        data = api_request("GET", url, token) or {}
    except urllib.error.HTTPError as e:
        if e.code == 401:
            write_report(
                [
                    "# Governance impact",
                    "",
                    "ℹ️ Skipped: GitLab API returned **401 Unauthorized** for the provided token.",
                    "",
                    "Tip: Ensure `GITLAB_TOKEN` is valid and available to MR pipelines (not protected-only).",
                    "",
                ]
            )
            return 0
        write_report(
            [
                "# Governance impact",
                "",
                f"ℹ️ Skipped: GitLab API error (**HTTP {e.code}**).",
                "",
                "This is treated as non-blocking to keep CI reliable.",
                "",
            ]
        )
        return 0
    except Exception as e:  # noqa: BLE001
        write_report(
            [
                "# Governance impact",
                "",
                f"ℹ️ Skipped: GitLab API request failed ({type(e).__name__}: {e}).",
                "",
                "This is treated as non-blocking to keep CI reliable.",
                "",
            ]
        )
        return 0

    changes = data.get("changes") or []

    hits: list[str] = []
    for ch in changes:
        diff = (ch.get("diff") or "")
        if "RATE" in diff:
            hits.append(ch.get("new_path") or ch.get("old_path") or "unknown")

    if hits:
        write_report(
            [
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
        )
    else:
        write_report(
            [
                "# Governance impact",
                "",
                "✅ No governance impact detected (heuristic: no `RATE` token found in diffs).",
                "",
            ]
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
