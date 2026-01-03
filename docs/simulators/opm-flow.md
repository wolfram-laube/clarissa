# OPM Flow Integration Guide

OPM Flow is CLARISSA's primary open-source reservoir simulator backend.
It provides full ECLIPSE syntax support without licensing requirements.

## Quick Start

### Local Development

```bash
# Build the Docker image
cd src/clarissa/simulators/opm
docker build -t opm-flow:latest .

# Run a simulation
docker run --rm \
  -v $(pwd)/cases:/simulation/data \
  -v $(pwd)/output:/simulation/output \
  opm-flow:latest \
  flow data/SPE1.DATA --output-dir=output/
```

### Using the Adapter

```python
from clarissa.simulators.opm import OPMFlowAdapter

# Create adapter (uses registry image by default)
adapter = OPMFlowAdapter()

# Run simulation
result = adapter.run("/path/to/CASE.DATA")

if result["converged"]:
    print(f"Success! Runtime: {result['metrics']['runtime_seconds']}s")
else:
    print(f"Failed: {result['errors']}")
```

## Docker Image

### Registry Location

```
registry.gitlab.com/wolfram_laube/blauweiss_llc/irena/opm-flow
```

### Available Tags

| Tag | Use Case | Stability |
|-----|----------|-----------|
| `latest` | Development | Updated on every main build |
| `v1.0.0` | Production | Semantic versioned, stable |
| `abc123de` | Debugging | Specific commit SHA |

### Image Contents

- **Base**: Ubuntu 24.04
- **OPM Flow**: Latest stable release
- **Entrypoint**: `/usr/bin/flow`
- **Working Dir**: `/simulation`

### Volume Mounts

| Container Path | Purpose |
|----------------|---------|
| `/simulation/data` | Input deck files |
| `/simulation/output` | Simulation results |

## Configuration

### Environment Variables

```python
# Override default image
import os
os.environ["CLARISSA_OPM_IMAGE"] = "opm-flow:v1.0.0"

# Then create adapter
adapter = OPMFlowAdapter()  # Uses v1.0.0
```

### Adapter Parameters

```python
adapter = OPMFlowAdapter(
    image="opm-flow:v1.0.0",     # Docker image
    timeout=3600,                 # Max runtime (seconds)
    work_dir=Path("/tmp/sim"),    # Working directory
    docker_options={              # Extra docker run options
        "memory": "8g",
        "cpus": "4",
    }
)
```

## Supported ECLIPSE Keywords

OPM Flow supports most ECLIPSE 100 keywords. Key categories:

### Fully Supported ✅

- **RUNSPEC**: TITLE, DIMENS, OIL, WATER, GAS, DISGAS, VAPOIL
- **GRID**: DX, DY, DZ, PERMX, PERMY, PERMZ, PORO, TOPS
- **PROPS**: PVTO, PVTW, PVDG, ROCK, DENSITY, SWOF, SGOF
- **REGIONS**: SATNUM, PVTNUM, FIPNUM
- **SOLUTION**: EQUIL, DATUM, RSVD, RVVD
- **SCHEDULE**: WELSPECS, COMPDAT, WCONPROD, WCONINJE, DATES, TSTEP

### Partial Support ⚠️

- **Aquifers**: AQUFETP (limited), AQUANCON
- **LGR**: Local grid refinement (basic)
- **Thermal**: Limited black-oil thermal

### Not Supported ❌

- **Compositional**: Full compositional (use OPM compositional branch)
- **Polymer**: PLYVISC, PLYADS
- **Surfactant**: SURFST, SURFADS

See [OPM Manual](https://opm-project.org/?page_id=955) for complete keyword reference.

## Troubleshooting

### Common Errors

**"Cannot connect to Docker daemon"**
```bash
# Ensure Docker is running
sudo systemctl start docker

# Add user to docker group
sudo usermod -aG docker $USER
```

**"Image not found"**
```bash
# Pull from registry
docker pull registry.gitlab.com/wolfram_laube/blauweiss_llc/irena/opm-flow:latest

# Or build locally
docker build -t opm-flow:latest src/clarissa/simulators/opm/
```

**"Simulation timed out"**
```python
# Increase timeout
adapter = OPMFlowAdapter(timeout=7200)  # 2 hours
```

**"Permission denied on output"**
```bash
# Fix output directory permissions
chmod 777 output/
```

### Debugging

Enable verbose output:

```python
adapter = OPMFlowAdapter()
result = adapter.run(case, verbose=True)

# Check the log artifact
if "log" in result.get("artifacts", {}):
    with open(result["artifacts"]["log"]) as f:
        print(f.read())
```

## Performance Tuning

### Memory

```python
adapter = OPMFlowAdapter(
    docker_options={"memory": "16g"}
)
```

### Parallelization

```bash
# OPM Flow supports MPI parallelization
docker run ... opm-flow:latest \
  mpirun -np 4 flow CASE.DATA
```

### GPU (Future)

GPU support is planned. See Issue #27 for status.

## See Also

- [Adapter Contract](adapter-contract.md) - Interface specification
- [Kubernetes Jobs](k8s-jobs.md) - Production deployment
- ADR-011 - Integration decision
- ADR-012 - Container registry strategy