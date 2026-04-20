#!/usr/bin/env python3
"""
realdata_ringdown_to_stage02_boundary_dataset.py — CUERDAS-MALDACENA
Real-data bridge: ringdown poles -> stage-02 boundary dataset.

Purpose
-------
Convert Stage-01 ringdown artifacts (poles_*.json, coincident_pairs.json, null_test.json)
into a boundary-only HDF5 dataset + manifest.json consumable by:

  02_emergent_geometry_engine.py --mode inference --data-dir <OUT_DIR> --checkpoint <MODEL>

Contract / Epistemic honesty
----------------------------
- This script DOES NOT inject theoretical targets (no GR templates, no bulk truth).
- It builds deterministic *surrogate embeddings* (G_R_real/imag, G2_ringdown) purely from
  extracted poles as feature-engineering, and stores full provenance in the output HDF5.

Path rules (aligned with readme_rutas.md spirit)
------------------------------------------------
- Relative paths are interpreted root-relative (PROJECT_ROOT / path).
- Relative paths containing '..' are rejected.
- Resolved paths must not escape PROJECT_ROOT.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from tools.g2_representation_contract import (
    G2RepresentationContractError,
    canonicalize_g2_representation,
)

try:
    from family_registry import get_family_status, get_family_status_description
except ImportError:
    def get_family_status(family: str, *, ads_boundary_mode: str = "toy", source: str = "sandbox") -> str:
        return "realdata_surrogate" if source == "realdata" else "toy_sandbox"

    def get_family_status_description(status: str) -> str:
        return status

try:
    import h5py
except Exception as e:
    raise SystemExit(f"[ERROR] h5py not available: {e}")

SCRIPT_VERSION = "realdata_ringdown_to_stage02_boundary_dataset.py v1.1 (2026-04-10)"
G2_TIME_CONTRACT_OMEGA_DOM_V1 = "omega_dom_v1"
G2_TIME_CONTRACT_GAMMA_DOM_V2 = "gamma_dom_v2"
DEFAULT_G2_TIME_CONTRACT = G2_TIME_CONTRACT_OMEGA_DOM_V1
G2_REPR_CONTRACT_OMEGA_DOM_V1 = "xmax_10_omega_dom_v1"
G2_REPR_CONTRACT_GAMMA_DOM_V2 = "xgamma_6_v2"

SANDBOX_OMEGA_MIN = 0.1
SANDBOX_OMEGA_MAX = 3.0
SANDBOX_N_OMEGA = 256
SANDBOX_K_MIN = 0.0
SANDBOX_K_MAX = 5.0
SANDBOX_N_K = 30
SANDBOX_X_MIN = 1e-3
SANDBOX_X_MAX = 10.0
SANDBOX_N_X = 100


def resolve_g2_repr_contract(g2_time_contract: str) -> Tuple[str, float]:
    if g2_time_contract == G2_TIME_CONTRACT_GAMMA_DOM_V2:
        return G2_REPR_CONTRACT_GAMMA_DOM_V2, 6.0
    if g2_time_contract == G2_TIME_CONTRACT_OMEGA_DOM_V1:
        return G2_REPR_CONTRACT_OMEGA_DOM_V1, SANDBOX_X_MAX
    raise ValueError(f"Unsupported g2_time_contract: {g2_time_contract}")


# Saturation detection: based on OBSERVED G2 curve, not predicted
SATURATION_TAIL_THRESHOLD = 0.99
SATURATION_FRACTION_THRESHOLD = 1.0  # all points must be >= 0.99


def detect_observed_saturation(
    g2_array: np.ndarray,
    tail_threshold: float = SATURATION_TAIL_THRESHOLD,
    fraction_threshold: float = SATURATION_FRACTION_THRESHOLD,
) -> Tuple[bool, Dict[str, Any]]:
    """
    Detect if an observed G2 curve is saturated (nearly constant 1 across all points).

    Saturation signature (strict):
      - g2[-1] >= tail_threshold (0.99)
      - fraction of points >= tail_threshold equals fraction_threshold (1.0 = all points)

    This is a POST-HOC check on the constructed observable, not a predictive heuristic.

    Returns:
        (is_saturated, meta): tuple of saturation flag and diagnostic metadata.
    """
    if g2_array is None or g2_array.size == 0:
        return False, {"error": "empty_array"}

    g2 = np.asarray(g2_array, dtype=np.float64).ravel()
    n_points = g2.size
    g2_last = float(g2[-1])
    n_ge_threshold = int(np.sum(g2 >= tail_threshold))
    fraction_ge_threshold = n_ge_threshold / n_points if n_points > 0 else 0.0

    is_saturated = (g2_last >= tail_threshold) and (fraction_ge_threshold >= fraction_threshold)

    meta = {
        "g2_last": g2_last,
        "n_points": n_points,
        "n_ge_threshold": n_ge_threshold,
        "fraction_ge_threshold": fraction_ge_threshold,
        "tail_threshold": tail_threshold,
        "fraction_threshold": fraction_threshold,
    }
    return is_saturated, meta


# ----------------------------
# Path resolution (root-relative, no '..', no escape)
# ----------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent  # repo root (basurin/)


def _reject_dotdot(p: Path) -> None:
    # Reject any '..' segment in a *relative* path
    if any(part == ".." for part in p.parts):
        raise ValueError(f"Relative path contains '..' (forbidden): {p}")


def resolve_root_relative(path_str: str) -> Path:
    p = Path(path_str).expanduser()
    if p.is_absolute():
        resolved = p.resolve(strict=False)
    else:
        _reject_dotdot(p)
        resolved = (PROJECT_ROOT / p).resolve(strict=False)

    # Reject paths escaping project root (for auditability)
    try:
        resolved.relative_to(PROJECT_ROOT.resolve(strict=False))
    except Exception:
        raise ValueError(f"Path escapes PROJECT_ROOT ({PROJECT_ROOT}): {path_str} -> {resolved}")
    return resolved


# ----------------------------
# JSON helpers
# ----------------------------

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_get(d: Dict[str, Any], keys: List[str], default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


# ----------------------------
# Ringdown parsing
# ----------------------------

@dataclass
class Pole:
    freq_hz: float
    damping_1_over_s: float
    amp_abs: float


def parse_poles_json(poles_payload: Dict[str, Any]) -> List[Pole]:
    poles_list = poles_payload.get("poles", [])
    out: List[Pole] = []
    for p in poles_list:
        try:
            f = float(p.get("freq_hz"))
            g = float(p.get("damping_1_over_s"))
            a = float(p.get("amp_abs", 1.0))
            if not np.isfinite(f) or not np.isfinite(g) or not np.isfinite(a):
                continue
            # Keep only positive-frequency poles by default (consistent with Stage 01 filters)
            if f <= 0:
                continue
            out.append(Pole(freq_hz=f, damping_1_over_s=g, amp_abs=max(a, 0.0)))
        except Exception:
            continue
    return out


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _safe_float(value: Any) -> Optional[float]:
    try:
        x = float(value)
    except Exception:
        return None
    return x if np.isfinite(x) else None


def load_literature_dataset(csv_path: Path) -> Dict[str, List[Dict[str, Any]]]:
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    by_event: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        event = str(row.get("event", "")).strip()
        if not event:
            continue
        by_event.setdefault(event, []).append(row)
    return by_event


def select_literature_row(rows: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Choose one literature row per event.

    Policy:
      1. Prefer rows already flagged is_220_candidate=True.
      2. Within that subset, choose the smallest finite kerr_220_distance.
      3. If no candidate exists, choose the row with the smallest finite distance.
      4. If no row has finite distance, fall back to the first row.
    """
    if not rows:
        return None

    def score(row: Dict[str, Any]) -> Tuple[int, float]:
        is_220 = _parse_bool(row.get("is_220_candidate"))
        dist = _safe_float(row.get("kerr_220_distance"))
        if dist is None:
            dist = float("inf")
        return (0 if is_220 else 1, dist)

    finite_rows = [r for r in rows if _safe_float(r.get("kerr_220_distance")) is not None]
    candidate_rows = [r for r in rows if _parse_bool(r.get("is_220_candidate"))]
    if candidate_rows:
        return min(candidate_rows, key=score)
    if finite_rows:
        return min(finite_rows, key=score)
    return rows[0]


def poles_from_literature_rows(rows: List[Dict[str, Any]]) -> List[Pole]:
    """
    Build surrogate poles from literature rows.

    Only the selected row will be used in the current bridge because multiple
    literature rows for the same event are usually alternative analyses of the
    same 220 mode, not distinct physical poles. This helper stays list-based to
    keep parity with the ringdown-artifact branch.
    """
    poles: List[Pole] = []
    for row in rows:
        freq_hz = _safe_float(row.get("freq_hz"))
        damping = _safe_float(row.get("damping_hz"))
        if freq_hz is None or damping is None or freq_hz <= 0 or damping <= 0:
            continue
        amp_abs = _safe_float(row.get("amp_abs"))
        poles.append(
            Pole(
                freq_hz=float(freq_hz),
                damping_1_over_s=float(damping),
                amp_abs=float(amp_abs) if amp_abs is not None and amp_abs > 0 else 1.0,
            )
        )
    return poles


def pick_best_pair(cp_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    pairs = cp_payload.get("pairs", [])
    if not isinstance(pairs, list) or not pairs:
        return None
    # Best = minimal score_2d
    best = None
    best_score = float("inf")
    for p in pairs:
        try:
            s = float(p.get("score_2d"))
            if np.isfinite(s) and s < best_score:
                best_score = s
                best = p
        except Exception:
            continue
    return best


def compute_p_values_from_null(best_score: float, null_scores: List[float]) -> Tuple[Optional[float], Optional[float], int, int]:
    """
    Return:
      p_unc  = (n_better+1)/(N+1) where N includes invalid (non-finite) scores, but only finite count as "better"
      p_cond = (n_better+1)/(N_valid+1) where N_valid excludes invalid
    This mirrors Stage-01 smoothing style and provides an explicit conditional alternative.
    """
    if not np.isfinite(best_score) or not isinstance(null_scores, list) or len(null_scores) == 0:
        return None, None, 0, 0

    scores = np.array([float(s) for s in null_scores], dtype=float)
    finite = np.isfinite(scores)
    N = int(scores.size)
    N_valid = int(np.sum(finite))
    n_better = int(np.sum((scores[finite] <= best_score))) if N_valid > 0 else 0

    p_unc = float(n_better + 1) / float(N + 1)
    p_cond = float(n_better + 1) / float(N_valid + 1) if N_valid > 0 else None
    return p_unc, p_cond, N, N_valid


# ----------------------------
# Surrogate embeddings (data-driven, deterministic)
# ----------------------------

def get_normalization_scales(poles: List[Pole]) -> Tuple[float, float]:
    """
    Return (omega_dom_rads, gamma_dom_inv_s) from the dominant (max-amplitude) pole.

    These two scales define the dimensionless units shared with sandbox embeddings:
      omega_dimless = (2π f) / omega_dom_rads
      x_dimless     = t_seconds * gamma_dom_inv_s

    Falls back to generic stellar-mass BH values if no poles are available.
    """
    if not poles:
        return 2.0 * math.pi * 250.0, 50.0  # generic fallback (~GW150914-like)

    dom = max(poles, key=lambda p: p.amp_abs)
    omega_dom = 2.0 * math.pi * float(dom.freq_hz)
    gamma_dom = max(float(dom.damping_1_over_s), 1e-6)  # guard zero-damping
    return omega_dom, gamma_dom


def build_omega_grid_dimless(
    poles: List[Pole],
    n_omega: int,
    omega_dom_rads: float,
    fmin_hz: Optional[float],
    fmax_hz: Optional[float],
) -> np.ndarray:
    """
    Build dimensionless omega grid: omega_dimless = (2π f) / omega_dom_rads.

    The dominant pole sits at omega_dimless ≈ 1; other poles at their frequency ratios.
    This matches the sandbox embedding space (dimensionless AdS natural units).
    """
    if fmin_hz is not None and fmax_hz is not None and fmax_hz > fmin_hz > 0:
        lo = (2.0 * math.pi * float(fmin_hz)) / omega_dom_rads
        hi = (2.0 * math.pi * float(fmax_hz)) / omega_dom_rads
    elif poles:
        freqs_rads = np.array([2.0 * math.pi * p.freq_hz for p in poles], dtype=float)
        fmin_d = float(np.min(freqs_rads)) / omega_dom_rads
        fmax_d = float(np.max(freqs_rads)) / omega_dom_rads
        lo = max(1e-3, 0.5 * fmin_d)
        hi = max(lo + 1e-3, 1.5 * fmax_d)
    else:
        lo, hi = 0.1, 10.0  # match sandbox default range

    return np.linspace(lo, hi, int(n_omega), dtype=np.float64)


def poles_to_gr(
    omega_grid_dimless: np.ndarray,
    poles: List[Pole],
    omega_dom_rads: float,
    normalization: str = "unit_peak",
) -> Tuple[np.ndarray, np.ndarray]:
    """
    GR(ω̃) = Σ aₙ / (ω̃ - w̃ₙ)   with  w̃ₙ = (2πfₙ - iγₙ) / omega_dom_rads

    omega_grid_dimless is already in units of omega_dom (dominant pole sits at ~1).
    Poles are renormalized by the same scale so the Lorentzian shape is preserved.
    Returns real/imag arrays shaped (Nw, 1).
    """
    Nw = int(omega_grid_dimless.size)
    if not poles or Nw <= 0:
        return np.zeros((Nw, 1), dtype=np.float64), np.zeros((Nw, 1), dtype=np.float64)

    amps = np.array([max(p.amp_abs, 0.0) for p in poles], dtype=np.float64)
    if not np.any(amps > 0):
        amps = np.ones_like(amps)
    amps = amps / (float(np.max(amps)) + 1e-12)

    omega = omega_grid_dimless.astype(np.float64).reshape(-1, 1)  # (Nw, 1)

    w_poles = []
    for p, a in zip(poles, amps):
        w_real = (2.0 * math.pi * float(p.freq_hz)) / omega_dom_rads
        w_imag = float(p.damping_1_over_s) / omega_dom_rads
        w_poles.append((w_real - 1j * w_imag, float(a)))

    GR = np.zeros((Nw, 1), dtype=np.complex128)
    for w, a in w_poles:
        GR[:, 0] += a / (omega[:, 0] - w)

    if normalization == "unit_peak":
        mag = np.abs(GR[:, 0])
        mmax = float(np.max(mag)) if mag.size else 0.0
        if mmax > 0:
            GR[:, 0] /= mmax

    return np.real(GR).astype(np.float64), np.imag(GR).astype(np.float64)


def build_x_grid_dimless(
    n_x: int,
    x_min_dimless: float = 1e-3,
    x_max_dimless: float = 10.0,
    g2_time_contract: str = DEFAULT_G2_TIME_CONTRACT,
) -> np.ndarray:
    """
    Build the dimensionless x grid for the selected G2 time contract.

    omega_dom_v1:
      x_dimless = t_seconds * omega_dom_rads

    gamma_dom_v2:
      x_dimless = t_seconds * gamma_dom_inv_s

    The grid itself remains [x_min_dimless, x_max_dimless]; the contract only
    changes the physical meaning of the dimensionless unit used later in G2.
    """
    n_x = int(n_x)
    x0 = max(float(x_min_dimless), 1e-6)
    x1 = float(x_max_dimless)
    if not (x1 > x0 > 0.0):
        raise ValueError(f"Invalid dimless x range: x_min={x0}, x_max={x1}")
    if g2_time_contract not in (G2_TIME_CONTRACT_OMEGA_DOM_V1, G2_TIME_CONTRACT_GAMMA_DOM_V2):
        raise ValueError(f"Unsupported g2_time_contract: {g2_time_contract}")
    return np.linspace(x0, x1, n_x, dtype=np.float64)


def poles_to_g2(
    x_grid_dimless: np.ndarray,
    poles: List[Pole],
    omega_dom_rads: float,
    gamma_dom_inv_s: float,
    normalization: str = "unit_peak",
    g2_time_contract: str = DEFAULT_G2_TIME_CONTRACT,
) -> np.ndarray:
    """
    G2(x̃) = |Σ aₙ exp((-γ̃ₙ + iω̃ₙ) x̃)|²

    omega_dom_v1:
      γ̃ₙ = γₙ / omega_dom_rads,  ω̃ₙ = 2πfₙ / omega_dom_rads,  x̃ = t * omega_dom

    gamma_dom_v2:
      γ̃ₙ = γₙ / gamma_dom_inv_s, ω̃ₙ = 2πfₙ / gamma_dom_inv_s, x̃ = t * gamma_dom
    """
    Nx = int(x_grid_dimless.size)
    if not poles or Nx <= 0:
        return np.zeros((Nx,), dtype=np.float64)

    amps = np.array([max(p.amp_abs, 0.0) for p in poles], dtype=np.float64)
    if not np.any(amps > 0):
        amps = np.ones_like(amps)
    amps = amps / (float(np.max(amps)) + 1e-12)

    x = x_grid_dimless.astype(np.float64).reshape(-1, 1)
    s = np.zeros((Nx, 1), dtype=np.complex128)

    if g2_time_contract == G2_TIME_CONTRACT_OMEGA_DOM_V1:
        time_scale = omega_dom_rads
    elif g2_time_contract == G2_TIME_CONTRACT_GAMMA_DOM_V2:
        time_scale = gamma_dom_inv_s
    else:
        raise ValueError(f"Unsupported g2_time_contract: {g2_time_contract}")

    for p, a in zip(poles, amps):
        g_dimless = float(p.damping_1_over_s) / time_scale
        w_dimless = (2.0 * math.pi * float(p.freq_hz)) / time_scale
        s[:, 0] += float(a) * np.exp((-g_dimless + 1j * w_dimless) * x[:, 0])

    G2 = (np.abs(s[:, 0]) ** 2).astype(np.float64)

    if normalization == "unit_peak":
        mmax = float(np.max(G2)) if G2.size else 0.0
        if mmax > 0:
            G2 = G2 / mmax

    return G2


def make_sandbox_compatible_gr(gr_column: np.ndarray, n_k: int = SANDBOX_N_K) -> np.ndarray:
    """
    Broadcast a single-k response onto the sandbox k-grid expected by Stage 02.
    This is a contract-compatibility view, not a new physical inference.
    """
    gr_column = np.asarray(gr_column, dtype=np.float64)
    if gr_column.ndim == 2 and gr_column.shape[1] == 1:
        gr_line = gr_column[:, 0]
    elif gr_column.ndim == 1:
        gr_line = gr_column
    else:
        gr_line = gr_column.reshape(-1)
    return np.repeat(gr_line[np.newaxis, :], int(n_k), axis=0)


def make_sandbox_compatible_gr(gr_column: np.ndarray, n_k: int = SANDBOX_N_K) -> np.ndarray:
    """
    Broadcast a single-k response onto the sandbox k-grid expected by Stage 02.
    This is a contract-compatibility view, not a new physical inference.
    """
    gr_column = np.asarray(gr_column, dtype=np.float64)
    if gr_column.ndim == 2 and gr_column.shape[1] == 1:
        gr_line = gr_column[:, 0]
    elif gr_column.ndim == 1:
        gr_line = gr_column
    else:
        gr_line = gr_column.reshape(-1)
    return np.repeat(gr_line[np.newaxis, :], int(n_k), axis=0)


# ----------------------------
# Main
# ----------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Real-data bridge: build a stage-02 boundary dataset from "
            "ringdown artifacts or literature QNM datasets "
            "(poles -> surrogate boundary embeddings)."
        )
    )
    ap.add_argument("--run-dir", type=str, help="Run directory containing ringdown_* and data_boundary/")
    ap.add_argument("--ringdown-dirs", nargs="+", help="One or more ringdown_* subdirectories inside --run-dir")
    ap.add_argument(
        "--dataset-csv",
        type=str,
        help=(
            "Alternative input: qnm_dataset.csv-style literature dataset. "
            "One representative row is selected per event."
        ),
    )
    ap.add_argument("--out-dir", required=True, type=str, help="Output directory to create (will contain manifest.json and *.h5)")

    ap.add_argument("--d", type=int, default=4, help="Boundary dimension d to store (default: 4)")
    ap.add_argument("--temperature", type=float, default=0.0, help="Temperature metadata to store (default: 0.0)")

    ap.add_argument("--n-omega", type=int, default=256, help="Number of omega grid points (dimensionless)")
    ap.add_argument("--fmin-hz", type=float, default=None, help="Override omega grid min (Hz; converted internally to dimless)")
    ap.add_argument("--fmax-hz", type=float, default=None, help="Override omega grid max (Hz; converted internally to dimless)")
    ap.add_argument("--gr-normalization", type=str, default="unit_peak", choices=["unit_peak", "none"],
                    help="Normalize GR by max |GR| (unit_peak) or leave raw (none)")

    ap.add_argument("--n-x", type=int, default=256, help="Number of x grid points for raw ringdown embedding (dimensionless damping units)")
    ap.add_argument("--x-min-dimless", type=float, default=1e-3, help="Min dimensionless x for the selected G2 time contract")
    ap.add_argument("--x-max-dimless", type=float, default=10.0, help="Max dimensionless x for the selected G2 time contract")
    ap.add_argument("--g2-normalization", type=str, default="unit_peak", choices=["unit_peak", "none"],
                    help="Normalize G2 by max (unit_peak) or leave raw (none)")
    ap.add_argument(
        "--g2-time-contract",
        type=str,
        default=DEFAULT_G2_TIME_CONTRACT,
        choices=[G2_TIME_CONTRACT_OMEGA_DOM_V1, G2_TIME_CONTRACT_GAMMA_DOM_V2],
        help="Dimensionless time contract for G2 construction: legacy omega_dom_v1 or versioned gamma_dom_v2.",
    )
    ap.add_argument(
        "--g2-contract-autoselect",
        action="store_true",
        default=False,
        help="Automatically switch to gamma_dom_v2 if observed G2 is saturated (all points >= 0.99).",
    )
    ap.add_argument(
        "--saturation-tail-threshold",
        type=float,
        default=SATURATION_TAIL_THRESHOLD,
        help=f"Threshold for saturation detection on observed G2 (default: {SATURATION_TAIL_THRESHOLD}).",
    )
    ap.add_argument(
        "--compat-mode",
        type=str,
        default="stage02_sandbox_v5",
        choices=["none", "stage02_sandbox_v5"],
        help="Compatibility view to emit in canonical boundary datasets.",
    )

    args = ap.parse_args()
    out_dir = resolve_root_relative(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    using_ringdown_dirs = bool(args.run_dir or args.ringdown_dirs)
    using_dataset_csv = bool(args.dataset_csv)
    if using_ringdown_dirs == using_dataset_csv:
        raise SystemExit(
            "[ERROR] Debes pasar exactamente una fuente de entrada: "
            "(--run-dir + --ringdown-dirs) o --dataset-csv"
        )

    run_dir: Optional[Path] = None
    event_id = None
    dataset_csv_path: Optional[Path] = None
    if using_ringdown_dirs:
        if not args.run_dir or not args.ringdown_dirs:
            raise SystemExit("[ERROR] Para la ruta de ringdown debes pasar --run-dir y --ringdown-dirs")
        run_dir = resolve_root_relative(args.run_dir)
        db_dir = run_dir / "data_boundary"
        if db_dir.exists() and db_dir.is_dir():
            candidates = sorted(db_dir.glob("*_boundary.h5"))
            if candidates:
                event_id = candidates[0].name.replace("_boundary.h5", "")
        if event_id is None:
            event_id = run_dir.name
    else:
        dataset_csv_path = resolve_root_relative(args.dataset_csv)
        event_id = dataset_csv_path.stem

    print("=" * 70)
    print("REAL-DATA BRIDGE — Ringdown/Literature -> stage-02 boundary dataset")
    print(f"Script:    {SCRIPT_VERSION}")
    if run_dir is not None:
        print(f"Run dir:   {run_dir}")
    if dataset_csv_path is not None:
        print(f"Dataset:   {dataset_csv_path}")
    print(f"Out dir:   {out_dir}")
    print(f"Event id:  {event_id}")
    print("=" * 70)

    manifest: Dict[str, Any] = {
        "created_at": utc_now_iso(),
        "script": SCRIPT_VERSION,
        "version": "realdata-ringdown-to-stage02-boundary-v1",
        "family_status": get_family_status("unknown", source="realdata"),
        "family_status_description": get_family_status_description(
            get_family_status("unknown", source="realdata")
        ),
        "source_run_dir": "" if run_dir is None else str(run_dir),
        "source_dataset_csv": "" if dataset_csv_path is None else str(dataset_csv_path),
        "event_id": event_id,
        "config": {
            "d": int(args.d),
            "temperature": float(args.temperature),
            "n_omega": int(args.n_omega),
            "fmin_hz": None if args.fmin_hz is None else float(args.fmin_hz),
            "fmax_hz": None if args.fmax_hz is None else float(args.fmax_hz),
            "gr_normalization": args.gr_normalization,
            "n_x": int(args.n_x),
            "x_min_dimless": float(args.x_min_dimless),
            "x_max_dimless": float(args.x_max_dimless),
            "g2_normalization": args.g2_normalization,
            "g2_time_contract": args.g2_time_contract,
            "g2_contract_autoselect": args.g2_contract_autoselect,
            "saturation_tail_threshold": args.saturation_tail_threshold,
            "compat_mode": args.compat_mode,
            "k_grid": [0.0],
            "embedding_space": "dimensionless_dominant_pole",
        },
        "geometries": [],
    }

    omega_grid_hz = None  # build per-system if auto bounds depend on poles

    if using_dataset_csv:
        by_event = load_literature_dataset(dataset_csv_path)
        sorted_items = sorted(by_event.items(), key=lambda kv: kv[0])
        input_items = []
        for ev_name, rows in sorted_items:
            selected = select_literature_row(rows)
            if selected is None:
                continue
            poles = poles_from_literature_rows([selected])
            if not poles:
                print(f"  [SKIP] {ev_name}: no freq/damping finite after literature selection")
                continue
            input_items.append(
                {
                    "kind": "literature",
                    "event_name": ev_name,
                    "system_name": ev_name,
                    "poles": poles,
                    "poles_payload": {
                        "selected_row": selected,
                        "all_rows_for_event": rows,
                        "selection_policy": "best_220_candidate_then_min_kerr_distance",
                    },
                    "cp_payload": {},
                    "null_payload": {},
                    "best_pair": None,
                    "best_score": None,
                    "best_p_value_stage01": None,
                    "null_scores": None,
                    "null_stats": {},
                    "n_invalid": None,
                    "n_trials": None,
                    "source_ringdown_dir": f"literature://{ev_name}",
                    "source_poles_file": str(dataset_csv_path),
                    "source_coincident_pairs_file": "",
                    "source_null_test_file": "",
                    "metadata_attrs": {
                        "source_dataset_csv": str(dataset_csv_path),
                        "source_analysis_method": str(selected.get("pole_source", "")),
                        "source_ifo": str(selected.get("ifo", "")),
                        "source_mode_rank": int(float(selected.get("mode_rank", 0) or 0)),
                        "literature_rows_for_event": int(len(rows)),
                        "literature_kerr_220_distance": float(selected["kerr_220_distance"])
                        if _safe_float(selected.get("kerr_220_distance")) is not None else np.nan,
                        "literature_is_220_candidate": bool(_parse_bool(selected.get("is_220_candidate"))),
                        "literature_selection_policy": "best_220_candidate_then_min_kerr_distance",
                    },
                }
            )
    else:
        input_items = []
        for rd in args.ringdown_dirs:
            rd_rel = Path(rd)
            _reject_dotdot(rd_rel)
            rd_dir = (run_dir / rd_rel).resolve(strict=False)
            try:
                rd_dir.relative_to(run_dir)
            except Exception:
                raise ValueError(f"ringdown-dir escapes run_dir: {rd} -> {rd_dir}")

            if not rd_dir.exists() or not rd_dir.is_dir():
                raise FileNotFoundError(f"Ringdown dir not found: {rd_dir}")

            poles_path = rd_dir / "poles_joint.json"
            if not poles_path.exists():
                alt = sorted(rd_dir.glob("poles_*.json"))
                poles_path = alt[0] if alt else poles_path

            cp_path = rd_dir / "coincident_pairs.json"
            null_path = rd_dir / "null_test.json"

            poles_payload = read_json(poles_path) if poles_path.exists() else {}
            cp_payload = read_json(cp_path) if cp_path.exists() else {}
            null_payload = read_json(null_path) if null_path.exists() else {}

            poles = parse_poles_json(poles_payload)
            best_pair = pick_best_pair(cp_payload)
            best_score = None
            best_p_value_stage01 = None
            if best_pair is not None:
                try:
                    best_score = float(best_pair.get("score_2d"))
                except Exception:
                    best_score = None
                try:
                    pv = best_pair.get("p_value", None)
                    best_p_value_stage01 = None if pv is None else float(pv)
                except Exception:
                    best_p_value_stage01 = None

            null_scores = _safe_get(null_payload, ["null_test", "scores_per_trial"], default=None)
            null_stats = _safe_get(null_payload, ["null_test", "statistics"], default={}) or {}
            n_invalid = None
            n_trials = None
            if isinstance(null_stats, dict):
                try:
                    n_invalid = int(null_stats.get("n_invalid_trials")) if "n_invalid_trials" in null_stats else None
                except Exception:
                    n_invalid = None
            if isinstance(null_scores, list):
                n_trials = int(len(null_scores))

            input_items.append(
                {
                    "kind": "ringdown",
                    "event_name": event_id,
                    "system_name": f"{event_id}__{rd_rel.name}",
                    "poles": poles,
                    "poles_payload": poles_payload,
                    "cp_payload": cp_payload,
                    "null_payload": null_payload,
                    "best_pair": best_pair,
                    "best_score": best_score,
                    "best_p_value_stage01": best_p_value_stage01,
                    "null_scores": null_scores,
                    "null_stats": null_stats,
                    "n_invalid": n_invalid,
                    "n_trials": n_trials,
                    "source_ringdown_dir": str(rd_rel.as_posix()),
                    "source_poles_file": str(poles_path),
                    "source_coincident_pairs_file": str(cp_path) if cp_path.exists() else "",
                    "source_null_test_file": str(null_path) if null_path.exists() else "",
                    "metadata_attrs": {},
                }
            )

    for item in input_items:
        poles = item["poles"]
        poles_payload = item["poles_payload"]
        cp_payload = item["cp_payload"]
        null_payload = item["null_payload"]
        best_pair = item["best_pair"]
        best_score = item["best_score"]
        best_p_value_stage01 = item["best_p_value_stage01"]
        null_scores = item["null_scores"]
        null_stats = item["null_stats"]
        n_invalid = item["n_invalid"]
        n_trials = item["n_trials"]
        system_name = item["system_name"]
        item_event_id = item["event_name"]

        # compute p-values (explicit unconditional + conditional)
        p_unc = p_cond = None
        N = N_valid = 0
        if best_score is not None and isinstance(null_scores, list):
            p_unc, p_cond, N, N_valid = compute_p_values_from_null(best_score, null_scores)

        # Normalization scales from dominant pole (makes embeddings dimensionless,
        # comparable to sandbox embeddings trained in AdS natural units)
        omega_dom_rads, gamma_dom_inv_s = get_normalization_scales(poles)

        # Build dimensionless grids and surrogate boundary embeddings
        omega_grid_dimless_raw = build_omega_grid_dimless(
            poles, args.n_omega, omega_dom_rads, args.fmin_hz, args.fmax_hz
        )
        k_grid_raw = np.array([0.0], dtype=np.float64)

        GR_real_raw, GR_imag_raw = poles_to_gr(
            omega_grid_dimless_raw,
            poles,
            omega_dom_rads,
            normalization=args.gr_normalization,
        )

        # Step 1: Build G2 with the requested contract
        x_grid_raw = build_x_grid_dimless(
            args.n_x,
            args.x_min_dimless,
            args.x_max_dimless,
            g2_time_contract=args.g2_time_contract,
        )
        G2_ringdown_raw = poles_to_g2(
            x_grid_raw,
            poles,
            omega_dom_rads,
            gamma_dom_inv_s,
            normalization=args.g2_normalization,
            g2_time_contract=args.g2_time_contract,
        )

        # Step 2: Detect observed saturation and autoselect if needed
        effective_g2_time_contract = args.g2_time_contract
        g2_contract_autoselected = False
        observed_saturation_detected = False
        saturation_meta: Dict[str, Any] = {}

        if args.g2_contract_autoselect and args.g2_time_contract == G2_TIME_CONTRACT_OMEGA_DOM_V1:
            is_saturated, saturation_meta = detect_observed_saturation(
                G2_ringdown_raw,
                tail_threshold=args.saturation_tail_threshold,
                fraction_threshold=SATURATION_FRACTION_THRESHOLD,
            )
            if is_saturated:
                observed_saturation_detected = True
                effective_g2_time_contract = G2_TIME_CONTRACT_GAMMA_DOM_V2
                g2_contract_autoselected = True
                print(f"  [AUTOSELECT] Observed saturation for {item_event_id}: "
                      f"g2_last={saturation_meta['g2_last']:.6f}, "
                      f"n_ge_threshold={saturation_meta['n_ge_threshold']}/{saturation_meta['n_points']}. "
                      f"Rebuilding with {G2_TIME_CONTRACT_GAMMA_DOM_V2}.")
                # Step 3: Rebuild G2 with gamma_dom_v2
                x_grid_raw = build_x_grid_dimless(
                    args.n_x,
                    args.x_min_dimless,
                    args.x_max_dimless,
                    g2_time_contract=effective_g2_time_contract,
                )
                G2_ringdown_raw = poles_to_g2(
                    x_grid_raw,
                    poles,
                    omega_dom_rads,
                    gamma_dom_inv_s,
                    normalization=args.g2_normalization,
                    g2_time_contract=effective_g2_time_contract,
                )

        g2_repr_contract, g2_canonical_x_max = resolve_g2_repr_contract(effective_g2_time_contract)

        if args.compat_mode == "stage02_sandbox_v5":
            omega_grid_dimless = np.linspace(SANDBOX_OMEGA_MIN, SANDBOX_OMEGA_MAX, SANDBOX_N_OMEGA, dtype=np.float64)
            k_grid = np.linspace(SANDBOX_K_MIN, SANDBOX_K_MAX, SANDBOX_N_K, dtype=np.float64)
            GR_real_line, GR_imag_line = poles_to_gr(
                omega_grid_dimless,
                poles,
                omega_dom_rads,
                normalization=args.gr_normalization,
            )
            GR_real = make_sandbox_compatible_gr(GR_real_line, SANDBOX_N_K)
            GR_imag = make_sandbox_compatible_gr(GR_imag_line, SANDBOX_N_K)
            try:
                g2_contract = canonicalize_g2_representation(
                    x_grid_raw,
                    G2_ringdown_raw,
                    n_x=SANDBOX_N_X,
                    x_min=SANDBOX_X_MIN,
                    x_max=g2_canonical_x_max,
                )
            except G2RepresentationContractError as exc:
                raise SystemExit(
                    f"[ERROR] failed to canonicalize G2 representation for {event_id}: {exc}"
                ) from exc
            x_grid = g2_contract.x_grid
            G2_ringdown = g2_contract.g2_canonical
            contract_attrs = {
                "x_grid_raw_range": np.asarray(g2_contract.meta["x_grid_raw_range"], dtype=np.float64),
                "x_grid_canon_range": np.asarray(g2_contract.meta["x_grid_canon_range"], dtype=np.float64),
                "omega_grid_raw_range": np.asarray(
                    [float(np.nanmin(omega_grid_dimless_raw)), float(np.nanmax(omega_grid_dimless_raw))],
                    dtype=np.float64,
                ),
                "omega_grid_compat_range": np.asarray(
                    [float(np.nanmin(omega_grid_dimless)), float(np.nanmax(omega_grid_dimless))],
                    dtype=np.float64,
                ),
                "G_R_raw_shape": np.asarray(GR_real_raw.shape, dtype=np.int64),
                "G_R_compat_shape": np.asarray(GR_real.shape, dtype=np.int64),
                "g2_interp_mode": g2_contract.meta["g2_interp_mode"],
                "g2_norm_mode": g2_contract.meta["g2_norm_mode"],
                "g2_repr_contract": g2_repr_contract,
                "g2_canonical_x_max": float(g2_canonical_x_max),
            }
        else:
            omega_grid_dimless = omega_grid_dimless_raw
            k_grid = k_grid_raw
            x_grid = x_grid_raw
            GR_real = GR_real_raw
            GR_imag = GR_imag_raw
            G2_ringdown = G2_ringdown_raw
            contract_attrs = {}

        # Output HDF5
        out_h5 = out_dir / f"{system_name}.h5"

        with h5py.File(out_h5, "w") as f:
            family_status = get_family_status("unknown", source="realdata")
            # File-level attrs
            f.attrs["created_at"] = utc_now_iso()
            f.attrs["script"] = SCRIPT_VERSION
            f.attrs["name"] = system_name
            f.attrs["system_name"] = system_name
            f.attrs["category"] = "ringdown"
            f.attrs["family"] = "unknown"
            f.attrs["family_status"] = family_status
            f.attrs["family_status_description"] = get_family_status_description(family_status)
            f.attrs["operators"] = "[]"  # boundary-only: no operator spectrum provided

            # boundary group (what Stage 02 consumes)
            b = f.create_group("boundary")
            if args.compat_mode == "stage02_sandbox_v5":
                b.create_dataset("omega_grid_raw", data=omega_grid_dimless_raw)
                b.create_dataset("k_grid_raw", data=k_grid_raw)
                b.create_dataset("G_R_real_raw", data=GR_real_raw)
                b.create_dataset("G_R_imag_raw", data=GR_imag_raw)
                b.create_dataset("x_grid_raw", data=x_grid_raw)
                b.create_dataset("G2_ringdown_raw", data=G2_ringdown_raw)
            b.create_dataset("omega_grid", data=omega_grid_dimless)
            b.create_dataset("k_grid", data=k_grid)
            # Normalization scales (for reproducibility and inverse-mapping)
            b.attrs["omega_dom_rads"] = float(omega_dom_rads)
            b.attrs["gamma_dom_inv_s"] = float(gamma_dom_inv_s)
            b.attrs["embedding_space"] = "dimensionless_omega_dom"
            b.attrs["g2_time_contract"] = effective_g2_time_contract
            b.attrs["g2_time_contract_requested"] = args.g2_time_contract
            b.attrs["g2_contract_autoselected"] = g2_contract_autoselected
            b.attrs["observed_saturation_detected"] = observed_saturation_detected
            if saturation_meta:
                b.attrs["saturation_g2_last"] = float(saturation_meta.get("g2_last", 0.0))
                b.attrs["saturation_n_ge_threshold"] = int(saturation_meta.get("n_ge_threshold", 0))
                b.attrs["saturation_fraction_ge_threshold"] = float(saturation_meta.get("fraction_ge_threshold", 0.0))
            b.attrs["g2_time_scale_attr"] = (
                "gamma_dom_inv_s"
                if effective_g2_time_contract == G2_TIME_CONTRACT_GAMMA_DOM_V2
                else "omega_dom_rads"
            )
            b.attrs["g2_time_space"] = (
                "dimensionless_gamma_dom"
                if effective_g2_time_contract == G2_TIME_CONTRACT_GAMMA_DOM_V2
                else "dimensionless_omega_dom"
            )
            b.attrs["g2_repr_contract"] = g2_repr_contract
            b.attrs["g2_canonical_x_max"] = float(g2_canonical_x_max)
            b.attrs["compat_mode"] = args.compat_mode
            if args.compat_mode == "stage02_sandbox_v5":
                for attr_key, attr_value in contract_attrs.items():
                    b.attrs[attr_key] = attr_value
                b.attrs["g2_eps"] = float(g2_contract.meta["eps"])
                b.attrs["g2_valid_points"] = int(g2_contract.meta["n_valid_after_filter"])
                b.attrs["g2_unique_points"] = int(g2_contract.meta["n_unique_after_dedup"])
            b.create_dataset("G_R_real", data=GR_real)
            b.create_dataset("G_R_imag", data=GR_imag)
            b.create_dataset("x_grid", data=x_grid)
            b.create_dataset("G2_ringdown", data=G2_ringdown)
            if args.compat_mode == "stage02_sandbox_v5":
                b.create_dataset("G2_O1", data=G2_ringdown)
                b.create_dataset("central_charge_eff", data=np.array([0.0], dtype=np.float64))

            b.attrs["d"] = int(args.d)
            b.attrs["family"] = "unknown"
            b.attrs["family_status"] = family_status
            b.attrs["family_status_description"] = get_family_status_description(family_status)
            b.attrs["temperature"] = float(args.temperature)
            b.attrs["T"] = float(args.temperature)

            # QNM-derived features (parallel to sandbox qnm_numerical.json attrs).
            # Primary discriminators between geometry families; replace Δ operator
            # features which are 0 for LIGO data (no CFT operator spectrum).
            if poles:
                dom = max(poles, key=lambda p: p.amp_abs)
                Q0 = math.pi * dom.freq_hz / dom.damping_1_over_s if dom.damping_1_over_s > 0 else 0.0
                if len(poles) >= 2:
                    sub = sorted(poles, key=lambda p: -p.amp_abs)
                    f0_v, f1_v = sub[0].freq_hz, sub[1].freq_hz
                    g0_v, g1_v = sub[0].damping_1_over_s, sub[1].damping_1_over_s
                    f1f0 = f1_v / f0_v if f0_v > 0 else 0.0
                    g1g0 = g1_v / g0_v if g0_v > 0 else 0.0
                else:
                    f1f0, g1g0 = 0.0, 0.0
                b.attrs["qnm_Q0"]      = float(Q0)
                b.attrs["qnm_f1f0"]    = float(f1f0)
                b.attrs["qnm_g1g0"]    = float(g1g0)
                b.attrs["qnm_n_modes"] = int(len(poles))
            else:
                b.attrs["qnm_Q0"]      = 0.0
                b.attrs["qnm_f1f0"]    = 0.0
                b.attrs["qnm_g1g0"]    = 0.0
                b.attrs["qnm_n_modes"] = 0

            # provenance / quality metadata (attrs for quick audit)
            b.attrs["source_run_dir"] = "" if run_dir is None else str(run_dir)
            b.attrs["source_ringdown_dir"] = item["source_ringdown_dir"]
            b.attrs["source_poles_file"] = item["source_poles_file"]
            b.attrs["source_coincident_pairs_file"] = item["source_coincident_pairs_file"]
            b.attrs["source_null_test_file"] = item["source_null_test_file"]
            for meta_key, meta_value in item["metadata_attrs"].items():
                b.attrs[meta_key] = meta_value

            if best_score is not None and np.isfinite(best_score):
                b.attrs["best_score_2d"] = float(best_score)
            if best_p_value_stage01 is not None and np.isfinite(best_p_value_stage01):
                b.attrs["best_p_value_stage01"] = float(best_p_value_stage01)

            if p_unc is not None and np.isfinite(p_unc):
                b.attrs["p_value_unconditional_including_invalid"] = float(p_unc)
            if p_cond is not None and np.isfinite(p_cond):
                b.attrs["p_value_conditional_valid_only"] = float(p_cond)

            if n_trials is not None:
                b.attrs["null_n_trials"] = int(n_trials)
            if n_invalid is not None:
                b.attrs["null_n_invalid_trials"] = int(n_invalid)
            if N:
                b.attrs["null_N_scores_total"] = int(N)
            if N_valid:
                b.attrs["null_N_scores_valid"] = int(N_valid)

            # raw ringdown JSON snapshots (for full traceability)
            raw = f.create_group("ringdown_raw")
            raw.create_dataset("poles_json", data=np.bytes_(json.dumps(poles_payload)))
            raw.create_dataset("coincident_pairs_json", data=np.bytes_(json.dumps(cp_payload)))
            raw.create_dataset("null_test_json", data=np.bytes_(json.dumps(null_payload)))

        # manifest entry
        manifest["geometries"].append(
            {
                "name": system_name,
                "family": "unknown",
                "family_status": get_family_status("unknown", source="realdata"),
                "category": "ringdown",
                "d": int(args.d),
                "file": str(out_h5.name),
                "source_kind": item["kind"],
                "source_ringdown_dir": item["source_ringdown_dir"],
                "poles_file": Path(item["source_poles_file"]).name if item["source_poles_file"] else "",
                "has_null_test": bool(item["source_null_test_file"]),
                "has_coincident_pairs": bool(item["source_coincident_pairs_file"]),
            }
        )

        print(f"[OK] wrote: {out_h5}")

    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[OK] wrote: {manifest_path}")

    print("=" * 70)
    print("[OK] real-data bridge completed")
    print("Next step: 02_emergent_geometry_engine.py --mode inference --data-dir <OUT_DIR> --checkpoint <MODEL>")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
