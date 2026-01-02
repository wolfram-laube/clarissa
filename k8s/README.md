# Kubernetes Manifests

Kustomize-based Kubernetes manifests for CLARISSA simulation jobs.

## Structure

```
k8s/
├── base/                    # Base manifests
│   ├── kustomization.yaml
│   └── opm-flow/
│       ├── job.yaml         # Batch Job template
│       └── configmap.yaml   # Example deck ConfigMap
└── overlays/
    └── dev/                 # Development overlay
        ├── kustomization.yaml
        └── patches/
            └── resource-limits.yaml
```

## Usage

### Preview manifests
```bash
kubectl kustomize k8s/overlays/dev
```

### Deploy to dev
```bash
kubectl apply -k k8s/overlays/dev
```

### Run with custom deck
```bash
# Create ConfigMap from local file
kubectl create configmap opm-flow-deck --from-file=simulation.DATA=./my-model.DATA

# Apply job
kubectl apply -k k8s/overlays/dev
```

### Check job status
```bash
kubectl get jobs -l app.kubernetes.io/name=opm-flow
kubectl logs job/dev-opm-flow-simulation
```

## Adding Production Overlay

Create `k8s/overlays/prod/` with:
- Higher resource limits
- Node selectors for GPU nodes
- PersistentVolumeClaims for large datasets

See ADR-012 for deployment strategy details.
