#!/usr/bin/env python3
"""
01b_generate_kerr_sandbox.py    CUERDAS-MALDACENA  (Stage 01b, v1.0)

Purpose
-------
Generate a synthetic Kerr ringdown boundary dataset for training the
geometry classifier (02_emergent_geometry_engine.py) in the Kerr family.

Each synthetic geometry corresponds to a binary black-hole merger with
parameters (M_final [Msun], a/M [dimensionless spin]) drawn from a grid
or random sample.  Theoretical Kerr QNMs (l=2, m=2, n=0 and n=1) are
computed with the `qnm` Python package and converted into surrogate
boundary embeddings using the same functions as realdata_ringdown_to_stage02_boundary_dataset.py.

Output HDF5 structure
---------------------
Each file mirrors the sandbox structure expected by the geometry engine:

  <name>.h5
   attrs: category="known", family="kerr", d=4, name, system_name, operators, M_msun, a_over_M
   boundary/
       attrs: family="kerr", d=4, qnm_Q0, qnm_f1f0, qnm_g1g0, qnm_n_modes, Delta_mass_dict
       G2_O1     (n_x,)
       G_R_real  (n_k, n_omega)
       G_R_imag  (n_k, n_omega)
       omega_grid (n_omega,)
       k_grid    (n_k,)
       x_grid    (n_x,)
       temperature (1,)
       central_charge_eff (1,)
       d         (1,)

There is NO bulk_truth group  Kerr has no holographic AdS dual.
The geometry engine masks reconstruction losses for has_bulk_truth=False.

Usage
-----
  python3 malda/01b_generate_kerr_sandbox.py \\
      --out-dir runs/kerr_sandbox_v1/01b_generate_kerr_sandbox \\
      --n-mass 8 --n-spin 10 \\
      --M-min 25 --M-max 150 \\
      --a-min 0.1 --a-max 0.9

Dependencies
------------
  pip install qnm h5py numpy
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np

try:
    import h5py
except ImportError:
    sys.exit("[ERROR] h5py not installed.  pip install h5py")

try:
    import qnm
except ImportError:
    sys.exit("[ERROR] qnm not installed.  pip install qnm")

SCRIPT_VERSION = "01b_generate_kerr_sandbox.py v1.0 (2026-04-08)"

# Physical constants
MSUN_S = 4.925491e-6   # Msun in seconds (G*Msun/c^3)
HZ_PER_MSUN_INV = 1.0 / MSUN_S   # Hz per (1/Msun)


# -------------------------------------------------------------------
# Path helpers
# -------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def resolve_path(p_str: str) -> Path:
    p = Path(p_str).expanduser()
    if p.is_absolute():
        return p.resolve()
    return (PROJECT_ROOT / p).resolve()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# -------------------------------------------------------------------
# Kerr QNM via `qnm` package
# -------------------------------------------------------------------

class KerrQNMCache:
    """Thin wrapper around qnm.modes_cache for (s=-2, l=2, m=2) spin-2 modes."""

    def __init__(self) -> None:
        # Pre-fetch mode sequences for n=0 and n=1
        self._seq0 = qnm.modes_cache(s=-2, l=2, m=2, n=0)
        self._seq1 = qnm.modes_cache(s=-2, l=2, m=2, n=1)

    def get_qnm(self, a_over_M: float, M_msun: float) -> Tuple[
        float, float, float, float, bool
    ]:
        """
        Return (f0_hz, tau0_s, f1_hz, tau1_s, has_overtone).

        qnm convention:  = _R + i _I with _I > 0 and  in units of 1/(M*G/c^3).
        Physical frequency: f = _R / (2 * M * G/c^3) = _R / (2 * M_msun * MSUN_S)
        Physical damping:    = _I / (M * G/c^3)     = 1/

        NOTE: qnm returns dimensionless ; sign convention varies by version.
        We take abs(_R) and abs(_I) to be robust.
        """
        a_dim = float(np.clip(a_over_M, 1e-4, 0.9999))
        M_s   = float(M_msun) * MSUN_S   # M in seconds

        # n=0 (fundamental)
        omega0, _, _ = self._seq0(a=a_dim, interp_only=True)
        omega0_R = abs(float(np.real(omega0)))
        omega0_I = abs(float(np.imag(omega0)))
        f0_hz  = omega0_R / (2.0 * math.pi * M_s)
        tau0_s = M_s / omega0_I if omega0_I > 0 else np.inf

        # n=1 (first overtone)
        has_overtone = False
        f1_hz  = f0_hz
        tau1_s = tau0_s
        try:
            omega1, _, _ = self._seq1(a=a_dim, interp_only=True)
            omega1_R = abs(float(np.real(omega1)))
            omega1_I = abs(float(np.imag(omega1)))
            if omega1_R > 0 and omega1_I > 0 and np.isfinite(omega1_R) and np.isfinite(omega1_I):
                f1_hz  = omega1_R / (2.0 * math.pi * M_s)
                tau1_s = M_s / omega1_I
                has_overtone = True
        except Exception:
            pass

        return f0_hz, tau0_s, f1_hz, tau1_s, has_overtone


# -------------------------------------------------------------------
# Boundary embedding helpers (mirrors real-data bridge)
# -------------------------------------------------------------------

class _Pole:
    __slots__ = ("freq_hz", "damping_1_over_s", "amp_abs")

    def __init__(self, freq_hz: float, damping_1_over_s: float, amp_abs: float = 1.0):
        self.freq_hz = float(freq_hz)
        self.damping_1_over_s = float(damping_1_over_s)
        self.amp_abs = float(amp_abs)


def _get_normalization_scales(poles: List[_Pole]) -> Tuple[float, float]:
    dom = max(poles, key=lambda p: p.amp_abs)
    omega_dom = 2.0 * math.pi * dom.freq_hz
    gamma_dom = max(dom.damping_1_over_s, 1e-6)
    return omega_dom, gamma_dom


def _poles_to_gr(
    omega_grid_dimless: np.ndarray,
    poles: List[_Pole],
    omega_dom_rads: float,
) -> Tuple[np.ndarray, np.ndarray]:
    """GR() =  an / ( - wn), normalised to unit peak |GR|."""
    Nw = int(omega_grid_dimless.size)
    if not poles or Nw <= 0:
        return np.zeros((Nw, 1)), np.zeros((Nw, 1))

    amps = np.array([p.amp_abs for p in poles], dtype=np.float64)
    amps /= (float(np.max(amps)) + 1e-12)

    omega = omega_grid_dimless.astype(np.float64)
    GR = np.zeros(Nw, dtype=np.complex128)
    for p, a in zip(poles, amps):
        w_real = (2.0 * math.pi * p.freq_hz) / omega_dom_rads
        w_imag = p.damping_1_over_s / omega_dom_rads
        GR += a / (omega - (w_real - 1j * w_imag))

    mag = np.abs(GR)
    mmax = float(np.max(mag))
    if mmax > 0:
        GR /= mmax

    return np.real(GR).reshape(-1, 1), np.imag(GR).reshape(-1, 1)


def _poles_to_g2(
    x_grid_dimless: np.ndarray,
    poles: List[_Pole],
    omega_dom_rads: float,
) -> np.ndarray:
    """G2(x) = | an exp((-n + in) x)|2,  x = t * omega_dom."""
    Nx = int(x_grid_dimless.size)
    if not poles or Nx <= 0:
        return np.zeros(Nx, dtype=np.float64)

    amps = np.array([p.amp_abs for p in poles], dtype=np.float64)
    amps /= (float(np.max(amps)) + 1e-12)

    x = x_grid_dimless.astype(np.float64)
    s = np.zeros(Nx, dtype=np.complex128)
    for p, a in zip(poles, amps):
        g_d = p.damping_1_over_s / omega_dom_rads
        w_d = (2.0 * math.pi * p.freq_hz) / omega_dom_rads
        s += float(a) * np.exp((-g_d + 1j * w_d) * x)

    G2 = np.abs(s) ** 2
    mmax = float(np.max(G2))
    if mmax > 0:
        G2 /= mmax
    return G2.astype(np.float64)


# -------------------------------------------------------------------
# QNM feature ratios
# -------------------------------------------------------------------

def _compute_qnm_features(
    poles: List[_Pole],
) -> Tuple[float, float, float]:
    """Return (Q0, f1/f0, 1/0) from pole list sorted by amplitude."""
    if not poles:
        return 0.0, 0.0, 0.0

    by_amp = sorted(poles, key=lambda p: p.amp_abs, reverse=True)
    dom = by_amp[0]
    f_dom  = dom.freq_hz
    g_dom  = dom.damping_1_over_s

    Q0 = math.pi * f_dom / g_dom if g_dom > 0 else 0.0

    if len(by_amp) >= 2:
        sub = by_amp[1]
        f1f0 = sub.freq_hz / f_dom if f_dom > 0 else 0.0
        g1g0 = sub.damping_1_over_s / g_dom if g_dom > 0 else 0.0
    else:
        f1f0 = 0.0
        g1g0 = 0.0

    return Q0, f1f0, g1g0


# -------------------------------------------------------------------
# HDF5 writer
# -------------------------------------------------------------------

def write_kerr_h5(
    out_path: Path,
    name: str,
    M_msun: float,
    a_over_M: float,
    poles: List[_Pole],
    has_overtone: bool,
    n_omega: int = 256,
    n_k: int = 30,
    n_x: int = 100,
    d: int = 4,
) -> None:
    """Write a single Kerr boundary HDF5 that matches the sandbox format."""
    omega_dom, gamma_dom = _get_normalization_scales(poles)

    # Dimensionless grids  match sandbox defaults so normalizer sees same range
    lo_omega = 0.1
    hi_omega = 3.0   # dominant pole sits at ~1; overtone at ~0.93-0.99
    omega_grid = np.linspace(lo_omega, hi_omega, n_omega)

    # Multi-k: k=0 to ~5 (dimensionless), like sandbox
    k_grid = np.linspace(0.0, 5.0, n_k)

    x_grid = np.linspace(1e-3, 10.0, n_x)

    # Surrogate G2 (k=0  spatial G2 at coincident points)
    G2 = _poles_to_g2(x_grid, poles, omega_dom)

    # Surrogate G_R: evaluated at each k (same poles, shifted by k^2 dispersion toy)
    GR_real_all = np.zeros((n_k, n_omega), dtype=np.float64)
    GR_imag_all = np.zeros((n_k, n_omega), dtype=np.float64)
    for ik, kval in enumerate(k_grid):
        # Toy dispersion: shift each pole frequency by sqrt(k^2) / omega_dom
        shifted_poles = [
            _Pole(
                freq_hz=p.freq_hz + kval * omega_dom / (2.0 * math.pi) * 0.1,
                damping_1_over_s=p.damping_1_over_s,
                amp_abs=p.amp_abs,
            )
            for p in poles
        ]
        gr_r, gr_i = _poles_to_gr(omega_grid, shifted_poles, omega_dom)
        GR_real_all[ik, :] = gr_r[:, 0]
        GR_imag_all[ik, :] = gr_i[:, 0]

    Q0, f1f0, g1g0 = _compute_qnm_features(poles)

    # Dummy operators (no CFT operator spectrum for Kerr)
    operators = json.dumps([{"name": "O1", "Delta": 0.0, "m2L2": 0.0, "spin": 2}])

    with h5py.File(out_path, "w") as hf:
        # Top-level attrs
        hf.attrs["category"]    = "known"
        hf.attrs["family"]      = "kerr"
        hf.attrs["d"]           = d
        hf.attrs["name"]        = name
        hf.attrs["system_name"] = name
        hf.attrs["operators"]   = operators
        hf.attrs["M_msun"]      = float(M_msun)
        hf.attrs["a_over_M"]    = float(a_over_M)
        hf.attrs["has_bulk_truth"] = False

        # boundary/ group
        bg = hf.create_group("boundary")
        bg.attrs["family"]          = "kerr"
        bg.attrs["d"]               = d
        bg.attrs["qnm_Q0"]          = float(Q0)
        bg.attrs["qnm_f1f0"]        = float(f1f0)
        bg.attrs["qnm_g1g0"]        = float(g1g0)
        bg.attrs["qnm_n_modes"]     = int(len(poles))
        bg.attrs["Delta_mass_dict"] = "{}"   # no CFT operators
        bg.attrs["M_msun"]          = float(M_msun)
        bg.attrs["a_over_M"]        = float(a_over_M)
        bg.attrs["has_overtone"]    = has_overtone

        bg.create_dataset("G2_O1",           data=G2)
        bg.create_dataset("G_R_real",        data=GR_real_all)
        bg.create_dataset("G_R_imag",        data=GR_imag_all)
        bg.create_dataset("omega_grid",      data=omega_grid)
        bg.create_dataset("k_grid",          data=k_grid)
        bg.create_dataset("x_grid",          data=x_grid)
        bg.create_dataset("temperature",     data=np.array([0.0]))
        bg.create_dataset("central_charge_eff", data=np.array([0.0]))
        bg.create_dataset("d",               data=np.array([float(d)]))

        # No bulk_truth group  masked out in train_one_epoch via has_bulk_mask


# -------------------------------------------------------------------
# Manifest
# -------------------------------------------------------------------

def write_manifest(out_dir: Path, entries: List[dict]) -> Path:
    manifest = {
        "created_at": utc_now_iso(),
        "script":     SCRIPT_VERSION,
        "version":    "01b-v1",
        "family":     "kerr",
        "geometries": entries,
    }
    p = out_dir / "geometries_manifest.json"
    p.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return p


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Generate synthetic Kerr ringdown boundary dataset for training."
    )
    ap.add_argument("--out-dir",  required=True, type=str)
    ap.add_argument("--n-mass",   type=int,   default=8,    help="Grid points in M (default 8)")
    ap.add_argument("--n-spin",   type=int,   default=10,   help="Grid points in a/M (default 10)")
    ap.add_argument("--M-min",    type=float, default=25.0, help="Min final mass [Msun]")
    ap.add_argument("--M-max",    type=float, default=150.0,help="Max final mass [Msun]")
    ap.add_argument("--a-min",    type=float, default=0.1,  help="Min dimensionless spin")
    ap.add_argument("--a-max",    type=float, default=0.9,  help="Max dimensionless spin")
    ap.add_argument("--n-omega",  type=int,   default=256,  help="Omega grid size")
    ap.add_argument("--n-k",      type=int,   default=30,   help="k grid size")
    ap.add_argument("--n-x",      type=int,   default=100,  help="x grid size")
    ap.add_argument("--d",        type=int,   default=4,    help="Boundary dimension")
    args = ap.parse_args()

    out_dir = resolve_path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    M_grid   = np.linspace(args.M_min, args.M_max, args.n_mass)
    a_grid   = np.linspace(args.a_min, args.a_max, args.n_spin)

    print("=" * 70)
    print("KERR SANDBOX GENERATOR (Stage 01b)")
    print(f"Script:  {SCRIPT_VERSION}")
    print(f"Out dir: {out_dir}")
    print(f"Grid:    {args.n_mass} masses  {args.n_spin} spins = {args.n_mass * args.n_spin} geometries")
    print(f"M:       [{args.M_min}, {args.M_max}] Msun")
    print(f"a/M:     [{args.a_min}, {args.a_max}]")
    print("=" * 70)

    cache = KerrQNMCache()

    entries = []
    idx = 0
    for M in M_grid:
        for a in a_grid:
            f0, tau0, f1, tau1, has_ot = cache.get_qnm(a, M)

            if not (np.isfinite(f0) and np.isfinite(tau0) and f0 > 0 and tau0 > 0):
                print(f"  [WARN] M={M:.1f} a={a:.3f}: invalid QNM ({f0:.1f} Hz, {tau0*1e3:.2f} ms)  skipping")
                continue

            gamma0 = 1.0 / tau0

            poles: List[_Pole] = [_Pole(freq_hz=f0, damping_1_over_s=gamma0, amp_abs=1.0)]
            if has_ot and np.isfinite(f1) and np.isfinite(tau1) and tau1 > 0:
                gamma1 = 1.0 / tau1
                # Overtone amplitude ratio ~0.3 (typical for non-extremal Kerr)
                poles.append(_Pole(freq_hz=f1, damping_1_over_s=gamma1, amp_abs=0.3))

            name = f"kerr_M{M:.0f}_a{a:.3f}_known_{idx:03d}"

            Q0, f1f0, g1g0 = _compute_qnm_features(poles)
            print(
                f"  [{idx:03d}] M={M:6.1f} Msun  a/M={a:.3f}  "
                f"f0={f0:.1f} Hz  0={tau0*1e3:.2f} ms  "
                f"Q0={Q0:.2f}  f1/f0={f1f0:.3f}  1/0={g1g0:.3f}  "
                f"ot={has_ot}"
            )

            h5_path = out_dir / f"{name}.h5"
            write_kerr_h5(
                out_path=h5_path,
                name=name,
                M_msun=M,
                a_over_M=a,
                poles=poles,
                has_overtone=has_ot,
                n_omega=args.n_omega,
                n_k=args.n_k,
                n_x=args.n_x,
                d=args.d,
            )

            entries.append({
                "name":      name,
                "category":  "known",
                "family":    "kerr",
                "M_msun":    float(M),
                "a_over_M":  float(a),
                "f0_hz":     float(f0),
                "tau0_ms":   float(tau0 * 1e3),
                "has_overtone": bool(has_ot),
                "qnm_Q0":    float(Q0),
                "qnm_f1f0":  float(f1f0),
                "qnm_g1g0":  float(g1g0),
            })
            idx += 1

    manifest_path = write_manifest(out_dir, entries)

    print("\n" + "=" * 70)
    print(f"[OK] Generated {len(entries)} Kerr geometries")
    print(f"  Manifest: {manifest_path}")
    print("=" * 70)
    print("Next: merge with sandbox_v1 manifest and retrain 02_emergent_geometry_engine.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
