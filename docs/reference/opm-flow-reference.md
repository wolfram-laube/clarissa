# OPM Flow Reservoir Simulation Workspace

This project is a workspace for running OPM Flow reservoir simulations. OPM Flow 2025.10 is installed at `/usr/bin/flow`.

## Directory Structure

```
~/projects/
  decks/              Simulation input decks (.DATA files)
    opm-data/         Reference models from the OPM project (read-only)
    <your-project>/   Create new folders here for custom models
  results/            Simulation output (timestamped, never overwritten)
  notebooks/          Jupyter notebooks for plotting results
```

## Commands

Try the justfile recipes first. If they fail, fall back to the shell functions below.

**Justfile recipes** (work in non-interactive shells):

| Command | Description |
|---------|-------------|
| `just run <DECK.DATA>` | Run a simulation. Output goes to a timestamped folder in `results/`. |
| `just models` | List all `.DATA` files under `decks/`. |
| `just results` | List completed simulation runs. |

Example: `just run ~/projects/decks/opm-data/spe1/SPE1CASE2.DATA`

**Shell functions** (defined in `~/.bashrc`, interactive terminals only):

| Command | Description |
|---------|-------------|
| `runsim <DECK.DATA>` | Run a simulation. Output goes to a timestamped folder in `results/`. |
| `lsmodels` | List all `.DATA` files under `decks/`. |
| `lsresults` | List completed simulation runs sorted by time. |
| `projects` / `decks` / `results` | Quick `cd` aliases. |

## Reference Models (decks/opm-data/)

Do NOT edit these directly. Copy to your own folder first.

| Model | Path | Grid Size | Description |
|-------|------|-----------|-------------|
| SPE1 | `spe1/SPE1CASE2.DATA` | 10x10x3 (300 cells) | Simplest black-oil model. Best starting point. |
| SPE3 | `spe3/SPE3CASE1.DATA` | 9x9x4 (324 cells) | Gas condensate with VAPOIL/DISGAS. |
| SPE5 | `spe5/SPE5CASE1.DATA` | 7x7x3 (147 cells) | Miscible flood with solvent (WAG injection). |
| SPE9 | `spe9/SPE9_CP.DATA` | 24x25x15 (9,000 cells) | Corner-point grid, 26 wells. |
| SPE10 M1 | `spe10model1/SPE10_MODEL1.DATA` | 100x1x20 (2,000 cells) | 2D cross-section upscaling benchmark. |
| SPE10 M2 | `spe10model2/SPE10_MODEL2.DATA` | 60x220x85 (1.1M cells) | Large 3D heterogeneous model. |
| Norne | `norne/NORNE_ATW2013.DATA` | 46x112x22 (113K cells) | Real North Sea field. Full production model. |
| Sleipner | `sleipner/SLEIPNER_ORG.DATA` | 64x118x263 (2M cells) | CO2 storage benchmark. |

SPE1 has 12+ variants in `spe1/` demonstrating features like restart, thermal, 2-phase, ACTNUM, etc.

## OPM Flow Deck File Format

Deck files use Eclipse syntax with sections in this order:

```
RUNSPEC    -- Dimensions, phases (OIL/GAS/WATER), units, start date, well limits
GRID       -- Grid geometry (DX/DY/DZ/TOPS or corner-point GRDECL), porosity, permeability
PROPS      -- Fluid PVT (PVTO/PVDG/PVTW), relative permeability (SWOF/SGOF), rock compressibility
SOLUTION   -- Initial equilibration (EQUIL, RSVD)
SUMMARY    -- Output variable requests (FOPR, FOPT, WBHP, etc.)
SCHEDULE   -- Wells (WELSPECS, COMPDAT), controls (WCONPROD, WCONINJE), time steps (TSTEP)
END
```

Key syntax:
- `--` starts a comment
- `/` terminates a data record
- `INCLUDE 'filename' /` inserts an external file
- `N*value` repeats a value N times (e.g., `300*1000`)
- `1*` means "use default"

File types: `.DATA` (main deck, must be uppercase), `.INC` (include files), `.GRDECL` (corner-point grid geometry), `.prop` (property arrays).

## Visualization

Two Jupyter notebooks in `notebooks/`:

- **Plot_Simulation_Results.ipynb** -- Plot a single run: field totals (FOPT, FGPT, FWPT, FPR), field rates (FOPR, FGPR, FWPR), well rates, and well BHP.
- **Compare_Runs.ipynb** -- Compare multiple runs side-by-side with overlay plots and a summary table.

Both use `resdata.summary.Summary` to read `.SMSPEC` files from results folders. The Python venv at `~/venv` has `resdata`, `matplotlib`, and `pandas` installed.

## Creating a New Model

1. Create a folder under `decks/` (e.g., `decks/my-project/`)
2. Write a `.DATA` file (or copy from `opm-data/` as a starting point)
3. Keep all INCLUDE files in the same folder as the `.DATA` file
4. Run: `runsim ~/projects/decks/my-project/MY_MODEL.DATA`
5. Visualize: open the plotting notebook and point it at the results folder

## Simulation Output

Each `runsim` call creates a timestamped folder in `results/` containing:
- `.EGRID` -- Grid geometry
- `.INIT` -- Initial properties
- `.UNRST` -- Restart data (cell properties over time)
- `.SMSPEC` / `.UNSMRY` -- Summary time-series data (what the notebooks read)
- `flow.log` -- Simulation log

## Post-Simulation Workflow

After a simulation finishes, remind Doug to view the results:

> Simulation done! To see the plots, open http://178.156.251.191:8888/ and Shift+Enter through the cells in `Plot_Simulation_Results.ipynb`. The notebook auto-selects the latest run.

## Additional OPM Utilities

- `compareECL` -- Compare two sets of Eclipse output files
- `convertECL` -- Convert between Eclipse file formats
- `summary` -- Quick summary data extraction from command line
