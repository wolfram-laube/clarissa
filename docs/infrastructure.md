# CLARISSA Infrastructure Credentials

> ⚠️ **PRIVATE** - Dieses Dokument enthält echte Credentials.
> Nur möglich weil das Repository privat ist.

## GitLab

| Key | Value |
|-----|-------|
| Project ID | `77260390` |
| Project URL | https://gitlab.com/wolfram_laube/blauweiss_llc/irena |
| PAT (Personal Access Token) | `glpat-B2kbE0n56oTpioepn5ZT-W86MQp1OnN4Y3gK.01.1007svpwt` |
| Default Branch | `main` |

### API Beispiele
```bash
# List commits
curl -H "PRIVATE-TOKEN: glpat-B2kbE0n56oTpioepn5ZT-W86MQp1OnN4Y3gK.01.1007svpwt" \
  "https://gitlab.com/api/v4/projects/77260390/repository/commits"

# Fetch file
curl -H "PRIVATE-TOKEN: glpat-B2kbE0n56oTpioepn5ZT-W86MQp1OnN4Y3gK.01.1007svpwt" \
  "https://gitlab.com/api/v4/projects/77260390/repository/files/README.md/raw?ref=main"
```

---

## GitLab Runner Matrix

> 📖 Vollständige Dokumentation: [Runner Management](runner-management.md)

### Ziel: 12 Runner (4 Maschinen × 3 Executors)

| Machine | Shell | Docker | K8s | Status |
|---------|-------|--------|-----|--------|
| Mac #1 | ✅ | ✅ | ✅ | 3/3 online |
| Mac #2 | ✅ | ✅ | ✅ | 3/3 online |
| Linux Yoga | ✅ | ✅ | ✅ | 3/3 online |
| GCP Nordic | ❌ | ✅ | ❌ | 1/3 online |

**Aktuell: 10/12 Runner online** (Stand: 2026-01-20)

### GCP Runner IDs

| Runner Name | ID | Executor | Status |
|-------------|-----|----------|--------|
| Nordic Docker Runner | 51385121 | docker | ✅ online |
| gcp-shell | 51223882 | shell | ❌ stale (alt) |
| gcp-group-shell | 51231875 | shell | ❌ offline (alt) |

---

## GCP (Google Cloud Platform)

| Key | Value |
|-----|-------|
| Project ID | `myk8sproject-207017` |
| Project Number | `518587440396` |
| Service Account | `claude-assistant@myk8sproject-207017.iam.gserviceaccount.com` |
| Region | `europe-north2` |
| Zone | `europe-north2-a` |

### Runner VM

| Key | Value |
|-----|-------|
| Instance Name | `gitlab-runner-nordic` |
| Machine Type | `e2-small` (2 vCPU, 2 GB RAM) |
| Disk | 20 GB |
| OS | Ubuntu + Docker |
| Internal IP | `10.226.0.4` |
| External IP | `34.51.185.83` (kann sich ändern) |
| Status | ✅ **RUNNING** |
| Kosten | ~$13/Monat (24/7) |

### VM Steuerung

**Via GitLab Pipeline (empfohlen):**
- `gcp-vm-start` - VM starten
- `gcp-vm-stop` - VM stoppen  
- `gcp-vm-status` - Status prüfen

**Via CLI:**
```bash
# Starten
gcloud compute instances start gitlab-runner-nordic --zone=europe-north2-a --project=myk8sproject-207017

# Stoppen
gcloud compute instances stop gitlab-runner-nordic --zone=europe-north2-a --project=myk8sproject-207017

# Status
gcloud compute instances describe gitlab-runner-nordic --zone=europe-north2-a --format="table(name,status)"

# SSH
gcloud compute ssh gitlab-runner-nordic --zone=europe-north2-a --project=myk8sproject-207017
```

### TODO: GCP Runner vervollständigen

1. **K3s installieren:**
   ```bash
   curl -sfL https://get.k3s.io | sh -
   ```

2. **Shell Runner registrieren:**
   ```bash
   gitlab-runner register --executor shell --description "GCP Shell Runner"
   ```

3. **K8s Runner registrieren:**
   ```bash
   gitlab-runner register --executor kubernetes --description "GCP K8s Runner"
   ```

---

## Google Drive

| Key | Value |
|-----|-------|
| Shared Folder ID | `1qh0skTeyRNs4g9KwAhpd3J8Yj_XENIFs` |
| Folder URL | https://drive.google.com/drive/folders/1qh0skTeyRNs4g9KwAhpd3J8Yj_XENIFs |
| Access | Service Account als Bearbeiter |

---

## LLM APIs

### OpenAI (ChatGPT / IRENA Relay)
| Key | Value |
|-----|-------|
| API Key | `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` |
| Model | `gpt-4o` |
| Use Case | IRENA Consultant (relay.py) |

### Anthropic (Claude-to-Claude)
| Key | Value |
|-----|-------|
| API Key | `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` |
| Model | `claude-3-5-sonnet-20241022` |
| Use Case | IRENA Consultant (claude_relay.py) |
| Status | ⚠️ Needs credits on account |

---

## GitLab CI Variables

Diese Werte sind als CI Variables gesetzt (Settings → CI/CD → Variables):

| Variable | Masked | Purpose |
|----------|--------|---------|
| `GITLAB_TOKEN` | ❌ | CI push-back to repo |
| `OPENAI_API_KEY` | ✅ | relay.py (ChatGPT) |
| `ANTHROPIC_API_KEY` | ✅ | claude_relay.py (Claude) |
| `GOOGLE_DRIVE_FOLDER_ID` | ❌ | Sync packages |
| `GOOGLE_SERVICE_ACCOUNT_KEY` | ❌ | GDrive API |

---

## Änderungshistorie

| Datum | Änderung |
|-------|----------|
| 2026-01-04 | Dokument erstellt |
| 2026-01-05 | GCP Runner Info hinzugefügt |
| 2026-01-20 | VM-Details korrigiert (gitlab-runner-nordic, europe-north2-a), Runner-Matrix aktualisiert |

---

*Letzte Aktualisierung: 2026-01-20*
