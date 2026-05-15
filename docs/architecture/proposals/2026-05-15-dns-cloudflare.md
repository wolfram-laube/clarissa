# DNS Strategy Proposal — Cloudflare Migration for CLARISSA & blauweiss-edv.com

**Proposal · Vorschlag**
**Author:** Wolfram Laube (blauweiss EDV LLC) with Claude (Anthropic)
**Date:** 2026-05-15
**Status:** Draft for review — Mike, Ian, Douglas
**Related:** GitLab Issue [CLARISSA#149](https://gitlab.com/wolfram_laube/blauweiss_llc/projects/clarissa/-/issues/149) — Custom Domain & Marketing Landing

---

## 1. Executive Summary · Zusammenfassung

### English

CLARISSA currently has no presentable public face. The GitLab Pages URL `irena-40cc50.gitlab.io` is not memorable and not suited for marketing or customer-facing use. We propose to expose CLARISSA at `clarissa.blauweiss-edv.com`, backed by Cloudflare DNS for API-driven automation.

The migration is structured in **three phases**, each independently valuable and reversible:

1. **Phase 1 (now):** Delegate only the `clarissa.*` subzone to Cloudflare. The main `blauweiss-edv.com` zone stays at IONOS. Zero risk to existing mail and web hosting.
2. **Phase 2 (3–12 months, when needed):** Migrate the full `blauweiss-edv.com` zone to Cloudflare once mail and web hosting have either been migrated to modern providers, or have been verified as importable cleanly.
3. **Phase 3 (optional, long-term):** Transfer domain registration to Cloudflare Registrar, codify DNS-as-code via Terraform.

### Deutsch

CLARISSA hat aktuell keine präsentable öffentliche Adresse. Die GitLab-Pages-URL `irena-40cc50.gitlab.io` ist nicht merkbar und für Marketing oder Kundenkontakt ungeeignet. Wir schlagen vor, CLARISSA unter `clarissa.blauweiss-edv.com` erreichbar zu machen, mit Cloudflare als DNS-Provider für API-gestützte Automatisierung.

Die Migration ist in **drei Phasen** strukturiert, jede für sich nutzbar und reversibel:

1. **Phase 1 (jetzt):** Nur die Subzone `clarissa.*` an Cloudflare delegieren. Die Hauptzone `blauweiss-edv.com` bleibt bei IONOS. Null Risiko für bestehende Mail und Webhosting.
2. **Phase 2 (3–12 Monate, bei Bedarf):** Vollmigration der `blauweiss-edv.com`-Zone zu Cloudflare, sobald Mail und Webhosting entweder zu modernen Anbietern umgezogen oder als sauber importierbar verifiziert wurden.
3. **Phase 3 (optional, langfristig):** Domain-Registrierung zu Cloudflare Registrar transferieren, DNS-as-Code via Terraform.

---

## 2. Problem Statement · Problembeschreibung

### English

**Current situation:**
- CLARISSA is served via GitLab Pages at `irena-40cc50.gitlab.io`, a system-generated URL that cannot be customized.
- The 8-character hash makes the URL unmemorable, hard to read aloud, and inappropriate for SPE Europe 2026 references, business cards, email signatures, or any public-facing context.
- The `blauweiss-edv.com` domain is registered at IONOS (1&1), where DNS is also hosted. IONOS does not offer a public DNS API for standard accounts, requiring manual web-UI clicks for every DNS change.
- Mail (`@blauweiss-edv.com`) is actively used and hosted at IONOS. Disruption is unacceptable.

**Why this matters now:**
- Issue #149 commits to a marketing-ready landing page as part of CLARISSA's public surface.
- Future projects under the same organization (Profile Service, Dialectic AI, AppTrack) will benefit from a DNS workflow that can be automated.

### Deutsch

**Aktuelle Situation:**
- CLARISSA läuft auf GitLab Pages unter `irena-40cc50.gitlab.io`, einer system-generierten URL, die nicht angepasst werden kann.
- Der 8-Zeichen-Hash macht die URL nicht merkbar, schwer mündlich kommunizierbar und unpassend für SPE Europe 2026, Visitenkarten, Email-Signaturen oder jeden öffentlichen Kontext.
- Die Domain `blauweiss-edv.com` ist bei IONOS (1&1) registriert, DNS liegt ebenfalls dort. IONOS bietet keine öffentliche DNS-API für Standard-Accounts; jede DNS-Änderung erfordert manuelle Web-UI-Klicks.
- Mail (`@blauweiss-edv.com`) wird produktiv genutzt und liegt bei IONOS. Eine Unterbrechung ist nicht akzeptabel.

**Warum jetzt:**
- Issue #149 verpflichtet uns auf eine marketing-fähige Landing-Page als Teil von CLARISSAs öffentlicher Präsenz.
- Künftige Projekte unter derselben Organisation (Profile Service, Dialectic AI, AppTrack) profitieren von einem automatisierbaren DNS-Workflow.

---

## 3. Why Cloudflare · Warum Cloudflare

### English

Three categories of reasons, ordered by relevance to our context:

**3.1 — API Access (the actual trigger)**

IONOS has no open DNS API for standard webhosting accounts. Every DNS record change requires manual web-UI login and clicks. Cloudflare offers a mature REST API addressable with a scoped API token.

Practical impact:
- *Current ask* (creating the `clarissa` subdomain): IONOS = manual clicks. Cloudflare = two API calls by Claude.
- *Future DNS changes* (more subdomains, third-party verifications, certificate challenges): IONOS = manual every time. Cloudflare = automated, documented per issue.
- *Infrastructure-as-Code possible:* DNS records can live in a Terraform/Pulumi file, reviewed via MR, with full audit history. Not possible at IONOS.

This is the only reason that genuinely matters for our current context. The other two categories are nice-to-haves.

**3.2 — Free Bundled Features (optional, ignorable)**

Cloudflare's free plan includes:
- *CDN caching* for static content (relevant for GitLab Pages if traffic grows)
- *DDoS protection* at L3/L4 (overkill for a demo page, possibly relevant later)
- *Privacy-respecting analytics* (no cookies, GDPR-friendly)
- *Page Rules / Redirects* (e.g. `www.clarissa.*` → `clarissa.*` without code)
- *Workers* (edge serverless functions — relevant medium-term for CLARISSA API edge caching)
- *R2 object storage* (S3-compatible, no egress fees — backup option)

We don't need these. But they exist for free if needs arise. IONOS either lacks them or charges for them.

**3.3 — DNS Performance (technically true, practically irrelevant)**

Cloudflare's anycast nameserver network responds under 20ms globally. IONOS responds similarly fast in Europe, slower overseas. Negligible for our Europe-focused use case.

**What Cloudflare does *not* provide:**

- **Mail hosting.** Cloudflare is not a mail provider. `@blauweiss-edv.com` mailboxes stay at IONOS regardless of DNS hosting. (Cloudflare's "Email Routing" is forwarding only, not a full mailbox replacement.)
- **Classical webhosting.** Cloudflare has Pages (static) and Workers (serverless), but no PHP/MySQL hosting. If `blauweiss-edv.com` ever needs dynamic hosting, a separate host (IONOS, Hetzner, etc.) remains necessary.
- **.at domain registration.** Cloudflare Registrar supports a limited TLD set. `.com`/`.de`/`.dev`/`.ai` yes, `.at` no.

### Deutsch

Drei Kategorien von Gründen, nach Relevanz für unseren Kontext sortiert:

**3.1 — API-Zugriff (der eigentliche Auslöser)**

IONOS hat keine offene DNS-API für Standard-Webhosting-Accounts. Jede DNS-Record-Änderung erfordert manuelles Einloggen ins Web-UI. Cloudflare bietet eine ausgereifte REST-API, ansprechbar mit einem berechtigungsbeschränkten API-Token.

Praktische Auswirkungen:
- *Aktuelle Anforderung* (Anlegen der `clarissa`-Subdomain): IONOS = manuelle Klicks. Cloudflare = zwei API-Calls durch Claude.
- *Künftige DNS-Änderungen* (weitere Subdomains, Drittanbieter-Verifizierungen, Zertifikats-Challenges): IONOS = jedes Mal manuell. Cloudflare = automatisiert, per Issue dokumentiert.
- *Infrastructure-as-Code möglich:* DNS-Records können in einem Terraform/Pulumi-File leben, per MR reviewt, mit vollständiger Audit-Historie. Bei IONOS unmöglich.

Das ist der einzige Grund, der für unseren aktuellen Kontext wirklich zählt. Die anderen zwei Kategorien sind Nice-to-haves.

**3.2 — Kostenlose Beilagen-Features (optional, ignorierbar)**

Cloudflares Free Plan beinhaltet:
- *CDN-Caching* für statische Inhalte (relevant für GitLab Pages bei wachsendem Traffic)
- *DDoS-Schutz* auf L3/L4 (übertrieben für eine Demo-Page, mittelfristig vielleicht relevant)
- *Datenschutz-konforme Analytics* (ohne Cookies, DSGVO-freundlich)
- *Page Rules / Redirects* (z.B. `www.clarissa.*` → `clarissa.*` ohne Code)
- *Workers* (Edge-Serverless-Funktionen — mittelfristig spannend für CLARISSA-API-Edge-Caching)
- *R2 Object Storage* (S3-kompatibel, ohne Egress-Kosten — Backup-Option)

Brauchen wir nicht. Aber sie sind kostenlos verfügbar, falls Bedarf entsteht. IONOS hat sie entweder gar nicht oder als kostenpflichtige Add-ons.

**3.3 — DNS-Performance (technisch wahr, praktisch egal)**

Cloudflares Anycast-Nameserver-Netz antwortet weltweit unter 20ms. IONOS antwortet in Europa ähnlich schnell, in Übersee langsamer. Vernachlässigbar für unseren Europa-fokussierten Use-Case.

**Was Cloudflare *nicht* bietet:**

- **Mail-Hosting.** Cloudflare ist kein Mail-Provider. `@blauweiss-edv.com`-Postfächer bleiben bei IONOS, egal wo das DNS liegt. (Cloudflares „Email Routing" ist nur Forwarding, kein vollständiger Mail-Ersatz.)
- **Klassisches Webhosting.** Cloudflare hat Pages (statisch) und Workers (serverless), aber kein PHP/MySQL-Hosting. Falls `blauweiss-edv.com` jemals dynamisches Hosting braucht, bleibt ein separater Hoster (IONOS, Hetzner, etc.) nötig.
- **.at-Domain-Registrierung.** Cloudflare Registrar unterstützt ein begrenztes TLD-Set. `.com`/`.de`/`.dev`/`.ai` ja, `.at` nicht.

---

## 4. Migration Strategy — Three Phases · Migrationsstrategie — Drei Phasen

### English

#### Phase 1 (now): Subzone Delegation for CLARISSA Demo

**Goal:** `clarissa.blauweiss-edv.com` live as the demo URL, zero risk to existing infrastructure.

**Steps:**
1. Create Cloudflare account, add subzone `clarissa.blauweiss-edv.com` (not the apex).
2. At IONOS: one-time addition of two NS records pointing the subzone to Cloudflare nameservers. This is the only step requiring IONOS access.
3. At Cloudflare (via API): set CNAME `clarissa` → `irena-40cc50.gitlab.io` and TXT record for GitLab Pages domain verification.
4. GitLab Pages: configure custom domain. Let's Encrypt certificate is automatically issued.
5. Result: demo page live at clean URL. IONOS practically not needed for CLARISSA after this point.

**Risk:** minimal. Existing mail and main website remain untouched. Safety valve: if anything fails, deleting the NS records at IONOS removes Cloudflare's authority over the subzone — full rollback in one record removal.

**IONOS dependency:** one-time, ~5 minutes of clicks. After Phase 1, IONOS access is not needed for CLARISSA-related work.

#### Phase 2 (3–12 months, when needed): Full Zone Migration

**Triggers** (any one is sufficient):
- We want more subdomains for other projects and find IONOS clicking tedious.
- We want to migrate mail away from IONOS (to Google Workspace, Microsoft 365, Migadu, Fastmail, etc. — any provider with better spam filtering and modern IMAP).
- We want to migrate the main website `blauweiss-edv.com` from IONOS shared hosting to something modern (Cloudflare Pages, Vercel, Netlify, own VPS).

**Steps:**
1. *If mail is migrated:* first set up new mail provider, configure mailboxes, sync messages. Obtain MX/SPF/DKIM/DMARC records from new provider.
2. *If website is migrated:* set up new hosting, deploy content, verify under temporary URL.
3. At Cloudflare: create the main zone `blauweiss-edv.com`, add all records (from IONOS scan or new mail/web provider).
4. Verify via direct Cloudflare-NS query before flipping NS at IONOS.
5. At IONOS: switch nameservers to Cloudflare.
6. Existing `clarissa.*` subzone merges seamlessly into the main zone.

**Risk:** well-controlled, because mail and website are not migrated *simultaneously* with DNS. The actual heavy lifting happens *before* the DNS switch. The DNS switch is then "flip a switch", not "perform open-heart surgery".

#### Phase 3 (optional, long-term): Optimizations

- Transfer domain registration from IONOS to Cloudflare Registrar (saves ~5 €/year, one fewer vendor; 60-day transfer lock applies).
- Codify DNS records as Terraform/Pulumi — records in Git, reviews via MR.
- Cloudflare Workers for edge API caching if CLARISSA-API traffic grows.
- Page Rules for `www.` → apex redirects, other routing policies.

### Deutsch

#### Phase 1 (jetzt): Subzone-Delegation für CLARISSA-Demo

**Ziel:** `clarissa.blauweiss-edv.com` als Demo-URL live, null Risiko für bestehende Infrastruktur.

**Schritte:**
1. Cloudflare-Account anlegen, Subzone `clarissa.blauweiss-edv.com` hinzufügen (nicht die Apex-Domain).
2. Bei IONOS: einmaliges Anlegen von zwei NS-Records, die die Subzone auf Cloudflare-Nameserver zeigen. Das ist der einzige Schritt, der IONOS-Zugang braucht.
3. Bei Cloudflare (via API): CNAME `clarissa` → `irena-40cc50.gitlab.io` und TXT-Record für GitLab-Pages-Domain-Verifizierung setzen.
4. GitLab Pages: Custom Domain konfigurieren. Let's-Encrypt-Zertifikat wird automatisch ausgestellt.
5. Resultat: Demo-Page live unter sauberer URL. IONOS praktisch nicht mehr nötig für CLARISSA nach diesem Punkt.

**Risiko:** minimal. Bestehende Mail und Hauptwebseite bleiben unangetastet. Sicherheitsventil: wenn etwas fehlschlägt, entfernt das Löschen der NS-Records bei IONOS Cloudflares Autorität über die Subzone — vollständiger Rollback durch eine einzige Record-Entfernung.

**IONOS-Abhängigkeit:** einmalig, ~5 Minuten Klicks. Nach Phase 1 ist kein IONOS-Zugang mehr nötig für CLARISSA-bezogene Arbeit.

#### Phase 2 (3–12 Monate, bei Bedarf): Vollmigration der Zone

**Auslöser** (einer reicht):
- Wir wollen weitere Subdomains für andere Projekte und merken, dass IONOS-Klickerei nervt.
- Wir wollen Mail von IONOS wegmigrieren (zu Google Workspace, Microsoft 365, Migadu, Fastmail, etc. — irgendein Provider mit besseren Spam-Filtern und modernem IMAP).
- Wir wollen die Hauptwebseite `blauweiss-edv.com` von IONOS-Shared-Hosting auf was Modernes umstellen (Cloudflare Pages, Vercel, Netlify, eigener VPS).

**Schritte:**
1. *Falls Mail migriert wird:* zuerst neuen Mail-Provider aufsetzen, Postfächer einrichten, Mails synchronisieren. MX/SPF/DKIM/DMARC-Records vom neuen Provider holen.
2. *Falls Webseite migriert wird:* neues Hosting aufsetzen, Inhalte deployen, unter temporärer URL verifizieren.
3. Bei Cloudflare: Hauptzone `blauweiss-edv.com` anlegen, alle Records eintragen (von IONOS-Scan oder neuem Mail/Web-Provider).
4. Via direkter Cloudflare-NS-Query verifizieren, *bevor* NS bei IONOS umgestellt wird.
5. Bei IONOS: Nameserver auf Cloudflare umstellen.
6. Bestehende `clarissa.*`-Subzone integriert sich nahtlos in die Hauptzone.

**Risiko:** gut kontrolliert, weil Mail und Webseite nicht *gleichzeitig* mit DNS migriert werden. Die eigentliche Schwerarbeit passiert *vor* dem DNS-Switch. Der DNS-Switch ist dann „Schalter umlegen", nicht „Operation am offenen Herzen".

#### Phase 3 (optional, langfristig): Optimierungen

- Domain-Registrierung von IONOS zu Cloudflare Registrar transferieren (spart ~5 €/Jahr, ein Anbieter weniger; 60-Tage-Transfer-Sperre beachten).
- DNS-Records als Terraform/Pulumi codifizieren — Records in Git, Reviews via MR.
- Cloudflare Workers für Edge-API-Caching, falls CLARISSA-API-Traffic wächst.
- Page Rules für `www.` → Apex-Redirects, andere Routing-Politik.

---

## 5. Risk Analysis · Risikoanalyse

### English

#### Mail continuity

The mail account `@blauweiss-edv.com` is in active use. Disruption is unacceptable. Risk assessment by phase:

| Phase | Mail risk | Reason |
|---|---|---|
| Phase 1 (subzone) | **None** | IONOS zone untouched. Subzone only handles `clarissa.*` subdomain. |
| Phase 2 (full zone), unprepared | Medium (10–20%) | Cloudflare's auto-scan may miss DKIM records with unusual selector names. |
| Phase 2 (full zone), with stop-and-verify | Very low (<2%) | All records cross-checked between IONOS and Cloudflare before NS switch. |

#### Verification strategy for Phase 2

Cloudflare's nameservers respond to queries *before* they become authoritative for the world. This enables pre-flight verification:

```bash
dig @abby.ns.cloudflare.com MX blauweiss-edv.com
dig @abby.ns.cloudflare.com TXT blauweiss-edv.com
dig @abby.ns.cloudflare.com TXT _dmarc.blauweiss-edv.com
dig @abby.ns.cloudflare.com TXT default._domainkey.blauweiss-edv.com
```

If Cloudflare returns the same records as IONOS would, the NS switch is safe. Claude can run this verification automatically.

#### Rollback semantics

- **Phase 1 rollback:** delete NS records at IONOS. Subzone authority dissolves immediately at IONOS level; propagation to resolvers takes minutes to hours depending on TTL.
- **Phase 2 rollback:** switch NS back to IONOS defaults. Propagation takes 6–24 hours during which DNS answers are globally inconsistent (some resolvers still cached Cloudflare answers). Rollback is a real safety net for catastrophic errors, not a casual "let me think about it" mechanism.

#### Vendor lock-in

Cloudflare zones are exportable in BIND format. Migrating away to another DNS provider is straightforward. Cloudflare is not a sticky lock-in.

### Deutsch

#### Mail-Kontinuität

Der Mail-Account `@blauweiss-edv.com` wird produktiv genutzt. Eine Unterbrechung ist nicht akzeptabel. Risikobewertung pro Phase:

| Phase | Mail-Risiko | Grund |
|---|---|---|
| Phase 1 (Subzone) | **Null** | IONOS-Zone unangetastet. Subzone behandelt nur die `clarissa.*`-Subdomain. |
| Phase 2 (Vollzone), unvorbereitet | Mittel (10–20%) | Cloudflares Auto-Scan kann DKIM-Records mit ungewöhnlichen Selector-Namen übersehen. |
| Phase 2 (Vollzone), mit Stopp-und-Verifiziere | Sehr gering (<2%) | Alle Records werden zwischen IONOS und Cloudflare abgeglichen, bevor NS umgestellt wird. |

#### Verifizierungs-Strategie für Phase 2

Cloudflares Nameserver beantworten Queries *bevor* sie für die Welt autoritativ werden. Das ermöglicht Pre-Flight-Verifikation:

```bash
dig @abby.ns.cloudflare.com MX blauweiss-edv.com
dig @abby.ns.cloudflare.com TXT blauweiss-edv.com
dig @abby.ns.cloudflare.com TXT _dmarc.blauweiss-edv.com
dig @abby.ns.cloudflare.com TXT default._domainkey.blauweiss-edv.com
```

Wenn Cloudflare dieselben Records zurückgibt wie IONOS, ist der NS-Switch safe. Claude kann diese Verifikation automatisiert durchführen.

#### Rollback-Semantik

- **Phase-1-Rollback:** NS-Records bei IONOS löschen. Subzone-Autorität löst sich sofort auf IONOS-Ebene auf; Propagation zu Resolvern dauert Minuten bis Stunden, je nach TTL.
- **Phase-2-Rollback:** NS bei IONOS auf Defaults zurücksetzen. Propagation dauert 6–24 Stunden, während derer DNS-Antworten global inkonsistent sind (manche Resolver haben noch Cloudflare-Antworten gecacht). Rollback ist ein echtes Sicherheitsnetz für katastrophale Fehler, kein lockerer „Lass mich nochmal überlegen"-Mechanismus.

#### Vendor-Lock-in

Cloudflare-Zonen sind im BIND-Format exportierbar. Eine Migration zu einem anderen DNS-Provider ist geradlinig. Cloudflare ist kein klebriger Lock-in.

---

## 6. Alternatives Considered · Geprüfte Alternativen

### English

| Alternative | Pro | Con | Verdict |
|---|---|---|---|
| **Stay at IONOS** | No migration needed. | No API access, manual clicks for every change, no IaC possible. Doesn't solve the actual problem. | Rejected. |
| **nip.io / sslip.io wildcard DNS** | No DNS setup at all. | Cannot set TXT records → no GitLab Pages domain verification → no Let's Encrypt cert. Hostname routing also broken. | Technically infeasible. |
| **Register new `.de` or `.dev` domain at Cloudflare** | Zero IONOS dependency. Fresh marketing identity option. | Costs ~10 €/year. Splits brand identity from `.com`. Doesn't solve the root API access issue for the main domain. | Viable as a parallel path, but doesn't replace the strategic move to Cloudflare. |
| **Full IONOS → Cloudflare migration in one step** | Solves API access immediately. | Higher mail-risk surface. Requires more IONOS access than Phase 1. | Rejected as Phase 1, deferred to Phase 2 once mail/web concerns are independently addressed. |
| **Subzone delegation (proposed)** | Minimal IONOS access, zero mail risk, full API access for CLARISSA. Sets up Phase 2 to be easier, not harder. | Requires running two Cloudflare zones temporarily during Phase 2 transition (cosmetic, not technical issue). | **Recommended.** |

### Deutsch

| Alternative | Pro | Contra | Verdikt |
|---|---|---|---|
| **Bei IONOS bleiben** | Keine Migration nötig. | Kein API-Zugriff, manuelle Klicks für jede Änderung, kein IaC möglich. Löst das eigentliche Problem nicht. | Verworfen. |
| **nip.io / sslip.io Wildcard-DNS** | Kein DNS-Setup nötig. | Kann keine TXT-Records setzen → keine GitLab-Pages-Domain-Verifikation → kein Let's-Encrypt-Zertifikat. Hostname-Routing auch kaputt. | Technisch nicht machbar. |
| **Neue `.de`- oder `.dev`-Domain bei Cloudflare registrieren** | Null IONOS-Abhängigkeit. Frische Marketing-Identität optional. | Kostet ~10 €/Jahr. Spaltet Markenidentität von `.com`. Löst das eigentliche API-Zugriffsproblem für die Hauptdomain nicht. | Als paralleler Pfad denkbar, ersetzt aber nicht den strategischen Schritt zu Cloudflare. |
| **Vollmigration IONOS → Cloudflare in einem Schritt** | Löst API-Zugriff sofort. | Höhere Mail-Risiko-Fläche. Erfordert mehr IONOS-Zugang als Phase 1. | Als Phase 1 verworfen, auf Phase 2 verschoben, sobald Mail/Web-Themen unabhängig adressiert sind. |
| **Subzone-Delegation (vorgeschlagen)** | Minimaler IONOS-Zugang, null Mail-Risiko, voller API-Zugriff für CLARISSA. Macht Phase 2 später *einfacher*, nicht schwerer. | Erfordert temporär zwei Cloudflare-Zonen während Phase-2-Übergang (kosmetisch, kein technisches Problem). | **Empfohlen.** |

---

## 7. Concrete Steps for Phase 1 · Konkrete Schritte für Phase 1

### English

**Prerequisite — once-off action requiring IONOS access:**
After Cloudflare account creation and subzone setup (which produces two nameserver names like `abby.ns.cloudflare.com` and `jim.ns.cloudflare.com`), enter the following two NS records in the IONOS DNS panel for `blauweiss-edv.com`:

```
clarissa    NS    abby.ns.cloudflare.com    (TTL: 1h or default)
clarissa    NS    jim.ns.cloudflare.com     (TTL: 1h or default)
```

**Everything else is handled by Claude via API:**
1. Verify subzone delegation is active (`dig NS clarissa.blauweiss-edv.com` shows Cloudflare NS).
2. Create GitLab Pages custom domain via GitLab API → obtain TXT verification token.
3. Set DNS records at Cloudflare via API:
   - `clarissa.blauweiss-edv.com` CNAME → `irena-40cc50.gitlab.io` (proxied=false)
   - `_gitlab-pages-verification-code.clarissa.blauweiss-edv.com` TXT → `<token>`
4. Poll GitLab Pages domain endpoint until `verified=true` and certificate is provisioned.
5. Set `clarissa.blauweiss-edv.com` as primary domain in GitLab Pages → automatic 308 redirects from `irena-40cc50.gitlab.io` activate.
6. Update Issue #149 with completion status, ADR entry.

**Estimated total time:** Phase 1 active work ~30 minutes (most of which is waiting for DNS propagation and cert provisioning).

### Deutsch

**Voraussetzung — einmalige Aktion mit IONOS-Zugang:**
Nach Cloudflare-Account-Erstellung und Subzone-Setup (woraus zwei Nameserver-Namen wie `abby.ns.cloudflare.com` und `jim.ns.cloudflare.com` entstehen), folgende zwei NS-Records im IONOS-DNS-Panel für `blauweiss-edv.com` eintragen:

```
clarissa    NS    abby.ns.cloudflare.com    (TTL: 1h oder Default)
clarissa    NS    jim.ns.cloudflare.com     (TTL: 1h oder Default)
```

**Alles andere wird von Claude via API erledigt:**
1. Subzone-Delegation als aktiv verifizieren (`dig NS clarissa.blauweiss-edv.com` zeigt Cloudflare-NS).
2. GitLab-Pages-Custom-Domain via GitLab-API anlegen → TXT-Verifizierungs-Token holen.
3. DNS-Records bei Cloudflare via API setzen:
   - `clarissa.blauweiss-edv.com` CNAME → `irena-40cc50.gitlab.io` (proxied=false)
   - `_gitlab-pages-verification-code.clarissa.blauweiss-edv.com` TXT → `<token>`
4. GitLab-Pages-Domain-Endpoint pollen bis `verified=true` und Zertifikat ausgestellt.
5. `clarissa.blauweiss-edv.com` als Primary Domain in GitLab Pages setzen → automatische 308-Redirects von `irena-40cc50.gitlab.io` aktiv.
6. Issue #149 mit Abschluss-Status updaten, ADR-Eintrag.

**Geschätzte Gesamtzeit:** Phase-1-aktive Arbeit ~30 Minuten (davon Großteil Warten auf DNS-Propagation und Cert-Provisionierung).

---

## 8. Decision Request · Entscheidungsanfrage

### English

We request team approval to proceed with **Phase 1: Subzone Delegation** as described above.

Reviewers:
- **Wolfram Laube** — final decision (account holder, IONOS access)
- **Mike, Ian, Douglas** — review for technical soundness and any concerns we may have missed

Phase 2 and Phase 3 are not part of this decision and will be re-evaluated separately when triggers occur.

### Deutsch

Wir bitten um Team-Freigabe für **Phase 1: Subzone-Delegation** wie oben beschrieben.

Reviewer:
- **Wolfram Laube** — finale Entscheidung (Account-Inhaber, IONOS-Zugang)
- **Mike, Ian, Douglas** — Review auf technische Stimmigkeit und übersehene Bedenken

Phase 2 und Phase 3 sind nicht Teil dieser Entscheidung und werden separat re-evaluiert, sobald Auslöser eintreten.

---

## Appendix · Anhang

### Glossary · Glossar

| Term | English | Deutsch |
|---|---|---|
| Apex domain | The bare domain without subdomain (e.g., `blauweiss-edv.com`). | Die nackte Domain ohne Subdomain (z.B. `blauweiss-edv.com`). |
| Subzone | A subdomain delegated to a different authoritative DNS provider. | Eine Subdomain, die an einen anderen autoritativen DNS-Provider delegiert ist. |
| NS record | Nameserver record — tells the DNS hierarchy where to look for authoritative answers. | Nameserver-Record — sagt der DNS-Hierarchie, wo autoritative Antworten zu finden sind. |
| CNAME | Canonical name record — aliases one domain to another. | Canonical-Name-Record — verweist eine Domain auf eine andere. |
| TTL | Time to Live — how long a DNS record may be cached. | Time to Live — wie lange ein DNS-Record gecacht werden darf. |
| MX | Mail Exchange record — tells senders where to deliver mail for the domain. | Mail-Exchange-Record — sagt Absendern, wohin Mail für die Domain zugestellt werden soll. |
| SPF/DKIM/DMARC | Email authentication standards published as TXT records. | E-Mail-Authentifizierungs-Standards, publiziert als TXT-Records. |
| ACME challenge | Protocol step for automated certificate issuance (Let's Encrypt). | Protokoll-Schritt für automatisierte Zertifikats-Ausstellung (Let's Encrypt). |
| Anycast | Routing technique where multiple servers share the same IP, traffic goes to the nearest. | Routing-Technik, bei der mehrere Server dieselbe IP teilen, Traffic geht zum nächsten. |
| IaC | Infrastructure as Code — managing infrastructure via versioned configuration files. | Infrastructure as Code — Infrastruktur-Verwaltung via versionierte Konfigurationsdateien. |

### References · Referenzen

- GitLab Issue [CLARISSA#149](https://gitlab.com/wolfram_laube/blauweiss_llc/projects/clarissa/-/issues/149) — Custom Domain & Marketing Landing
- [Cloudflare DNS Documentation](https://developers.cloudflare.com/dns/)
- [GitLab Pages Custom Domain Documentation](https://docs.gitlab.com/ee/user/project/pages/custom_domains_ssl_tls_certification/)
- [RFC 1034](https://www.rfc-editor.org/rfc/rfc1034) — DNS concepts and facilities (incl. zone delegation)
