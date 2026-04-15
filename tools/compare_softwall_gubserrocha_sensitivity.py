#!/usr/bin/env python3
"""
compare_softwall_gubserrocha_sensitivity.py

Compare baseline reports from one-at-a-time sensitivity rails for the
preregistered soft_wall vs gubser_rocha experiment.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


REPO_ROOT = Path(__file__).resolve().parents[1]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Compare one-at-a-time sensitivity baseline reports.")
    ap.add_argument("--output-json", type=Path, required=True)
    ap.add_argument("--sensitivity-name", type=str, required=True, help="Name of the single variable under study, e.g. n_epochs")
    ap.add_argument(
        "--input",
        action="append",
        nargs=2,
        metavar=("LABEL", "BASELINE_REPORT_JSON"),
        required=True,
        help="Sensitivity label plus path to a baseline_report.json",
    )
    return ap.parse_args(argv)


def _load_report(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"baseline report not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid baseline report JSON at {path}: {exc}") from exc


def _one_at_a_time_verdict(rows: List[Dict[str, Any]]) -> str:
    values = [float(r["ba"]) for r in rows]
    if all(v >= 0.75 for v in values):
        return "SENSITIVITY_SURVIVES"
    if any(v >= 0.75 for v in values):
        return "SENSITIVITY_FRAGILE"
    return "NO_CONCLUSIVE_SEPARATION"


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    rows: List[Dict[str, Any]] = []
    for label, path_str in args.input:
        path = Path(path_str).resolve()
        report = _load_report(path)
        primary = report["primary_observable"]
        rows.append(
            {
                "label": label,
                "report_path": str(path),
                "ba": float(primary["value"]),
                "bootstrap_q025": float(primary["bootstrap"]["q025"]),
                "baseline_status": str(report.get("baseline_status")),
            }
        )

    verdict = _one_at_a_time_verdict(rows)
    payload = {
        "schema_version": "softwall-gubserrocha-sensitivity-v1",
        "created_at": _utc_now_iso(),
        "sensitivity_name": args.sensitivity_name,
        "n_reports": len(rows),
        "reports": rows,
        "aggregate": {
            "ba_min": min(r["ba"] for r in rows),
            "ba_max": max(r["ba"] for r in rows),
            "bootstrap_q025_min": min(r["bootstrap_q025"] for r in rows),
            "verdict": verdict,
        },
        "notes": [
            "This comparator assumes exactly one variable changed across inputs.",
            "It does not replace the final preregistered verdict aggregator.",
        ],
    }
    _write_json(args.output_json.resolve(), payload)
    print(f"[OK] sensitivity={args.sensitivity_name} verdict={verdict}")
    print(f"[OK] output: {args.output_json.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
