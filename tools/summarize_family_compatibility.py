#!/usr/bin/env python3
"""
summarize_family_compatibility.py  —  lector de emergent_geometry_summary.json.

Lee el JSON que produce `02_emergent_geometry_engine.py --mode inference` y
emite, por evento, un resumen epistemológicamente honesto del ranking de
compatibilidad familia↔dato. No hace inferencia nueva, no toca el modelo.

Salidas:
  - stdout: bloque legible por evento
  - opcional: CSV plano con una fila por evento y columnas clave

Uso:
  python3 tools/summarize_family_compatibility.py \\
      <run_dir_o_summary_json> [--csv out.csv]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def _resolve_summary(path_arg: str) -> Path:
    p = Path(path_arg).expanduser().resolve()
    if p.is_file():
        return p
    if p.is_dir():
        cand = p / "emergent_geometry_summary.json"
        if cand.is_file():
            return cand
        cand2 = p / "02_emergent_geometry_engine" / "emergent_geometry_summary.json"
        if cand2.is_file():
            return cand2
    sys.exit(f"[ERROR] no encuentro emergent_geometry_summary.json en {path_arg}")


def _format_event_block(entry: Dict[str, Any]) -> str:
    name = entry.get("name", "?")
    raw = entry.get("family_raw_pred", entry.get("family_raw_name", "?"))
    top2 = entry.get("family_top2_name", "?")
    top1 = entry.get("family_top1_score", float("nan"))
    top2s = entry.get("family_top2_score", float("nan"))
    margin = entry.get("family_margin", float("nan"))
    entropy = entry.get("family_entropy", float("nan"))
    mode = entry.get("family_classification_mode", "?")
    abstained = entry.get("family_pred_was_abstained", True)
    reason = entry.get("family_abstention_reason", "unknown")
    bank_status = entry.get("family_bank_status", "unknown")
    bank_active = entry.get("family_bank_active_families", [])
    note = entry.get("family_interpretation_note", "")
    scores = entry.get("family_scores", {})
    scores_active = entry.get("family_scores_active", {}) or {}

    # Ranking completo ordenado descendente.
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    ranked_str = ", ".join(f"{k}={v:.3f}" for k, v in ranked[:6])
    if scores_active and set(scores_active.keys()) != set(scores.keys()):
        ranked_active = sorted(scores_active.items(), key=lambda kv: kv[1], reverse=True)
        ranked_active_str = ", ".join(f"{k}={v:.3f}" for k, v in ranked_active)
    else:
        ranked_active_str = "(coincide con ranking completo)"

    lines = [
        f"── {name} ──",
        f"  top1        : {raw}  (score={top1:.3f})",
        f"  top2        : {top2}  (score={top2s:.3f})",
        f"  margin      : {margin:.3f}",
        f"  entropy     : {entropy:.3f}",
        f"  mode        : {mode}  (abstained={abstained}, reason={reason})",
        f"  bank        : {bank_status}  active={bank_active}",
        f"  ranking     : {ranked_str}" + (" ..." if len(ranked) > 6 else ""),
        f"  ranking_act : {ranked_active_str}",
        f"  nota        : {note}",
    ]
    return "\n".join(lines)


def _csv_rows(entries: List[Dict[str, Any]]):
    cols = [
        "name",
        "family_raw_pred", "family_top1_score",
        "family_top2_name", "family_top2_score",
        "family_margin", "family_entropy",
        "family_classification_mode",
        "family_pred_confident", "family_pred_was_abstained",
        "family_abstention_reason",
        "family_bank_status", "family_bank_active_families",
        "family_scores_active_json",
        "family_interpretation_note",
    ]
    yield cols
    for e in entries:
        yield [
            e.get("name", ""),
            e.get("family_raw_pred", e.get("family_raw_name", "")),
            e.get("family_top1_score", ""),
            e.get("family_top2_name", ""),
            e.get("family_top2_score", ""),
            e.get("family_margin", ""),
            e.get("family_entropy", ""),
            e.get("family_classification_mode", ""),
            e.get("family_pred_confident", ""),
            e.get("family_pred_was_abstained", ""),
            e.get("family_abstention_reason", ""),
            e.get("family_bank_status", ""),
            "|".join(e.get("family_bank_active_families", []) or []),
            json.dumps(e.get("family_scores_active", {}), sort_keys=True),
            e.get("family_interpretation_note", ""),
        ]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Lee emergent_geometry_summary.json y emite por evento un resumen "
            "epistemológicamente honesto del ranking de compatibilidad por familia."
        )
    )
    ap.add_argument(
        "path",
        help=(
            "run_dir de Stage 02 inference, o ruta directa a "
            "emergent_geometry_summary.json."
        ),
    )
    ap.add_argument("--csv", type=str, default=None, help="CSV de salida opcional.")
    args = ap.parse_args(argv)

    summary_path = _resolve_summary(args.path)
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    systems: List[Dict[str, Any]] = data.get("systems", []) or []

    print(f"# summary   : {summary_path}")
    print(f"# n_systems : {len(systems)}")
    print(f"# mode      : {data.get('mode','?')}")
    print(f"# checkpoint: {data.get('checkpoint','?')}")
    print()

    if not systems:
        print("[WARN] summary no contiene 'systems'; nada que resumir.")
        return 0

    # Advertencia global única cuando el banco es single-family.
    first = systems[0]
    bank_status = first.get("family_bank_status", "unknown")
    bank_active = first.get("family_bank_active_families", [])
    if bank_status == "single_family_bank":
        print(
            "[GLOBAL] checkpoint entrenado con banco single-family "
            f"({bank_active!r}). El 'ranking entre familias' solo es ruido del "
            "head softmax; lo único interpretable por evento es compatibilidad "
            "con la familia activa."
        )
        print()

    for e in systems:
        print(_format_event_block(e))
        print()

    if args.csv:
        out_csv = Path(args.csv).expanduser().resolve()
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        with out_csv.open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            for row in _csv_rows(systems):
                w.writerow(row)
        print(f"[OK] csv: {out_csv}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
