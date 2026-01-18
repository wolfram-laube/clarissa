# ADR-016: GitLab Runner Load Balancing Strategy

## Status
**Accepted** (Implemented 2026-01-17)

!!! success "Implementation Complete"
    All 12 runners configured with load-balancing tags. See `.gitlab/parallel-jobs.yml` for usage examples.

## Context

The CLARISSA CI/CD infrastructure operates 12 self-hosted GitLab runners distributed across 4 machines:

| Machine | Shell | Docker | K8s | Total |
|---------|-------|--------|-----|-------|
| Mac #1 | ✓ | ✓ | ✓ | 3 |
| Mac #2 | ✓ | ✓ | ✓ | 3 |
| Linux Yoga | ✓ | ✓ | ✓ | 3 |
| GCP VM | ✓ | ✓ | ✓ | 3 |
| **Total** | 4 | 4 | 4 | **12** |

**Problem:** Each runner has a unique tag (e.g., `mac-docker`, `gcp-shell`), requiring jobs to explicitly target a specific runner. This creates limitations:

1. **No Load Balancing**: A job tagged `mac-docker` always runs on Mac #1, even if Mac #2's Docker runner is idle
2. **No Parallelization**: Cannot fan-out work across multiple runners of the same type
3. **Single Point of Failure**: If a specific runner is offline, jobs fail instead of falling back
4. **Manual Scheduling**: Pipeline authors must know runner topology

## Decision

Implement a **hierarchical tag system** that enables GitLab's native runner selection to balance load:

### Tag Hierarchy

```
any-runner (12)
├── shell-any (4)
│   ├── mac-group-shell
│   ├── mac2-shell
│   ├── linux-shell
│   └── gcp-shell
├── docker-any (4)
│   ├── mac-docker
│   ├── mac2-docker
│   ├── linux-docker
│   └── gcp-docker
├── k8s-any (4)
│   ├── mac-k8s
│   ├── mac2-k8s
│   ├── linux-k8s
│   └── gcp-k8s
├── mac-any (6)
│   ├── mac-group-shell, mac-docker, mac-k8s
│   └── mac2-shell, mac2-docker, mac2-k8s
├── linux-any (3)
│   └── linux-shell, linux-docker, linux-k8s
└── gcp-any (3)
    └── gcp-shell, gcp-docker, gcp-k8s
```

### Tag Definitions

| Tag | Runners | Use Case |
|-----|---------|----------|
| `any-runner` | 12 | Maximum distribution, any executor |
| `shell-any` | 4 | Shell scripts, native tools |
| `docker-any` | 4 | Container builds, isolated environments |
| `k8s-any` | 4 | Kubernetes deployments, helm charts |
| `mac-any` | 6 | macOS-specific builds |
| `linux-any` | 3 | Linux-specific builds |
| `gcp-any` | 3 | Cloud-native workloads |

### Implementation

Tags are added via GitLab API to existing runners:

```python
# Each runner gets: original_tag + generic_tags
TAG_ADDITIONS = {
    "mac-group-shell": ["shell-any", "mac-any", "any-runner"],
    "mac-docker": ["docker-any", "mac-any", "any-runner"],
    "gcp-k8s": ["k8s-any", "gcp-any", "any-runner"],
    # ... etc for all 12 runners
}
```

No changes required to runner `config.toml` files on individual machines.

## Usage Examples

### Basic Load Balancing

```yaml
# Before: Specific runner
build:
  tags: [mac-docker]  # Always Mac #1

# After: Any available Docker runner
build:
  tags: [docker-any]  # Mac #1, Mac #2, Linux, or GCP
```

### Parallel Fan-Out

```yaml
# Run 8 parallel jobs across 4 shell runners
parallel-test:
  tags: [shell-any]
  parallel: 8
  script:
    - echo "Job $CI_NODE_INDEX of $CI_NODE_TOTAL on $CI_RUNNER_DESCRIPTION"
```

### Matrix Build

```yaml
# Build across all executor types
matrix-build:
  parallel:
    matrix:
      - EXECUTOR: shell
        RUNNER_TAG: shell-any
      - EXECUTOR: docker
        RUNNER_TAG: docker-any
      - EXECUTOR: k8s
        RUNNER_TAG: k8s-any
  tags: ["${RUNNER_TAG}"]
```

### Platform-Specific with Fallback

```yaml
# Prefer Mac, but allow any runner
macos-build:
  tags: [mac-any]  # 6 runners available
```

## Alternatives Considered

### 1. GitLab Runner Autoscaling
- **Rejected**: Adds cloud cost complexity
- Our static 12-runner pool is sufficient for current workloads

### 2. Kubernetes-Only Infrastructure
- **Rejected**: Loses bare-metal performance for shell executors
- Mac-specific builds require macOS hosts

### 3. External Load Balancer (HAProxy, Traefik)
- **Rejected**: GitLab handles runner selection natively
- No need for additional infrastructure

### 4. Round-Robin via CI Variables
- **Rejected**: Complex, fragile, no built-in retry
- Tags are the idiomatic GitLab solution

## Consequences

### Positive

- **Automatic Load Distribution**: GitLab assigns jobs to first available runner
- **Fault Tolerance**: If one runner is offline, jobs run on others
- **Scalability**: Add more runners with same generic tags
- **Backward Compatible**: Original specific tags still work
- **No Infrastructure Changes**: Pure configuration via API

### Negative

- **Non-Deterministic**: Same job may run on different machines
- **Debugging Complexity**: Logs spread across runners
- **Resource Contention**: Multiple jobs may land on same runner

### Mitigations

| Risk | Mitigation |
|------|------------|
| Non-deterministic execution | Log `$CI_RUNNER_DESCRIPTION` in all jobs |
| Resource contention | Use `resource_group` for heavy jobs |
| Debug difficulty | Centralize logs via artifacts or external system |

## Verification

```yaml
# Test load distribution
loadbalancing-test:
  tags: [any-runner]
  parallel: 12
  script:
    - echo "Runner: $CI_RUNNER_DESCRIPTION"
```

Expected: Jobs distributed across all 4 machines.

## Future Extensions

1. **Weighted Distribution**: Prefer faster runners via GitLab Runner `limit` setting
2. **Geographic Tags**: `eu-runner`, `us-runner` for latency optimization
3. **Capability Tags**: `gpu-any`, `high-memory` for specialized workloads
4. **Cost Tags**: `spot-any`, `on-demand` for cloud cost optimization

## References

- [GitLab Runner Tags](https://docs.gitlab.com/ee/ci/runners/configure_runners.html#use-tags-to-control-which-jobs-a-runner-can-run)
- [Parallel Jobs](https://docs.gitlab.com/ee/ci/yaml/#parallel)
- [ADR-015: LLM CI Notifications](ADR-015-llm-ci-notifications.md) - Related CI infrastructure
- [BENCHMARK_HOWTO.md](../../ci/BENCHMARK_HOWTO.md) - Runner benchmark reference

---

*Accepted: 2026-01-17*
*Author: Wolfram Laube*
