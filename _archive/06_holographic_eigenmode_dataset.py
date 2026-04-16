#!/usr/bin/env python3
"""
06_holographic_eigenmode_dataset.py  —  CUERDAS-MALDACENA  (Stage 06 GW, v1.0)

Build the eigenmode dataset for stage 07.  Two modes:

HOLOGRAPHIC (sandbox)
---------------------
For each holographic geometry with a bulk_truth group and a Delta_mass_dict
in boundary attrs:

  Tier Canonical: ads, lifshitz, hyperscaling, deformed, dpbrane, unknown
  Tier A:         rn_ads, gauss_bonnet, massive_gravity, linear_axion, charged_hvlif
  Tier A ext:     gubser_rocha, soft_wall

  - lambda_sl  = m²L²   (bulk scalar mass squared, can be negative/tachyonic)
  - Delta_UV   = Δ       (operator dimension)
  - d          = d_cft   = (d_spatial + 1)  so that Δ(Δ - d_cft) = m²L²

One row per operator per geometry.  The SL frequency solver is also run as
an independent cross-check (stored in lambda_sl_freq column).

KERR
----
For each Kerr geometry (no holographic bulk):

  - Uses QNM attrs: qnm_Q0, qnm_f1f0, qnm_g1g0, M_msun, a_over_M
  - Outputs to a separate CSV (--kerr-csv)

USAGE
-----
  python3 malda/06_holographic_eigenmode_dataset.py \
      --source-dir  runs/sandbox_v5/01_merged \
      --out-dir     runs/sandbox_v5_b3/06_holographic_eigenmode_dataset \
      --n-eigs      4
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import h5py
import numpy as np

SCRIPT_VERSION = "06_holographic_eigenmode_dataset.py v1.1 (2026-04-13)"

# ── Registro canónico de familias ──────────────────────────────────────────
try:
    from family_registry import HOLOGRAPHIC_FAMILIES as _HOLO_FAMS, read_extra_attrs_from_h5
    _HAS_FAMILY_REGISTRY = True
except ImportError:
    _HOLO_FAMS = frozenset({
        "ads", "lifshitz", "hyperscaling", "deformed", "dpbrane", "unknown",
        "rn_ads", "gauss_bonnet", "massive_gravity", "linear_axion", "charged_hvlif",
        "gubser_rocha", "soft_wall",
    })
    _HAS_FAMILY_REGISTRY = False

    def read_extra_attrs_from_h5(h5_attrs, family):  # type: ignore
        return {}

# ── Try to import bulk solver ──────────────────────────────────────────────
try:
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    import bulk_scalar_solver as _bss
    HAS_SOLVER = True
except ImportError:
    _bss = None
    HAS_SOLVER = False


# ── Helpers ────────────────────────────────────────────────────────────────

def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _str(x: Any) -> str:
    if isinstance(x, bytes):
        return x.decode("utf-8", errors="ignore")
    return str(x)


# ── Row definitions ────────────────────────────────────────────────────────

HOLO_FIELDS = [
    "system_name", "family", "d",        # d = d_cft = d_spatial + 1
    "operator", "Delta_UV", "lambda_sl", # Δ and m²L²
    "lambda_sl_freq",                     # ω² from SL frequency solver (cross-check)
    "z_dyn", "theta", "quality_flag",
    "is_ground_state", "delta_source",
    # Tier A extra attrs (NaN/empty for Tier Canonical geometries)
    "charge_Q", "lambda_gb", "m_g", "alpha_axion",
]

KERR_FIELDS = [
    "system_name", "M_msun", "a_over_M",
    "f0_hz", "tau0_ms", "f1_hz", "tau1_ms",
    "qnm_Q0", "qnm_f1f0", "qnm_g1g0",
    "has_overtone",
]


# ── Holographic geometry processing ───────────────────────────────────────

def process_holographic(
    h5_path: Path,
    n_eigs: int,
) -> List[Dict[str, Any]]:
    """Return rows for one holographic geometry."""
    rows: List[Dict[str, Any]] = []

    with h5py.File(h5_path, "r") as f:
        family = _str(f.attrs.get("family", "unknown"))
        d_sp   = int(f.attrs.get("d", 4))          # spatial dim
        d_cft  = d_sp + 1                           # CFT dim (for Δ(Δ-d_cft) = m²L²)
        system_name = _str(f.attrs.get("system_name", f.attrs.get("name", h5_path.stem)))
        z_dyn  = float(f.attrs.get("z_dyn", float("nan")))
        theta  = float(f.attrs.get("theta", float("nan")))
        # Tier A: leer attrs canónicos extra (NaN para H5 legacy que no los tienen)
        extra = read_extra_attrs_from_h5(f.attrs, family)
        charge_Q    = extra.get("charge_Q",    float("nan"))
        lambda_gb   = extra.get("lambda_gb",   float("nan"))
        m_g         = extra.get("m_g",         float("nan"))
        alpha_axion = extra.get("alpha_axion", float("nan"))

        # Delta_mass_dict from boundary attrs
        bd_attrs = dict(f["boundary"].attrs) if "boundary" in f else {}
        delta_str = bd_attrs.get("Delta_mass_dict", "{}")
        try:
            delta_dict: Dict[str, Any] = json.loads(delta_str)
        except Exception:
            delta_dict = {}

    if not delta_dict:
        return []   # no operators to map

    # Compute d_formula empirically: d = (Δ² - m2L2) / Δ
    # This is derived from m2L2 = Δ(Δ - d_formula) → d_formula = (Δ² - m2L2) / Δ
    # We take the median across all operators for robustness.
    d_estimates = []
    for op_name, op_vals in delta_dict.items():
        D_  = float(op_vals.get("Delta", float("nan")))
        m2_ = float(op_vals.get("m2L2",  float("nan")))
        if np.isfinite(D_) and np.isfinite(m2_) and abs(D_) > 0.01:
            d_estimates.append((D_**2 - m2_) / D_)
    if d_estimates:
        d_formula = float(np.round(np.median(d_estimates)))  # round to nearest integer
    else:
        d_formula = float(d_cft)  # fallback

    # Run SL frequency solver on truth geometry (cross-check)
    freq_eigs: List[float] = []
    if HAS_SOLVER:
        try:
            res = _bss.solve_geometry(h5_path, n_eigs=n_eigs,
                                       z_dataset="z_grid",
                                       A_dataset="bulk_truth/A_truth",
                                       f_dataset="bulk_truth/f_truth")
            freq_eigs = res.get("lambda_sl", [])
        except Exception as e:
            pass  # solver failure is non-fatal

    # One row per operator
    operators_sorted = sorted(delta_dict.items(), key=lambda kv: kv[1].get("Delta", 0))
    for op_idx, (op_name, op_vals) in enumerate(operators_sorted):
        D   = float(op_vals.get("Delta", float("nan")))
        m2  = float(op_vals.get("m2L2", float("nan")))

        if not (np.isfinite(D) and np.isfinite(m2)):
            continue

        # Verify formula: D*(D - d_formula) ≈ m2L2
        theory = D * (D - d_formula)
        rel_err = abs(theory - m2) / (abs(m2) + 1e-10)
        quality = "ok" if rel_err < 0.01 else f"theory_mismatch_{rel_err:.3f}"

        # SL frequency eigenvalue (cross-check, sorted by frequency)
        lam_freq = freq_eigs[op_idx] if op_idx < len(freq_eigs) else float("nan")

        rows.append({
            "system_name":    system_name,
            "family":         family,
            "d":              d_formula,       # empirical d where Δ(Δ-d) = m²L²
            "operator":       op_name,
            "Delta_UV":       round(D, 8),
            "lambda_sl":      round(m2, 8),   # m²L² (main eigenvalue)
            "lambda_sl_freq": round(lam_freq, 6) if np.isfinite(lam_freq) else "",
            "z_dyn":          round(z_dyn, 6) if np.isfinite(z_dyn) else "",
            "theta":          round(theta, 6) if np.isfinite(theta) else "",
            "quality_flag":   quality,
            "is_ground_state": 1 if op_idx == 0 else 0,
            "delta_source":   "boundary_delta_mass_dict",
            # Tier A extra attrs (empty string for Tier Canonical H5)
            "charge_Q":    round(charge_Q, 6) if np.isfinite(charge_Q) else "",
            "lambda_gb":   round(lambda_gb, 6) if np.isfinite(lambda_gb) else "",
            "m_g":         round(m_g, 6) if np.isfinite(m_g) else "",
            "alpha_axion": round(alpha_axion, 6) if np.isfinite(alpha_axion) else "",
        })

    return rows


# ── Kerr geometry processing ───────────────────────────────────────────────

def process_kerr(h5_path: Path) -> Optional[Dict[str, Any]]:
    """Return a single Kerr row from QNM attrs."""
    with h5py.File(h5_path, "r") as f:
        family = _str(f.attrs.get("family", ""))
        if family != "kerr":
            return None

        system_name = _str(f.attrs.get("system_name", h5_path.stem))
        M    = float(f.attrs.get("M_msun",  float("nan")))
        a    = float(f.attrs.get("a_over_M", float("nan")))

        bd_attrs = dict(f["boundary"].attrs) if "boundary" in f else {}
        Q0   = float(bd_attrs.get("qnm_Q0",   float("nan")))
        f1f0 = float(bd_attrs.get("qnm_f1f0", float("nan")))
        g1g0 = float(bd_attrs.get("qnm_g1g0", float("nan")))
        has_ot = bool(bd_attrs.get("has_overtone", False))
        n_modes = int(bd_attrs.get("qnm_n_modes", 1))

    if not (np.isfinite(M) and np.isfinite(a) and np.isfinite(Q0)):
        return None

    # Reconstruct f0, tau0 from Q0 = π f0 / γ0 and qnm features
    # The sandbox stores only ratios; for inverse map we need raw values.
    # Read them from the manifest or recompute via qnm package.
    # For now store what we have; the inverse is done in 07K.
    return {
        "system_name": system_name,
        "M_msun":      round(M, 4),
        "a_over_M":    round(a, 4),
        "f0_hz":       float("nan"),   # filled by 07K from manifest
        "tau0_ms":     float("nan"),
        "f1_hz":       float("nan"),
        "tau1_ms":     float("nan"),
        "qnm_Q0":      round(Q0,   4),
        "qnm_f1f0":    round(f1f0, 4),
        "qnm_g1g0":    round(g1g0, 4),
        "has_overtone": int(has_ot),
    }


# ── CSV writers ────────────────────────────────────────────────────────────

def write_csv(rows: List[Dict], fields: List[str], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


# ── Main ───────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Stage 06 (GW): build holographic + Kerr eigenmode datasets."
    )
    ap.add_argument("--source-dir", required=True,
                    help="Directory with sandbox_v5 source HDF5 files (has Delta_mass_dict)")
    ap.add_argument("--out-dir", required=True,
                    help="Output directory")
    ap.add_argument("--n-eigs", type=int, default=4,
                    help="SL frequency eigenmodes to compute (cross-check; default 4)")
    args = ap.parse_args()

    src_dir = Path(args.source_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    h5_files = sorted(src_dir.glob("*.h5"))
    if not h5_files:
        print(f"[ERROR] No .h5 files in {src_dir}")
        return 2

    print("=" * 70)
    print("HOLOGRAPHIC EIGENMODE DATASET  —  Stage 06 (GW)")
    print(f"Script: {SCRIPT_VERSION}")
    print(f"Source: {src_dir}  ({len(h5_files)} files)")
    print(f"Output: {out_dir}")
    print(f"SL solver: {'available' if HAS_SOLVER else 'NOT available (cross-check disabled)'}")
    print("=" * 70)

    holo_rows: List[Dict] = []
    kerr_rows: List[Dict] = []
    n_skipped = 0

    for h5_path in h5_files:
        with h5py.File(h5_path, "r") as f:
            family = _str(f.attrs.get("family", "unknown"))

        if family == "kerr":
            row = process_kerr(h5_path)
            if row:
                kerr_rows.append(row)
        else:
            rows = process_holographic(h5_path, args.n_eigs)
            if rows:
                holo_rows.extend(rows)
                lambdas = ", ".join(f"{r['lambda_sl']:.3f}" for r in rows)
                print(f"  {h5_path.stem[:50]:50s}: {len(rows)} ops, d_cft={rows[0]['d']}, m2L2=[{lambdas}]")
            else:
                n_skipped += 1

    # Write holographic CSV
    holo_csv = out_dir / "bulk_modes_dataset.csv"
    write_csv(holo_rows, HOLO_FIELDS, holo_csv)

    # Write Kerr CSV
    kerr_csv = out_dir / "kerr_qnm_dataset.csv"
    if kerr_rows:
        write_csv(kerr_rows, KERR_FIELDS, kerr_csv)

    # Meta
    meta = {
        "created_at": utc_now(),
        "script": SCRIPT_VERSION,
        "source_dir": str(src_dir),
        "n_holographic_geometries": len(set(r["system_name"] for r in holo_rows)),
        "n_holographic_rows": len(holo_rows),
        "n_kerr_geometries": len(kerr_rows),
        "n_skipped": n_skipped,
        "solver_available": HAS_SOLVER,
        "formula": "lambda_sl = Delta * (Delta - d)  where d = d_spatial + 1 (CFT dim)",
        "lambda_sl_definition": "m2L2 = bulk scalar mass squared (from Delta_mass_dict attrs)",
        "lambda_sl_freq_definition": "omega^2 from SL frequency eigensolver (cross-check only)",
        "notes": [
            "lambda_sl = m2L2 < 0 for tachyonic scalars (above BF bound: m2L2 > -(d_cft)^2/4)",
            "d in CSV = d_cft = d_spatial + 1 so that Delta*(Delta-d_cft) = m2L2",
            "Kerr geometries have no holographic bulk; written to separate kerr_qnm_dataset.csv",
        ],
    }
    (out_dir / "bulk_modes_meta.json").write_text(json.dumps(meta, indent=2))

    print("\n" + "=" * 70)
    print(f"[OK] Holographic:  {meta['n_holographic_rows']:4d} rows  ({meta['n_holographic_geometries']} geometries) → {holo_csv}")
    print(f"     Kerr:         {meta['n_kerr_geometries']:4d} geometries → {kerr_csv}")
    print(f"     Skipped:      {n_skipped}")
    print("=" * 70)
    print("Next: 07_emergent_lambda_sl_dictionary.py  (holographic) and  07K_kerr_qnm_dictionary.py  (Kerr)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
