# ADR-012 — Container Registry and Kubernetes Deployment Strategy

## Status
Proposed

## Context

With ADR-011 implemented, CLARISSA now has a Dockerized OPM Flow simulator adapter.
Currently, the Docker image is built locally via `docker build` and referenced by
the `OPMFlowAdapter` at runtime. This approach has limitations:

1. **No CI/CD integration**: Images are not built or tested automatically.
2. **No versioning**: No tagged images in a registry; developers must build locally.
3. **No production path**: No mechanism to deploy simulations to shared infrastructure.
4. **Reproducibility gaps**: Local builds may differ across developer machines.

As CLARISSA matures, we need:
- Automated image builds on every merge to `main`
- A container registry for versioned, immutable images
- A clear path to run simulations on Kubernetes (batch jobs initially)

This decision focuses on the minimal viable infrastructure for container-based
simulation execution, deferring advanced orchestration (Helm, operators) until
concrete requirements emerge.

## Decision

### 1. Container Registry: GitLab Container Registry

Use GitLab's built-in Container Registry at `registry.gitlab.com/wolfram_laube/blauweiss_llc/irena`.

**Image naming convention:**
```
registry.gitlab.com/wolfram_laube/blauweiss_llc/irena/opm-flow:<tag>
```

**Tagging strategy:**
- `latest` — most recent build from `main` (mutable, convenience only)
- `<commit-sha>` — immutable, traceable to exact code version
- `v<semver>` — release tags (when applicable)

### 2. CI Pipeline: Automated Image Build

Add a new `build` stage to `.gitlab-ci.yml`:

```yaml
stages:
  - build      # NEW
  - test
  - classify
  - automation
  - deploy

build_opm_image:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      changes:
        - src/clarissa/simulators/opm/**/*
      when: on_success
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
      changes:
        - src/clarissa/simulators/opm/**/*
      when: on_success
    - when: never
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $CI_REGISTRY_IMAGE/opm-flow:$CI_COMMIT_SHORT_SHA src/clarissa/simulators/opm/
    - docker push $CI_REGISTRY_IMAGE/opm-flow:$CI_COMMIT_SHORT_SHA
    - |
      if [ "$CI_COMMIT_BRANCH" == "main" ]; then
        docker tag $CI_REGISTRY_IMAGE/opm-flow:$CI_COMMIT_SHORT_SHA $CI_REGISTRY_IMAGE/opm-flow:latest
        docker push $CI_REGISTRY_IMAGE/opm-flow:latest
      fi
```

### 3. Kubernetes: Simple Job Manifests with Kustomize

Place Kubernetes manifests under `k8s/` using Kustomize for environment flexibility:

```
k8s/
├── base/
│   ├── kustomization.yaml
│   └── opm-flow/
│       ├── job.yaml
│       ├── configmap.yaml    # Optional: deck file mounting
│       └── pvc.yaml          # Optional: persistent storage for results
└── overlays/
    └── dev/
        ├── kustomization.yaml
        └── patches/
            └── resource-limits.yaml
```

**Job template** (`k8s/base/opm-flow/job.yaml`):
```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: opm-flow-simulation
  labels:
    app.kubernetes.io/name: opm-flow
    app.kubernetes.io/component: simulator
    app.kubernetes.io/part-of: clarissa
spec:
  backoffLimit: 2
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: opm-flow
          image: registry.gitlab.com/wolfram_laube/blauweiss_llc/irena/opm-flow:latest
          command: ["flow"]
          args: ["data/CASE.DATA", "--output-dir=output/"]
          volumeMounts:
            - name: data
              mountPath: /simulation/data
            - name: output
              mountPath: /simulation/output
          resources:
            requests:
              memory: "2Gi"
              cpu: "1"
            limits:
              memory: "8Gi"
              cpu: "4"
      volumes:
        - name: data
          configMap:
            name: opm-deck-files
        - name: output
          emptyDir: {}
```

### 4. OPMFlowAdapter Update

Update `OPMFlowAdapter` to use the registry image by default:

```python
DEFAULT_IMAGE = "registry.gitlab.com/wolfram_laube/blauweiss_llc/irena/opm-flow:latest"
```

Allow override via environment variable `CLARISSA_OPM_IMAGE` for flexibility.

## Rationale

1. **GitLab Registry**: Zero additional infrastructure; integrated with existing CI/CD;
   authentication handled via CI variables.

2. **Minimal CI job**: Only builds when OPM files change; tagged images enable rollback
   and traceability.

3. **Kustomize over Helm**: Simpler for current needs; no templating complexity;
   overlays provide environment differentiation when needed.

4. **Job (not Deployment)**: Reservoir simulations are batch workloads, not long-running
   services. Kubernetes Jobs are the appropriate primitive.

## Consequences

### Positive
- Reproducible builds on every commit to `main`
- Immutable, versioned images in registry
- Clear path from development to K8s execution
- Foundation for future scaling (parallel simulations, GPU nodes)

### Negative
- CI pipeline becomes longer (Docker build adds ~2-5 min)
- Requires Docker-in-Docker or Kaniko (slight complexity)
- K8s manifests add maintenance surface

### Neutral / Open
- Helm adoption deferred until multi-environment or complex parametrization needed
- GPU support for accelerated solvers not yet addressed
- Result collection from K8s jobs (S3, PVC, etc.) to be decided per use case

## Alternatives Considered

### GitHub Container Registry / Docker Hub
**Rejected**: Would require additional credentials management; GitLab Registry is
already available and integrated.

### Helm from the start
**Rejected**: Premature complexity. Kustomize provides sufficient flexibility for
current single-environment needs. Helm can be adopted later if templating or
chart distribution becomes necessary.

### Kaniko instead of Docker-in-Docker
**Considered but deferred**: Kaniko is more secure (no privileged container) but
adds complexity. DinD is acceptable for now; can migrate to Kaniko if security
requirements tighten.

## Implementation Notes

- CI variables `CI_REGISTRY`, `CI_REGISTRY_USER`, `CI_REGISTRY_PASSWORD` are
  automatically available in GitLab CI
- Test image build in MR pipeline before merge
- Update `OPMFlowAdapter` default image after first successful push
- Document K8s job execution in `docs/simulators/`

## Related ADRs
- ADR-001 — Physics-Centric, Simulator-in-the-Loop Architecture
- ADR-011 — OPM Flow Simulator Integration
