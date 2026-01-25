# Kubernetes Simulation Jobs

CLARISSA uses Kubernetes Jobs for production-scale simulation workloads.
Jobs are the appropriate primitive for batch processing (not Deployments).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                      Job                             │   │
│  │  ┌─────────────────────────────────────────────┐    │   │
│  │  │              Pod                             │    │   │
│  │  │  ┌───────────────────────────────────────┐  │    │   │
│  │  │  │        opm-flow:v1.0.0                │  │    │   │
│  │  │  │  ┌─────────┐     ┌─────────────────┐  │  │    │   │
│  │  │  │  │  /data  │     │    /output      │  │  │    │   │
│  │  │  │  │ConfigMap│     │   EmptyDir/PVC  │  │  │    │   │
│  │  │  │  └─────────┘     └─────────────────┘  │  │    │   │
│  │  │  └───────────────────────────────────────┘  │    │   │
│  │  └─────────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Apply Job Manifest

```bash
# Using Kustomize
kubectl apply -k k8s/overlays/dev/

# Or raw manifest
kubectl apply -f k8s/base/opm-flow/job.yaml
```

### Monitor Progress

```bash
# Watch job status
kubectl get jobs -w

# View logs
kubectl logs job/opm-flow-simulation -f

# Get pod details
kubectl describe pod -l job-name=opm-flow-simulation
```

## Manifest Structure

```
k8s/
├── base/
│   ├── kustomization.yaml
│   └── opm-flow/
│       ├── job.yaml          # Job template
│       ├── configmap.yaml    # Deck files (optional)
│       └── pvc.yaml          # Persistent storage (optional)
└── overlays/
    ├── dev/
    │   ├── kustomization.yaml
    │   └── patches/
    │       └── resource-limits.yaml
    └── prod/
        ├── kustomization.yaml
        └── patches/
            └── resource-limits.yaml
```

## Job Configuration

### Basic Job (`k8s/base/opm-flow/job.yaml`)

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
          image: registry.gitlab.com/wolfram_laube/blauweiss_llc/clarissa/opm-flow:v1.0.0
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

### Deck Files via ConfigMap

```yaml
# k8s/base/opm-flow/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: opm-deck-files
data:
  CASE.DATA: |
    RUNSPEC
    TITLE
    Test Simulation
    
    DIMENS
    10 10 3 /
    
    -- ... rest of deck ...
```

### Persistent Output via PVC

```yaml
# k8s/base/opm-flow/pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: opm-output
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

Then reference in job:

```yaml
volumes:
  - name: output
    persistentVolumeClaim:
      claimName: opm-output
```

## Environment Overlays

### Development (`k8s/overlays/dev/`)

```yaml
# kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namespace: clarissa-dev
resources:
  - ../../base/opm-flow

patches:
  - path: patches/resource-limits.yaml
```

```yaml
# patches/resource-limits.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: opm-flow-simulation
spec:
  template:
    spec:
      containers:
        - name: opm-flow
          resources:
            limits:
              memory: "4Gi"
              cpu: "2"
```

### Production (`k8s/overlays/prod/`)

```yaml
# patches/resource-limits.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: opm-flow-simulation
spec:
  template:
    spec:
      containers:
        - name: opm-flow
          resources:
            requests:
              memory: "8Gi"
              cpu: "4"
            limits:
              memory: "32Gi"
              cpu: "16"
```

## Usage Patterns

### One-off Simulation

```bash
# Create job with unique name
kubectl create job opm-sim-$(date +%s) \
  --image=registry.gitlab.com/.../opm-flow:v1.0.0 \
  -- flow /data/CASE.DATA
```

### Parameterized Jobs

```bash
# Using envsubst
export CASE_NAME="SPE1"
export IMAGE_TAG="v1.0.0"
envsubst < job-template.yaml | kubectl apply -f -
```

### Batch Processing

```python
# Python client
from kubernetes import client, config

config.load_kube_config()
batch_v1 = client.BatchV1Api()

for case in ["CASE1", "CASE2", "CASE3"]:
    job = create_job_manifest(case)
    batch_v1.create_namespaced_job("clarissa", job)
```

## Retrieving Results

### From EmptyDir (ephemeral)

```bash
# Copy from running pod
kubectl cp opm-flow-simulation-xyz:/simulation/output ./results/

# Or exec into pod
kubectl exec -it opm-flow-simulation-xyz -- ls /simulation/output
```

### From PVC (persistent)

```bash
# Create a helper pod to access PVC
kubectl run pvc-reader --image=busybox --restart=Never \
  --overrides='{"spec":{"volumes":[{"name":"data","persistentVolumeClaim":{"claimName":"opm-output"}}],"containers":[{"name":"reader","image":"busybox","volumeMounts":[{"name":"data","mountPath":"/data"}]}]}}'

# Copy files
kubectl cp pvc-reader:/data ./results/
```

### To Object Storage (S3/GCS)

Add a sidecar or post-job to upload:

```yaml
initContainers:
  - name: upload-results
    image: amazon/aws-cli
    command: ["aws", "s3", "sync", "/output", "s3://bucket/results/"]
    volumeMounts:
      - name: output
        mountPath: /output
```

## Monitoring

### Job Status

```bash
# List jobs
kubectl get jobs -l app.kubernetes.io/part-of=clarissa

# Describe specific job
kubectl describe job opm-flow-simulation

# Get completion status
kubectl get job opm-flow-simulation -o jsonpath='{.status.conditions[0].type}'
```

### Resource Usage

```bash
# Pod metrics (requires metrics-server)
kubectl top pod -l job-name=opm-flow-simulation
```

## Troubleshooting

### Job Stuck in Pending

```bash
# Check events
kubectl describe pod -l job-name=opm-flow-simulation

# Common causes:
# - Insufficient resources: Adjust requests/limits
# - Image pull error: Check registry credentials
# - PVC not bound: Check storage class
```

### Simulation Crashes

```bash
# Check logs
kubectl logs job/opm-flow-simulation

# Check exit code
kubectl get pod -l job-name=opm-flow-simulation -o jsonpath='{.items[0].status.containerStatuses[0].state.terminated.exitCode}'
```

### Cleanup Failed Jobs

```bash
# Delete completed jobs older than 1 hour
kubectl delete jobs --field-selector status.successful=1

# Delete all jobs
kubectl delete jobs -l app.kubernetes.io/part-of=clarissa
```

## Best Practices

1. **Always use semver tags** in production (`v1.0.0`, not `latest`)
2. **Set resource limits** to prevent noisy neighbor issues
3. **Use PVCs** for results you need to keep
4. **Add labels** for easy filtering and cleanup
5. **Set backoffLimit** to prevent infinite retries

## See Also

- [OPM Flow Guide](opm-flow.md) - Local Docker usage
- [Adapter Contract](adapter-contract.md) - Programmatic interface
- ADR-012 - Container registry and K8s strategy
