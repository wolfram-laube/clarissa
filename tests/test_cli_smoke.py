import subprocess, sys, os, pathlib

def test_cli_help():
    # just verify module can be invoked
    p = subprocess.run([sys.executable, "-m", "clarissa", "--help"], capture_output=True, text=True)
    assert p.returncode == 0
    assert "clarissa" in p.stdout.lower() or "clarissa" in p.stderr.lower()
