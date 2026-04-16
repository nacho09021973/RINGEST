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

Input layout expected (default):
    <runs-dir>/
        <EVENT_NAME>/
            ringdown/
                poles_joint.json   ← preferred (H1+L1)
                poles_H1.json      ← fallback if no joint

Output:
    <out-dir>/qnm_dataset.csv
    <out-dir>/qnm_dataset_manifest.json

CSV columns:
    event          – GW event name (e.g. GW150914)
    ifo            – interferometer(s): H1, L1, H1+L1
    mode_rank      – 0 = dominant mode (highest amplitude)
    freq_hz        – Re(omega)/(2*pi)  [Hz]
    damping_hz     – -Im(omega)/(2*pi) [Hz, positive for decaying modes]
    tau_ms         – damping time = 1000/damping_hz  [ms]
    omega_re       – Re(omega_qnm)  [rad/s]
    omega_im       – Im(omega_qnm)  [rad/s, negative = decaying]
    amp_abs        – amplitude magnitude from ESPRIT fit
    relative_rms   – ESPRIT fit residual / signal RMS  (quality indicator)
    M_final_Msun   – final BH mass [solar masses]  (NaN if unavailable)
    chi_final      – final BH spin [-1,1]           (NaN if unavailable)
    omega_re_norm  – omega_re * M_final * G/c^3      (dimensionless, NaN if no mass)
    omega_im_norm  – omega_im * M_final * G/c^3      (dimensionless, NaN if no mass)

Usage
-----
    # Basic: scan runs/gwosc_all, write to runs/qnm_dataset/
    python3 02_poles_to_dataset.py --runs-dir runs/gwosc_all

    # With event-parameter table (CSV with columns: event,M_final_Msun,chi_final)
    python3 02_poles_to_dataset.py --runs-dir runs/gwosc_all \
        --params-csv catalog_params.csv

    # Try to fetch event parameters from GWOSC catalog automatically
    python3 02_poles_to_dataset.py --runs-dir runs/gwosc_all --fetch-params

    # Limit to top N modes per event
    python3 02_poles_to_dataset.py --runs-dir runs/gwosc_all --max-modes 3

    # Only include modes with relative_rms < threshold
    python3 02_poles_to_dataset.py --runs-dir runs/gwosc_all --max-rms 0.3
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

SCRIPT_VERSION = "02_poles_to_dataset.py v1.0"

# G/c^3 in seconds per solar mass — for dimensionless QNM normalization
G_OVER_C3_PER_MSUN = 4.925491025543576e-6  # s / M_sun


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Parameter tables
# ---------------------------------------------------------------------------

def load_params_csv(path: Path) -> Dict[str, Dict[str, float]]:
    """
    Load a CSV with columns: event, M_final_Msun, chi_final
    Returns dict: event_name -> {M_final_Msun, chi_final}
    """
    params: Dict[str, Dict[str, float]] = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("event", "").strip()
            if not name:
                continue
            try:
                m = float(row.get("M_final_Msun", "nan"))
            except (ValueError, TypeError):
                m = float("nan")
            try:
                chi = float(row.get("chi_final", "nan"))
            except (ValueError, TypeError):
                chi = float("nan")
            params[name] = {"M_final_Msun": m, "chi_final": chi}
    return params


def fetch_params_gwosc() -> Dict[str, Dict[str, float]]:
    """
    Try to pull M_final and chi_final from the GWOSC catalog API.
    Returns dict: event_name -> {M_final_Msun, chi_final}

    Uses gwosc.catalog if available; otherwise returns empty dict.
    """
    try:
        from gwosc import catalog as gwosc_catalog
    except ImportError:
        print("[WARN] gwosc not installed — cannot fetch parameters automatically.")
        print("       Install with: pip install gwosc")
        print("       Or supply --params-csv with columns: event,M_final_Msun,chi_final")
        return {}

    params: Dict[str, Dict[str, float]] = {}

    catalog_names = ["GWTC-1-confident", "GWTC-2.1-confident", "GWTC-3-confident"]
    for cat_name in catalog_names:
        try:
            cat = gwosc_catalog.Catalog(cat_name)
            for ev_name in cat.events:
                try:
                    ev = cat.event(ev_name)
                    # GWOSC parameter keys vary by catalog; try common names
                    m = _first_float(ev.parameters, [
                        "final_mass_source",
                        "remnant_mass_msun",
                        "M_final",
                    ])
                    chi = _first_float(ev.parameters, [
                        "final_spin",
                        "chi_f",
                        "remnant_spin",
                    ])
                    params[ev_name] = {"M_final_Msun": m, "chi_final": chi}
                except Exception:
                    pass
        except Exception as e:
            print(f"[WARN] Could not load catalog {cat_name}: {e}")

    return params


def _first_float(d: Any, keys: List[str]) -> float:
    if not isinstance(d, dict):
        return float("nan")
    for k in keys:
        v = d.get(k)
        if v is not None:
            try:
                return float(v)
            except (ValueError, TypeError):
                pass
    return float("nan")


# ---------------------------------------------------------------------------
# Poles file discovery and parsing
# ---------------------------------------------------------------------------

def find_poles_files(runs_dir: Path) -> List[Tuple[str, Path]]:
    """
    Scan runs_dir for poles files. Prefer poles_joint.json, fall back to poles_H1.json.
    Returns list of (event_name, poles_path).
    """
    found: List[Tuple[str, Path]] = []
    for event_dir in sorted(runs_dir.iterdir()):
        if not event_dir.is_dir():
            continue
        ringdown_dir = event_dir / "ringdown"
        if not ringdown_dir.exists():
            continue
        joint = ringdown_dir / "poles_joint.json"
        h1 = ringdown_dir / "poles_H1.json"
        if joint.exists():
            found.append((event_dir.name, joint))
        elif h1.exists():
            found.append((event_dir.name, h1))
    return found


def parse_poles_file(
    event_name: str,
    path: Path,
    max_modes: int,
    max_rms: Optional[float],
) -> List[Dict[str, Any]]:
    """
    Parse a poles_joint.json or poles_H1.json produced by 01_extract_ringdown_poles.py.
    Returns list of row dicts, one per mode.
    """
    payload = json.loads(path.read_text(encoding="utf-8"))
    ifo = payload.get("ifo", "UNKNOWN")
    relative_rms = float(payload.get("fit", {}).get("relative_rms", float("nan")))

    # Quality gate
    if max_rms is not None and not np.isnan(relative_rms) and relative_rms > max_rms:
        return []

    poles = payload.get("poles", [])

    rows = []
    for rank, pole in enumerate(poles):
        if max_modes > 0 and rank >= max_modes:
            break

        omega_re = float(pole["omega_qnm"][0])
        omega_im = float(pole["omega_qnm"][1])

        freq_hz = float(pole.get("freq_hz", omega_re / (2.0 * np.pi)))
        damping_hz = float(pole.get("damping_1_over_s", -omega_im / (2.0 * np.pi)))
        tau_ms = 1000.0 / damping_hz if damping_hz > 1e-10 else float("nan")

        rows.append({
            "event":        event_name,
            "ifo":          ifo,
            "mode_rank":    rank,
            "freq_hz":      freq_hz,
            "damping_hz":   damping_hz,
            "tau_ms":       tau_ms,
            "omega_re":     omega_re,
            "omega_im":     omega_im,
            "amp_abs":      float(pole.get("amp_abs", float("nan"))),
            "relative_rms": relative_rms,
        })

    return rows


# ---------------------------------------------------------------------------
# Dataset assembly
# ---------------------------------------------------------------------------

def build_dataset(
    runs_dir: Path,
    params: Dict[str, Dict[str, float]],
    max_modes: int,
    max_rms: Optional[float],
) -> List[Dict[str, Any]]:
    poles_files = find_poles_files(runs_dir)
    if not poles_files:
        raise FileNotFoundError(
            f"No poles files found under {runs_dir}.\n"
            "Run 00_download_gwosc_events.py → 00_load_ligo_data.py → "
            "01_extract_ringdown_poles.py first."
        )

    print(f"  Found {len(poles_files)} events with poles files")

    rows: List[Dict[str, Any]] = []
    n_skipped = 0

    for event_name, poles_path in poles_files:
        event_rows = parse_poles_file(event_name, poles_path, max_modes, max_rms)
        if not event_rows:
            n_skipped += 1
            continue

        # Attach event parameters
        ev_params = params.get(event_name, {})
        m_final = ev_params.get("M_final_Msun", float("nan"))
        chi_final = ev_params.get("chi_final", float("nan"))

        for row in event_rows:
            row["M_final_Msun"] = m_final
            row["chi_final"] = chi_final

            # Dimensionless QNM parameters (Kerr convention: M*omega)
            if not np.isnan(m_final) and m_final > 0:
                scale = m_final * G_OVER_C3_PER_MSUN  # seconds
                row["omega_re_norm"] = row["omega_re"] * scale
                row["omega_im_norm"] = row["omega_im"] * scale
            else:
                row["omega_re_norm"] = float("nan")
                row["omega_im_norm"] = float("nan")

        rows.extend(event_rows)
        print(f"    {event_name}: {len(event_rows)} modes  "
              f"(rms={event_rows[0]['relative_rms']:.3f})")

    if n_skipped:
        print(f"  Skipped {n_skipped} events (rms > {max_rms or 'n/a'} or no modes)")

    return rows


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

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


def write_manifest(
    rows: List[Dict[str, Any]],
    path: Path,
    runs_dir: Path,
    args: argparse.Namespace,
) -> None:
    events = sorted({r["event"] for r in rows})
    n_with_params = sum(
        1 for e in events
        if not np.isnan(next((r["M_final_Msun"] for r in rows if r["event"] == e), float("nan")))
    )
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
        "n_modes_per_event": {
            e: sum(1 for r in rows if r["event"] == e) for e in events
        },
        "columns": COLUMNS,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build QNM dataset CSV from ringdown poles for KAN/PySR analysis."
    )
    ap.add_argument(
        "--runs-dir", default="runs/gwosc_all",
        help="Root directory containing event subdirs with ringdown/ (default: runs/gwosc_all)"
    )
    ap.add_argument(
        "--out-dir", default="runs/qnm_dataset",
        help="Output directory (default: runs/qnm_dataset)"
    )
    ap.add_argument(
        "--params-csv", default=None,
        help="Optional CSV with columns: event,M_final_Msun,chi_final"
    )
    ap.add_argument(
        "--fetch-params", action="store_true",
        help="Fetch M_final,chi_final from GWOSC catalog API (requires gwosc)"
    )
    ap.add_argument(
        "--max-modes", type=int, default=4,
        help="Keep at most N modes per event (0 = all, default: 4)"
    )
    ap.add_argument(
        "--max-rms", type=float, default=None,
        help="Skip events where ESPRIT relative_rms > this threshold (e.g. 0.3)"
    )
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

    # Load event parameters
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
        params = fetch_params_gwosc()
        print(f"Fetched parameters for {len(params)} events")

    if not params:
        print("\n[NOTE] No event parameters (M_final, chi_final) loaded.")
        print("       Dimensionless columns (omega_*_norm) will be NaN.")
        print("       Use --params-csv or --fetch-params to add them.")

    # Build dataset
    print("\nScanning for poles files...")
    rows = build_dataset(runs_dir, params, args.max_modes, args.max_rms)

    if not rows:
        print("[ERROR] No rows produced. Check that poles files exist.")
        return 1

    # Write outputs
    csv_path = out_dir / "qnm_dataset.csv"
    manifest_path = out_dir / "qnm_dataset_manifest.json"

    write_csv(rows, csv_path)
    write_manifest(rows, manifest_path, runs_dir, args)

    # Summary
    events = sorted({r["event"] for r in rows})
    n_with_norm = sum(1 for r in rows if not np.isnan(r.get("omega_re_norm", float("nan"))))
    print("\n" + "=" * 60)
    print("DONE")
    print(f"  Events    : {len(events)}")
    print(f"  Total rows: {len(rows)}  (modes across all events)")
    print(f"  With M/chi: {n_with_norm} rows have dimensionless columns")
    print(f"  CSV       : {csv_path}")
    print(f"  Manifest  : {manifest_path}")
    print("=" * 60)
    print()
    print("Next step — feed qnm_dataset.csv to KAN or PySR:")
    print("  Suggested target variables for PySR:")
    print("    y = freq_hz  or  omega_re_norm")
    print("    X = [M_final_Msun, chi_final, mode_rank]")
    print()
    print("  Suggested target variables for KAN:")
    print("    Input : omega_re_norm, omega_im_norm per event")
    print("    Output: cluster / family label")

    return 0


if __name__ == "__main__":
    sys.exit(main())
