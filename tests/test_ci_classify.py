import os
import subprocess
import sys
from pathlib import Path

JUNIT_FAIL = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite tests="1" failures="1">
  <testcase classname="t" name="fails">
    <failure message="nope">trace</failure>
  </testcase>
</testsuite>
"""

JUNIT_PASS = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite tests="1" failures="0">
  <testcase classname="t" name="passes"/>
</testsuite>
"""

def run_classify(tmp_path: Path, junit: str, rerun_code: str | None):
    (tmp_path / "junit.xml").write_text(junit, encoding="utf-8")
    if rerun_code is not None:
        (tmp_path / "rerun_exit_code.txt").write_text(rerun_code, encoding="utf-8")
    script = Path("scripts/ci_classify.py").resolve()
    p = subprocess.run([sys.executable, str(script)], cwd=tmp_path, capture_output=True, text=True)
    assert p.returncode == 0
    envfile = (tmp_path / "ci_classify.env").read_text(encoding="utf-8")
    return envfile

def test_classify_flaky(tmp_path):
    envfile = run_classify(tmp_path, JUNIT_FAIL, "0")
    assert "CI_BOT_CONFIRMED_FAILURE=0" in envfile
    assert "CI_BOT_FLAKY=1" in envfile

def test_classify_confirmed(tmp_path):
    envfile = run_classify(tmp_path, JUNIT_FAIL, "1")
    assert "CI_BOT_CONFIRMED_FAILURE=1" in envfile
    assert "CI_BOT_FLAKY=0" in envfile

def test_classify_no_failure(tmp_path):
    envfile = run_classify(tmp_path, JUNIT_PASS, None)
    assert "CI_BOT_CONFIRMED_FAILURE=0" in envfile
    assert "CI_BOT_FLAKY=0" in envfile
