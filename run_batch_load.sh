#!/usr/bin/env bash
# run_batch_load.sh — Procesa todos los eventos GWOSC con 00_load_ligo_data.py
#
# Para cada evento:
#   - Si tiene H1: usa H1 como primario, L1 como secundario (si existe)
#   - Si NO tiene H1 pero sí L1: usa L1 como primario (--h1-npz = L1 file)
#
# Uso:    cd ~/RINGEST && bash malda/run_batch_load.sh [--jobs N] [--dry-run]
# Opciones:
#   --jobs N    Paralelismo con GNU parallel (default: 4; 1 = secuencial)
#   --dry-run   Imprime comandos sin ejecutarlos

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
RUNS_ROOT="$PROJECT_ROOT/malda/runs/gwosc_all"
PYTHON="${PYTHON:-python3}"
JOBS=4
DRY_RUN=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --jobs)    JOBS="$2"; shift 2 ;;
        --dry-run) DRY_RUN=1; shift ;;
        *) echo "Argumento desconocido: $1" >&2; exit 1 ;;
    esac
done

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$RUNS_ROOT/batch_load_${TIMESTAMP}.log"
RESULTS_FILE="$RUNS_ROOT/batch_load_${TIMESTAMP}_results.tsv"

mapfile -t EVENTS < <(ls "$RUNS_ROOT" | grep -v download_manifest | sort)
TOTAL=${#EVENTS[@]}

echo "======================================================"
echo " RINGEST batch 00_load_ligo_data — $(date)"
echo " Eventos: $TOTAL | Jobs: $JOBS | Dry-run: $DRY_RUN"
[[ "$DRY_RUN" -eq 0 ]] && echo " Log: $LOG_FILE"
echo "======================================================"

# Función que procesa un evento y emite "<STATUS>\t<ev>\t<note>"
_run_event() {
    local ev="$1"
    local raw_dir="$RUNS_ROOT/$ev/raw"
    local out_dir="$RUNS_ROOT/$ev/boundary"

    local h1_npz l1_npz primary secondary ifo_note

    h1_npz=$(ls "$raw_dir"/*_H1_*.npz 2>/dev/null | head -1 || true)
    l1_npz=$(ls "$raw_dir"/*_L1_*.npz 2>/dev/null | head -1 || true)

    if [[ -z "$h1_npz" && -z "$l1_npz" ]]; then
        printf "SKIP\t%s\tsin H1 y L1\n" "$ev"
        return 0
    fi

    if [[ -n "$h1_npz" ]]; then
        primary="$h1_npz"
        ifo_note="H1"
        [[ -n "$l1_npz" ]] && secondary="--l1-npz $l1_npz" && ifo_note="H1+L1" || secondary=""
    else
        primary="$l1_npz"
        secondary=""
        ifo_note="L1-only"
    fi

    local cmd
    cmd="$PYTHON $SCRIPT_DIR/00_load_ligo_data.py \
        --h1-npz $primary \
        ${secondary} \
        --run-dir $out_dir \
        --whiten \
        --fft"

    if [[ "$DRY_RUN" -eq 1 ]]; then
        echo "  [DRY] $ev [$ifo_note]"
        echo "        $cmd"
        printf "OK\t%s\t%s (dry)\n" "$ev" "$ifo_note"
        return 0
    fi

    {
        echo "======== $ev [$ifo_note] $(date) ========"
        echo "CMD: $cmd"
    } >> "$LOG_FILE" 2>&1

    local t0=$SECONDS
    if eval "$cmd" >> "$LOG_FILE" 2>&1; then
        local dt=$(( SECONDS - t0 ))
        printf "OK\t%s\t%s (%ds)\n" "$ev" "$ifo_note" "$dt"
    else
        printf "FAIL\t%s\t%s\n" "$ev" "$ifo_note"
    fi
}

export -f _run_event
export RUNS_ROOT SCRIPT_DIR PYTHON DRY_RUN LOG_FILE

[[ "$DRY_RUN" -eq 0 ]] && touch "$LOG_FILE" && touch "$RESULTS_FILE"

# Ejecutar
if [[ "$JOBS" -gt 1 ]] && command -v parallel &>/dev/null; then
    printf '%s\n' "${EVENTS[@]}" \
        | parallel -j "$JOBS" --line-buffer _run_event {} \
        | tee -a "$RESULTS_FILE"
else
    for ev in "${EVENTS[@]}"; do
        _run_event "$ev" | tee -a "$RESULTS_FILE"
    done
fi

echo ""
echo "======================================================"
echo " RESUMEN"
echo "======================================================"

if [[ "$DRY_RUN" -eq 0 ]]; then
    ok=$(grep -c $'^OK\t'   "$RESULTS_FILE" || true)
    sk=$(grep -c $'^SKIP\t' "$RESULTS_FILE" || true)
    fa=$(grep -c $'^FAIL\t' "$RESULTS_FILE" || true)
else
    ok=$(grep -c $'^OK\t'   /dev/stdin <<< "$(cat /dev/stdin)" 2>/dev/null || true)
    ok=0; sk=0; fa=0
fi

echo " OK    : $ok / $TOTAL"
echo " SKIP  : $sk"
echo " FAIL  : $fa"
echo ""

if [[ "$DRY_RUN" -eq 0 && "$fa" -gt 0 ]]; then
    echo " Eventos fallidos:"
    grep $'^FAIL\t' "$RESULTS_FILE" | awk -F'\t' '{print "   " $2}' || true
    echo ""
    echo " Ver errores en: $LOG_FILE"
fi
echo "======================================================"

[[ "${fa:-0}" -eq 0 ]] && exit 0 || exit 1
