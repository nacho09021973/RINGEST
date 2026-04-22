#!/usr/bin/env python3
"""
Prueba de universalidad jerarquica del ansatz maestro sobre los 7 eventos
con ringdown congelado.
"""

from __future__ import annotations

import csv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MASTER_AUDIT_CSV = REPO_ROOT / "runs/routeB_all18_20260422/analysis/master_ansatz_audit.csv"
OUT_DIR = REPO_ROOT / "runs/routeB_all18_20260422/analysis"
OUT_CSV = OUT_DIR / "master_ansatz_universality.csv"

MODEL_A = "R ~ x2*(C - x4/x1) + g(x3), con g(x3) baja (cuadratica o lineal)"
MODEL_B = "Modelo A + deformacion moderada de mezcla x0/x3"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def classify_assignment(row: dict[str, str]) -> tuple[str, str]:
    status = row["ansatz_status"]
    if status == "base_plus_x3":
        return "A", "entra en el nucleo racional con correccion baja en x3"
    if status == "base_plus_x0x3":
        return "B", "requiere mezcla moderada x0/x3 ademas del nucleo"
    return "outside", "queda fuera de la familia maestra compacta"


def main() -> None:
    rows = _read_csv(MASTER_AUDIT_CSV)
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
        "model_A",
        "model_B",
        "assignment",
        "assignment_rationale",
    ]

    with OUT_CSV.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            assignment, rationale = classify_assignment(row)
            writer.writerow(
                {
                    "event": row["event"],
                    "equation_class": row["equation_class"],
                    "equation": row["equation"],
                    "r2": row["r2"],
                    "source_kind": row["source_kind"],
                    "M_final_Msun": row["M_final_Msun"],
                    "chi_final": row["chi_final"],
                    "zh_pred": row["zh_pred"],
                    "model_A": MODEL_A,
                    "model_B": MODEL_B,
                    "assignment": assignment,
                    "assignment_rationale": rationale,
                }
            )

    print(OUT_CSV)


if __name__ == "__main__":
    main()
