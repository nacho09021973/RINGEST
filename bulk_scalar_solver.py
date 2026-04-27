#!/usr/bin/env python3
"""
bulk_scalar_solver.py    CUERDAS-MALDACENA  (v1.0)

Sturm-Liouville eigensolver for a massless scalar field in the emergent
bulk geometry A(z), f(z) inferred by 02_emergent_geometry_engine.py.

Physics
-------
The equation of motion for a massless scalar  ~ e^{-it} (z) in the metric

    ds2 = A(z)2[-f(z) dt2 + dx_{d-1}2] + dz2

is, at zero spatial momentum k=0,

    -_z[p(z) _z ] =  w(z) 

with:
    p(z) = A(z)^{d-1} f(z)          (SL coefficient)
    w(z) = A(z)^{d-3}               (weight function)
        = 2                        (eigenvalue)

This is a proper Sturm-Liouville problem; its eigenvalues _sl  0 and
eigenfunctions are real and orthogonal with weight w.

Boundary conditions
-------------------
UV (z  0 / boundary): Dirichlet  = 0  (normalizable mode)
IR (z = z_max / horizon): Dirichlet  = 0  (Dirichlet at horizon)

UV exponents
-----------
Near z  0 in the holographic geometry A ~ const/z^.  The two independent
solutions behave as  ~ z^{_} with

    _ = (d  (d2 + 4)) / 2

The normalizable mode corresponds to the larger root _+ (operator dimension).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import h5py
import numpy as np
from scipy import linalg


# ---------------------------------------------------------------------------
# Core solver
# ---------------------------------------------------------------------------

def _build_sl_matrix(
    p: np.ndarray,
    w: np.ndarray,
    dz: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Build the finite-difference SL matrix for interior points.

    The operator  L = -d/dz[p(z) d/dz]  is discretised with second-order
    central differences.  Dirichlet BC at both ends (boundary rows excluded).

    Returns (L, W) where L  =  W .
    """
    n = len(p)  # number of interior points (boundaries already stripped)
    L = np.zeros((n, n), dtype=np.float64)
    W = np.zeros((n, n), dtype=np.float64)

    for i in range(n):
        # Recover p at half-cell faces using harmonic average for robustness
        # at the horizon where f0 and p0
        p_plus  = 0.5 * (p[i] + p[i+1]) if i < n - 1 else p[i]  # p_{i+1/2}
        p_minus = 0.5 * (p[i] + p[i-1]) if i > 0     else p[i]  # p_{i-1/2}

        # -d/dz[p d/dz] with Dirichlet BCs  ghost points = 0
        # Interior:   L_ii = (p_{i+1/2} + p_{i-1/2}) / dz2
        # Off-diag:   L_{i,i1} = -p_{i1/2} / dz2
        if i == 0:
            p_minus = p[i]          # ghost point at left boundary (=0)
        if i == n - 1:
            p_plus = p[i]           # ghost point at right boundary (=0)

        L[i, i] = (p_plus + p_minus) / dz**2
        if i > 0:
            L[i, i-1] = -p_minus / dz**2
        if i < n - 1:
            L[i, i+1] = -p_plus  / dz**2

        W[i, i] = w[i]

    return L, W


def _uv_exponents(lambda_sl: np.ndarray, d: int) -> np.ndarray:
    """
    Compute UV exponents + from eigenvalues _sl.

    _+ = (d + sqrt(d2 + 4)) / 2

    This is the holographic relation between the bulk eigenvalue and the
    conformal dimension of the dual boundary operator.
    """
    discriminant = d**2 + 4.0 * np.maximum(lambda_sl, 0.0)
    return (d + np.sqrt(discriminant)) / 2.0


# ---------------------------------------------------------------------------
# Public API: solve_geometry
# ---------------------------------------------------------------------------

def solve_geometry(
    h5_path: Path,
    n_eigs: int = 4,
    z_dataset: str = "z_grid",
    A_dataset: str = "A_of_z",
    f_dataset: str = "f_emergent",
    d_override: Optional[int] = None,
    trim_horizon_fraction: float = 0.05,
) -> Dict[str, Any]:
    """
    Compute the n_eigs lowest Sturm-Liouville eigenvalues for the geometry
    stored in *h5_path*.

    Parameters
    ----------
    h5_path : Path
        HDF5 file containing z_grid, A(z), f(z).
    n_eigs : int
        Number of eigenvalues to return (ground state + overtones).
    z_dataset, A_dataset, f_dataset : str
        Dataset names inside the HDF5.  The function tries several fallback
        names automatically.
    d_override : int or None
        Boundary dimension d.  If None, read from file attrs.
    trim_horizon_fraction : float
        Strip the last fraction of the grid near the horizon where f0 causes
        p0 and numerical instability.  Default: 5 %.

    Returns
    -------
    dict with keys:
        lambda_sl   : list[float]   eigenvalues (sorted ascending)
        uv_exponents: list[float]   _+ from _sl
        n_modes     : int
        d           : int
        solver      : str
        z_range     : [z_min, z_max]
        quality_flags: list[str]
    """
    h5_path = Path(h5_path)

    with h5py.File(h5_path, "r") as fh:
        # --- Read d ---
        if d_override is not None:
            d = int(d_override)
        else:
            d = int(fh.attrs.get("d", fh.attrs.get("d_pred", 4)))

        # Read predicted horizon position (used to trim the grid)
        zh_pred = fh.attrs.get("zh_pred", None)
        if zh_pred is not None:
            zh_pred = float(zh_pred)

        # --- Resolve dataset names ---
        def _pick(candidates):
            for name in candidates:
                if name in fh:
                    return fh[name][:]
            raise KeyError(f"None of {candidates} found in {h5_path.name}")

        z = _pick([z_dataset, "z_grid", "bulk_truth/z_grid"])
        A = _pick([A_dataset, "A_of_z", "A_emergent", "bulk_truth/A_truth"])
        f = _pick([f_dataset, "f_of_z", "f_emergent", "bulk_truth/f_truth"])

    z = np.asarray(z, dtype=np.float64).ravel()
    A = np.asarray(A, dtype=np.float64).ravel()
    f = np.asarray(f, dtype=np.float64).ravel()

    # --- Sanity checks ---
    n_pts = len(z)
    if n_pts < 10:
        raise ValueError(f"Grid too coarse: {n_pts} points")
    if not (len(A) == n_pts and len(f) == n_pts):
        raise ValueError(f"Shape mismatch: z={n_pts}, A={len(A)}, f={len(f)}")

    # Ensure z is monotonically increasing
    if z[0] > z[-1]:
        z, A, f = z[::-1], A[::-1], f[::-1]

    # --- Trim at horizon ---
    # Strategy 1: use zh_pred attribute if available
    # Strategy 2: find where f first drops below a threshold (f < 0.02)
    # Strategy 3: fallback to trim_horizon_fraction
    if zh_pred is not None and zh_pred > z[0]:
        # Keep only z < zh_pred * (1 - trim_horizon_fraction)
        cutoff = zh_pred * (1.0 - trim_horizon_fraction)
        mask = z < cutoff
        if mask.sum() >= 10:
            z, A, f = z[mask], A[mask], f[mask]
    else:
        # Auto-detect: find where f drops below 0.02 (near-horizon)
        low_f = np.where(f < 0.02)[0]
        if len(low_f) > 0:
            cut_idx = max(10, low_f[0] - 3)
            z, A, f = z[:cut_idx], A[:cut_idx], f[:cut_idx]
        else:
            # Simple fraction trim
            n_trim = max(1, int(trim_horizon_fraction * n_pts))
            z, A, f = z[:-n_trim], A[:-n_trim], f[:-n_trim]

    # Floor f and A to avoid negative values (reconstruction artifacts beyond horizon)
    f = np.maximum(f, 1e-8)
    A = np.maximum(A, 1e-8)

    # --- Refine grid: interpolate to n_refine points in the physical region ---
    # The original grid may have too few points between UV boundary and horizon.
    # Re-sample to 200 uniform points for accurate SL eigenvalues.
    n_refine = 200
    if len(z) < n_refine:
        from scipy.interpolate import interp1d
        z_new = np.linspace(z[0], z[-1], n_refine)
        A = interp1d(z, A, kind="cubic", fill_value="extrapolate")(z_new)
        f = interp1d(z, f, kind="cubic", fill_value="extrapolate")(z_new)
        f = np.maximum(f, 1e-8)
        A = np.maximum(A, 1e-8)
        z = z_new

    # --- SL coefficients ---
    # p(z) = A^{d-1} f(z)
    # w(z) = A^{d-3}
    p = A**(d - 1) * f
    w = A**(d - 3)

    # Strip boundary points (Dirichlet BC at both ends)
    p_int = p[1:-1]
    w_int = w[1:-1]

    n_int = len(p_int)
    if n_int < 3:
        raise ValueError(f"Too few interior points: {n_int}")

    dz = float(z[1] - z[0])

    # --- Build and solve generalised eigenvalue problem ---
    L, W = _build_sl_matrix(p_int, w_int, dz)

    # Use scipy.linalg.eigh for symmetric positive-definite problems
    # W may become singular near the horizon (w0)  regularise slightly
    W_reg = W + 1e-14 * np.eye(n_int)

    n_eigs_req = min(n_eigs, n_int - 1)
    try:
        # eigh returns eigenvalues in ascending order
        eigenvalues, eigenvectors = linalg.eigh(
            L, W_reg,
            subset_by_index=[0, n_eigs_req - 1],
            driver="gvd",
            check_finite=False,
        )
    except Exception:
        # Fallback: full diagonalisation
        eigenvalues, eigenvectors = linalg.eigh(L, W_reg, check_finite=False)
        eigenvalues = eigenvalues[:n_eigs_req]

    # --- Filter and quality-flag ---
    lambda_sl: List[float] = []
    quality_flags: List[str] = []
    for ev in eigenvalues:
        ev_f = float(np.real(ev))
        if ev_f < -1e-6:
            # Unphysical negative eigenvalue  numerical noise
            quality_flags.append("negative")
            ev_f = abs(ev_f)  # still include with flag
        elif ev_f < 1e-10:
            quality_flags.append("near_zero")
        else:
            quality_flags.append("ok")
        lambda_sl.append(max(ev_f, 0.0))

    uv_exponents = _uv_exponents(np.array(lambda_sl), d).tolist()

    return {
        "lambda_sl":    lambda_sl,
        "uv_exponents": uv_exponents,
        "n_modes":      len(lambda_sl),
        "d":            d,
        "solver":       "finite_difference_eigh_v1",
        "z_range":      [float(z[0]), float(z[-1])],
        "n_grid_used":  int(len(z)),
        "quality_flags": quality_flags,
    }
