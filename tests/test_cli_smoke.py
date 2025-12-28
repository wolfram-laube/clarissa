import subprocess, sys, os, pathlib

def test_cli_help():
    # just verify module can be invoked
    p = subprocess.run([sys.executable, "-m", "orsa", "--help"], capture_output=True, text=True)
    assert p.returncode == 0
    assert "orsa" in p.stdout.lower() or "orsa" in p.stderr.lower()
