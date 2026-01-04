# ECLIPSE Keyword Reference

Quick reference für die wichtigsten ECLIPSE Keywords die CLARISSA generieren muss.

## Well Definition

### WELSPECS - Well Specification
```
WELSPECS
-- Name  Group  I   J   Depth  Phase
  'PROD1' 'G1'  10  10  2500   'OIL' /
  'INJ1'  'G1'  1   1   2500   'WATER' /
/
```

### COMPDAT - Completion Data
```
COMPDAT
-- Well   I   J  K1  K2  Status  Sat  TranFac  Diam  Kh    Skin  Dir
  'PROD1' 10  10  1   5  'OPEN'  1*   1*       0.5   1*    0     'Z' /
/
```

## Production Control

### WCONPROD - Producer Control
```
WCONPROD
-- Well   Status  Mode  OilRate  WaterRate  GasRate  LiqRate  ResvRate  BHP
  'PROD1' 'OPEN'  'ORAT' 500      1*         1*       1*       1*       1000 /
/
```

**Control Modes:**
- `ORAT` - Oil rate target
- `WRAT` - Water rate target
- `GRAT` - Gas rate target
- `LRAT` - Liquid rate target
- `RESV` - Reservoir volume rate
- `BHP` - Bottom hole pressure

### WCONINJE - Injector Control
```
WCONINJE
-- Well   Type    Status  Mode  Rate    ResvRate  BHP
  'INJ1'  'WATER' 'OPEN'  'RATE' 1000   1*        5000 /
/
```

**Injection Types:**
- `WATER` - Water injection
- `GAS` - Gas injection
- `OIL` - Oil injection (rare)

## Schedule Control

### DATES - Simulation Dates
```
DATES
  1 'JAN' 2025 /
  1 'FEB' 2025 /
  1 'MAR' 2025 /
/
```

### TSTEP - Timesteps
```
TSTEP
  30 30 30 /  -- Three 30-day steps
/
```

## Well Operations

### WELOPEN - Open/Close Wells
```
WELOPEN
-- Well   Status  I  J  K1  K2  Comp
  'PROD1' 'SHUT' /
  'INJ1'  'OPEN' /
/
```

### WELTARG - Well Targets
```
WELTARG
-- Well   Control  Value
  'PROD1' 'ORAT'   750 /
  'INJ1'  'RATE'   1200 /
/
```

## Common Patterns

### Rate Change
```
-- Änderung der Produktionsrate
WELTARG
  'PROD1' 'ORAT' 500 /
/
```

### Well Shut-In
```
WELOPEN
  'PROD1' 'SHUT' /
/
```

### New Producer
```
WELSPECS
  'PROD2' 'G1' 15 15 2500 'OIL' /
/
COMPDAT
  'PROD2' 15 15 1 5 'OPEN' /
/
WCONPROD
  'PROD2' 'OPEN' 'ORAT' 300 /
/
```

### New Injector
```
WELSPECS
  'INJ2' 'G1' 5 5 2500 'WATER' /
/
COMPDAT
  'INJ2' 5 5 1 5 'OPEN' /
/
WCONINJE
  'INJ2' 'WATER' 'OPEN' 'RATE' 800 /
/
```

## Units

### Metric vs Field

| Quantity | Field | Metric |
|----------|-------|--------|
| Length | ft | m |
| Pressure | psi | bar, kPa |
| Oil Rate | STB/day | SM3/day |
| Gas Rate | MSCF/day | SM3/day |
| Water Rate | STB/day | SM3/day |

### Unit Conversion (im Code)
```python
# STB/day to SM3/day
rate_metric = rate_field * 0.158987

# psi to bar
pressure_bar = pressure_psi * 0.0689476

# psi to kPa
pressure_kpa = pressure_psi * 6.89476
```

## Validation Rules

1. **Well must exist** before WCONPROD/WCONINJE
2. **Completions required** before production
3. **Date must advance** (no backwards time)
4. **Rate must be positive**
5. **BHP must be reasonable** (typically 500-10000 psi)
6. **Grid indices must be valid** (within DIMENS)
---

## Group Operations (IRENA Contribution)

### GRUPTREE - Group Hierarchy Definition

Defines the hierarchy of production or injection groups in the field.

#### Syntax
```eclipse
GRUPTREE
-- Child     Parent
  'GROUP1'   'FIELD' /
  'GROUP2'   'GROUP1' /
/
```

| Parameter | Description |
|-----------|-------------|
| Child | Name of the subgroup |
| Parent | Name of the parent group or FIELD |

#### Example: Multi-level hierarchy
```eclipse
GRUPTREE
  'NORTH'    'FIELD' /
  'SOUTH'    'FIELD' /
  'PLATFORM_A' 'NORTH' /
  'PLATFORM_B' 'NORTH' /
/
```

---

### GCONPROD - Group Production Control

Controls production targets for an entire group of wells.

#### Syntax
```eclipse
GCONPROD
-- Group   Status  Control  OilRate  WaterRate  GasRate  LiqRate  ResvRate  BHP
  'GROUP1' 'OPEN'  'ORAT'   10000    1*         1*       1*       1*        500 /
/
```

| Parameter | Values | Description |
|-----------|--------|-------------|
| Group | string | Group name |
| Status | OPEN/SHUT | Group status |
| Control | ORAT/WRAT/GRAT/LRAT/RESV/BHP | Control mode |
| Rates | number or 1* | Target rates (1* = no limit) |

#### Control Modes
- `ORAT` - Oil rate control
- `WRAT` - Water rate control  
- `GRAT` - Gas rate control
- `LRAT` - Liquid rate control
- `RESV` - Reservoir volume rate control
- `BHP` - Bottom-hole pressure control

---

### GCONINJE - Group Injection Control

Controls injection rates at the group level.

#### Syntax
```eclipse
GCONINJE
-- Group   Type    Status  Mode   Rate   ResvRate  BHP
  'GROUP1' 'WATER' 'OPEN'  'RATE' 5000   1*        3000 /
/
```

| Parameter | Values | Description |
|-----------|--------|-------------|
| Group | string | Injection group name |
| Type | WATER/GAS/OIL | Injection fluid type |
| Status | OPEN/SHUT | Group status |
| Mode | RATE/RESV/BHP | Control mode |
| Rate | number | Surface injection rate |
| BHP | number | Max bottom-hole pressure |

#### Example: Water injection group
```eclipse
GCONINJE
  'NORTH_INJ' 'WATER' 'OPEN' 'RATE' 15000 1* 4500 /
  'SOUTH_INJ' 'WATER' 'OPEN' 'RATE' 12000 1* 4500 /
/
```