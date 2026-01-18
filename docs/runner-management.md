# Runner Management

Diese Seite fasst die wichtigsten Ressourcen zur Runner-Verwaltung zusammen.

## Architektur-Entscheidungen

- [ADR-016: Runner Load Balancing](architecture/adr/ADR-016-runner-load-balancing.md) - Strategie für 12-Runner-Matrix

## Operative Dokumentation

- [BENCHMARK_HOWTO.md](ci/BENCHMARK_HOWTO.md) - Runner-Benchmarks und Performance-Tests
- [Infrastructure Overview](infrastructure.md) - Überblick aller Runner

## Quick Reference

### Runner-Matrix (12 Runner)

| Machine | Shell | Docker | K8s |
|---------|-------|--------|-----|
| Mac #1  | ✅    | ✅     | ✅  |
| Mac #2  | ✅    | ✅     | ✅  |
| Linux Yoga | ✅ | ✅     | ✅  |
| GCP VM  | ✅    | ✅     | ✅  |

### Tags

- **Generic**: `any-runner` - Load Balancing über alle Runner
- **Executor**: `shell`, `docker`, `k8s`
- **Machine**: `mac`, `mac2`, `linux`, `gcp`

Siehe [ADR-016](architecture/adr/ADR-016-runner-load-balancing.md) für Details.
