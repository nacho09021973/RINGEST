#!/usr/bin/env python3
"""
Run a non-canonical BASURIN physics probe over the 90-event expanded cohort.

This wrapper does not promote the result to a canonical cohort. It reuses:
- the real 90-event stage-02 H5 inputs,
- the governed 33-event canonical lane,
- the governed 55-event OOD lane,
- the 35 -> 33 exclusion summary,
- the frozen 33-event baseline-vs-premium comparison,
- and the existing decay_type_discrimination fitting logic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.decay_type_discrimination import process_event  # noqa: E402


RUNS_ROOT_DEFAULT = REPO_ROOT / "runs"
STAGE_NAME = "experiment/fullcohort_90_physics_probe"
INPUT_DIR_DEFAULT = REPO_ROOT / "runs" / "reopen_v1" / "90_event_xmax6_stage02_input"
CANONICAL33_INPUT_DIR = REPO_ROOT / "runs" / "reopen_v1" / "33_event_effective_contract_pass_stage02_input"
OOD55_INPUT_DIR = REPO_ROOT / "runs" / "reopen_v1" / "55_event_effective_ood_stage02_input"
CANONICAL33_SUMMARY = REPO_ROOT / "runs" / "reopen_v1" / "33_event_effective_contract_pass_summary.json"
GEOMETRY33_SUMMARY = (
    REPO_ROOT / "runs" / "reopen_v1" / "04_geometry_physics_contracts_33_event_effective_contract_pass_xmax6_v1" / "geometry_contracts_summary.json"
)
GEOMETRY55_SUMMARY = (
    REPO_ROOT / "runs" / "reopen_v1" / "04_geometry_physics_contracts_55_event_effective_ood_xmax6_v1" / "geometry_contracts_summary.json"
)
GATE90_SUMMARY = REPO_ROOT / "runs" / "reopen_v1" / "90_event_gate_split_summary.json"
PREMIUM33_PER_EVENT = (
    REPO_ROOT
    / "runs"
    / "reopen_v1_33event_baseline_vs_premium_final_iter1_20260413"
    / "experiment"
    / "baseline_vs_premium_multievent"
    / "outputs"
    / "per_event_comparison.json"
)
PREMIUM33_AGGREGATE = (
    REPO_ROOT
    / "runs"
    / "reopen_v1_33event_baseline_vs_premium_final_iter1_20260413"
    / "experiment"
    / "baseline_vs_premium_multievent"
    / "outputs"
    / "aggregate_comparison.json"
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp_", suffix=path.suffix or ".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(_jsonify(payload), indent=2, ensure_ascii=False))
            fh.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _jsonify(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonify(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonify(v) for v in value]
    if isinstance(value, tuple):
        return [_jsonify(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def _stage04_contract_map(summary_path: Path) -> dict[str, dict[str, Any]]:
    payload = _load_json(summary_path)
    out: dict[str, dict[str, Any]] = {}
    for item in payload.get("contracts", []):
        out[item["name"]] = {
            "contract_mode": item.get("correlator_structure", {}).get("contract_mode"),
            "has_spatial_structure": item.get("correlator_structure", {}).get("has_spatial_structure"),
            "is_monotonic_decay": item.get("correlator_structure", {}).get("is_monotonic_decay"),
            "has_power_law": item.get("correlator_structure", {}).get("has_power_law"),
            "log_slope": item.get("correlator_structure", {}).get("log_slope"),
            "correlation_quality": item.get("correlator_structure", {}).get("correlation_quality"),
            "warnings": item.get("warnings", []),
            "errors": item.get("errors", []),
        }
    return out


def _premium_map(per_event_path: Path) -> dict[str, dict[str, Any]]:
    payload = _load_json(per_event_path)
    events = payload.get("events", {})
    out: dict[str, dict[str, Any]] = {}
    for event_id, item in events.items():
        comparison = item.get("comparison", {})
        out[f"{event_id}__ringdown"] = {
            "verdict": item.get("verdict"),
            "premium_null_rejects": comparison.get("premium_null_rejects"),
            "premium_control_signature_distinct": comparison.get("premium_control_signature_distinct"),
            "premium_signal_classes": comparison.get("premium_signal_classes", []),
        }
    return out


def _count_classification(results: dict[str, dict[str, Any]], label: str) -> int:
    return sum(1 for item in results.values() if item.get("decay_classification") == label)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run the non-canonical 90-event BASURIN physics probe.")
    ap.add_argument("--run-id", required=True, help="Run identifier under runs/<run_id>/experiment/fullcohort_90_physics_probe/")
    ap.add_argument("--runs-root", type=Path, default=RUNS_ROOT_DEFAULT)
    ap.add_argument("--input-dir", type=Path, default=INPUT_DIR_DEFAULT)
    ap.add_argument("--x-min", type=float, default=4.0, help="Tail window minimum x. Default aligns with tail_strict freeze.")
    ap.add_argument("--g2-min", type=float, default=1e-6)
    return ap


def main() -> int:
    args = build_parser().parse_args()
    runs_root = Path(args.runs_root).resolve(strict=False)
    input_dir = Path(args.input_dir).resolve(strict=False)
    stage_dir = runs_root / args.run_id / "experiment" / "fullcohort_90_physics_probe"
    outputs_dir = stage_dir / "outputs"
    manifest_path = stage_dir / "manifest.json"
    stage_summary_path = stage_dir / "stage_summary.json"
    stdout_log = stage_dir / "stdout.log"
    stderr_log = stage_dir / "stderr.log"

    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    def log(msg: str) -> None:
        stdout_lines.append(msg)
        print(msg)

    def fail(code: int, message: str) -> int:
        stderr_lines.append(message)
        stage_dir.mkdir(parents=True, exist_ok=True)
        stdout_log.write_text("\n".join(stdout_lines) + ("\n" if stdout_lines else ""), encoding="utf-8")
        stderr_log.write_text("\n".join(stderr_lines) + ("\n" if stderr_lines else ""), encoding="utf-8")
        stage_summary = {
            "created_at": _utc_now_iso(),
            "stage": STAGE_NAME,
            "status": "FAIL",
            "failure_reason": message,
            "non_canonical": True,
            "purpose": "physics_probe",
            "automatic_downstream_promotion": False,
        }
        _write_json_atomic(stage_summary_path, stage_summary)
        return code

    required_paths = [
        input_dir,
        CANONICAL33_INPUT_DIR,
        OOD55_INPUT_DIR,
        CANONICAL33_SUMMARY,
        GEOMETRY33_SUMMARY,
        GEOMETRY55_SUMMARY,
        GATE90_SUMMARY,
        PREMIUM33_PER_EVENT,
        PREMIUM33_AGGREGATE,
    ]
    missing = [str(p) for p in required_paths if not p.exists()]
    if missing:
        return fail(2, f"Missing required inputs: {missing[0]}")
    if outputs_dir.exists():
        return fail(2, f"Output directory already exists: {outputs_dir}")

    h5_files = sorted(input_dir.glob("*.h5"))
    if not h5_files:
        return fail(2, f"No H5 files found in input directory: {input_dir}")

    stage_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=False)

    canonical33 = {p.stem for p in CANONICAL33_INPUT_DIR.glob("*.h5")}
    ood55 = {p.stem for p in OOD55_INPUT_DIR.glob("*.h5")}
    exclusion_summary = _load_json(CANONICAL33_SUMMARY)
    excluded_low_signal = {
        item["name"] for item in exclusion_summary.get("exclusion_analysis", {}).get("excluded_events", [])
    }
    stage04_map = _stage04_contract_map(GEOMETRY33_SUMMARY)
    stage04_map.update(_stage04_contract_map(GEOMETRY55_SUMMARY))
    premium_map = _premium_map(PREMIUM33_PER_EVENT)
    premium_aggregate = _load_json(PREMIUM33_AGGREGATE)

    per_event_status: dict[str, dict[str, Any]] = {}
    per_event_probe: dict[str, dict[str, Any]] = {}
    cohort_partition = {
        "usable_for_mainline": [],
        "ood_but_informative": [],
        "contract_blocked": [],
        "low_signal_or_uninformative": [],
        "needs_manual_review": [],
        "rules_used": {
            "usable_for_mainline": "event belongs to the governed canonical_33 lane",
            "ood_but_informative": "event belongs to the governed ood_55 lane and decay probe is not NEITHER_GOOD",
            "contract_blocked": "required contractual input is missing or no auditable governed lane exists",
            "low_signal_or_uninformative": "event is an explicit low-signal exclusion or the minimal decay probe is NEITHER_GOOD outside canonical_33",
            "needs_manual_review": "event has auditable inputs but missing or conflicting governed metadata for a prudent automatic assignment",
        },
    }

    log(f"Processing {len(h5_files)} real events from {input_dir}")
    for h5_path in h5_files:
        event_name = h5_path.stem
        in_canonical = event_name in canonical33
        in_ood = event_name in ood55
        in_excluded = event_name in excluded_low_signal
        stage04 = stage04_map.get(event_name)
        premium = premium_map.get(event_name)

        decay_result = process_event(h5_path, x_min_window=args.x_min, g2_min_threshold=args.g2_min)
        decay_class = decay_result.classification

        if not h5_path.exists():
            utility = "contract_blocked"
            stage_status = "FAIL"
            status_reason = "missing input H5"
        elif in_canonical:
            utility = "usable_for_mainline"
            stage_status = "PASS"
            status_reason = "governed canonical_33 lane"
        elif in_excluded:
            utility = "low_signal_or_uninformative"
            stage_status = "DEGRADED"
            status_reason = "explicit 35->33 exclusion by spatial-structure loss / near-flat signal"
        elif in_ood and decay_class != "NEITHER_GOOD":
            utility = "ood_but_informative"
            stage_status = "DEGRADED"
            status_reason = "governed ood_55 lane with usable minimal decay structure"
        elif in_ood and decay_class == "NEITHER_GOOD":
            utility = "low_signal_or_uninformative"
            stage_status = "DEGRADED"
            status_reason = "governed ood_55 lane but minimal decay probe is NEITHER_GOOD"
        else:
            utility = "needs_manual_review"
            stage_status = "DEGRADED"
            status_reason = "event is outside the governed 33/55 lanes and not covered by known exclusions"

        per_event_status[event_name] = {
            "event_id": event_name.replace("__ringdown", ""),
            "input_h5": str(h5_path),
            "stage_status": stage_status,
            "status_reason": status_reason,
            "lane_membership": "canonical_33" if in_canonical else "ood_55" if in_ood else "excluded_low_signal" if in_excluded else "unassigned",
            "contractual_input_present": True,
            "non_canonical": True,
            "purpose": "physics_probe",
        }

        per_event_probe[event_name] = {
            "event_id": event_name.replace("__ringdown", ""),
            "decay_classification": decay_class,
            "decay_reason": decay_result.classification_reason,
            "delta_bic": decay_result.delta_bic,
            "r2_exponential": decay_result.r2_exponential,
            "r2_power_law": decay_result.r2_power_law,
            "n_points_valid": decay_result.n_points_valid,
            "has_oscillations": decay_result.has_oscillations,
            "monotonicity_fraction": decay_result.monotonicity_fraction,
            "stage04_relaxed_correlator": stage04,
            "premium_probe": premium,
            "utility_class": utility,
        }
        cohort_partition[utility].append(event_name)

    aggregate_probe_summary = {
        "created_at": _utc_now_iso(),
        "stage": STAGE_NAME,
        "purpose": "physics_probe",
        "non_canonical": True,
        "automatic_downstream_promotion": False,
        "n_events_total": len(h5_files),
        "n_contract_pass": len(canonical33 | ood55),
        "n_degraded": sum(1 for item in per_event_status.values() if item["stage_status"] == "DEGRADED"),
        "n_fail": sum(1 for item in per_event_status.values() if item["stage_status"] == "FAIL"),
        "n_usable_for_mainline": len(cohort_partition["usable_for_mainline"]),
        "n_ood_but_informative": len(cohort_partition["ood_but_informative"]),
        "n_low_signal_or_uninformative": len(cohort_partition["low_signal_or_uninformative"]),
        "n_needs_manual_review": len(cohort_partition["needs_manual_review"]),
        "n_contract_blocked": len(cohort_partition["contract_blocked"]),
        "decay_structure_summary": {
            "x_min": args.x_min,
            "g2_min": args.g2_min,
            "n_exponential_preferred": _count_classification(per_event_probe, "EXPONENTIAL_PREFERRED"),
            "n_powerlaw_preferred": _count_classification(per_event_probe, "POWERLAW_PREFERRED"),
            "n_ambiguous": _count_classification(per_event_probe, "AMBIGUOUS"),
            "n_neither_good": _count_classification(per_event_probe, "NEITHER_GOOD"),
        },
        "premium_advantage_count": premium_aggregate["aggregate_metrics"]["verdict_counts"]["LIMITED_ADVANTAGE"]
        + premium_aggregate["aggregate_metrics"]["verdict_counts"]["CLEAR_ADVANTAGE"],
        "premium_no_advantage_count": premium_aggregate["aggregate_metrics"]["verdict_counts"]["NO_ADVANTAGE"],
        "premium_advantage_scope": "canonical_33_only",
        "source_artifacts": {
            "input_dir": str(input_dir),
            "canonical_33_input_dir": str(CANONICAL33_INPUT_DIR),
            "ood_55_input_dir": str(OOD55_INPUT_DIR),
            "canonical_33_summary": str(CANONICAL33_SUMMARY),
            "geometry_33_summary": str(GEOMETRY33_SUMMARY),
            "geometry_55_summary": str(GEOMETRY55_SUMMARY),
            "gate_90_summary": str(GATE90_SUMMARY),
            "premium_per_event": str(PREMIUM33_PER_EVENT),
            "premium_aggregate": str(PREMIUM33_AGGREGATE),
        },
    }

    stage_summary = {
        "created_at": _utc_now_iso(),
        "stage": STAGE_NAME,
        "status": "PASS",
        "purpose": "physics_probe",
        "non_canonical": True,
        "automatic_downstream_promotion": False,
        "n_events_total": aggregate_probe_summary["n_events_total"],
        "n_contract_pass": aggregate_probe_summary["n_contract_pass"],
        "n_degraded": aggregate_probe_summary["n_degraded"],
        "n_fail": aggregate_probe_summary["n_fail"],
        "n_usable_for_mainline": aggregate_probe_summary["n_usable_for_mainline"],
        "n_ood_but_informative": aggregate_probe_summary["n_ood_but_informative"],
        "n_low_signal_or_uninformative": aggregate_probe_summary["n_low_signal_or_uninformative"],
        "n_needs_manual_review": aggregate_probe_summary["n_needs_manual_review"],
        "premium_advantage_scope": aggregate_probe_summary["premium_advantage_scope"],
        "warnings": [
            "Non-canonical physics probe only; no automatic cohort promotion",
            "Stage 04 relaxed correlator semantics remain non-physical by default",
            "Premium advantage counts are reused from canonical_33 only",
        ],
    }

    manifest = {
        "created_at": _utc_now_iso(),
        "stage": STAGE_NAME,
        "script": str(Path(__file__).resolve()),
        "command": [
            sys.executable,
            str(Path(__file__).resolve()),
            "--run-id",
            args.run_id,
            "--runs-root",
            str(runs_root),
            "--input-dir",
            str(input_dir),
            "--x-min",
            str(args.x_min),
            "--g2-min",
            str(args.g2_min),
        ],
        "parameters": {
            "run_id": args.run_id,
            "x_min": args.x_min,
            "g2_min": args.g2_min,
            "purpose": "physics_probe",
            "non_canonical": True,
            "automatic_downstream_promotion": False,
        },
        "inputs": {
            "input_dir": {"path": str(input_dir), "sha256_listing": hashlib.sha256("\n".join(sorted(p.name for p in h5_files)).encode("utf-8")).hexdigest()},
            "canonical_33_summary": {"path": str(CANONICAL33_SUMMARY), "sha256": _sha256_file(CANONICAL33_SUMMARY)},
            "geometry_33_summary": {"path": str(GEOMETRY33_SUMMARY), "sha256": _sha256_file(GEOMETRY33_SUMMARY)},
            "geometry_55_summary": {"path": str(GEOMETRY55_SUMMARY), "sha256": _sha256_file(GEOMETRY55_SUMMARY)},
            "gate_90_summary": {"path": str(GATE90_SUMMARY), "sha256": _sha256_file(GATE90_SUMMARY)},
            "premium_per_event": {"path": str(PREMIUM33_PER_EVENT), "sha256": _sha256_file(PREMIUM33_PER_EVENT)},
            "premium_aggregate": {"path": str(PREMIUM33_AGGREGATE), "sha256": _sha256_file(PREMIUM33_AGGREGATE)},
        },
        "outputs": {
            "manifest_json": str(manifest_path),
            "stage_summary_json": str(stage_summary_path),
            "per_event_status_json": str(outputs_dir / "per_event_status.json"),
            "per_event_physics_probe_json": str(outputs_dir / "per_event_physics_probe.json"),
            "aggregate_probe_summary_json": str(outputs_dir / "aggregate_probe_summary.json"),
            "cohort_partition_json": str(outputs_dir / "cohort_partition.json"),
            "stdout_log": str(stdout_log),
            "stderr_log": str(stderr_log),
        },
    }

    _write_json_atomic(outputs_dir / "per_event_status.json", per_event_status)
    _write_json_atomic(outputs_dir / "per_event_physics_probe.json", per_event_probe)
    _write_json_atomic(outputs_dir / "aggregate_probe_summary.json", aggregate_probe_summary)
    _write_json_atomic(outputs_dir / "cohort_partition.json", cohort_partition)
    _write_json_atomic(stage_summary_path, stage_summary)
    _write_json_atomic(manifest_path, manifest)

    stdout_lines.extend(
        [
            f"run_id={args.run_id}",
            f"n_events_total={aggregate_probe_summary['n_events_total']}",
            f"n_usable_for_mainline={aggregate_probe_summary['n_usable_for_mainline']}",
            f"n_ood_but_informative={aggregate_probe_summary['n_ood_but_informative']}",
            f"n_low_signal_or_uninformative={aggregate_probe_summary['n_low_signal_or_uninformative']}",
            f"n_needs_manual_review={aggregate_probe_summary['n_needs_manual_review']}",
        ]
    )
    stdout_log.write_text("\n".join(stdout_lines) + "\n", encoding="utf-8")
    stderr_log.write_text("\n".join(stderr_lines) + ("\n" if stderr_lines else ""), encoding="utf-8")

    log(f"[OK] wrote: {outputs_dir / 'aggregate_probe_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
