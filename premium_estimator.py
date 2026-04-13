#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import h5py
import numpy as np

SCRIPT_VERSION = "premium_estimator.py v0.4-beta"


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


def compute_minimal_backend_features(boundary_h5: Path) -> tuple[dict, np.ndarray]:
    with h5py.File(boundary_h5, "r") as f:
        if "boundary" not in f:
            raise ValueError("missing group 'boundary'")
        boundary = f["boundary"]
        if "G2_ringdown" not in boundary or "x_grid" not in boundary:
            raise ValueError("missing boundary/G2_ringdown or boundary/x_grid")

        g2 = np.asarray(boundary["G2_ringdown"][:], dtype=np.float64)
        x = np.asarray(boundary["x_grid"][:], dtype=np.float64)

    if g2.ndim != 1 or x.ndim != 1 or len(g2) != len(x) or len(g2) < 8:
        raise ValueError("invalid G2/x_grid shape")
    if not np.all(np.isfinite(g2)) or not np.all(np.isfinite(x)):
        raise ValueError("non-finite values in G2/x_grid")

    positive_fraction = float(np.mean(g2 > 0))
    g2_mean = float(np.mean(g2))
    g2_std = float(np.std(g2))
    g2_max = float(np.max(g2))
    g2_min = float(np.min(g2))
    monotonicity_fraction = float(np.mean(np.diff(g2) <= 0)) if len(g2) > 1 else 1.0
    head_mean = float(np.mean(g2[: max(1, len(g2) // 8)]))
    tail_mean = float(np.mean(g2[-max(1, len(g2) // 8):]))
    tail_ratio = float(tail_mean / head_mean) if abs(head_mean) > 1e-12 else 0.0

    # --- sensitivity features (v0.3) ---
    # Tail energy fraction: L2 energy in last quarter vs total
    total_energy = float(np.sum(g2 ** 2))
    tail_quarter = g2[-max(1, len(g2) // 4):]
    tail_energy_fraction = float(np.sum(tail_quarter ** 2)) / max(total_energy, 1e-30)

    # Curvature RMS: root mean square of second differences
    if len(g2) > 2:
        d2 = np.diff(g2, n=2)
        curvature_rms = float(np.sqrt(np.mean(d2 ** 2)))
    else:
        curvature_rms = 0.0

    # Signal class: coarse shape discriminant
    if positive_fraction == 0.0 or g2_std < 1e-10:
        signal_class = "null_like"
    elif monotonicity_fraction > 0.85 and tail_energy_fraction < 0.05:
        # Distinguish pure sharp decays (low tail retention) from attenuated
        # decays that retain significant tail energy relative to head.
        if tail_ratio >= 0.05:
            signal_class = "attenuated_decay"
        elif tail_ratio >= 0.005:
            signal_class = "moderate_decay"
        else:
            signal_class = "sharp_decay"
    else:
        signal_class = "broad_signal"

    features = {
        "n_points": int(len(g2)),
        "positive_fraction": positive_fraction,
        "g2_mean": g2_mean,
        "g2_std": g2_std,
        "g2_min": g2_min,
        "g2_max": g2_max,
        "monotonicity_fraction": monotonicity_fraction,
        "tail_ratio": tail_ratio,
        "tail_energy_fraction": tail_energy_fraction,
        "curvature_rms": curvature_rms,
        "signal_class": signal_class,
    }
    vector = np.array(
        [
            float(len(g2)),
            positive_fraction,
            g2_mean,
            g2_std,
            monotonicity_fraction,
            tail_ratio,
            tail_energy_fraction,
            curvature_rms,
        ],
        dtype=np.float64,
    )
    return features, vector


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

    backend_name = (backend_cfg or {}).get("backend_name", "local_g2_summary_v2")
    backend_enabled = True
    feature_dict, feature_vector = compute_minimal_backend_features(baseline_h5)
    positive_fraction = feature_dict["positive_fraction"]
    g2_std = feature_dict["g2_std"]
    signal_class = feature_dict["signal_class"]
    compute_ran = True
    estimator_status = "PASS" if positive_fraction > 0.0 and g2_std > 1e-10 else "FAIL"

    feature_path = outputs_dir / "premium_features.npz"
    np.savez(
        feature_path,
        premium_feature_vector=feature_vector,
        source_boundary_h5=np.array([str(baseline_h5)], dtype=np.str_),
    )

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
        "feature_summary": feature_dict,
        "notes": [
            "Minimal local backend over boundary/G2_ringdown",
            "Operational but intentionally non-physical",
            "Downstream governance remains separate from this minimal backend",
        ],
    }
    write_json(outputs_dir / "provenance.json", provenance)

    premium_estimate = {
        "schema_version": "premium-estimator-0.1",
        "event_id": args.event_id,
        "estimator_name": args.estimator_name,
        "estimator_version": args.estimator_version,
        "input_artifacts": provenance["input_artifacts"],
        "status": estimator_status,
        "summary_metrics": {
            "n_features": int(len(feature_vector)),
            "is_placeholder": False,
            "backend_enabled": backend_enabled,
            "compute_ran": compute_ran,
            "positive_fraction": positive_fraction,
            "g2_std": g2_std,
            "signal_class": signal_class,
        },
        "feature_paths": {
            "premium_features_npz": str(feature_path),
        },
        "feature_summary": feature_dict,
        "provenance_hash": hashlib.sha256(
            json.dumps(provenance, sort_keys=True).encode("utf-8")
        ).hexdigest(),
    }
    write_json(outputs_dir / "premium_estimate.json", premium_estimate)

    stage_summary = {
        "stage_name": "premium_estimator",
        "status": estimator_status,
        "event_id": args.event_id,
        "estimator_name": args.estimator_name,
        "n_inputs": 1,
        "n_outputs": 4,
        "warnings": [] if estimator_status == "PASS" else [
            "Input behaves as null or degenerate under minimal backend",
        ],
        "blocking_reason": None if estimator_status == "PASS" else "minimal backend found no usable non-null signal",
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
        "request_status": "COMPLETE",
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
        "degraded_allowed_for_stub_only": False,
        "notes": [
            "Auto-generated by premium_estimator.py",
            "Minimal backend completed locally",
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
