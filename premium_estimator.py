#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

SCRIPT_VERSION = "premium_estimator.py v0.1-beta"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Fase B: premium estimator skeleton with canonical IO."
    )
    ap.add_argument("--run-id", required=True, help="Run id under runs/<run_id>/")
    ap.add_argument("--event-id", required=True, help="Canonical event id")
    ap.add_argument("--baseline-boundary-h5", required=True, help="Boundary HDF5 from baseline lane")
    ap.add_argument("--runs-dir", default="runs", help="Root runs directory")
    ap.add_argument("--estimator-name", default="premium_estimator_stub", help="Estimator identifier")
    ap.add_argument("--estimator-version", default="0.1-beta", help="Estimator version")
    ap.add_argument("--backend-config", default=None, help="Optional backend config JSON")
    args = ap.parse_args()

    backend_cfg = None
    if args.backend_config is not None:
        backend_path = Path(args.backend_config).resolve()
        if not backend_path.exists():
            raise SystemExit(f"[ERROR] Missing backend config: {backend_path}")
        backend_cfg = json.loads(backend_path.read_text(encoding="utf-8"))

    runs_dir = Path(args.runs_dir).resolve()
    run_dir = (runs_dir / args.run_id).resolve()
    stage_dir = (run_dir / "premium_estimator").resolve()
    outputs_dir = (stage_dir / "outputs").resolve()

    baseline_h5 = Path(args.baseline_boundary_h5).resolve()
    if not baseline_h5.exists():
        raise SystemExit(f"[ERROR] Missing contractual input: {baseline_h5}")

    outputs_dir.mkdir(parents=True, exist_ok=True)

    feature_path = outputs_dir / "premium_features.npz"
    np.savez(
        feature_path,
        dummy_feature=np.array([0.0], dtype=np.float64),
        source_boundary_h5=np.array([str(baseline_h5)], dtype=object),
    )

    backend_enabled = bool((backend_cfg or {}).get("enabled", False))
    backend_name = (backend_cfg or {}).get("backend_name", args.estimator_name)

    provenance = {
        "created_at": utc_now(),
        "script": SCRIPT_VERSION,
        "event_id": args.event_id,
        "estimator_name": args.estimator_name,
        "estimator_version": args.estimator_version,
        "backend_config_path": str(Path(args.backend_config).resolve()) if args.backend_config else None,
        "backend_name": backend_name,
        "backend_enabled": backend_enabled,
        "input_artifacts": {
            "baseline_boundary_h5": str(baseline_h5),
            "baseline_boundary_h5_sha256": sha256_file(baseline_h5),
        },
        "notes": [
            "Skeleton only",
            "No premium inference performed yet",
            "Backend disabled or adapter not implemented",
            "Downstream remains blocked",
        ],
    }
    write_json(outputs_dir / "provenance.json", provenance)

    premium_estimate = {
        "schema_version": "premium-estimator-0.1",
        "event_id": args.event_id,
        "estimator_name": args.estimator_name,
        "estimator_version": args.estimator_version,
        "input_artifacts": provenance["input_artifacts"],
        "status": "DEGRADED",
        "summary_metrics": {
            "n_features": 1,
            "is_placeholder": True,
            "backend_enabled": backend_enabled,
        },
        "feature_paths": {
            "premium_features_npz": str(feature_path),
        },
        "provenance_hash": hashlib.sha256(
            json.dumps(provenance, sort_keys=True).encode("utf-8")
        ).hexdigest(),
    }
    write_json(outputs_dir / "premium_estimate.json", premium_estimate)

    stage_summary = {
        "stage_name": "premium_estimator",
        "status": "DEGRADED",
        "event_id": args.event_id,
        "estimator_name": args.estimator_name,
        "n_inputs": 1,
        "n_outputs": 4,
        "warnings": [
            "Skeleton implementation only",
            "Backend disabled or premium adapter not implemented",
        ],
        "blocking_reason": "premium estimator backend disabled or not implemented; downstream blocked",
        "created_at": utc_now(),
        "script": SCRIPT_VERSION,
    }
    write_json(stage_dir / "stage_summary.json", stage_summary)

    backend_request_path = outputs_dir / "backend_request.json"
    backend_request = {
        "schema_version": "premium-backend-request-0.1",
        "event_id": args.event_id,
        "backend_name": backend_name,
        "backend_enabled": backend_enabled,
        "request_status": "PENDING" if backend_enabled else "DISABLED",
        "input_artifacts": {
            "baseline_boundary_h5": str(baseline_h5),
            "backend_config_path": str(Path(args.backend_config).resolve()) if args.backend_config else None,
        },
        "write_constraints": {
            "allowed_root": str(stage_dir),
            "forbid_writes_outside_run": True,
        },
        "required_outputs": [
            "stage_summary.json",
            "outputs/premium_estimate.json",
            "outputs/premium_features.npz",
            "outputs/provenance.json",
        ],
        "required_stage_status": "PASS",
        "degraded_allowed_for_stub_only": True,
        "notes": [
            "Auto-generated by premium_estimator.py",
            "Downstream remains blocked unless stage_summary.json is PASS",
        ],
    }
    write_json(backend_request_path, backend_request)

    manifest = {
        "created_at": utc_now(),
        "script": SCRIPT_VERSION,
        "run_id": args.run_id,
        "stage": "premium_estimator",
        "event_id": args.event_id,
        "artifacts": {
            "stage_summary_json": str(stage_dir / "stage_summary.json"),
            "premium_estimate_json": str(outputs_dir / "premium_estimate.json"),
            "premium_features_npz": str(feature_path),
            "provenance_json": str(outputs_dir / "provenance.json"),
            "backend_request_json": str(backend_request_path) if backend_request_path.exists() else None,
        },
        "inputs": {
            "baseline_boundary_h5": str(baseline_h5),
        },
    }
    write_json(stage_dir / "manifest.json", manifest)

    print(f"[OK] premium_estimator skeleton written under: {stage_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
