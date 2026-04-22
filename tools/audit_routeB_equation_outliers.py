#!/usr/bin/env python3
"""
Audita outliers y subfamilias algebraicas de routeB_all18_20260422
usando solo artefactos ya congelados.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_JSON = REPO_ROOT / "runs/routeB_all18_20260422/03_discover_bulk_equations/outputs/einstein_discovery_summary.json"
GEOMETRY_JSON = REPO_ROOT / "runs/routeB_all18_20260422/02_emergent_geometry_engine/emergent_geometry_summary.json"
REFERENCE_CSV = REPO_ROOT / "runs/community_ringdown_cohort/community_ringdown_reference_table.csv"
TIERS_CSV = REPO_ROOT / "runs/community_ringdown_cohort/community_ringdown_tiers.csv"
OUT_DIR = REPO_ROOT / "runs/routeB_all18_20260422/analysis"
OUT_CSV = OUT_DIR / "equation_outlier_audit.csv"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def classify_equation(eq: str) -> str:
    has_square_x3 = "square(" in eq and "x3" in eq
    has_x4_over_x1 = "(x4 / x1)" in eq or "(x4 / neg(x1))" in eq or "((x2 * x4) / x1)" in eq
    has_x0 = "x0" in eq
    has_x3_x1 = "(x3 * x1)" in eq
    has_linear_x3 = "(x3 /" in eq
    has_x2_x4_over_x1 = "(x2 * x4) / x1" in eq or "x4 / (x1 / x2)" in eq

    if has_x0:
        return "mixed_x0_x3_coupled"
    if has_x3_x1:
        return "x3_x1_bilinear"
    if has_linear_x3 and not has_square_x3:
        return "linear_x3_rational"
    if has_square_x3 and has_x4_over_x1:
        return "square_x3_plus_rational"
    if has_x2_x4_over_x1:
        return "x2x4_over_x1_variant"
    return "other"


def _float_or_none(value: str) -> float | None:
    try:
        return float(value) if value != "" else None
    except ValueError:
        return None


def _relative_width(median: float | None, q05: float | None, q95: float | None) -> float | None:
    if median is None or q05 is None or q95 is None:
        return None
    if median == 0:
        return None
    return (q95 - q05) / abs(median)


def main() -> None:
    discovery = json.loads(DISCOVERY_JSON.read_text())
    geometry = json.loads(GEOMETRY_JSON.read_text())
    reference = {row["event"]: row for row in _read_csv(REFERENCE_CSV)}
    tiers = {row["event"]: row for row in _read_csv(TIERS_CSV)}
    geometry_by_event = {row["name"]: row for row in geometry["systems"]}

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "event",
        "equation_class",
        "r2",
        "validation_tier",
        "tier_status",
        "source_kind",
        "fit_status",
        "M_final_Msun",
        "M_final_Msun_q05",
        "M_final_Msun_q95",
        "M_final_rel_width",
        "chi_final",
        "chi_final_q05",
        "chi_final_q95",
        "chi_final_rel_width",
        "f_ringdown_hz",
        "f_ringdown_hz_q05",
        "f_ringdown_hz_q95",
        "f_ringdown_rel_width",
        "damping_hz",
        "damping_hz_q05",
        "damping_hz_q95",
        "damping_rel_width",
        "zh_pred",
        "notes",
    ]

    with OUT_CSV.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()

        for item in discovery["geometries"]:
            event = item["name"]
            eq = item["results"]["R_equation"]["equation"]
            ref = reference[event]
            geo = geometry_by_event[event]
            tier = tiers[event]

            m = _float_or_none(ref["M_final_Msun"])
            m05 = _float_or_none(ref["M_final_Msun_q05"])
            m95 = _float_or_none(ref["M_final_Msun_q95"])
            chi = _float_or_none(ref["chi_final"])
            chi05 = _float_or_none(ref["chi_final_q05"])
            chi95 = _float_or_none(ref["chi_final_q95"])
            f = _float_or_none(ref["f_ringdown_hz"])
            f05 = _float_or_none(ref["f_ringdown_hz_q05"])
            f95 = _float_or_none(ref["f_ringdown_hz_q95"])
            g = _float_or_none(ref["damping_hz"])
            g05 = _float_or_none(ref["damping_hz_q05"])
            g95 = _float_or_none(ref["damping_hz_q95"])

            writer.writerow(
                {
                    "event": event,
                    "equation_class": classify_equation(eq),
                    "r2": item["results"]["R_equation"]["r2"],
                    "validation_tier": tier["validation_tier"],
                    "tier_status": tier["tier_status"],
                    "source_kind": ref["source_kind"],
                    "fit_status": ref["fit_status"],
                    "M_final_Msun": ref["M_final_Msun"],
                    "M_final_Msun_q05": ref["M_final_Msun_q05"],
                    "M_final_Msun_q95": ref["M_final_Msun_q95"],
                    "M_final_rel_width": _relative_width(m, m05, m95),
                    "chi_final": ref["chi_final"],
                    "chi_final_q05": ref["chi_final_q05"],
                    "chi_final_q95": ref["chi_final_q95"],
                    "chi_final_rel_width": _relative_width(chi, chi05, chi95),
                    "f_ringdown_hz": ref["f_ringdown_hz"],
                    "f_ringdown_hz_q05": ref["f_ringdown_hz_q05"],
                    "f_ringdown_hz_q95": ref["f_ringdown_hz_q95"],
                    "f_ringdown_rel_width": _relative_width(f, f05, f95),
                    "damping_hz": ref["damping_hz"],
                    "damping_hz_q05": ref["damping_hz_q05"],
                    "damping_hz_q95": ref["damping_hz_q95"],
                    "damping_rel_width": _relative_width(g, g05, g95),
                    "zh_pred": geo["zh_pred"],
                    "notes": ref["notes"],
                }
            )

    print(OUT_CSV)


if __name__ == "__main__":
    main()
