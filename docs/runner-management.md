# GitLab Runner Management

> Dokumentation für alle CLARISSA GitLab Runner

## Runner Übersicht

| Runner | Location | Executor | Tags | Status | Kosten |
|--------|----------|----------|------|--------|--------|
| mac-group-shell | Mac (lokal) | Shell | `mac`, `shell`, `deploy` | 🟢 Always on | $0 |
| mac-docker | Mac (lokal) | Docker | `docker` | 🟢 Always on | $0 |
| mac-k8s | Mac (Docker Desktop K8s) | Kubernetes | `mac-k8s`, `k8s`, `docker` | 🟢 Always on | $0 |
| gcp-k8s | GCP VM (K3s) | Kubernetes | `gcp`, `k8s`, `docker` | 🔴 On-demand | ~$0.02/h |

## Mac Runner (Lokal)

### Voraussetzungen

- GitLab Runner installiert: `brew install gitlab-runner`
- Docker Desktop läuft (für `mac-docker` und `mac-k8s`)
- Kubernetes aktiviert in Docker Desktop (für `mac-k8s`)

### Runner starten

```bash
# Als Hintergrund-Service (empfohlen)
brew services start gitlab-runner

# Oder im Vordergrund (für Debugging)
gitlab-runner run
```

### Runner stoppen

```bash
brew services stop gitlab-runner
```

### Status prüfen

```bash
gitlab-runner status
gitlab-runner list
gitlab-runner verify
```

### Config Location

```
~/.gitlab-runner/config.toml
```

## GCP Runner (Cloud)

### VM Details

| Key | Value |
|-----|-------|
| Instance Name | `gitlab-runner` |
| Zone | `europe-west3-a` |
| Machine Type | `e2-small` |
| OS | Ubuntu + K3s |
| Kosten | ~$13/Monat (wenn 24/7), ~$0.02/Stunde |

### VM starten

**Option 1: GitLab Pipeline (empfohlen)**
```
GitLab → CI/CD → Pipelines → Job "gcp-vm-start" ▶️
```

**Option 2: gcloud CLI**
```bash
gcloud compute instances start gitlab-runner \
  --zone=europe-west3-a \
  --project=myk8sproject-207017
```

### VM stoppen

**Option 1: GitLab Pipeline (empfohlen)**
```
GitLab → CI/CD → Pipelines → Job "gcp-vm-stop" ▶️
```

**Option 2: gcloud CLI**
```bash
gcloud compute instances stop gitlab-runner \
  --zone=europe-west3-a \
  --project=myk8sproject-207017
```

### Status prüfen

**Option 1: GitLab Pipeline**
```
GitLab → CI/CD → Pipelines → Job "gcp-vm-status" ▶️
```

**Option 2: gcloud CLI**
```bash
gcloud compute instances describe gitlab-runner \
  --zone=europe-west3-a \
  --project=myk8sproject-207017 \
  --format="table(name,status,networkInterfaces[0].accessConfigs[0].natIP)"
```

### SSH Zugang

```bash
gcloud compute ssh gitlab-runner \
  --zone=europe-west3-a \
  --project=myk8sproject-207017
```

### Logs auf der VM

```bash
# GitLab Runner Logs
sudo journalctl -u gitlab-runner -f

# K3s Logs
sudo journalctl -u k3s -f

# Runner Pods
sudo kubectl get pods -n gitlab-runner
```

## Jobs auf bestimmte Runner lenken

```yaml
# Nur Mac Shell Runner
job1:
  tags: [mac, shell]

# Nur Mac Docker Runner
job2:
  tags: [docker]
  image: python:3.11

# Nur Mac K8s Runner (lokal testen)
job3:
  tags: [mac-k8s]
  image: python:3.11

# Nur GCP K8s Runner (production)
job4:
  tags: [gcp, k8s]
  image: python:3.11
```

## Empfohlener Workflow

```
Entwicklung:     mac-group-shell oder mac-docker
K8s Testing:     mac-k8s (lokal, kostenlos)
K8s Production:  gcp-k8s (VM bei Bedarf starten)
```

## Benchmarks (Jan 2026)

| Runner | Typische Job-Zeit |
|--------|-------------------|
| mac-group-shell | ~26s |
| gcp-shell | ~39s |
| mac-k8s | ~52s |
| gcp-k8s | ~72s |
| mac-docker | ~167s (Container-Overhead) |

## Troubleshooting

### Runner offline?

```bash
# Mac: Service neustarten
brew services restart gitlab-runner

# GCP: VM starten
gcloud compute instances start gitlab-runner --zone=europe-west3-a
```

### Jobs hängen?

```bash
# Aktive Jobs anzeigen
gitlab-runner list

# Config validieren
gitlab-runner verify
```

### Docker-Probleme auf Mac?

```bash
# Docker Desktop neustarten
osascript -e 'quit app "Docker"'
open -a Docker

# Warten bis Docker ready
docker info
```

---

*Letzte Aktualisierung: Januar 2026*
