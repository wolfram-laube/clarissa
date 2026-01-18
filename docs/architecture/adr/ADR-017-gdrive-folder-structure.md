# ADR-017: GDrive Folder Structure for BLAUWEISS-EDV-LLC

**Status:** Accepted  
**Date:** 2026-01-18  
**Authors:** Wolfram Laube, Claude  
**Tags:** infrastructure, gdrive, organization

## Context

The shared Google Drive folder `BLAUWEISS-EDV-LLC` (ID: `1qh0skTeyRNs4g9KwAhpd3J8Yj_XENIFs`) serves multiple purposes:

1. CLARISSA project artifacts (notebooks, benchmarks, credentials)
2. Business operations (invoices, offers, contracts)
3. Job acquisition pipeline (future)
4. Team collaboration (CVs, profiles)

The current structure grew organically and is disorganized:
- Files and folders at root level without clear hierarchy
- CLARISSA-specific folders mixed with business folders
- No clear separation between automation targets and human-edited documents

## Decision

Implement a hierarchical folder structure that:
- Separates concerns (CLARISSA, business, acquisition)
- Supports automation (well-defined target folders for CI jobs)
- Scales for team growth (Mike, Ian, future collaborators)
- Follows German naming conventions for business folders

### Target Structure

```
BLAUWEISS-EDV-LLC/
│
├── Akquise/                          # Job acquisition pipeline
│   ├── Profile/                      # Team member profiles (JSON)
│   ├── Jobs/
│   │   ├── _neu/                     # Fresh scans, unprocessed
│   │   ├── matched/                  # Matched to team combinations
│   │   └── abgelehnt/                # Rejected / no interest
│   └── Bewerbungen/
│       ├── entwurf/                  # Draft applications
│       ├── gesendet/                 # Sent, awaiting response
│       ├── interview/                # In discussion
│       ├── verhandlung/              # Rate negotiation
│       └── abgeschlossen/            # Won or lost
│
├── CLARISSA/                         # Project artifacts
│   ├── config/                       # credentials.json, settings
│   ├── notebooks/                    # Colab notebooks
│   └── benchmarks/                   # CI benchmark reports
│
├── Buchhaltung/                      # Accounting
│   ├── Rechnungen/                   # Invoices (by year)
│   ├── Angebote/                     # Quotes/Offers
│   └── Belege/                       # Receipts
│
├── Kunden/                           # Client folders
│   └── [Kundenname]/                 # Per-client subfolders
│
├── Personal/                         # HR / Team
│   └── CVs/                          # Resumes, skill matrices
│
├── Vorlagen/                         # Templates
│   ├── Rechnung_Template.docx
│   ├── Angebot_Template.docx
│   └── Bewerbung_Template.md
│
└── Archiv/                           # Archived/legacy content
```

### Key Folder IDs (after migration)

| Purpose | Folder | ID |
|---------|--------|-----|
| Root | BLAUWEISS-EDV-LLC | `1qh0skTeyRNs4g9KwAhpd3J8Yj_XENIFs` |
| CLARISSA Config | CLARISSA/config | (generated) |
| CLARISSA Notebooks | CLARISSA/notebooks | (generated) |
| CLARISSA Benchmarks | CLARISSA/benchmarks | (generated) |
| New Jobs | Akquise/Jobs/_neu | (generated) |
| Draft Applications | Akquise/Bewerbungen/entwurf | (generated) |

## Consequences

### Positive
- Clear separation of concerns
- Automation-friendly (CI knows exactly where to write)
- Scalable for team and business growth
- Colab users find credentials at predictable path

### Negative
- One-time migration effort required
- CI scripts need updating with new folder IDs
- Colab notebook setup cell needs path updates

### Migration Plan

1. Run `scripts/gdrive_reorganize.py` via CI job `gdrive:reorganize`
2. Update `config/clarissa_credentials.json` with new folder IDs
3. Update sync scripts: `sync_credentials_gdrive.py`, `sync_notebooks_gdrive.py`
4. Update notebook credential loading paths
5. Verify all CI jobs work with new structure

## Related

- ADR-016: Runner Load Balancing (CI infrastructure)
- ADR-015: LLM CI Notifications
- Future: Akquise-System Design Doc
