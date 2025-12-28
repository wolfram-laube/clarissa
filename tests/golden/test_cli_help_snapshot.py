import subprocess, sys
from .snapshot import assert_snapshot

def test_cli_help_snapshot():
    p = subprocess.run([sys.executable, "-m", "orsa", "--help"], capture_output=True, text=True)
    assert p.returncode == 0
    out = (p.stdout or "") + "\n" + (p.stderr or "")
    assert_snapshot(out, "cli_help.snap")
