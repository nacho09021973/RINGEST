from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np


CANONICAL_X_MIN = 1e-3
CANONICAL_X_MAX = 10.0
CANONICAL_N_X = 100
DEFAULT_G2_EPS = 1e-12
DEFAULT_COMPAT_MODE = "stage02_sandbox_v5"
DEFAULT_COMPAT_CONTRACT = "sandbox_v5_stage02"
DEFAULT_G2_REPR_CONTRACT = "logx_logg2_interp_unit_peak_v1"
DEFAULT_G2_INTERP_MODE = "logx_logg2"
DEFAULT_G2_NORM_MODE = "unit_peak"


class G2RepresentationContractError(RuntimeError):
    """Raised when raw G2/x samples cannot be canonicalized safely."""


@dataclass(frozen=True)
class CanonicalG2Representation:
    x_grid_raw: np.ndarray
    g2_raw: np.ndarray
    x_grid: np.ndarray
    g2_canonical: np.ndarray
    eps: float
    n_valid_points: int
    n_unique_points: int


def build_canonical_x_grid(
    n_points: int = CANONICAL_N_X,
    x_min: float = CANONICAL_X_MIN,
    x_max: float = CANONICAL_X_MAX,
) -> np.ndarray:
    n_points = int(n_points)
    x_min = float(x_min)
    x_max = float(x_max)
    if n_points <= 1:
        raise G2RepresentationContractError("canonical x_grid requires at least 2 points")
    if not np.isfinite(x_min) or not np.isfinite(x_max) or x_min <= 0.0 or x_max <= x_min:
        raise G2RepresentationContractError(
            f"invalid canonical x range: x_min={x_min}, x_max={x_max}"
        )
    return np.linspace(x_min, x_max, n_points, dtype=np.float64)


def _coerce_1d_float64(name: str, values: np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64).reshape(-1)
    if arr.size == 0:
        raise G2RepresentationContractError(f"{name} is empty")
    return arr


def _prepare_unique_valid_samples(
    x_grid_raw: np.ndarray,
    g2_raw: np.ndarray,
    *,
    eps: float,
) -> Tuple[np.ndarray, np.ndarray, int]:
    x_raw = _coerce_1d_float64("x_grid_raw", x_grid_raw)
    g2 = _coerce_1d_float64("g2_raw", g2_raw)
    if x_raw.size != g2.size:
        raise G2RepresentationContractError(
            f"x_grid_raw and g2_raw size mismatch: {x_raw.size} != {g2.size}"
        )

    mask = np.isfinite(x_raw) & np.isfinite(g2) & (x_raw > 0.0) & ((g2 + eps) > 0.0)
    n_valid = int(np.sum(mask))
    if n_valid < 3:
        raise G2RepresentationContractError(
            f"insufficient valid G2/x samples after filtering: {n_valid}"
        )

    x_valid = x_raw[mask]
    g2_valid = g2[mask]
    order = np.argsort(x_valid, kind="mergesort")
    x_sorted = x_valid[order]
    log_g2_sorted = np.log(g2_valid[order] + eps)

    unique_x, inverse = np.unique(x_sorted, return_inverse=True)
    if unique_x.size < 3:
        raise G2RepresentationContractError(
            f"insufficient unique x samples after deduplication: {unique_x.size}"
        )

    log_g2_unique = np.zeros(unique_x.shape, dtype=np.float64)
    counts = np.zeros(unique_x.shape, dtype=np.int64)
    np.add.at(log_g2_unique, inverse, log_g2_sorted)
    np.add.at(counts, inverse, 1)
    log_g2_unique = log_g2_unique / counts
    return unique_x.astype(np.float64), log_g2_unique.astype(np.float64), n_valid


def canonicalize_g2_representation(
    x_grid_raw: np.ndarray,
    g2_raw: np.ndarray,
    *,
    eps: float = DEFAULT_G2_EPS,
    n_points: int = CANONICAL_N_X,
    x_min: float = CANONICAL_X_MIN,
    x_max: float = CANONICAL_X_MAX,
) -> CanonicalG2Representation:
    eps = float(eps)
    if not np.isfinite(eps) or eps <= 0.0:
        raise G2RepresentationContractError(f"eps must be finite and positive, got {eps}")

    x_raw = _coerce_1d_float64("x_grid_raw", x_grid_raw)
    g2 = _coerce_1d_float64("g2_raw", g2_raw)
    unique_x, log_g2_unique, n_valid = _prepare_unique_valid_samples(x_raw, g2, eps=eps)

    x_grid = build_canonical_x_grid(n_points=n_points, x_min=x_min, x_max=x_max)
    log_x_unique = np.log(unique_x)
    log_x_target = np.log(x_grid)
    log_g2_target = np.interp(
        log_x_target,
        log_x_unique,
        log_g2_unique,
        left=float(log_g2_unique[0]),
        right=float(log_g2_unique[-1]),
    )

    g2_target = np.exp(log_g2_target) - eps
    g2_target = np.clip(g2_target, 0.0, None).astype(np.float64)
    peak = float(np.max(g2_target)) if g2_target.size else 0.0
    if not np.isfinite(peak) or peak <= 0.0:
        raise G2RepresentationContractError("canonical G2 peak is not positive and finite")
    g2_target /= peak

    return CanonicalG2Representation(
        x_grid_raw=x_raw.astype(np.float64),
        g2_raw=g2.astype(np.float64),
        x_grid=x_grid,
        g2_canonical=g2_target.astype(np.float64),
        eps=eps,
        n_valid_points=n_valid,
        n_unique_points=int(unique_x.size),
    )


def build_stage02_contract_attrs(
    *,
    x_grid_raw: np.ndarray,
    x_grid_canon: np.ndarray,
    omega_grid_raw: np.ndarray,
    omega_grid_compat: np.ndarray,
    g_r_raw_shape: Tuple[int, ...],
    g_r_compat_shape: Tuple[int, ...],
    compat_mode: str = DEFAULT_COMPAT_MODE,
    compat_contract: str = DEFAULT_COMPAT_CONTRACT,
    compat_note: str = (
        "canonical datasets are deterministic representation-gauge views for Stage 02; "
        "raw ringdown embeddings are preserved in *_raw datasets"
    ),
    g2_repr_contract: str = DEFAULT_G2_REPR_CONTRACT,
    g2_interp_mode: str = DEFAULT_G2_INTERP_MODE,
    g2_norm_mode: str = DEFAULT_G2_NORM_MODE,
) -> Dict[str, str]:
    x_grid_raw = _coerce_1d_float64("x_grid_raw", x_grid_raw)
    x_grid_canon = _coerce_1d_float64("x_grid_canon", x_grid_canon)
    omega_grid_raw = _coerce_1d_float64("omega_grid_raw", omega_grid_raw)
    omega_grid_compat = _coerce_1d_float64("omega_grid_compat", omega_grid_compat)

    return {
        "compat_mode": str(compat_mode),
        "compat_contract": str(compat_contract),
        "compat_note": str(compat_note),
        "g2_repr_contract": str(g2_repr_contract),
        "g2_interp_mode": str(g2_interp_mode),
        "g2_norm_mode": str(g2_norm_mode),
        "x_grid_raw_range": json.dumps([float(x_grid_raw[0]), float(x_grid_raw[-1])]),
        "x_grid_canon_range": json.dumps([float(x_grid_canon[0]), float(x_grid_canon[-1])]),
        "omega_grid_raw_range": json.dumps([float(omega_grid_raw[0]), float(omega_grid_raw[-1])]),
        "omega_grid_compat_range": json.dumps([float(omega_grid_compat[0]), float(omega_grid_compat[-1])]),
        "G_R_raw_shape": json.dumps(list(g_r_raw_shape)),
        "G_R_compat_shape": json.dumps(list(g_r_compat_shape)),
    }
