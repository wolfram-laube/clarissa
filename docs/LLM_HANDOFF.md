# CLARISSA LLM Handoff Guide

Anleitung zum Teilen des Projektkontexts mit einem anderen LLM (z.B. neuer Claude-Chat).

## Voraussetzung

Setze dein GitLab PAT als Environment-Variable (einmalig in `~/.zshrc` oder `~/.bashrc`):

```bash
export CLARISSA_PAT="glpat-xxxxxxxxxxxxxxxxxxxx"
```

## Quick Handoff (One-Liner)

```bash
curl -s --header "PRIVATE-TOKEN: $CLARISSA_PAT" \
  "https://gitlab.com/api/v4/projects/77260390/jobs/artifacts/main/raw/clarissa_sync_medium.md?job=llm_sync_package" | \
  { echo "Ich arbeite an CLARISSA - einem NLP-System für Reservoir-Simulation. Hier ist das Sync-Paket mit Projektstand, CI/CD, ADRs. Bestätige kurz dass du den Kontext verstehst, dann stelle ich meine Frage.

---
"; cat; } | pbcopy && echo "✓ In Zwischenablage! Neuen Chat öffnen → ⌘+V"
```

## Was ist im Sync-Paket?

| Inhalt | Beschreibung |
|--------|--------------|
| Repository-Struktur | Alle Dateien und Verzeichnisse |
| Letzte Commits | Die letzten 7 Commits mit Messages |
| `.gitlab-ci.yml` | Komplette CI/CD-Pipeline |
| `README.md` | Projektübersicht |
| `CHANGELOG.md` | Versionshistorie |
| `mkdocs.yml` | Docs-Konfiguration |
| `Makefile` | Build-Befehle |
| `docs/adr/*` | Alle 10 Architecture Decision Records |
| `docs/architecture/*` | Architektur-Dokumentation |

**Größe:** ~51 KB (~15k tokens, 7% vom Claude Context Window)

## Verfügbare Paket-Größen

```bash
# Lite (~26 KB) - nur Core-Konfigs
.../clarissa_sync_lite.md?job=llm_sync_package

# Medium (~51 KB) - + ADRs + Arch-Docs (empfohlen)
.../clarissa_sync_medium.md?job=llm_sync_package

# Diff - Änderungen seit letztem Commit
.../clarissa_sync_diff.md?job=llm_sync_package
```

## Für anderen Branch

```bash
# Branch-Name URL-encoden: feature/xyz → feature%2Fxyz
curl -s --header "PRIVATE-TOKEN: $CLARISSA_PAT" \
  "https://gitlab.com/api/v4/projects/77260390/jobs/artifacts/feature%2Fmy-branch/raw/clarissa_sync_medium.md?job=llm_sync_package" \
  | pbcopy
```

## Lokal generieren (ohne CI)

```bash
cd /path/to/clarissa
python3 scripts/llm_sync_generator.py --medium -o sync.md
cat sync.md | pbcopy
```

## Erwartete Antwort

Das andere LLM sollte etwa so antworten:

> Ich habe das CLARISSA Sync-Paket gelesen:
> - **Struktur:** Microservices mit NLP-Pipeline, Data Mesh, Simulator-Adapter
> - **ADRs:** Physics-centric (001), Dual-simulator (004), NLP Pipeline (009)
> - **CI/CD:** GitLab mit test → classify → automation → deploy
>
> Ich kann jetzt Code/Docs im passenden Stil erstellen. Was ist deine Frage?

## Typische Follow-up Fragen

- "Schreib einen neuen ADR für [Entscheidung]"
- "Erstelle einen CI-Job der [X macht]"
- "Review diesen Code auf ADR-Konformität"
- "Erweitere den CHANGELOG für Version 0.4.0"
