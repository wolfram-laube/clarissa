# How to Read CI Results (CLARISSA)

CLARISSA uses CI primarily as an **observability and reporting system**, not as a
binary pass/fail gate.

CI produces *signals*. Humans make *decisions*.

---

## 1. CI Stages at a Glance

The CLARISSA pipeline is structured into four conceptual layers:

### 1. Test & Signal Collection
- Unit and integration tests
- Golden (snapshot) CLI tests
- Contract tests for simulator adapters
- Governance-impact detection
- Architecture diagram rendering (best-effort)

### 2. Signal Refinement
- Targeted reruns of previously failing tests
- Purpose: distinguish deterministic failures from flaky behavior

### 3. Signal Classification
- A dedicated classifier evaluates all collected signals
- Produces a machine-readable verdict (`ci_classify.env`)
- Captures flakiness, recovery, and primary failure causes

### 4. Signal Publishing
- Aggregated MR report
- Optional MR comments
- Optional issue creation
- All bots are best-effort and must never block CI

---

## 2. What a Green Pipeline Means

A green pipeline means:
- Required technical checks passed
- Optional jobs either succeeded or failed non-fatally
- CI infrastructure itself is healthy

It does **not** automatically mean:
- no governance-relevant change occurred
- no review attention is needed

Always inspect the MR report.

---

## 3. What a Red Pipeline Means

A red pipeline usually indicates:
- a deterministic test failure
- a broken contract
- a regression that could not be classified as flaky

In such cases:
- inspect the failing job
- check whether a rerun occurred
- consult the classifier output

---

## 4. Governance Signals

CLARISSA explicitly separates **governance signals** from **enforcement**.

- Governance detection is heuristic and informational
- Signals are surfaced in the MR report
- CI does not block merges automatically

Reviewers are expected to:
- read governance notes
- apply human judgment
- trigger approvals if required

---

## 5. Snapshot (Golden) Tests

Golden tests protect:
- CLI output
- user-facing behavior
- documentation-level contracts

On mismatch:
- diffs are generated
- a summary is attached to the MR
- CI uploads diffs and normalized outputs as artifacts

Snapshot changes are review aids, not automatic vetoes.

---

## 6. Diagrams and Reports

Some jobs (e.g. architecture diagrams) are best-effort:
- failures do not block CI
- source diagrams remain authoritative
- rendered outputs are provided when possible

---

## 7. Review Checklist

When reviewing an CLARISSA MR:

1. Read the MR report
2. Check the classification
3. Inspect governance signals
4. Review snapshot diffs if present
5. Apply human judgment

CI provides context.
Decisions remain human.

---

## 8. Manual Job Triggers

Some jobs can be triggered manually without a code change.

### How to Trigger

1. Go to **CI/CD → Pipelines**
2. Click **Run Pipeline**
3. Select branch (usually `main`)
4. Click **Run Pipeline**
5. In the pipeline view, click the ▶️ play button on the manual job

### Available Manual Jobs

| Job | Stage | Use Case |
|-----|-------|----------|
| `rebuild_docs` | deploy | Rebuild documentation without code change |
| `rebuild_opm_image` | build | Force rebuild Docker image (e.g., after base image update) |
| `rerun_all_tests` | test | Run full test suite for debugging |
| `llm_sync_package` | deploy | Generate LLM sync package on demand |
| `build_paper` | build | Build LaTeX paper to PDF |

### When to Use

**rebuild_docs**
- After updating MkDocs theme
- To verify documentation changes
- Troubleshooting Pages deployment

**rebuild_opm_image**  
- After OPM base image update
- Security patches
- When `--no-cache` build is needed

**build_paper**
- Rebuild IJACSA paper from LaTeX
- Useful after text edits
- Artifacts contain the PDF

**rerun_all_tests**
- Debugging flaky tests
- Verifying fix without new commit
- Checking environment issues

### API Trigger

You can also trigger via API:

```bash
curl --request POST \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://gitlab.com/api/v4/projects/77260390/pipeline" \
  --form "ref=main"
```

Then use the pipeline ID to trigger a specific job:

```bash
curl --request POST \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://gitlab.com/api/v4/projects/77260390/jobs/$JOB_ID/play"
```

---

## 9. Benchmark Reports & LLM Email Notifications

CLARISSA supports automated benchmark reporting with AI-generated email summaries.

### Quick Start

```bash
# Trigger benchmarks with English email notification
curl --request POST \
  --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  --header "Content-Type: application/json" \
  "https://gitlab.com/api/v4/projects/77260390/pipeline" \
  --data '{"ref":"main","variables":[
    {"key":"BENCHMARK","value":"true"},
    {"key":"SEND_BENCHMARK_EMAIL","value":"true"},
    {"key":"EMAIL_LANGUAGE","value":"en"}
  ]}'
```

### Features

- **12-Runner Matrix**: Shell, Docker, K8s across 4 machines
- **Automated Charts**: 4 PNG visualizations generated per run
- **LLM-Powered Emails**: OpenAI or Anthropic analyzes results
- **Multilingual**: German, English, Spanish, French

See [BENCHMARK_HOWTO.md](BENCHMARK_HOWTO.md) for full documentation.
