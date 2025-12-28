#!/usr/bin/env python3
"""Update CLI snapshots for tests/golden snapshot tests."""
from __future__ import annotations
import os, subprocess, sys
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
from tests.golden.snapshot import normalize, write_expected

def run(args, env=None) -> str:
    p = subprocess.run(args, cwd=repo, capture_output=True, text=True, env=env)
    if p.returncode != 0:
        raise SystemExit(f"Command failed: {args}\n{p.stdout}\n{p.stderr}")
    return (p.stdout or "") + "\n" + (p.stderr or "")

out = run([sys.executable, "-m", "orsa", "--help"])
write_expected("cli_help.snap", normalize(out))

env = os.environ.copy()
env["ORSA_AUTO_APPROVE"] = "1"
out = run([sys.executable, "-m", "orsa", "demo"], env=env)
write_expected("cli_demo.snap", normalize(out))

print("Updated snapshots.")
