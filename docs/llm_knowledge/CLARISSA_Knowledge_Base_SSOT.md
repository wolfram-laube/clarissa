# CLARISSA Knowledge Base — Single Source of Truth (SSOT)
**Version:** 1.1
**Compiled:** February 28, 2026
**Sources:** Genesis Curriculum (15p) | Self-Directed Training Protocol (25p) | Complete Self-Bootstrap Training (66p) | Exercise 1 (5p) | Exercise 2 (11p)
**Subject:** CLARISSA — Claude-based Reservoir Simulation Assistant Training & Reference

---

## Part A: CLARISSA Identity & Training History

### A.1 Executive Summary

CLARISSA (Claude-based Reservoir Simulation Assistant) chronicles the systematic development of an AI assistant specialized in reservoir simulation engineering. Over 7 months of iterative learning, corrections, and field application, a general-purpose LLM was transformed into a domain expert capable of autonomous reservoir simulation workflow execution, compositional modeling, and economic optimization.

**Key Metrics:**
- Training duration: 7 months (August 2025 – February 2026)
- Knowledge base versions: 5 major iterations (v1.0 → v1.5)
- Session logs documented: 26+
- Fields worked: 3 (Shah, Dolphin, San Andres ROZ)
- Model types mastered: Black oil, compositional, thermal
- Critical corrections applied: 15+

### A.2 Training Curriculum (7 Phases)

#### Phase 1: Foundation Training (August 2025)
**Objective:** Establish basic Eclipse/tNavigator literacy and file structure understanding.

- **Module 1.1:** Eclipse Data File Structure — RUNSPEC, GRID, PROPS, SOLUTION, SCHEDULE; keyword syntax (uppercase, terminated with `/`); comment convention (`--`); 8-character naming limit; INCLUDE file architecture
- **Module 1.2:** tNavigator Execution — Shell requirement: `csh` (not bash); `.DATA` file format; execution commands; output file interpretation (.PRT, .RSM, .UNSMRY)

#### Phase 2: Core Simulation Skills (September 2025)
- **Module 2.1:** PVT Properties — Dead oil (PVDO) vs. live oil (PVTO); gas dissolution (Rs); formation volume factor (Bo); PVDO = dead oil → no DISGAS needed; Bo must DECREASE with pressure below Pb (monotonicity)
- **Module 2.2:** Rock & Fluid Interactions — SWOF/SGOF interpretation; SCAL data import; relative permeability endpoints; capillary pressure
- **Module 2.3:** OOIP Analysis & Recovery — Eclipse OOIP extraction from `.sum` files; Recovery factor calculation; 100-year extended simulations; well pattern analysis (5-spot, line drive); Validation method: `Recovery Factor = (OOIP_initial - FOIP_final) / OOIP_initial × 100%`
- **Module 2.4:** Well Management — WELSPECS (well definitions); COMPDAT (completions); WCONPROD/WCONINJE (controls); SUMMARY section requirements; well activation/deactivation; Dependency Chain: `WELSPECS → COMPDAT → WCONPROD/WCONINJE → SUMMARY keywords`
- **Module 2.5:** Engineering Methodology vs LLM Anti-Patterns — LLMs tend toward "clean-slate" solutions; correct approach: incremental modification with preservation; **Golden Rules:** (1) Never delete working code — comment it out, (2) Preserve reference values in comments, (3) Make one change at a time, (4) Test after each modification

#### Phase 3: Field Application (October 2025)
**Objective:** Apply simulation skills to real field models with production history.

- **Module 3.1:** Shah Field Compositional Model — Abu Dhabi sour gas field; compositional EOS with H2S/CO2; multi-layer carbonate reservoir; history matching against production data; Al Hosn plant component model recalibration
- **Module 3.2:** Dolphin Gas Field — Qatar/UAE cross-border gas export; partner meeting evaluations; horizontal well logging evaluation with tractor (successfully argued against); reserves governance model development
- **Module 3.3:** Multi-Layer Heterogeneous Models — Transition from uniform to layered properties; layer-by-layer PORO/PERMX assignment; COPY/MULTIPLY patterns for anisotropy; understanding flow unit hierarchy (thief zones, barriers, pay)

#### Phase 4: Advanced Topics (November 2025)
**Objective:** Master compositional modeling, EOR mechanisms, and thermal recovery.

- **Module 4.1:** Compositional EOS Modeling — Peng-Robinson (PR) vs. Soave-Redlich-Kwong (SRK) equations of state; component lumping strategies (C1, C2-C6, C7+, etc.); critical property characterization (Tc, Pc, ω); binary interaction coefficients (BIC) — lower triangular matrix with n×(n-1)/2 entries; volume shifts (SSHIFT) for liquid density correction; flash calculation convergence
- **Module 4.2:** CO2 WAG Injection — Water-Alternating-Gas mechanism; miscibility conditions (MMP — minimum miscibility pressure); WELLSTRE for injection gas composition; WINJGAS for stream assignment; gas/water cycle switching via WCONINJE; mobility control rationale; expected RF: 40–60% for miscible WAG
- **Module 4.3:** Thermal Recovery — Steam flooding models; STARS-type thermal simulation concepts; temperature-dependent viscosity; steam quality and injection enthalpy; CSS (cyclic steam stimulation) vs. steamflood vs. SAGD patterns

#### Phase 5: Automation & Workflow (December 2025)
**Objective:** Build automated simulation pipelines for batch execution and analysis.

- **Module 5.1:** Automated Simulation Submission — Shell scripts for tNavigator batch execution; `.DATA` file templating with parameter substitution; queue management for multiple runs; output file collection and organization
- **Module 5.2:** Result Extraction & Post-Processing — `.RSM` and `.UNSMRY` file parsing; SUMMARY vector extraction to CSV/pandas; automated plot generation (FOPR, FPR, FWCT vs. time); comparison plots across sensitivity cases
- **Module 5.3:** Batch Sensitivity Studies — Parameter sweep design (porosity, permeability, injection rate); tornado chart generation for sensitivity ranking; design of experiments (DOE) for multi-parameter studies; response surface methodology concepts

#### Phase 6: Integration (January 2026)
- **Module 6.5:** Log-to-Simulation Workflow (San Andres ROZ 34-layer from well logs)
  - **Workflow:** (1) Log interpretation → honor φ, So measurements, (2) Zone identification → GR character drives architecture, (3) Barrier confirmation → GR spike MUST have Rt drop (both must agree), (4) Layer model → variable thickness geologically driven, (5) Permeability → Lucia rock fabric transform, (6) kv/kh → analog data (SSAU = 0.06), (7) Simulation → validate behavior matches expectation
  - **Lucia Rock Fabric Permeability Transform:** `log(k) = [A - B·log(rfn)] + [C - D·log(rfn)] · log(φip)` where k = permeability (mD), rfn = rock fabric number (1-4), φip = interparticle porosity (fraction)
- **Module 6.6:** Grid Sizing Correction — WRONG: 10×10×34 @ 200 ft/cell = 92 acres (too large!); RIGHT: 10×10×34 @ 66 ft/cell = 10 acres (quarter pattern)

#### Phase 7: Optimization & Economics (February 2026)
**Objective:** Integrate economic analysis with simulation for decision-making.

- **Module 7.1:** NPV-Driven Scenario Evaluation — Discounted cash flow per simulation scenario; oil revenue ($50/STB), water cost ($3/bbl injection + $3/bbl disposal); discount rate 10%; comparison of development options by NPV ranking; time value of money: early oil worth more than late oil
- **Module 7.2:** Conformance Control Strategies — Thief zone identification via permeability contrast; surgical shutoff (skip high-perm layer in completions) → RF from ~30% to ~45-55%; selective completion design; layer-by-layer COMPDAT K1/K2 manipulation; comparison: full completion vs. surgical vs. avoid-thief
- **Module 7.3:** Recovery Factor Optimization — Waterflood optimization (injection rate, pattern selection); WAG ratio tuning (gas slug size vs. water slug size); injection pressure optimization (BHP-controlled vs. rate-controlled); multi-scenario NPV comparison for investment decision

### A.3 CLARISSA Operating Principles

1. **Baseline first.** Always validate before modifying.
2. **One change at a time.** Isolate cause and effect.
3. **Document everything.** Your knowledge folder is your memory.
4. **Trust material balance.** If it doesn't close, something is wrong.
5. **Errors are teachers.** Every failure teaches you something.

### A.4 Behavioral Corrections Log

| # | Wrong Pattern | Correct Pattern | Context |
|---|--------------|-----------------|---------|
| 1 | `MNTH = 2` | `MNTH = FEB` | Month specification in DATES |
| 2 | `DAY >= 4000` | Use ELAPSED or specific dates | Time-based conditions |
| 3 | Composition in WINJGAS | Use WELLSTRE stream name | Gas injection stream reference |
| 4 | Clean-slate file rewrites | Incremental modification | LLM anti-pattern avoidance |
| 5 | Delete working code | Comment it out | Preserve reference values |
| 6 | 200 ft/cell grid sizing | 66 ft/cell for 10-acre pattern | Grid sizing for quarter pattern |

---

## Part B: Eclipse/tNavigator Technical Reference

### B.1 Data File Structure — Mandatory Section Order

```
RUNSPEC → GRID → PROPS → SOLUTION → SUMMARY → SCHEDULE
```
**Why order matters:** Later sections reference data defined in earlier sections (dependencies).

### B.2 RUNSPEC Section Keywords

| Keyword | Purpose | Example |
|---------|---------|---------|
| TITLE | Model name | `SIMPLE BLACK OIL MODEL` |
| DIMENS | Grid dimensions NX NY NZ | `10 10 3 /` = 300 cells |
| OIL | Enable oil phase | (flag, no data) |
| WATER | Enable water phase | (flag, no data) |
| GAS | Enable gas phase | (flag, no data) |
| DISGAS | Enable dissolved gas in oil | (flag, compositional) |
| FIELD | FIELD unit system | (flag) |
| METRIC | METRIC unit system | (flag) |
| START | Simulation start date | `1 JAN 2017 /` |
| TABDIMS | Table dimension limits | Required if custom SWOF/SGOF |
| WELLDIMS | Well dimension limits | Max wells, completions, groups |
| COMPS | Number of components | `7 /` (compositional only) |
| ENDSCALE | Endpoint scaling options | `NODIR REVERS` |

### B.3 GRID Section Keywords

| Keyword | Purpose | Example | Notes |
|---------|---------|---------|-------|
| DX | Cell size X (ft in FIELD) | `300*200 /` | Repeat notation: N*value |
| DY | Cell size Y | `300*200 /` | |
| DZ | Cell size Z (thickness) | Variable by layer | |
| TOPS | Depth to top of layer 1 | `100*4000 /` | Deeper layers auto-calculated |
| PORO | Porosity (fraction) | `100*0.200 /` | Range: 0.05–0.35 typical |
| PERMX | Permeability X (mD) | `100*200 /` | millidarcies |
| PERMY | Permeability Y | via COPY | Usually = PERMX |
| PERMZ | Permeability Z | via MULTIPLY | Usually PERMX × 0.01 |
| COPY | Copy one array to another | `PERMX PERMY /` | |
| MULTIPLY | Multiply array by factor | `PERMZ 0.01 /` | Kv/Kh anisotropy |
| EQUALS | Set property by region | `DZ 50.0 1 25 1 25 7 7 /` | Format: KW VAL I1 I2 J1 J2 K1 K2 |

### B.4 PROPS Section Keywords

#### Fluid Properties
| Keyword | Structure | Critical Rules |
|---------|-----------|----------------|
| DENSITY | Oil, Water, Gas surface densities | Units: lb/ft³ (FIELD) |
| PVDO | Pressure, Bo, Viscosity (dead oil) | **Bo MUST DECREASE with pressure** (monotonicity) |
| PVTW | Pref, Bw, Cw, μw, Cv | 5-value single-row table |
| ROCK | Rock compressibility at ref pressure | Single row: Pref, Cr |

##### Reference DENSITY Values (Exercise 1)
```
DENSITY
-- Oil    Water   Gas (lb/ft3)
   45.0   64.0    0.044 /
```

##### Reference PVDO Data (Exercise 1 — Dead Oil)
```
PVDO
-- Pressure(psia)  Bo(RB/STB)  Viscosity(cP)
   1000             1.200       1.20
   1500             1.150       1.15
   2000             1.100       1.10
   2500             1.062       1.05
   3000             1.040       1.00
   3500             1.025       0.98
   4000             1.018       0.97
   4500             1.014       0.96
   5000             1.012       0.95  /
```
**Note:** Bo decreases from 1.200 → 1.012 as pressure increases. This is monotonically decreasing — violating this causes "Non-monotonic" errors.

##### Reference PVTW Data (Exercise 1)
```
PVTW
-- Pref(psia)  Bw(RB/STB)  Cw(1/psi)  Visc(cP)  Cv
   4000         1.01         3.0E-6     0.5       0 /
```

##### Reference ROCK Data (Exercise 1)
```
ROCK
-- Pref(psia)  Cr(1/psi)
   4000         4.0E-6 /
```

#### Relative Permeability Tables
| Keyword | Columns | Notes |
|---------|---------|-------|
| SWOF | Sw, Krw, Krow, Pcow | Water-oil; connate Sw first row, Krw=0 |
| SGOF | Sg, Krg, Krog, Pcgo | Gas-oil; Sg=0 first row, Krg=0 |

**SWOF Key Points:**
- First row: Connate water saturation (Sw=0.15–0.20), Krw=0, Krow=max
- Last row: Sw=1.0, Krw=max, Krow=0
- Pcow: Capillary pressure (can be 0 for simplified models)

**SGOF Key Points:**
- First row: Sg=0, Krg=0, Krog=max
- Last row: Sg=max (1-Swc), Krg=max, Krog=0
- Pcgo: Usually 0 for simplified models

##### Reference SWOF Table (Exercise 1 — Simplified, No Pcow)
```
SWOF
-- Sw      Krw      Krow     Pcow
   0.20    0.00     0.60     0.0
   0.30    0.03     0.45     0.0
   0.40    0.05     0.33     0.0
   0.50    0.08     0.20     0.0
   0.60    0.13     0.10     0.0
   0.70    0.22     0.00     0.0
   0.80    0.37     0.00     0.0
   0.90    0.61     0.00     0.0
   1.00    1.00     0.00     0.0  /
```

##### Reference SWOF Table (Exercise 2 — With Capillary Pressure, 18 rows)
```
SWOF
-- Sw      Krw        Krow       Pcow(psi)
   0.150   0.00000    0.80000    100.00
   0.200   0.00001    0.66250     94.12
   0.250   0.00019    0.53790     88.24
   0.300   0.00097    0.42630     82.35
   0.350   0.00307    0.32770     76.47
   0.400   0.00748    0.24200     70.59
   0.450   0.01552    0.16930     64.71
   0.500   0.02875    0.10950     58.82
   0.550   0.04904    0.06270     52.94
   0.600   0.07856    0.02890     47.06
   0.650   0.11973    0.00800     41.18
   0.700   0.17530    0.00000     35.29
   0.750   0.24827    0.00000     29.41
   0.800   0.34196    0.00000     23.53
   0.850   0.45996    0.00000     17.65
   0.900   0.60613    0.00000     11.76
   0.950   0.78466    0.00000      5.88
   1.000   1.00000    0.00000      0.00  /
```

##### Reference SGOF Table (Exercise 2 — 18 rows)
```
SGOF
-- Sg      Krg        Krog       Pcgo(psi)
   0.0000  0.00000    0.80000    0
   0.0500  0.01118    0.64705    0
   0.1000  0.03162    0.51622    0
   0.1500  0.05809    0.40548    0
   0.2000  0.08944    0.31284    0
   0.2500  0.12500    0.23640    0
   0.3000  0.16432    0.17434    0
   0.3500  0.20706    0.12489    0
   0.4000  0.25298    0.08637    0
   0.4500  0.30187    0.05719    0
   0.5000  0.35355    0.03584    0
   0.5500  0.40789    0.02090    0
   0.6000  0.46476    0.01104    0
   0.6500  0.52405    0.00506    0
   0.7000  0.58566    0.00185    0
   0.7500  0.64952    0.00045    0
   0.8000  0.71554    0.00004    0
   0.8500  0.78366    0.00000    0  /
```

#### Endpoint Scaling (Advanced)
| Keyword | Value | Meaning |
|---------|-------|---------|
| SCALECRS | YES | Enable 3-point endpoint scaling |
| SWL | = SWATINIT | Lower water saturation endpoint |
| SWCR | = SWATINIT + 0.10 | Critical water saturation |
| SGU | = 1.0 - SWCR | Upper gas saturation |
| SWU | = 1.0 | Upper water saturation |
| SGCR | = 0.01 | Critical gas saturation |
| SOWCR | = 0.35 | Critical oil-in-water saturation |
| SOGCR | = 0.20 | Critical oil-in-gas saturation |
| KRW | 1.0 | Max water rel perm |
| KRO | 0.80 | Max oil rel perm |
| KRWR | 0.60 | Water Kr when oil stops flowing |
| KRGR | 0.30 | Gas Kr at residual conditions |
| KRG | 0.50 | Max gas rel perm |

#### Compositional EOS (Peng-Robinson)
| Keyword | Purpose | Units |
|---------|---------|-------|
| EOS | Equation of state type | `PR /` or `SRK /` |
| CNAMES | Component names | String list |
| TCRIT | Critical temperatures | Rankine |
| PCRIT | Critical pressures | psia |
| VCRIT | Critical volumes | ft³/lb-mol |
| ZCRIT | Critical Z-factors | dimensionless |
| MW | Molecular weights | lb/lb-mol |
| ACF | Acentric factors | dimensionless |
| BIC | Binary interaction coefficients | Lower triangular matrix |
| OMEGAA | EOS constant A | 0.45724 (standard PR) |
| OMEGAB | EOS constant B | 0.0778 (standard PR) |
| SSHIFT | Volume shift parameters | Per-component |
| PARACHOR | Parachor values (IFT) | Per-component |
| ZMFVD | Initial mole fractions vs depth | Per-component per depth |
| TEMPVD | Temperature vs depth | °F vs ft |
| STCOND | Standard conditions | T(°F), P(psia) |
| FIELDSEP | Separator conditions | Stage T, P |

##### Complete 7-Component EOS Data (Exercise 2 — Peng-Robinson)

**Components:** CO2, C1N2, C2C3H2S, C4-C6, C7-C10, C11-C16, C17+

| Property | CO2 | C1N2 | C2C3H2S | C4-C6 | C7-C10 | C11-C16 | C17+ |
|----------|-----|------|---------|-------|--------|---------|------|
| TCRIT (°R) | 547.56 | 339.21 | 619.38 | 835.43 | 1117.84 | 1344.62 | 1686.57 |
| PCRIT (psia) | 1071.34 | 666.78 | 722.56 | 491.31 | 389.65 | 277.43 | 159.30 |
| VCRIT (ft³/lb-mol) | 1.51 | 1.565 | 2.712 | 5.018 | 7.731 | 12.125 | 22.15 |
| ZCRIT | 0.2753 | 0.2867 | 0.2949 | 0.2750 | 0.2511 | 0.2331 | 0.1949 |
| MW (lb/lb-mol) | 44.01 | 16.29 | 36.19 | 70.06 | 114.17 | 180.94 | 358.25 |
| ACF | 0.2250 | 0.0139 | 0.1254 | 0.2452 | 0.3832 | 0.5820 | 1.0054 |
| SSHIFT | -0.0626 | -0.0866 | -0.1047 | -0.0419 | 0.1209 | 0.2089 | 0.3426 |
| PARACHOR | 78.0 | 76.03 | 127.34 | 229.44 | 329.70 | 489.0 | 925.99 |

**EOS Constants:** OMEGAA = 0.45724, OMEGAB = 0.0778 (all components)

**BIC Matrix (Lower Triangular):**
```
BIC
  0.0976
  0.1289  0.0103
  0.1271  0.0019  0.0063
  0.1105  0.0241  0.0196  0.003
  0.0943  0.0494  0.0333  0.0061  0.0
  0.0997  0.1365  0.0588  0.0120  0.0   0.0  /
```
Total entries: 21 (7×6/2). Row i contains BIC values for component i with components 1 through i-1.

**Initial Composition (ZMFVD — uniform with depth):**

| Component | CO2 | C1N2 | C2C3H2S | C4-C6 | C7-C10 | C11-C16 | C17+ |
|-----------|------|-------|---------|-------|--------|---------|------|
| Mole fraction | 0.0234 | 0.2088 | 0.1837 | 0.1310 | 0.1385 | 0.1451 | 0.1695 |

**Interpretation:** Moderately heavy oil (2.34% CO2, 20.88% C1, 16.95% C17+). Requires CO2 injection for miscibility. Undersaturated — no initial gas cap.

### B.5 SOLUTION Section

| Keyword | Structure | Example |
|---------|-----------|---------|
| EQUIL | Datum_depth Pdat OWC Pcow_OWC GOC Pcgo_GOC / | `4000 3600 4100 0 0 0 /` |
| SWATINIT | Initial water saturation per cell | Layer-by-layer specification |

**EQUIL Notes:**
- OWC below reservoir → 100% oil saturation initially
- GOC not specified → undersaturated (no gas cap)
- Pcow at OWC usually 0 for simplified models

### B.6 SUMMARY Section — Output Vectors

#### Field Level
| Vector | Meaning |
|--------|---------|
| FOPR | Field Oil Production Rate |
| FOPT | Field Oil Production Total |
| FWPR | Field Water Production Rate |
| FWPT | Field Water Production Total |
| FWIR | Field Water Injection Rate |
| FWIT | Field Water Injection Total |
| FPR | Field Pressure (average) |
| FOIP | Field Oil In Place |
| FWCT | Field Water Cut |

#### Well Level
| Vector | Meaning |
|--------|---------|
| WOPR | Well Oil Production Rate |
| WWPR | Well Water Production Rate |
| WGPR | Well Gas Production Rate |
| WLPR | Well Liquid Production Rate |
| WOPT/WWPT/WGPT/WLPT | Cumulative production totals |
| WWCT | Well Water Cut |
| WGOR | Well Gas-Oil Ratio |
| WBHP | Well Bottomhole Pressure |
| WPI | Well Productivity Index |
| WBP | Well Block Pressure |
| WWIR/WGIR | Well injection rates (water/gas) |
| WWIT/WGIT | Cumulative injection totals |

### B.7 SCHEDULE Section — Well Management

#### WELSPECS
`Well_name  Group  I  J  Datum_depth  Preferred_phase /`

#### COMPDAT
`Well_name  I  J  K1  K2  Status  2*  Wellbore_radius  3*  Direction  1* /`
- K1 = top completion layer, K2 = bottom completion layer
- Status: OPEN or SHUT
- `2*` defaults: saturation table number, transmissibility factor
- `3*` defaults: skin, D-factor, penetration direction qualifier

#### WCONPROD
`Well_name  Status  Control_mode  Target_rate  4*  Min_BHP /`
- Control modes: ORAT (oil rate), LRAT (liquid rate), WRAT (water rate), BHP, RESV (reservoir voidage)
- `4*` defaults: water/gas/liquid/reservoir rate limits

#### WCONINJE
`Well_name  Inj_type  Status  Control_mode  Rate  1*  Max_BHP /`
- Injection types: WATER, GAS, OIL
- Control modes: RATE, BHP
- `1*` default: reservoir rate limit

#### Time Stepping
| Keyword | Purpose | Example |
|---------|---------|---------|
| TSTEP | Advance by days | `12*30.4167 /` (12 monthly) |
| DATES | Advance to specific date | `1 JAN 2018 /` |
| END | Terminate simulation | Required last keyword |

#### WAG Implementation
| Keyword | Purpose | Example |
|---------|---------|---------|
| WELLSTRE | Define gas composition | `PURECO2 1.0 0.0 0.0 ... /` |
| WINJGAS | Assign gas stream to well | `INJE STREAM PURECO2 /` |
| ACTIONX | Conditional switching | Trigger on WWCT threshold |

**WAG Cycle Switching Pattern:**
```
-- Gas phase
WINJGAS
  INJE  STREAM  PURECO2 /
/
WCONINJE
  INJE  GAS  OPEN  BHP  2*  3000 /
/

-- Water phase
WCONINJE
  INJE  WATER  OPEN  BHP  2*  3000 /
/
```

---

## Part C: Reference Exercise Models

### C.1 Exercise 1: Layered Waterflood (BEGINNER)

**Grid:** 10×10×3 = 300 cells, DX=DY=200 ft, DZ=10 ft
**Pattern:** 10-acre pilot waterflood (2000 ft × 2000 ft), line drive
**Phases:** Oil + Water (dead oil, no gas)
**Wells:** PRD01 at (1,1), INJ01 at (10,10), both K1-K2=1-3
**Duration:** 1 JAN 2017 – 1 JAN 2050 (33 years, annual reporting)
**Reference file:** `SS_FIX_INJ_BHP_TNAV.DATA` at `/home/matejkam/eclipse_claude_code/TEST_081425/`
**Expected OOIP:** ~1.1–1.3 MM STB

#### C.1.1 Layer Architecture (3 Layers)

| Layer | TOPS (ft) | DZ (ft) | PORO | PERMX (mD) | Role |
|-------|-----------|---------|------|------------|------|
| 1 | 4000 | 10 | 0.200 | 50 | Tight — bypassed oil |
| 2 | 4010 | 10 | 0.250 | 300 | **Primary flow unit** — early water breakthrough |
| 3 | 4020 | 10 | 0.220 | 15 | Moderate — bypassed oil |

**Vertical anisotropy:** Kv/Kh = 0.01 (strong) → limits crossflow between layers
**Net pay:** 30 ft total (3 × 10 ft)
**Drive mechanism:** Line drive (injector and producer at opposite corners)
**Expected behavior:** Water preferentially flows through Layer 2 (300 mD), causing early breakthrough. Layers 1 and 3 have significant bypassed oil due to permeability contrast.

#### C.1.2 EQUIL Data

```
EQUIL
-- Datum(ft) Pdat(psia) OWC(ft) Pcow  GOC(ft) Pcgo
   4000      3600       4100    0     0       0    /
```
**Note:** OWC at 4100 ft is below reservoir bottom (4030 ft) → 100% oil saturation initially.

#### C.1.3 Well Controls

```
WELSPECS
  PRD01  G1  1   1   4000  OIL /
  INJ01  G1  10  10  4000  WATER /
/

COMPDAT
  PRD01  1   1   1  3  OPEN  2*  0.3  3*  Z  1* /
  INJ01  10  10  1  3  OPEN  2*  0.3  3*  Z  1* /
/

WCONPROD
  PRD01  OPEN  ORAT  5000  4*  1000 /
/

WCONINJE
  INJ01  WATER  OPEN  RATE  7000  1*  5000 /
/
```

#### C.1.4 Schedule — Annual Reporting (33 dates)

```
DATES
  1 JAN 2018 /
  1 JAN 2019 /
  1 JAN 2020 /
  ... (continues annually)
  1 JAN 2049 /
  1 JAN 2050 /
/

END
```

#### C.1.5 Validation Checklist (Exercise 1-Specific)

| Check | Expected Value |
|-------|---------------|
| Total cells | 300 (10×10×3) |
| Initial pressure | 3600 psia |
| OOIP | ~1.1–1.3 MM STB |
| Oil production start | Near 5000 STB/day |
| Water injection start | 7000 STB/day |
| FWCT trend | Increases over time |
| Layer 2 breakthrough | First (highest perm) |
| Simulation end | 1 JAN 2050 |

### C.2 Exercise 2: CO2-WAG Compositional (ADVANCED)

**Grid:** 25×25×10 = 6,250 cells, DX=DY=10 ft, DZ variable (1–50 ft)
**Pattern:** 6.25-acre sector model (250 ft × 250 ft), line drive
**Phases:** Oil + Water + Gas (7-component Peng-Robinson, DISGAS)
**Components:** CO2, C1N2, C2C3H2S, C4-C6, C7-C10, C11-C16, C17+
**Wells:** PROD at (1,1), INJE at (25,25), both K1-K2=1-10
**Duration:** 1 JAN 2010 – 1 JAN 2021 (11 years)
**Expected RF:** 40–60% for miscible WAG

#### C.2.1 10-Layer Reservoir Architecture

| Layer | DZ (ft) | PORO | PERMX (mD) | Role |
|-------|---------|------|------------|------|
| 1 | 1.0 | 0.05 | 0.01 | **Barrier** — sealing |
| 2 | 2.0 | 0.10 | 5.00 | Tight |
| 3 | 5.0 | 0.15 | 10.00 | Moderate |
| 4 | 8.0 | 0.18 | 20.00 | Good pay |
| 5 | 10.0 | 0.20 | 25.00 | Good pay |
| 6 | 7.0 | 0.12 | 8.00 | Moderate-tight |
| 7 | 50.0 | 0.20 | 30.00 | **Primary flow unit** — 54% of gross thickness |
| 8 | 1.0 | 0.05 | 0.01 | **Barrier** — sealing |
| 9 | 5.0 | 0.15 | 10.00 | Moderate |
| 10 | 4.0 | 0.10 | 5.00 | Tight |

**Total gross thickness:** 93 ft
**Vertical anisotropy:** Kv/Kh = 0.01 (strong) → prevents vertical CO2 migration
**Key insight:** Layer 7 dominates flow (50 ft, 30 mD, 20% porosity). Barriers at Layers 1 and 8 compartmentalize the reservoir.

#### C.2.2 GRID Assignment via EQUALS

```
EQUALS
-- DZ assignments per layer
  DZ   1.000   1  25  1  25   1   1 /
  DZ   2.000   1  25  1  25   2   2 /
  DZ   5.000   1  25  1  25   3   3 /
  DZ   8.000   1  25  1  25   4   4 /
  DZ  10.000   1  25  1  25   5   5 /
  DZ   7.000   1  25  1  25   6   6 /
  DZ  50.000   1  25  1  25   7   7 /
  DZ   1.000   1  25  1  25   8   8 /
  DZ   5.000   1  25  1  25   9   9 /
  DZ   4.000   1  25  1  25  10  10 /
-- PORO assignments per layer
  PORO  0.050   1  25  1  25   1   1 /
  PORO  0.100   1  25  1  25   2   2 /
  PORO  0.150   1  25  1  25   3   3 /
  PORO  0.180   1  25  1  25   4   4 /
  PORO  0.200   1  25  1  25   5   5 /
  PORO  0.120   1  25  1  25   6   6 /
  PORO  0.200   1  25  1  25   7   7 /
  PORO  0.050   1  25  1  25   8   8 /
  PORO  0.150   1  25  1  25   9   9 /
  PORO  0.100   1  25  1  25  10  10 /
-- PERMX assignments per layer
  PERMX   0.01  1  25  1  25   1   1 /
  PERMX   5.00  1  25  1  25   2   2 /
  PERMX  10.00  1  25  1  25   3   3 /
  PERMX  20.00  1  25  1  25   4   4 /
  PERMX  25.00  1  25  1  25   5   5 /
  PERMX   8.00  1  25  1  25   6   6 /
  PERMX  30.00  1  25  1  25   7   7 /
  PERMX   0.01  1  25  1  25   8   8 /
  PERMX  10.00  1  25  1  25   9   9 /
  PERMX   5.00  1  25  1  25  10  10 /
/
```

#### C.2.3 EQUIL & Initial Conditions

```
EQUIL
-- Datum(ft) Pdat(psia) OWC(ft) Pcow  GOC(ft) Pcgo
   4000      3000       5000    0     0       0    /
```
**Note:** OWC at 5000 ft is far below reservoir (max depth ~4093 ft) → undersaturated, 100% oil initially, no gas cap.

```
TEMPVD
-- Depth(ft)  Temperature(°F)
   4000        104
   5000        104  /
```
**Isothermal reservoir** — no temperature gradient modeled.

```
STCOND
  60.0  14.70 /

FIELDSEP
  1  60.0  14.70 /
/
```

#### C.2.4 Well Controls — Compositional

```
WELSPECS
  PROD  G1   1   1   4000  OIL /
  INJE  G1  25  25   4000  WATER /
/

COMPDAT
  PROD   1   1   1  10  OPEN  2*  0.1  3*  Z  1* /
  INJE  25  25   1  10  OPEN  2*  0.1  3*  Z  1* /
/

-- Initial waterflood
WCONPROD
  PROD  OPEN  RESV  5*  1000 /
/

WCONINJE
  INJE  WATER  OPEN  BHP  2*  3000 /
/
```
**Note:** Producer uses RESV (reservoir voidage replacement) control — not ORAT. Injector uses BHP control at 3000 psia — not RATE.

#### C.2.5 Injection Gas Stream Definition

```
WELLSTRE
  PURECO2  1.0  0.0  0.0  0.0  0.0  0.0  0.0 /
/
```
**100% pure CO2** — all mole fraction assigned to component 1 (CO2). The remaining 6 component slots are zero.

#### C.2.6 Complete WAG Schedule (20 Half-Cycles)

```
-- Phase 1: Initial Waterflood (12 months)
WCONINJE
  INJE  WATER  OPEN  BHP  2*  3000 /
/
DATES
  1 JUL 2010 /
  1 JAN 2011 /
/

-- WAG Cycle 1: Gas (6 months)
WINJGAS
  INJE  STREAM  PURECO2 /
/
WCONINJE
  INJE  GAS  OPEN  BHP  2*  3000 /
/
DATES
  1 JUL 2011 /
/

-- WAG Cycle 1: Water (6 months)
WCONINJE
  INJE  WATER  OPEN  BHP  2*  3000 /
/
DATES
  1 JAN 2012 /
/

-- WAG Cycle 2: Gas (6 months)
WINJGAS
  INJE  STREAM  PURECO2 /
/
WCONINJE
  INJE  GAS  OPEN  BHP  2*  3000 /
/
DATES
  1 JUL 2012 /
/

-- WAG Cycle 2: Water (6 months)
WCONINJE
  INJE  WATER  OPEN  BHP  2*  3000 /
/
DATES
  1 JAN 2013 /
/

-- WAG Cycles 3-10 follow identical pattern:
-- Gas:  WINJGAS + WCONINJE GAS OPEN BHP → DATES +6 months
-- Water: WCONINJE WATER OPEN BHP → DATES +6 months
-- Final dates: 1 JUL 2013, 1 JAN 2014, ... 1 JUL 2020, 1 JAN 2021

END
```

**Schedule Summary Table:**

| Phase | Start | End | Duration | Injection Type |
|-------|-------|-----|----------|---------------|
| Initial Waterflood | JAN 2010 | DEC 2010 | 12 months | WATER |
| WAG Cycle 1 Gas | JAN 2011 | JUN 2011 | 6 months | CO2 (PURECO2) |
| WAG Cycle 1 Water | JUL 2011 | DEC 2011 | 6 months | WATER |
| WAG Cycle 2 Gas | JAN 2012 | JUN 2012 | 6 months | CO2 (PURECO2) |
| WAG Cycle 2 Water | JUL 2012 | DEC 2012 | 6 months | WATER |
| ... | ... | ... | ... | ... |
| WAG Cycle 10 Gas | JAN 2020 | JUN 2020 | 6 months | CO2 (PURECO2) |
| WAG Cycle 10 Water | JUL 2020 | DEC 2020 | 6 months | WATER |

**Total:** 12 months waterflood + 10 × 12 months WAG = 132 months = 11 years

#### C.2.7 Physical Interpretation — CO2-WAG

- **Reservoir character:** 6.25-acre sector, 93 ft gross pay, Layer 7 = dominant flow unit
- **Oil composition:** Moderately heavy (2.34% CO2, 20.88% C1, 16.95% C17+)
- **Initial conditions:** 3000 psia, undersaturated, no gas cap
- **WAG rationale:** Waterflood first establishes pressure support. CO2 slugs mobilize residual oil via miscibility. Water slugs control gas mobility and maintain pressure.
- **Expected behavior:** Early oil production from Layer 7; CO2 breakthrough in Layer 7 first; water alternation controls gas mobility; barriers (Layers 1, 8) prevent vertical CO2 migration
- **Recovery target:** 40–60% for miscible WAG vs. ~30% waterflood only

#### C.2.8 Validation Checklist (Exercise 2-Specific)

| Check | Expected |
|-------|----------|
| Total cells | 6,250 (25×25×10) |
| Components defined | 7 |
| EOS solves | No convergence errors |
| Initial pressure | 3000 psia at datum |
| Initial composition | Matches ZMFVD (sum ≈ 1.0) |
| WAG cycles execute | Gas/water switching works |
| CO2 injection | Occurs during gas phases only |
| Simulation end | 1 JAN 2021 |

### C.3 Complete 5×5×1 Reference Model (.DATA Template)

This is the simplest complete Eclipse/tNavigator model — useful as a syntax reference.

```
-- ============================================
-- SIMPLE BLACK OIL WATERFLOOD MODEL
-- 5x5x1 grid, 2-phase (Oil + Water)
-- ============================================

RUNSPEC
TITLE
SIMPLE 5X5 WATERFLOOD MODEL

DIMENS
  5  5  1 /

OIL
WATER
FIELD

START
  1 JAN 2020 /

TABDIMS
  1  1  20  20 /

WELLDIMS
  2  1  1  2 /

-- ============================================
GRID

DX
  25*100 /

DY
  25*100 /

DZ
  25*20 /

TOPS
  25*4000 /

PORO
  25*0.20 /

PERMX
  25*200 /

COPY
  PERMX  PERMY /
/

MULTIPLY
  PERMZ  0.01 /
/

-- ============================================
PROPS

DENSITY
  45.0  64.0  0.044 /

PVDO
  1000  1.200  1.20
  2000  1.100  1.10
  3000  1.040  1.00
  4000  1.018  0.97
  5000  1.012  0.95  /

PVTW
  4000  1.01  3.0E-6  0.5  0 /

ROCK
  4000  4.0E-6 /

SWOF
  0.20  0.00  0.60  0
  0.30  0.03  0.45  0
  0.40  0.05  0.33  0
  0.50  0.08  0.20  0
  0.60  0.13  0.10  0
  0.70  0.22  0.00  0
  1.00  1.00  0.00  0  /

-- ============================================
SOLUTION

EQUIL
  4000  3600  4100  0  0  0 /

-- ============================================
SUMMARY

FOPR
FOPT
FWPR
FWPT
FWIR
FWIT
FPR
FOIP
FWCT

-- ============================================
SCHEDULE

WELSPECS
  PROD  G1  1  1  4000  OIL /
  INJ1  G1  5  5  4000  WATER /
/

COMPDAT
  PROD  1  1  1  1  OPEN  2*  0.3 /
  INJ1  5  5  1  1  OPEN  2*  0.3 /
/

WCONPROD
  PROD  OPEN  ORAT  1000  4*  500 /
/

WCONINJE
  INJ1  WATER  OPEN  RATE  1500  1*  5000 /
/

TSTEP
  12*30.4167 /

TSTEP
  12*30.4167 /

TSTEP
  12*30.4167 /

END
```

### C.4 Complexity Progression

| Level | Description | Key Features |
|-------|-------------|--------------|
| 1 BEGINNER | 5×5×1 waterflood | File structure, basic keywords |
| 2 INTERMEDIATE | 10×10×3 layered | Heterogeneity, layer bypass, aquifers |
| 3 ADVANCED | Compositional WAG | EOS, ACTIONX, WELLSTRE, endpoint scaling |
| 4 EXPERT | Conformance control | Selective completions, NPV optimization |

---

## Part D: Debugging & Validation

### D.1 PRT File Debugging Methodology

1. Simulation fails → Open .PRT file
2. Search for "ERROR" or "WARNING"
3. Find line number and keyword
4. Go to location in .DATA file
5. Fix issue
6. Re-run

### D.2 Common Error Patterns

| Error Message | Cause | Fix |
|---------------|-------|-----|
| "Unexpected keyword" | Missing `/` terminator | Add slash after data entry |
| "Insufficient data" | Wrong array count | Check DIMENS (NX×NY×NZ) |
| "Non-monotonic" | PVDO Bo increasing with pressure | Bo MUST DECREASE |
| "Well outside grid" | I,J exceeds DIMENS | Check well I,J vs grid NX,NY |
| "No oil in place" | OWC above reservoir | Check EQUIL OWC vs TOPS depth |
| "Missing TABDIMS" | Custom rel perm tables undefined | Add TABDIMS to RUNSPEC |
| "SWOF at Sw=0" | Invalid table start | Must start at connate Sw |

### D.3 8-Point Validation Checklist

1. **OOIP matches hand calculation** (within 5%)
2. **Material balance:** `FOPT = FOIP(initial) - FOIP(final)`
3. **Pressure behavior:** Not negative, not increasing during production
4. **Water cut:** Increases over time (waterflood) or stays at Swc (depletion)
5. **Production rates:** Honor constraints (not exceeding ORAT limit)
6. **Injection ≈ Production** (approximately, for pressure maintenance)
7. **No NaN or Inf values** in output
8. **Simulation time reasonable** (not frozen at timestep 1)

### D.4 Compositional Validation (Exercise 2 additions)

| Check | Expected |
|-------|----------|
| 7 components defined correctly | ✓ |
| EOS solves without convergence errors | ✓ |
| Initial composition matches ZMFVD | ✓ |
| WAG cycles execute (gas/water switching) | ✓ |
| CO2 injection occurs during gas phases | ✓ |

### D.5 Certification Questions

| # | Question | Answer |
|---|----------|--------|
| 1 | First section? | RUNSPEC |
| 2 | Data entry terminator? | `/` (forward slash) |
| 3 | DIMENS 10 10 3 creates? | 10×10×3 grid (300 cells) |
| 4 | PORO specifies? | Porosity (fraction of rock = pore space) |
| 5 | PVDO: pressure↑ → Bo? | Bo DECREASES (oil compresses) |
| 6 | SWOF represents? | Water-oil relative perm vs water saturation |
| 7 | EQUIL calculates? | Initial pressures & saturations from equilibrium |
| 8 | WCONPROD ORAT means? | Oil rate control mode |
| 9 | TSTEP 365 does? | Advances simulation 365 days |
| 10 | Why section order? | Later sections reference data from earlier ones |

---

## Part E: Conformance Control & Economics

### E.1 Thief Zone Strategies

| Strategy | Description | Expected RF |
|----------|-------------|-------------|
| Baseline | Full completion, thief zone present | ~30% |
| Surgical Shutoff | Skip thief zone layer (e.g., layers 1-4, 6-10) | ~45-55% |
| Avoid Thief | Complete only non-thief layers | Variable |

### E.2 NPV Calculation

```
NPV = Σ (Revenue_n - Cost_n) / (1 + r)^n

Revenue_n = Oil_produced_year_n × $50/STB
Cost_n = (Water_injected + Water_produced) × $3/bbl
r = 0.10 (10% discount rate)
```
**Key insight:** Early oil worth more than late oil (time value of money).

### E.3 WAG Strategy Rationale

- 1-year waterflood establishes pressure support before CO2
- 6-month CO2 slugs mobilize residual oil (miscibility effect)
- 6-month water slugs maintain pressure and improve sweep efficiency
- Water alternation controls gas mobility
- Expected recovery: 40–60% for miscible WAG (vs. ~30% waterflood only)

---

## Part F: Infrastructure & File Paths

### F.1 Eclipse Manual Organization
**Base path:** `/home/matejkam/eclipse_claude_code/eclipse_manual_organized/`
```
eclipse_manual_organized/
├── 00_front_matter/
├── 02_data_file_overview/
└── 03_keywords/[A-Z]/
```

### F.2 Knowledge Persistence Protocol
**Folder:** `/home/matejkam/eclipse_claude_code/ORSA_TRAINEE_KNOWLEDGE/`

| File | Purpose |
|------|---------|
| TRAINING_LOG.md | Progress tracker with completion dates |
| MASTER_SUMMARY.md | Comprehensive knowledge summary |
| UNIT_XX_TOPIC.md | Per-unit learnings and corrections |
| TEST_BOOTSTRAP_001/ | Experiment folder with .DATA files |

### F.3 Reference Files
- Exercise 1 solution: `/home/matejkam/eclipse_claude_code/TEST_081425/SS_FIX_INJ_BHP_TNAV.DATA`
- Simplest model: `/home/matejkam/eclipse_claude_code/TEST_081425/MODEL_5X5.DATA`
- Reference manual files: `ECLIPSE_EXCEPTIONS.md`, `SCHEDULE_QUICKREF.md`, `SHAH_FIELD_SPECIFICS.md`

### F.4 tNavigator Solver Controls (Optional)

```
TNAVCTRL
  MODEL_E3  YES /
  WELLPRESTOL  1E-5 /
  CONVERGENCE_PROBLEM_NUM  5 /
  MIN_MOLAR_DENSITY_VALUE  1E-6 /
  SMOOTH_RP  YES /
  GPU_MODE  2 /
/

RUNCTRL
  DTMAX 3.0  DTMIN 0.001  DTINITIAL 0.01  DTPRED 1
  WELLEQUATIONS 1  WELLDENWEIGHT 0.5  CHECKP 2  NDTAVG 3  AIM 2
/

FLASHCTRL
  FL_V_PREC  0.0000005 /
/
```

---

## Part G: Quick Reference Card

### Essential Keywords by Section
- **RUNSPEC:** DIMENS, OIL, WATER, GAS, FIELD, START, COMPS, ENDSCALE, DISGAS
- **GRID:** DX, DY, DZ, TOPS, PORO, PERMX, COPY, MULTIPLY, EQUALS
- **PROPS:** DENSITY, PVDO, PVTW, ROCK, SWOF, SGOF, EOS, CNAMES, TCRIT, PCRIT, BIC, ZMFVD
- **SOLUTION:** EQUIL, SWATINIT, FIELDSEP
- **SUMMARY:** FOPR, FOPT, FWPR, FPR, FOIP, FWCT, WOPR, WBHP, WGOR, WGIR
- **SCHEDULE:** WELSPECS, COMPDAT, WCONPROD, WCONINJE, WELLSTRE, WINJGAS, TSTEP, DATES, END

### Material Balance Check
```
Oil_recovered = FOIP(initial) - FOIP(final)
Must equal FOPT (cumulative production)
```

### OOIP Hand Calculation (Volumetric Method)

```
OOIP (STB) = (NX × DX × NY × DY × NZ × DZ) × φ × (1 - Swc) / Bo

Where:
  NX, NY, NZ = grid dimensions (cells)
  DX, DY, DZ = cell sizes (ft)
  φ = porosity (fraction)
  Swc = connate water saturation (from SWOF first row Sw)
  Bo = formation volume factor at initial pressure (RB/STB)
```

**Exercise 1 Example:**
```
Bulk volume = 10 × 200 × 10 × 200 × 3 × 10 = 12,000,000 ft³
Average φ = (0.200 + 0.250 + 0.220) / 3 = 0.223
Swc = 0.20 (from SWOF)
Bo = 1.025 at 3600 psia (interpolated from PVDO)

OOIP = 12,000,000 × 0.223 × (1 - 0.20) / 1.025
     = 12,000,000 × 0.223 × 0.80 / 1.025
     = 2,089,756 ft³ / 1.025
     ≈ 2,087,567 RB → convert to STB via 1/Bo
     ≈ 1.28 MM STB  ✓ (matches expected 1.1–1.3 MM STB)
```

**Note:** For layered models, calculate per-layer and sum:
```
OOIP_total = Σ(layer=1 to NZ) [NX × DX × NY × DY × DZ_layer × φ_layer × (1 - Swc) / Bo]
```

### Units Conversion Reference (FIELD Units)

| Conversion | Formula |
|-----------|---------|
| ft² → acres | ÷ 43,560 |
| ft³ → barrels | ÷ 5.615 |
| bbl → STB | × (1 / Bo) |
| mD × ft → Transmissibility | × 0.00633 × (kA/μBo∆x) |
| psi → atm | ÷ 14.696 |
| °F → °R | + 459.67 |

### Pattern Sizing Quick Reference

| Pattern | Spacing (acres) | Side Length (ft) | Typical DX for 10×10 grid |
|---------|----------------|-----------------|--------------------------|
| 5-spot (quarter) | 10 | 660 | 66 ft/cell |
| 5-spot (full) | 40 | 1320 | 132 ft/cell |
| Line drive (pilot) | 10 | 660 | 66 ft/cell |
| Sector model | 6.25 | 522 | varies |

**Critical formula:** `Area (acres) = (NX × DX × NY × DY) / 43,560`

### Standard Workflow Template — Detailed 12-Step Procedure

**Phase I: Model Construction**
1. **Create .DATA file** following mandatory section order: RUNSPEC → GRID → PROPS → SOLUTION → SUMMARY → SCHEDULE
2. **Define grid geometry** — choose DX/DY/DZ based on pattern size (10 acres = ~660 ft side for 5-spot, ~200 ft/cell for 10×10). Verify: `total_area_ft2 = NX × DX × NY × DY`, convert to acres (÷ 43,560)
3. **Assign rock properties** — PORO, PERMX per layer; COPY PERMX→PERMY; MULTIPLY PERMZ × Kv/Kh ratio (typically 0.01–0.1)
4. **Build PVT tables** — DENSITY, PVDO (or PVTO for live oil), PVTW, ROCK. **Verify Bo monotonicity before running**
5. **Build relative permeability** — SWOF (and SGOF if gas present). Verify: first row Krw=0, last row Krow=0. Endpoints must be consistent with SCAL data

**Phase II: Initialization & Wells**
6. **Set EQUIL** — datum depth matching TOPS, initial pressure, OWC/GOC positions. OWC below reservoir → 100% oil
7. **Define SUMMARY vectors** — minimum: FOPR, FOPT, FWPR, FPR, FOIP. Add well-level (WOPR, WBHP, WWCT) for diagnostics
8. **Place wells** — WELSPECS (I,J position), COMPDAT (K1-K2 completion interval), WCONPROD/WCONINJE (controls). Verify: well I,J within DIMENS NX,NY

**Phase III: Execution & Validation**
9. **Validate syntax** — check all `/` terminators, verify array counts match NX×NY×NZ, ensure keyword spelling (all caps)
10. **Run simulation** — `csh` shell for tNavigator; check for .PRT output file
11. **Debug if needed** — search .PRT for "ERROR"/"WARNING", find line number, fix .DATA file, re-run
12. **Validate results** — apply 8-point checklist: (1) OOIP within 5% of hand calc, (2) material balance closes, (3) pressure reasonable, (4) water cut trend correct, (5) rates honor constraints, (6) injection ≈ production, (7) no NaN/Inf, (8) simulation completes

### Self-Directed Training Protocol — Session Workflow

This protocol defines how CLARISSA trains itself on new reservoir models.

**Pre-Session:**
1. Read the `.DATA` file completely before modifying anything
2. Identify the 5 sections and their contents
3. Note grid dimensions, phases, number of wells
4. Check for INCLUDE files

**During Session (PROMPT/EXPECTED/CHECKPOINT pedagogy):**
1. **PROMPT:** Trainer poses specific question about the model
2. **EXPECTED:** Correct answer provided for self-check
3. **CHECKPOINT:** Gating criterion — if understood, proceed; if not, revisit

**Knowledge Persistence (after each session):**
1. Update `TRAINING_LOG.md` with completion date and topics
2. Create `UNIT_XX_TOPIC.md` with key learnings
3. Document any corrections or anti-patterns discovered
4. Save modified `.DATA` files in `TEST_BOOTSTRAP_001/` folder

### Eclipse Reference Manual Usage Protocol

**Philosophy:** Trust Eclipse knowledge (90% accurate), only check files when stuck.

**Three reference files for when stuck:**
1. `ECLIPSE_EXCEPTIONS.md` — known deviations from standard syntax
2. `SCHEDULE_QUICKREF.md` — quick reference for SCHEDULE keywords
3. `SHAH_FIELD_SPECIFICS.md` — field-specific configurations

**Before using unfamiliar keywords:** READ the keyword's `.md` file in `03_keywords/[LETTER]/`, study examples, verify syntax.

---

*End of SSOT — Version 1.1*
