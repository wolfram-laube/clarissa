from __future__ import annotations

import os
import re
import difflib
from pathlib import Path


def snapshots_dir() -> Path:
    return Path(__file__).parent / "snapshots"


def normalize(s: str) -> str:
    s = s.replace("\r\n", "\n")
    s = s.lower()
    s = re.sub(r"https?://\S+", "<url>", s)
    s = re.sub(r"\b[0-9a-f]{7,40}\b", "<sha>", s)
    s = re.sub(r"/[^\s]+", "<path>", s)
    s = "\n".join(line.rstrip() for line in s.splitlines())
    s = s.strip() + "\n"
    return s


def load_expected(name: str) -> str:
    p = snapshots_dir() / name
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def write_expected(name: str, content: str) -> None:
    snapshots_dir().mkdir(parents=True, exist_ok=True)
    p = snapshots_dir() / name
    if content and not content.endswith("\n"):
        content = content + "\n"
    p.write_text(content, encoding="utf-8")


def _update_mode_enabled() -> bool:
    return os.getenv("UPDATE_SNAPSHOTS", "").strip().lower() in {"1", "true", "yes", "y"}


def assert_snapshot(actual: str, snapshot_name: str) -> None:
    act = normalize(actual)

    if _update_mode_enabled():
        write_expected(snapshot_name, act)
        return

    exp = load_expected(snapshot_name)
    if act != exp:
        diff = "\n".join(
            difflib.unified_diff(
                exp.splitlines(),
                act.splitlines(),
                fromfile=f"expected/{snapshot_name}",
                tofile=f"actual/{snapshot_name}",
                lineterm="",
            )
        )
        raise AssertionError("Snapshot mismatch:\n" + diff)
