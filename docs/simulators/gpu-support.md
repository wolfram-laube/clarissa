# GPU Support for Kubernetes Simulation Jobs

This document covers GPU acceleration for reservoir simulation workloads
in Kubernetes. GPU support enables faster simulations for large models.

## Current Status

| Feature | Status | Notes |
|---------|--------|-------|
| CPU Jobs | ✅ Production | Fully supported |
| NVIDIA GPU | 🔜 Planned | Requires GPU nodes |
| AMD GPU | 📋 Future | ROCm support TBD |

## Prerequisites

### Cluster Requirements

1. **GPU Nodes**: At least one node with NVIDIA GPU
2. **NVIDIA Device Plugin**: Kubernetes plugin for GPU scheduling
3. **NVIDIA Drivers**: Installed on GPU nodes

```bash
# Check GPU availability in cluster
kubectl get nodes -o json | jq '.items[].status.allocatable["nvidia.com/gpu"]'
```

### OPM Flow GPU Support

OPM Flow supports GPU acceleration via:
- **cuSPARSE**: For sparse matrix operations
- **CUDA**: For linear solver acceleration

> **Note**: GPU-enabled OPM Flow requires a different Docker image build.

## GPU-Enabled Job Manifest

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: opm-flow-gpu-simulation
  labels:
    app.kubernetes.io/name: opm-flow
    app.kubernetes.io/component: simulator
    accelerator: nvidia-gpu
spec:
  backoffLimit: 2
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: opm-flow
          # GPU-enabled image (when available)
          image: registry.gitlab.com/wolfram_laube/blauweiss_llc/irena/opm-flow-gpu:v1.0.0
          command: ["flow"]
          args: 
            - "data/CASE.DATA"
            - "--output-dir=output/"
            - "--use-gpu=true"
          resources:
            requests:
              memory: "8Gi"
              cpu: "2"
              nvidia.com/gpu: 1  # Request 1 GPU
            limits:
              memory: "32Gi"
              cpu: "8"
              nvidia.com/gpu: 1  # Limit to 1 GPU
          volumeMounts:
            - name: data
              mountPath: /simulation/data
            - name: output
              mountPath: /simulation/output
      # Ensure scheduling on GPU nodes
      nodeSelector:
        accelerator: nvidia-gpu
      tolerations:
        - key: nvidia.com/gpu
          operator: Exists
          effect: NoSchedule
      volumes:
        - name: data
          configMap:
            name: opm-deck-files
        - name: output
          emptyDir: {}
```

## Building GPU-Enabled Image

### Dockerfile Changes

```dockerfile
# Dockerfile.gpu
FROM nvidia/cuda:12.2-runtime-ubuntu22.04

# Install OPM Flow with GPU support
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:opm/ppa \
    && apt-get update \
    && apt-get install -y \
        libopm-simulators-bin \
        libopm-common-bin \
    && rm -rf /var/lib/apt/lists/*

# GPU-specific environment
ENV CUDA_VISIBLE_DEVICES=0
ENV OPM_USE_GPU=1

WORKDIR /simulation
ENTRYPOINT ["flow"]
```

### CI/CD Pipeline

```yaml
# .gitlab-ci.yml addition
build_opm_gpu_image:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  rules:
    - if: '$CI_COMMIT_TAG =~ /^opm-flow-gpu-v[0-9]+/'
      when: on_success
    - when: never
  script:
    - docker build -f Dockerfile.gpu -t $CI_REGISTRY_IMAGE/opm-flow-gpu:$CI_COMMIT_TAG .
    - docker push $CI_REGISTRY_IMAGE/opm-flow-gpu:$CI_COMMIT_TAG
```

## Performance Considerations

### When to Use GPU

| Model Size | Cells | GPU Benefit | Recommendation |
|------------|-------|-------------|----------------|
| Small | < 100K | Minimal | Use CPU |
| Medium | 100K - 1M | 2-3x faster | Consider GPU |
| Large | > 1M | 5-10x faster | Use GPU |

### GPU Memory Requirements

```
Estimated GPU Memory = Cells × 8 bytes × Variables × 2 (safety factor)

Example: 1M cells, 5 variables
= 1,000,000 × 8 × 5 × 2 = 80 MB

Most simulations fit in 4-8 GB GPU memory.
```

### Cost-Benefit Analysis

| Resource | Cost/Hour | Use Case |
|----------|-----------|----------|
| 4 CPU | $0.10 | Small models, testing |
| 16 CPU | $0.40 | Medium models |
| 1 GPU (T4) | $0.35 | Large models, time-critical |
| 1 GPU (A100) | $2.50 | Very large, production |

## Monitoring GPU Usage

### NVIDIA SMI

```bash
# Check GPU utilization in pod
kubectl exec -it opm-flow-gpu-xyz -- nvidia-smi

# Watch GPU usage
kubectl exec -it opm-flow-gpu-xyz -- watch -n 1 nvidia-smi
```

### Prometheus Metrics

If using DCGM exporter:

```promql
# GPU utilization
DCGM_FI_DEV_GPU_UTIL{pod="opm-flow-gpu-xyz"}

# GPU memory used
DCGM_FI_DEV_FB_USED{pod="opm-flow-gpu-xyz"}
```

## Troubleshooting

### "CUDA out of memory"

```yaml
# Reduce batch size or model complexity
# Or request more GPU memory
resources:
  limits:
    nvidia.com/gpu: 2  # Use 2 GPUs if supported
```

### "No GPU devices found"

```bash
# Check if GPU plugin is installed
kubectl get pods -n kube-system | grep nvidia

# Check node labels
kubectl get nodes --show-labels | grep gpu
```

### Pod Stuck in Pending

```bash
# Check if GPU resources are available
kubectl describe node <gpu-node> | grep -A5 "Allocated resources"

# Check events
kubectl describe pod opm-flow-gpu-xyz | grep -A10 Events
```

## Future Work

1. **Multi-GPU Support**: Distribute simulation across multiple GPUs
2. **GPU Sharing**: Allow multiple small jobs to share one GPU
3. **Spot Instances**: Use preemptible GPU nodes for cost savings
4. **AMD ROCm**: Support for AMD GPUs

## See Also

- [Kubernetes Jobs](k8s-jobs.md) - General K8s deployment
- [OPM Flow Guide](opm-flow.md) - OPM Flow basics
- [NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/overview.html)