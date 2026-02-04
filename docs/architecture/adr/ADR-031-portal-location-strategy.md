# ADR-031: Operations Portal Location Strategy

## Status
**Accepted** (2026-02-04)

## Context
Das Blauweiss Operations Portal ist ein zentrales Tool für:
- Bewerbungs-Management (Crawler, Matcher, Gmail Drafter)
- CRM (GitLab Issues-basiert)
- Billing (Timesheet, Invoice)
- Infrastruktur (Runner, GCP VM Control)

Es dient der gesamten Blauweiss LLC, nicht nur dem CLARISSA-Forschungsprojekt.

**Problem:** Wo soll das Portal gehostet werden?

### Optionen

| Option | Pro | Contra |
|--------|-----|--------|
| A) In CLARISSA belassen | Bereits deployed, Pages funktionieren | Semantisch falsch - Ops ≠ Research |
| B) Eigenes `ops/portal` Projekt | Saubere Trennung | Overhead für 3-Personen-Team |
| C) Group-Level Landing | Zentral | GitLab unterstützt keine Group Pages |

## Decision
**Option A mit Mitigation:** Portal bleibt in CLARISSA, aber:

1. **Group Description** enthält prominenten Portal-Link
2. **CLARISSA README** dokumentiert Portal als separates Concern
3. **Future Migration Path** definiert für Wachstum

### Begründung
- Team ist klein (Wolfram, Mike, Ian)
- Portal URL ist bereits etabliert
- Overhead für Separation nicht gerechtfertigt
- Migration später möglich ohne Breaking Changes

## Consequences

### Positive
- Keine Änderung an URLs nötig
- Pages-Infrastruktur bereits funktional
- Einfach für kleines Team

### Negative
- Semantische Unschärfe (Ops in Research-Repo)
- CLARISSA CI baut auch Portal (vermischte Concerns)

### Mitigations
- Klare Dokumentation der Trennung
- Portal-Dateien in eigenem `docs/` Unterordner
- Group Description als offizieller Einstiegspunkt

## Future Considerations
Bei Firmenwachstum (MAGNUS, AURORA, weitere Projekte):

```
blauweiss_llc/
├── ops/
│   └── portal/          # ← Portal hierhin migrieren
├── projects/
│   ├── clarissa/
│   ├── magnus/
│   └── aurora/
```

**Trigger für Migration:**
- Mehr als 5 aktive Teammitglieder
- Zweites Produkt/Projekt in Produktion
- Portal-Komplexität erfordert eigene CI

## Links
- Portal: https://irena-40cc50.gitlab.io/portal.html
- Group: https://gitlab.com/groups/wolfram_laube/blauweiss_llc
- Issue: #102
- Epic: #86 (i18n)
