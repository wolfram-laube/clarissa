# NEXT SESSION — CLARISSA Phase 1 Public Surface (Domain Live + Landing + 404-Fix)

**Date:** 2026-05-17
**Project:** CLARISSA (project_id: 77260390)
**Parent Issue:** #149 — Phase 1: Custom Domain & Marketing Landing
**Architectural Basis:** ADR-042 (DNS Provider Strategy — Cloudflare via Subzone Delegation)

---

## Context

In dieser Session wurde das Cloudflare/Domain-Setup vollständig abgeschlossen und Issue #151 autonom
ausgeführt. Die öffentliche URL für CLARISSA ist jetzt `clarissa.blauweiss-ai.com` (temporär,
bis spätere Migration zu `clarissa.blauweiss-edv.com` via IONOS-Subzone möglich ist).

---

## ERLEDIGT (Session 2026-05-17)

### Domain & DNS
- **Domain `blauweiss-ai.com`** registriert bei Porkbun (~$11/Jahr, läuft bis 2027-05-17)
- **Cloudflare-Account** angelegt (`Wolfram.laube@blauweiss-edv.at`)
- **`blauweiss-ai.com`** zu Cloudflare hinzugefügt (Nameserver: `ashton.ns.cloudflare.com`, `laylah.ns.cloudflare.com`)
- **Porkbun Nameserver** auf Cloudflare umgestellt
- **Cloudflare API Token** erstellt (TTL bis 2027-01-01)

### Issue #151 — DNS-Phase-1 (MR !141, squash-merged)
- GitLab Pages custom domain `clarissa.blauweiss-ai.com` erstellt & verifiziert ✅
- Cloudflare DNS-Records gesetzt:
  - `CNAME clarissa → irena-40cc50.gitlab.io` (proxied=false)
  - `TXT _gitlab-pages-verification-code.clarissa` (verification token)
- Auto SSL (Let's Encrypt) aktiviert
- `mkdocs.yml` `site_url` → `https://clarissa.blauweiss-ai.com/`
- GitLab CI-Variables hinterlegt: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ZONE_ID`
- CHANGELOG aktualisiert
- Pipeline grün, MR !141 squash-merged, Branch gelöscht

### Handover-Dokument-Korrektur
- Der alte PAT im Handover-Dokument war falsch — der korrekte PAT ist in Bitwarden hinterlegt
- Bitwarden-Eintrag: `GitLabToken::GitHubToken::BitWarden`

---

## Credentials-Übersicht (Stand 2026-05-17)

| Service | Token/Key | Status | Ablauf |
|---------|-----------|--------|--------|
| GitLab PAT (`claude-helper`) | In Bitwarden | ✅ Aktiv | 2026-06-01 |
| GitHub PAT | In Bitwarden | ✅ Aktiv | unbekannt |
| BWS Access Token | In Bitwarden | ❓ nicht verifiziert | unbekannt |
| Cloudflare API Token | `cfut_sxB58y...f29` (masked in CI) | ✅ Aktiv | 2027-01-01 |
| Cloudflare Zone ID | `915b9bb2f3de354752b6a23212299cbd` | ✅ | permanent |

### ⚠️ Wichtig: GitLab PAT läuft am 2026-06-01 ab!
Vor dem 1. Juni neuen Token erstellen und in Bitwarden + CI-Variable `GITLAB_TOKEN` aktualisieren.

---

## Cloudflare-Setup (für Referenz)

| Was | Wert |
|-----|------|
| Account Email | `Wolfram.laube@blauweiss-edv.at` |
| Domain (Porkbun) | `blauweiss-ai.com` |
| Cloudflare Zone ID | `915b9bb2f3de354752b6a23212299cbd` |
| Nameserver 1 | `ashton.ns.cloudflare.com` |
| Nameserver 2 | `laylah.ns.cloudflare.com` |
| API Token | in GitLab CI: `CLOUDFLARE_API_TOKEN` (masked) |

---

## OFFEN / NÄCHSTE SCHRITTE

### Sofort prüfen
- [ ] `https://clarissa.blauweiss-ai.com` im Browser öffnen — Let's Encrypt braucht ~15 Min
- [ ] MR !140 (ADR-042 + Proposal) noch nicht gemerged — Wolfram liest erst

### Issue #152 — Landing Page (CLAUDE, autonom nach Freigabe)
Hand-crafted HTML hero replacing default mkdocs-material landing.
Design-Sprache: `docs/portal.html` (Premium-Dark, `#6c5ce7`/`#00cec9`).
**Wolfram-Review erforderlich vor Merge.**

### Issue #153 — Demo-404-Fix (CLAUDE, autonom)
`/demos/` und `/demos/voice-demo.html` returnen 404 trotz existierender HTML-Files.
Vermutlich mkdocs-nav-Eintrag oder include-Konfiguration.
CI-Step zur URL-Verifikation nach Deploy hinzufügen.

### Spätere Migration zu `clarissa.blauweiss-edv.com` (wenn Mike Zeit hat)
1. Mike trägt 2 NS-Records bei IONOS ein (ashton + laylah)
2. `clarissa.blauweiss-edv.com` zu Cloudflare hinzufügen (gleicher Account)
3. GitLab Pages Custom Domain tauschen
4. `mkdocs.yml` `site_url` updaten
5. `blauweiss-ai.com` auslaufen lassen

---

## Wichtige Hinweise

- **GitLab PAT läuft 2026-06-01 ab** — rechtzeitig rotieren!
- **Porkbun Auto-Renew** ist AN — falls nicht gewünscht, im Porkbun-Dashboard deaktivieren
- **Anthropic Credits leer** — GPT-4o/GPT-4o-mini als Fallback
- **Nordic-Shell-Runner unzuverlässig** — Yoga-Docker-Runner bevorzugen
- **proxied=false** zwingend für GitLab Pages CNAME (ACME-Challenge)

## Architektur-Referenz

- ADR-042: `docs/architecture/adr/ADR-042-dns-provider-strategy.md`
- Proposal: `docs/architecture/proposals/2026-05-15-dns-cloudflare.md`
