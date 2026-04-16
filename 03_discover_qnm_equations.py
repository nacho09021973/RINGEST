#!/usr/bin/env python3
"""
03_discover_qnm_equations.py  v1.0

Symbolic regression (PySR) on the QNM dataset to discover analytic relations
between ring-down frequencies / damping times and source parameters.

Chain:
    02_poles_to_dataset.py  →  runs/qnm_dataset/qnm_dataset.csv
    THIS SCRIPT             →  runs/qnm_symbolic/
                                  qnm_dataset_profile.json
                                  qnm_symbolic_summary.json   ← KAN contract
                                  <target>/
                                      equation_summary.json
                                      equations_pareto.csv    (if PySR ran)

Default targets (always attempted, require M_final / chi_final for norm cols):
    freq_hz    ~ f(M_final_Msun, chi_final, mode_rank)
    damping_hz ~ f(M_final_Msun, chi_final, mode_rank)

With --include-normalized-targets (dimensionless Kerr plane):
    omega_re_norm ~ f(chi_final, mode_rank)
    omega_im_norm ~ f(chi_final, mode_rank)

Usage
-----
    # Analysis only — profiling, no PySR / no Julia dependency:
    python3 03_discover_qnm_equations.py \\
        --dataset-csv runs/qnm_dataset/qnm_dataset.csv \\
        --analysis-only

    # Full symbolic discovery:
    python3 03_discover_qnm_equations.py \\
        --dataset-csv runs/qnm_dataset/qnm_dataset.csv \\
        --include-normalized-targets \\
        --niterations 80 --maxsize 18
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

SCRIPT_VERSION = "03_discover_qnm_equations.py v1.0"

# ---------------------------------------------------------------------------
# Lazy PySR import — keeps --analysis-only and --help free of Julia overhead
# ---------------------------------------------------------------------------
_PYSR_IMPORT_ATTEMPTED: bool = False
_PYSR_IMPORT_ERROR: Optional[str] = None
PySRRegressor = None  # populated by _ensure_pysr()


def _ensure_pysr() -> None:
    global _PYSR_IMPORT_ATTEMPTED, _PYSR_IMPORT_ERROR, PySRRegressor
    if _PYSR_IMPORT_ATTEMPTED:
        return
    _PYSR_IMPORT_ATTEMPTED = True
    try:
        from pysr import PySRRegressor as _PSR  # noqa: PLC0415
        PySRRegressor = _PSR
    except Exception as exc:
        _PYSR_IMPORT_ERROR = str(exc)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------

def load_dataset(csv_path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            parsed: Dict[str, Any] = {}
            for k, v in row.items():
                if v in ("", "nan", "NaN", "inf", "-inf"):
                    parsed[k] = float("nan")
                else:
                    try:
                        parsed[k] = float(v)
                    except (ValueError, TypeError):
                        parsed[k] = v
            rows.append(parsed)
    return rows


def _col_stats(rows: List[Dict[str, Any]], col: str) -> Dict[str, Any]:
    n = len(rows)
    vals = []
    for r in rows:
        raw = r.get(col)
        if raw is None:
            continue
        try:
            f = float(raw)
        except (ValueError, TypeError):
            continue
        if np.isfinite(f):
            vals.append(f)
    if not vals:
        return {"n_valid": 0, "n_nan": n}
    arr = np.array(vals, dtype=float)
    return {
        "n_valid": int(len(arr)),
        "n_nan": n - int(len(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "median": float(np.median(arr)),
    }


def profile_dataset(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute summary statistics for the QNM dataset."""
    if not rows:
        return {"n_rows": 0, "n_events": 0}

    events = sorted({r["event"] for r in rows if isinstance(r.get("event"), str)})
    n_rows = len(rows)

    def _has_finite(r: Dict[str, Any], col: str) -> bool:
        raw = r.get(col)
        try:
            return np.isfinite(float(raw))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return False

    numeric_cols = [
        "mode_rank", "freq_hz", "damping_hz", "tau_ms",
        "omega_re", "omega_im", "amp_abs", "relative_rms",
        "M_final_Msun", "chi_final", "omega_re_norm", "omega_im_norm",
    ]

    return {
        "n_rows": n_rows,
        "n_events": len(events),
        "events": events,
        "n_with_mass_spin": sum(
            1 for r in rows if _has_finite(r, "M_final_Msun") and _has_finite(r, "chi_final")
        ),
        "n_with_norm": sum(
            1 for r in rows
            if _has_finite(r, "omega_re_norm") and _has_finite(r, "omega_im_norm")
        ),
        "column_stats": {col: _col_stats(rows, col) for col in numeric_cols},
    }


# ---------------------------------------------------------------------------
# PySR symbolic regression — one target at a time
# ---------------------------------------------------------------------------

def run_pysr_target(
    rows: List[Dict[str, Any]],
    target_col: str,
    feature_cols: List[str],
    out_dir: Path,
    niterations: int,
    maxsize: int,
    min_rows: int,
    seed: int,
) -> Dict[str, Any]:
    """
    Fit PySR on *target_col ~ f(feature_cols)* using finite rows only.
    Writes equation_summary.json and equations_pareto.csv to *out_dir*.
    Returns the equation_summary dict.
    """
    _ensure_pysr()
    if PySRRegressor is None:
        return {
            "target": target_col,
            "features": feature_cols,
            "status": "pysr_unavailable",
            "error": _PYSR_IMPORT_ERROR,
        }

    needed = [target_col] + feature_cols
    valid_rows = [
        r for r in rows
        if all(
            np.isfinite(float(r.get(c, float("nan")) or float("nan")))
            for c in needed
        )
    ]

    if len(valid_rows) < min_rows:
        summary = {
            "target": target_col,
            "features": feature_cols,
            "status": "insufficient_data",
            "n_valid": len(valid_rows),
            "min_rows": min_rows,
        }
        (out_dir / "equation_summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        return summary

    X = np.array([[float(r[c]) for c in feature_cols] for r in valid_rows])
    y = np.array([float(r[target_col]) for r in valid_rows])

    model = PySRRegressor(
        niterations=niterations,
        populations=8,
        population_size=50,
        binary_operators=["+", "-", "*", "/"],
        unary_operators=["square", "sqrt", "log", "neg"],
        extra_sympy_mappings={"neg": lambda x: -x},
        elementwise_loss="L2DistLoss()",
        maxsize=maxsize,
        model_selection="best",
        progress=False,
        verbosity=0,
        parallelism="serial",
        deterministic=True,
        random_state=seed,
        tempdir=str(out_dir),
    )
    model.fit(X, y, variable_names=feature_cols)

    best = model.get_best()
    y_pred = model.predict(X)
    ss_res = float(np.sum((y - y_pred) ** 2))
    ss_tot = float(np.sum((y - float(np.mean(y))) ** 2))
    r2 = 1.0 - ss_res / (ss_tot + 1e-10)

    pareto_path: Optional[Path] = out_dir / "equations_pareto.csv"
    try:
        model.equations_.to_csv(str(pareto_path), index=False)
    except Exception:
        pareto_path = None

    summary = {
        "target": target_col,
        "features": feature_cols,
        "status": "ok",
        "n_rows": len(valid_rows),
        "best_equation": str(best["equation"]),
        "complexity": int(best["complexity"]),
        "loss": float(best["loss"]),
        "r2": r2,
        "pareto_csv": str(pareto_path) if pareto_path else None,
    }
    (out_dir / "equation_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return summary


# ---------------------------------------------------------------------------
# KAN output contract
# ---------------------------------------------------------------------------

def build_kan_contract(
    dataset_csv: Path,
    profile: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Produce the section of qnm_symbolic_summary.json that the KAN stage reads.

    KAN task: learn a smooth map (omega_re_norm, omega_im_norm) → family cluster
    using the 2-D dimensionless QNM plane.  If no normalised columns are
    available, fall back to dimensional features for regression.
    """
    n_with_norm = profile.get("n_with_norm", 0)
    n_rows = profile.get("n_rows", 0)

    if n_with_norm >= 4:
        kan_features = ["omega_re_norm", "omega_im_norm"]
        kan_task = "cluster_classification"
        kan_note = (
            "Feed (omega_re_norm, omega_im_norm) as 2-D input to KAN. "
            "Each row is a (event, mode_rank) point in the dimensionless Kerr "
            "QNM plane. Cluster labels can come from GWOSC family assignments "
            "or be learned unsupervised (k-means / HDBSCAN)."
        )
    else:
        kan_features = ["freq_hz", "damping_hz", "mode_rank"]
        kan_task = "frequency_regression"
        kan_note = (
            "Dimensionless columns are absent or sparse (no M_final / chi_final). "
            "Fall back to (freq_hz, damping_hz, mode_rank) for KAN regression."
        )

    return {
        "schema_version": "1.0",
        "producer": SCRIPT_VERSION,
        "dataset_csv": str(dataset_csv.resolve()),
        "n_rows": n_rows,
        "n_events": profile.get("n_events", 0),
        "n_rows_with_dimensionless": n_with_norm,
        "kan_input_features": kan_features,
        "kan_suggested_task": kan_task,
        "kan_note": kan_note,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description=(
            "Symbolic regression on QNM dataset "
            "(02_poles_to_dataset.py output)."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument(
        "--dataset-csv",
        default="runs/qnm_dataset/qnm_dataset.csv",
        help="CSV produced by 02_poles_to_dataset.py",
    )
    ap.add_argument(
        "--out-dir",
        default="runs/qnm_symbolic",
        help="Output directory for profile, summary, and per-target results",
    )
    ap.add_argument(
        "--analysis-only", action="store_true",
        help="Profile the dataset and write KAN contract; skip PySR entirely",
    )
    ap.add_argument(
        "--include-normalized-targets", action="store_true",
        help=(
            "Also run PySR on dimensionless targets "
            "omega_re_norm and omega_im_norm ~ f(chi_final, mode_rank)"
        ),
    )
    ap.add_argument(
        "--niterations", type=int, default=50,
        help="PySR iterations per target",
    )
    ap.add_argument(
        "--maxsize", type=int, default=15,
        help="PySR maximum expression size",
    )
    ap.add_argument(
        "--min-rows", type=int, default=10,
        help="Minimum finite rows required before running PySR on a target",
    )
    ap.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for PySR",
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()

    dataset_csv = Path(args.dataset_csv).resolve()
    out_dir = Path(args.out_dir).resolve()

    print("=" * 60)
    print(f"QNM SYMBOLIC DISCOVERY  —  {SCRIPT_VERSION}")
    print(f"  dataset : {dataset_csv}")
    print(f"  out-dir : {out_dir}")
    print(f"  mode    : {'analysis-only' if args.analysis_only else 'symbolic-regression'}")
    print("=" * 60)

    if not dataset_csv.exists():
        print(f"[ERROR] Dataset CSV not found: {dataset_csv}")
        print(
            "  Run 02_poles_to_dataset.py first:\n"
            "    python3 02_poles_to_dataset.py --runs-dir runs/gwosc_all"
        )
        return 1

    # ------------------------------------------------------------------
    # Load & profile
    # ------------------------------------------------------------------
    print("\nLoading dataset...")
    rows = load_dataset(dataset_csv)
    print(f"  {len(rows)} rows loaded")

    profile = profile_dataset(rows)
    print(
        f"  {profile['n_events']} events  |  "
        f"{profile['n_with_norm']} rows with dimensionless columns"
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    profile_path = out_dir / "qnm_dataset_profile.json"
    profile_path.write_text(
        json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"  Profile : {profile_path}")

    # ------------------------------------------------------------------
    # Build target list
    # ------------------------------------------------------------------
    # Default: dimensional targets (always available if events have poles)
    targets: List[Dict[str, Any]] = [
        {
            "col": "freq_hz",
            "features": ["M_final_Msun", "chi_final", "mode_rank"],
        },
        {
            "col": "damping_hz",
            "features": ["M_final_Msun", "chi_final", "mode_rank"],
        },
    ]

    if args.include_normalized_targets:
        targets += [
            {
                "col": "omega_re_norm",
                "features": ["chi_final", "mode_rank"],
            },
            {
                "col": "omega_im_norm",
                "features": ["chi_final", "mode_rank"],
            },
        ]

    # ------------------------------------------------------------------
    # Symbolic regression (skipped in analysis-only mode)
    # ------------------------------------------------------------------
    target_summaries: List[Dict[str, Any]] = []

    if not args.analysis_only:
        for t in targets:
            (out_dir / t["col"]).mkdir(parents=True, exist_ok=True)

    if args.analysis_only:
        print("\n[analysis-only] Skipping PySR.")
        for t in targets:
            target_summaries.append({
                "target": t["col"],
                "features": t["features"],
                "status": "skipped_analysis_only",
            })
    else:
        for t in targets:
            col = t["col"]
            features = t["features"]
            print(f"\nTarget: {col}  features: {features}")
            result = run_pysr_target(
                rows=rows,
                target_col=col,
                feature_cols=features,
                out_dir=out_dir / col,
                niterations=args.niterations,
                maxsize=args.maxsize,
                min_rows=args.min_rows,
                seed=args.seed,
            )
            target_summaries.append(result)
            status = result.get("status", "?")
            if status == "ok":
                print(f"  Best: {result.get('best_equation')}  R²={result.get('r2', 0):.4f}")
            else:
                print(f"  Status: {status}")

    # ------------------------------------------------------------------
    # Write qnm_symbolic_summary.json  (KAN contract)
    # ------------------------------------------------------------------
    kan_contract = build_kan_contract(dataset_csv, profile)

    summary = {
        "created_at": utc_now(),
        "script": SCRIPT_VERSION,
        "dataset_csv": str(dataset_csv),
        "out_dir": str(out_dir),
        "analysis_only": bool(args.analysis_only),
        "pysr_import_attempted": bool(_PYSR_IMPORT_ATTEMPTED),
        "pysr_available": (
            bool(PySRRegressor is not None) if _PYSR_IMPORT_ATTEMPTED else None
        ),
        "pysr_import_error": _PYSR_IMPORT_ERROR,
        "n_rows": profile["n_rows"],
        "n_events": profile["n_events"],
        "n_with_norm": profile["n_with_norm"],
        "targets": target_summaries,
        "kan_contract": kan_contract,
    }

    summary_path = out_dir / "qnm_symbolic_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # ------------------------------------------------------------------
    # Final report
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("DONE")
    print(f"  Profile : {profile_path}")
    print(f"  Summary : {summary_path}")
    if not args.analysis_only:
        ok = sum(1 for t in target_summaries if t.get("status") == "ok")
        print(f"  Targets : {ok}/{len(target_summaries)} symbolic equations found")
    print("=" * 60)
    print()
    print("KAN contract written to qnm_symbolic_summary.json → kan_contract")
    print(f"  Input features : {kan_contract['kan_input_features']}")
    print(f"  Suggested task : {kan_contract['kan_suggested_task']}")
    print()
    print("Next step — KAN training:")
    print("  python3 04_kan_qnm_classifier.py \\")
    print("      --summary runs/qnm_symbolic/qnm_symbolic_summary.json")

    return 0


if __name__ == "__main__":
    sys.exit(main())
