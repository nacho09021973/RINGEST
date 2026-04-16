#!/usr/bin/env python3
"""
03_clean_physical_dataset.py

Aplica filtro físico mínimo antes de reclustering KAN / Kerr validation.
Elimina filas no físicas o poco interpretables.

Outputs:
    runs/qnm_dataset/qnm_dataset_clean.csv
    runs/qnm_dataset/qnm_dataset_clean_manifest.json
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

SCRIPT_VERSION = "03_clean_physical_dataset.py v1.1"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Limpieza física del dataset QNM (pre-clustering)"
    )
    ap.add_argument(
        "--input-csv",
        default="runs/qnm_dataset/qnm_dataset.csv",
        help="CSV original (default: runs/qnm_dataset/qnm_dataset.csv)",
    )
    ap.add_argument(
        "--output-dir",
        default="runs/qnm_dataset",
        help="Carpeta de salida",
    )
    ap.add_argument(
        "--max-re-norm",
        type=float,
        default=1.5,
        help="omega_re_norm < este valor (corte fenomenológico, default: 1.5)",
    )
    ap.add_argument(
        "--max-im-norm",
        type=float,
        default=-1e-3,
        help="omega_im_norm < este valor (default: -1e-3)",
    )
    args = ap.parse_args()

    input_path = Path(args.input_csv)
    out_dir = Path(args.output_dir)
    out_csv = out_dir / "qnm_dataset_clean.csv"
    out_manifest = out_dir / "qnm_dataset_clean_manifest.json"

    if not input_path.exists():
        print(f"[ERROR] No se encontró {input_path}")
        print("       Ejecuta primero 02_poles_to_dataset.py --params-csv o --fetch-params")
        return 1

    print("=" * 75)
    print(f"LIMPIEZA FÍSICA DEL DATASET QNM  —  {SCRIPT_VERSION}")
    print(f"Input  : {input_path}")
    print(f"Output : {out_csv}")
    print("=" * 75)

    df = pd.read_csv(input_path)

    required_cols = [
        "event",
        "mode_rank",
        "M_final_Msun",
        "chi_final",
        "omega_re_norm",
        "omega_im_norm",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"[ERROR] Faltan columnas requeridas en el CSV: {missing}")
        return 1

    mask = (
        (df["omega_re_norm"] > 0.0)
        & (df["omega_re_norm"] < args.max_re_norm)
        & (df["omega_im_norm"] < args.max_im_norm)
        & df["M_final_Msun"].notna()
        & df["chi_final"].notna()
    )

    df_clean = df.loc[mask].copy().reset_index(drop=True)

    n_total = len(df)
    n_clean = len(df_clean)
    n_removed = n_total - n_clean

    print("\nFiltro físico aplicado:")
    print(f"  • omega_re_norm ∈ (0, {args.max_re_norm})")
    print(f"  • omega_im_norm < {args.max_im_norm}")
    print("  • M_final_Msun y chi_final no NaN")

    print("\nResultados:")
    print(f"  Filas originales : {n_total}")
    print(f"  Filas limpias    : {n_clean}  ({(100.0 * n_clean / n_total) if n_total else 0.0:.1f}%)")
    print(f"  Filas eliminadas : {n_removed}  ({(100.0 * n_removed / n_total) if n_total else 0.0:.1f}%)")
    print(f"  Eventos antes    : {df['event'].nunique()}")
    print(f"  Eventos después  : {df_clean['event'].nunique()}")

    print("\nSupervivencia por mode_rank:")
    orig_counts = df["mode_rank"].value_counts().sort_index()
    clean_counts = df_clean["mode_rank"].value_counts().sort_index()
    all_ranks = sorted(set(orig_counts.index).union(set(clean_counts.index)))
    for rank in all_ranks:
        orig = int(orig_counts.get(rank, 0))
        clean = int(clean_counts.get(rank, 0))
        frac = (100.0 * clean / orig) if orig else 0.0
        print(f"  mode_rank {int(rank):2d} : {clean:4d} / {orig:4d}  ({frac:5.1f}% sobreviven)")

    out_dir.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(out_csv, index=False)

    manifest = {
        "created_at": utc_now(),
        "script": SCRIPT_VERSION,
        "input_csv": str(input_path),
        "output_csv": str(out_csv),
        "filters": {
            "omega_re_norm": {"min_exclusive": 0.0, "max_exclusive": args.max_re_norm},
            "omega_im_norm": {"max_exclusive": args.max_im_norm},
            "require_mass_spin": True,
        },
        "rows_before": int(n_total),
        "rows_after": int(n_clean),
        "removed": int(n_removed),
        "events_before": int(df["event"].nunique()),
        "events_after": int(df_clean["event"].nunique()),
        "mode_rank_survival": {str(int(k)): int(v) for k, v in clean_counts.to_dict().items()},
        "columns": list(df_clean.columns),
    }
    out_manifest.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print("\n" + "=" * 75)
    print("DATASET LIMPIO LISTO")
    print(f"  → {out_csv}")
    print(f"  → {out_manifest}")
    print("=" * 75)

    return 0


if __name__ == "__main__":
    sys.exit(main())