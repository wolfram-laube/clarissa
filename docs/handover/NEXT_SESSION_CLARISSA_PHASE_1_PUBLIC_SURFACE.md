# NEXT SESSION — CLARISSA Phase 1 Public Surface (DNS + Landing + 404-Fix)

**Date:** 2026-05-15
**Project:** CLARISSA (project_id: 77260390)
**Parent Issue:** #149 — Phase 1: Custom Domain & Marketing Landing
**Architectural Basis:** ADR-042 (DNS Provider Strategy — Cloudflare via Subzone Delegation)

---

## Context

In dieser Session wurde die DNS-Strategie für CLARISSAs öffentliche Surface entschieden und dokumentiert. ADR-042 legt fest: `clarissa.blauweiss-edv.com` wird via Cloudflare-Subzone-Delegation an GitLab Pages angebunden. Hauptzone `blauweiss-edv.com` bleibt unangetastet bei IONOS (null Risiko für bestehende Mail).

Die ursprünglich breit geschnittene Phase 1 (#149) wurde in drei Sub-Task-Issues dekomponiert (#151, #152, #153), damit jede Aufgabe einen eigenen sauberen Branch + MR bekommt.

### ERLEDIGT (Session 2026-05-15)

- **ADR-042** geschrieben (`docs/architecture/adr/ADR-042-dns-provider-strategy.md`) — Status: Accepted
- **Bilinguales Proposal-Dokument** in MD/HTML/PDF unter `docs/architecture/proposals/2026-05-15-dns-cloudflare.md` (13 Seiten PDF für Mike/Ian/Doug-Review)
- **ADR-Index** retroaktiv aufgeräumt — fehlende Einträge für ADR-029, ADR-030, ADR-041 nachgetragen, plus neue ADR-042-Zeile
- **CHANGELOG** aktualisiert unter `[Unreleased] > Added`
- **5 neue Issues** angelegt:
  - #150 — ADR-042 MR-Tracker
  - #151 — DNS-Subzone-Delegation (1.1 von #149)
  - #152 — Hand-crafted Landing-Page (1.2 von #149)
  - #153 — Demo-404-Fix (1.3 von #149)
  - #154 — Phase-2-Vollmigration-Backlog (trigger-driven)
- **MR !140** offen, ready-for-review, Pipeline grün
- **Kommentar an #149** mit Issue-Struktur-Übersicht

### OFFEN AM ENDE DER SESSION

- MR !140 (ADR-042 + Proposal) noch nicht gemerged — Wolfram wollte Inhalt erst lesen
- Cloudflare-Account noch nicht angelegt — Wolfram-blocked
- Issues #151, #152, #153 alle in `workflow::ready`, keine Branches angefangen

---

## NÄCHSTE SCHRITTE

### Schritt 0 — MR !140 mergen

Sobald Wolfram das ADR-042-PDF gelesen und gut findet:

```bash
# MR !140 squash-merge + branch-delete (oder via API):
curl --request PUT \
  --header "PRIVATE-TOKEN: $TOKEN" \
  --data "merge_when_pipeline_succeeds=false&should_remove_source_branch=true&squash=true" \
  "https://gitlab.com/api/v4/projects/77260390/merge_requests/140/merge"
```

Danach #150 automatisch geschlossen (via "Closes #150" in MR-Description).

### Schritt 1 — Cloudflare-Setup (WOLFRAM, blocking)

Vier Aktionen, ca. 15 Min Gesamtaufwand:

1. **Cloudflare-Account anlegen** auf https://dash.cloudflare.com/sign-up (Free Plan, 2FA aktivieren)
2. **Site hinzufügen:** `clarissa.blauweiss-edv.com` (Subzone, nicht Apex!) → Free Plan → Cloudflare zeigt zwei Nameserver-Namen (`xyz.ns.cloudflare.com`, `abc.ns.cloudflare.com`)
3. **IONOS-Zugang besorgen** und im IONOS-DNS-Panel für `blauweiss-edv.com` zwei NS-Records eintragen:
   ```
   clarissa    NS    xyz.ns.cloudflare.com
   clarissa    NS    abc.ns.cloudflare.com
   ```
4. **Cloudflare-API-Token erstellen** unter https://dash.cloudflare.com/profile/api-tokens
   - Template: "Edit zone DNS"
   - Permissions ergänzen: `Zone:Read` zusätzlich zu `DNS:Edit`
   - Zone Resources: **Specific zone — clarissa.blauweiss-edv.com** (nicht "All zones"!)
   - TTL: 6 Monate (z.B. 2026-11-15)
   - Token kopieren, sicher aufbewahren

Sobald alle vier erledigt, weiter mit Schritt 2.

### Schritt 2 — #151 DNS-Phase-1 (CLAUDE, autonom)

Voraussetzungen erfüllt (NS-Records propagiert, API-Token vorhanden). Claude erstellt Branch `feat/151-dns-subzone-cloudflare`, dann:

```python
# 1. Verify subzone delegation is active
import subprocess
r = subprocess.run(["dig", "+short", "NS", "clarissa.blauweiss-edv.com"], capture_output=True, text=True)
assert "cloudflare.com" in r.stdout

# 2. GitLab API: create Pages custom domain
import urllib.request, json
TOKEN_GL = "<gitlab-pat>"
req = urllib.request.Request(
    "https://gitlab.com/api/v4/projects/77260390/pages/domains",
    data=urllib.parse.urlencode({
        "domain": "clarissa.blauweiss-edv.com",
        "auto_ssl_enabled": "true"
    }).encode(),
    headers={"PRIVATE-TOKEN": TOKEN_GL},
)
domain = json.loads(urllib.request.urlopen(req).read())
verification_token = domain["verification_code"]

# 3. Cloudflare API: set CNAME + TXT
TOKEN_CF = "<cloudflare-token>"
ZONE_ID = "<from-cloudflare-zone-list>"
for record in [
    {"type": "CNAME", "name": "clarissa", "content": "irena-40cc50.gitlab.io", "proxied": False, "ttl": 1},
    {"type": "TXT", "name": "_gitlab-pages-verification-code", "content": verification_token, "ttl": 1},
]:
    req = urllib.request.Request(
        f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records",
        data=json.dumps(record).encode(),
        headers={"Authorization": f"Bearer {TOKEN_CF}", "Content-Type": "application/json"},
    )
    urllib.request.urlopen(req)

# 4. Poll GitLab Pages domain until verified + cert provisioned
# 5. Set as primary domain
# 6. Update mkdocs.yml site_url
# 7. Update README references
# 8. CHANGELOG entry, MR, squash-merge
```

**Wichtig:** `proxied=false` zwingend, sonst bricht Let's-Encrypt-ACME-Challenge.

### Schritt 3 — #152 Landing-Page (parallel zu Schritt 2 möglich)

Hand-crafted HTML hero replacing default mkdocs-material landing. Design-Sprache: `docs/portal.html` (Premium-Dark, `#6c5ce7`/`#00cec9`). Sections: Hero, drei CTAs (Sim-Viewer, Voice-Demo, Docs), Status-Strip, Team, Tech-Stack-Badges, Footer. Englisch per ADR-013.

**Wolfram-Review erforderlich vor Merge** — Public-Surface-Visual.

### Schritt 4 — #153 Demo-404-Fix (parallel möglich, mini)

`/demos/` und `/demos/voice-demo.html` returnen 404 trotz existierender HTML-Files. Vermutlich mkdocs-nav-Eintrag oder include-Konfiguration. Plus: CI-Step der Demo-URLs nach Deploy verifiziert (HTTP 200), um Regressionen zu fangen.

---

## Wichtige Hinweise für nächste Session

- **GitLab-PAT:** der zuvor in der Session genutzte PAT (`glpat-09nRT7Th4HODebN_...`) sollte noch gültig sein; ansonsten in dieser Session konfigurierter `claude-helper` (ID 21525815, bis 2026-12-31)
- **Cloudflare-API-Token:** Wolfram gibt ihn in der nächsten Session
- **MR-Konvention:** Branch `feat/<issue>-<slug>`, squash-merge, source-branch-delete, conventional commits, CHANGELOG `[Unreleased]`-Eintrag
- **Anthropic Credits leer** — falls Sim-Agent-Tests nötig: GPT-4o als Fallback
- **Nordic-Shell-Runner unzuverlässig** — Yoga-Docker-Runner bevorzugen
- **Memory-Update** (in dieser Session gemacht):
  - Eintrag #6 ersetzt: ADR-042 + MR !140 + Issue-Struktur
  - Eintrag #7 neu: Cloudflare-Prerequisites-Checklist

## Architektur-Referenz

- ADR-042 (DNS Provider Strategy — Cloudflare via Subzone Delegation): `docs/architecture/adr/ADR-042-dns-provider-strategy.md`
- Bilingual Proposal: `docs/architecture/proposals/2026-05-15-dns-cloudflare.md`
- ADR-029 (Deployment Infrastructure — adjacent)
- ADR-030 (Multi-Target Deployment — adjacent)
- ADR-013 (i18n — Public-Surface ist English-only)
