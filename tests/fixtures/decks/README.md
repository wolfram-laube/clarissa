# Test Fixture Decks

Reference simulation input decks for integration and contract testing.

## Provenance

| Deck | Source | License | Grid | Description |
|------|--------|---------|------|-------------|
| `spe1/SPE1CASE1.DATA` | OPM/opm-data | ODbL | 10×10×3 (300) | SPE1 Case 1 — basic three-phase black-oil |
| `spe1/SPE1CASE2.DATA` | OPM/opm-data | ODbL | 10×10×3 (300) | SPE1 Case 2 — dissolved gas, primary reference |
| `spe1/SPE1CASE2_2P.DATA` | OPM/opm-data | ODbL | 10×10×3 (300) | SPE1 two-phase (oil-water only) |
| `spe9/SPE9_CP.DATA` | OPM/opm-data | ODbL | 24×25×15 (9000) | SPE9 corner-point, 26 wells |
| `spe9/SPE9_CP_SHORT.DATA` | OPM/opm-data | ODbL | 24×25×15 (9000) | SPE9 short run (fewer timesteps) |
| `watershed/WATERSHED.DATA` | Doug (pm-flow) | Internal | 20×20×3 (1200) | Groundwater recharge demo |

## Large Models (via Git Submodule)

Available in `data/opm-data/` (not copied into fixtures due to size):

| Model | Grid | Size | Use Case |
|-------|------|------|----------|
| Norne | 46×112×22 (113K) | 31MB | Real North Sea field validation |
| Sleipner | 64×118×263 (2M) | 59MB | CO₂ storage benchmark |
| SPE10 Model 2 | 60×220×85 (1.1M) | 74MB | Large heterogeneous stress test |

Access: `git submodule update --init data/opm-data`

## Licensing

OPM reference data: Open Database License (ODbL 1.0)
http://opendatacommons.org/licenses/odbl/1.0/

Individual contents: Database Contents License (DbCL 1.0)
http://opendatacommons.org/licenses/dbcl/1.0/
