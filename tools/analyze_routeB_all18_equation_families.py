#!/usr/bin/env python3
"""
Analiza la cohorte routeB_all18_20260422 cruzando:
- ecuaciones descubiertas en Stage 03
- zh_pred de Stage 02
- source_kind y variables fisicas congeladas en la tabla de referencia
- tier de validacion
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DISCOVERY_JSON = REPO_ROOT / "runs/routeB_all18_20260422/03_discover_bulk_equations/outputs/einstein_discovery_summary.json"
GEOMETRY_JSON = REPO_ROOT / "runs/routeB_all18_20260422/02_emergent_geometry_engine/emergent_geometry_summary.json"
REFERENCE_CSV = REPO_ROOT / "runs/community_ringdown_cohort/community_ringdown_reference_table.csv"
TIERS_CSV = REPO_ROOT / "runs/community_ringdown_cohort/community_ringdown_tiers.csv"


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


def load_rows() -> list[dict[str, object]]:
    discovery = json.loads(DISCOVERY_JSON.read_text())
    geometry = json.loads(GEOMETRY_JSON.read_text())
    reference = {row["event"]: row for row in _read_csv(REFERENCE_CSV)}
    tiers = {row["event"]: row for row in _read_csv(TIERS_CSV)}
    geometry_by_name = {row["name"]: row for row in geometry["systems"]}

    rows: list[dict[str, object]] = []
    for item in discovery["geometries"]:
        event = item["name"]
        ref = reference[event]
        geo = geometry_by_name[event]
        eq = item["results"]["R_equation"]["equation"]
        row = {
            "event": event,
            "equation": eq,
            "algebraic_class": classify_equation(eq),
            "r2": float(item["results"]["R_equation"]["r2"]),
            "source_kind": ref["source_kind"],
            "validation_tier": tiers[event]["validation_tier"],
            "M_final_Msun": float(ref["M_final_Msun"]) if ref["M_final_Msun"] else None,
            "chi_final": float(ref["chi_final"]) if ref["chi_final"] else None,
            "zh_pred": float(geo["zh_pred"]),
            "family": geo["family"],
            "family_mode": geo["family_classification_mode"],
            "family_top1_score": float(geo["family_top1_score"]),
            "family_margin": float(geo["family_margin"]),
        }
        rows.append(row)
    return rows


def fmt(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6f}"
    return str(value)


def main() -> None:
    rows = load_rows()
    rows.sort(key=lambda row: str(row["event"]))

    print("TABLE")
    print(
        "event\talgebraic_class\tr2\tsource_kind\tvalidation_tier\tM_final_Msun\tchi_final\tzh_pred\tequation"
    )
    for row in rows:
        print(
            "\t".join(
                [
                    fmt(row["event"]),
                    fmt(row["algebraic_class"]),
                    fmt(row["r2"]),
                    fmt(row["source_kind"]),
                    fmt(row["validation_tier"]),
                    fmt(row["M_final_Msun"]),
                    fmt(row["chi_final"]),
                    fmt(row["zh_pred"]),
                    fmt(row["equation"]),
                ]
            )
        )

    counts = Counter(row["algebraic_class"] for row in rows)
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["algebraic_class"])].append(row)

    print("\nAGGREGATE")
    print("algebraic_class\tn_events\tmean_r2\tmin_r2\tmax_r2\tsource_kind_counts\ttier_counts\tmean_M_final\tmean_chi\tmean_zh_pred")
    for algebraic_class, class_rows in sorted(grouped.items()):
        source_counts = Counter(str(row["source_kind"]) for row in class_rows)
        tier_counts = Counter(str(row["validation_tier"]) for row in class_rows)
        mean_r2 = sum(float(row["r2"]) for row in class_rows) / len(class_rows)
        min_r2 = min(float(row["r2"]) for row in class_rows)
        max_r2 = max(float(row["r2"]) for row in class_rows)
        mean_m = sum(float(row["M_final_Msun"]) for row in class_rows) / len(class_rows)
        mean_chi = sum(float(row["chi_final"]) for row in class_rows) / len(class_rows)
        mean_zh = sum(float(row["zh_pred"]) for row in class_rows) / len(class_rows)
        print(
            "\t".join(
                [
                    algebraic_class,
                    str(len(class_rows)),
                    f"{mean_r2:.6f}",
                    f"{min_r2:.6f}",
                    f"{max_r2:.6f}",
                    ",".join(f"{k}:{v}" for k, v in sorted(source_counts.items())),
                    ",".join(f"{k}:{v}" for k, v in sorted(tier_counts.items())),
                    f"{mean_m:.6f}",
                    f"{mean_chi:.6f}",
                    f"{mean_zh:.6f}",
                ]
            )
        )

    print("\nCROSSTABS")
    for key in ["source_kind", "validation_tier"]:
        bucket: dict[str, Counter[str]] = defaultdict(Counter)
        for row in rows:
            bucket[str(row[key])][str(row["algebraic_class"])] += 1
        print(key)
        for group_name, counter in sorted(bucket.items()):
            print(group_name, ",".join(f"{k}:{v}" for k, v in sorted(counter.items())))


if __name__ == "__main__":
    main()
