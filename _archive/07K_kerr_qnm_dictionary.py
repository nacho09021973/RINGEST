#!/usr/bin/env python3
"""
07K_kerr_qnm_dictionary.py  —  CUERDAS-MALDACENA  (Stage 07K, v1.0)

Learn the INVERSE QNM map for Kerr black holes:
    (f₀_Hz, τ₀_ms)  →  (M_Msun, a/M)

Physical basis
--------------
For a Kerr BH of mass M and spin a/M, the (ℓ=2,m=2,n=0) QNM frequency and
damping time scale as:

    f₀  ∝  1/M  × α(a/M)
    τ₀  ∝  M    × β(a/M)

where α, β are dimensionless functions of a/M known from the `qnm` package.

Given (f₀, τ₀) measured from a ringdown signal, invert:

    M  ≈  f(f₀, τ₀)
    a/M ≈  g(f₀, τ₀)

Using the sandbox data from `01b_generate_kerr_sandbox.py` as training set.

Input
-----
  - runs/kerr_sandbox_v1/01b_generate_kerr_sandbox/geometries_manifest.json
    (contains f0_hz, tau0_ms, M_msun, a_over_M for each geometry)

Output
------
  runs/sandbox_v5_b3/07K_kerr_qnm_dictionary/
    kerr_dictionary_report.json
    kerr_predictions.csv
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

SCRIPT_VERSION = "07K_kerr_qnm_dictionary.py v1.0 (2026-04-08)"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Load Kerr sandbox data ─────────────────────────────────────────────────

def load_kerr_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load the Kerr sandbox manifest and extract (f0, tau0, M, a/M)."""
    manifest = json.loads(manifest_path.read_text())
    entries = manifest["geometries"]

    data: Dict[str, list] = {
        "system_name": [], "M_msun": [], "a_over_M": [],
        "f0_hz": [], "tau0_ms": [], "f1_hz": [], "tau1_ms": [],
        "qnm_Q0": [], "qnm_f1f0": [], "qnm_g1g0": [],
    }
    for e in entries:
        data["system_name"].append(e["name"])
        data["M_msun"].append(float(e["M_msun"]))
        data["a_over_M"].append(float(e["a_over_M"]))
        data["f0_hz"].append(float(e.get("f0_hz", float("nan"))))
        # tau0_ms: stored in manifest as tau0_ms
        tau0 = float(e.get("tau0_ms", float("nan")))
        data["tau0_ms"].append(tau0)
        data["f1_hz"].append(float(e.get("f1_hz", data["f0_hz"][-1])))
        data["tau1_ms"].append(float(e.get("tau1_ms", tau0)))
        data["qnm_Q0"].append(float(e.get("qnm_Q0", float("nan"))))
        data["qnm_f1f0"].append(float(e.get("qnm_f1f0", float("nan"))))
        data["qnm_g1g0"].append(float(e.get("qnm_g1g0", float("nan"))))
    return data


# ── QNM feature engineering ────────────────────────────────────────────────

def build_features(data: Dict[str, list]) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Build feature matrix X and target arrays (M, a/M).

    Features:
      - f0_hz      (fundamental frequency)
      - tau0_ms    (damping time)
      - f0*tau0    (dimensionless product — mass-independent)
      - qnm_Q0     (= π f0 τ0 — quality factor)
      - qnm_f1f0   (overtone frequency ratio — spin indicator)
      - qnm_g1g0   (overtone damping ratio)

    Physical intuition:
      - f0 × tau0 = f0 × τ0 = Q0/π  → depends mainly on a/M
      - f0 × M = dimensionless freq  → depends only on a/M
      - τ0 / M = dimensionless τ     → depends only on a/M
      - So M is determined by f0 alone given a/M
    """
    f0  = np.array(data["f0_hz"],   dtype=float)
    t0  = np.array(data["tau0_ms"], dtype=float)
    Q0  = np.array(data["qnm_Q0"],  dtype=float)
    r10 = np.array(data["qnm_f1f0"],dtype=float)
    g10 = np.array(data["qnm_g1g0"],dtype=float)

    # Derived features
    f0t0    = f0 * t0           # ∝ Q0/π (spin proxy)
    inv_f0  = 1.0 / (f0 + 1e-9)  # ∝ M (mass proxy)

    X = np.column_stack([
        f0,       # Hz — contains M information
        t0,       # ms — contains M information
        f0t0,     # dimensionless — spin proxy
        Q0,       # quality factor
        r10,      # f1/f0 — strong spin indicator (Kerr: <1)
        g10,      # γ1/γ0 — ~3 for all Kerr
        inv_f0,   # 1/f0 ∝ M
    ])

    M_arr = np.array(data["M_msun"],  dtype=float)
    a_arr = np.array(data["a_over_M"],dtype=float)

    # Filter invalid rows
    valid = (
        np.isfinite(X).all(axis=1) &
        np.isfinite(M_arr) &
        np.isfinite(a_arr)
    )
    return X[valid], M_arr[valid], a_arr[valid]


# ── Model training ─────────────────────────────────────────────────────────

def train_model(X: np.ndarray, y: np.ndarray, target_name: str) -> Tuple[Any, Dict]:
    """Train a gradient boosting model to predict target from features."""
    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("gbr",    GradientBoostingRegressor(
            n_estimators=300,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42,
        )),
    ])

    # Cross-validation R² (leave-one-out at this sample size ~80)
    cv_r2 = cross_val_score(pipe, X, y, cv=5, scoring="r2")

    pipe.fit(X, y)
    y_pred = pipe.predict(X)

    metrics = {
        "r2_train":    float(r2_score(y, y_pred)),
        "mae_train":   float(mean_absolute_error(y, y_pred)),
        "r2_cv_mean":  float(cv_r2.mean()),
        "r2_cv_std":   float(cv_r2.std()),
        "n_samples":   int(len(y)),
    }
    print(f"  {target_name:12s}: R²_train={metrics['r2_train']:.4f}  "
          f"R²_cv={metrics['r2_cv_mean']:.4f}±{metrics['r2_cv_std']:.4f}  "
          f"MAE={metrics['mae_train']:.4f}")
    return pipe, metrics


# ── Physical invariance checks ─────────────────────────────────────────────

def check_physical_invariants(
    data: Dict[str, list],
    pipe_M: Any,
    pipe_a: Any,
    X: np.ndarray,
    M_true: np.ndarray,
    a_true: np.ndarray,
) -> Dict[str, Any]:
    """
    Verify physical scaling laws:
      - f0 × M = α(a/M)  (should be pure function of spin)
      - τ0 / M = β(a/M)  (should be pure function of spin)
    """
    f0 = X[:, 0]
    t0 = X[:, 1]
    a  = a_true

    # Physical constants
    MSUN_S = 4.925491e-6  # seconds per solar mass

    # Dimensionless QNM products (should be function of a/M only)
    alpha = f0 * M_true * MSUN_S * 2 * np.pi  # ωR × M (dim'less)
    beta  = t0 * 1e-3 / (M_true * MSUN_S)     # τ0 / M (dim'less, τ0 in s)

    # Correlation of (alpha, beta) with a/M — should be very high
    corr_alpha = float(np.corrcoef(alpha, a)[0, 1])
    corr_beta  = float(np.corrcoef(beta,  a)[0, 1])

    return {
        "alpha_corr_with_spin": corr_alpha,
        "beta_corr_with_spin":  corr_beta,
        "alpha_range": [float(alpha.min()), float(alpha.max())],
        "beta_range":  [float(beta.min()),  float(beta.max())],
        "note": "alpha = ω_R M (dim'less freq), beta = τ0 / M (dim'less time). Both should be functions of a/M only.",
    }


# ── Main ───────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Stage 07K: learn Kerr inverse QNM map (f0,τ0) → (M, a/M)."
    )
    ap.add_argument("--manifest",  required=True,
                    help="Path to Kerr sandbox geometries_manifest.json")
    ap.add_argument("--out-dir",   required=True,
                    help="Output directory")
    ap.add_argument("--ligo-f0-hz",  type=float, default=None,
                    help="(Optional) LIGO f0 [Hz] to predict M and a/M")
    ap.add_argument("--ligo-tau0-ms", type=float, default=None,
                    help="(Optional) LIGO τ0 [ms] to predict M and a/M")
    ap.add_argument("--ligo-Q0",   type=float, default=None,
                    help="(Optional) LIGO Q0 for prediction")
    ap.add_argument("--ligo-f1f0", type=float, default=None,
                    help="(Optional) LIGO f1/f0 for prediction")
    ap.add_argument("--ligo-g1g0", type=float, default=None,
                    help="(Optional) LIGO γ1/γ0 for prediction")
    args = ap.parse_args()

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("KERR QNM DICTIONARY  —  Stage 07K")
    print(f"Script: {SCRIPT_VERSION}")
    print(f"Output: {out_dir}")
    print("=" * 70)

    # Load data
    manifest_path = Path(args.manifest).resolve()
    data = load_kerr_manifest(manifest_path)
    X, M_true, a_true = build_features(data)

    print(f"\n  Loaded {len(M_true)} Kerr geometries")
    print(f"  M range:   [{M_true.min():.1f}, {M_true.max():.1f}] Msun")
    print(f"  a/M range: [{a_true.min():.3f}, {a_true.max():.3f}]")
    print(f"  Features:  {X.shape[1]} (f0, tau0, f0*tau0, Q0, f1/f0, g1/g0, 1/f0)")

    # Train models
    print("\n>> Training inverse QNM models...")
    pipe_M, metrics_M = train_model(X, M_true,  "M [Msun]")
    pipe_a, metrics_a = train_model(X, a_true,  "a/M")

    # ── Two-step analytical predictor ──────────────────────────────────────
    # Step 1: a/M from f1/f0, Q0 (via ML model — essentially exact)
    # Step 2: M from f0 given a/M using M = α(a/M) / (2π f0 MSUN_S)
    print("\n>> Two-step analytical predictor (physics-based)...")
    MSUN_S = 4.925491e-6  # seconds per solar mass
    try:
        import qnm
        seq0 = qnm.modes_cache(s=-2, l=2, m=2, n=0)

        def alpha_from_a(a_val: float) -> float:
            """Dimensionless frequency ω_R M = ω_R * (M*G/c³)"""
            a_clip = float(np.clip(a_val, 1e-4, 0.9999))
            omega, _, _ = seq0(a=a_clip, interp_only=True)
            return abs(float(np.real(omega)))  # ω_R in units of 1/M

        a_pred_ml = np.clip(pipe_a.predict(X), 0.01, 0.9999)
        M_pred_2step = np.array([
            alpha_from_a(a) / (2 * np.pi * f0 * MSUN_S)
            for a, f0 in zip(a_pred_ml, X[:, 0])
        ])

        r2_2step_M = float(r2_score(M_true, M_pred_2step))
        mae_2step_M = float(mean_absolute_error(M_true, M_pred_2step))
        print(f"  2-step M: R²={r2_2step_M:.4f}, MAE={mae_2step_M:.2f} Msun  "
              f"(vs ML-only R²={metrics_M['r2_cv_mean']:.4f})")
        metrics_M["r2_2step"] = r2_2step_M
        metrics_M["mae_2step"] = mae_2step_M
    except Exception as e:
        print(f"  [WARN] 2-step predictor failed: {e}")

    # Physical invariance check
    print("\n>> Physical invariance check...")
    inv_check = check_physical_invariants(data, pipe_M, pipe_a, X, M_true, a_true)
    print(f"  corr(ωM, a/M) = {inv_check['alpha_corr_with_spin']:.4f}  "
          f"(expected ≈ 1.0 — ωM is function of spin only)")
    print(f"  corr(τ/M, a/M) = {inv_check['beta_corr_with_spin']:.4f}  "
          f"(expected ≈ 1.0 — τ/M is function of spin only)")

    # LIGO prediction (if provided)
    ligo_pred: Optional[Dict] = None
    if args.ligo_f0_hz is not None and args.ligo_tau0_ms is not None:
        print("\n>> LIGO prediction...")
        f0  = args.ligo_f0_hz
        t0  = args.ligo_tau0_ms
        Q0  = args.ligo_Q0  if args.ligo_Q0  is not None else np.pi * f0 * t0 / 1000.0
        r10 = args.ligo_f1f0 if args.ligo_f1f0 is not None else 0.97  # typical Kerr
        g10 = args.ligo_g1g0 if args.ligo_g1g0 is not None else 3.0   # typical Kerr

        X_ligo = np.array([[f0, t0, f0*t0, Q0, r10, g10, 1.0/f0]])

        M_pred = float(pipe_M.predict(X_ligo)[0])
        a_pred = float(np.clip(pipe_a.predict(X_ligo)[0], 0.0, 0.9999))

        # Clamp to training range
        M_pred_clamped = float(np.clip(M_pred, M_true.min()*0.5, M_true.max()*1.5))

        print(f"  Input:  f0={f0:.1f} Hz, τ0={t0:.2f} ms, Q0={Q0:.2f}, f1/f0={r10:.3f}, γ1/γ0={g10:.3f}")
        print(f"  Output: M_pred={M_pred:.1f} Msun, a/M_pred={a_pred:.3f}")
        print(f"  Note: training range M=[{M_true.min():.0f},{M_true.max():.0f}] Msun, a/M=[{a_true.min():.2f},{a_true.max():.2f}]")
        if M_pred < M_true.min() * 0.5 or M_pred > M_true.max() * 2:
            print(f"  [WARN] M prediction {M_pred:.1f} outside training range — extrapolation")

        ligo_pred = {
            "f0_hz": f0, "tau0_ms": t0, "Q0": Q0,
            "f1f0": r10, "g1g0": g10,
            "M_pred_msun": M_pred,
            "a_over_M_pred": a_pred,
        }

    # Save results
    report = {
        "created_at":    utc_now(),
        "script":        SCRIPT_VERSION,
        "manifest":      str(manifest_path),
        "n_geometries":  int(len(M_true)),
        "feature_names": ["f0_hz","tau0_ms","f0*tau0","qnm_Q0","qnm_f1f0","qnm_g1g0","1/f0"],
        "model_M":       {"type": "GradientBoostingRegressor", **metrics_M},
        "model_a":       {"type": "GradientBoostingRegressor", **metrics_a},
        "physical_invariants": inv_check,
        "ligo_prediction": ligo_pred,
        "training_ranges": {
            "M_msun":   [float(M_true.min()),  float(M_true.max())],
            "a_over_M": [float(a_true.min()),  float(a_true.max())],
            "f0_hz":    [float(X[:,0].min()),  float(X[:,0].max())],
            "tau0_ms":  [float(X[:,1].min()),  float(X[:,1].max())],
        },
        "limitations": [
            "With a single QNM mode, M and a/M are degenerate: f0*tau0 = Q0/pi depends only on spin.",
            "Separate M prediction requires f0 (gives M given a/M known) or two modes.",
            "For GW150914 at ESPRIT-extracted tau0 >> theory, extrapolation occurs.",
            "Bayesian tau0 (Isi+2019: 13 ms) closer to theory (4 ms for M=68, a=0.69).",
        ],
    }
    out_path = out_dir / "kerr_dictionary_report.json"
    out_path.write_text(json.dumps(report, indent=2))

    # Predictions CSV
    M_pred_all = pipe_M.predict(X)
    a_pred_all = pipe_a.predict(X)
    import csv
    csv_path = out_dir / "kerr_predictions.csv"
    with open(csv_path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["system_name","M_true","a_true","M_pred","a_pred","M_err","a_err"])
        names = [data["system_name"][i] for i in range(len(data["system_name"]))
                 if np.isfinite(data["f0_hz"][i])]
        for i, name in enumerate(names):
            w.writerow([name, round(M_true[i],3), round(a_true[i],4),
                        round(M_pred_all[i],3), round(a_pred_all[i],4),
                        round(abs(M_pred_all[i]-M_true[i]),3),
                        round(abs(a_pred_all[i]-a_true[i]),4)])

    print("\n" + "=" * 70)
    print(f"[OK] Kerr QNM dictionary trained")
    print(f"  M prediction:   R²={metrics_M['r2_cv_mean']:.4f} (CV), "
          f"MAE={metrics_M['mae_train']:.2f} Msun")
    print(f"  a/M prediction: R²={metrics_a['r2_cv_mean']:.4f} (CV), "
          f"MAE={metrics_a['mae_train']:.4f}")
    print(f"  Report: {out_path}")
    print(f"  CSV:    {csv_path}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
