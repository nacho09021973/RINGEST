#!/usr/bin/env python3
"""
02c_prepare_community_ringdown_cohort.py

Prepara una cohorte minima y trazable de eventos reales para analisis de
ringdown con herramientas comunitarias externas (por ejemplo ringdown o
pyRingGW), sin acoplar el pipeline a ninguna API externa concreta.

Entrada contractual:
  - runs/qnm_dataset_literature/qnm_dataset.csv
  - data/gwosc_events/<EVENT>/

Salida:
  - <out-dir>/community_ringdown_cohort.csv
  - <out-dir>/community_ringdown_cohort.json

Politica:
  - Solo emite eventos presentes en el dataset de literatura.
  - Requiere raw/ local para poder relanzar analisis comunitario.
  - Requiere boundary_h5 local para conservar el puente downstream existente.
  - Si existe un ringdown local previo, lo adjunta como metadato trazable
    (dir preferido, poles_joint.json, t0_rel), pero no lo toma como verdad.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional


OUTPUT_COLUMNS = [
    "event",
    "ifo",
    "pole_source",
    "mode_rank",
    "freq_hz",
    "damping_hz",
    "tau_ms",
    "M_final_Msun",
    "chi_final",
    "omega_re",
    "omega_im",
    "omega_re_norm",
    "omega_im_norm",
    "sigma_freq_hz",
    "sigma_damping_hz",
    "sigma_M_final_Msun",
    "sigma_chi_final",
    "raw_dir",
    "boundary_h5",
    "preferred_ringdown_dir",
    "preferred_poles_joint_json",
    "existing_t0_rel",
]


def parse_args():
    ap = argparse.ArgumentParser(
        description="Construye una cohorte candidata para ringdown comunitario desde literatura + artefactos GWOSC locales."
    )
    ap.add_argument(
        "--dataset-csv",
        type=Path,
        default=Path("runs/qnm_dataset_literature/qnm_dataset.csv"),
        help="CSV canonico de literatura con columnas tipo qnm_dataset.csv",
    )
    ap.add_argument(
        "--gwosc-root",
        type=Path,
        default=Path("data/gwosc_events"),
        help="Raiz local de eventos GWOSC",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path("runs/community_ringdown_cohort"),
        help="Directorio de salida",
    )
    return ap.parse_args()


def _read_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _first_existing(paths: List[Path]) -> Optional[Path]:
    for path in paths:
        if path.exists():
            return path
    return None


def _load_t0_rel(poles_json: Optional[Path]) -> Optional[float]:
    if poles_json is None:
        return None
    try:
        payload = json.loads(poles_json.read_text(encoding="utf-8"))
    except Exception:
        return None
    value = payload.get("t0_rel")
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_row(src: Dict[str, str], gwosc_root: Path) -> Optional[Dict[str, object]]:
    event = str(src.get("event", "")).strip()
    if not event:
        return None

    event_dir = gwosc_root / event
    raw_dir = event_dir / "raw"
    boundary_h5 = event_dir / "boundary" / "data_boundary" / f"{event}_boundary.h5"

    if not raw_dir.exists() or not boundary_h5.exists():
        return None

    preferred_ringdown_dir = _first_existing(
        [
            event_dir / "boundary" / "ringdown_calibrated_v1",
            event_dir / "boundary" / "ringdown",
        ]
    )
    preferred_poles_joint_json = None
    if preferred_ringdown_dir is not None:
        candidate = preferred_ringdown_dir / "poles_joint.json"
        if candidate.exists():
            preferred_poles_joint_json = candidate

    row: Dict[str, object] = {k: src.get(k, "") for k in OUTPUT_COLUMNS if k in src}
    row["raw_dir"] = str(raw_dir.resolve())
    row["boundary_h5"] = str(boundary_h5.resolve())
    row["preferred_ringdown_dir"] = (
        str(preferred_ringdown_dir.resolve()) if preferred_ringdown_dir is not None else ""
    )
    row["preferred_poles_joint_json"] = (
        str(preferred_poles_joint_json.resolve()) if preferred_poles_joint_json is not None else ""
    )
    t0_rel = _load_t0_rel(preferred_poles_joint_json)
    row["existing_t0_rel"] = t0_rel if t0_rel is not None else ""
    return row


def main() -> int:
    args = parse_args()
    dataset_csv = args.dataset_csv.resolve()
    gwosc_root = args.gwosc_root.resolve()
    out_dir = args.out_dir.resolve()

    rows_in = _read_rows(dataset_csv)
    rows_out = []
    for src in rows_in:
        row = _build_row(src, gwosc_root)
        if row is not None:
            rows_out.append(row)

    out_dir.mkdir(parents=True, exist_ok=True)
    csv_out = out_dir / "community_ringdown_cohort.csv"
    json_out = out_dir / "community_ringdown_cohort.json"

    with csv_out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row in rows_out:
            writer.writerow({k: row.get(k, "") for k in OUTPUT_COLUMNS})

    summary = {
        "script": "02c_prepare_community_ringdown_cohort.py",
        "dataset_csv": str(dataset_csv),
        "gwosc_root": str(gwosc_root),
        "n_input_rows": len(rows_in),
        "n_selected_rows": len(rows_out),
        "events": [str(row["event"]) for row in rows_out],
        "csv": str(csv_out),
    }
    json_out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Cohorte preparada: {len(rows_out)} eventos")
    print(f"CSV:  {csv_out}")
    print(f"JSON: {json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
