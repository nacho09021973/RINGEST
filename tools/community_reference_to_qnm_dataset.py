#!/usr/bin/env python3
"""
Adapt community_ringdown_reference_table.csv to the qnm_dataset.csv schema
consumed by realdata_ringdown_to_stage02_boundary_dataset.py.

This is an offline adapter: it does not rerun ringdown or pyRingGW. It only
uses values already frozen in the community reference table.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Optional


G_OVER_C3_PER_MSUN = 4.925491025543576e-6  # s / M_sun
KERR_220_FAIR_THRESHOLD = 0.15

KERR_N0_TABLE = [
    {"chi": 0.00, "omega_re": 0.37367, "omega_im": -0.08896},
    {"chi": 0.10, "omega_re": 0.38519, "omega_im": -0.08752},
    {"chi": 0.20, "omega_re": 0.39793, "omega_im": -0.08588},
    {"chi": 0.30, "omega_re": 0.41225, "omega_im": -0.08394},
    {"chi": 0.40, "omega_re": 0.42858, "omega_im": -0.08156},
    {"chi": 0.50, "omega_re": 0.44753, "omega_im": -0.07853},
    {"chi": 0.60, "omega_re": 0.47004, "omega_im": -0.07449},
    {"chi": 0.69, "omega_re": 0.49766, "omega_im": -0.06893},
    {"chi": 0.80, "omega_re": 0.53383, "omega_im": -0.06064},
    {"chi": 0.90, "omega_re": 0.58839, "omega_im": -0.04725},
    {"chi": 0.99, "omega_re": 0.67876, "omega_im": -0.02055},
]

OUTPUT_COLUMNS = [
    "event",
    "ifo",
    "pole_source",
    "mode_rank",
    "freq_hz",
    "damping_hz",
    "tau_ms",
    "omega_re",
    "omega_im",
    "amp_abs",
    "relative_rms",
    "M_final_Msun",
    "chi_final",
    "is_220_candidate",
    "kerr_220_distance",
    "kerr_220_chi_ref",
    "omega_re_norm",
    "omega_im_norm",
    "sigma_freq_hz",
    "sigma_damping_hz",
    "sigma_M_final_Msun",
    "sigma_chi_final",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build qnm_dataset.csv-style input from the frozen community reference table."
    )
    parser.add_argument(
        "--reference-csv",
        type=Path,
        default=Path("runs/community_ringdown_cohort/community_ringdown_reference_table.csv"),
        help="Frozen community_ringdown_reference_table.csv",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("runs/community_ringdown_cohort/qnm_dataset_community_reference.csv"),
        help="Output qnm_dataset.csv-style file",
    )
    return parser.parse_args()


def _float_or_none(value: object) -> Optional[float]:
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    try:
        out = float(text)
    except ValueError:
        return None
    if not math.isfinite(out):
        return None
    return out


def _interp_kerr_220(chi: float) -> Optional[tuple[float, float]]:
    if chi < KERR_N0_TABLE[0]["chi"] or chi > KERR_N0_TABLE[-1]["chi"]:
        return None
    for row in KERR_N0_TABLE:
        if chi == float(row["chi"]):
            return float(row["omega_re"]), float(row["omega_im"])
    for left, right in zip(KERR_N0_TABLE[:-1], KERR_N0_TABLE[1:]):
        cl, cr = float(left["chi"]), float(right["chi"])
        if cl <= chi <= cr:
            w = (chi - cl) / (cr - cl)
            ore = float(left["omega_re"]) + w * (float(right["omega_re"]) - float(left["omega_re"]))
            oim = float(left["omega_im"]) + w * (float(right["omega_im"]) - float(left["omega_im"]))
            return ore, oim
    return None


def _sigma_from_quantiles(low: object, high: object) -> Optional[float]:
    lo = _float_or_none(low)
    hi = _float_or_none(high)
    if lo is None or hi is None:
        return None
    return abs(hi - lo) / 2.0


def adapt_row(row: dict[str, str]) -> Optional[dict[str, object]]:
    event = row.get("event", "").strip()
    freq_hz = _float_or_none(row.get("f_ringdown_hz"))
    damping_hz = _float_or_none(row.get("damping_hz"))
    tau_ms = _float_or_none(row.get("tau_ms"))
    mass = _float_or_none(row.get("M_final_Msun"))
    chi = _float_or_none(row.get("chi_final"))

    required = [event, freq_hz, damping_hz, tau_ms, mass, chi]
    if any(value in ("", None) for value in required):
        return None
    if freq_hz <= 0 or damping_hz <= 0 or tau_ms <= 0 or mass <= 0:
        return None

    omega_re = 2.0 * math.pi * freq_hz
    omega_im = -damping_hz
    scale = mass * G_OVER_C3_PER_MSUN
    omega_re_norm = omega_re * scale
    omega_im_norm = omega_im * scale

    target = _interp_kerr_220(chi)
    if target is not None:
        target_re, target_im = target
        kerr_dist = math.hypot(omega_re_norm - target_re, omega_im_norm - target_im)
        kerr_chi_ref: object = chi
    else:
        kerr_dist = None
        kerr_chi_ref = None

    sigma_freq = _sigma_from_quantiles(row.get("f_ringdown_hz_q05"), row.get("f_ringdown_hz_q95"))
    sigma_damping = _sigma_from_quantiles(row.get("damping_hz_q05"), row.get("damping_hz_q95"))
    sigma_mass = _sigma_from_quantiles(row.get("M_final_Msun_q05"), row.get("M_final_Msun_q95"))
    sigma_chi = _sigma_from_quantiles(row.get("chi_final_q05"), row.get("chi_final_q95"))

    source_kind = row.get("source_kind", "").strip() or "community_reference"
    fit_status = row.get("fit_status", "").strip()
    pole_source = f"community_ringdown_reference_table:{source_kind}"
    if fit_status:
        pole_source = f"{pole_source}:{fit_status}"

    return {
        "event": event,
        "ifo": "community",
        "pole_source": pole_source,
        "mode_rank": 0,
        "freq_hz": freq_hz,
        "damping_hz": damping_hz,
        "tau_ms": tau_ms,
        "omega_re": omega_re,
        "omega_im": omega_im,
        "amp_abs": "",
        "relative_rms": "",
        "M_final_Msun": mass,
        "chi_final": chi,
        "is_220_candidate": bool(kerr_dist is not None and kerr_dist < KERR_220_FAIR_THRESHOLD),
        "kerr_220_distance": kerr_dist,
        "kerr_220_chi_ref": kerr_chi_ref,
        "omega_re_norm": omega_re_norm,
        "omega_im_norm": omega_im_norm,
        "sigma_freq_hz": sigma_freq,
        "sigma_damping_hz": sigma_damping,
        "sigma_M_final_Msun": sigma_mass,
        "sigma_chi_final": sigma_chi,
    }


def main() -> int:
    args = parse_args()
    rows = list(csv.DictReader(args.reference_csv.open(newline="", encoding="utf-8")))
    adapted = []
    skipped = []
    for row in rows:
        out = adapt_row(row)
        if out is None:
            skipped.append(row.get("event", ""))
            continue
        adapted.append(out)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row in adapted:
            writer.writerow({key: row.get(key, "") for key in OUTPUT_COLUMNS})

    print(f"input: {args.reference_csv}")
    print(f"output: {args.out}")
    print(f"rows_read: {len(rows)}")
    print(f"rows_written: {len(adapted)}")
    if skipped:
        print("skipped_events: " + ",".join(skipped))
    return 0 if adapted else 1


if __name__ == "__main__":
    raise SystemExit(main())
