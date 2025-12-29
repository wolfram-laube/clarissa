# How to Read CI Results (ORSA)

ORSA uses CI primarily as an **observability and reporting system**, not as a
binary pass/fail gate.

CI produces *signals*. Humans make *decisions*.

---

## 1. CI Stages at a Glance

The ORSA pipeline is structured into four conceptual layers:

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

ORSA explicitly separates **governance signals** from **enforcement**.

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

When reviewing an ORSA MR:

1. Read the MR report
2. Check the classification
3. Inspect governance signals
4. Review snapshot diffs if present
5. Apply human judgment

CI provides context.
Decisions remain human.
