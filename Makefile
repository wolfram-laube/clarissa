# CLARISSA Makefile
# Usage: make <target>

PY ?= python
PIP ?= pip

.PHONY: help install dev test demo clean

help:
	@echo "Targets:"
	@echo "  install   Install CLARISSA in editable mode"
	@echo "  dev       Install CLARISSA + dev dependencies (pytest, ruff)"
	@echo "  test      Run tests"
	@echo "  demo      Run minimal governed demo (interactive approval)"
	@echo "  clean     Remove caches"

install:
	$(PY) -m $(PIP) install -e .

dev:
	$(PY) -m $(PIP) install -e ".[dev]"

test:
	$(PY) -m pytest -q

demo:
	$(PY) -m clarissa demo

clean:
	@rm -rf .pytest_cache .ruff_cache __pycache__ */__pycache__ */*/__pycache__ */*/*/__pycache__

.PHONY: ci-bot ci-mr-bot ci-recovery-bot

ci-bot:
	$(PY) scripts/gitlab_issue_bot.py

ci-mr-bot:
	$(PY) scripts/gitlab_mr_bot.py

ci-recovery-bot:
	$(PY) scripts/gitlab_recovery_bot.py

.PHONY: classify
classify:
	$(PY) scripts/ci_classify.py

.PHONY: ci-flaky-ledger
ci-flaky-ledger:
	$(PY) scripts/gitlab_flaky_ledger_bot.py

.PHONY: demo-ci

demo-ci:
	AUTO_APPROVE=1 $(PY) -m clarissa demo

.PHONY: update-golden

update-golden:
	@echo 'usage:' > tests/golden/cli_help.txt
	@printf '[GOV]\n[SIM]\n[CLARISSA/LLM]\n' > tests/golden/cli_demo.txt

.PHONY: update-snapshots

update-snapshots:
	$(PY) scripts/update_snapshots.py

.PHONY: mr-report mr-report-html

mr-report:
	$(PY) scripts/generate_mr_report.py

mr-report-html: mr-report
	$(PY) scripts/render_report_html.py
