import os
import subprocess
import sys

def test_demo_runs_non_interactive_with_auto_approve():
    env = os.environ.copy()
    env["AUTO_APPROVE"] = "1"
    p = subprocess.run([sys.executable, "-m", "clarissa", "demo"], capture_output=True, text=True, env=env)
    assert p.returncode == 0
    out = (p.stdout + "\n" + p.stderr).lower()
    assert "auto-approve" in out
    assert "outcome" in out
