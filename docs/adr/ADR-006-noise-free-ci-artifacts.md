# ADR-006: Noise-free CI artifact directories

## Status
Accepted

## Context
GitLab CI emits warnings when `artifacts.paths` entries do not exist at job end, e.g.
- "WARNING: ... no matching files"

These warnings add noise and make true failures harder to spot, especially in MR pipelines
where jobs are best-effort (diagrams, reports, bots).

## Decision
For every job that uploads artifacts, the job script MUST create the artifact directories
up front using `mkdir -p ...`, even if the job might not generate files in them.

Additionally, jobs that create optional summary files (e.g. snapshot diff summaries) MUST
write a default placeholder file early, then overwrite it if real content is produced.

## Consequences
### Positive
- CI logs are quieter; real failures stand out.
- Artifact collection is predictable and consistent.
- Optional jobs remain best-effort without spurious warnings.

### Negative
- Some artifact archives may contain empty directories or placeholder files.
- Slightly more shell boilerplate in job scripts.

## Implementation notes
- Prefer runtime directory creation in CI over committing empty directories to the repo.
- Keep build outputs as artifacts; do not commit generated files unless explicitly intended.
