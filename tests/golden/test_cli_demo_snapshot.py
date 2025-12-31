import os, subprocess, sys
from .snapshot import assert_snapshot

def test_cli_demo_snapshot():
    env = os.environ.copy()
    env["AUTO_APPROVE"] = "1"
    p = subprocess.run([sys.executable, "-m", "clarissa", "demo"], capture_output=True, text=True, env=env)
    assert p.returncode == 0
    out = (p.stdout or "") + "\n" + (p.stderr or "")
    assert_snapshot(out, "cli_demo.snap")
