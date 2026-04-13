#!/usr/bin/env python3
"""
Minimal BASURIN experiment for auditable multi-event baseline vs premium comparison.
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools import run_baseline_vs_premium_experiment as single


STAGE_NAME = "baseline_vs_premium_multievent"
SCRIPT_VERSION = "run_baseline_vs_premium_multievent.py v0.1"


def _select_event_h5s(input_dir: Path, event_limit: int | None) -> list[Path]:
    h5_files = sorted(input_dir.glob("*.h5"))
    if event_limit is None:
        return [path.resolve(strict=False) for path in h5_files]
    if len(h5_files) < event_limit:
        raise FileNotFoundError(
            f"Requested {event_limit} canonical events but only found {len(h5_files)} in {input_dir}"
        )
    return [path.resolve(strict=False) for path in h5_files[:event_limit]]


def _run_premium_estimator(
    *,
    runs_root: Path,
    top_run_id: str,
    event_id: str,
    rail_name: str,
    boundary_h5: Path,
    logs_dir: Path,
) -> dict[str, Any]:
    rail_run_id = f"{top_run_id}/experiment/{STAGE_NAME}/rails/{event_id}/{rail_name}"
    cmd = [
        sys.executable,
        str(single.PREMIUM_ESTIMATOR_SCRIPT),
        "--run-id",
        rail_run_id,
        "--event-id",
        f"{event_id}__{rail_name}",
        "--baseline-boundary-h5",
        str(boundary_h5),
        "--runs-dir",
        str(runs_root),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    (logs_dir / f"{event_id}__{rail_name}.stdout.log").write_text(proc.stdout, encoding="utf-8")
    (logs_dir / f"{event_id}__{rail_name}.stderr.log").write_text(proc.stderr, encoding="utf-8")

    rail_stage_dir = runs_root / rail_run_id / "premium_estimator"
    stage_summary_path = rail_stage_dir / "stage_summary.json"
    estimate_path = rail_stage_dir / "outputs" / "premium_estimate.json"
    provenance_path = rail_stage_dir / "outputs" / "provenance.json"

    if proc.returncode != 0:
        raise RuntimeError(
            f"event={event_id} rail={rail_name} premium_estimator failed: {(proc.stderr or proc.stdout).strip()}"
        )
    for required in (stage_summary_path, estimate_path, provenance_path):
        if not required.exists():
            raise RuntimeError(f"event={event_id} rail={rail_name} missing expected artifact: {required}")

    stage_summary = json.loads(stage_summary_path.read_text(encoding="utf-8"))
    estimate = json.loads(estimate_path.read_text(encoding="utf-8"))
    signature = {
        "stage_status": stage_summary.get("status"),
        "estimate_status": estimate.get("status"),
        "backend_enabled": bool(estimate.get("summary_metrics", {}).get("backend_enabled", False)),
        "is_placeholder": bool(estimate.get("summary_metrics", {}).get("is_placeholder", True)),
        "n_features": int(estimate.get("summary_metrics", {}).get("n_features", 0)),
        "signal_class": estimate.get("summary_metrics", {}).get("signal_class"),
        "compute_ran": bool(estimate.get("summary_metrics", {}).get("compute_ran", False)),
        "usable_signal": estimate.get("status") == "PASS",
    }
    return {
        "command": cmd,
        "event_id": event_id,
        "input_h5": str(boundary_h5),
        "stage_dir": str(rail_stage_dir),
        "stage_summary_path": str(stage_summary_path),
        "estimate_path": str(estimate_path),
        "provenance_path": str(provenance_path),
        "stage_summary": stage_summary,
        "estimate": estimate,
        "signature": signature,
    }


def _compute_aggregate_verdict(per_event_payload: dict[str, Any]) -> tuple[dict[str, Any], str, str]:
    verdict_counts = {"NO_ADVANTAGE": 0, "LIMITED_ADVANTAGE": 0, "CLEAR_ADVANTAGE": 0}
    premium_control_separation_count = 0
    baseline_control_separation_count = 0
    premium_null_reject_count = 0
    premium_signal_class_taxonomy_count = 0

    event_rows = []
    for event_id, event_payload in per_event_payload["events"].items():
        verdict = event_payload["verdict"]
        verdict_counts[verdict] += 1
        cmp_metrics = event_payload["comparison_metrics"]["comparative_metrics"]
        if cmp_metrics["premium_control_signature_distinct"]:
            premium_control_separation_count += 1
        if cmp_metrics["baseline_control_signature_distinct"]:
            baseline_control_separation_count += 1
        if cmp_metrics["premium_null_rejects"]:
            premium_null_reject_count += 1
        if cmp_metrics["premium_has_explicit_class_taxonomy"]:
            premium_signal_class_taxonomy_count += 1
        event_rows.append(
            {
                "event_id": event_id,
                "verdict": verdict,
                "baseline_control_signature_distinct": cmp_metrics["baseline_control_signature_distinct"],
                "premium_control_signature_distinct": cmp_metrics["premium_control_signature_distinct"],
                "premium_null_rejects": cmp_metrics["premium_null_rejects"],
                "premium_signal_classes": cmp_metrics["premium_signal_classes"],
            }
        )

    n_events = per_event_payload["n_events"]
    majority_threshold = math.ceil(n_events / 2)

    if verdict_counts["CLEAR_ADVANTAGE"] >= majority_threshold and verdict_counts["NO_ADVANTAGE"] == 0:
        aggregate_verdict = "CLEAR_ADVANTAGE"
        aggregate_reason = "clear advantage appears in a majority of the subcohort with no no-advantage events"
    elif verdict_counts["LIMITED_ADVANTAGE"] + verdict_counts["CLEAR_ADVANTAGE"] >= majority_threshold:
        aggregate_verdict = "LIMITED_ADVANTAGE"
        aggregate_reason = "premium shows at least limited advantage in a majority of the subcohort"
    else:
        aggregate_verdict = "NO_ADVANTAGE"
        aggregate_reason = "premium does not sustain even limited advantage across a majority of the subcohort"

    payload = {
        "schema_version": "baseline-vs-premium-multievent-0.1",
        "n_events": n_events,
        "event_selection_rule": per_event_payload["event_selection_rule"],
        "events": event_rows,
        "aggregate_metrics": {
            "verdict_counts": verdict_counts,
            "premium_control_separation_count": premium_control_separation_count,
            "baseline_control_separation_count": baseline_control_separation_count,
            "premium_null_reject_count": premium_null_reject_count,
            "premium_signal_class_taxonomy_count": premium_signal_class_taxonomy_count,
            "majority_threshold": majority_threshold,
        },
        "aggregate_verdict_rules": {
            "CLEAR_ADVANTAGE": "clear advantage in at least ceil(n_events/2) events and zero no-advantage events",
            "LIMITED_ADVANTAGE": "limited or clear advantage in at least ceil(n_events/2) events, but clear-advantage rule not met",
            "NO_ADVANTAGE": "otherwise",
        },
        "verdict": aggregate_verdict,
        "verdict_reason": aggregate_reason,
    }
    return payload, aggregate_verdict, aggregate_reason


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run auditable multi-event baseline vs premium BASURIN experiment.")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--runs-root", type=Path, default=single.RUNS_ROOT_DEFAULT)
    ap.add_argument("--canonical-input-dir", type=Path, default=single.CANONICAL_INPUT_DIR_DEFAULT)
    ap.add_argument("--event-limit", type=int, default=None)
    return ap


def main() -> int:
    args = build_parser().parse_args()

    runs_root = Path(args.runs_root).resolve(strict=False)
    canonical_input_dir = Path(args.canonical_input_dir).resolve(strict=False)
    stage_dir = runs_root / args.run_id / "experiment" / STAGE_NAME
    outputs_dir = stage_dir / "outputs"
    inputs_dir = stage_dir / "inputs"
    logs_dir = stage_dir / "logs"

    if args.event_limit is not None and args.event_limit < 1:
        print("ERROR: --event-limit must be >= 1", file=sys.stderr)
        return 2
    if not single.PREMIUM_ESTIMATOR_SCRIPT.exists():
        print(f"ERROR: missing premium estimator script: {single.PREMIUM_ESTIMATOR_SCRIPT}", file=sys.stderr)
        return 2
    if not canonical_input_dir.exists():
        print(f"ERROR: canonical input dir not found: {canonical_input_dir}", file=sys.stderr)
        return 2
    if outputs_dir.exists():
        print(f"ERROR: output directory already exists: {outputs_dir}", file=sys.stderr)
        return 2

    try:
        selected_h5s = _select_event_h5s(canonical_input_dir, args.event_limit)
    except Exception as exc:
        stage_dir.mkdir(parents=True, exist_ok=True)
        single._write_json_atomic(stage_dir / "stage_summary.json", {
            "created_at": single._utc_now_iso(),
            "stage_name": STAGE_NAME,
            "status": "FAIL",
            "event_id": None,
            "n_inputs": 0,
            "n_outputs": 0,
            "warnings": [],
            "blocking_reason": str(exc),
            "script": SCRIPT_VERSION,
        })
        single._write_json_atomic(stage_dir / "manifest.json", {
            "created_at": single._utc_now_iso(),
            "stage": STAGE_NAME,
            "script": SCRIPT_VERSION,
            "parameters": {
                "run_id": args.run_id,
                "canonical_input_dir": str(canonical_input_dir),
                "event_limit": args.event_limit,
            },
            "status": "FAIL",
        })
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    build_feature_vector = single._load_stage02_feature_builder(None)
    stage_dir.mkdir(parents=True, exist_ok=True)
    inputs_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    per_event_events: dict[str, Any] = {}
    all_rail_inputs: dict[str, dict[str, str]] = {}
    premium_commands: dict[str, dict[str, list[str]]] = {}

    try:
        for event_h5 in selected_h5s:
            event_id = event_h5.stem.replace("__ringdown", "")
            event_input_dir = inputs_dir / event_id
            event_input_dir.mkdir(parents=True, exist_ok=True)

            rail_inputs: dict[str, Path] = {}
            baseline_results: dict[str, Any] = {}
            premium_results: dict[str, Any] = {}

            for rail_name in single.EXPECTED_RAILS:
                rail_h5 = event_input_dir / f"{event_id}__{rail_name}.h5"
                single._copy_h5_with_rail(event_h5, rail_h5, rail_name)
                rail_inputs[rail_name] = rail_h5

            for rail_name in single.EXPECTED_RAILS:
                baseline_results[rail_name] = single._compute_baseline_signature(build_feature_vector, rail_inputs[rail_name])
                premium_results[rail_name] = _run_premium_estimator(
                    runs_root=runs_root,
                    top_run_id=args.run_id,
                    event_id=event_id,
                    rail_name=rail_name,
                    boundary_h5=rail_inputs[rail_name],
                    logs_dir=logs_dir,
                )

            comparison_metrics, verdict, verdict_reason = single._compute_comparison_metrics(
                event_id=event_id,
                baseline_results=baseline_results,
                premium_results=premium_results,
            )

            per_event_events[event_id] = {
                "source_h5": str(event_h5),
                "rails": list(single.EXPECTED_RAILS),
                "baseline": {
                    rail: baseline_results[rail]["signature"]
                    for rail in single.EXPECTED_RAILS
                },
                "premium": {
                    rail: premium_results[rail]["signature"]
                    for rail in single.EXPECTED_RAILS
                },
                "comparison_metrics": comparison_metrics,
                "verdict": verdict,
                "verdict_reason": verdict_reason,
            }
            all_rail_inputs[event_id] = {rail: str(path) for rail, path in rail_inputs.items()}
            premium_commands[event_id] = {rail: premium_results[rail]["command"] for rail in single.EXPECTED_RAILS}
    except Exception as exc:
        stage_summary = {
            "created_at": single._utc_now_iso(),
            "stage_name": STAGE_NAME,
            "status": "FAIL",
            "event_id": None,
            "n_inputs": len(selected_h5s),
            "n_outputs": 0,
            "warnings": [],
            "blocking_reason": str(exc),
            "script": SCRIPT_VERSION,
        }
        manifest = {
            "created_at": single._utc_now_iso(),
            "stage": STAGE_NAME,
            "script": SCRIPT_VERSION,
            "parameters": {
                "run_id": args.run_id,
                "canonical_input_dir": str(canonical_input_dir),
                "event_limit": args.event_limit,
            },
            "inputs": {
                "selected_events": [str(path) for path in selected_h5s],
            },
            "outputs": {
                "logs_dir": str(logs_dir),
                "stage_summary_json": str(stage_dir / "stage_summary.json"),
            },
            "status": "FAIL",
        }
        single._write_json_atomic(stage_dir / "stage_summary.json", stage_summary)
        single._write_json_atomic(stage_dir / "manifest.json", manifest)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    outputs_dir.mkdir(parents=True, exist_ok=True)
    per_event_payload = {
        "schema_version": "baseline-vs-premium-per-event-0.1",
        "n_events": len(selected_h5s),
        "event_selection_rule": {
            "strategy": "first_n_sorted_h5",
            "event_limit": args.event_limit,
            "source_dir": str(canonical_input_dir),
            "selected_event_ids": sorted(per_event_events.keys()),
        },
        "events": per_event_events,
    }
    single._write_json_atomic(outputs_dir / "per_event_comparison.json", per_event_payload)

    aggregate_payload, aggregate_verdict, aggregate_reason = _compute_aggregate_verdict(per_event_payload)
    single._write_json_atomic(outputs_dir / "aggregate_comparison.json", aggregate_payload)

    provenance = {
        "created_at": single._utc_now_iso(),
        "script": SCRIPT_VERSION,
        "inputs": {
            "canonical_input_dir": {
                "path": str(canonical_input_dir),
            },
            "selected_h5s": [
                {
                    "path": str(path),
                    "sha256": single._sha256_file(path),
                }
                for path in selected_h5s
            ],
        },
        "rail_inputs": {
            event_id: {
                rail: {
                    "path": path,
                    "sha256": single._sha256_file(Path(path)),
                }
                for rail, path in rails.items()
            }
            for event_id, rails in all_rail_inputs.items()
        },
        "premium_commands": premium_commands,
        "baseline_feature_builder_source": "tools.g2_representation_contract._load_stage02_feature_builder",
    }
    single._write_json_atomic(outputs_dir / "provenance.json", provenance)

    warnings: list[str] = []
    if aggregate_verdict == "LIMITED_ADVANTAGE":
        warnings.append("premium advantage remains bounded at subcohort level")
    stage_summary = {
        "created_at": single._utc_now_iso(),
        "stage_name": STAGE_NAME,
        "status": "PASS",
        "event_id": None,
        "n_inputs": len(selected_h5s) * len(single.EXPECTED_RAILS),
        "n_outputs": 3,
        "warnings": warnings,
        "blocking_reason": None,
        "n_events": len(selected_h5s),
        "aggregate_verdict": aggregate_verdict,
        "aggregate_verdict_reason": aggregate_reason,
        "script": SCRIPT_VERSION,
    }
    single._write_json_atomic(stage_dir / "stage_summary.json", stage_summary)

    manifest = {
        "created_at": single._utc_now_iso(),
        "stage": STAGE_NAME,
        "script": SCRIPT_VERSION,
        "parameters": {
            "run_id": args.run_id,
            "canonical_input_dir": str(canonical_input_dir),
            "event_limit": args.event_limit,
        },
        "inputs": {
            "selected_h5s": [
                {
                    "path": str(path),
                    "sha256": single._sha256_file(path),
                }
                for path in selected_h5s
            ],
        },
        "outputs": {
            "inputs_dir": str(inputs_dir),
            "logs_dir": str(logs_dir),
            "per_event_comparison_json": {
                "path": str(outputs_dir / "per_event_comparison.json"),
                "sha256": single._sha256_file(outputs_dir / "per_event_comparison.json"),
            },
            "aggregate_comparison_json": {
                "path": str(outputs_dir / "aggregate_comparison.json"),
                "sha256": single._sha256_file(outputs_dir / "aggregate_comparison.json"),
            },
            "provenance_json": {
                "path": str(outputs_dir / "provenance.json"),
                "sha256": single._sha256_file(outputs_dir / "provenance.json"),
            },
            "stage_summary_json": str(stage_dir / "stage_summary.json"),
        },
        "status": "PASS",
    }
    single._write_json_atomic(stage_dir / "manifest.json", manifest)

    print(f"[OK] stage_dir: {stage_dir}")
    print(f"[OK] aggregate_verdict: {aggregate_verdict}")
    print(f"[OK] report: {outputs_dir / 'aggregate_comparison.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
