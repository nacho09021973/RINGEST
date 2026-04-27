#!/usr/bin/env python3
"""
02d_parse_ringdown_netcdf.py

Convierte resultados NetCDF reales de `ringdown` a una tabla intermedia,
homogenea y trazable para el repo, sin acoplarse a la API Python de
`ringdown` ni inventar columnas no verificadas.

Hechos verificados en la instalacion local de `ringdown`:
  - `ringdown_fit` escribe por defecto `ringdown_fit.nc`
  - `ringdown.result.Result.from_netcdf(...)` carga un `InferenceData`
    de ArviZ
  - el grupo `posterior` puede contener parametros como `f`, `g`, `m`, `chi`
  - `f` se etiqueta en Hz y `g` como tasa de damping en Hz
  - `t0` se recupera desde la configuracion embebida (`attrs["config"]`)

Contrato de salida:
  - CSV:  <out-dir>/ringdown_intermediate.csv
  - JSON: <out-dir>/ringdown_intermediate.json
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import xarray as xr


OUTPUT_COLUMNS = [
    "event",
    "fit_status",
    "source_dir",
    "source_file",
    "available_groups",
    "available_posterior_vars",
    "t0",
    "f_ringdown_hz",
    "f_ringdown_hz_q05",
    "f_ringdown_hz_q95",
    "damping_hz",
    "damping_hz_q05",
    "damping_hz_q95",
    "tau_ms",
    "tau_ms_q05",
    "tau_ms_q95",
    "M_final_Msun",
    "M_final_Msun_q05",
    "M_final_Msun_q95",
    "chi_final",
    "chi_final_q05",
    "chi_final_q95",
    "parser_notes",
]

STANDARD_GROUPS = [
    "posterior",
    "sample_stats",
    "observed_data",
    "constant_data",
    "log_likelihood",
    "prior",
    "posterior_predictive",
]


def parse_args():
    ap = argparse.ArgumentParser(
        description="Resume resultados NetCDF de ringdown en una tabla intermedia minima."
    )
    ap.add_argument(
        "--input-path",
        type=Path,
        required=True,
        help="Fichero .nc o directorio que contenga resultados NetCDF de ringdown",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        required=True,
        help="Directorio de salida para CSV/JSON intermedios",
    )
    return ap.parse_args()


def _find_netcdf_files(input_path: Path) -> List[Path]:
    if input_path.is_file():
        return [input_path] if input_path.suffix.lower() == ".nc" else []
    return sorted(p for p in input_path.rglob("*.nc") if p.is_file())


def _safe_open_root(path: Path) -> Tuple[Optional[xr.Dataset], List[str]]:
    notes: List[str] = []
    try:
        return xr.open_dataset(path), notes
    except Exception as exc:
        notes.append(f"root_open_failed:{type(exc).__name__}")
        return None, notes


def _safe_open_group(path: Path, group: str) -> Optional[xr.Dataset]:
    try:
        return xr.open_dataset(path, group=group)
    except Exception:
        return None


def _parse_config_dict(root_ds: Optional[xr.Dataset]) -> Tuple[Dict[str, Any], List[str]]:
    notes: List[str] = []
    if root_ds is None:
        notes.append("config_unavailable_root_missing")
        return {}, notes
    raw = root_ds.attrs.get("config")
    if raw is None:
        notes.append("config_attr_missing")
        return {}, notes
    try:
        parsed = json.loads(raw)
    except Exception as exc:
        notes.append(f"config_json_parse_failed:{type(exc).__name__}")
        return {}, notes
    if not isinstance(parsed, dict):
        notes.append("config_not_dict")
        return {}, notes
    return parsed, notes


def _coerce_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _cell(value: Optional[float]) -> Any:
    return "" if value is None else value


def _summarize_var(ds: xr.Dataset, var_name: str) -> Tuple[Dict[str, Optional[float]], List[str]]:
    notes: List[str] = []
    if var_name not in ds.data_vars:
        notes.append(f"{var_name}_missing")
        return {"median": None, "q05": None, "q95": None}, notes

    da = ds[var_name]
    if "mode" in da.dims and int(da.sizes.get("mode", 0)) > 1:
        notes.append(f"{var_name}_multi_mode_skipped")
        return {"median": None, "q05": None, "q95": None}, notes

    try:
        values = np.asarray(da.values, dtype=float).reshape(-1)
    except Exception as exc:
        notes.append(f"{var_name}_coerce_failed:{type(exc).__name__}")
        return {"median": None, "q05": None, "q95": None}, notes

    values = values[np.isfinite(values)]
    if values.size == 0:
        notes.append(f"{var_name}_no_finite_values")
        return {"median": None, "q05": None, "q95": None}, notes

    stats = {
        "median": float(np.quantile(values, 0.50)),
        "q05": float(np.quantile(values, 0.05)),
        "q95": float(np.quantile(values, 0.95)),
    }
    return stats, notes


def _derive_event(path: Path) -> str:
    stem = path.stem
    for suffix in ("_ringdown_fit", ".ringdown_fit", "_fit", ".fit"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    return stem


def _parse_one_file(path: Path) -> Dict[str, Any]:
    row: Dict[str, Any] = {key: "" for key in OUTPUT_COLUMNS}
    notes: List[str] = ["event_from_filename_stem"]

    row["event"] = _derive_event(path)
    row["source_dir"] = str(path.parent.resolve())
    row["source_file"] = str(path.resolve())

    root_ds, root_notes = _safe_open_root(path)
    notes.extend(root_notes)
    config_dict, config_notes = _parse_config_dict(root_ds)
    notes.extend(config_notes)

    group_names: List[str] = []
    posterior_ds: Optional[xr.Dataset] = None
    for group in STANDARD_GROUPS:
        ds = _safe_open_group(path, group)
        if ds is not None:
            group_names.append(group)
            if group == "posterior":
                posterior_ds = ds
            else:
                ds.close()

    row["available_groups"] = ";".join(group_names)

    target_t0 = _coerce_float(config_dict.get("target", {}).get("t0"))
    if target_t0 is not None:
        row["t0"] = target_t0
        notes.append("t0_from_config_target")

    if posterior_ds is None:
        row["fit_status"] = "missing_posterior"
        row["available_posterior_vars"] = ""
        notes.append("posterior_group_missing")
    else:
        row["fit_status"] = "ok_posterior"
        posterior_vars = sorted(str(v) for v in posterior_ds.data_vars)
        row["available_posterior_vars"] = ";".join(posterior_vars)

        f_stats, f_notes = _summarize_var(posterior_ds, "f")
        g_stats, g_notes = _summarize_var(posterior_ds, "g")
        m_stats, m_notes = _summarize_var(posterior_ds, "m")
        chi_stats, chi_notes = _summarize_var(posterior_ds, "chi")
        notes.extend(f_notes)
        notes.extend(g_notes)
        notes.extend(m_notes)
        notes.extend(chi_notes)

        row["f_ringdown_hz"] = _cell(f_stats["median"])
        row["f_ringdown_hz_q05"] = _cell(f_stats["q05"])
        row["f_ringdown_hz_q95"] = _cell(f_stats["q95"])

        row["damping_hz"] = _cell(g_stats["median"])
        row["damping_hz_q05"] = _cell(g_stats["q05"])
        row["damping_hz_q95"] = _cell(g_stats["q95"])

        if g_stats["median"] and g_stats["median"] > 0:
            row["tau_ms"] = 1000.0 / g_stats["median"]
            row["tau_ms_q05"] = 1000.0 / g_stats["q95"] if g_stats["q95"] else ""
            row["tau_ms_q95"] = 1000.0 / g_stats["q05"] if g_stats["q05"] else ""
            notes.append("tau_ms_derived_as_1000_over_g_hz")

        row["M_final_Msun"] = _cell(m_stats["median"])
        row["M_final_Msun_q05"] = _cell(m_stats["q05"])
        row["M_final_Msun_q95"] = _cell(m_stats["q95"])

        row["chi_final"] = _cell(chi_stats["median"])
        row["chi_final_q05"] = _cell(chi_stats["q05"])
        row["chi_final_q95"] = _cell(chi_stats["q95"])
        posterior_ds.close()

    if root_ds is not None:
        root_ds.close()

    row["parser_notes"] = ";".join(dict.fromkeys(notes))
    return row


def main() -> int:
    args = parse_args()
    input_path = args.input_path.resolve()
    out_dir = args.out_dir.resolve()

    files = _find_netcdf_files(input_path)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = [_parse_one_file(path) for path in files]
    csv_out = out_dir / "ringdown_intermediate.csv"
    json_out = out_dir / "ringdown_intermediate.json"

    with csv_out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in OUTPUT_COLUMNS})

    summary = {
        "script": "02d_parse_ringdown_netcdf.py",
        "input_path": str(input_path),
        "n_files_found": len(files),
        "n_rows_written": len(rows),
        "files": [str(path.resolve()) for path in files],
        "csv": str(csv_out),
    }
    json_out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Resultados NetCDF detectados: {len(files)}")
    print(f"CSV:  {csv_out}")
    print(f"JSON: {json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
