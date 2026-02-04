# 📊 CRM System

## Übersicht

Das CRM basiert auf GitLab Issues mit einem 8-Spalten Kanban Board.

### Board
**[→ CRM Board öffnen](https://gitlab.com/wolfram_laube/blauweiss_llc/ops/crm/-/boards/10081703)**

### Spalten

| Spalte | Beschreibung |
|--------|--------------|
| Open | Neue Leads |
| Contacted | Erstkontakt erfolgt |
| Screening | In Prüfung |
| Interview | Interview-Phase |
| Negotiation | Vertragsverhandlung |
| Won | Erfolgreich abgeschlossen |
| Lost | Nicht erfolgreich |
| On Hold | Pausiert |

### Labels

- `hot-lead` - Priorisierte Leads
- `rate::105+` - Premium-Rate
- `branche::*` - Industrie-Sektor
- `region::dach` / `region::us` - Region

### Integrity Check

Der CRM Integrity Check prüft:
- Fehlende Labels
- Verwaiste Issues
- Doppelte Einträge

[→ Integrity Check ausführen](../portal.html)
