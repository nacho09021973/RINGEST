#!/usr/bin/env python3
"""
Consolida una tabla final portable para la cohorte comunitaria de Ruta B
sin depender de reruns externos.
"""

from __future__ import annotations

import configparser
import csv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = REPO_ROOT / "runs/community_ringdown_cohort"

COHORT_CSV = RUNS_DIR / "community_ringdown_cohort.csv"
TIERS_CSV = RUNS_DIR / "community_ringdown_tiers.csv"
QNM_LITERATURE_CSV = REPO_ROOT / "runs/qnm_dataset_literature/qnm_dataset.csv"
PILOT_PARSED_CSV = RUNS_DIR / "pilot_ringdown_parsed/ringdown_intermediate.csv"
T0_SCAN_PARSED_CSV = RUNS_DIR / "pilot_ringdown_t0_scan_parsed/ringdown_intermediate.csv"
EXPANDED_PARSED_CSV = RUNS_DIR / "pilot_ringdown_expanded_parsed/ringdown_intermediate.csv"

REFERENCE_TABLE_CSV = RUNS_DIR / "community_ringdown_reference_table.csv"
README_MD = RUNS_DIR / "README_reference_table.md"

PILOT_INI = {
    "GW150914": REPO_ROOT / "runs/community_ringdown_cohort/pilot_ringdown/GW150914_ringdown.ini",
}

SINGLE_PASS_INI = {
    "GW170823": REPO_ROOT / "runs/community_ringdown_cohort/pilot_ringdown/GW170823_ringdown.ini",
    "GW190421_213856": REPO_ROOT
    / "runs/community_ringdown_cohort/pilot_ringdown/GW190421_213856_ringdown.ini",
    "GW190503_185404": REPO_ROOT
    / "runs/community_ringdown_cohort/pilot_ringdown/GW190503_185404_ringdown.ini",
    "GW190828_063405": REPO_ROOT
    / "runs/community_ringdown_cohort/pilot_ringdown/GW190828_063405_ringdown.ini",
}

SELECTED_T0 = {
    "GW170104": {
        "delta_t": "+0.004 s",
        "scan_event": "GW170104_t0_p0p004",
        "ini": REPO_ROOT
        / "runs/community_ringdown_cohort/pilot_ringdown/GW170104_t0_p0p004_ringdown.ini",
    },
    "GW170814": {
        "delta_t": "-0.002 s",
        "scan_event": "GW170814_t0_m0p002",
        "ini": REPO_ROOT
        / "runs/community_ringdown_cohort/pilot_ringdown/GW170814_t0_m0p002_ringdown.ini",
    },
}

OUTPUT_COLUMNS = [
    "event",
    "validation_tier",
    "tier_status",
    "tier_rationale",
    "source_kind",
    "source_artifacts",
    "selected_t0",
    "selected_duration",
    "f_ringdown_hz",
    "f_ringdown_hz_q05",
    "f_ringdown_hz_q95",
    "damping_hz",
    "damping_hz_q05",
    "damping_hz_q95",
    "tau_ms",
    "tau_ms_q05",
    "tau_ms_q95",
    "M_final_Msun",
    "M_final_Msun_q05",
    "M_final_Msun_q95",
    "chi_final",
    "chi_final_q05",
    "chi_final_q95",
    "fit_status",
    "notes",
]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT))


def _read_ini_target(path: Path) -> tuple[str, str]:
    cp = configparser.ConfigParser(inline_comment_prefixes=(";", "#"))
    cp.read(path)
    return cp["target"]["t0"], cp["target"]["duration"]


def _empty_row() -> dict[str, str]:
    return {key: "" for key in OUTPUT_COLUMNS}


def _copy_fields(dst: dict[str, str], src: dict[str, str], fields: list[str]) -> None:
    for field in fields:
        dst[field] = src.get(field, "")


def _literature_matches(cohort_row: dict[str, str], qnm_row: dict[str, str]) -> bool:
    fields = ["freq_hz", "damping_hz", "tau_ms", "M_final_Msun", "chi_final"]
    return all(cohort_row.get(field, "") == qnm_row.get(field, "") for field in fields)


def _detect_bias_against_literature(reference_row: dict[str, str], fit_row: dict[str, str]) -> list[str]:
    biased: list[str] = []

    def rel_diff(reference_field: str, fit_field: str) -> float | None:
        try:
            ref = float(reference_row[reference_field])
            val = float(fit_row[fit_field])
        except (KeyError, TypeError, ValueError):
            return None
        if ref == 0:
            return None
        return abs(val - ref) / abs(ref)

    for reference_field, fit_field, label in [
        ("freq_hz", "f_ringdown_hz", "f"),
        ("damping_hz", "damping_hz", "damping"),
        ("M_final_Msun", "M_final_Msun", "M_final"),
    ]:
        diff = rel_diff(reference_field, fit_field)
        if diff is not None and diff > 0.20:
            biased.append(label)

    try:
        ref_chi = float(reference_row["chi_final"])
        fit_chi = float(fit_row["chi_final"])
        if abs(fit_chi - ref_chi) > 0.15:
            biased.append("chi")
    except (KeyError, TypeError, ValueError):
        pass

    return biased


def build_reference_table() -> list[dict[str, str]]:
    cohort_rows = _read_csv(COHORT_CSV)
    tiers_by_event = {row["event"]: row for row in _read_csv(TIERS_CSV)}
    qnm_by_event = {row["event"]: row for row in _read_csv(QNM_LITERATURE_CSV)}
    pilot_by_event = {row["event"]: row for row in _read_csv(PILOT_PARSED_CSV)}
    expanded_by_event = {row["event"]: row for row in _read_csv(EXPANDED_PARSED_CSV)}
    scan_by_event = {row["event"]: row for row in _read_csv(T0_SCAN_PARSED_CSV)}

    rows: list[dict[str, str]] = []
    for cohort_row in cohort_rows:
        event = cohort_row["event"]
        tier_row = tiers_by_event[event]
        qnm_row = qnm_by_event.get(event)
        out = _empty_row()

        out["event"] = event
        out["validation_tier"] = tier_row["validation_tier"]
        out["tier_status"] = tier_row["tier_status"]
        out["tier_rationale"] = tier_row["tier_rationale"]

        notes: list[str] = []
        artifacts = [_rel(TIERS_CSV)]

        if event in SELECTED_T0:
            selected = SELECTED_T0[event]
            scan_row = scan_by_event[selected["scan_event"]]
            selected_t0, selected_duration = _read_ini_target(selected["ini"])
            out["source_kind"] = "community_ringdown_t0_selected"
            out["source_artifacts"] = ";".join(
                artifacts
                + [
                    _rel(T0_SCAN_PARSED_CSV),
                    _rel(selected["ini"]),
                ]
            )
            out["selected_t0"] = selected_t0
            out["selected_duration"] = selected_duration
            _copy_fields(
                out,
                scan_row,
                [
                    "f_ringdown_hz",
                    "f_ringdown_hz_q05",
                    "f_ringdown_hz_q95",
                    "damping_hz",
                    "damping_hz_q05",
                    "damping_hz_q95",
                    "tau_ms",
                    "tau_ms_q05",
                    "tau_ms_q95",
                    "M_final_Msun",
                    "M_final_Msun_q05",
                    "M_final_Msun_q95",
                    "chi_final",
                    "chi_final_q05",
                    "chi_final_q95",
                    "fit_status",
                ],
            )
            notes.append(
                f"seleccion operativa congelada hoy: barrido local de t0, delta_t={selected['delta_t']}"
            )
            notes.append("valores tomados de ringdown_intermediate del barrido de t0")
            if event == "GW170104":
                notes.append("resultado aun sesgado frente a literatura; mantener lectura operativamente provisional")
        elif event in PILOT_INI and event in pilot_by_event:
            pilot_row = pilot_by_event[event]
            selected_t0, selected_duration = _read_ini_target(PILOT_INI[event])
            out["source_kind"] = "community_ringdown_pilot"
            out["source_artifacts"] = ";".join(
                artifacts
                + [
                    _rel(PILOT_PARSED_CSV),
                    _rel(PILOT_INI[event]),
                ]
            )
            out["selected_t0"] = selected_t0
            out["selected_duration"] = selected_duration
            _copy_fields(
                out,
                pilot_row,
                [
                    "f_ringdown_hz",
                    "f_ringdown_hz_q05",
                    "f_ringdown_hz_q95",
                    "damping_hz",
                    "damping_hz_q05",
                    "damping_hz_q95",
                    "tau_ms",
                    "tau_ms_q05",
                    "tau_ms_q95",
                    "M_final_Msun",
                    "M_final_Msun_q05",
                    "M_final_Msun_q95",
                    "chi_final",
                    "chi_final_q05",
                    "chi_final_q95",
                    "fit_status",
                ],
            )
            notes.append("valores tomados del piloto ringdown ya congelado")
        elif event in SINGLE_PASS_INI and event in expanded_by_event:
            single_pass_row = expanded_by_event[event]
            selected_t0, selected_duration = _read_ini_target(SINGLE_PASS_INI[event])
            out["source_kind"] = "community_ringdown_single_pass"
            out["source_artifacts"] = ";".join(
                artifacts
                + [
                    _rel(EXPANDED_PARSED_CSV),
                    _rel(SINGLE_PASS_INI[event]),
                ]
            )
            out["selected_t0"] = selected_t0
            out["selected_duration"] = selected_duration
            _copy_fields(
                out,
                single_pass_row,
                [
                    "f_ringdown_hz",
                    "f_ringdown_hz_q05",
                    "f_ringdown_hz_q95",
                    "damping_hz",
                    "damping_hz_q05",
                    "damping_hz_q95",
                    "tau_ms",
                    "tau_ms_q05",
                    "tau_ms_q95",
                    "M_final_Msun",
                    "M_final_Msun_q05",
                    "M_final_Msun_q95",
                    "chi_final",
                    "chi_final_q05",
                    "chi_final_q95",
                    "fit_status",
                ],
            )
            notes.append("pasada unica H1 ejecutada hoy con patron base del piloto comunitario")
            notes.append("sin optimizacion adicional de t0 ni duration")
            if qnm_row is not None:
                biased_fields = _detect_bias_against_literature(qnm_row, single_pass_row)
                if biased_fields:
                    notes.append(
                        "comparacion rapida con literatura: sesgo visible en " + "/".join(biased_fields)
                    )
        elif qnm_row is not None:
            out["source_kind"] = "literature_anchor"
            if tier_row["tier_status"] == "provisional":
                out["source_kind"] = "provisional"
            out["source_artifacts"] = ";".join(
                artifacts
                + [
                    _rel(COHORT_CSV),
                    _rel(QNM_LITERATURE_CSV),
                ]
            )
            out["f_ringdown_hz"] = cohort_row["freq_hz"]
            out["damping_hz"] = cohort_row["damping_hz"]
            out["tau_ms"] = cohort_row["tau_ms"]
            out["M_final_Msun"] = cohort_row["M_final_Msun"]
            out["chi_final"] = cohort_row["chi_final"]
            notes.append("valores anclados a literatura ya materializada en community_ringdown_cohort")
            if _literature_matches(cohort_row, qnm_row):
                notes.append("coincide con qnm_dataset_literature en freq/damping/tau/M_final/chi_final")
            else:
                notes.append("advertencia: discrepancia entre community_ringdown_cohort y qnm_dataset_literature")
            notes.append("sin selected_t0 ni duration congelados para reutilizacion offline")
            notes.append("sin cuantiles q05/q95 materializados en las fuentes de literatura usadas hoy")
        else:
            out["source_kind"] = "no_frozen_value"
            out["source_artifacts"] = ";".join(artifacts + [_rel(COHORT_CSV)])
            notes.append("sin valor congelado suficiente en los artefactos inspeccionados")

        if tier_row["tier_status"] == "provisional" and out["source_kind"] != "provisional":
            notes.append("evento con tier provisional segun community_ringdown_tiers")

        out["notes"] = "; ".join(notes)
        rows.append(out)

    return rows


def write_reference_table(rows: list[dict[str, str]]) -> None:
    with REFERENCE_TABLE_CSV.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def write_readme(rows: list[dict[str, str]]) -> None:
    pilot_events = [row["event"] for row in rows if row["source_kind"] == "community_ringdown_pilot"]
    t0_events = [row["event"] for row in rows if row["source_kind"] == "community_ringdown_t0_selected"]
    single_pass_events = [
        row["event"] for row in rows if row["source_kind"] == "community_ringdown_single_pass"
    ]
    provisional_events = [row["event"] for row in rows if row["tier_status"] == "provisional"]

    lines = [
        "# Community Ringdown Reference Table",
        "",
        "## Proposito",
        "",
        "Esta tabla congela una referencia final, portable y versionable por evento para Ruta B.",
        "Se puede reutilizar manana en otro ordenador sin reinstalar ni rerunear `ringdown`, `pyRingGW` ni otros ecosistemas externos.",
        "",
        "Artefacto principal: `runs/community_ringdown_cohort/community_ringdown_reference_table.csv`.",
        "",
        "## Politica A/B/C Reutilizada",
        "",
        "- La clasificacion se toma tal cual de `runs/community_ringdown_cohort/community_ringdown_tiers.csv`.",
        "- `A`: ancla multipolo local + remanente materializado.",
        "- `B`: remanente materializado pero sin ancla multipolo suficiente en los artefactos inspeccionados.",
        "- `C`: sin remanente suficiente. Hoy no aparece ningun caso en la cohorte congelada.",
        "",
        "## Significado de `source_kind`",
        "",
        "- `community_ringdown_pilot`: valor tomado del piloto `ringdown` ya parseado.",
        "- `community_ringdown_t0_selected`: valor tomado del barrido de `t0` ya parseado y seleccionado hoy.",
        "- `community_ringdown_single_pass`: valor tomado de una unica corrida H1 ejecutada hoy con el patron base del piloto.",
        "- `literature_anchor`: valor tomado de la cohorte/literatura materializada y usado como ancla congelada.",
        "- `provisional`: valor de literatura usado para eventos cuyo tier sigue siendo provisional.",
        "- `no_frozen_value`: no hay valor congelado suficiente; los campos quedan vacios.",
        "",
        "## Criterio De Seleccion",
        "",
        "- Prioridad 1: decisiones operativas congeladas hoy.",
        "- Prioridad 2: piloto `ringdown` ya materializado.",
        "- Prioridad 3: ancla de literatura ya materializada en el repo.",
        "- Si una fuente no trae cuantiles `q05/q95` o `selected_t0/duration`, esos campos quedan vacios y se explica en `notes`.",
        "",
        "## Casos Con `ringdown` Piloto Directo",
        "",
        f"- {', '.join(pilot_events) if pilot_events else 'ninguno'}",
        "",
        "## Casos Con `ringdown` y `t0` Seleccionado",
        "",
        "- GW170104 usa `delta_t = +0.004 s`.",
        "- GW170814 usa `delta_t = -0.002 s`.",
        "",
        "## Casos Con `ringdown` De Una Sola Pasada Hoy",
        "",
        f"- {', '.join(single_pass_events) if single_pass_events else 'ninguno'}",
        "",
        "## Casos Provisionales",
        "",
        f"- {', '.join(provisional_events) if provisional_events else 'ninguno'}",
        "",
        "## Reutilizacion Offline Manana",
        "",
        "- Usar `community_ringdown_reference_table.csv` como tabla canonica de entrada por evento.",
        "- No rerunear `ringdown` para recuperar estos valores; ya estan congelados en el CSV.",
        "- Consultar `source_kind`, `source_artifacts` y `notes` antes de promover un evento a uso mas fuerte downstream.",
        "",
        "## Cobertura De Hoy",
        "",
        f"- Eventos con piloto directo congelado: {len(pilot_events)}.",
        f"- Eventos con `t0` seleccionado congelado: {len(t0_events)}.",
        f"- Eventos con una sola pasada H1 hoy: {len(single_pass_events)}.",
        f"- Eventos provisionales segun tiers: {len(provisional_events)}.",
    ]

    README_MD.write_text("\n".join(lines) + "\n")


def main() -> None:
    rows = build_reference_table()
    write_reference_table(rows)
    write_readme(rows)


if __name__ == "__main__":
    main()
