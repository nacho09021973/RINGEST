#!/usr/bin/env python3
"""
Materializa una clasificacion A/B/C de la cohorte real de Ruta B usando solo
artefactos ya presentes en el repo.

Politica aplicada:
  - A: ancla multipolo local + ancla de remanente materializada
  - B: ancla de remanente materializada, sin ancla multipolo suficiente
  - C: resto
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
COHORT_CSV = REPO_ROOT / "runs/community_ringdown_cohort/community_ringdown_cohort.csv"
QNM_LITERATURE_CSV = REPO_ROOT / "runs/qnm_dataset_literature/qnm_dataset.csv"
AUDIT_MULTIPOLE_CSV = REPO_ROOT / "runs/audit_envsum_v3/dataset_envsum/qnm_dataset.csv"
AUDIT_RUNS_DIR = REPO_ROOT / "runs/audit_envsum_v3/runs_sumabs"
OUT_DIR = REPO_ROOT / "runs/community_ringdown_cohort"
OUT_CSV = OUT_DIR / "community_ringdown_tiers.csv"
OUT_JSON = OUT_DIR / "community_ringdown_tiers.json"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def _has_value(row: dict[str, str], key: str) -> bool:
    return bool(str(row.get(key, "")).strip())


def main() -> None:
    cohort_rows = _read_csv(COHORT_CSV)
    qnm_rows = _read_csv(QNM_LITERATURE_CSV)
    audit_rows = _read_csv(AUDIT_MULTIPOLE_CSV) if AUDIT_MULTIPOLE_CSV.exists() else []

    remnant_anchor_events = {
        row["event"]
        for row in qnm_rows
        if _has_value(row, "M_final_Msun") and _has_value(row, "chi_final")
    }

    audit_counts = Counter(row["event"] for row in audit_rows)

    output_rows: list[dict[str, str]] = []
    for row in cohort_rows:
        event = row["event"]
        has_remnant_anchor = (
            event in remnant_anchor_events
            and _has_value(row, "M_final_Msun")
            and _has_value(row, "chi_final")
        )

        audit_poles = AUDIT_RUNS_DIR / event / "ringdown/poles_joint.json"
        n_audit_modes = audit_counts.get(event, 0)
        has_multipole_anchor = has_remnant_anchor and n_audit_modes > 1 and audit_poles.exists()

        if has_multipole_anchor:
            validation_tier = "A"
            tier_status = "verified_from_repo"
            tier_rationale = (
                f"remanente materializado en cohorte+qnm_dataset_literature; "
                f"ancla multipolo local en audit_envsum_v3 con {n_audit_modes} mode_rank "
                f"y poles_joint.json presente"
            )
            source_artifacts = [
                _rel(COHORT_CSV),
                _rel(QNM_LITERATURE_CSV),
                _rel(AUDIT_MULTIPOLE_CSV),
                _rel(audit_poles),
            ]
        elif has_remnant_anchor:
            validation_tier = "B"
            tier_status = "provisional"
            tier_rationale = (
                "remanente usable materializado en cohorte+qnm_dataset_literature; "
                "sin ancla multipolo local suficiente en los artefactos inspeccionados"
            )
            source_artifacts = [
                _rel(COHORT_CSV),
                _rel(QNM_LITERATURE_CSV),
            ]
        else:
            validation_tier = "C"
            tier_status = "provisional"
            tier_rationale = (
                "sin remanente usable materializado de forma suficiente en los artefactos inspeccionados"
            )
            source_artifacts = [_rel(COHORT_CSV)]

        output_rows.append(
            {
                "event": event,
                "validation_tier": validation_tier,
                "tier_status": tier_status,
                "tier_rationale": tier_rationale,
                "has_multipole_anchor": "yes" if has_multipole_anchor else "no",
                "has_remnant_anchor": "yes" if has_remnant_anchor else "no",
                "source_artifacts": ";".join(source_artifacts),
            }
        )

    with OUT_CSV.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "event",
                "validation_tier",
                "tier_status",
                "tier_rationale",
                "has_multipole_anchor",
                "has_remnant_anchor",
                "source_artifacts",
            ],
        )
        writer.writeheader()
        writer.writerows(output_rows)

    with OUT_JSON.open("w") as fh:
        json.dump(
            {
                "policy": {
                    "A": "multipole_anchor_and_remnant_anchor",
                    "B": "remnant_anchor_only",
                    "C": "no_sufficient_remnant_anchor",
                },
                "artifacts_used": [
                    _rel(COHORT_CSV),
                    _rel(QNM_LITERATURE_CSV),
                    _rel(AUDIT_MULTIPOLE_CSV) if AUDIT_MULTIPOLE_CSV.exists() else "",
                ],
                "rows": output_rows,
            },
            fh,
            indent=2,
        )


if __name__ == "__main__":
    main()
