#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════
# CLARISSA · SPE Benchmark Runner
# Runs all SPE benchmarks through OPM Flow on Nordic VM
# and converts results to spe-viewer.html JSON format.
#
# Usage:
#   chmod +x run_benchmarks.sh
#   ./run_benchmarks.sh           # Run all benchmarks
#   ./run_benchmarks.sh spe1      # Run only SPE1
#   ./run_benchmarks.sh spe10m2   # Run only SPE10 Model 2 (long!)
#
# Prerequisites:
#   - OPM Flow 2025.10 at /usr/bin/flow
#   - ~/venv with resdata, numpy
#   - Decks in ~/projects/decks/opm-data/
#
# Output:
#   ~/projects/results/clarissa-benchmarks/spe_benchmarks.json
# ═══════════════════════════════════════════════════════════════════════
set -euo pipefail

DECKS_DIR="${HOME}/projects/decks/opm-data"
RESULTS_DIR="${HOME}/projects/results/clarissa-benchmarks"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONVERTER="${SCRIPT_DIR}/opm_to_viewer_json.py"
VENV="${HOME}/venv"
FILTER="${1:-all}"

mkdir -p "$RESULTS_DIR"

# Colors
G='\033[0;32m'; Y='\033[1;33m'; C='\033[0;36m'; R='\033[0;31m'; N='\033[0m'

log()  { echo -e "${C}[CLARISSA]${N} $*"; }
ok()   { echo -e "${G}[✓]${N} $*"; }
warn() { echo -e "${Y}[!]${N} $*"; }
err()  { echo -e "${R}[✗]${N} $*"; }

# ─── Preflight ─────────────────────────────────────────────────────
log "Preflight checks..."
command -v flow >/dev/null 2>&1 || { err "OPM Flow not found"; exit 1; }
flow --version 2>&1 | head -1
[ -d "$DECKS_DIR" ] || { err "Decks dir not found: $DECKS_DIR"; exit 1; }
[ -f "$CONVERTER" ] || { err "Converter not found: $CONVERTER"; exit 1; }

# Activate venv
source "${VENV}/bin/activate" 2>/dev/null || warn "Could not activate venv"
python3 -c "import resdata; print(f'resdata {resdata.__version__}')" 2>/dev/null || { err "resdata not available"; exit 1; }

# ─── Benchmark definitions ─────────────────────────────────────────
declare -A BENCHMARKS
BENCHMARKS[spe1]="spe1/SPE1CASE2.DATA"
BENCHMARKS[spe5]="spe5/SPE5CASE1.DATA"
BENCHMARKS[spe9]="spe9/SPE9_CP.DATA"
BENCHMARKS[spe10m1]="spe10model1/SPE10_MODEL1.DATA"
BENCHMARKS[spe10m2]="spe10model2/SPE10_MODEL2.DATA"

# ─── Run simulations ──────────────────────────────────────────────
run_sim() {
    local key="$1"
    local deck_rel="${BENCHMARKS[$key]}"
    local deck_path="${DECKS_DIR}/${deck_rel}"
    local out_dir="${RESULTS_DIR}/${key}"

    if [ ! -f "$deck_path" ]; then
        warn "Deck not found: $deck_path — skipping $key"
        return 1
    fi

    log "━━━ ${key^^} ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "Deck: $deck_path"
    
    mkdir -p "$out_dir"

    # Copy deck + includes to output dir (OPM needs them co-located)
    local deck_dir
    deck_dir="$(dirname "$deck_path")"
    cp "$deck_dir"/* "$out_dir/" 2>/dev/null || true

    local deck_name
    deck_name="$(basename "$deck_rel")"

    # Run OPM Flow
    log "Running OPM Flow..."
    local start_time
    start_time=$(date +%s)

    if flow "$out_dir/$deck_name" --output-dir="$out_dir" 2>&1 | tee "$out_dir/flow.log" | tail -5; then
        local end_time
        end_time=$(date +%s)
        local elapsed=$((end_time - start_time))
        ok "${key^^} completed in ${elapsed}s"
        echo "$elapsed" > "$out_dir/wall_time.txt"
    else
        err "${key^^} failed — check $out_dir/flow.log"
        return 1
    fi
}

# ─── Main ──────────────────────────────────────────────────────────
log "CLARISSA SPE Benchmark Runner"
log "Filter: $FILTER"
log "Results: $RESULTS_DIR"
echo ""

FAILED=()
SUCCEEDED=()

for key in spe1 spe5 spe9 spe10m1 spe10m2; do
    if [ "$FILTER" != "all" ] && [ "$FILTER" != "$key" ]; then
        continue
    fi

    if [ "$key" = "spe10m2" ]; then
        warn "SPE10 Model 2 has 1.1M cells — estimated runtime: 30-120 minutes"
        warn "Consider running with: ./run_benchmarks.sh spe10m2"
    fi

    if run_sim "$key"; then
        SUCCEEDED+=("$key")
    else
        FAILED+=("$key")
    fi
    echo ""
done

# ─── Convert to JSON ──────────────────────────────────────────────
log "Converting results to viewer JSON..."
python3 "$CONVERTER" \
    --results-dir "$RESULTS_DIR" \
    --output "$RESULTS_DIR/spe_benchmarks.json" \
    --benchmarks "${SUCCEEDED[@]}"

if [ -f "$RESULTS_DIR/spe_benchmarks.json" ]; then
    local_size=$(du -h "$RESULTS_DIR/spe_benchmarks.json" | cut -f1)
    ok "Output: $RESULTS_DIR/spe_benchmarks.json ($local_size)"
    log ""
    log "Next: copy to your machine and open with spe-viewer.html"
    log "  scp nordic:${RESULTS_DIR}/spe_benchmarks.json ."
    log "  # Then place next to spe-viewer.html and open in browser"
else
    err "JSON conversion failed"
fi

echo ""
log "═══ Summary ═══"
ok "Succeeded: ${SUCCEEDED[*]:-none}"
[ ${#FAILED[@]} -gt 0 ] && err "Failed: ${FAILED[*]}" || true
