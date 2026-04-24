#!/usr/bin/env python3
"""
05_kerr_consistency_audit.py

Lee el CSV producido por 02b_literature_to_dataset.py y ejecuta el contraste
Kerr por evento y global para Ruta C.

Entrada:
    --csv  CSV con columnas residual_f, residual_gamma, f_kerr_hz, etc.
           (por defecto: runs/qnm_dataset_literature/qnm_dataset.csv)

Salidas:
    <out>/kerr_audit_table.csv   — tabla maestra por evento con veredicto
    <out>/kerr_audit_summary.json — estadísticas globales (KS, AD, N)

Clasificación de consistencia por evento:
    consistent   : max(|r_f|, |r_gamma|) < 1
    marginal     : 1 <= max < 2
    tension      : 2 <= max < 3
    strong_tension : max >= 3
    no_data      : residuos no disponibles (falta sigma_obs)

El test global KS y Anderson-Darling se aplica sobre la distribución conjunta
de todos los residuos (r_f y r_gamma) respecto a N(0,1).

Nota: cuando kerr_sigma_source == "point_estimate" los residuos usan solo
sigma_obs. Una vez que se añadan sigma_M y sigma_chi al YAML, los residuos
mejorarán usando sigma_kerr propagada también.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_VERSION = "05_kerr_consistency_audit.py v1.0"

VERDICT_THRESHOLDS = [
    (1.0, "consistent"),
    (2.0, "marginal"),
    (3.0, "tension"),
    (math.inf, "strong_tension"),
]

AUDIT_COLUMNS = [
    "event", "mode_rank", "f_obs_hz", "sigma_f_obs_hz",
    "f_kerr_hz", "sigma_f_kerr_hz",
    "gamma_obs_hz", "sigma_gamma_obs_hz",
    "gamma_kerr_hz", "sigma_gamma_kerr_hz",
    "residual_f", "residual_gamma", "max_abs_residual",
    "kerr_sigma_source", "verdict_kerr",
]


def _float_or_none(v: Any) -> Optional[float]:
    if v is None or v == "" or v == "None":
        return None
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def verdict_from_residuals(r_f: Optional[float], r_g: Optional[float]) -> tuple[Optional[float], str]:
    vals = [abs(r) for r in (r_f, r_g) if r is not None]
    if not vals:
        return None, "no_data"
    m = max(vals)
    for threshold, label in VERDICT_THRESHOLDS:
        if m < threshold:
            return m, label
    return m, "strong_tension"


def load_csv(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def build_audit_rows(rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    audit = []
    for row in rows:
        r_f = _float_or_none(row.get("residual_f"))
        r_g = _float_or_none(row.get("residual_gamma"))
        max_r, verdict = verdict_from_residuals(r_f, r_g)
        audit.append({
            "event": row.get("event", ""),
            "mode_rank": row.get("mode_rank", ""),
            "f_obs_hz": _float_or_none(row.get("freq_hz")),
            "sigma_f_obs_hz": _float_or_none(row.get("sigma_freq_hz")),
            "f_kerr_hz": _float_or_none(row.get("f_kerr_hz")),
            "sigma_f_kerr_hz": _float_or_none(row.get("sigma_f_kerr_hz")),
            "gamma_obs_hz": _float_or_none(row.get("damping_hz")),
            "sigma_gamma_obs_hz": _float_or_none(row.get("sigma_damping_hz")),
            "gamma_kerr_hz": _float_or_none(row.get("gamma_kerr_hz")),
            "sigma_gamma_kerr_hz": _float_or_none(row.get("sigma_gamma_kerr_hz")),
            "residual_f": r_f,
            "residual_gamma": r_g,
            "max_abs_residual": max_r,
            "kerr_sigma_source": row.get("kerr_sigma_source", ""),
            "verdict_kerr": verdict,
        })
    return audit


def write_audit_csv(rows: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=AUDIT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k) for k in AUDIT_COLUMNS})


def global_stats(audit_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    all_residuals: List[float] = []
    for row in audit_rows:
        for key in ("residual_f", "residual_gamma"):
            v = row.get(key)
            if v is not None:
                all_residuals.append(v)

    n = len(all_residuals)
    unique_events = sorted({row["event"] for row in audit_rows})
    stats: Dict[str, Any] = {
        "n_unique_events": len(unique_events),
        "n_mode_rows": len(audit_rows),
        "n_residuals": n,
        "kerr_sigma_source": audit_rows[0].get("kerr_sigma_source", "") if audit_rows else "",
    }

    # Per-mode verdict counts (one entry per CSV row / mode)
    verdict_counts: Dict[str, int] = {}
    for row in audit_rows:
        v = row.get("verdict_kerr", "no_data")
        verdict_counts[v] = verdict_counts.get(v, 0) + 1
    stats["verdict_counts_by_mode"] = verdict_counts

    # Per-event verdict: worst mode verdict per event
    event_worst: Dict[str, str] = {}
    order = ["no_data", "consistent", "marginal", "tension", "strong_tension"]
    for row in audit_rows:
        ev = row["event"]
        v = row.get("verdict_kerr", "no_data")
        prev = event_worst.get(ev, "no_data")
        if order.index(v) > order.index(prev):
            event_worst[ev] = v
    event_verdict_counts: Dict[str, int] = {}
    for v in event_worst.values():
        event_verdict_counts[v] = event_verdict_counts.get(v, 0) + 1
    stats["verdict_counts_by_event"] = event_verdict_counts

    if n == 0:
        stats["note"] = "no residuals available"
        return stats

    mean_r = sum(all_residuals) / n
    var_r = sum((x - mean_r) ** 2 for x in all_residuals) / n
    stats["residual_mean"] = round(mean_r, 4)
    stats["residual_std"] = round(math.sqrt(var_r), 4)

    try:
        from scipy import stats as scipy_stats
        ks_stat, ks_p = scipy_stats.kstest(all_residuals, "norm")
        stats["ks_stat"] = round(float(ks_stat), 4)
        stats["ks_pvalue"] = round(float(ks_p), 4)
        stats["ks_consistent_with_normal"] = bool(ks_p > 0.05)

        ad_result = scipy_stats.anderson(all_residuals, dist="norm")
        stats["ad_stat"] = round(float(ad_result.statistic), 4)
        stats["ad_critical_5pct"] = round(float(ad_result.critical_values[2]), 4)
        stats["ad_consistent_with_normal_5pct"] = bool(
            ad_result.statistic < ad_result.critical_values[2]
        )
    except ImportError:
        stats["note"] = "scipy not available; KS/AD tests skipped"

    return stats


def print_summary(audit_rows: List[Dict[str, Any]], gstats: Dict[str, Any]) -> None:
    print(f"\n[KERR CONSISTENCY AUDIT — {SCRIPT_VERSION}]")
    print(f"  eventos únicos       : {gstats['n_unique_events']}")
    print(f"  filas de modos       : {gstats['n_mode_rows']}")
    print(f"  residuos totales     : {gstats['n_residuals']}")
    print(f"  kerr_sigma_source    : {gstats.get('kerr_sigma_source', 'n/a')}")
    print(f"  residual mean / std  : {gstats.get('residual_mean', 'n/a')} / {gstats.get('residual_std', 'n/a')}")
    if "ks_stat" in gstats:
        print(f"  KS stat / p-value    : {gstats['ks_stat']} / {gstats['ks_pvalue']}  "
              f"({'OK' if gstats['ks_consistent_with_normal'] else 'FAIL'} vs N(0,1))")
        print(f"  AD stat / crit 5%    : {gstats['ad_stat']} / {gstats['ad_critical_5pct']}  "
              f"({'OK' if gstats['ad_consistent_with_normal_5pct'] else 'FAIL'} vs N(0,1))")

    print(f"\n  Veredictos por evento (peor modo):")
    for v, cnt in sorted(gstats.get("verdict_counts_by_event", {}).items()):
        print(f"    {v:20s} : {cnt}")

    print(f"\n  Tabla por evento:")
    print(f"  {'evento':30s} {'r_f':>8s} {'r_g':>8s} {'max|r|':>8s}  veredicto")
    for row in audit_rows:
        r_f = row["residual_f"]
        r_g = row["residual_gamma"]
        m = row["max_abs_residual"]
        rf_s = f"{r_f:+.2f}" if r_f is not None else "  n/a "
        rg_s = f"{r_g:+.2f}" if r_g is not None else "  n/a "
        m_s = f"{m:.2f}" if m is not None else " n/a"
        print(f"  {row['event']:30s} {rf_s:>8s} {rg_s:>8s} {m_s:>8s}  {row['verdict_kerr']}")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=SCRIPT_VERSION)
    p.add_argument(
        "--csv", type=Path,
        default=Path("runs/qnm_dataset_literature/qnm_dataset.csv"),
        help="CSV de entrada (output de 02b_literature_to_dataset.py)",
    )
    p.add_argument(
        "--out", type=Path,
        default=Path("runs/kerr_consistency_audit"),
        help="Directorio de salida",
    )
    args = p.parse_args(argv)

    if not args.csv.exists():
        print(f"[ERROR] CSV no encontrado: {args.csv}", file=sys.stderr)
        return 2

    print(f"[{SCRIPT_VERSION}]")
    print(f"  csv: {args.csv}")
    print(f"  out: {args.out}")

    rows = load_csv(args.csv)
    if not rows:
        print("[ERROR] CSV vacío", file=sys.stderr)
        return 2

    audit_rows = build_audit_rows(rows)
    gstats = global_stats(audit_rows)

    out_table = args.out / "kerr_audit_table.csv"
    write_audit_csv(audit_rows, out_table)
    print(f"\n  escribió {len(audit_rows)} filas → {out_table}")

    out_summary = args.out / "kerr_audit_summary.json"
    out_summary.parent.mkdir(parents=True, exist_ok=True)
    with out_summary.open("w") as fh:
        json.dump(gstats, fh, indent=2)
    print(f"  escribió resumen global → {out_summary}")

    print_summary(audit_rows, gstats)
    return 0


if __name__ == "__main__":
    sys.exit(main())
