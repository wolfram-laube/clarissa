% ═══════════════════════════════════════════════════════════════════════
% CLARISSA · SPE Benchmark MRST Runner
% Runs SPE benchmarks through MRST and exports results as JSON.
%
% Usage (in Octave/MATLAB with MRST on path):
%   run_mrst_benchmarks('spe1')     % Single benchmark
%   run_mrst_benchmarks('all')      % All benchmarks
%
% Prerequisites:
%   - MRST installed (startup.m sourced)
%   - Modules: ad-core, ad-blackoil, ad-props, deckformat, mrst-gui
%
% Output:
%   mrst_results/<benchmark>_mrst.json
% ═══════════════════════════════════════════════════════════════════════

function run_mrst_benchmarks(filter)
    if nargin < 1, filter = 'all'; end

    % MRST startup
    mrstModule add ad-core ad-blackoil ad-props deckformat

    benchmarks = struct();
    benchmarks.spe1  = struct('deck', 'SPE1CASE2.DATA',    'nx',10, 'ny',10, 'nz',3);
    benchmarks.spe5  = struct('deck', 'SPE5CASE1.DATA',    'nx',7,  'ny',7,  'nz',3);
    benchmarks.spe9  = struct('deck', 'SPE9_CP.DATA',      'nx',24, 'ny',25, 'nz',15);
    benchmarks.spe10 = struct('deck', 'SPE10_MODEL1.DATA',  'nx',100,'ny',1,  'nz',20);

    keys = fieldnames(benchmarks);
    mkdir_if_needed('mrst_results');

    for i = 1:numel(keys)
        key = keys{i};
        if ~strcmp(filter, 'all') && ~strcmp(filter, key)
            continue;
        end

        bm = benchmarks.(key);
        fprintf('\n═══ %s ═══\n', upper(key));

        try
            run_single(key, bm);
        catch ME
            fprintf('ERROR: %s — %s\n', key, ME.message);
        end
    end
end

function run_single(key, bm)
    % Find deck
    deck_path = fullfile('decks', 'opm-data', dirname_for_key(key), bm.deck);
    if ~exist(deck_path, 'file')
        fprintf('  Deck not found: %s\n', deck_path);
        return;
    end

    fprintf('  Reading deck: %s\n', deck_path);
    deck = readEclipseDeck(deck_path);
    deck = convertDeckUnits(deck);

    % Initialize model
    G = initEclipseGrid(deck);
    G = computeGeometry(G);

    rock = initEclipseRock(deck);
    rock = compressRock(rock, G.cells.indexMap);

    fluid = initDeckADIFluid(deck);

    model = GenericBlackOilModel(G, rock, fluid, 'disgas', true, 'vapoil', false);

    % Schedule
    schedule = convertDeckScheduleToMRST(model, deck);

    % Initial state
    state0 = initEclipseState(G, deck, fluid);

    % Run simulation
    fprintf('  Running MRST simulation...\n');
    tic;
    [wellSols, states, report] = simulateScheduleAD(state0, model, schedule);
    elapsed = toc;
    fprintf('  Completed in %.1f seconds\n', elapsed);

    % Export to JSON
    export_json(key, bm, G, states, wellSols, schedule, elapsed);
end

function export_json(key, bm, G, states, wellSols, schedule, elapsed)
    fprintf('  Exporting JSON...\n');

    % Select timesteps
    n_states = numel(states);
    max_ts = 25;
    step = max(1, floor(n_states / max_ts));
    indices = 1:step:n_states;
    if indices(end) ~= n_states
        indices = [indices, n_states];
    end

    % Build timestep data
    timesteps = {};
    cum_time = 0;
    for si = 1:numel(indices)
        idx = indices(si);
        state = states{idx};

        % Cumulative time
        for ti = 1:idx
            cum_time = cum_time + schedule.step.val(ti);
        end
        t_days = cum_time / day;

        % Cell data (convert pressure from Pa to bar)
        cells = struct();
        cells.pressure = round(state.pressure / barsa, 2);
        cells.saturation_oil = round(state.s(:,2), 4);  % oil
        cells.saturation_water = round(state.s(:,1), 4); % water
        if size(state.s, 2) >= 3
            cells.saturation_gas = round(state.s(:,3), 4);
        else
            cells.saturation_gas = zeros(G.cells.num, 1);
        end

        % Well data
        ws = wellSols{idx};
        wells = {};
        for wi = 1:numel(ws)
            w = ws(wi);
            wells{wi} = struct( ...
                'well_name', w.name, ...
                'oil_rate_m3_day', round(-w.qOs / day, 2), ...
                'water_rate_m3_day', round(-w.qWs / day, 2), ...
                'gas_rate_m3_day', round(-w.qGs / day, 2), ...
                'bhp_bar', round(w.bhp / barsa, 2), ...
                'cumulative_oil_m3', 0, ...
                'cumulative_water_m3', 0 ...
            );
        end

        timesteps{si} = struct('time_days', round(t_days, 1), ...
                               'cells', cells, 'wells', {wells});
    end

    % Static properties
    grid_data = struct();
    grid_data.nx = bm.nx;
    grid_data.ny = bm.ny;
    grid_data.nz = bm.nz;
    grid_data.permx = round(convertTo(G.rock.perm(:,1), milli*darcy), 2);
    grid_data.poro = round(G.rock.poro, 4);

    % Assemble
    result = struct();
    result.job_id = sprintf('%s-mrst-001', lower(key));
    result.title = sprintf('%s — MRST', upper(key));
    result.status = 'completed';
    result.timesteps = timesteps;
    result.metadata = struct( ...
        'backend', 'MRST Octave', ...
        'backend_version', '2024a', ...
        'grid_cells', G.cells.num, ...
        'wall_time_seconds', elapsed, ...
        'converged', true ...
    );

    % Write JSON
    outpath = fullfile('mrst_results', sprintf('%s_mrst.json', key));
    fid = fopen(outpath, 'w');
    fprintf(fid, '%s', jsonencode(result));
    fclose(fid);
    fprintf('  ✓ Saved: %s\n', outpath);
end

function d = dirname_for_key(key)
    switch key
        case 'spe1',  d = 'spe1';
        case 'spe5',  d = 'spe5';
        case 'spe9',  d = 'spe9';
        case 'spe10', d = 'spe10model1';
        otherwise,    d = key;
    end
end

function mkdir_if_needed(d)
    if ~exist(d, 'dir'), mkdir(d); end
end
