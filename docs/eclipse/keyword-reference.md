# ECLIPSE Keyword Reference

Quick reference for commonly used ECLIPSE keywords, organized by section.

## RUNSPEC Keywords

### Simulation Type

| Keyword | Purpose | Example |
|---------|---------|---------|
| `TITLE` | Model name | `TITLE` followed by text line |
| `START` | Start date | `START 1 JAN 2025 /` |
| `NOSIM` | Data check only | `NOSIM` |

### Phase Specification

| Keyword | Purpose | Notes |
|---------|---------|-------|
| `OIL` | Enable oil phase | Required for black-oil |
| `WATER` | Enable water phase | |
| `GAS` | Enable gas phase | |
| `DISGAS` | Dissolved gas in oil | Requires GAS |
| `VAPOIL` | Vaporized oil in gas | Requires OIL, GAS |

### Dimensions

| Keyword | Format | Description |
|---------|--------|-------------|
| `DIMENS` | `NX NY NZ /` | Grid dimensions |
| `TABDIMS` | `NTSFUN NTPVT... /` | Table sizes |
| `WELLDIMS` | `NWMAX NCMAX... /` | Well arrays |
| `REGDIMS` | `NTFIP NMFIPR... /` | Region arrays |
| `AQUDIMS` | `MXNAQN MXNAQC... /` | Aquifer arrays |

### Units

| Keyword | Description |
|---------|-------------|
| `METRIC` | SI units (default) |
| `FIELD` | US oilfield units |
| `LAB` | Laboratory units |

## GRID Keywords

### Cartesian Grid

| Keyword | Format | Unit |
|---------|--------|------|
| `DX` | Per-cell values | Length |
| `DY` | Per-cell values | Length |
| `DZ` | Per-cell values | Length |
| `TOPS` | Top depth, layer 1 | Length |

### Corner-Point Grid

| Keyword | Description |
|---------|-------------|
| `COORD` | Pillar coordinates |
| `ZCORN` | Corner depths |
| `ACTNUM` | Active cell flags |

### Properties

| Keyword | Format | Unit |
|---------|--------|------|
| `PERMX` | Per-cell | mD |
| `PERMY` | Per-cell | mD |
| `PERMZ` | Per-cell | mD |
| `PORO` | Per-cell | fraction |
| `NTG` | Per-cell | fraction |

### Grid Operations

| Keyword | Purpose |
|---------|---------|
| `MINPV` | Minimum pore volume |
| `PINCH` | Pinchout handling |
| `MULTZ` | Z-transmissibility multiplier |

## PROPS Keywords

### PVT Tables

| Keyword | Phases | Description |
|---------|--------|-------------|
| `PVTO` | Oil w/ dissolved gas | Bo, viscosity vs P, Rs |
| `PVDO` | Dead oil | Bo, viscosity vs P |
| `PVTW` | Water | Bw, compressibility, viscosity |
| `PVDG` | Dry gas | Bg, viscosity vs P |
| `PVTG` | Wet gas | Bg, viscosity vs P, Rv |

### Rock Properties

| Keyword | Format | Description |
|---------|--------|-------------|
| `ROCK` | `Pref Cr /` | Rock compressibility |
| `DENSITY` | `ρo ρw ρg /` | Surface densities |

### Relative Permeability

| Keyword | Columns | Description |
|---------|---------|-------------|
| `SWOF` | Sw Krw Krow Pcow | Water-oil (water-wet) |
| `SGOF` | Sg Krg Krog Pcog | Gas-oil |
| `SOF2` | So Kro | 2-phase oil |
| `SOF3` | So Krow Krog | 3-phase oil |
| `SWFN` | Sw Krw Pcow | Water function |
| `SGFN` | Sg Krg Pcog | Gas function |

### Endpoint Scaling

| Keyword | Description |
|---------|-------------|
| `SWL` | Connate water saturation |
| `SWU` | Maximum water saturation |
| `SGL` | Connate gas saturation |
| `SGU` | Maximum gas saturation |

## REGIONS Keywords

| Keyword | Purpose |
|---------|---------|
| `SATNUM` | Saturation table region |
| `PVTNUM` | PVT table region |
| `FIPNUM` | Fluid-in-place region |
| `EQLNUM` | Equilibration region |
| `IMBNUM` | Imbibition region |

## SOLUTION Keywords

### Equilibration

| Keyword | Format | Description |
|---------|--------|-------------|
| `EQUIL` | See below | Equilibration data |
| `RSVD` | Depth Rs pairs | Rs vs depth |
| `RVVD` | Depth Rv pairs | Rv vs depth |
| `PBVD` | Depth Pb pairs | Bubble point vs depth |

**EQUIL Format:**
```
EQUIL
-- Datum  Pdatum   OWC   Pcow   GOC   Pcog  RSVD  RVVD  N
   8500   4000     9000  0      8000  0     1     1     0 /
```

### Explicit Initialization

| Keyword | Description |
|---------|-------------|
| `PRESSURE` | Initial pressure |
| `SWAT` | Initial water saturation |
| `SGAS` | Initial gas saturation |
| `RS` | Initial dissolved gas |

## SUMMARY Keywords

### Field Totals

| Keyword | Description |
|---------|-------------|
| `FOPR` | Field oil production rate |
| `FWPR` | Field water production rate |
| `FGPR` | Field gas production rate |
| `FOPT` | Field oil total (cumulative) |
| `FWPT` | Field water total |
| `FGPT` | Field gas total |
| `FPR` | Field pressure (average) |
| `FWCT` | Field water cut |
| `FGOR` | Field GOR |

### Well Data

| Pattern | Examples |
|---------|----------|
| `WOPR` | Oil production rate |
| `WWPR` | Water production rate |
| `WGPR` | Gas production rate |
| `WBHP` | Bottom-hole pressure |
| `WTHP` | Tubing-head pressure |
| `WWIR` | Water injection rate |
| `WGIR` | Gas injection rate |

**Specifying Wells:**
```
WOPR
'PROD1' 'PROD2' /    -- Specific wells

WOPR
/                     -- All wells
```

### Block Data

```
BPR
I J K /              -- Block pressure at (I,J,K)

BSGAS
I J K /              -- Gas saturation at (I,J,K)
```

## SCHEDULE Keywords

### Well Definition

| Keyword | Purpose |
|---------|---------|
| `WELSPECS` | Well specification |
| `COMPDAT` | Completion data |
| `COMPSEGS` | Multi-segment completions |

**WELSPECS Format:**
```
WELSPECS
-- Name  Group  I    J    RefDepth  PreferredPhase
   PROD1 G1     50   50   8500      OIL /
/
```

**COMPDAT Format:**
```
COMPDAT
-- Well  I  J  K1 K2 Open Sat  Diam   Kh    Skin  Dir
   PROD1 50 50 1  10 OPEN 2*   0.5    1*    0     Z /
/
```

### Production Control

| Keyword | Description |
|---------|-------------|
| `WCONPROD` | Producer control |
| `WCONHIST` | Historical producer |

**WCONPROD Format:**
```
WCONPROD
-- Well  Open  Ctrl  Orat  Wrat  Grat  Lrat  Resv  BHP
   PROD1 OPEN  ORAT  1000  1*    1*    1*    1*    1500 /
/
```

**Control Modes:**
| Code | Description |
|------|-------------|
| `ORAT` | Oil rate |
| `WRAT` | Water rate |
| `GRAT` | Gas rate |
| `LRAT` | Liquid rate |
| `RESV` | Reservoir voidage |
| `BHP` | Bottom-hole pressure |

### Injection Control

| Keyword | Description |
|---------|-------------|
| `WCONINJE` | Injector control |
| `WCONINJH` | Historical injector |

**WCONINJE Format:**
```
WCONINJE
-- Well  Type  Open  Ctrl  Rate   Resv   BHP
   INJ1  WAT   OPEN  RATE  2000   1*     5000 /
/
```

### Well Operations

| Keyword | Purpose |
|---------|---------|
| `WELOPEN` | Open/shut wells |
| `WELTARG` | Modify targets |
| `WEFAC` | Well efficiency factor |
| `WECON` | Economic limits |

### Time Stepping

| Keyword | Format |
|---------|--------|
| `TSTEP` | `days... /` |
| `DATES` | `D MON YEAR /` |
| `END` | End simulation |

**Examples:**
```
TSTEP
10 20 30 30 30 /     -- Variable steps

DATES
1 JAN 2025 /
1 FEB 2025 /
/

END
```

## Special Keywords

### Include Files

```
INCLUDE
'path/to/file.inc' /
```

### Skip/Resume

```
SKIP                  -- Start skipping
...
ENDSKIP              -- Resume reading
```

### Paths

```
PATHS
'GRID' 'include/grid/' /
/
```

## See Also

- [Deck Structure](deck-structure.md) - Section organization
- [Common Errors](common-errors.md) - Troubleshooting
- [OPM Manual](https://opm-project.org/) - Complete reference