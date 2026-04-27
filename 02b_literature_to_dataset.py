#!/usr/bin/env python3
"""
02b_literature_to_dataset.py  v1.0

Lee valores QNM de LITERATURA (o theory-seed Berti) para alimentar el
bridge real-data  stage02. Reemplaza el carril de extraccion ESPRIT
(desaparecido): la extraccion propia no identificaba limpiamente el modo
(2,2,0) de strain real.

Motivo: la extraccion propia no identifica limpiamente el modo (2,2,0)
de strain real. Los posteriors Bayesianos publicados por LVC/Isi/Giesler/
Capano/pyRing son la entrada limpia para Ruta B (mapeo surrogate AdS).

Entrada:
    data/qnm_events_literature.yml

Salida:
    runs/qnm_dataset_literature/qnm_dataset.csv
    runs/qnm_dataset_literature/qnm_dataset_220.csv

Schema identico al legacy qnm_dataset_220.csv + 4 columnas opcionales:
sigma_freq_hz, sigma_damping_hz, sigma_M_final_Msun, sigma_chi_final.

Uso:
    python3 02b_literature_to_dataset.py \\
        --sources data/qnm_events_literature.yml \\
        --out runs/qnm_dataset_literature
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

SCRIPT_VERSION = "02b_literature_to_dataset.py v1.1"

# Kerr l=m=2 n=0 table from Berti 2009 (arXiv:0905.2975, Table VIII).
G_OVER_C3_PER_MSUN = 4.925491025543576e-6  # s / M_sun

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


def kerr_220_target(chi_final: Optional[float]) -> Optional[tuple]:
    """Interpolate (omega_re, omega_im) n=0 l=m=2 Kerr target at chi_final."""
    if chi_final is None:
        return None
    try:
        chi = float(chi_final)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(chi) or chi < 0.0 or chi > 0.99:
        return None
    return _interpolate(KERR_N0_TABLE, chi)

# Higher-n Kerr table (n=1,2) from Berti 2009, for theory-seed of overtones
# arXiv:0905.2975, Table VIII, l=m=2
KERR_N1_TABLE = [
    {"chi": 0.00, "omega_re": 0.34671, "omega_im": -0.27392},
    {"chi": 0.10, "omega_re": 0.35595, "omega_im": -0.27078},
    {"chi": 0.20, "omega_re": 0.36662, "omega_im": -0.26698},
    {"chi": 0.30, "omega_re": 0.37909, "omega_im": -0.26239},
    {"chi": 0.40, "omega_re": 0.39386, "omega_im": -0.25677},
    {"chi": 0.50, "omega_re": 0.41159, "omega_im": -0.24977},
    {"chi": 0.60, "omega_re": 0.43329, "omega_im": -0.24084},
    {"chi": 0.69, "omega_re": 0.46169, "omega_im": -0.22940},
    {"chi": 0.80, "omega_re": 0.50150, "omega_im": -0.21247},
    {"chi": 0.90, "omega_re": 0.55927, "omega_im": -0.18482},
    {"chi": 0.99, "omega_re": 0.65506, "omega_im": -0.13040},
]

OUTPUT_COLUMNS = [
    "event", "ifo", "pole_source", "mode_rank",
    "freq_hz", "damping_hz", "tau_ms",
    "omega_re", "omega_im",
    "amp_abs", "relative_rms",
    "M_final_Msun", "chi_final",
    "z", "M_final_detector_Msun",
    "is_220_candidate", "kerr_220_distance", "kerr_220_chi_ref",
    "omega_re_norm", "omega_im_norm",
    # extensions for literature uncertainty (downstream scripts ignore them)
    "sigma_freq_hz", "sigma_damping_hz",
    "sigma_M_final_Msun", "sigma_chi_final",
    # Ruta C: Kerr prediction in physical Hz (detector-frame) and standardized residuals
    "f_kerr_hz", "gamma_kerr_hz",
    "sigma_f_kerr_hz", "sigma_gamma_kerr_hz",
    "residual_f", "residual_gamma",
    "kerr_sigma_source",
]

KERR_220_FAIR_THRESHOLD = 0.15


def _interpolate(table: List[Dict[str, float]], chi: float) -> Optional[tuple]:
    if chi < table[0]["chi"] or chi > table[-1]["chi"]:
        return None
    for row in table:
        if chi == float(row["chi"]):
            return float(row["omega_re"]), float(row["omega_im"])
    for left, right in zip(table[:-1], table[1:]):
        cl, cr = float(left["chi"]), float(right["chi"])
        if cl <= chi <= cr:
            w = (chi - cl) / (cr - cl)
            ore = float(left["omega_re"]) + w * (float(right["omega_re"]) - float(left["omega_re"]))
            oim = float(left["omega_im"]) + w * (float(right["omega_im"]) - float(left["omega_im"]))
            return ore, oim
    return None


def kerr_theory(chi_final: float, n: int) -> Optional[tuple]:
    """Dimensionless (M*omega_re, M*omega_im) for Kerr l=m=2, overtone n."""
    if n == 0:
        return _interpolate(KERR_N0_TABLE, chi_final)
    if n == 1:
        return _interpolate(KERR_N1_TABLE, chi_final)
    return None


def load_sources(path: Path) -> Dict[str, Any]:
    with path.open("r") as fh:
        data = yaml.safe_load(fh)
    if "events" not in data:
        raise ValueError(f"{path}: missing 'events' top-level key")
    return data


def row_from_entry(event_name: str, ifo: str,
                   M_f: float, chi_f: float,
                   sigma_M: Optional[float], sigma_chi: Optional[float],
                   z: float,
                   mode_rank: int,
                   mode_entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Build a single CSV row from a YAML mode entry."""
    l = int(mode_entry.get("l", 2))
    m = int(mode_entry.get("m", 2))
    n = int(mode_entry.get("n", 0))
    if (l, m) != (2, 2):
        print(f"  [SKIP] {event_name} mode ({l},{m},{n}): only l=m=2 supported for now")
        return None

    f_hz = mode_entry.get("f_hz")
    tau_ms = mode_entry.get("tau_ms")
    source_paper = str(mode_entry.get("source_paper", "unknown"))

    # scale for normalization uses source-frame mass (omega_re_norm is dimensionless)
    scale = M_f * G_OVER_C3_PER_MSUN  # s per rad/s (to dimensionless)
    # Detector-frame mass accounts for cosmological redshift:
    # f_detector = f_source / (1+z)  ↔  M_detector = M_source * (1+z)
    M_detector = M_f * (1.0 + z)
    scale_detector = M_detector * G_OVER_C3_PER_MSUN

    # THEORY SEED: if f_hz is null AND source_paper starts with "berti_theory",
    # compute from Kerr table. This is a pipeline sanity check  Berti distance
    # should be ~0 by construction.
    if f_hz is None:
        if not source_paper.startswith("berti_theory"):
            print(f"  [SKIP] {event_name} n={n}: f_hz null but source_paper not berti_theory")
            return None
        theory = kerr_theory(chi_f, n)
        if theory is None:
            print(f"  [SKIP] {event_name} n={n}: chi_f={chi_f} out of Berti table")
            return None
        omega_re_norm, omega_im_norm = theory
        omega_re = omega_re_norm / scale
        omega_im = omega_im_norm / scale
        freq_hz = omega_re / (2.0 * math.pi)
        damping_hz = -omega_im
        tau_ms = 1000.0 / damping_hz if damping_hz > 1e-10 else float("nan")
        sigma_f_hz = 0.0
        sigma_damping_hz = 0.0
    else:
        freq_hz = float(f_hz)
        tau_ms_val = float(tau_ms) if tau_ms is not None else float("nan")
        damping_hz = 1000.0 / tau_ms_val if tau_ms_val and tau_ms_val > 0 else float("nan")
        omega_re = 2.0 * math.pi * freq_hz
        omega_im = -damping_hz
        omega_re_norm = omega_re * scale if scale > 0 else float("nan")
        omega_im_norm = omega_im * scale if scale > 0 else float("nan")
        tau_ms = tau_ms_val
        sigma_f_hz = mode_entry.get("sigma_f_hz")
        sigma_tau_ms = mode_entry.get("sigma_tau_ms")
        # Propagate sigma_tau to sigma_damping_hz: d/dtau(1000/tau) = -1000/tau^2
        if sigma_tau_ms is not None and tau_ms_val > 0:
            sigma_damping_hz = 1000.0 * float(sigma_tau_ms) / (tau_ms_val ** 2)
        else:
            sigma_damping_hz = None

    # Kerr-220 distance (fundamental n=0 reference, regardless of this mode's n)
    target_220 = kerr_220_target(chi_f)
    if target_220 is not None and math.isfinite(omega_re_norm) and math.isfinite(omega_im_norm):
        ore_220, oim_220 = target_220
        kerr_dist = math.hypot(omega_re_norm - ore_220, omega_im_norm - oim_220)
    else:
        kerr_dist = None

    is_220 = (n == 0) and (kerr_dist is not None) and (kerr_dist < KERR_220_FAIR_THRESHOLD)

    # --- Ruta C: Kerr prediction in physical Hz for this mode (detector-frame) ---
    # Uses scale_detector = M_source*(1+z)*G/c^3 so that f_kerr is in the
    # detector frame, matching f_hz from the literature.
    kerr_target = kerr_theory(chi_f, n)
    if kerr_target is not None and scale_detector > 0:
        ore_k, oim_k = kerr_target
        f_kerr_hz = ore_k / (2.0 * math.pi * scale_detector)
        gamma_kerr_hz = -oim_k / scale_detector  # oim_k < 0, so gamma > 0
    else:
        f_kerr_hz = None
        gamma_kerr_hz = None

    # Propagate sigma_M and sigma_chi into Kerr prediction uncertainty.
    # f_kerr ∝ omega_re(chi)/M_detector  →  df/dM = -f_kerr/M_detector
    # df/dchi from numerical derivative of Berti table.
    # When sigma_M or sigma_chi are absent: sigma_f_kerr_hz = 0 (conservative
    # choice: treats Kerr prediction as exact given the point estimate M,chi).
    sigma_f_kerr_hz = None
    sigma_gamma_kerr_hz = None
    kerr_sigma_source = "none"
    if f_kerr_hz is not None:
        if sigma_M is not None or sigma_chi is not None:
            # Compute chi derivative (used when sigma_chi is available)
            dchi = 1e-3
            t_hi = kerr_theory(min(chi_f + dchi, 0.99), n)
            t_lo = kerr_theory(max(chi_f - dchi, 0.0), n)
            step = (min(chi_f + dchi, 0.99) - max(chi_f - dchi, 0.0))
            if t_hi is not None and t_lo is not None and step > 0:
                df_dchi = (t_hi[0] - t_lo[0]) / step / (2.0 * math.pi * scale_detector)
                dg_dchi = -(t_hi[1] - t_lo[1]) / step / scale_detector
            else:
                df_dchi = dg_dchi = 0.0
            # sigma_M is uncertainty on M_source, so df/dM_source = -f_kerr/M_source
            df_dM = -f_kerr_hz / M_f if M_f > 0 else 0.0
            dg_dM = -gamma_kerr_hz / M_f if (gamma_kerr_hz is not None and M_f > 0) else 0.0
            # Use whichever sigmas are available; treat absent ones as 0
            s_chi = float(sigma_chi) if sigma_chi is not None else 0.0
            s_M = float(sigma_M) if sigma_M is not None else 0.0
            sigma_f_kerr_hz = math.sqrt(
                (df_dchi * s_chi) ** 2 + (df_dM * s_M) ** 2
            )
            sigma_gamma_kerr_hz = math.sqrt(
                (dg_dchi * s_chi) ** 2 + (dg_dM * s_M) ** 2
            )
            if sigma_M is not None and sigma_chi is not None:
                kerr_sigma_source = "propagated"
            else:
                kerr_sigma_source = "propagated_partial"
        else:
            # No M/chi uncertainties in YAML: treat Kerr prediction as exact
            sigma_f_kerr_hz = 0.0
            sigma_gamma_kerr_hz = 0.0
            kerr_sigma_source = "point_estimate"

    # Standardized residuals: r = (obs - kerr) / sqrt(sigma_obs^2 + sigma_kerr^2)
    residual_f = None
    residual_gamma = None
    if f_kerr_hz is not None and sigma_f_hz is not None:
        sigma_f_obs = float(sigma_f_hz)
        sigma_f_kerr = float(sigma_f_kerr_hz) if sigma_f_kerr_hz is not None else 0.0
        denom_f = math.sqrt(sigma_f_obs ** 2 + sigma_f_kerr ** 2)
        if denom_f > 0:
            residual_f = (freq_hz - f_kerr_hz) / denom_f
    if gamma_kerr_hz is not None and sigma_damping_hz is not None:
        sigma_g_obs = float(sigma_damping_hz)
        sigma_g_kerr = float(sigma_gamma_kerr_hz) if sigma_gamma_kerr_hz is not None else 0.0
        denom_g = math.sqrt(sigma_g_obs ** 2 + sigma_g_kerr ** 2)
        if denom_g > 0:
            residual_gamma = (damping_hz - gamma_kerr_hz) / denom_g

    return {
        "event": event_name,
        "ifo": ifo,
        "pole_source": source_paper,
        "mode_rank": mode_rank,
        "freq_hz": freq_hz,
        "damping_hz": damping_hz,
        "tau_ms": tau_ms,
        "omega_re": omega_re,
        "omega_im": omega_im,
        "amp_abs": mode_entry.get("amp_abs"),
        "relative_rms": None,
        "M_final_Msun": M_f,
        "chi_final": chi_f,
        "z": z,
        "M_final_detector_Msun": M_detector,
        "is_220_candidate": is_220,
        "kerr_220_distance": kerr_dist,
        "kerr_220_chi_ref": chi_f if target_220 is not None else None,
        "omega_re_norm": omega_re_norm,
        "omega_im_norm": omega_im_norm,
        "sigma_freq_hz": sigma_f_hz,
        "sigma_damping_hz": sigma_damping_hz,
        "sigma_M_final_Msun": sigma_M,
        "sigma_chi_final": sigma_chi,
        "f_kerr_hz": f_kerr_hz,
        "gamma_kerr_hz": gamma_kerr_hz,
        "sigma_f_kerr_hz": sigma_f_kerr_hz,
        "sigma_gamma_kerr_hz": sigma_gamma_kerr_hz,
        "residual_f": residual_f,
        "residual_gamma": residual_gamma,
        "kerr_sigma_source": kerr_sigma_source,
    }


def build_rows(sources: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for ev in sources["events"]:
        event_name = str(ev["event"])
        ifo = str(ev.get("ifo", "literature"))
        M_raw = ev.get("M_final_Msun")
        chi_raw = ev.get("chi_final")
        if M_raw is None or chi_raw is None:
            print(f"  [SKIP] {event_name}: M_final_Msun or chi_final is null")
            continue
        M_f = float(M_raw)
        chi_f = float(chi_raw)
        sigma_M = ev.get("sigma_M_final_Msun")
        sigma_chi = ev.get("sigma_chi_final")
        z_raw = ev.get("z", 0.0)
        z = float(z_raw) if z_raw is not None else 0.0
        modes = ev.get("modes", [])
        # Sort modes by n so mode_rank=0 is fundamental
        modes_sorted = sorted(modes, key=lambda x: int(x.get("n", 0)))
        for rank, mode_entry in enumerate(modes_sorted):
            row = row_from_entry(event_name, ifo, M_f, chi_f,
                                 sigma_M, sigma_chi, z, rank, mode_entry)
            if row is not None:
                rows.append(row)
    return rows


def write_csv(rows: List[Dict[str, Any]], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k) for k in OUTPUT_COLUMNS})


def summarise(rows: List[Dict[str, Any]]) -> None:
    n = len(rows)
    n_220 = sum(1 for r in rows if r.get("is_220_candidate"))
    theory_seed = [r for r in rows if str(r.get("pole_source", "")).startswith("berti_theory")]
    lit_rows = [r for r in rows if not str(r.get("pole_source", "")).startswith("berti_theory")]

    print(f"\n[SUMMARY]")
    print(f"  rows total          : {n}")
    print(f"  is_220_candidate    : {n_220}")
    print(f"  theory-seed rows    : {len(theory_seed)}")
    print(f"  literature rows     : {len(lit_rows)}")

    if theory_seed:
        print("\n  [THEORY-SEED sanity  Berti distance debe ser ~0]")
        for r in theory_seed[:10]:
            d = r.get("kerr_220_distance")
            d_str = f"{d:.2e}" if d is not None else "none"
            print(f"    {r['event']:25s} n_rank={r['mode_rank']} "
                  f"kerr_220_distance={d_str}")

    if lit_rows:
        print("\n  [LITERATURE rows  Berti distance esperada dentro de error]")
        for r in lit_rows[:20]:
            d = r.get("kerr_220_distance")
            d_str = f"{d:.3f}" if d is not None else "none"
            print(f"    {r['event']:25s} source={r['pole_source']:30s} "
                  f"kerr_220_distance={d_str}")


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description=SCRIPT_VERSION)
    p.add_argument("--sources", type=Path,
                   default=Path("data/qnm_events_literature.yml"),
                   help="YAML con eventos + modos de literatura / theory seed")
    p.add_argument("--out", type=Path,
                   default=Path("runs/qnm_dataset_literature"),
                   help="Directorio de salida")
    args = p.parse_args(argv)

    print(f"[{SCRIPT_VERSION}]")
    print(f"  sources: {args.sources}")
    print(f"  out    : {args.out}")

    if not args.sources.exists():
        print(f"[ERROR] sources file not found: {args.sources}", file=sys.stderr)
        return 2

    sources = load_sources(args.sources)
    rows = build_rows(sources)

    if not rows:
        print("[ERROR] No rows produced from sources YAML", file=sys.stderr)
        return 2

    out_csv = args.out / "qnm_dataset.csv"
    write_csv(rows, out_csv)
    print(f"\n  wrote {len(rows)} rows  {out_csv}")

    # 220-only filter (fundamentals)
    rows_220 = [r for r in rows if r.get("is_220_candidate")]
    out_csv_220 = args.out / "qnm_dataset_220.csv"
    write_csv(rows_220, out_csv_220)
    print(f"  wrote {len(rows_220)} rows (is_220)  {out_csv_220}")

    summarise(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
