# Developer Onboarding: GitLab Runner Infrastructure

> **Ref:** ADR-015 (Hierarchical Tag System), Issue #155

## Overview

Das CLARISSA-Projekt nutzt einen verteilten Runner-Pool mit 12 Runnern auf 4 Plattformen:

| Plattform | Shell | Docker | K8s | Lokation |
|-----------|:-----:|:------:|:---:|----------|
| Mac #1 | ✅ | ✅ | ✅ | Schärding |
| Mac #2 | ✅ | ✅ | ✅ | Schärding |
| Linux Yoga | ✅ | ✅ | ✅ | Schärding |
| GCP VM | ✅ | ✅ | ✅ | Helsinki (europe-north2) |

**Vorteile:**
- **Load Balancing:** Jobs verteilen sich automatisch
- **Fallback:** Bei Offline-Runner übernimmt der nächste
- **Geo-Redundanz:** Schärding + Cloud

---

## Option A: Nur GitLab-Zugang (empfohlen für Start)

Nutze den bestehenden Runner-Pool ohne eigene Hardware.

### Schritte

1. **GitLab-Zugang erhalten** (Developer oder Maintainer Role)
2. **Fertig!** Deine Jobs laufen auf dem Pool

### Pipeline-Nutzung

```yaml
# Beliebiger Shell-Runner (4 verfügbar)
test:
  tags: [shell-any]
  script:
    - pytest

# Beliebiger Docker-Runner (4 verfügbar)
build:
  tags: [docker-any]
  image: python:3.11
  script:
    - pip install -e .

# Beliebiger K8s-Runner (4 verfügbar)
deploy:
  tags: [k8s-any]
  image: bitnami/kubectl
  script:
    - kubectl apply -f manifests/
```

---

## Option B: Eigene Runner hinzufügen

Für volle Integration mit eigener Hardware.

### Voraussetzungen

- macOS, Linux, oder Windows mit Docker/K8s
- GitLab Runner installiert
- Netzwerkzugang zu GitLab.com

### 1. GitLab Runner installieren

**macOS:**
```bash
brew install gitlab-runner
brew services start gitlab-runner
```

**Linux (Debian/Ubuntu):**
```bash
curl -L https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh | sudo bash
sudo apt install gitlab-runner
sudo gitlab-runner start
```

**Linux (mit Docker):**
```bash
docker run -d --name gitlab-runner --restart always   -v /srv/gitlab-runner/config:/etc/gitlab-runner   -v /var/run/docker.sock:/var/run/docker.sock   gitlab/gitlab-runner:latest
```

### 2. Runner registrieren

Hole dir ein Runner-Token vom Projekt: **Settings → CI/CD → Runners → New project runner**

#### Shell Runner
```bash
gitlab-runner register   --url https://gitlab.com   --token <RUNNER_TOKEN>   --description "YourName Shell Runner"   --tag-list "yourname-shell,shell-any,any-runner"   --executor shell
```

#### Docker Runner
```bash
gitlab-runner register   --url https://gitlab.com   --token <RUNNER_TOKEN>   --description "YourName Docker Runner"   --tag-list "yourname-docker,docker-any,any-runner"   --executor docker   --docker-image python:3.11-slim
```

#### Kubernetes Runner
```bash
gitlab-runner register   --url https://gitlab.com   --token <RUNNER_TOKEN>   --description "YourName K8s Runner"   --tag-list "yourname-k8s,k8s-any,any-runner"   --executor kubernetes   --kubernetes-namespace gitlab-runner
```

### 3. K8s-spezifische Konfiguration

```bash
# Namespace erstellen
kubectl create namespace gitlab-runner

# kubeconfig in config.toml eintragen
# Finde [runners.kubernetes] und füge hinzu:
#   config = "/path/to/.kube/config"
#   image = "python:3.11-slim"
```

**config.toml Beispiel:**
```toml
[[runners]]
  name = "YourName K8s Runner"
  executor = "kubernetes"
  [runners.kubernetes]
    host = ""
    config = "/Users/yourname/.kube/config"  # <-- wichtig!
    image = "python:3.11-slim"
    namespace = "gitlab-runner"
```

### 4. Runner neustarten

```bash
# macOS
gitlab-runner restart

# Linux
sudo gitlab-runner restart
```

### 5. Verifizieren

```bash
# Lokal
gitlab-runner verify

# GitLab UI
# Settings → CI/CD → Runners → sollte "Online" zeigen
```

---

## Tag-Hierarchie (ADR-015)

Jeder Runner bekommt hierarchische Tags für automatisches Fallback:

```
any-runner (alle 12+)
├── shell-any (alle Shell)
├── docker-any (alle Docker)
├── k8s-any (alle K8s)
├── mac-any (alle macOS)
├── linux-any (alle Linux)
└── gcp-any (alle GCP)
```

### Tag-Schema für neue Runner

| Dein Tag | + Generische Tags |
|----------|-------------------|
| `alice-shell` | `shell-any, any-runner` |
| `alice-docker` | `docker-any, any-runner` |
| `alice-k8s` | `k8s-any, any-runner` |

**Optional:** Plattform-Tags hinzufügen:
- macOS: `+ mac-any`
- Linux: `+ linux-any`

---

## Troubleshooting

### Runner nimmt keine Jobs an

```bash
# Status prüfen
gitlab-runner status

# Logs anschauen
gitlab-runner --debug run
```

### K8s Job failed: namespace not found

```bash
kubectl create namespace gitlab-runner
```

### K8s Job failed: kubeconfig error

In `config.toml` unter `[runners.kubernetes]`:
```toml
config = "/absolute/path/to/.kube/config"
```

### Docker Job failed: permission denied

```bash
# Linux: User zur docker-Gruppe hinzufügen
sudo usermod -aG docker gitlab-runner
sudo gitlab-runner restart
```

---

## Kontakt

Bei Fragen: Wolfram Laube (wolfram@blauweiss-edv.at)

---

*Letzte Aktualisierung: 2026-05-25 (Issue #155)*
