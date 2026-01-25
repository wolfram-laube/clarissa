# CLARISSA Makefile
# Usage: make <target>

PY ?= python
PIP ?= pip

help:
	@echo "CLARISSA Development Commands"
	@echo ""
	@echo "Quick Start (Local Docker):"
	@echo "  make dev          Start everything (docker-compose + pull model)"
	@echo "  make dev-down     Stop all services"
	@echo "  make dev-logs     View logs"
	@echo ""
	@echo "Development:"
	@echo "  make install      Install CLARISSA in editable mode"
	@echo "  make test         Run tests"
	@echo "  make lint         Run linter"
	@echo "  make format       Format code"
	@echo ""
	@echo "Simulation:"
	@echo "  make simulate     Run example simulation"
	@echo "  make opm-shell    Open OPM Flow shell"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean        Remove caches"
	@echo "  make dev-clean    Remove Docker volumes
"
	@echo "Terraform:"
	@echo "  make tf-plan      Plan changes (preview)"
	@echo "  make tf-apply     Apply changes (deploy!)"
	@echo "  make deploy-gcp   Deploy to GCP"
	@echo "  make deploy-local-k8s  Deploy to local K8s"

.PHONY: help install dev-install test demo clean dev dev-up dev-down dev-logs dev-build dev-clean ollama-pull lint format simulate opm-shell

install:
	$(PY) -m $(PIP) install -e .

dev-install:
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

# ============================================================
# CLARISSA Local Development Commands
# ============================================================

.PHONY: dev dev-up dev-down dev-logs dev-build dev-clean ollama-pull

# ------------------------------------------------------------
# Quick Start
# ------------------------------------------------------------

## Start local development environment
dev: dev-up ollama-pull
	@echo ""
	@echo "✅ CLARISSA is running!"
	@echo ""
	@echo "   API:       http://localhost:8000"
	@echo "   Docs:      http://localhost:8000/docs"
	@echo "   Firestore: http://localhost:8080"
	@echo "   Ollama:    http://localhost:11434"
	@echo "   Qdrant:    http://localhost:6333"
	@echo ""
	@echo "   Logs: make dev-logs"
	@echo "   Stop: make dev-down"
	@echo ""

## Start all services
dev-up:
	docker-compose up -d

## Stop all services
dev-down:
	docker-compose down

## View logs (follow mode)
dev-logs:
	docker-compose logs -f

## View API logs only
dev-logs-api:
	docker-compose logs -f api

## Rebuild containers
dev-build:
	docker-compose build --no-cache

## Clean up volumes and containers
dev-clean:
	docker-compose down -v --remove-orphans
	docker volume rm clarissa_ollama_data clarissa_qdrant_data clarissa_opm_output 2>/dev/null || true

## Pull Ollama model (first time setup)
ollama-pull:
	@echo "Pulling Ollama model (this may take a few minutes)..."
	@docker exec clarissa-ollama ollama pull llama3.2:3b 2>/dev/null || echo "Ollama not ready yet, run again after 'make dev-up'"

# ------------------------------------------------------------
# Development Helpers
# ------------------------------------------------------------

## Run tests
	pytest tests/ -v

## Run linter
lint:
	ruff check src/ tests/

## Format code
format:
	ruff format src/ tests/

## Type check
typecheck:
	mypy src/

## Run API locally (without Docker)
run-api:
	uvicorn clarissa.api.main:app --reload --host 0.0.0.0 --port 8000

# ------------------------------------------------------------
# Simulation
# ------------------------------------------------------------

## Run OPM Flow simulation (example)
simulate:
	@echo "Running example simulation..."
	docker exec clarissa-opm-flow flow /simulation/data/SPE1.DATA --output-dir=/simulation/output/

## Open OPM Flow shell
opm-shell:
	docker exec -it clarissa-opm-flow bash

# ============================================================
# CLARISSA Terraform Commands
# ============================================================

.PHONY: tf-init tf-plan tf-apply tf-destroy tf-fmt tf-validate

TF_ENV ?= gcp
TF_DIR = infrastructure/terraform/environments/$(TF_ENV)

# ------------------------------------------------------------
# Terraform Workflow
# ------------------------------------------------------------

## Initialize Terraform (run first!)
tf-init:
	@echo "Initializing Terraform for environment: $(TF_ENV)"
	cd $(TF_DIR) && terraform init

## Plan changes (preview)
tf-plan:
	@echo "Planning Terraform for environment: $(TF_ENV)"
	cd $(TF_DIR) && terraform plan

## Apply changes (creates real resources!)
tf-apply:
	@echo "Applying Terraform for environment: $(TF_ENV)"
	cd $(TF_DIR) && terraform apply

## Destroy all resources
tf-destroy:
	@echo "⚠️  Destroying Terraform resources for environment: $(TF_ENV)"
	cd $(TF_DIR) && terraform destroy

## Format Terraform files
tf-fmt:
	terraform fmt -recursive infrastructure/terraform/

## Validate Terraform configuration
tf-validate:
	cd $(TF_DIR) && terraform validate

## Show Terraform outputs
tf-output:
	cd $(TF_DIR) && terraform output

# ------------------------------------------------------------
# Environment-specific shortcuts
# ------------------------------------------------------------

## Deploy to GCP
deploy-gcp:
	$(MAKE) tf-init TF_ENV=gcp
	$(MAKE) tf-apply TF_ENV=gcp

## Deploy to local K8s
deploy-local-k8s:
	$(MAKE) tf-init TF_ENV=local-k8s
	$(MAKE) tf-apply TF_ENV=local-k8s

## Destroy GCP deployment
destroy-gcp:
	$(MAKE) tf-destroy TF_ENV=gcp

## Destroy local K8s deployment
destroy-local-k8s:
	$(MAKE) tf-destroy TF_ENV=local-k8s
