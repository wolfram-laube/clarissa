#!/usr/bin/env python3
"""Generate a Markdown summary of contract test failures for MR reporting.

Reads pytest output from stdout/stderr via a file (pytest_contracts.log) and extracts failing nodeids.
Writes tests/contracts/summary.md when failures are present.
"""
from __future__ import annotations
import re
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
log_path = repo / "pytest_contracts.log"
out_path = repo / "tests" / "contracts" / "summary.md"

if not log_path.exists():
    # Nothing to summarize
    raise SystemExit(0)

text = log_path.read_text(encoding="utf-8", errors="replace")

# Extract failing test nodeids from pytest output lines like "FAILED tests/...::test_name - ..."
failed = []
for line in text.splitlines():
    m = re.match(r"FAILED\s+([^\s]+::[^\s]+)", line.strip())
    if m:
        failed.append(m.group(1))

failed = list(dict.fromkeys(failed))

if not failed:
    # No failures; remove previous summary if any
    if out_path.exists():
        out_path.unlink()
    raise SystemExit(0)

out_path.parent.mkdir(parents=True, exist_ok=True)
md = ["# Contract status", "", "❌ Contract tests failed:", ""]
for f in failed[:50]:
    md.append(f"- `{f}`")
if len(failed) > 50:
    md.append(f"- … and {len(failed)-50} more")
md.append("")
out_path.write_text("\n".join(md), encoding="utf-8")
