# OPM Flow Docker Container

A Docker container for [OPM Flow](https://opm-project.org/), the open-source reservoir simulator from the Open Porous Media initiative.

## Quick Start

### Build the Image

```bash
docker build -t opm-flow:latest .
```

### Check Installation

```bash
docker run --rm opm-flow:latest flow --version
```

## Running Simulations

### Setup

```bash
# Create data and output directories
mkdir -p data output

# Download a test case (SPE1)
wget -P data/ https://raw.githubusercontent.com/OPM/opm-data/master/spe1/SPE1CASE1.DATA
```

### Run a Simulation

```bash
docker run --rm \
  -v $(pwd)/data:/simulation/data \
  -v $(pwd)/output:/simulation/output \
  opm-flow:latest \
  flow data/SPE1CASE1.DATA --output-dir=output/
```

### Interactive Mode

```bash
docker run -it --rm \
  -v $(pwd)/data:/simulation/data \
  -v $(pwd)/output:/simulation/output \
  opm-flow:latest \
  /bin/bash
```

### Parallel Execution with MPI

```bash
docker run --rm \
  -v $(pwd)/data:/simulation/data \
  -v $(pwd)/output:/simulation/output \
  opm-flow:latest \
  mpirun --allow-run-as-root -np 4 flow data/SPE1CASE1.DATA --output-dir=output/
```

## Directory Structure

```
opm-flow-docker/
├── Dockerfile
├── README.md
├── data/           # Place your .DATA deck files here
│   └── SPE1CASE1.DATA
└── output/         # Simulation results will appear here
```

## Common OPM Flow Options

| Option | Description |
|--------|-------------|
| `--output-dir=DIR` | Output directory for results |
| `--enable-vtk-output=true` | Enable VTK output for visualization |
| `--linear-solver=SOLVER` | Choose linear solver |
| `--threads-per-process=N` | Number of threads per MPI process |

## Troubleshooting

### Permission Denied / Failed opening file

If you see `Failed opening file output/...PRT for StreamLog`:

```bash
# Delete and recreate the output directory
sudo rm -rf output
mkdir output

# Then run again
```

### Output files owned by root

Since the container runs as root, output files will be owned by root. To fix:

```bash
sudo chown -R $(whoami):$(whoami) output/
```

## Resources

- [OPM Project Website](https://opm-project.org/)
- [OPM Flow Manual](https://opm-project.org/?page_id=955)
- [OPM GitHub Repository](https://github.com/OPM)
- [Sample Data Files](https://github.com/OPM/opm-data)
