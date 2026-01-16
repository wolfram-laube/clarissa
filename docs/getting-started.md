# Getting Started with CLARISSA

> 🎯 **Ziel:** In 15 Minuten CLARISSA lokal laufen haben und verstehen wie alles zusammenhängt.

---

## Übersicht

```
┌─────────────────────────────────────────────────────────────┐
│  Du bist hier                                               │
│       ↓                                                     │
│  1. Prerequisites    → Was du brauchst                      │
│  2. Repository       → Code holen                           │
│  3. Installation     → CLARISSA installieren                │
│  4. Erster Start     → "Hello World"                        │
│  5. Pipeline         → CI/CD verstehen & triggern           │
│  6. Deployment       → Auf Kubernetes deployen              │
│  7. Verifizieren     → Testen ob alles funktioniert         │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. Prerequisites

### Minimum (für lokale Entwicklung)

| Tool | Version | Installation | Check |
|------|---------|--------------|-------|
| Git | 2.30+ | [git-scm.com](https://git-scm.com) | `git --version` |
| Python | 3.11+ | [python.org](https://python.org) | `python3 --version` |
| pip | 21+ | Mit Python | `pip --version` |

### Empfohlen (für Docker/K8s)

| Tool | Version | Installation | Check |
|------|---------|--------------|-------|
| Docker Desktop | 4.0+ | [docker.com](https://docker.com/products/docker-desktop) | `docker --version` |
| kubectl | 1.28+ | Mit Docker Desktop oder [kubernetes.io](https://kubernetes.io/docs/tasks/tools/) | `kubectl version --client` |
| Helm | 3.12+ | `brew install helm` (Mac) | `helm version` |

### Optional (für GCP Deployment)

| Tool | Installation | Check |
|------|--------------|-------|
| gcloud CLI | [cloud.google.com/sdk](https://cloud.google.com/sdk/docs/install) | `gcloud --version` |

---

## 2. Repository klonen

```bash
# Via HTTPS
git clone https://gitlab.com/wolfram_laube/blauweiss_llc/irena.git clarissa
cd clarissa

# Oder via SSH (wenn du einen SSH Key hast)
git clone git@gitlab.com:wolfram_laube/blauweiss_llc/irena.git clarissa
cd clarissa
```

**Struktur:**
```
clarissa/
├── src/clarissa/        # Python Package
├── docs/                # Dokumentation
├── tests/               # Tests
├── scripts/             # Hilfs-Scripts
└── .gitlab-ci.yml       # CI/CD Pipeline
```

---

## 3. Installation

### Option A: Lokale Installation (Entwicklung)

```bash
# Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -e ".[dev]"

# Prüfen ob es funktioniert
clarissa --version
```

### Option B: Docker (empfohlen)

```bash
# Image bauen
docker build -t clarissa:local .

# Prüfen
docker run --rm clarissa:local --version
```

---

## 4. Erster Start ("Hello World")

### CLARISSA CLI testen

```bash
# Hilfe anzeigen
clarissa --help

# Version
clarissa --version

# Einfacher Test: Syntax-Check eines ECLIPSE Decks
clarissa validate examples/spe1.data
```

### Tests lokal ausführen

```bash
# Alle Tests
pytest

# Nur schnelle Tests
pytest -m "not slow"

# Mit Coverage
pytest --cov=src/clarissa
```

---

## 5. GitLab Pipeline verstehen & triggern

### Was ist die Pipeline?

Die Pipeline führt automatisch Tests, Builds und Deployments aus wenn du Code pushst.

```
Push → Build → Test → Deploy
         ↓       ↓       ↓
      Python   pytest  GitLab
      Package  + lint   Pages
```

### Pipeline Status sehen

1. Geh zu: https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/pipelines
2. Grün ✅ = alles OK, Rot ❌ = Fehler

### Pipeline manuell triggern

**Option 1: Web UI**
```
GitLab → CI/CD → Pipelines → "Run pipeline" Button → Run
```

**Option 2: Leerer Commit**
```bash
git commit --allow-empty -m "ci: trigger pipeline"
git push
```

### Einzelne Jobs triggern

Manche Jobs sind `manual` und müssen explizit gestartet werden:

```
GitLab → CI/CD → Pipelines → [Pipeline auswählen] → Job mit ▶️ klicken
```

**Wichtige manuelle Jobs:**

| Job | Funktion |
|-----|----------|
| `gcp-vm-start` | GCP Runner VM starten |
| `gcp-vm-stop` | GCP Runner VM stoppen |
| `benchmark-*` | Runner Performance testen |

---

## 6. Deployment

### Option A: Lokales Kubernetes (Docker Desktop)

**Voraussetzung:** Kubernetes in Docker Desktop aktiviert.

```bash
# Namespace erstellen
kubectl create namespace clarissa

# Deployment anwenden
kubectl apply -f k8s/deployment.yaml -n clarissa

# Status prüfen
kubectl get pods -n clarissa

# Logs ansehen
kubectl logs -f deployment/clarissa -n clarissa
```

### Option B: GCP Kubernetes (K3s)

**Voraussetzung:** GCP VM läuft (siehe [Runner Management](runner-management.md))

```bash
# 1. GCP VM starten (via GitLab oder CLI)
gcloud compute instances start gitlab-runner --zone=europe-west3-a

# 2. SSH auf die VM
gcloud compute ssh gitlab-runner --zone=europe-west3-a

# 3. Auf der VM: Deployment anwenden
sudo kubectl apply -f /path/to/deployment.yaml -n clarissa

# 4. Status prüfen
sudo kubectl get pods -n clarissa
```

### Option C: Via GitLab CI/CD (automatisch)

Pushe auf `main` Branch → Pipeline deployt automatisch.

```bash
git checkout main
git merge feature/my-feature
git push origin main
# → Pipeline startet → Deployment erfolgt automatisch
```

---

## 7. Verifizieren

### Lokale Installation prüfen

```bash
# CLI funktioniert?
clarissa --version

# Tests grün?
pytest --tb=short

# Import funktioniert?
python -c "import clarissa; print('OK')"
```

### Docker prüfen

```bash
# Container läuft?
docker ps | grep clarissa

# Logs OK?
docker logs clarissa
```

### Kubernetes prüfen

```bash
# Pod läuft?
kubectl get pods -n clarissa
# STATUS sollte "Running" sein

# Logs OK?
kubectl logs -f deployment/clarissa -n clarissa

# Service erreichbar?
kubectl port-forward svc/clarissa 8080:80 -n clarissa
# Dann: http://localhost:8080
```

### Pipeline prüfen

1. Geh zu: https://gitlab.com/wolfram_laube/blauweiss_llc/irena/-/pipelines
2. Letzte Pipeline sollte grün ✅ sein
3. Bei Fehlern: Klick auf den roten Job → Logs lesen

---

## Troubleshooting

### "clarissa: command not found"

```bash
# Virtual Environment aktiviert?
source venv/bin/activate

# Oder neu installieren
pip install -e .
```

### "docker: command not found"

Docker Desktop installieren und starten.

### "kubectl: connection refused"

```bash
# Docker Desktop K8s aktiviert?
# Settings → Kubernetes → Enable Kubernetes ✓

# Context richtig?
kubectl config use-context docker-desktop
```

### Pipeline failed

1. Klick auf den roten Job
2. Lies die Logs
3. Häufige Ursachen:
   - Syntax-Fehler im Code
   - Fehlende Dependencies
   - Tests schlagen fehl

### GCP VM startet nicht

```bash
# Rechte prüfen
gcloud auth list

# VM Status
gcloud compute instances describe gitlab-runner --zone=europe-west3-a
```

---

## Nächste Schritte

| Was du tun willst | Wo nachlesen |
|-------------------|--------------|
| Code beitragen | [Contributing Guide](contributing.md) |
| Workflow verstehen | [Interactive Slides](guides/contributing/index.html) |
| Architektur verstehen | [Architecture Overview](architecture/README.md) |
| CI/CD verstehen | [CI Guide](ci/README.md) |
| Runner verwalten | [Runner Management](runner-management.md) |

---

## Hilfe bekommen

- **Fragen?** → Issue erstellen auf GitLab
- **Bug gefunden?** → Issue mit Label `bug`
- **Feature-Idee?** → Issue mit Label `enhancement`

---

*Letzte Aktualisierung: Januar 2026*
