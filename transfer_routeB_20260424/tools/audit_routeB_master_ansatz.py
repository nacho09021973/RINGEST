#!/usr/bin/env python3
"""
Audita un ansatz maestro minimo sobre el subconjunto consolidado de 7 eventos
con ringdown congelado, sin recalcular symbolic regression.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_JSON = REPO_ROOT / "runs/routeB_all18_20260422/03_discover_bulk_equations/outputs/einstein_discovery_summary.json"
GEOMETRY_JSON = REPO_ROOT / "runs/routeB_all18_20260422/02_emergent_geometry_engine/emergent_geometry_summary.json"
REFERENCE_CSV = REPO_ROOT / "runs/community_ringdown_cohort/community_ringdown_reference_table.csv"
OUT_DIR = REPO_ROOT / "runs/routeB_all18_20260422/analysis"
OUT_CSV = OUT_DIR / "master_ansatz_audit.csv"

EVENTS = {
    "GW150914",
    "GW170104",
    "GW170814",
    "GW170823",
    "GW190421_213856",
    "GW190503_185404",
    "GW190828_063405",
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def classify_equation(eq: str) -> str:
    has_square_x3 = "square(" in eq and "x3" in eq
    has_x0 = "x0" in eq
    has_x3_x1 = "(x3 * x1)" in eq
    has_linear_x3 = "(x3 /" in eq

    if has_x3_x1:
        return "x3_x1_bilinear"
    if has_x0:
        return "mixed_x0_x3_coupled"
    if has_linear_x3 and not has_square_x3:
        return "linear_x3_rational"
    return "square_x3_plus_rational"


def has_rational_core(eq: str) -> bool:
    return "(x4 / x1)" in eq or "(x4 / neg(x1))" in eq or "((x2 * x4) / x1)" in eq


def has_x3_square(eq: str) -> bool:
    return "square(" in eq and "x3" in eq


def has_x3_linear(eq: str) -> bool:
    return "(x3 /" in eq


def has_x0x3_coupling(eq: str) -> bool:
    return "x0" in eq and "x3" in eq


def has_x3x1_bilinear(eq: str) -> bool:
    return "(x3 * x1)" in eq


def main() -> None:
    discovery = json.loads(DISCOVERY_JSON.read_text())
    geometry = {row["name"]: row for row in json.loads(GEOMETRY_JSON.read_text())["systems"]}
    reference = {row["event"]: row for row in _read_csv(REFERENCE_CSV)}

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "event",
        "equation_class",
        "equation",
        "r2",
        "source_kind",
        "M_final_Msun",
        "chi_final",
        "zh_pred",
        "has_rational_core",
        "has_x3_square",
        "has_x3_linear",
        "has_x0x3_coupling",
        "has_x3x1_bilinear",
        "fits_base_core",
        "fits_base_plus_x3",
        "fits_base_plus_x0x3",
        "ansatz_status",
    ]

    with OUT_CSV.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()

        for item in discovery["geometries"]:
            event = item["name"]
            if event not in EVENTS:
                continue

            eq = item["results"]["R_equation"]["equation"]
            rational = has_rational_core(eq)
            x3_square = has_x3_square(eq)
            x3_linear = has_x3_linear(eq)
            x0x3 = has_x0x3_coupling(eq)
            x3x1 = has_x3x1_bilinear(eq)

            fits_base_core = rational and not x3_square and not x3_linear and not x0x3 and not x3x1
            fits_base_plus_x3 = rational and (x3_square or x3_linear) and not x0x3 and not x3x1
            fits_base_plus_x0x3 = rational and x0x3 and not x3x1

            if fits_base_core:
                ansatz_status = "base_core"
            elif fits_base_plus_x3:
                ansatz_status = "base_plus_x3"
            elif fits_base_plus_x0x3:
                ansatz_status = "base_plus_x0x3"
            else:
                ansatz_status = "outside_master_ansatz"

            writer.writerow(
                {
                    "event": event,
                    "equation_class": classify_equation(eq),
                    "equation": eq,
                    "r2": item["results"]["R_equation"]["r2"],
                    "source_kind": reference[event]["source_kind"],
                    "M_final_Msun": reference[event]["M_final_Msun"],
                    "chi_final": reference[event]["chi_final"],
                    "zh_pred": geometry[event]["zh_pred"],
                    "has_rational_core": "yes" if rational else "no",
                    "has_x3_square": "yes" if x3_square else "no",
                    "has_x3_linear": "yes" if x3_linear else "no",
                    "has_x0x3_coupling": "yes" if x0x3 else "no",
                    "has_x3x1_bilinear": "yes" if x3x1 else "no",
                    "fits_base_core": "yes" if fits_base_core else "no",
                    "fits_base_plus_x3": "yes" if fits_base_plus_x3 else "no",
                    "fits_base_plus_x0x3": "yes" if fits_base_plus_x0x3 else "no",
                    "ansatz_status": ansatz_status,
                }
            )

    print(OUT_CSV)


if __name__ == "__main__":
    main()
