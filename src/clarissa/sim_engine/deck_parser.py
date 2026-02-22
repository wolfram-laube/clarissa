"""Eclipse Deck Parser — .DATA file → SimRequest.

Parses Eclipse-format simulation decks (as used by OPM Flow) and extracts
grid, well, fluid, and schedule information into CLARISSA's SimRequest model.

This is NOT a full Eclipse parser — it handles the subset of keywords needed
for CLARISSA's contract testing and deck validation. For production use,
consider opm.io.Parser or resdata.

Supported keywords:
  RUNSPEC: DIMENS, OIL/GAS/WATER, FIELD/METRIC, TITLE
  GRID:    DX/DY/DZ, TOPS, PORO, PERMX/PERMY/PERMZ
  PROPS:   DENSITY, PVTW (basic fluid properties)
  SCHEDULE: WELSPECS, COMPDAT, WCONPROD, WCONINJE, TSTEP
  SOLUTION: EQUIL

Issue #173 | Epic #161 | ADR-040
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Optional

from clarissa.sim_engine.models import (
    FluidProperties,
    GridParams,
    Phase,
    SimRequest,
    WellConfig,
    WellType,
)

logger = logging.getLogger(__name__)


# ─── Unit Conversion ──────────────────────────────────────────────────────

def _ft_to_m(ft: float) -> float:
    return ft * 0.3048

def _psi_to_bar(psi: float) -> float:
    return psi * 0.0689476

def _stbd_to_m3d(stbd: float) -> float:
    """Stock tank barrels/day → m³/day."""
    return stbd * 0.158987

def _mscfd_to_m3d(mscfd: float) -> float:
    """Mscf/day → m³/day (at standard conditions)."""
    return mscfd * 28.3168


# ─── Token Stream ─────────────────────────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    """Tokenize Eclipse deck, stripping comments and expanding N*val."""
    lines = []
    for line in text.splitlines():
        # Strip comments (-- to end of line)
        idx = line.find("--")
        if idx >= 0:
            line = line[:idx]
        line = line.strip()
        if line:
            lines.append(line)

    joined = " ".join(lines)
    raw_tokens = joined.split()

    # Expand repeat notation: 300*1000 → [1000, 1000, ...]
    tokens = []
    for t in raw_tokens:
        if "*" in t and not t.startswith("'"):
            parts = t.split("*", 1)
            try:
                count = int(parts[0])
                val = parts[1] if parts[1] else ""
                if val:
                    tokens.extend([val] * count)
                else:
                    # N* means "use default N times" — keep as placeholder
                    tokens.extend(["1*"] * count)
            except ValueError:
                tokens.append(t)
        else:
            tokens.append(t)

    return tokens


def _find_keyword(tokens: list[str], keyword: str) -> int:
    """Find index of keyword in token list. Returns -1 if not found."""
    kw_upper = keyword.upper()
    for i, t in enumerate(tokens):
        if t.upper() == kw_upper:
            return i
    return -1


def _extract_record(tokens: list[str], start: int) -> tuple[list[str], int]:
    """Extract tokens from start until next '/' terminator.

    Returns (record_tokens, index_after_slash).
    """
    record = []
    i = start
    while i < len(tokens):
        t = tokens[i]
        if t == "/":
            return record, i + 1
        # Handle tokens ending with / like "0.5 /"
        if t.endswith("/"):
            record.append(t[:-1])
            return record, i + 1
        record.append(t)
        i += 1
    return record, i


def _extract_records(tokens: list[str], start: int, count: int = -1) -> list[list[str]]:
    """Extract multiple /-terminated records."""
    records = []
    i = start
    while i < len(tokens) and (count < 0 or len(records) < count):
        # Skip if we hit another keyword (all-caps, no quotes, no numbers)
        t = tokens[i]
        if t == "/":
            # Empty record
            records.append([])
            i += 1
            continue
        if re.match(r"^[A-Z]{2,}$", t) and t not in ("OIL", "GAS", "WATER"):
            break

        record, i = _extract_record(tokens, i)
        if record or True:  # include empty records
            records.append(record)
    return records


# ─── Main Parser ──────────────────────────────────────────────────────────

class DeckParseResult:
    """Result of parsing an Eclipse deck."""

    def __init__(self):
        self.title: str = ""
        self.units: str = "FIELD"  # FIELD or METRIC
        self.nx: int = 0
        self.ny: int = 0
        self.nz: int = 0
        self.phases: list[str] = []

        # Grid
        self.dx_values: list[float] = []
        self.dy_values: list[float] = []
        self.dz_values: list[float] = []
        self.tops_values: list[float] = []
        self.poro_values: list[float] = []
        self.permx_values: list[float] = []
        self.permy_values: list[float] = []
        self.permz_values: list[float] = []

        # Wells
        self.welspecs: list[dict] = []
        self.compdat: list[dict] = []
        self.wconprod: list[dict] = []
        self.wconinje: list[dict] = []

        # Schedule
        self.tstep_values: list[float] = []

        # Fluid
        self.density: dict = {}
        self.pvtw: dict = {}
        self.equil: list[float] = []

    @property
    def total_cells(self) -> int:
        return self.nx * self.ny * self.nz

    @property
    def is_field(self) -> bool:
        return self.units == "FIELD"


def parse_deck(text: str) -> DeckParseResult:
    """Parse Eclipse deck text into DeckParseResult."""
    result = DeckParseResult()
    tokens = _tokenize(text)

    # Units
    if _find_keyword(tokens, "FIELD") >= 0:
        result.units = "FIELD"
    elif _find_keyword(tokens, "METRIC") >= 0:
        result.units = "METRIC"

    # Phases
    for phase in ("OIL", "GAS", "WATER"):
        if _find_keyword(tokens, phase) >= 0:
            result.phases.append(phase)

    # TITLE
    idx = _find_keyword(tokens, "TITLE")
    if idx >= 0 and idx + 1 < len(tokens):
        # Title is everything until next keyword
        title_parts = []
        i = idx + 1
        while i < len(tokens) and not re.match(r"^[A-Z]{2,}$", tokens[i]):
            title_parts.append(tokens[i].strip("'"))
            i += 1
        result.title = " ".join(title_parts)

    # DIMENS
    idx = _find_keyword(tokens, "DIMENS")
    if idx >= 0:
        rec, _ = _extract_record(tokens, idx + 1)
        if len(rec) >= 3:
            result.nx = int(rec[0])
            result.ny = int(rec[1])
            result.nz = int(rec[2])

    # Grid arrays
    for kw, attr in [
        ("DX", "dx_values"), ("DY", "dy_values"), ("DZ", "dz_values"),
        ("TOPS", "tops_values"), ("PORO", "poro_values"),
        ("PERMX", "permx_values"), ("PERMY", "permy_values"),
        ("PERMZ", "permz_values"),
    ]:
        idx = _find_keyword(tokens, kw)
        if idx >= 0:
            rec, _ = _extract_record(tokens, idx + 1)
            setattr(result, attr, [float(v) for v in rec if v != "1*"])

    # DENSITY
    idx = _find_keyword(tokens, "DENSITY")
    if idx >= 0:
        rec, _ = _extract_record(tokens, idx + 1)
        if len(rec) >= 3:
            result.density = {
                "oil": float(rec[0]),
                "water": float(rec[1]),
                "gas": float(rec[2]),
            }

    # PVTW
    idx = _find_keyword(tokens, "PVTW")
    if idx >= 0:
        rec, _ = _extract_record(tokens, idx + 1)
        if len(rec) >= 4:
            result.pvtw = {
                "ref_pressure": float(rec[0]),
                "fvf": float(rec[1]),
                "compressibility": float(rec[2]),
                "viscosity": float(rec[3]),
            }

    # EQUIL
    idx = _find_keyword(tokens, "EQUIL")
    if idx >= 0:
        rec, _ = _extract_record(tokens, idx + 1)
        result.equil = [float(v) for v in rec if v != "1*"]

    # WELSPECS
    idx = _find_keyword(tokens, "WELSPECS")
    if idx >= 0:
        records = _extract_records(tokens, idx + 1)
        for rec in records:
            if len(rec) >= 6:
                result.welspecs.append({
                    "name": rec[0].strip("'"),
                    "group": rec[1].strip("'"),
                    "i": int(rec[2]),
                    "j": int(rec[3]),
                    "ref_depth": float(rec[4]) if rec[4] != "1*" else 0,
                    "phase": rec[5].strip("'"),
                })

    # COMPDAT
    idx = _find_keyword(tokens, "COMPDAT")
    if idx >= 0:
        records = _extract_records(tokens, idx + 1)
        for rec in records:
            if len(rec) >= 5:
                result.compdat.append({
                    "well": rec[0].strip("'"),
                    "i": int(rec[1]),
                    "j": int(rec[2]),
                    "k_top": int(rec[3]),
                    "k_bottom": int(rec[4]),
                    "status": rec[5].strip("'") if len(rec) > 5 else "OPEN",
                })

    # WCONPROD
    idx = _find_keyword(tokens, "WCONPROD")
    if idx >= 0:
        records = _extract_records(tokens, idx + 1)
        for rec in records:
            if len(rec) >= 4:
                result.wconprod.append({
                    "well": rec[0].strip("'"),
                    "status": rec[1].strip("'"),
                    "control": rec[2].strip("'"),
                    "rate": float(rec[3]) if rec[3] != "1*" else 0,
                    "bhp_limit": float(rec[-1]) if len(rec) > 4 and rec[-1] != "1*" else 0,
                })

    # WCONINJE
    idx = _find_keyword(tokens, "WCONINJE")
    if idx >= 0:
        records = _extract_records(tokens, idx + 1)
        for rec in records:
            if len(rec) >= 5:
                result.wconinje.append({
                    "well": rec[0].strip("'"),
                    "fluid": rec[1].strip("'"),
                    "status": rec[2].strip("'"),
                    "control": rec[3].strip("'"),
                    "rate": float(rec[4]) if rec[4] != "1*" else 0,
                    "bhp_limit": float(rec[-1]) if len(rec) > 5 and rec[-1] != "1*" else 0,
                })

    # TSTEP
    idx = _find_keyword(tokens, "TSTEP")
    if idx >= 0:
        rec, _ = _extract_record(tokens, idx + 1)
        result.tstep_values = [float(v) for v in rec if v != "1*"]

    return result


def parse_deck_file(path: str) -> DeckParseResult:
    """Parse Eclipse deck from file path.

    Handles INCLUDE directives by resolving relative to the deck directory.
    """
    deck_path = Path(path)
    text = deck_path.read_text(errors="replace")

    # Resolve INCLUDE files
    text = _resolve_includes(text, deck_path.parent)

    return parse_deck(text)


def _resolve_includes(text: str, base_dir: Path, depth: int = 0) -> str:
    """Recursively resolve INCLUDE directives."""
    if depth > 10:
        logger.warning("INCLUDE recursion depth exceeded")
        return text

    lines = text.splitlines()
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Check for INCLUDE keyword
        if stripped.upper() == "INCLUDE":
            # Next non-empty, non-comment line has the filename
            i += 1
            while i < len(lines):
                next_line = lines[i].strip()
                if next_line and not next_line.startswith("--"):
                    # Extract filename (may be quoted, terminated with /)
                    fname = next_line.strip("' /\t")
                    include_path = base_dir / fname
                    if include_path.exists():
                        inc_text = include_path.read_text(errors="replace")
                        inc_text = _resolve_includes(inc_text, include_path.parent, depth + 1)
                        result.append(inc_text)
                    else:
                        logger.warning(f"INCLUDE file not found: {include_path}")
                    break
                i += 1
        else:
            result.append(line)
        i += 1

    return "\n".join(result)


# ─── SimRequest Conversion ────────────────────────────────────────────────

def deck_to_sim_request(parsed: DeckParseResult) -> SimRequest:
    """Convert DeckParseResult to SimRequest.

    Applies unit conversion (FIELD → SI) and maps Eclipse well
    definitions to CLARISSA's WellConfig model.
    """
    is_field = parsed.is_field
    conv_len = _ft_to_m if is_field else (lambda x: x)
    conv_pres = _psi_to_bar if is_field else (lambda x: x)

    # Grid — use mean values for non-uniform properties
    dx_vals = parsed.dx_values or [1000.0]
    dy_vals = parsed.dy_values or [1000.0]
    dz_vals = parsed.dz_values or [20.0]
    poro_vals = parsed.poro_values or [0.2]
    permx_vals = parsed.permx_values or [100.0]
    permy_vals = parsed.permy_values or [100.0]
    permz_vals = parsed.permz_values or [10.0]

    # For non-uniform grids, use mean cell size
    mean_dx = sum(dx_vals) / len(dx_vals) if dx_vals else 100.0
    mean_dy = sum(dy_vals) / len(dy_vals) if dy_vals else 100.0
    mean_dz = sum(dz_vals) / len(dz_vals) if dz_vals else 10.0
    mean_poro = sum(poro_vals) / len(poro_vals) if poro_vals else 0.2
    mean_permx = sum(permx_vals) / len(permx_vals) if permx_vals else 100.0
    mean_permy = sum(permy_vals) / len(permy_vals) if permy_vals else 100.0
    mean_permz = sum(permz_vals) / len(permz_vals) if permz_vals else 10.0

    # Top depth
    depth_top = conv_len(parsed.tops_values[0]) if parsed.tops_values else 2000.0

    grid = GridParams(
        nx=parsed.nx or 10,
        ny=parsed.ny or 10,
        nz=parsed.nz or 1,
        dx=conv_len(mean_dx),
        dy=conv_len(mean_dy),
        dz=conv_len(mean_dz),
        depth_top=depth_top,
        porosity=mean_poro,
        permeability_x=mean_permx,  # mD is same in both unit systems
        permeability_y=mean_permy,
        permeability_z=mean_permz,
    )

    # Fluid
    init_pressure = conv_pres(parsed.equil[1]) if len(parsed.equil) > 1 else 200.0
    water_visc = parsed.pvtw.get("viscosity", 0.5)

    # Density — FIELD units are lb/ft³, convert to kg/m³
    oil_density = 800.0
    water_density = 1000.0
    if parsed.density:
        if is_field:
            oil_density = parsed.density.get("oil", 53.66) * 16.0185
            water_density = parsed.density.get("water", 64.49) * 16.0185
        else:
            oil_density = parsed.density.get("oil", 800.0)
            water_density = parsed.density.get("water", 1000.0)

    fluid = FluidProperties(
        oil_density_kg_m3=oil_density,
        water_density_kg_m3=water_density,
        oil_viscosity_cp=1.0,  # Would need PVTO parsing for proper value
        water_viscosity_cp=water_visc,
        initial_pressure_bar=init_pressure,
    )

    # Wells — merge WELSPECS + COMPDAT + WCONPROD/WCONINJE
    wells = _build_wells(parsed, is_field)

    # Timesteps — cumulative from incremental
    timesteps_days = []
    cumulative = 0.0
    for dt in parsed.tstep_values:
        cumulative += dt
        timesteps_days.append(cumulative)

    return SimRequest(
        grid=grid,
        wells=wells,
        fluid=fluid,
        timesteps_days=timesteps_days,
        title=parsed.title or "Imported Eclipse Deck",
        backend="opm",
    )


def _build_wells(parsed: DeckParseResult, is_field: bool) -> list[WellConfig]:
    """Build WellConfig list from WELSPECS + COMPDAT + WCON* records."""
    conv_rate_oil = _stbd_to_m3d if is_field else (lambda x: x)
    conv_rate_gas = _mscfd_to_m3d if is_field else (lambda x: x)
    conv_pres = _psi_to_bar if is_field else (lambda x: x)

    wells = []
    well_names = {ws["name"] for ws in parsed.welspecs}

    for ws in parsed.welspecs:
        name = ws["name"]

        # COMPDAT — find completion data for this well
        comp = next((c for c in parsed.compdat if c["well"] == name), None)

        # Eclipse uses 1-based indexing, CLARISSA uses 0-based
        i = (comp["i"] if comp else ws["i"]) - 1
        j = (comp["j"] if comp else ws["j"]) - 1
        k_top = (comp["k_top"] - 1) if comp else 0
        k_bottom = (comp["k_bottom"] - 1) if comp else k_top

        # Determine well type from WCONPROD / WCONINJE
        prod = next((p for p in parsed.wconprod if p["well"] == name), None)
        inje = next((inj for inj in parsed.wconinje if inj["well"] == name), None)

        if inje:
            well_type = WellType.INJECTOR
            fluid_type = inje.get("fluid", "WATER")
            phases = [Phase.GAS] if fluid_type == "GAS" else [Phase.WATER]

            rate = None
            bhp = None
            control = inje.get("control", "RATE")
            if control == "RATE" and inje.get("rate"):
                if fluid_type == "GAS":
                    rate = conv_rate_gas(inje["rate"])
                else:
                    rate = conv_rate_oil(inje["rate"])
            if inje.get("bhp_limit"):
                bhp = conv_pres(inje["bhp_limit"])
        elif prod:
            well_type = WellType.PRODUCER
            phases = [Phase.OIL, Phase.WATER]
            if "GAS" in parsed.phases:
                phases.append(Phase.GAS)

            rate = None
            bhp = None
            control = prod.get("control", "ORAT")
            if control in ("ORAT", "RATE") and prod.get("rate"):
                rate = conv_rate_oil(prod["rate"])
            if prod.get("bhp_limit"):
                bhp = conv_pres(prod["bhp_limit"])
        else:
            # Default to producer
            well_type = WellType.PRODUCER
            phases = [Phase.OIL, Phase.WATER]
            rate = None
            bhp = None

        wells.append(WellConfig(
            name=name,
            well_type=well_type,
            i=max(0, i),
            j=max(0, j),
            k_top=max(0, k_top),
            k_bottom=max(0, k_bottom),
            rate_m3_day=rate,
            bhp_bar=bhp,
            phases=phases,
        ))

    return wells
