#!/usr/bin/env python3
"""
GitLab CI Merge Request Comment Bot (stdlib only)

Adds or updates a merge request note when CI fails in MR pipelines.

Required env:
  - GITLAB_TOKEN
  - CI_API_V4_URL
  - CI_PROJECT_ID
  - CI_PIPELINE_URL
  - CI_JOB_URL
  - CI_COMMIT_SHORT_SHA
  - CI_PROJECT_PATH
  - CI_MERGE_REQUEST_IID   (available in MR pipelines)
Optional:
  - CI_BOT_FINGERPRINT     (default: "orsa-mr:<job>:mr<iid>")
  - CI_BOT_JUNIT_PATH      (default: junit.xml)
  - CI_BOT_MAX_TESTS       (default: 10)
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional


def env(name: str, default: Optional[str] = None) -> str:
    v = os.getenv(name, default)
    if v is None or v == "":
        return default or ""
    return v


def api_request(method: str, url: str, token: str, data: Optional[dict] = None) -> Any:
    headers = {
        "PRIVATE-TOKEN": token,
        "Content-Type": "application/json",
        "User-Agent": "orsa-ci-mr-bot/1.0",
    }
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url=url, method=method, headers=headers, data=body)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return None
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} for {url}: {msg}") from e


def parse_junit_failures(path: str, max_tests: int) -> List[str]:
    if not os.path.exists(path):
        return []
    try:
        tree = ET.parse(path)
        root = tree.getroot()
    except Exception:
        return []

    failures: List[str] = []
    testcases = root.findall(".//testcase")
    for tc in testcases:
        if len(failures) >= max_tests:
            break
        failed = tc.find("failure") is not None or tc.find("error") is not None
        if failed:
            classname = tc.attrib.get("classname", "").strip()
            name = tc.attrib.get("name", "").strip()
            if classname and name:
                failures.append(f"{classname}::{name}")
            else:
                failures.append(name or classname or "unknown_test")
    return failures


def build_marker(fingerprint: str) -> str:
    return f"<!-- orsa-mr-bot:{fingerprint} -->"


def list_mr_notes(api: str, project_id: str, token: str, mr_iid: str) -> List[Dict[str, Any]]:
    q = urllib.parse.urlencode({"per_page": 100, "sort": "desc", "order_by": "updated_at"})
    url = f"{api}/projects/{urllib.parse.quote(project_id, safe='')}/merge_requests/{mr_iid}/notes?{q}"
    notes = api_request("GET", url, token) or []
    return notes if isinstance(notes, list) else []


def create_mr_note(api: str, project_id: str, token: str, mr_iid: str, body: str) -> Any:
    url = f"{api}/projects/{urllib.parse.quote(project_id, safe='')}/merge_requests/{mr_iid}/notes"
    return api_request("POST", url, token, {"body": body})


def update_mr_note(api: str, project_id: str, token: str, mr_iid: str, note_id: int, body: str) -> Any:
    url = f"{api}/projects/{urllib.parse.quote(project_id, safe='')}/merge_requests/{mr_iid}/notes/{note_id}"
    return api_request("PUT", url, token, {"body": body})



def update_merge_request_labels(api: str, project_id: str, token: str, mr_iid: str, add_labels: List[str]) -> None:
    if not add_labels:
        return
    # Fetch MR to get current labels
    url = f"{api}/projects/{urllib.parse.quote(project_id, safe='')}/merge_requests/{mr_iid}"
    mr = api_request("GET", url, token) or {}
    current = mr.get("labels") or []
    merged = list(dict.fromkeys([*current, *add_labels]))
    # Update labels
    url2 = f"{api}/projects/{urllib.parse.quote(project_id, safe='')}/merge_requests/{mr_iid}"
    api_request("PUT", url2, token, {"labels": ",".join(merged)})


def main() -> int:
    token = env("GITLAB_TOKEN")
    api = env("CI_API_V4_URL", "https://gitlab.com/api/v4")
    project_id = env("CI_PROJECT_ID")
    mr_iid = env("CI_MERGE_REQUEST_IID")
    snapshot_path = env(\"CI_BOT_SNAPSHOT_SUMMARY_PATH\", \"tests/golden/summary.md\")

    if not token or not project_id or not mr_iid:
        print("Missing GITLAB_TOKEN, CI_PROJECT_ID, or CI_MERGE_REQUEST_IID", file=sys.stderr)
        return 2

    job = env("CI_JOB_NAME", "tests")
    project_path = env("CI_PROJECT_PATH", "unknown/project")
    short_sha = env("CI_COMMIT_SHORT_SHA", "unknown")
    pipeline_url = env("CI_PIPELINE_URL", "")
    job_url = env("CI_JOB_URL", "")

    fingerprint = env("CI_BOT_FINGERPRINT", f"orsa-mr:{job}:mr{mr_iid}")
    marker = build_marker(fingerprint)

    max_tests = int(env("CI_BOT_MAX_TESTS", "10") or "10")
    junit_path = env("CI_BOT_JUNIT_PATH", "junit.xml")
    failures = parse_junit_failures(junit_path, max_tests=max_tests)


    confirmed = env("CI_BOT_CONFIRMED_FAILURE", "1").strip() == "1"
    flaky = env("CI_BOT_FLAKY", "0").strip() == "1"

    # Optional: apply MR labels based on classification
    try:
        if flaky and not confirmed:
            flaky_label = env("CI_BOT_MR_FLAKY_LABEL", "ci-flaky-suspected").strip()
            if flaky_label:
                update_merge_request_labels(api, project_id, token, mr_iid, [flaky_label])
        if confirmed:
            confirmed_label = env("CI_BOT_MR_CONFIRMED_LABEL", "ci-regression-confirmed").strip()
            if confirmed_label:
                update_merge_request_labels(api, project_id, token, mr_iid, [confirmed_label])
    except Exception as e:
        print(f"Warning: could not update MR labels: {e}")

    # Optional: apply MR label on flaky classification
    if flaky and not confirmed:
        flaky_label = env("CI_BOT_MR_FLAKY_LABEL", "ci-flaky-suspected").strip()
        if flaky_label:
            try:
                update_merge_request_labels(api, project_id, token, mr_iid, [flaky_label])
            except Exception as e:
                print(f"Warning: could not update MR labels: {e}")

snapshot_section = ""
if snapshot_path and os.path.exists(snapshot_path):
    try:
        snap = open(snapshot_path, "r", encoding="utf-8").read().strip()
        if snap:
            snapshot_section = "\n\n---\n\n## 🧾 Snapshot diff summary\n\n" + snap + "\n"
    except Exception as e:
        print(f"Warning: could not read snapshot summary: {e}")

    failures_md = ""
    if failures:
    snapshot_section = ""
if snapshot_path and os.path.exists(snapshot_path):
    try:
        snap = open(snapshot_path, "r", encoding="utf-8").read().strip()
        if snap:
            snapshot_section = "\n\n---\n\n## 🧾 Snapshot diff summary\n\n" + snap + "\n"
    except Exception as e:
        print(f"Warning: could not read snapshot summary: {e}")

    failures_md = "\n\n**Failing tests (sample):**\n" + "\n".join([f"- `{t}`" for t in failures])

def status_row(label: str, ok: bool | None) -> str:
    if ok is None:
        return f"| {label} | ⚪ n/a |"
    return f"| {label} | {'✅ pass' if ok else '❌ fail'} |"

snapshot_ok = not bool(snapshot_section)
contract_ok = not bool(contract_section)
gov_hit = bool(gov_section)

status_table = (
    "## 🧭 CI status overview\n\n"
    "| Check | Status |\n"
    "|---|---|\n"
    + status_row("CLI snapshots", snapshot_ok) + "\n"
    + status_row("Contract tests", contract_ok) + "\n"
    + status_row("Governance impact", None if not gov_hit else False) + "\n"
)

links = []
if pipeline_url:
    links.append(f"- 🔗 Pipeline: {pipeline_url}")
if job_url:
    links.append(f"- 🧩 Job: {job_url}")
links_section = ""
if links:
    links_section = "\n\n## 🔗 Links\n\n" + "\n".join(links) + "\n"

    body = (
        f"{marker}\n"
        f"{'🟡 Flaky CI detected' if flaky and not confirmed else '⚠️ CI failure detected'} for MR !{mr_iid}.\n\n"
        f"- Project: `{project_path}`\n"
        f"- Commit: `{short_sha}`\n"
        f"- Pipeline: {pipeline_url}\n"
        f"- Job: {job_url}\n"
        f"{failures_md}\n\n"
        f"Suggested next step: re-run the job to check flakiness.\n"
    )

    notes = list_mr_notes(api, project_id, token, mr_iid)
    for n in notes:
        if marker in (n.get("body") or ""):
            note_id = int(n["id"])
            update_mr_note(api, project_id, token, mr_iid, note_id, body)
            print(f"Updated MR note {note_id} on MR !{mr_iid}")
            return 0

    create_mr_note(api, project_id, token, mr_iid, body)
    print(f"Created MR note on MR !{mr_iid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
