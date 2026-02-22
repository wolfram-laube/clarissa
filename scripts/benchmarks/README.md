# SPE Benchmark Runner

Run all 4 SPE benchmarks through OPM Flow on the simulation VM and convert
results to JSON format compatible with `spe-viewer.html`.

## Quick Start (on Nordic VM)

```bash
# SSH to the OPM Flow machine
ssh doug@178.156.251.191

# Pull latest scripts
cd ~/projects && git -C decks/opm-data pull 2>/dev/null
cd ~
git clone https://gitlab.com/wolfram_laube/blauweiss_llc/projects/clarissa.git clarissa-scripts 2>/dev/null || git -C clarissa-scripts pull
cd clarissa-scripts/scripts/benchmarks

# Run all benchmarks (SPE1 takes ~10s, SPE9 ~5min, SPE10 M2 ~30-120min)
chmod +x run_benchmarks.sh
./run_benchmarks.sh           # All benchmarks
./run_benchmarks.sh spe1      # Just SPE1 (quick test)
./run_benchmarks.sh spe10m2   # Just SPE10 M2 (long)
```

## Files

| File | Description |
|------|-------------|
| `run_benchmarks.sh` | Main runner — calls OPM Flow for each deck |
| `opm_to_viewer_json.py` | Converts OPM `.UNRST`/`.SMSPEC` → viewer JSON |
| `merge_results.py` | Merges OPM + MRST results into unified JSON |
| `run_mrst_benchmarks.m` | Octave/MATLAB MRST runner (optional) |

## Output

After `run_benchmarks.sh` completes:

```bash
# Copy result JSON to your machine
scp doug@178.156.251.191:~/projects/results/clarissa-benchmarks/spe_benchmarks.json .

# Open viewer (spe-viewer.html loads spe_benchmarks.json automatically)
open spe-viewer.html
```

## SPE10 Model 2 Subsampling

SPE10 M2 has 1.1M cells (60×220×85). The converter subsamples to ~8,400 cells
(20×20×21) using stride (3,11,4) to keep the JSON under 10MB for browser rendering.
Full-resolution cell data is preserved in the `.UNRST` file for offline analysis.

## Benchmarks

| Model | Cells | Est. Runtime | Notes |
|-------|-------|-------------|-------|
| SPE1 | 300 | ~10s | Gas injection, 10 years |
| SPE5 | 147 | ~5s | WAG miscible flood, 20 years |
| SPE9 | 9,000 | ~5min | 26 wells, corner-point |
| SPE10 M1 | 2,000 | ~30s | 2D cross-section |
| SPE10 M2 | 1,122,000 | ~30-120min | Full 3D heterogeneous |

## Prerequisites

- OPM Flow 2025.10 (`/usr/bin/flow`)
- Python 3 with `resdata` and `numpy` (`~/venv`)
- Decks in `~/projects/decks/opm-data/`
