"""MRST Script Generator — SimRequest → MATLAB/Octave .m script.

Generates MRST-compatible scripts that GNU Octave can execute directly.
The script uses MRST's standard modules (ad-blackoil, ad-core, mrst-autodiff)
to set up and run a reservoir simulation, then exports results as .mat files.

Pipeline:
1. SimRequest → .m script (this module)
2. octave --no-gui script.m  (MRSTBackend.run)
3. .mat → UnifiedResult  (MRSTBackend.parse_result)

Supported features:
- Cartesian grids (cartGrid)
- Injector/producer wells
- Two-phase (oil-water) and three-phase (oil-water-gas)
- Black-oil PVT with simplified properties
- Output: pressure, saturations, well data per timestep

Issue #166 | Epic #161 | ADR-040
"""
from __future__ import annotations

import textwrap
from datetime import datetime, timezone
from typing import Optional

from clarissa.sim_engine.models import (
    FluidProperties,
    GridParams,
    Phase,
    SimRequest,
    WellConfig,
    WellType,
)


def generate_mrst_script(request: SimRequest, output_mat: str = "results.mat") -> str:
    """Generate a complete MRST .m script from a SimRequest.

    Args:
        request: Simulation request with grid, wells, fluid properties.
        output_mat: Filename for the .mat output file.

    Returns:
        Complete MATLAB/Octave script as string.
    """
    sections = [
        _header(request),
        _mrst_startup(),
        _grid_section(request.grid),
        _rock_section(request.grid),
        _fluid_section(request.fluid, request),
        _well_section(request.wells, request.grid),
        _initial_state(request.grid, request.fluid),
        _schedule_section(request.timesteps_days),
        _solver_section(),
        _run_section(),
        _export_section(output_mat, request),
    ]
    return "\n".join(sections)


def write_mrst_script(
    request: SimRequest,
    script_path: str,
    output_mat: str = "results.mat",
) -> str:
    """Write MRST script to file.

    Returns:
        Path to written script.
    """
    script = generate_mrst_script(request, output_mat)
    with open(script_path, "w") as f:
        f.write(script)
    return script_path


# ─── Section Generators ───────────────────────────────────────────────────


def _header(request: SimRequest) -> str:
    """Script header with metadata."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    grid = request.grid
    return textwrap.dedent(f"""\
        %% CLARISSA Simulation — MRST Backend
        %% Generated: {now}
        %% Title: {request.title}
        %% Grid: {grid.nx}×{grid.ny}×{grid.nz} = {grid.total_cells} cells
        %% Wells: {len(request.wells)}
        %% Backend: mrst
        %% Issue #166 | Epic #161 | ADR-040
        %%
    """)


def _mrst_startup() -> str:
    """MRST module loading."""
    return textwrap.dedent("""\
        %% ─── MRST Startup ───────────────────────────────────────────
        % Ensure MRST is on the path
        if exist('mrstPath', 'file') == 0
            error('MRST not found. Set MRST_DIR or add to Octave path.');
        end
        mrstModule add ad-blackoil ad-core ad-props mrst-autodiff deckformat
    """)


def _grid_section(grid: GridParams) -> str:
    """Cartesian grid definition."""
    return textwrap.dedent(f"""\
        %% ─── Grid ───────────────────────────────────────────────────
        G = cartGrid([{grid.nx}, {grid.ny}, {grid.nz}], ...
                     [{grid.nx * grid.dx}, {grid.ny * grid.dy}, {grid.nz * grid.dz}]);
        G = computeGeometry(G);
        fprintf('Grid: %d cells\\n', G.cells.num);
    """)


def _rock_section(grid: GridParams) -> str:
    """Rock properties (porosity, permeability)."""
    # MRST uses SI: permeability in m², we convert from mD
    # 1 mD = 9.869233e-16 m²
    perm_x = grid.permeability_x * 9.869233e-16
    perm_y = grid.permeability_y * 9.869233e-16
    perm_z = grid.permeability_z * 9.869233e-16
    return textwrap.dedent(f"""\
        %% ─── Rock Properties ────────────────────────────────────────
        rock = makeRock(G, [{perm_x:.6e}, {perm_y:.6e}, {perm_z:.6e}], {grid.porosity});
    """)


def _fluid_section(fluid: FluidProperties, request: SimRequest) -> str:
    """Fluid model definition."""
    has_gas = any(Phase.GAS in w.phases for w in request.wells)

    if has_gas:
        return textwrap.dedent(f"""\
            %% ─── Fluid (Three-Phase Black Oil) ─────────────────────────
            fluid = initSimpleADIFluid('phases', 'WOG', ...
                'mu',  [{fluid.water_viscosity_cp}*centi*poise, ...
                        {fluid.oil_viscosity_cp}*centi*poise, ...
                        0.02*centi*poise], ...
                'rho', [{fluid.water_density_kg_m3}, ...
                        {fluid.oil_density_kg_m3}, ...
                        100], ...
                'n',   [2, 2, 2]);
        """)
    else:
        return textwrap.dedent(f"""\
            %% ─── Fluid (Two-Phase Oil-Water) ───────────────────────────
            fluid = initSimpleADIFluid('phases', 'WO', ...
                'mu',  [{fluid.water_viscosity_cp}*centi*poise, ...
                        {fluid.oil_viscosity_cp}*centi*poise], ...
                'rho', [{fluid.water_density_kg_m3}, ...
                        {fluid.oil_density_kg_m3}], ...
                'n',   [2, 2]);
        """)


def _well_section(wells: list[WellConfig], grid: GridParams) -> str:
    """Well definitions."""
    lines = [
        "%% ─── Wells ──────────────────────────────────────────────────",
        "W = [];",
    ]
    for w in wells:
        # MRST uses 1-based indexing
        i1 = w.i + 1
        j1 = w.j + 1
        k_top1 = w.k_top + 1
        k_bot1 = w.k_bottom + 1

        if w.well_type == WellType.INJECTOR:
            well_type_str = "'InjectWell'"
            if w.rate_m3_day is not None:
                control = f"'rate', {w.rate_m3_day / 86400:.6e}, 'type', 'rate'"
            elif w.bhp_bar is not None:
                control = f"'val', {w.bhp_bar * 1e5}, 'type', 'bhp'"
            else:
                control = f"'rate', {100.0 / 86400:.6e}, 'type', 'rate'"
        else:
            well_type_str = "'ProducerWell'"
            if w.bhp_bar is not None:
                control = f"'val', {w.bhp_bar * 1e5}, 'type', 'bhp'"
            elif w.rate_m3_day is not None:
                control = f"'rate', {w.rate_m3_day / 86400:.6e}, 'type', 'rate'"
            else:
                control = f"'val', {100.0 * 1e5}, 'type', 'bhp'"

        # MRST addWell: cell indices for perforated layers
        lines.append(f"% Well: {w.name} ({w.well_type.value})")
        lines.append(
            f"cells_{w.name} = sub2ind(G.cartDims, "
            f"{i1}*ones({k_bot1 - k_top1 + 1},1), "
            f"{j1}*ones({k_bot1 - k_top1 + 1},1), "
            f"({k_top1}:{k_bot1})');"
        )
        lines.append(
            f"W = addWell(W, G, rock, cells_{w.name}, "
            f"'Name', '{w.name}', {control}, "
            f"'Comp_i', [{_comp_injection(w)}]);"
        )

    return "\n".join(lines) + "\n"


def _comp_injection(well: WellConfig) -> str:
    """Composition vector for well injection (water fraction, oil fraction, ...)."""
    has_gas = Phase.GAS in well.phases
    if well.well_type == WellType.INJECTOR:
        if Phase.WATER in well.phases:
            return "1, 0, 0" if has_gas else "1, 0"
        elif Phase.GAS in well.phases:
            return "0, 0, 1"
        else:
            return "0, 1, 0" if has_gas else "0, 1"
    else:
        # Producer — use default
        return "0, 1, 0" if has_gas else "0, 1"


def _initial_state(grid: GridParams, fluid: FluidProperties) -> str:
    """Initial reservoir state."""
    p_init_pa = fluid.initial_pressure_bar * 1e5
    return textwrap.dedent(f"""\
        %% ─── Initial State ──────────────────────────────────────────
        state0 = initResSol(G, {p_init_pa}, [0.0, 1.0]);
        %% state0.pressure = initial pressure in Pa
        %% state0.s = [Sw, So] initial saturations (fully oil-saturated)
    """)


def _schedule_section(timesteps_days: list[float]) -> str:
    """Time stepping schedule."""
    # Convert cumulative days to incremental steps in seconds
    steps = []
    prev = 0.0
    for t in sorted(timesteps_days):
        dt = t - prev
        if dt > 0:
            steps.append(dt * 86400.0)  # days → seconds
        prev = t

    steps_str = "; ".join(f"{s:.1f}" for s in steps)
    return textwrap.dedent(f"""\
        %% ─── Schedule ────────────────────────────────────────────────
        dt = [{steps_str}];
        schedule = simpleSchedule(dt, 'W', W);
        fprintf('Timesteps: %d, total %.1f days\\n', numel(dt), sum(dt)/86400);
    """)


def _solver_section() -> str:
    """Solver / model setup."""
    return textwrap.dedent("""\
        %% ─── Model & Solver ─────────────────────────────────────────
        model = GenericBlackOilModel(G, rock, fluid, 'gas', false, 'oil', true, 'water', true);
        solver = NonLinearSolver('maxIterations', 25, 'maxTimestepCuts', 6);
    """)


def _run_section() -> str:
    """Execute simulation."""
    return textwrap.dedent("""\
        %% ─── Run ────────────────────────────────────────────────────
        fprintf('Starting simulation...\\n');
        tic;
        [wellSols, states, report] = simulateScheduleAD(state0, model, schedule, ...
            'NonLinearSolver', solver);
        wall_time = toc;
        fprintf('Simulation completed in %.2f seconds\\n', wall_time);
        converged = report.Converged;
    """)


def _export_section(output_mat: str, request: SimRequest) -> str:
    """Export results to .mat file."""
    well_names = [w.name for w in request.wells]
    well_names_str = "{" + ", ".join(f"'{n}'" for n in well_names) + "}"

    return textwrap.dedent(f"""\
        %% ─── Export Results ──────────────────────────────────────────
        n_steps = numel(states);
        n_cells = G.cells.num;
        n_wells = numel(W);

        % Pre-allocate result arrays
        time_days = zeros(n_steps, 1);
        pressure = zeros(n_steps, n_cells);
        s_water = zeros(n_steps, n_cells);
        s_oil = zeros(n_steps, n_cells);

        % Well data: [n_steps × n_wells] for each quantity
        well_bhp = zeros(n_steps, n_wells);
        well_qOs = zeros(n_steps, n_wells);
        well_qWs = zeros(n_steps, n_wells);

        cumulative_time = 0;
        for i = 1:n_steps
            cumulative_time = cumulative_time + schedule.step.val(i);
            time_days(i) = cumulative_time / 86400;

            pressure(i, :) = states{{i}}.pressure / 1e5;  % Pa → bar
            s_water(i, :) = states{{i}}.s(:, 1)';
            if size(states{{i}}.s, 2) >= 2
                s_oil(i, :) = states{{i}}.s(:, 2)';
            end

            for w = 1:n_wells
                well_bhp(i, w) = wellSols{{i}}(w).bhp / 1e5;  % Pa → bar
                well_qOs(i, w) = wellSols{{i}}(w).qOs * 86400; % m³/s → m³/day
                well_qWs(i, w) = wellSols{{i}}(w).qWs * 86400; % m³/s → m³/day
            end
        end

        well_names = {well_names_str};
        grid_dims = [{request.grid.nx}, {request.grid.ny}, {request.grid.nz}];

        save('{output_mat}', 'time_days', 'pressure', 's_water', 's_oil', ...
             'well_bhp', 'well_qOs', 'well_qWs', 'well_names', 'grid_dims', ...
             'wall_time', 'converged', '-v7');

        fprintf('Results exported to {output_mat}\\n');
        fprintf('Steps: %d, Cells: %d, Wells: %d\\n', n_steps, n_cells, n_wells);
    """)
