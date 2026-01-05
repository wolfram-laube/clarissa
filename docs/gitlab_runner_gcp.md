# GitLab Runner auf GCP - Setup Guide

## 1. GCP VM erstellen

```bash
# Via gcloud CLI
gcloud compute instances create gitlab-runner \
  --project=myk8sproject-207017 \
  --zone=europe-west1-b \
  --machine-type=e2-small \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=30GB \
  --tags=gitlab-runner \
  --metadata=startup-script='#!/bin/bash
    apt-get update
    apt-get install -y docker.io
    systemctl enable docker
    systemctl start docker
    usermod -aG docker $USER
  '
```

**Geschätzte Kosten:** ~$13/Monat (e2-small) oder ~$6/Monat (e2-micro)

## 2. GitLab Runner installieren

```bash
# SSH auf die VM
gcloud compute ssh gitlab-runner --zone=europe-west1-b

# Runner installieren
curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh" | sudo bash
sudo apt-get install gitlab-runner

# Docker installieren (falls nicht via startup-script)
sudo apt-get install -y docker.io
sudo usermod -aG docker gitlab-runner
```

## 3. Runner registrieren

```bash
# Registration Token von GitLab holen:
# Settings → CI/CD → Runners → New project runner

sudo gitlab-runner register \
  --non-interactive \
  --url "https://gitlab.com/" \
  --token "PROJECT_RUNNER_TOKEN" \
  --executor "docker" \
  --docker-image "python:3.11-slim" \
  --description "gcp-runner-clarissa" \
  --tag-list "gcp,docker" \
  --run-untagged="true"
```

## 4. Runner konfigurieren

```bash
# /etc/gitlab-runner/config.toml
sudo nano /etc/gitlab-runner/config.toml
```

```toml
concurrent = 4
check_interval = 0

[[runners]]
  name = "gcp-runner-clarissa"
  url = "https://gitlab.com/"
  token = "PROJECT_TOKEN"
  executor = "docker"
  [runners.docker]
    image = "python:3.11-slim"
    privileged = true  # Für Docker-in-Docker
    volumes = ["/cache", "/var/run/docker.sock:/var/run/docker.sock"]
    shm_size = 0
```

## 5. Runner starten

```bash
sudo gitlab-runner start
sudo gitlab-runner status

# Logs checken
sudo journalctl -u gitlab-runner -f
```

## 6. GitLab konfigurieren

In `.gitlab-ci.yml` optional Tags nutzen:

```yaml
tests:
  tags:
    - gcp  # Nur auf GCP Runner ausführen
  script:
    - pytest
```

Oder `run-untagged: true` lassen für alle Jobs.

## Vorteile

- ✅ Unbegrenzte CI-Minuten
- ✅ Schnellere Builds (keine Warteschlange)
- ✅ Docker-in-Docker für Container-Builds
- ✅ Persistenter Cache
- ✅ Volle Kontrolle über Umgebung
- ✅ ~$6-13/Monat statt $29/User

## Wartung

```bash
# Runner updaten
sudo apt-get update && sudo apt-get upgrade gitlab-runner

# Docker cleanup (wöchentlich)
docker system prune -af

# Logs rotieren - passiert automatisch via journald
```