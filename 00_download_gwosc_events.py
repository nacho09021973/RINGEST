#!/usr/bin/env python3
"""
00_download_gwosc_events.py  —  CUERDAS-MALDACENA  (v1.0)

Download strain data for all confident LIGO/Virgo events from GWOSC and
convert them to the NPZ format expected by 00_load_ligo_data.py.

Sources:
  - GWTC-1-confident   (11 events, O1/O2)
  - GWTC-2.1-confident (54 events, O3a)
  - GWTC-3-confident   (35 events, O3b)

For each event the script:
  1. Fetches the 32-second / 4096 Hz event-window HDF5 file from GWOSC for
     each available IFO (H1, L1, V1).
  2. Reads strain + GPS metadata from the HDF5.
  3. Saves a NPZ file at:
       <out-dir>/<event_name>/raw/<event_name>_<IFO>_4096Hz_32s.npz
     with keys matching the schema expected by 00_load_ligo_data.py:
       t_gps, strain, fs, ifo, event, gps, start, end, source_url
  4. Keeps the raw HDF5 alongside the NPZ for reproducibility.

Skips events/IFOs already downloaded unless --force is passed.

USAGE
-----
  python3 malda/00_download_gwosc_events.py --out-dir runs/gwosc_all

  # Dry-run (shows what would be downloaded):
      --dry-run

  # Restrict to a specific catalog:
      --catalogs GWTC-1-confident

  # Limit events (for testing):
      --max-events 5

  # Re-download even if NPZ exists:
      --force

REQUIREMENTS
------------
  pip install gwosc requests numpy h5py
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import h5py
import numpy as np
import requests

try:
    from gwosc.datasets import find_datasets, event_gps
    from gwosc.locate import get_event_urls
    HAS_GWOSC = True
except ImportError:
    HAS_GWOSC = False

SCRIPT_VERSION = "00_download_gwosc_events.py v1.0 (2026-04-08)"

# Catalogs to pull from (in priority order — later catalogs are more refined)
DEFAULT_CATALOGS = [
    "GWTC-1-confident",
    "GWTC-2.1-confident",
    "GWTC-3-confident",
]

# Preferred IFOs, in order
IFO_ORDER = ["H1", "L1", "V1"]

# IFO prefix in filename
IFO_PREFIX = {"H1": "H-H1", "L1": "L-L1", "V1": "V-V1"}

DOWNLOAD_TIMEOUT_S = 120
RETRY_DELAYS = [5, 15, 30]  # seconds between retries


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── GWOSC HDF5 reader ─────────────────────────────────────────────────────────

def read_gwosc_hdf5(
    hdf5_path: Path,
    event_gps: Optional[float] = None,
    window_duration: float = 32.0,
) -> Dict[str, Any]:
    """
    Read a GWOSC HDF5 file (event-window or full observation block) and return
    a dict with: strain, t_gps, fs, gps_start, ifo, duration.

    If the file contains more than 2×window_duration seconds of data (i.e. it
    is a full observation block rather than an event-window file), a
    window_duration-second segment centred on event_gps is extracted instead.
    """
    with h5py.File(hdf5_path, "r") as f:
        strain_ds = f["strain/Strain"]
        strain_full = strain_ds[:].astype(np.float64)
        xstart   = float(strain_ds.attrs["Xstart"])
        xspacing = float(strain_ds.attrs["Xspacing"])   # 1/fs
        npts     = len(strain_full)

        # IFO from meta
        try:
            det = f["meta/Detector"][()].decode("utf-8", errors="ignore").strip()
        except Exception:
            det = ""
        try:
            obs = f["meta/Observatory"][()].decode("utf-8", errors="ignore").strip()
        except Exception:
            obs = ""
        ifo = _infer_ifo(hdf5_path.name, det, obs)

    fs       = 1.0 / xspacing
    duration = float(npts) * xspacing

    # If this is a full observation block, extract the event window
    if duration > 2.0 * window_duration and event_gps is not None:
        half  = window_duration / 2.0
        t_win_start = event_gps - half
        t_win_end   = event_gps + half
        i0 = max(0, int((t_win_start - xstart) * fs))
        i1 = min(npts, int((t_win_end   - xstart) * fs))
        if i1 - i0 < int(window_duration * fs * 0.9):
            # event is near the edge — take whatever is available
            i0 = max(0, i0)
            i1 = min(npts, i0 + int(window_duration * fs))
        strain = strain_full[i0:i1]
        xstart = xstart + i0 * xspacing
    else:
        strain = strain_full

    t_gps = xstart + np.arange(len(strain), dtype=np.float64) * xspacing

    return {
        "strain":    strain,
        "t_gps":     t_gps,
        "fs":        fs,
        "gps_start": xstart,
        "duration":  float(len(strain)) * xspacing,
        "ifo":       ifo,
        "full_duration": duration,
    }


def _infer_ifo(filename: str, det: str, obs: str) -> str:
    """Infer IFO string from filename and metadata."""
    name = filename.upper()
    if name.startswith("H-H1") or "H1" in det.upper():
        return "H1"
    if name.startswith("L-L1") or "L1" in det.upper():
        return "L1"
    if name.startswith("V-V1") or "V1" in det.upper() or "VIRGO" in det.upper():
        return "V1"
    # Fallback: first two chars of Observatory
    if obs:
        return obs[:2].upper()
    return "XX"


# ── Downloader ────────────────────────────────────────────────────────────────

def download_file(url: str, dest: Path, timeout: int = DOWNLOAD_TIMEOUT_S,
                  retries: List[int] = RETRY_DELAYS) -> bool:
    """Download url → dest. Returns True on success."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    for attempt, delay in enumerate([0] + retries):
        if delay > 0:
            print(f"      Retry in {delay}s (attempt {attempt+1})...")
            time.sleep(delay)
        try:
            r = requests.get(url, timeout=timeout, stream=True)
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)
            return True
        except Exception as e:
            print(f"      [WARN] Download failed: {e}")
    return False


# ── Event catalogue ────────────────────────────────────────────────────────────

def collect_events(catalogs: List[str]) -> List[Dict[str, Any]]:
    """
    Return a deduplicated list of events across catalogs.
    Each entry: {event_name, catalog, version, gps, dataset_name}
    When an event appears in multiple catalogs, keep the most recent version
    (highest version number).
    """
    seen: Dict[str, Dict] = {}  # event_name → entry

    for catalog in catalogs:
        datasets = find_datasets(type="event", catalog=catalog)
        for ds in datasets:
            # ds looks like "GW150914-v3"
            parts = ds.rsplit("-v", 1)
            if len(parts) == 2:
                ev_name = parts[0]
                version = int(parts[1])
            else:
                ev_name = ds
                version = 1

            try:
                gps = event_gps(ds)
            except Exception:
                gps = float("nan")

            existing = seen.get(ev_name)
            if existing is None or version > existing["version"]:
                seen[ev_name] = {
                    "event_name":   ev_name,
                    "dataset_name": ds,
                    "catalog":      catalog,
                    "version":      version,
                    "gps":          gps,
                }

    # Sort by GPS time
    events = sorted(seen.values(), key=lambda e: e["gps"])
    return events


# ── Per-event downloader ───────────────────────────────────────────────────────

def process_event(
    ev: Dict[str, Any],
    out_dir: Path,
    dry_run: bool,
    force: bool,
    sample_rate: int,
    duration: int,
) -> Dict[str, Any]:
    """
    Download and convert one event. Returns a status dict.
    """
    ev_name  = ev["event_name"]
    ds_name  = ev["dataset_name"]
    gps_peak = ev["gps"]

    ev_dir  = out_dir / ev_name
    raw_dir = ev_dir / "raw"

    print(f"\n  [{ev_name}]  GPS={gps_peak:.1f}  dataset={ds_name}")

    # Fetch URLs for all IFOs
    try:
        urls = get_event_urls(ds_name, duration=duration, sample_rate=sample_rate)
    except Exception as e:
        print(f"    [ERROR] Could not fetch URLs: {e}")
        return {"event": ev_name, "status": "url_error", "error": str(e)}

    if not urls:
        print(f"    [WARN] No URLs found")
        return {"event": ev_name, "status": "no_urls"}

    results_per_ifo = []

    for url in urls:
        fname = Path(url).name  # e.g. H-H1_GWOSC_4KHZ_R1-1126259447-32.hdf5
        hdf5_dest = raw_dir / fname

        # Determine IFO from URL/filename
        ifo = _infer_ifo(fname, "", "")

        npz_name = f"{ev_name}_{ifo}_{sample_rate}Hz_{duration}s.npz"
        npz_dest = raw_dir / npz_name

        if npz_dest.exists() and not force:
            print(f"    [{ifo}] Already exists: {npz_name} — skip")
            results_per_ifo.append({"ifo": ifo, "status": "skipped", "npz": str(npz_dest)})
            continue

        if dry_run:
            print(f"    [{ifo}] DRY-RUN: would download {url}")
            results_per_ifo.append({"ifo": ifo, "status": "dry_run", "url": url})
            continue

        # Download HDF5
        print(f"    [{ifo}] Downloading {url}")
        ok = download_file(url, hdf5_dest)
        if not ok:
            print(f"    [{ifo}] [ERROR] Download failed after retries")
            results_per_ifo.append({"ifo": ifo, "status": "download_error", "url": url})
            continue

        # Read HDF5 (extracts window if full block)
        try:
            data = read_gwosc_hdf5(hdf5_dest,
                                   event_gps=gps_peak,
                                   window_duration=float(duration))
        except Exception as e:
            print(f"    [{ifo}] [ERROR] Could not read HDF5: {e}")
            results_per_ifo.append({"ifo": ifo, "status": "read_error", "error": str(e)})
            continue

        full_dur = data.get("full_duration", data["duration"])
        if full_dur > 2 * duration:
            print(f"      (Extracted {data['duration']:.1f}s window from {full_dur:.0f}s block)")

        # Save NPZ
        np.savez(
            npz_dest,
            t_gps     = data["t_gps"],
            strain    = data["strain"],
            fs        = np.float64(data["fs"]),
            ifo       = np.str_(data["ifo"]),
            event     = np.str_(ev_name),
            gps       = np.float64(gps_peak),
            start     = np.float64(data["gps_start"]),
            end       = np.float64(data["gps_start"] + data["duration"]),
            source_url= np.str_(url),
        )
        print(f"    [{ifo}] Saved: {npz_dest.relative_to(out_dir)}")
        results_per_ifo.append({"ifo": ifo, "status": "ok",
                                 "npz": str(npz_dest.relative_to(out_dir)),
                                 "fs": data["fs"], "n_samples": len(data["strain"])})

    return {
        "event":    ev_name,
        "dataset":  ds_name,
        "gps":      gps_peak,
        "catalog":  ev["catalog"],
        "ifos":     results_per_ifo,
        "status":   "ok" if results_per_ifo else "no_ifos",
    }


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    if not HAS_GWOSC:
        print("[ERROR] gwosc not installed. Run: pip install gwosc")
        return 1

    ap = argparse.ArgumentParser(
        description="Download all confident LIGO/Virgo events from GWOSC."
    )
    ap.add_argument("--out-dir",    default="runs/gwosc_all",
                    help="Root output directory (default: runs/gwosc_all)")
    ap.add_argument("--catalogs",   nargs="+", default=DEFAULT_CATALOGS,
                    help="GWOSC catalogs to fetch (default: all three GWTC)")
    ap.add_argument("--sample-rate", type=int, default=4096,
                    help="Sample rate in Hz (default: 4096)")
    ap.add_argument("--duration",    type=int, default=32,
                    help="Window duration in seconds around merger (default: 32)")
    ap.add_argument("--max-events",  type=int, default=0,
                    help="Download at most N events (0 = all)")
    ap.add_argument("--dry-run",     action="store_true",
                    help="Print what would be downloaded without doing it")
    ap.add_argument("--force",       action="store_true",
                    help="Re-download even if NPZ already exists")
    ap.add_argument("--event",       nargs="+", default=[],
                    help="Download only these events by name (e.g. GW150914)")
    args = ap.parse_args()

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("GWOSC EVENT BULK DOWNLOADER  —  CUERDAS-MALDACENA")
    print(f"Script:   {SCRIPT_VERSION}")
    print(f"Catalogs: {args.catalogs}")
    print(f"Out dir:  {out_dir}")
    print(f"Fs={args.sample_rate} Hz  dur={args.duration}s")
    if args.dry_run:
        print("MODE: DRY-RUN (nothing will be written)")
    print("=" * 70)

    # Collect events
    print("\nQuerying GWOSC event catalogue...")
    events = collect_events(args.catalogs)
    print(f"  Found {len(events)} unique confident events across {len(args.catalogs)} catalogs")

    # Optional filter by name
    if args.event:
        filter_set = set(args.event)
        events = [e for e in events if e["event_name"] in filter_set]
        print(f"  Filtered to {len(events)} requested events")

    # Optional limit
    if args.max_events > 0:
        events = events[:args.max_events]
        print(f"  Limited to first {len(events)} events (--max-events)")

    # Print catalogue
    print(f"\n{'#':>3}  {'Event':20s}  {'GPS':14s}  {'Catalog':25s}")
    print("-" * 70)
    for i, ev in enumerate(events):
        print(f"  {i+1:>2}.  {ev['event_name']:20s}  {ev['gps']:14.1f}  {ev['catalog']}")

    # Download loop
    print()
    all_results = []
    n_ok = n_skip = n_err = 0

    for ev in events:
        res = process_event(
            ev, out_dir,
            dry_run     = args.dry_run,
            force       = args.force,
            sample_rate = args.sample_rate,
            duration    = args.duration,
        )
        all_results.append(res)

        # Count outcomes
        for ifo_r in res.get("ifos", []):
            s = ifo_r.get("status", "")
            if s == "ok":
                n_ok += 1
            elif s == "skipped":
                n_skip += 1
            elif s == "dry_run":
                pass
            else:
                n_err += 1

    # Write manifest
    manifest = {
        "created_at":   utc_now(),
        "script":       SCRIPT_VERSION,
        "catalogs":     args.catalogs,
        "sample_rate":  args.sample_rate,
        "duration":     args.duration,
        "n_events":     len(events),
        "n_ifo_files_downloaded": n_ok,
        "n_ifo_files_skipped":    n_skip,
        "n_errors":               n_err,
        "events":                 all_results,
    }
    manifest_path = out_dir / "download_manifest.json"
    if not args.dry_run:
        manifest_path.write_text(json.dumps(manifest, indent=2))

    print("\n" + "=" * 70)
    print("[DONE] GWOSC download summary")
    print(f"  Events processed : {len(events)}")
    print(f"  IFO files new    : {n_ok}")
    print(f"  IFO files skipped: {n_skip}")
    print(f"  Errors           : {n_err}")
    if not args.dry_run:
        print(f"  Manifest         : {manifest_path}")
    print("=" * 70)
    print()
    print("Next step — run 00_load_ligo_data.py for each event:")
    print("  for npz in runs/gwosc_all/*/raw/*_H1_*.npz; do")
    print("    ev=$(basename $(dirname $(dirname $npz)))")
    print("    python3 malda/00_load_ligo_data.py \\")
    print("      --npz $npz \\")
    print("      --out-dir runs/gwosc_all/${ev}/boundary \\")
    print("      --whiten")
    print("  done")

    return 0 if n_err == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
