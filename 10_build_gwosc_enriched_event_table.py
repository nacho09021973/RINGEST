#!/usr/bin/env python3
"""
Build a single enriched event-level table for all events materialized under
runs/gwosc_all by combining:

- local ringdown observables and quality flags already produced in the repo
- official GWOSC event metadata / default PE values
- Kerr-derived horizon quantities computed from final mass and final spin

Outputs:
- runs/gwosc_all/gwosc_enriched_event_table.csv
- runs/gwosc_all/gwosc_enriched_event_table_summary.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests


GWOSC_ALLEVENTS_URL = "https://gwosc.org/eventapi/jsonfull/allevents/"

# Physical constants
G_SI = 6.67430e-11
C_SI = 299792458.0
HBAR_SI = 1.054571817e-34
KB_SI = 1.380649e-23
MSUN_KG = 1.988409870698051e30
M_SUN_TIME_S = G_SI * MSUN_KG / (C_SI ** 3)
M_SUN_LENGTH_M = G_SI * MSUN_KG / (C_SI ** 2)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Build enriched GWOSC event table for local runs/gwosc_all")
    ap.add_argument("--runs-dir", default="runs/gwosc_all", help="Local GWOSC runs directory")
    ap.add_argument("--timeout", type=float, default=60.0, help="HTTP timeout in seconds")
    return ap.parse_args()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv_map(path: Path, key: str = "event") -> Dict[str, Dict[str, str]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        out: Dict[str, Dict[str, str]] = {}
        for row in reader:
            event = row.get(key)
            if event:
                out[event] = row
        return out


def find_local_events(runs_dir: Path) -> List[Path]:
    return sorted(
        p for p in runs_dir.iterdir()
        if p.is_dir() and p.name.startswith("GW")
    )


def maybe_float(value: Any) -> Optional[float]:
    if value in (None, "", "null"):
        return None
    try:
        if isinstance(value, str) and value.strip().lower() in {"nan", "none"}:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def maybe_int(value: Any) -> Optional[int]:
    out = maybe_float(value)
    if out is None:
        return None
    return int(out)


def maybe_bool(value: Any) -> Optional[bool]:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        v = value.strip().lower()
        if v == "true":
            return True
        if v == "false":
            return False
    return None


def detectors_from_raw(raw_dir: Path) -> str:
    if not raw_dir.exists():
        return ""
    dets = sorted({p.name.split("_")[-2] for p in raw_dir.glob("*.npz") if "_" in p.name})
    return ",".join(dets)


def first_row_fields(csv_path: Path) -> Dict[str, Optional[float]]:
    if not csv_path.exists():
        return {}
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        row = next(reader, None)
        if row is None:
            return {}
    freq = maybe_float(row.get("freq_hz"))
    gamma = maybe_float(row.get("damping_1_over_s"))
    tau = (1.0 / gamma) if gamma and gamma > 0 else None
    return {
        "freq_hz": freq,
        "damping_1_over_s": gamma,
        "tau_s": tau,
        "n_modes": 1,
    }


def count_rows(csv_path: Path) -> Optional[int]:
    if not csv_path.exists():
        return None
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.reader(fh)
        next(reader, None)
        return sum(1 for _ in reader)


def fetch_gwosc_allevents(timeout: float) -> Dict[str, Any]:
    resp = requests.get(GWOSC_ALLEVENTS_URL, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    if "events" not in data or not isinstance(data["events"], dict):
        raise RuntimeError("Unexpected GWOSC allevents payload: missing events dict")
    return data


def fetch_event_record_from_jsonurl(session: requests.Session, jsonurl: str, timeout: float) -> Dict[str, Any]:
    resp = session.get(jsonurl, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    events = data.get("events", {})
    if not isinstance(events, dict) or not events:
        raise RuntimeError(f"Unexpected GWOSC event payload from {jsonurl}")
    return next(iter(events.values()))


def latest_gwosc_records_by_common_name(events_payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    latest: Dict[str, Dict[str, Any]] = {}
    for record in events_payload["events"].values():
        common_name = record.get("commonName")
        version = maybe_int(record.get("version"))
        if not common_name or version is None:
            continue
        prev = latest.get(common_name)
        prev_version = maybe_int(prev.get("version")) if prev else None
        if prev is None or prev_version is None or version > prev_version:
            latest[common_name] = record
    return latest


def choose_preferred_parameter_block(record: Dict[str, Any]) -> Dict[str, Any]:
    params = record.get("parameters", {})
    if not isinstance(params, dict) or not params:
        return {}

    preferred_pe: Optional[Dict[str, Any]] = None
    first_pe: Optional[Dict[str, Any]] = None
    first_any: Optional[Dict[str, Any]] = None

    for meta in params.values():
        if not isinstance(meta, dict):
            continue
        if first_any is None:
            first_any = meta
        if meta.get("pipeline_type") == "pe":
            if first_pe is None:
                first_pe = meta
            if meta.get("is_preferred") is True:
                preferred_pe = meta
                break

    return preferred_pe or first_pe or first_any or {}


def merge_event_record_with_preferred_parameters(record: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(record)
    preferred = choose_preferred_parameter_block(record)
    for key, value in preferred.items():
        if merged.get(key) in (None, "", "null") and value not in (None, "", "null"):
            merged[key] = value
        elif key in {"final_spin", "mass_ratio", "mass_ratio_source"} and value not in (None, "", "null"):
            merged[key] = value
    return merged


def derive_kerr_quantities(final_mass_msun: Optional[float], final_spin: Optional[float]) -> Dict[str, Optional[float]]:
    out = {
        "kerr_A_H_m2": None,
        "kerr_A_H_km2": None,
        "kerr_M_irr_msun": None,
        "kerr_T_H_K": None,
        "kerr_Omega_H_rad_s": None,
        "kerr_M_times_T_H_geom": None,
        "kerr_M_times_Omega_H_geom": None,
    }
    if final_mass_msun is None or final_spin is None:
        return out
    if final_mass_msun <= 0:
        return out
    a = final_spin
    if abs(a) >= 1:
        return out

    root = math.sqrt(1.0 - a * a)
    rg_m = M_SUN_LENGTH_M * final_mass_msun
    m_geom_s = M_SUN_TIME_S * final_mass_msun

    area_m2 = 8.0 * math.pi * (rg_m ** 2) * (1.0 + root)
    m_irr_msun = final_mass_msun * math.sqrt((1.0 + root) / 2.0)
    omega_h_rad_s = a / (2.0 * m_geom_s * (1.0 + root))
    temp_k = (
        (HBAR_SI * (C_SI ** 3)) / (8.0 * math.pi * G_SI * MSUN_KG * KB_SI * final_mass_msun)
    ) * (root / (1.0 + root))

    out.update({
        "kerr_A_H_m2": area_m2,
        "kerr_A_H_km2": area_m2 / 1.0e6,
        "kerr_M_irr_msun": m_irr_msun,
        "kerr_T_H_K": temp_k,
        "kerr_Omega_H_rad_s": omega_h_rad_s,
        "kerr_M_times_T_H_geom": root / (4.0 * math.pi * (1.0 + root)),
        "kerr_M_times_Omega_H_geom": a / (2.0 * (1.0 + root)),
    })
    return out


def derive_experiment_features(
    final_mass_msun: Optional[float],
    dominant_freq_joint_hz: Optional[float],
    dominant_gamma_joint_1_over_s: Optional[float],
) -> Dict[str, Optional[float]]:
    out = {
        "exp_M_seconds": None,
        "exp_joint_omega_dimless": None,
        "exp_joint_gamma_dimless": None,
        "exp_joint_freq_hz_times_M": None,
    }
    if final_mass_msun is None or final_mass_msun <= 0:
        return out
    m_seconds = M_SUN_TIME_S * final_mass_msun
    out["exp_M_seconds"] = m_seconds
    if dominant_freq_joint_hz is not None:
        out["exp_joint_omega_dimless"] = 2.0 * math.pi * dominant_freq_joint_hz * m_seconds
        out["exp_joint_freq_hz_times_M"] = dominant_freq_joint_hz * m_seconds
    if dominant_gamma_joint_1_over_s is not None:
        out["exp_joint_gamma_dimless"] = dominant_gamma_joint_1_over_s * m_seconds
    return out


def preferred_network_snr(record: Dict[str, Any]) -> Optional[float]:
    return (
        maybe_float(record.get("network_matched_filter_snr"))
        or maybe_float(record.get("network_snr"))
    )


def choose_fields(record: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not record:
        return {}
    m1 = maybe_float(record.get("mass_1_source"))
    m2 = maybe_float(record.get("mass_2_source"))
    mass_ratio = maybe_float(record.get("mass_ratio")) or maybe_float(record.get("mass_ratio_source"))
    if mass_ratio is None and m1 is not None and m2 is not None and m1 > 0 and m2 > 0:
        hi = max(m1, m2)
        lo = min(m1, m2)
        mass_ratio = lo / hi
    return {
        "gwosc_common_name": record.get("commonName"),
        "gwosc_event_version": f"v{record.get('version')}" if record.get("version") is not None else None,
        "gwosc_catalog": record.get("catalog.shortName"),
        "gwosc_gps": maybe_float(record.get("GPS")),
        "gwosc_mass_1_source_msun": m1,
        "gwosc_mass_2_source_msun": m2,
        "gwosc_total_mass_source_msun": maybe_float(record.get("total_mass_source")),
        "gwosc_chirp_mass_source_msun": maybe_float(record.get("chirp_mass_source")),
        "gwosc_mass_ratio": mass_ratio,
        "gwosc_chi_eff": maybe_float(record.get("chi_eff")),
        "gwosc_final_mass_source_msun": maybe_float(record.get("final_mass_source")),
        "gwosc_final_spin": maybe_float(record.get("final_spin")),
        "gwosc_redshift": maybe_float(record.get("redshift")),
        "gwosc_luminosity_distance_mpc": maybe_float(record.get("luminosity_distance")),
        "gwosc_network_snr": preferred_network_snr(record),
        "gwosc_far_yr_inv": maybe_float(record.get("far")),
        "gwosc_jsonurl": record.get("jsonurl"),
    }


def build_row(
    event_dir: Path,
    ringdown_table: Dict[str, Dict[str, str]],
    detector_consistency: Dict[str, Dict[str, str]],
    matched_consistency: Dict[str, Dict[str, str]],
    anchor_dataset: Dict[str, Dict[str, str]],
    pysr_dataset: Dict[str, Dict[str, str]],
    gwosc_latest: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    event = event_dir.name
    boundary_dir = event_dir / "boundary"
    raw_dir = event_dir / "raw"
    rd_dir = boundary_dir / "ringdown"

    boundary_summary = load_json(boundary_dir / "summary.json") if (boundary_dir / "summary.json").exists() else {}
    ringdown_summary = load_json(rd_dir / "summary.json") if (rd_dir / "summary.json").exists() else {}

    base_row: Dict[str, Any] = {
        "event": event,
        "event_dir": str(event_dir),
        "has_boundary_dir": boundary_dir.exists(),
        "has_raw_dir": raw_dir.exists(),
        "has_ringdown_dir": rd_dir.exists(),
        "local_gps": maybe_float(boundary_summary.get("gps")),
        "detectors_available_local": (
            ringdown_table.get(event, {}).get("detectors_available")
            or matched_consistency.get(event, {}).get("detectors_available")
            or anchor_dataset.get(event, {}).get("detectors_available")
            or detector_consistency.get(event, {}).get("detectors_available")
            or detectors_from_raw(raw_dir)
        ),
        "has_poles_H1": (rd_dir / "poles_H1.csv").exists(),
        "has_poles_L1": (rd_dir / "poles_L1.csv").exists(),
        "has_poles_joint": (rd_dir / "poles_joint.csv").exists(),
        "has_poles_V1": (rd_dir / "poles_V1.csv").exists(),
    }

    base_row["n_modes_H1"] = count_rows(rd_dir / "poles_H1.csv")
    base_row["n_modes_L1"] = count_rows(rd_dir / "poles_L1.csv")
    base_row["n_modes_joint"] = count_rows(rd_dir / "poles_joint.csv")

    for prefix, csv_name in (("H1", "poles_H1.csv"), ("L1", "poles_L1.csv"), ("joint", "poles_joint.csv")):
        fields = first_row_fields(rd_dir / csv_name)
        base_row[f"dominant_freq_{prefix}_hz"] = fields.get("freq_hz")
        base_row[f"dominant_gamma_{prefix}_1_over_s"] = fields.get("damping_1_over_s")
        base_row[f"dominant_tau_{prefix}_s"] = fields.get("tau_s")

    fit_quality = ringdown_summary.get("fit_quality", {})
    base_row["rel_rms_H1"] = maybe_float(fit_quality.get("H1_relative_rms"))
    base_row["rel_rms_L1"] = maybe_float(fit_quality.get("L1_relative_rms"))
    if base_row["rel_rms_H1"] is not None and base_row["rel_rms_L1"] is not None:
        base_row["rel_rms_mean"] = 0.5 * (base_row["rel_rms_H1"] + base_row["rel_rms_L1"])
    else:
        base_row["rel_rms_mean"] = None

    for source in (
        ringdown_table.get(event, {}),
        detector_consistency.get(event, {}),
        matched_consistency.get(event, {}),
        anchor_dataset.get(event, {}),
        pysr_dataset.get(event, {}),
    ):
        for key, value in source.items():
            if key == "event":
                continue
            base_row[key] = value

    gwosc_fields = choose_fields(gwosc_latest.get(event))
    base_row.update(gwosc_fields)
    base_row.update(
        derive_kerr_quantities(
            final_mass_msun=gwosc_fields.get("gwosc_final_mass_source_msun"),
            final_spin=gwosc_fields.get("gwosc_final_spin"),
        )
    )
    base_row.update(
        derive_experiment_features(
            final_mass_msun=gwosc_fields.get("gwosc_final_mass_source_msun"),
            dominant_freq_joint_hz=maybe_float(base_row.get("dominant_freq_joint_hz")),
            dominant_gamma_joint_1_over_s=maybe_float(base_row.get("dominant_gamma_joint_1_over_s")),
        )
    )
    return base_row


def numeric_columns(rows: Iterable[Dict[str, Any]]) -> List[str]:
    names = set()
    for row in rows:
        for key, value in row.items():
            if isinstance(value, (int, float)) or value is None:
                names.add(key)
    return sorted(names)


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        raise RuntimeError("No rows to write")
    fieldnames: List[str] = []
    seen = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    args = parse_args()
    runs_dir = Path(args.runs_dir)
    if not runs_dir.exists():
        raise FileNotFoundError(f"Runs dir not found: {runs_dir}")

    event_dirs = find_local_events(runs_dir)
    if not event_dirs:
        raise RuntimeError(f"No local event directories under {runs_dir}")

    ringdown_table = load_csv_map(runs_dir / "observational_ringdown_table.csv")
    detector_consistency = load_csv_map(runs_dir / "observational_ringdown_detector_consistency.csv")
    matched_consistency = load_csv_map(runs_dir / "observational_ringdown_detector_consistency_matched.csv")
    anchor_dataset = load_csv_map(runs_dir / "observational_ringdown_anchor_dataset.csv")
    pysr_dataset = load_csv_map(runs_dir / "observational_pysr_dataset_matched.csv")

    gwosc_payload = fetch_gwosc_allevents(timeout=args.timeout)
    gwosc_latest = latest_gwosc_records_by_common_name(gwosc_payload)

    session = requests.Session()
    gwosc_latest_detailed: Dict[str, Dict[str, Any]] = {}
    for event_name, record in gwosc_latest.items():
        jsonurl = record.get("jsonurl")
        if not jsonurl:
            gwosc_latest_detailed[event_name] = merge_event_record_with_preferred_parameters(record)
            continue
        detailed = fetch_event_record_from_jsonurl(session=session, jsonurl=jsonurl, timeout=args.timeout)
        gwosc_latest_detailed[event_name] = merge_event_record_with_preferred_parameters(detailed)

    rows = [
        build_row(
            event_dir=event_dir,
            ringdown_table=ringdown_table,
            detector_consistency=detector_consistency,
            matched_consistency=matched_consistency,
            anchor_dataset=anchor_dataset,
            pysr_dataset=pysr_dataset,
            gwosc_latest=gwosc_latest_detailed,
        )
        for event_dir in event_dirs
    ]

    out_csv = runs_dir / "gwosc_enriched_event_table.csv"
    out_exp_csv = runs_dir / "gwosc_enriched_event_table_experiment_joint46.csv"
    out_summary = runs_dir / "gwosc_enriched_event_table_summary.json"
    write_csv(out_csv, rows)

    experiment_rows = [
        r for r in rows
        if r.get("gwosc_final_mass_source_msun") is not None
        and r.get("gwosc_final_spin") is not None
        and r.get("dominant_freq_joint_hz") is not None
        and r.get("dominant_gamma_joint_1_over_s") is not None
        and r.get("kerr_M_times_Omega_H_geom") is not None
    ]
    write_csv(out_exp_csv, experiment_rows)

    summary = {
        "runs_dir": str(runs_dir),
        "n_local_events": len(event_dirs),
        "n_rows_written": len(rows),
        "n_gwosc_joined": sum(1 for r in rows if r.get("gwosc_common_name")),
        "n_with_final_mass_spin": sum(
            1
            for r in rows
            if r.get("gwosc_final_mass_source_msun") is not None and r.get("gwosc_final_spin") is not None
        ),
        "n_with_mass_ratio": sum(1 for r in rows if r.get("gwosc_mass_ratio") is not None),
        "n_with_chi_eff": sum(1 for r in rows if r.get("gwosc_chi_eff") is not None),
        "n_with_network_snr": sum(1 for r in rows if r.get("gwosc_network_snr") is not None),
        "n_with_anchor_ready": sum(1 for r in rows if maybe_bool(r.get("anchor_ready")) is True),
        "n_with_high_consistency": sum(1 for r in rows if r.get("consistency_bucket") == "high_consistency"),
        "n_experiment_joint_rows": len(experiment_rows),
        "output_csv": str(out_csv),
        "output_experiment_csv": str(out_exp_csv),
        "numeric_columns": numeric_columns(rows),
        "gwosc_source_url": GWOSC_ALLEVENTS_URL,
    }
    out_summary.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
