# ADR-019: Billing Folder Structure for Contractors

**Status:** Accepted  
**Date:** 2026-01-21  
**Authors:** Wolfram Laube, Claude  
**Tags:** infrastructure, billing, gdrive, contractors  
**Supersedes:** Partially extends ADR-017 (Buchhaltung section)

## Context

BLAUWEISS EDV LLC operates as a consulting firm with multiple contractors (Wolfram, Ian, potentially more). Each contractor:

1. Works for different clients at different rates
2. Submits individual timesheets and honorar notes to the LLC
3. May work for multiple clients simultaneously

The LLC then:
1. Consolidates contractor timesheets into a team summary
2. Issues a single invoice to the client (hiding individual rates)
3. Manages internal contractor payments

### Requirements

| Requirement | Reason |
|-------------|--------|
| **Rate Privacy** | Clients should not see individual contractor rates |
| **Consolidated View** | Client receives one team timesheet, not individual files |
| **Audit Trail** | Internal records must track per-contractor hours |
| **Multi-Client Support** | Contractors may work for multiple clients per month |
| **Scalability** | Structure must support adding new contractors |

## Decision

Implement a two-tier folder structure within `Buchhaltung/`:

```
Buchhaltung/
│
├── clients/                              # ══════ EXTERNAL (to customers) ══════
│   └── {client}/
│       └── {year}/
│           └── {month}/
│               ├── invoice_AR_{nr}.pdf           # Invoice to client
│               └── timesheet_consolidated.pdf    # Team hours (no rates)
│
└── contractors/                          # ══════ INTERNAL (LLC records) ══════
    └── {person}/
        └── {year}/
            └── {month}/
                └── {client}/
                    ├── timesheet.pdf             # Individual hours
                    └── honorar.pdf               # Contractor's invoice to LLC
```

### Example: January 2026

```
Buchhaltung/
├── clients/
│   └── nemensis/
│       └── 2026/
│           └── 01/
│               ├── invoice_AR_001.pdf            # €15,000 invoice
│               └── timesheet_consolidated.pdf    # 120h total
│
└── contractors/
    ├── wolfram/
    │   └── 2026/
    │       └── 01/
    │           └── nemensis/
    │               ├── timesheet.pdf             # 80h
    │               └── honorar.pdf               # €X (internal)
    │
    └── ian/
        └── 2026/
            └── 01/
                ├── nemensis/
                │   ├── timesheet.pdf             # 40h
                │   └── honorar.pdf               # €Y (internal)
                │
                └── other_client/                 # Ian also works here
                    ├── timesheet.pdf
                    └── honorar.pdf
```

### Document Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        BLAUWEISS EDV LLC                            │
│                                                                     │
│  Wolfram ──► timesheet + honorar ──┐                               │
│                                    │                                │
│  Ian ──────► timesheet + honorar ──┼──► consolidate_timesheets.py  │
│                                    │           │                    │
│  (future) ─► timesheet + honorar ──┘           ▼                   │
│                                      timesheet_consolidated.pdf     │
│                                                +                    │
│                                      invoice_AR_xxx.pdf             │
│                                                │                    │
└────────────────────────────────────────────────┼────────────────────┘
                                                 ▼
                                              CLIENT
```

### Filename Conventions

**Input files (from contractors):**
```
{person}_{client}_{year}-{month}_timesheet.pdf
{person}_{client}_{year}-{month}_honorar.pdf

Examples:
  wolfram_nemensis_2026-01_timesheet.pdf
  ian_nemensis_2026-01_honorar.pdf
```

**Output files (to clients):**
```
{client}_{year}-{month}_invoice_AR_{nr}.pdf
{client}_{year}-{month}_timesheet.pdf

Examples:
  nemensis_2026-01_invoice_AR_001.pdf
  nemensis_2026-01_timesheet.pdf
```

### Automation

| Script | Purpose | Trigger |
|--------|---------|---------|
| `upload_to_drive.py` | Route files to correct folders | CI: `upload_invoice` |
| `consolidate_timesheets.py` | Merge contractor → team | CI: `build_invoice` |
| `billing_trigger.html` | Manual pipeline trigger | Pages button |

## Consequences

### Positive

- **Privacy:** Clients never see individual rates or contractor splits
- **Clarity:** Clear separation of internal vs. external documents
- **Scalability:** Adding a new contractor = new folder, no structural changes
- **Auditability:** Complete paper trail for LLC accounting
- **Automation-friendly:** Predictable paths for CI/CD

### Negative

- **Migration:** Existing files need reorganization
- **Consolidation logic:** New script required to merge timesheets
- **Naming discipline:** Team must follow filename conventions

### Migration Plan

1. Create new folder structure in GDrive
2. Update `upload_to_drive.py` with routing logic
3. Create `consolidate_timesheets.py`
4. Move existing files to new structure
5. Update CI pipeline
6. Document conventions in team wiki

## Related

- ADR-017: GDrive Folder Structure (general structure)
- Issue #60: Restructure GDrive folder hierarchy
- `billing/scripts/upload_to_drive.py`
- `billing/scripts/consolidate_timesheets.py` (new)
