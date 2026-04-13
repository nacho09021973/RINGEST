#!/usr/bin/env python3
"""
Audit whether the current 90-event master run supports a unified analytical cohort.

This is a non-canonical governance audit over existing artifacts only.
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
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT_DEFAULT = REPO_ROOT / "runs"
STAGE_NAME = "experiment/cohort_unification_audit_90"
MASTER_RUN_DEFAULT = (
    REPO_ROOT
    / "runs"
    / "fullcohort_90_physics_probe_20260413_rerun1"
    / "experiment"
    / "fullcohort_90_physics_probe"
)
OOD_VS_CANONICAL_DEFAULT = REPO_ROOT / "runs" / "reopen_v1" / "ood_vs_canonical_comparison_summary.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _jsonify(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonify(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_jsonify(v) for v in value]
    if isinstance(value, tuple):
        return [_jsonify(v) for v in value]
    return value


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run cohort unification audit over the 90-event master probe.")
    ap.add_argument("--run-id", required=True, help="Run identifier under runs/<run_id>/experiment/cohort_unification_audit_90/")
    ap.add_argument("--runs-root", type=Path, default=RUNS_ROOT_DEFAULT)
    ap.add_argument("--master-run-dir", type=Path, default=MASTER_RUN_DEFAULT)
    ap.add_argument("--ood-vs-canonical-summary", type=Path, default=OOD_VS_CANONICAL_DEFAULT)
    return ap


def main() -> int:
    args = build_parser().parse_args()
    runs_root = Path(args.runs_root).resolve(strict=False)
    master_run_dir = Path(args.master_run_dir).resolve(strict=False)
    ood_vs_canonical_summary = Path(args.ood_vs_canonical_summary).resolve(strict=False)
    stage_dir = runs_root / args.run_id / "experiment" / "cohort_unification_audit_90"
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
            "decision": "INSUFFICIENT_EVIDENCE",
            "decision_reason": message,
            "non_canonical_master_run": True,
            "automatic_promotion": False,
        }
        _write_json_atomic(stage_summary_path, stage_summary)
        return code

    aggregate_path = master_run_dir / "outputs" / "aggregate_probe_summary.json"
    per_event_probe_path = master_run_dir / "outputs" / "per_event_physics_probe.json"
    cohort_partition_path = master_run_dir / "outputs" / "cohort_partition.json"
    required = [aggregate_path, per_event_probe_path, cohort_partition_path, ood_vs_canonical_summary]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        return fail(2, f"Missing required input: {missing[0]}")
    if outputs_dir.exists():
        return fail(2, f"Output directory already exists: {outputs_dir}")

    stage_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=False)

    aggregate = _load_json(aggregate_path)
    per_event_probe = _load_json(per_event_probe_path)
    cohort_partition = _load_json(cohort_partition_path)
    ood_vs_canonical = _load_json(ood_vs_canonical_summary)

    mainline = cohort_partition["usable_for_mainline"]
    ood_informative = cohort_partition["ood_but_informative"]
    low_signal = cohort_partition["low_signal_or_uninformative"]
    candidate_unified = sorted(mainline + ood_informative)

    decay_counts = {"EXPONENTIAL_PREFERRED": 0, "POWERLAW_PREFERRED": 0, "AMBIGUOUS": 0, "NEITHER_GOOD": 0}
    subset_decay: dict[str, dict[str, int]] = {}
    for subset_name, subset in {
        "mainline_33": mainline,
        "ood_informative_47": ood_informative,
        "low_signal_10": low_signal,
        "candidate_unified_80": candidate_unified,
    }.items():
        counts = {"EXPONENTIAL_PREFERRED": 0, "POWERLAW_PREFERRED": 0, "AMBIGUOUS": 0, "NEITHER_GOOD": 0}
        for event_name in subset:
            counts[per_event_probe[event_name]["decay_classification"]] += 1
        subset_decay[subset_name] = counts

    low_signal_all_neither = subset_decay["low_signal_10"]["NEITHER_GOOD"] == len(low_signal)
    ood_has_no_neither = subset_decay["ood_informative_47"]["NEITHER_GOOD"] == 0
    stage03_delta = abs(ood_vs_canonical["comparative_readout"]["stage03"]["score_delta_ood_minus_canonical"])
    stage04_delta = abs(ood_vs_canonical["comparative_readout"]["stage04"]["avg_score_delta_ood_minus_canonical"])
    stage03_compatible = stage03_delta <= 0.02
    stage04_compatible = stage04_delta <= 1e-6
    premium_scope_limited = aggregate.get("premium_advantage_scope") == "canonical_33_only"

    include_mainline = len(mainline) > 0
    include_ood_informative = stage03_compatible and stage04_compatible and ood_has_no_neither
    include_low_signal = not low_signal_all_neither

    if include_mainline and include_ood_informative and not include_low_signal:
        decision = "UNIFY_80_ONLY"
        decision_reason = (
            "canonical_33 and ood_informative_47 remain operationally compatible under reused Stage03/04 evidence, "
            "while low_signal_10 stays excluded because 10/10 are NEITHER_GOOD in the minimal decay probe"
        )
    elif include_mainline and not include_ood_informative:
        decision = "KEEP_PARTITIONED"
        decision_reason = (
            "mainline remains valid, but the ood_informative subset does not clear the minimal compatibility checks "
            "needed for an auditable unified analytical cohort"
        )
    elif include_mainline and include_ood_informative and include_low_signal:
        decision = "UNIFY_90"
        decision_reason = "all three subsets clear the minimal compatibility checks for a single analytical cohort"
    else:
        decision = "INSUFFICIENT_EVIDENCE"
        decision_reason = "available artifacts do not support a clean unification decision"

    unification_inputs_summary = {
        "created_at": _utc_now_iso(),
        "master_run_dir": str(master_run_dir),
        "n_events_total": aggregate["n_events_total"],
        "n_mainline": len(mainline),
        "n_ood_informative": len(ood_informative),
        "n_low_signal": len(low_signal),
        "source_artifacts": {
            "aggregate_probe_summary": str(aggregate_path),
            "per_event_physics_probe": str(per_event_probe_path),
            "cohort_partition": str(cohort_partition_path),
            "ood_vs_canonical_summary": str(ood_vs_canonical_summary),
        },
        "available_signals": [
            "utility partition from fullcohort_90_physics_probe",
            "per-event decay classification",
            "per-event relaxed Stage04 correlator descriptors",
            "canonical_33 vs ood_55 Stage03/04 compatibility summary",
            "canonical_33-only premium comparison reuse",
        ],
    }

    subset_compatibility_report = {
        "created_at": _utc_now_iso(),
        "subset_sizes": {
            "mainline_33": len(mainline),
            "ood_informative_47": len(ood_informative),
            "low_signal_10": len(low_signal),
            "candidate_unified_80": len(candidate_unified),
        },
        "decay_classification_by_subset": subset_decay,
        "compatibility_checks": {
            "ood_stage03_compatible": {
                "value": stage03_compatible,
                "score_delta_ood_minus_canonical": stage03_delta,
                "rule": "abs(score_delta_ood_minus_canonical) <= 0.02",
            },
            "ood_stage04_compatible": {
                "value": stage04_compatible,
                "avg_score_delta_ood_minus_canonical": stage04_delta,
                "rule": "abs(avg_score_delta_ood_minus_canonical) <= 1e-6",
            },
            "ood_informative_has_no_neither_good": {
                "value": ood_has_no_neither,
                "rule": "NEITHER_GOOD count in ood_informative_47 == 0",
            },
            "low_signal_all_neither_good": {
                "value": low_signal_all_neither,
                "rule": "NEITHER_GOOD count in low_signal_10 == 10",
            },
            "premium_signal_is_limited_scope_only": {
                "value": premium_scope_limited,
                "rule": "premium_advantage_scope == canonical_33_only",
            },
        },
        "interpretation_limits": [
            "This audit is operational, not a physical-homogeneity claim",
            "Premium evidence is reused only on canonical_33 and does not validate OOD unification by itself",
            "The 90-event master run remains non-canonical even if 80 events are recommended together",
        ],
    }

    unification_decision = {
        "created_at": _utc_now_iso(),
        "n_events_total": aggregate["n_events_total"],
        "n_mainline": len(mainline),
        "n_ood_informative": len(ood_informative),
        "n_low_signal": len(low_signal),
        "candidate_unified_count": len(candidate_unified),
        "decision": decision,
        "decision_reason": decision_reason,
        "include_mainline": include_mainline,
        "include_ood_informative": include_ood_informative,
        "include_low_signal": include_low_signal,
        "non_canonical_master_run": True,
        "automatic_promotion": False,
    }

    excluded_events = []
    for event_name in low_signal:
        excluded_events.append(
            {
                "event_name": event_name,
                "exclusion_class": "low_signal_or_uninformative",
                "reason": "minimal decay probe is NEITHER_GOOD and event is already classified low utility in the 90-event master probe",
            }
        )

    recommended_cohort = {
        "created_at": _utc_now_iso(),
        "recommended_cohort_kind": "expanded_analytical_cohort" if decision == "UNIFY_80_ONLY" else "partitioned_only",
        "decision": decision,
        "recommended_events": candidate_unified if decision == "UNIFY_80_ONLY" else mainline,
        "excluded_events": excluded_events,
        "exclusion_reason_by_class": {
            "low_signal_or_uninformative": "kept outside the expanded analytical cohort because the audit found no minimum stability/utility signal for inclusion",
        },
    }

    stage_summary = {
        "created_at": _utc_now_iso(),
        "stage": STAGE_NAME,
        "status": "PASS",
        "n_events_total": aggregate["n_events_total"],
        "n_mainline": len(mainline),
        "n_ood_informative": len(ood_informative),
        "n_low_signal": len(low_signal),
        "candidate_unified_count": len(candidate_unified),
        "decision": decision,
        "decision_reason": decision_reason,
        "include_mainline": include_mainline,
        "include_ood_informative": include_ood_informative,
        "include_low_signal": include_low_signal,
        "non_canonical_master_run": True,
        "automatic_promotion": False,
        "warnings": [
            "This audit does not canonicalize the 90-event run",
            "Operational compatibility does not imply physical homogeneity",
            "Premium evidence remains limited to canonical_33 reuse",
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
            "--master-run-dir",
            str(master_run_dir),
            "--ood-vs-canonical-summary",
            str(ood_vs_canonical_summary),
        ],
        "parameters": {
            "run_id": args.run_id,
            "non_canonical_master_run": True,
            "automatic_promotion": False,
        },
        "inputs": {
            "aggregate_probe_summary": {"path": str(aggregate_path), "sha256": _sha256_file(aggregate_path)},
            "per_event_physics_probe": {"path": str(per_event_probe_path), "sha256": _sha256_file(per_event_probe_path)},
            "cohort_partition": {"path": str(cohort_partition_path), "sha256": _sha256_file(cohort_partition_path)},
            "ood_vs_canonical_summary": {"path": str(ood_vs_canonical_summary), "sha256": _sha256_file(ood_vs_canonical_summary)},
        },
        "outputs": {
            "manifest_json": str(manifest_path),
            "stage_summary_json": str(stage_summary_path),
            "unification_inputs_summary_json": str(outputs_dir / "unification_inputs_summary.json"),
            "subset_compatibility_report_json": str(outputs_dir / "subset_compatibility_report.json"),
            "unification_decision_json": str(outputs_dir / "unification_decision.json"),
            "recommended_cohort_json": str(outputs_dir / "recommended_cohort.json"),
            "stdout_log": str(stdout_log),
            "stderr_log": str(stderr_log),
        },
    }

    _write_json_atomic(outputs_dir / "unification_inputs_summary.json", unification_inputs_summary)
    _write_json_atomic(outputs_dir / "subset_compatibility_report.json", subset_compatibility_report)
    _write_json_atomic(outputs_dir / "unification_decision.json", unification_decision)
    _write_json_atomic(outputs_dir / "recommended_cohort.json", recommended_cohort)
    _write_json_atomic(stage_summary_path, stage_summary)
    _write_json_atomic(manifest_path, manifest)

    stdout_lines.extend(
        [
            f"run_id={args.run_id}",
            f"decision={decision}",
            f"candidate_unified_count={len(candidate_unified)}",
            f"n_low_signal_excluded={len(low_signal)}",
        ]
    )
    stdout_log.write_text("\n".join(stdout_lines) + "\n", encoding="utf-8")
    stderr_log.write_text("\n".join(stderr_lines) + ("\n" if stderr_lines else ""), encoding="utf-8")
    log(f"[OK] wrote: {outputs_dir / 'unification_decision.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
