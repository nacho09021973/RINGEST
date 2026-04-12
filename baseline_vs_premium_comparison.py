#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

SCRIPT_VERSION = "baseline_vs_premium_comparison.py v0.1-beta"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Canonical baseline vs premium comparison scaffold."
    )
    ap.add_argument("--run-id", required=True, help="Run id under runs/<run_id>/")
    ap.add_argument("--event-id", required=True, help="Canonical event id")
    ap.add_argument("--runs-dir", default="runs", help="Root runs directory")
    ap.add_argument("--baseline-boundary-h5", required=True, help="Canonical baseline boundary HDF5")
    ap.add_argument("--premium-stage-dir", required=True, help="runs/<run_id>/premium_estimator")
    args = ap.parse_args()

    runs_dir = Path(args.runs_dir).resolve()
    run_dir = (runs_dir / args.run_id).resolve()
    stage_dir = (run_dir / "baseline_vs_premium_comparison").resolve()
    outputs_dir = (stage_dir / "outputs").resolve()

    baseline_h5 = Path(args.baseline_boundary_h5).resolve()
    premium_stage_dir = Path(args.premium_stage_dir).resolve()
    premium_estimate = premium_stage_dir / "outputs" / "premium_estimate.json"
    premium_features = premium_stage_dir / "outputs" / "premium_features.npz"
    premium_provenance = premium_stage_dir / "outputs" / "provenance.json"

    missing = [
        str(p) for p in [baseline_h5, premium_estimate, premium_features, premium_provenance]
        if not p.exists()
    ]
    if missing:
        raise SystemExit("[ERROR] Missing contractual inputs:\\n" + "\\n".join(missing))

    outputs_dir.mkdir(parents=True, exist_ok=True)

    with premium_estimate.open("rb") as f:
        premium_estimate_bytes = f.read()
    premium_estimate_json = json.loads(premium_estimate_bytes.decode("utf-8"))

    premium_npz = np.load(premium_features, allow_pickle=False)
    premium_keys = sorted(list(premium_npz.files))
    n_features_premium = int(premium_estimate_json.get("summary_metrics", {}).get("n_features", 0))
    compute_ran_premium = bool(premium_estimate_json.get("summary_metrics", {}).get("compute_ran", False))
    placeholder_flag_premium = bool(premium_estimate_json.get("summary_metrics", {}).get("is_placeholder", True))

    comparison_metrics = {
        "schema_version": "baseline-vs-premium-comparison-0.1",
        "event_id": args.event_id,
        "baseline_artifacts": {
            "baseline_boundary_h5": str(baseline_h5),
        },
        "premium_artifacts": {
            "premium_stage_dir": str(premium_stage_dir),
            "premium_estimate_json": str(premium_estimate),
            "premium_features_npz": str(premium_features),
            "premium_provenance_json": str(premium_provenance),
        },
        "metrics": {
            "n_features_baseline": None,
            "n_features_premium": n_features_premium,
            "compute_ran_premium": compute_ran_premium,
            "placeholder_flag_premium": placeholder_flag_premium,
            "premium_feature_keys": premium_keys,
            "premium_artifact_completeness": {
                "premium_estimate_exists": True,
                "premium_features_exists": True,
                "premium_provenance_exists": True,
            },
        },
        "verdict": "DEGRADED",
        "provenance_hash": sha256_bytes(premium_estimate_bytes),
    }
    write_json(outputs_dir / "comparison_metrics.json", comparison_metrics)

    comparison_report = {
        "created_at": utc_now(),
        "script": SCRIPT_VERSION,
        "event_id": args.event_id,
        "summary": {
            "premium_compute_ran": compute_ran_premium,
            "premium_is_placeholder": placeholder_flag_premium,
            "premium_n_features": n_features_premium,
        },
        "interpretation": [
            "Scaffold comparison only",
            "No scientific PASS/FAIL decision yet",
            "Downstream remains blocked by default",
        ],
    }
    write_json(outputs_dir / "comparison_report.json", comparison_report)

    provenance = {
        "created_at": utc_now(),
        "script": SCRIPT_VERSION,
        "event_id": args.event_id,
        "inputs": {
            "baseline_boundary_h5": str(baseline_h5),
            "premium_estimate_json": str(premium_estimate),
            "premium_features_npz": str(premium_features),
            "premium_provenance_json": str(premium_provenance),
        },
        "notes": [
            "Canonical comparison scaffold",
            "No automatic downstream enablement",
            "Verdict remains DEGRADED in scaffold mode",
        ],
    }
    write_json(outputs_dir / "provenance.json", provenance)

    stage_summary = {
        "stage_name": "baseline_vs_premium_comparison",
        "status": "DEGRADED",
        "event_id": args.event_id,
        "n_inputs": 4,
        "n_outputs": 3,
        "warnings": [
            "Scaffold implementation only",
            "No scientific comparison logic yet",
        ],
        "blocking_reason": "comparison scaffold only; downstream remains blocked",
        "created_at": utc_now(),
        "script": SCRIPT_VERSION,
    }
    write_json(stage_dir / "stage_summary.json", stage_summary)

    manifest = {
        "created_at": utc_now(),
        "script": SCRIPT_VERSION,
        "run_id": args.run_id,
        "stage": "baseline_vs_premium_comparison",
        "event_id": args.event_id,
        "artifacts": {
            "stage_summary_json": str(stage_dir / "stage_summary.json"),
            "comparison_report_json": str(outputs_dir / "comparison_report.json"),
            "comparison_metrics_json": str(outputs_dir / "comparison_metrics.json"),
            "provenance_json": str(outputs_dir / "provenance.json"),
        },
        "inputs": {
            "baseline_boundary_h5": str(baseline_h5),
            "premium_stage_dir": str(premium_stage_dir),
        },
    }
    write_json(stage_dir / "manifest.json", manifest)

    print(f"[OK] baseline_vs_premium_comparison scaffold written under: {stage_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
