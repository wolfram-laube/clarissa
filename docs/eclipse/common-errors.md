# Common ECLIPSE Errors

This document catalogs common ECLIPSE deck errors and their solutions.
Essential reference for CLARISSA's debugging capabilities (ORSA Phase 1).

## Syntax Errors

### Missing Terminator

**Error:**
```
@--  ERROR AT LINE   125
@--  KEYWORD 'WELSPECS' REQUIRES RECORD TERMINATION
```

**Cause:** Missing `/` at end of record or keyword.

**Wrong:**
```
WELSPECS
PROD1 G1 50 50 8500 OIL
```

**Correct:**
```
WELSPECS
PROD1 G1 50 50 8500 OIL /
/
```

---

### Unexpected End of File

**Error:**
```
@--  ERROR AT LINE  1523
@--  UNEXPECTED END OF FILE IN KEYWORD 'SCHEDULE'
```

**Cause:** Missing `END` keyword or unclosed record.

**Solution:** Add `END` at end of SCHEDULE section:
```
TSTEP
365 /

END
```

---

### Invalid Keyword Spelling

**Error:**
```
@--  ERROR AT LINE    45
@--  KEYWORD 'WELSPEC' NOT RECOGNIZED
```

**Cause:** Typo in keyword name.

**Common Typos:**
| Wrong | Correct |
|-------|---------|
| WELSPEC | WELSPECS |
| COMDAT | COMPDAT |
| WCONPRD | WCONPROD |
| PVTDO | PVDO |
| DIMNS | DIMENS |

---

### Wrong Number of Values

**Error:**
```
@--  ERROR AT LINE   234
@--  KEYWORD 'DIMENS' EXPECTS 3 VALUES, FOUND 2
```

**Wrong:**
```
DIMENS
100 100 /
```

**Correct:**
```
DIMENS
100 100 20 /
```

---

## Grid Errors

### Negative Cell Volume

**Error:**
```
@--  WARNING: CELL (45, 23, 5) HAS NEGATIVE VOLUME
@--  CHECK CORNER POINT GEOMETRY
```

**Causes:**
1. Inverted corners in ZCORN
2. Crossing pillars in COORD
3. Inconsistent grid include files

**Solutions:**
1. Check ZCORN ordering (should increase with depth)
2. Verify COORD pillar definitions
3. Visualize grid in external tool (ResInsight)

---

### Cells with Zero Pore Volume

**Error:**
```
@--  WARNING: 234 CELLS HAVE ZERO PORE VOLUME
@--  THESE CELLS WILL BE DEACTIVATED
```

**Causes:**
1. PORO = 0 for some cells
2. NTG = 0 for some cells
3. Very thin cells (DZ ≈ 0)

**Solutions:**
```
-- Set minimum pore volume
MINPV
1.0 /           -- Minimum 1 rb per cell

-- Or fix porosity
PORO
10000*0.01 /    -- Ensure non-zero
```

---

### Missing ACTNUM

**Warning:**
```
@--  NO ACTNUM SPECIFIED - ALL CELLS ACTIVE
```

**Note:** Not an error, but can cause performance issues with inactive cells.

**Solution:**
```
ACTNUM
-- 0 = inactive, 1 = active
5000*1 5000*0 /    -- Deactivate half the grid
```

---

## PVT Errors

### Non-Monotonic Table

**Error:**
```
@--  ERROR IN PVTO TABLE AT LINE 345
@--  PRESSURE MUST INCREASE MONOTONICALLY
```

**Wrong:**
```
PVTO
0.5  1000  1.2  0.5
0.5  800   1.18 0.52    -- Pressure decreased!
0.5  1200  1.22 0.48 /
/
```

**Correct:**
```
PVTO
0.5  800   1.18 0.52
0.5  1000  1.2  0.5
0.5  1200  1.22 0.48 /
/
```

---

### Relative Permeability Not Normalized

**Error:**
```
@--  WARNING: KRWMAX IN SWOF TABLE NOT EQUAL TO 1.0
```

**Common Issues:**
1. Krw(Sw=1) ≠ 1
2. Krow(Sw=Swc) ≠ 1
3. Krg(Sg=1-Swc) ≠ 1

**Correct Table Structure:**
```
SWOF
-- Sw    Krw   Krow  Pcow
   0.2   0     1     0      -- Swc: Krow = 1
   0.4   0.05  0.5   0
   0.6   0.2   0.2   0
   0.8   0.5   0.05  0
   1.0   1     0     0 /    -- Sw=1: Krw = 1
```

---

### Missing Bubble Point Data

**Error:**
```
@--  ERROR: UNDERSATURATED OIL DATA MISSING FOR Rs = 0.65
```

**Cause:** PVTO table doesn't cover the required Rs range.

**Solution:** Extend PVTO table or add undersaturation data:
```
PVTO
-- Rs    P      Bo     Visc
   0.5   1000   1.2    0.8
         2000   1.19   0.85
         3000   1.18   0.9  /    -- Undersaturated
   0.65  1500   1.25   0.75
         2500   1.24   0.78
         3500   1.23   0.82 /
/
```

---

## Well Errors

### Well Not in Grid

**Error:**
```
@--  ERROR: WELL 'PROD1' AT (150, 50) IS OUTSIDE GRID
@--  GRID DIMENSIONS ARE (100, 100, 20)
```

**Cause:** Well I,J coordinates exceed grid dimensions.

**Solution:** Check WELSPECS coordinates:
```
WELSPECS
-- Name  Group  I    J    RefDepth  Phase
-- I and J must be <= NX, NY in DIMENS
   PROD1 G1     50   50   8500      OIL /
/
```

---

### No Perforated Cells

**Error:**
```
@--  WARNING: WELL 'PROD1' HAS NO OPEN CONNECTIONS
```

**Causes:**
1. COMPDAT layers don't exist
2. All connection cells are inactive
3. Wrong I,J in COMPDAT

**Solution:**
```
COMPDAT
-- Well  I  J  K1 K2 Open
-- Ensure K1-K2 range contains active cells
   PROD1 50 50 1  10 OPEN /    -- Layers 1-10
/
```

---

### BHP Below Bubble Point

**Warning:**
```
@--  WARNING: WELL 'PROD1' BHP (1200 PSIA) BELOW BUBBLE POINT (1500 PSIA)
@--  FREE GAS MAY OCCUR IN WELLBORE
```

**Cause:** BHP constraint too low for reservoir fluid.

**Solutions:**
1. Raise BHP limit:
   ```
   WCONPROD
   PROD1 OPEN ORAT 1000 4* 1600 /    -- Higher BHP
   /
   ```
2. Accept gas production (if intentional)

---

## Schedule Errors

### Well Used Before Definition

**Error:**
```
@--  ERROR AT LINE 1234
@--  WELL 'PROD2' REFERENCED IN WCONPROD BUT NOT DEFINED
```

**Cause:** Using well before WELSPECS.

**Wrong Order:**
```
SCHEDULE

WCONPROD
PROD1 OPEN ORAT 1000 /    -- Error: PROD1 not defined yet
/

WELSPECS
PROD1 G1 50 50 8500 OIL /
/
```

**Correct Order:**
```
SCHEDULE

WELSPECS
PROD1 G1 50 50 8500 OIL /
/

COMPDAT
PROD1 50 50 1 10 OPEN /
/

WCONPROD
PROD1 OPEN ORAT 1000 /
/
```

---

### Date Going Backwards

**Error:**
```
@--  ERROR: DATE '1 JAN 2025' IS BEFORE CURRENT DATE '1 FEB 2025'
```

**Cause:** Dates not in chronological order.

**Wrong:**
```
DATES
1 FEB 2025 /
/

TSTEP
30 /

DATES
1 JAN 2025 /    -- Error: Before Feb!
/
```

**Correct:**
```
DATES
1 JAN 2025 /
1 FEB 2025 /
1 MAR 2025 /
/
```

---

## Convergence Errors

### Linear Solver Failure

**Error:**
```
@--  WARNING: LINEAR SOLVER FAILED TO CONVERGE
@--  ITERATION 50, RESIDUAL = 1.23E+05
```

**Causes:**
1. Bad initial guess (poor initialization)
2. Very heterogeneous permeability
3. Timestep too large

**Solutions:**
1. Improve equilibration:
   ```
   EQUIL
   -- Use more accurate initial conditions
   8500 4000 9000 0 8000 0 1 1 20 /
   --                       ^^ More iterations
   ```
2. Reduce timestep:
   ```
   TSTEP
   1 2 5 10 20 30 /    -- Ramp up gradually
   ```

---

### Newton Convergence Failure

**Error:**
```
@--  WARNING: NEWTON ITERATION FAILED
@--  MAX SATURATION CHANGE = 0.45 (LIMIT = 0.2)
```

**Causes:**
1. Large saturation changes
2. Discontinuous rel-perm curves
3. Numerical instability

**Solutions:**
1. Tighten timestep control
2. Smooth relative permeability tables
3. Add numerical controls (if available):
   ```
   TUNING
   1 5 0.1 /    -- Smaller initial timestep
   /
   /
   ```

---

## Error Categories for Training

| Category | Examples | Training Priority |
|----------|----------|-------------------|
| Syntax | Missing /, typos | High - common, fixable |
| Grid | Negative volume, zero PV | Medium - need geometry check |
| PVT | Non-monotonic, missing data | High - common in new decks |
| Wells | Outside grid, no connections | High - frequent user errors |
| Schedule | Order issues, date errors | High - common mistakes |
| Convergence | Solver failures | Medium - need parameter tuning |

## See Also

- [Deck Structure](deck-structure.md) - Proper organization
- [Keyword Reference](keyword-reference.md) - Correct syntax
- ORSA Proposal - Phase 1 debugging objectives