#!/usr/bin/env python3
"""
02_poles_to_dataset.py

Collects QNM poles extracted by 01_extract_ringdown_poles.py across all
events and assembles a flat CSV dataset ready for KAN / PySR analysis.

Chain:
    00_download_gwosc_events.py  →  NPZ per event/IFO
    00_load_ligo_data.py         →  boundary HDF5 (whitened strain)
    01_extract_ringdown_poles.py →  poles_joint.json per event
    THIS SCRIPT                  →  qnm_dataset.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

SCRIPT_VERSION = "02_poles_to_dataset.py v1.6 (gwosc v2 + results/parameters fix)"

# G/c^3 in seconds per solar mass — for dimensionless QNM normalization
G_OVER_C3_PER_MSUN = 4.925491025543576e-6  # s / M_sun


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Parameter tables
# ---------------------------------------------------------------------------

def load_params_csv(path: Path) -> Dict[str, Dict[str, float]]:
    params: Dict[str, Dict[str, float]] = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("event", "").strip()
            if not name:
                continue
            m = float(row.get("M_final_Msun", "nan") or "nan")
            chi = float(row.get("chi_final", "nan") or "nan")
            params[name] = {"M_final_Msun": m, "chi_final": chi}
    return params


def _coerce_float(value: Any) -> float:
    if value is None:
        return float("nan")
    if isinstance(value, (int, float, np.floating)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except (ValueError, TypeError):
            return float("nan")
    if isinstance(value, dict):
        for key in ("best", "value", "median"):
            if key in value:
                out = _coerce_float(value.get(key))
                if not np.isnan(out):
                    return out
    return float("nan")


def _first_float(d: Any, keys: List[str]) -> float:
    if not isinstance(d, dict):
        return float("nan")
    for k in keys:
        out = _coerce_float(d.get(k))
        if not np.isnan(out):
            return out
    return float("nan")


def _first_float_from_parameter_list(items: Any, keys: List[str]) -> float:
    if not isinstance(items, list):
        return float("nan")
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("parameter")
        if name in keys:
            out = _coerce_float(item)
            if not np.isnan(out):
                return out
        nested = item.get("parameters")
        out = _extract_from_parameter_sets(nested, keys)
        if not np.isnan(out):
            return out
    return float("nan")


def _extract_from_parameter_sets(parameters: Any, keys: List[str]) -> float:
    if isinstance(parameters, list):
        return _first_float_from_parameter_list(parameters, keys)
    if not isinstance(parameters, dict):
        return float("nan")
    out = _first_float(parameters, keys)
    if not np.isnan(out):
        return out
    for value in parameters.values():
        if isinstance(value, dict):
            out = _first_float(value, keys)
            if not np.isnan(out):
                return out
            out = _extract_from_parameter_sets(value.get("parameters"), keys)
            if not np.isnan(out):
                return out
        elif isinstance(value, list):
            out = _first_float_from_parameter_list(value, keys)
            if not np.isnan(out):
                return out
    return float("nan")


def _extract_mass_spin_from_event(event_payload: Any) -> Tuple[float, float]:
    """Maneja tanto la API antigua como la nueva v2 (results → parameters)"""
    if not isinstance(event_payload, dict):
        return float("nan"), float("nan")

    mass_keys = ["final_mass_source", "remnant_mass_msun", "M_final", "M_f", "mfinal"]
    spin_keys = ["final_spin", "chi_f", "remnant_spin", "a_final", "chi_final"]

    # === NUEVO: soporte para API v2 parameters_url ===
    if "results" in event_payload:
        results = event_payload.get("results", [])
        if results and isinstance(results, list):
            first = results[0]
            if isinstance(first, dict) and "parameters" in first:
                params_list = first.get("parameters", [])
                m = _first_float_from_parameter_list(params_list, mass_keys)
                chi = _first_float_from_parameter_list(params_list, spin_keys)
                if not np.isnan(m) or not np.isnan(chi):
                    return m, chi
            # fallback
            event_payload = first

    # === Código original (v1 + fallback) ===
    m = _extract_from_parameter_sets(event_payload.get("parameters"), mass_keys)
    chi = _extract_from_parameter_sets(event_payload.get("parameters"), spin_keys)
    if not np.isnan(m) or not np.isnan(chi):
        return m, chi

    events = event_payload.get("events", {})
    if isinstance(events, dict):
        for ev_data in events.values():
            if not isinstance(ev_data, dict):
                continue
            m = _extract_from_parameter_sets(ev_data.get("parameters"), mass_keys)
            chi = _extract_from_parameter_sets(ev_data.get("parameters"), spin_keys)
            if not np.isnan(m) or not np.isnan(chi):
                return m, chi

    return float("nan"), float("nan")


# ---------------------------------------------------------------------------
# fetch_params_gwosc (actualizado)
# ---------------------------------------------------------------------------
def fetch_params_gwosc(event_names: Optional[List[str]] = None) -> Dict[str, Dict[str, float]]:
    try:
        import gwosc
    except ImportError:
        print("[WARN] gwosc package not installed.")
        return {}

    params: Dict[str, Dict[str, float]] = {}
    event_list = sorted(set(event_names or []))

    if not event_list:
        return params

    # API v2 (2026)
    try:
        from gwosc.api.v2 import fetch_event_version, fetch_json
        fetch_event = fetch_event_version
        fetch_json_func = fetch_json
        backend = "gwosc.api.v2 (results/parameters)"
    except ImportError:
        print("[WARN] No se encontró API v2. Actualiza gwosc: pip install --upgrade gwosc")
        return {}

    print(f"  GWOSC fetch backend: {backend}")

    for ev_name in event_list:
        try:
            event_payload = fetch_event(ev_name)
        except Exception as e:
            print(f"[WARN] GWOSC lookup failed for {ev_name}: {e}")
            continue

        m, chi = float("nan"), float("nan")

        parameters_url = None
        if isinstance(event_payload, dict):
            parameters_url = event_payload.get("parameters_url")

        if parameters_url:
            try:
                param_payload = fetch_json_func(parameters_url)
                m, chi = _extract_mass_spin_from_event(param_payload)
            except Exception as e:
                print(f"[WARN] Failed to fetch parameters_url for {ev_name}: {e}")
                m, chi = _extract_mass_spin_from_event(event_payload)
        else:
            m, chi = _extract_mass_spin_from_event(event_payload)

        if np.isnan(m) and np.isnan(chi):
            print(f"[WARN] GWOSC event {ev_name} has no final mass/spin parameters")
            continue

        params[ev_name] = {"M_final_Msun": m, "chi_final": chi}
        print(f"    ✓ {ev_name}: M={m:.1f} Msun, χ={chi:.2f}")

    return params


# ---------------------------------------------------------------------------
# El resto del script (find_poles_files, parse_poles_file, etc.) sin cambios
# ---------------------------------------------------------------------------

def find_poles_files(runs_dir: Path) -> List[Tuple[str, Path]]:
    found: List[Tuple[str, Path]] = []
    for event_dir in sorted(runs_dir.iterdir()):
        if not event_dir.is_dir():
            continue
        candidates = [event_dir / "ringdown", event_dir / "boundary" / "ringdown"]
        for ringdown_dir in candidates:
            if not ringdown_dir.exists():
                continue
            joint = ringdown_dir / "poles_joint.json"
            h1 = ringdown_dir / "poles_H1.json"
            if joint.exists():
                found.append((event_dir.name, joint))
                break
            if h1.exists():
                found.append((event_dir.name, h1))
                break
    return found


def parse_poles_file(
    event_name: str,
    path: Path,
    max_modes: int,
    max_rms: Optional[float],
) -> List[Dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    ifo = payload.get("ifo", "UNKNOWN")
    relative_rms = float(payload.get("fit", {}).get("relative_rms", float("nan")))

    if max_rms is not None and not np.isnan(relative_rms) and relative_rms > max_rms:
        return []

    poles = payload.get("poles", [])
    rows: List[Dict[str, Any]] = []
    for rank, pole in enumerate(poles):
        if max_modes > 0 and rank >= max_modes:
            break

        omega_re = float(pole["omega_qnm"][0])
        omega_im = float(pole["omega_qnm"][1])

        freq_hz = float(pole.get("freq_hz", omega_re / (2.0 * np.pi)))
        damping_hz = float(pole.get("damping_1_over_s", -omega_im / (2.0 * np.pi)))
        tau_ms = 1000.0 / damping_hz if damping_hz > 1e-10 else float("nan")

        rows.append({
            "event": event_name,
            "ifo": ifo,
            "mode_rank": rank,
            "freq_hz": freq_hz,
            "damping_hz": damping_hz,
            "tau_ms": tau_ms,
            "omega_re": omega_re,
            "omega_im": omega_im,
            "amp_abs": float(pole.get("amp_abs", float("nan"))),
            "relative_rms": relative_rms,
        })
    return rows


def build_dataset(
    runs_dir: Path,
    params: Dict[str, Dict[str, float]],
    max_modes: int,
    max_rms: Optional[float],
) -> List[Dict[str, Any]]:
    poles_files = find_poles_files(runs_dir)
    if not poles_files:
        raise FileNotFoundError(f"No poles files found under {runs_dir}.")

    print(f"  Found {len(poles_files)} events with poles files")

    rows: List[Dict[str, Any]] = []
    n_skipped = 0

    for event_name, poles_path in poles_files:
        event_rows = parse_poles_file(event_name, poles_path, max_modes, max_rms)
        if not event_rows:
            n_skipped += 1
            continue

        ev_params = params.get(event_name, {})
        m_final = ev_params.get("M_final_Msun", float("nan"))
        chi_final = ev_params.get("chi_final", float("nan"))

        for row in event_rows:
            row["M_final_Msun"] = m_final
            row["chi_final"] = chi_final
            if not np.isnan(m_final) and m_final > 0:
                scale = m_final * G_OVER_C3_PER_MSUN
                row["omega_re_norm"] = row["omega_re"] * scale
                row["omega_im_norm"] = row["omega_im"] * scale
            else:
                row["omega_re_norm"] = float("nan")
                row["omega_im_norm"] = float("nan")

        rows.extend(event_rows)
        print(f"    {event_name}: {len(event_rows)} modes  (rms={event_rows[0]['relative_rms']:.3f})")

    if n_skipped:
        print(f"  Skipped {n_skipped} events (rms > {max_rms or 'n/a'})")

    return rows


COLUMNS = [
    "event", "ifo", "mode_rank",
    "freq_hz", "damping_hz", "tau_ms",
    "omega_re", "omega_im",
    "amp_abs", "relative_rms",
    "M_final_Msun", "chi_final",
    "omega_re_norm", "omega_im_norm",
]


def write_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, float("nan")) for col in COLUMNS})


def write_manifest(rows: List[Dict[str, Any]], path: Path, runs_dir: Path, args: argparse.Namespace) -> None:
    events = sorted({r["event"] for r in rows})
    n_with_params = sum(1 for e in events if not np.isnan(next((r["M_final_Msun"] for r in rows if r["event"] == e), float("nan"))))

    manifest = {
        "created_at": utc_now(),
        "script": SCRIPT_VERSION,
        "runs_dir": str(runs_dir),
        "params_csv": str(args.params_csv) if args.params_csv else None,
        "fetch_params": args.fetch_params,
        "max_modes": args.max_modes,
        "max_rms": args.max_rms,
        "n_events": len(events),
        "n_events_with_mass_spin": n_with_params,
        "n_rows": len(rows),
        "n_modes_per_event": {e: sum(1 for r in rows if r["event"] == e) for e in events},
        "columns": COLUMNS,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description="Build QNM dataset CSV from ringdown poles.")
    ap.add_argument("--runs-dir", default="runs/gwosc_all", help="Root directory with event subdirs")
    ap.add_argument("--out-dir", default="runs/qnm_dataset", help="Output directory")
    ap.add_argument("--params-csv", default=None, help="Optional CSV with columns: event,M_final_Msun,chi_final")
    ap.add_argument("--fetch-params", action="store_true", help="Fetch from GWOSC (requires gwosc)")
    ap.add_argument("--max-modes", type=int, default=4, help="Keep at most N modes per event (0 = all)")
    ap.add_argument("--max-rms", type=float, default=None, help="Skip events with relative_rms > this")
    args = ap.parse_args()

    runs_dir = Path(args.runs_dir).resolve()
    out_dir = Path(args.out_dir).resolve()

    if not runs_dir.exists():
        print(f"[ERROR] --runs-dir does not exist: {runs_dir}")
        return 1

    print("=" * 60)
    print(f"QNM DATASET BUILDER  —  {SCRIPT_VERSION}")
    print(f"runs-dir : {runs_dir}")
    print(f"out-dir  : {out_dir}")
    print(f"max-modes: {args.max_modes or 'all'}")
    if args.max_rms:
        print(f"max-rms  : {args.max_rms}")
    print("=" * 60)

    params: Dict[str, Dict[str, float]] = {}
    if args.params_csv:
        p = Path(args.params_csv)
        if not p.exists():
            print(f"[ERROR] --params-csv not found: {p}")
            return 1
        params = load_params_csv(p)
        print(f"\nLoaded parameters for {len(params)} events from {p.name}")
    elif args.fetch_params:
        print("\nFetching event parameters from GWOSC catalog...")
        event_names = [event_name for event_name, _ in find_poles_files(runs_dir)]
        params = fetch_params_gwosc(event_names)
        print(f"Fetched parameters for {len(params)} events")

    if not params:
        print("\n[NOTE] No event parameters loaded → omega_*_norm will be NaN.")

    print("\nScanning for poles files...")
    rows = build_dataset(runs_dir, params, args.max_modes, args.max_rms)

    if not rows:
        print("[ERROR] No rows produced.")
        return 1

    csv_path = out_dir / "qnm_dataset.csv"
    manifest_path = out_dir / "qnm_dataset_manifest.json"

    write_csv(rows, csv_path)
    write_manifest(rows, manifest_path, runs_dir, args)

    events = sorted({r["event"] for r in rows})
    n_with_norm = sum(1 for r in rows if not np.isnan(r.get("omega_re_norm", float("nan"))))

    print("\n" + "=" * 60)
    print("DONE ✅")
    print(f"  Events    : {len(events)}")
    print(f"  Total rows: {len(rows)}")
    print(f"  With M/χ  : {n_with_norm} rows")
    print(f"  CSV       : {csv_path}")
    print(f"  Manifest  : {manifest_path}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())