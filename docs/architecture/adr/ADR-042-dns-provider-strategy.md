# ADR-042: DNS Provider Strategy — Cloudflare via Subzone Delegation

**Status:** Accepted
**Date:** 2026-05-15
**Deciders:** Wolfram Laube, Claude (AI Assistant)
**Related:** [Proposal Document](../proposals/2026-05-15-dns-cloudflare.md) (bilingual EN/DE long-form), ADR-013 (i18n — proposal is bilingual per convention), ADR-029 (Deployment Infrastructure Strategy), ADR-030 (Multi-Target Deployment), Issue #149 (Phase 1: Custom Domain & Marketing Landing)

---

## Context

CLARISSA is served via GitLab Pages at `irena-40cc50.gitlab.io`, a system-generated URL with an 8-character hash. The URL is unmemorable, hard to communicate verbally, and inappropriate for SPE Europe 2026 references, business cards, email signatures, or any public-facing context. Issue #149 commits to fixing this by exposing CLARISSA at `clarissa.blauweiss-edv.com`.

The domain `blauweiss-edv.com` is registered at IONOS (1&1), with DNS hosted there as well. Two constraints shape the decision:

1. **IONOS has no public DNS API for standard webhosting accounts.** Every DNS record change requires manual web-UI clicks. This blocks automation now and for every future DNS change across the organization's projects (Profile Service, Dialectic AI, AppTrack).

2. **Mail (`@blauweiss-edv.com`) is in active production use at IONOS.** Any DNS strategy that risks mail continuity is unacceptable.

A naive solution (full migration of `blauweiss-edv.com` to Cloudflare) addresses constraint 1 but creates exposure to constraint 2 — DNS scanners can miss DKIM records with unusual selector names, and mail authentication failures are subtle and slow to detect.

### Trigger for this decision

Issue #149 (CLARISSA Phase 1 public surface) requires a stable, custom DNS entry for the demo URL. The DNS strategy needs to be chosen and documented before any DNS records are touched.

## Decision

**Adopt Cloudflare as DNS provider for CLARISSA, via subzone delegation. Defer full zone migration to a future phase, conditional on independent triggers.**

Concretely:

1. **Phase 1 (immediate):** Delegate only the subzone `clarissa.blauweiss-edv.com` to Cloudflare via two NS records added at IONOS. The main `blauweiss-edv.com` zone — including all mail records (MX, SPF, DKIM, DMARC), the apex A-record, and any other existing records — remains authoritative at IONOS, untouched.

2. **Phase 2 (deferred, trigger-driven):** Migrate the full `blauweiss-edv.com` zone to Cloudflare when at least one of the following triggers fires:
   - Demand for additional subdomains under `blauweiss-edv.com` for other projects makes IONOS manual management untenable
   - Mail is being migrated away from IONOS to a modern provider (Google Workspace, Microsoft 365, Migadu, Fastmail, etc.)
   - The main website is being migrated off IONOS shared hosting
   - Cloudflare-only features (Workers, R2, advanced Page Rules) become genuinely needed

3. **Phase 3 (optional, long-term):** Transfer domain registration to Cloudflare Registrar, codify DNS records as Infrastructure-as-Code via Terraform.

The trigger condition for Phase 2 is recorded as backlog issue #154.

## Rationale

### Why Cloudflare (vs. staying at IONOS)

**API access is the only reason that genuinely matters.** Cloudflare's REST API enables Claude to manage DNS records autonomously, supports Infrastructure-as-Code via Terraform/Pulumi, and audits cleanly via Git history. IONOS offers none of this. Every other Cloudflare differentiator (free CDN, DDoS protection, Workers, R2, analytics) is a bundled bonus that we can adopt later or ignore entirely.

### Why subzone delegation (vs. full zone migration)

The subzone approach decouples the architectural choice from the operational risk:

- **Mail risk is zero.** The IONOS-authoritative zone — where all mail records live — is not modified at all. The only record added at IONOS is an NS pair pointing the `clarissa` subdomain at Cloudflare. Existing records are untouched.
- **IONOS access requirement is minimal and one-time.** Adding two NS records at IONOS is a ~5-minute web-UI action. After that, IONOS is not needed for any CLARISSA-related DNS work.
- **Phase 2 becomes easier, not harder.** When Phase 2 eventually executes, Cloudflare already has account, tooling, and operator familiarity. The Phase 2 NS switch absorbs the subzone into the main zone without service interruption.
- **Rollback is trivial.** If anything goes wrong with the Cloudflare subzone, deleting the two NS records at IONOS removes Cloudflare's authority — full rollback in one record removal at IONOS.

### Why defer Phase 2

Full zone migration adds 10–20% risk of DNS-scanner gaps (typically DKIM records with non-standard selector names), and the consequences are subtle: outgoing mail may silently land in spam at strict receivers, detectable only by user complaint. This risk is acceptable when independently justified by triggers (e.g., mail is being migrated anyway and DNS values come from the new provider, not from an IONOS scan), but is not justified by CLARISSA's needs alone.

## Consequences

### Positive

- CLARISSA gets a clean, memorable URL (`clarissa.blauweiss-edv.com`) without touching production mail.
- Claude can manage DNS for the subzone autonomously via Cloudflare API, with token-based access scoped to the single subzone (principle of least privilege).
- Phase 2 migration path is clear, with concrete triggers and a documented procedure. Decision is not lost.
- Pattern is reusable: subzone delegation could later be used for other projects (`profile.blauweiss-edv.com`, `apptrack.blauweiss-edv.com`) without further IONOS clicking, if the Phase 2 trigger has fired in the meantime.

### Negative

- Two authoritative zones temporarily exist: IONOS for the apex, Cloudflare for the `clarissa` subzone. This is a minor cosmetic complication, not a technical issue — both are visible side-by-side in the Cloudflare dashboard and behave as standard delegated zones.
- The one-time IONOS NS-record-entry step still requires IONOS-account access. Not eliminated by this decision, only minimized.
- During Phase 2 (if/when it happens), the existing subzone must be merged into the apex zone, requiring brief duplicate-records hygiene work. The DNS continuity itself is unaffected — Cloudflare handles the subzone-into-apex transition gracefully.

### Neutral / Open

- Cloudflare account and API token are now part of the operational surface. Token must be rotated periodically (TTL recommended: 6 months).
- DNS-as-Code (Terraform) is enabled but not adopted in this ADR. A future ADR may codify it.

## Alternatives Considered

### A) Stay at IONOS

**Pro:** No migration. Zero risk to existing services.
**Con:** Does not solve the actual problem. No API, no IaC path, manual clicks for every future change across multiple projects.
**Verdict:** Rejected. This is the problem we're solving.

### B) Full IONOS → Cloudflare migration immediately

**Pro:** Single decisive step. Solves API access for all subdomains. Reduces vendor count by one.
**Con:** Exposes mail to 10–20% scanner-gap risk that is independently unjustified by CLARISSA's needs. Requires more IONOS access than the subzone approach (NS switch on the entire zone vs. adding one record pair).
**Verdict:** Rejected as Phase 1. Re-considered as Phase 2 only when independent triggers justify the risk.

### C) Use nip.io / sslip.io wildcard DNS

**Pro:** No DNS setup at all. Trivial.
**Con:** Cannot set TXT records on these services, so GitLab Pages domain verification fails, so Let's Encrypt issuance fails. Additionally, GitLab Pages routes by `Host:` header — a `nip.io` hostname is not routable to the project. Two independent failure modes.
**Verdict:** Technically infeasible.

### D) Register a new domain (`.de`, `.dev`, etc.) at Cloudflare Registrar

**Pro:** Zero IONOS dependency. Cloudflare-native from day one. Fresh marketing identity option.
**Con:** ~10 €/year extra cost. Splits brand identity from the established `.com`. Does not solve the underlying problem (API access for the main domain) — `blauweiss-edv.com` still stuck at IONOS for other future needs.
**Verdict:** Viable as a parallel path or fallback, but does not replace the strategic move to Cloudflare for the main domain. Not chosen.

### E) Cloudflare with apex domain proxied (`proxied=true`)

**Pro:** Free CDN, DDoS protection, Workers integration immediate.
**Con:** Cloudflare's edge serves its own TLS certificate, breaking the Let's Encrypt ACME-HTTP challenge that GitLab Pages relies on. Adds an extra hop with marginal benefit for a low-traffic demo site.
**Verdict:** Rejected for now. DNS-only mode (`proxied=false`) is the default. Proxied mode may be revisited per record later when there is a concrete reason.

## Notes

### Phase 1 execution

Phase 1 execution is tracked in issue #151. Once Cloudflare account and subzone are set up by Wolfram and the API token is provided to Claude, the rest of the work is autonomous: CNAME + TXT records at Cloudflare via API, GitLab Pages domain registration, Let's Encrypt cert provisioning, primary-domain switch.

### Phase 2 backlog

Phase 2 is tracked as backlog issue #154 with explicit trigger conditions. The issue is not actionable until at least one trigger has fired.

### Long-form proposal

A detailed bilingual (EN/DE) proposal document with full risk analysis, alternative comparison, and step-by-step procedure is committed alongside this ADR at `docs/architecture/proposals/2026-05-15-dns-cloudflare.md` (plus rendered PDF and HTML versions for offline and browser review by team members Mike, Ian, Doug).
