#!/usr/bin/env python3
"""
Audita el sesgo UV de Stage 02 contra truth AdS ya materializado en disco.

Uso por defecto:
  - Lee los NPZ de predicciones del run fixAprior congelado.
  - Mide el error de A_pred y f_pred en la ventana UV z <= z_uv_max.
  - Verifica adicionalmente que A_truth coincide con -log(z).
  - Escribe resultados evento a evento y un resumen agregado.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN_DIR = REPO_ROOT / "runs/ads_gkpw_20260416_091407_fixAprior"
DEFAULT_PREDICTIONS_DIR = DEFAULT_RUN_DIR / "02_emergent_geometry_engine/predictions"
DEFAULT_OUT_DIR = DEFAULT_RUN_DIR / "analysis"
DEFAULT_OUT_CSV = DEFAULT_OUT_DIR / "stage02_uv_truth_audit.csv"
DEFAULT_OUT_JSON = DEFAULT_OUT_DIR / "stage02_uv_truth_summary.json"


def _metrics(pred: np.ndarray, truth: np.ndarray) -> dict[str, float]:
    delta = np.asarray(pred, dtype=np.float64) - np.asarray(truth, dtype=np.float64)
    return {
        "bias": float(np.mean(delta)),
        "mae": float(np.mean(np.abs(delta))),
        "rmse": float(np.sqrt(np.mean(delta**2))),
        "max_abs": float(np.max(np.abs(delta))),
    }


def _load_row(npz_path: Path, z_uv_max: float) -> dict[str, float | str | int]:
    data = np.load(npz_path)
    z = np.asarray(data["z"], dtype=np.float64)
    A_pred = np.asarray(data["A_pred"], dtype=np.float64)
    A_truth = np.asarray(data["A_truth"], dtype=np.float64)
    f_pred = np.asarray(data["f_pred"], dtype=np.float64)
    f_truth = np.asarray(data["f_truth"], dtype=np.float64)

    uv_mask = z <= z_uv_max
    if not np.any(uv_mask):
        raise ValueError(f"No hay puntos UV en {npz_path} para z_uv_max={z_uv_max}")

    z_uv = z[uv_mask]
    A_pred_uv = A_pred[uv_mask]
    A_truth_uv = A_truth[uv_mask]
    f_pred_uv = f_pred[uv_mask]
    f_truth_uv = f_truth[uv_mask]

    A_metrics = _metrics(A_pred_uv, A_truth_uv)
    f_metrics = _metrics(f_pred_uv, f_truth_uv)
    formula_metrics = _metrics(A_truth_uv, -np.log(z_uv))

    ratio = A_metrics["mae"] / max(f_metrics["mae"], 1e-12)
    if ratio >= 5.0:
        dominant = "A"
    elif ratio <= 0.2:
        dominant = "f"
    else:
        dominant = "mixed"

    return {
        "event": npz_path.stem.replace("_geometry", ""),
        "category": str(data["category"]),
        "n_uv_points": int(z_uv.size),
        "z_uv_min": float(z_uv.min()),
        "z_uv_max": float(z_uv.max()),
        "z0": float(z[0]),
        "A0_pred": float(A_pred[0]),
        "A0_truth": float(A_truth[0]),
        "A0_formula": float(-np.log(z[0])),
        "A0_bias": float(A_pred[0] - A_truth[0]),
        "f0_pred": float(f_pred[0]),
        "f0_truth": float(f_truth[0]),
        "f0_bias": float(f_pred[0] - f_truth[0]),
        "A_uv_bias": A_metrics["bias"],
        "A_uv_mae": A_metrics["mae"],
        "A_uv_rmse": A_metrics["rmse"],
        "A_uv_max_abs": A_metrics["max_abs"],
        "f_uv_bias": f_metrics["bias"],
        "f_uv_mae": f_metrics["mae"],
        "f_uv_rmse": f_metrics["rmse"],
        "f_uv_max_abs": f_metrics["max_abs"],
        "A_truth_vs_minus_log_mae": formula_metrics["mae"],
        "A_truth_vs_minus_log_max_abs": formula_metrics["max_abs"],
        "A_over_f_mae_ratio": float(ratio),
        "uv_error_dominant": dominant,
        "zh_pred": float(data["zh_pred"]),
        "zh_truth": float(data["zh_truth"]),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Audita el sesgo UV de Stage 02 contra truth AdS.")
    ap.add_argument("--predictions-dir", type=Path, default=DEFAULT_PREDICTIONS_DIR)
    ap.add_argument("--z-uv-max", type=float, default=0.2)
    ap.add_argument("--out-csv", type=Path, default=DEFAULT_OUT_CSV)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    args = ap.parse_args()

    predictions_dir = args.predictions_dir.resolve()
    out_csv = args.out_csv.resolve()
    out_json = args.out_json.resolve()
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    rows = [_load_row(path, args.z_uv_max) for path in sorted(predictions_dir.glob("*_geometry.npz"))]
    if not rows:
        raise SystemExit(f"No se encontraron predicciones en {predictions_dir}")

    fieldnames = list(rows[0].keys())
    with out_csv.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    a_mae = np.array([float(row["A_uv_mae"]) for row in rows], dtype=np.float64)
    f_mae = np.array([float(row["f_uv_mae"]) for row in rows], dtype=np.float64)
    ratios = np.array([float(row["A_over_f_mae_ratio"]) for row in rows], dtype=np.float64)
    a0_bias = np.array([float(row["A0_bias"]) for row in rows], dtype=np.float64)
    f0_bias = np.array([float(row["f0_bias"]) for row in rows], dtype=np.float64)

    summary = {
        "predictions_dir": str(predictions_dir),
        "n_events": len(rows),
        "z_uv_max_requested": float(args.z_uv_max),
        "n_uv_points_per_event": int(rows[0]["n_uv_points"]),
        "A_uv_mae_mean": float(np.mean(a_mae)),
        "A_uv_mae_median": float(np.median(a_mae)),
        "f_uv_mae_mean": float(np.mean(f_mae)),
        "f_uv_mae_median": float(np.median(f_mae)),
        "A_over_f_mae_ratio_mean": float(np.mean(ratios)),
        "A_over_f_mae_ratio_median": float(np.median(ratios)),
        "A0_bias_mean": float(np.mean(a0_bias)),
        "A0_bias_median": float(np.median(a0_bias)),
        "f0_bias_mean": float(np.mean(f0_bias)),
        "f0_bias_median": float(np.median(f0_bias)),
        "dominant_uv_error_counts": {
            key: int(sum(1 for row in rows if row["uv_error_dominant"] == key))
            for key in ("A", "mixed", "f")
        },
        "A_truth_formula_check_max_abs": float(
            np.max(np.array([float(row["A_truth_vs_minus_log_max_abs"]) for row in rows], dtype=np.float64))
        ),
        "worst_A_uv_event": max(rows, key=lambda row: float(row["A_uv_mae"])),
        "worst_f_uv_event": max(rows, key=lambda row: float(row["f_uv_mae"])),
    }

    out_json.write_text(json.dumps(summary, indent=2))

    print(out_csv)
    print(out_json)


if __name__ == "__main__":
    main()
