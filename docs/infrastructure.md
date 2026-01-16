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

## GitLab Runner

> 📖 Vollständige Dokumentation: [Runner Management](runner-management.md)

### Aktive Runner (Januar 2026)

| Runner | Location | Executor | Tags | Kosten |
|--------|----------|----------|------|--------|
| mac-group-shell | Mac | Shell | `mac`, `shell`, `deploy` | $0 |
| mac-docker | Mac | Docker | `docker` | $0 |
| mac-k8s | Mac (Docker Desktop) | Kubernetes | `mac-k8s`, `k8s` | $0 |
| gcp-k8s | GCP VM | Kubernetes | `gcp`, `k8s` | ~$0.02/h |

---

## GCP (Google Cloud Platform)

| Key | Value |
|-----|-------|
| Project ID | `myk8sproject-207017` |
| Service Account | `claude-assistant@myk8sproject-207017.iam.gserviceaccount.com` |
| Region | `europe-west3` |
| Zone | `europe-west3-a` |

### Runner VM

| Key | Value |
|-----|-------|
| Instance Name | `gitlab-runner` |
| Machine Type | `e2-small` |
| OS | Ubuntu 22.04 + K3s |
| Status | ✅ **Deployed** (on-demand) |
| Kosten | ~$13/Monat (24/7) oder ~$0.02/Stunde |

### VM Steuerung

**Via GitLab Pipeline (empfohlen):**
- `gcp-vm-start` - VM starten
- `gcp-vm-stop` - VM stoppen  
- `gcp-vm-status` - Status prüfen

**Via CLI:**
```bash
# Starten
gcloud compute instances start gitlab-runner --zone=europe-west3-a --project=myk8sproject-207017

# Stoppen
gcloud compute instances stop gitlab-runner --zone=europe-west3-a --project=myk8sproject-207017

# Status
gcloud compute instances describe gitlab-runner --zone=europe-west3-a --format="table(name,status)"
```

---

*Letzte Aktualisierung: Januar 2026*
