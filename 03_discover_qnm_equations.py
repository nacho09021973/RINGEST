#!/usr/bin/env python3
"""
03_discover_qnm_equations.py

Run symbolic regression on the flat QNM dataset produced by
02_poles_to_dataset.py.

Chain:
    00_download_gwosc_events.py  → NPZ per event/IFO
    00_load_ligo_data.py         → boundary HDF5 (whitened strain)
    01_extract_ringdown_poles.py → poles_joint.json per event
    02_poles_to_dataset.py       → qnm_dataset.csv
    THIS SCRIPT                  → symbolic equations for QNM observables

Default input:
    runs/qnm_dataset/qnm_dataset.csv

Default output:
    runs/qnm_symbolic/
        qnm_symbolic_summary.json
        qnm_dataset_profile.json
        <target>/equation_summary.json
        <target>/equations_pareto.csv

Targets discovered by default:
    - freq_hz     as function of [M_final_Msun, chi_final, mode_rank]
    - damping_hz  as function of [M_final_Msun, chi_final, mode_rank]

If the dataset contains normalized columns and --include-normalized-targets is set,
it also tries:
    - omega_re_norm as function of [chi_final, mode_rank]
    - omega_im_norm as function of [chi_final, mode_rank]

Design notes:
    - No Kerr/QNM formulae are injected as forced structure.
    - The script is still useful without PySR: it writes dataset diagnostics and
      target-preparation summaries, and marks symbolic regression as skipped.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

try:
    from sklearn.model_selection import train_test_split

    HAS_SKLEARN = True
except Exception:
    HAS_SKLEARN = False
    train_test_split = None  # type: ignore


SCRIPT_VERSION = "03_discover_qnm_equations.py v1.0"
_PYSR_IMPORT_ATTEMPTED = False
_PYSR_IMPORT_ERROR: Optional[str] = None
PySRRegressor = None  # type: ignore[assignment]


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_pysr() -> Tuple[bool, Optional[str]]:
    global _PYSR_IMPORT_ATTEMPTED, _PYSR_IMPORT_ERROR, PySRRegressor

    if _PYSR_IMPORT_ATTEMPTED:
        return PySRRegressor is not None, _PYSR_IMPORT_ERROR

    _PYSR_IMPORT_ATTEMPTED = True
    try:
        from pysr import PySRRegressor as _PySRRegressor

        PySRRegressor = _PySRRegressor  # type: ignore[assignment]
        _PYSR_IMPORT_ERROR = None
        return True, None
    except Exception as exc:
        PySRRegressor = None  # type: ignore[assignment]
        _PYSR_IMPORT_ERROR = str(exc)
        return False, _PYSR_IMPORT_ERROR


def _safe_float(value: Any) -> float:
    if value is None:
        return float("nan")
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return float("nan")
    try:
        return float(text)
    except ValueError:
        return float("nan")


def _json_default(value: Any) -> Any:
    if isinstance(value, (np.floating,)):
        out = float(value)
        if math.isnan(out) or math.isinf(out):
            return None
        return out
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=_json_default) + "\n",
        encoding="utf-8",
    )


def r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    if y_true.size == 0:
        return float("nan")
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    if ss_tot <= 1e-12:
        return 1.0 if ss_res <= 1e-12 else 0.0
    return 1.0 - ss_res / ss_tot


def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    if y_true.size == 0:
        return float("nan")
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    if y_true.size == 0:
        return float("nan")
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def load_dataset(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
    return rows


def summarize_dataset(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    events = sorted({str(r.get("event", "")).strip() for r in rows if str(r.get("event", "")).strip()})
    ifos: Dict[str, int] = {}
    mode_rank_hist: Dict[str, int] = {}

    masses = np.array([_safe_float(r.get("M_final_Msun", r.get("M_final"))) for r in rows], dtype=np.float64)
    spins = np.array([_safe_float(r.get("chi_final")) for r in rows], dtype=np.float64)
    freqs = np.array([_safe_float(r.get("freq_hz")) for r in rows], dtype=np.float64)
    damps = np.array([_safe_float(r.get("damping_hz")) for r in rows], dtype=np.float64)

    for row in rows:
        ifo = str(row.get("ifo", "")).strip() or "UNKNOWN"
        ifos[ifo] = ifos.get(ifo, 0) + 1
        rank = row.get("mode_rank", "")
        key = str(rank).strip() or "UNKNOWN"
        mode_rank_hist[key] = mode_rank_hist.get(key, 0) + 1

    def _finite_stats(values: np.ndarray) -> Dict[str, Any]:
        valid = values[np.isfinite(values)]
        if valid.size == 0:
            return {"count": 0, "min": None, "max": None, "mean": None, "median": None}
        return {
            "count": int(valid.size),
            "min": float(np.min(valid)),
            "max": float(np.max(valid)),
            "mean": float(np.mean(valid)),
            "median": float(np.median(valid)),
        }

    return {
        "created_at": utc_now(),
        "n_rows": int(len(rows)),
        "n_events": int(len(events)),
        "events_preview": events[:20],
        "ifos": ifos,
        "mode_rank_histogram": mode_rank_hist,
        "mass_stats_msun": _finite_stats(masses),
        "spin_stats": _finite_stats(spins),
        "freq_stats_hz": _finite_stats(freqs),
        "damping_stats_hz": _finite_stats(damps),
    }


@dataclass(frozen=True)
class TargetSpec:
    name: str
    feature_columns: Tuple[str, ...]
    description: str


def resolve_target_specs(rows: Sequence[Dict[str, Any]], include_normalized: bool) -> List[TargetSpec]:
    columns = set(rows[0].keys()) if rows else set()
    specs = [
        TargetSpec(
            name="freq_hz",
            feature_columns=("M_final_Msun", "chi_final", "mode_rank"),
            description="Observed ringdown frequency in Hz",
        ),
        TargetSpec(
            name="damping_hz",
            feature_columns=("M_final_Msun", "chi_final", "mode_rank"),
            description="Observed damping rate in Hz",
        ),
    ]

    if include_normalized and {"omega_re_norm", "omega_im_norm"}.issubset(columns):
        specs.extend(
            [
                TargetSpec(
                    name="omega_re_norm",
                    feature_columns=("chi_final", "mode_rank"),
                    description="Dimensionless real QNM frequency M*Re(omega)",
                ),
                TargetSpec(
                    name="omega_im_norm",
                    feature_columns=("chi_final", "mode_rank"),
                    description="Dimensionless imaginary QNM frequency M*Im(omega)",
                ),
            ]
        )
    return specs


def prepare_matrix(
    rows: Sequence[Dict[str, Any]],
    target: str,
    feature_columns: Sequence[str],
    max_mode_rank: Optional[int],
) -> Tuple[np.ndarray, np.ndarray, List[Dict[str, Any]], Dict[str, Any]]:
    prepared_rows: List[Dict[str, Any]] = []
    X_list: List[List[float]] = []
    y_list: List[float] = []

    n_missing = 0
    n_filtered_rank = 0

    for row in rows:
        mode_rank = _safe_float(row.get("mode_rank"))
        if max_mode_rank is not None and np.isfinite(mode_rank) and mode_rank > max_mode_rank:
            n_filtered_rank += 1
            continue

        y = _safe_float(row.get(target))
        x = [_safe_float(row.get(col)) for col in feature_columns]

        if not np.isfinite(y) or not all(np.isfinite(v) for v in x):
            n_missing += 1
            continue

        prepared_rows.append(row)
        X_list.append(x)
        y_list.append(y)

    X = np.asarray(X_list, dtype=np.float64)
    y = np.asarray(y_list, dtype=np.float64)

    profile = {
        "target": target,
        "feature_columns": list(feature_columns),
        "n_rows_total": int(len(rows)),
        "n_rows_used": int(len(prepared_rows)),
        "n_rows_missing_or_nonfinite": int(n_missing),
        "n_rows_filtered_by_mode_rank": int(n_filtered_rank),
        "target_min": float(np.min(y)) if y.size else None,
        "target_max": float(np.max(y)) if y.size else None,
        "target_mean": float(np.mean(y)) if y.size else None,
    }
    return X, y, prepared_rows, profile


def split_train_test(
    X: np.ndarray,
    y: np.ndarray,
    seed: int,
    test_fraction: float,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    if (
        not HAS_SKLEARN
        or X.shape[0] < 8
        or test_fraction <= 0.0
        or test_fraction >= 0.5
    ):
        return X, X[:0], y, y[:0]

    X_train, X_test, y_train, y_test = train_test_split(  # type: ignore[misc]
        X,
        y,
        test_size=test_fraction,
        random_state=seed,
    )
    return X_train, X_test, y_train, y_test


def equations_table_to_csv(model: Any, path: Path) -> Optional[str]:
    equations = getattr(model, "equations_", None)
    if equations is None:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        equations.to_csv(path, index=False)
        return str(path)
    except Exception:
        return None


def run_symbolic_regression(
    target_spec: TargetSpec,
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    output_dir: Path,
    niterations: int,
    maxsize: int,
    seed: int,
) -> Dict[str, Any]:
    has_pysr, pysr_error = ensure_pysr()
    if not has_pysr:
        return {
            "status": "skipped",
            "reason": "pysr_not_available",
            "detail": pysr_error,
        }

    model = PySRRegressor(
        niterations=niterations,
        populations=8,
        population_size=50,
        maxsize=maxsize,
        model_selection="best",
        binary_operators=["+", "-", "*", "/"],
        unary_operators=["square", "cube", "abs", "neg"],
        extra_sympy_mappings={"neg": lambda x: -x},
        elementwise_loss="L2DistLoss()",
        progress=False,
        verbosity=0,
        deterministic=True,
        random_state=seed,
        parallelism="serial",
        tempdir=str(output_dir),
    )

    model.fit(X_train, y_train, variable_names=list(target_spec.feature_columns))
    best = model.get_best()

    y_pred_train = np.asarray(model.predict(X_train), dtype=np.float64)
    y_pred_test = np.asarray(model.predict(X_test), dtype=np.float64) if X_test.size else np.array([], dtype=np.float64)

    pareto_path = output_dir / "equations_pareto.csv"
    exported_pareto = equations_table_to_csv(model, pareto_path)

    result = {
        "status": "ok",
        "equation": str(best["equation"]),
        "sympy_format": str(best["sympy_format"]) if "sympy_format" in best else str(best["equation"]),
        "complexity": int(best["complexity"]),
        "loss": float(best["loss"]),
        "feature_columns": list(target_spec.feature_columns),
        "train_metrics": {
            "r2": r2_score(y_train, y_pred_train),
            "mae": mae(y_train, y_pred_train),
            "rmse": rmse(y_train, y_pred_train),
            "n_rows": int(y_train.size),
        },
        "test_metrics": {
            "r2": r2_score(y_test, y_pred_test) if y_test.size else None,
            "mae": mae(y_test, y_pred_test) if y_test.size else None,
            "rmse": rmse(y_test, y_pred_test) if y_test.size else None,
            "n_rows": int(y_test.size),
        },
        "artifacts": {
            "equations_pareto_csv": exported_pareto,
        },
    }
    return result


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Discover empirical QNM equations from qnm_dataset.csv using PySR."
    )
    parser.add_argument(
        "--dataset-csv",
        default="runs/qnm_dataset/qnm_dataset.csv",
        help="Input CSV from 02_poles_to_dataset.py (default: runs/qnm_dataset/qnm_dataset.csv)",
    )
    parser.add_argument(
        "--out-dir",
        default="runs/qnm_symbolic",
        help="Output directory for symbolic-discovery artifacts (default: runs/qnm_symbolic)",
    )
    parser.add_argument(
        "--include-normalized-targets",
        action="store_true",
        help="Also fit omega_re_norm and omega_im_norm if those columns exist.",
    )
    parser.add_argument(
        "--max-mode-rank",
        type=int,
        default=None,
        help="Ignore rows with mode_rank greater than this value.",
    )
    parser.add_argument(
        "--min-rows",
        type=int,
        default=12,
        help="Minimum usable rows required per target before fitting PySR (default: 12).",
    )
    parser.add_argument(
        "--test-fraction",
        type=float,
        default=0.2,
        help="Holdout fraction for quick generalization metrics when sklearn is available (default: 0.2).",
    )
    parser.add_argument(
        "--niterations",
        type=int,
        default=80,
        help="PySR iterations per target (default: 80).",
    )
    parser.add_argument(
        "--maxsize",
        type=int,
        default=18,
        help="Maximum symbolic-expression complexity (default: 18).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )
    parser.add_argument(
        "--analysis-only",
        action="store_true",
        help="Do not run PySR; only write dataset diagnostics and target profiles.",
    )
    return parser


def main() -> int:
    args = build_argument_parser().parse_args()

    dataset_csv = Path(args.dataset_csv).resolve()
    out_dir = Path(args.out_dir).resolve()

    if not dataset_csv.exists():
        print(f"[ERROR] Dataset CSV not found: {dataset_csv}")
        print("Run 02_poles_to_dataset.py first.")
        return 1

    rows = load_dataset(dataset_csv)
    if not rows:
        print(f"[ERROR] Dataset CSV is empty: {dataset_csv}")
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)

    dataset_profile = summarize_dataset(rows)
    write_json(out_dir / "qnm_dataset_profile.json", dataset_profile)

    target_specs = resolve_target_specs(rows, include_normalized=args.include_normalized_targets)
    target_results: Dict[str, Any] = {}

    print("=" * 60)
    print(f"QNM SYMBOLIC DISCOVERY  —  {SCRIPT_VERSION}")
    print(f"dataset : {dataset_csv}")
    print(f"out-dir : {out_dir}")
    print(f"rows    : {dataset_profile['n_rows']}")
    print(f"events  : {dataset_profile['n_events']}")
    print("=" * 60)

    for target_spec in target_specs:
        target_dir = out_dir / target_spec.name
        X, y, _, prep_profile = prepare_matrix(
            rows=rows,
            target=target_spec.name,
            feature_columns=target_spec.feature_columns,
            max_mode_rank=args.max_mode_rank,
        )

        target_summary: Dict[str, Any] = {
            "target": target_spec.name,
            "description": target_spec.description,
            "dataset_profile": prep_profile,
        }

        print()
        print(f"[target={target_spec.name}]")
        print(f"  features : {', '.join(target_spec.feature_columns)}")
        print(f"  usable   : {prep_profile['n_rows_used']} / {prep_profile['n_rows_total']}")

        if y.size < args.min_rows:
            target_summary["symbolic_regression"] = {
                "status": "skipped",
                "reason": "insufficient_rows",
                "min_rows_required": int(args.min_rows),
            }
            print(f"  skipped  : insufficient rows (< {args.min_rows})")
        elif args.analysis_only:
            target_summary["symbolic_regression"] = {
                "status": "skipped",
                "reason": "analysis_only",
            }
            print("  skipped  : analysis-only")
        else:
            X_train, X_test, y_train, y_test = split_train_test(
                X=X,
                y=y,
                seed=args.seed,
                test_fraction=args.test_fraction,
            )
            print(f"  fit rows : train={y_train.size}, test={y_test.size}")

            result = run_symbolic_regression(
                target_spec=target_spec,
                X_train=X_train,
                y_train=y_train,
                X_test=X_test,
                y_test=y_test,
                output_dir=target_dir,
                niterations=args.niterations,
                maxsize=args.maxsize,
                seed=args.seed,
            )
            target_summary["symbolic_regression"] = result

            status = result.get("status")
            if status == "ok":
                print(f"  equation : {result['equation']}")
                print(f"  train R2 : {result['train_metrics']['r2']:.4f}")
                test_r2 = result["test_metrics"]["r2"]
                if test_r2 is not None:
                    print(f"  test R2  : {test_r2:.4f}")
            else:
                print(f"  skipped  : {result.get('reason')}")

        write_json(target_dir / "equation_summary.json", target_summary)
        target_results[target_spec.name] = target_summary

    summary = {
        "created_at": utc_now(),
        "script": SCRIPT_VERSION,
        "dataset_csv": str(dataset_csv),
        "out_dir": str(out_dir),
        "analysis_only": bool(args.analysis_only),
        "pysr_import_attempted": bool(_PYSR_IMPORT_ATTEMPTED),
        "pysr_available": (bool(PySRRegressor is not None) if _PYSR_IMPORT_ATTEMPTED else None),
        "pysr_import_error": _PYSR_IMPORT_ERROR,
        "include_normalized_targets": bool(args.include_normalized_targets),
        "targets": target_results,
    }
    write_json(out_dir / "qnm_symbolic_summary.json", summary)

    print()
    print("=" * 60)
    print("DONE")
    print(f"  Profile : {out_dir / 'qnm_dataset_profile.json'}")
    print(f"  Summary : {out_dir / 'qnm_symbolic_summary.json'}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
