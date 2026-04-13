#!/usr/bin/env python3
"""
Minimal BASURIN experiment for auditable baseline vs premium comparison.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import h5py
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.g2_representation_contract import _load_stage02_feature_builder


RUNS_ROOT_DEFAULT = REPO_ROOT / "runs"
CANONICAL_INPUT_DIR_DEFAULT = REPO_ROOT / "runs" / "reopen_v1" / "33_event_effective_contract_pass_stage02_input"
PREMIUM_ESTIMATOR_SCRIPT = REPO_ROOT / "premium_estimator.py"
STAGE_NAME = "baseline_vs_premium"
SCRIPT_VERSION = "run_baseline_vs_premium_experiment.py v0.1"
EXPECTED_RAILS = ("canonical_real", "null", "synthetic", "bias")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_jsonable(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp_", suffix=path.suffix or ".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, indent=2, ensure_ascii=False))
            fh.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _resolve_canonical_h5(input_dir: Path, baseline_h5: Path | None) -> Path:
    if baseline_h5 is not None:
        return baseline_h5.resolve(strict=False)
    h5_files = sorted(input_dir.glob("*.h5"))
    if not h5_files:
        raise FileNotFoundError(f"No canonical H5 files found in {input_dir}")
    return h5_files[0].resolve(strict=False)


def _copy_h5_with_rail(source_h5: Path, target_h5: Path, rail_name: str) -> None:
    target_h5.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_h5, target_h5)
    with h5py.File(target_h5, "r+") as f:
        x = np.asarray(f["boundary/x_grid"][:], dtype=np.float64)
        if rail_name == "canonical_real":
            g2 = np.asarray(f["boundary/G2_ringdown"][:], dtype=np.float64)
        elif rail_name == "null":
            g2 = np.zeros_like(x, dtype=np.float64)
        elif rail_name == "synthetic":
            g2 = np.exp(-0.9 * (x - x.min()))
            g2 = g2 / max(float(g2.max()), 1e-12)
        elif rail_name == "bias":
            src = np.asarray(f["boundary/G2_ringdown"][:], dtype=np.float64)
            g2 = np.clip(np.power(src, 0.5), 0.0, None)
            g2 = g2 / max(float(g2.max()), 1e-12)
        else:
            raise ValueError(f"Unknown rail {rail_name}")

        del f["boundary/G2_ringdown"]
        f["boundary"].create_dataset("G2_ringdown", data=g2)
        f["boundary"].attrs["baseline_vs_premium_rail"] = rail_name


def _boundary_to_dict(boundary_group: h5py.Group) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in boundary_group.keys():
        out[key] = np.asarray(boundary_group[key][...])
    for key, value in boundary_group.attrs.items():
        out[key] = value
    return out


def _compute_baseline_signature(build_feature_vector: Any, boundary_h5: Path) -> dict[str, Any]:
    with h5py.File(boundary_h5, "r") as f:
        if "boundary" not in f:
            raise ValueError("missing group 'boundary'")
        boundary_data = _boundary_to_dict(f["boundary"])

    feature_vector = np.asarray(build_feature_vector(boundary_data, []), dtype=np.float64)
    feature_vector_shape = list(feature_vector.shape)
    is_valid = bool(feature_vector_shape == [20] and np.all(np.isfinite(feature_vector)))
    g2_std_feature = float(feature_vector[7]) if len(feature_vector) > 7 else 0.0
    g2_large_x_feature = float(feature_vector[3]) if len(feature_vector) > 3 else 0.0
    usable_signal = bool(abs(g2_std_feature) > 1e-10 or abs(g2_large_x_feature) > 1e-10)
    rounded = np.round(feature_vector, 6)
    vector_hash = hashlib.sha256(rounded.tobytes()).hexdigest()

    return {
        "status": "PASS" if is_valid else "FAIL",
        "signature": {
            "n_features": int(len(feature_vector)),
            "feature_vector_shape": feature_vector_shape,
            "feature_vector_finite": bool(np.all(np.isfinite(feature_vector))),
            "usable_signal": usable_signal,
            "g2_std_feature": g2_std_feature,
            "g2_large_x_feature": g2_large_x_feature,
            "vector_hash_6dp": vector_hash,
        },
        "feature_vector": feature_vector.tolist(),
    }


def _run_premium_estimator(
    *,
    runs_root: Path,
    top_run_id: str,
    rail_name: str,
    event_id: str,
    boundary_h5: Path,
    logs_dir: Path,
) -> dict[str, Any]:
    rail_run_id = f"{top_run_id}/experiment/baseline_vs_premium/rails/{rail_name}"
    cmd = [
        sys.executable,
        str(PREMIUM_ESTIMATOR_SCRIPT),
        "--run-id",
        rail_run_id,
        "--event-id",
        event_id,
        "--baseline-boundary-h5",
        str(boundary_h5),
        "--runs-dir",
        str(runs_root),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    (logs_dir / f"{rail_name}.stdout.log").write_text(proc.stdout, encoding="utf-8")
    (logs_dir / f"{rail_name}.stderr.log").write_text(proc.stderr, encoding="utf-8")

    rail_stage_dir = runs_root / rail_run_id / "premium_estimator"
    stage_summary_path = rail_stage_dir / "stage_summary.json"
    estimate_path = rail_stage_dir / "outputs" / "premium_estimate.json"
    provenance_path = rail_stage_dir / "outputs" / "provenance.json"

    if proc.returncode != 0:
        raise RuntimeError(f"rail={rail_name} premium_estimator failed: {(proc.stderr or proc.stdout).strip()}")
    for required in (stage_summary_path, estimate_path, provenance_path):
        if not required.exists():
            raise RuntimeError(f"rail={rail_name} missing expected artifact: {required}")

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


def _compute_comparison_metrics(
    event_id: str,
    baseline_results: dict[str, Any],
    premium_results: dict[str, Any],
) -> tuple[dict[str, Any], str, str]:
    baseline_hashes = {
        rail: baseline_results[rail]["signature"]["vector_hash_6dp"]
        for rail in EXPECTED_RAILS
    }
    premium_signatures = {
        rail: premium_results[rail]["signature"]
        for rail in EXPECTED_RAILS
    }
    premium_signature_keys = {
        rail: json.dumps(premium_results[rail]["signature"], sort_keys=True)
        for rail in EXPECTED_RAILS
    }

    baseline_valid_all = all(baseline_results[rail]["status"] == "PASS" for rail in EXPECTED_RAILS)
    premium_backend_enabled_all = all(premium_signatures[rail]["backend_enabled"] for rail in EXPECTED_RAILS)
    premium_non_placeholder_all = all(not premium_signatures[rail]["is_placeholder"] for rail in EXPECTED_RAILS)
    premium_compute_ran_all = all(premium_signatures[rail]["compute_ran"] for rail in EXPECTED_RAILS)
    premium_passes_non_null = all(
        premium_signatures[rail]["estimate_status"] == "PASS"
        for rail in ("canonical_real", "synthetic", "bias")
    )
    premium_null_rejects = premium_signatures["null"]["estimate_status"] != "PASS"
    baseline_usable_by_rail = {
        rail: baseline_results[rail]["signature"]["usable_signal"]
        for rail in EXPECTED_RAILS
    }
    premium_signal_classes = sorted({
        premium_signatures[rail]["signal_class"]
        for rail in EXPECTED_RAILS
        if premium_signatures[rail]["signal_class"] is not None
    })

    baseline_control_signature_distinct = len({baseline_hashes[rail] for rail in ("null", "synthetic", "bias")}) == 3
    premium_control_signature_distinct = len({premium_signature_keys[rail] for rail in ("null", "synthetic", "bias")}) == 3
    premium_has_explicit_class_taxonomy = len(premium_signal_classes) >= 3

    if not (baseline_valid_all and premium_backend_enabled_all and premium_non_placeholder_all and premium_compute_ran_all):
        verdict = "NO_ADVANTAGE"
        verdict_reason = "premium lane did not satisfy minimum operational prerequisites across all rails"
    elif premium_null_rejects and premium_control_signature_distinct and premium_has_explicit_class_taxonomy:
        if not baseline_control_signature_distinct or baseline_usable_by_rail["null"]:
            verdict = "CLEAR_ADVANTAGE"
            verdict_reason = "premium separates null and controlled perturbations under minimum controls where baseline does not"
        else:
            verdict = "LIMITED_ADVANTAGE"
            verdict_reason = "premium adds explicit status/class discrimination, but baseline already separates the same controls at feature-signature level"
    elif premium_null_rejects and premium_control_signature_distinct:
        verdict = "LIMITED_ADVANTAGE"
        verdict_reason = "premium adds operational discrimination under minimum controls, but the gain remains bounded in this minimal experiment"
    else:
        verdict = "NO_ADVANTAGE"
        verdict_reason = "premium did not add material controlled-rail discrimination beyond baseline signatures"

    metrics = {
        "schema_version": "baseline-vs-premium-experiment-0.1",
        "event_id": event_id,
        "rails": list(EXPECTED_RAILS),
        "baseline": {
            rail: baseline_results[rail]["signature"]
            for rail in EXPECTED_RAILS
        },
        "premium": {
            rail: premium_signatures[rail]
            for rail in EXPECTED_RAILS
        },
        "comparative_metrics": {
            "baseline_valid_all": baseline_valid_all,
            "baseline_distinct_signature_count": len(set(baseline_hashes.values())),
            "baseline_control_signature_distinct": baseline_control_signature_distinct,
            "baseline_null_usable_signal": baseline_usable_by_rail["null"],
            "premium_backend_enabled_all": premium_backend_enabled_all,
            "premium_non_placeholder_all": premium_non_placeholder_all,
            "premium_compute_ran_all": premium_compute_ran_all,
            "premium_passes_non_null": premium_passes_non_null,
            "premium_null_rejects": premium_null_rejects,
            "premium_distinct_signature_count": len(set(premium_signature_keys.values())),
            "premium_control_signature_distinct": premium_control_signature_distinct,
            "premium_signal_classes": premium_signal_classes,
            "premium_has_explicit_class_taxonomy": premium_has_explicit_class_taxonomy,
            "class_or_signature_delta": {
                "baseline_uses_feature_signatures": True,
                "premium_has_explicit_status": True,
                "premium_has_explicit_signal_class": True,
            },
        },
        "verdict": verdict,
        "verdict_reason": verdict_reason,
    }
    return metrics, verdict, verdict_reason


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run auditable minimal baseline vs premium BASURIN experiment.")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--runs-root", type=Path, default=RUNS_ROOT_DEFAULT)
    ap.add_argument("--canonical-input-dir", type=Path, default=CANONICAL_INPUT_DIR_DEFAULT)
    ap.add_argument(
        "--baseline-h5",
        type=Path,
        default=None,
        help="Optional canonical H5 anchor. Defaults to first sorted H5 in canonical-input-dir.",
    )
    return ap


def main() -> int:
    args = build_parser().parse_args()

    runs_root = Path(args.runs_root).resolve(strict=False)
    canonical_input_dir = Path(args.canonical_input_dir).resolve(strict=False)
    stage_dir = runs_root / args.run_id / "experiment" / STAGE_NAME
    outputs_dir = stage_dir / "outputs"
    inputs_dir = stage_dir / "inputs"
    logs_dir = stage_dir / "logs"

    try:
        baseline_h5 = _resolve_canonical_h5(canonical_input_dir, args.baseline_h5)
    except FileNotFoundError as exc:
        stage_dir.mkdir(parents=True, exist_ok=True)
        _write_json_atomic(stage_dir / "stage_summary.json", {
            "created_at": _utc_now_iso(),
            "stage_name": STAGE_NAME,
            "status": "FAIL",
            "event_id": None,
            "n_inputs": 0,
            "n_outputs": 0,
            "warnings": [],
            "blocking_reason": str(exc),
            "script": SCRIPT_VERSION,
        })
        _write_json_atomic(stage_dir / "manifest.json", {
            "created_at": _utc_now_iso(),
            "stage": STAGE_NAME,
            "script": SCRIPT_VERSION,
            "parameters": {
                "run_id": args.run_id,
                "canonical_input_dir": str(canonical_input_dir),
                "baseline_h5": str(args.baseline_h5) if args.baseline_h5 else None,
            },
            "status": "FAIL",
        })
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if not PREMIUM_ESTIMATOR_SCRIPT.exists():
        print(f"ERROR: missing premium estimator script: {PREMIUM_ESTIMATOR_SCRIPT}", file=sys.stderr)
        return 2
    if not canonical_input_dir.exists():
        print(f"ERROR: canonical input dir not found: {canonical_input_dir}", file=sys.stderr)
        return 2
    if not baseline_h5.exists():
        print(f"ERROR: canonical baseline H5 not found: {baseline_h5}", file=sys.stderr)
        return 2
    if outputs_dir.exists():
        print(f"ERROR: output directory already exists: {outputs_dir}", file=sys.stderr)
        return 2

    event_id = baseline_h5.stem.replace("__ringdown", "")
    build_feature_vector = _load_stage02_feature_builder(None)

    stage_dir.mkdir(parents=True, exist_ok=True)
    inputs_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    rail_inputs: dict[str, Path] = {}
    for rail_name in EXPECTED_RAILS:
        rail_h5 = inputs_dir / f"{event_id}__{rail_name}.h5"
        _copy_h5_with_rail(baseline_h5, rail_h5, rail_name)
        rail_inputs[rail_name] = rail_h5

    baseline_results: dict[str, Any] = {}
    premium_results: dict[str, Any] = {}
    try:
        for rail_name in EXPECTED_RAILS:
            baseline_results[rail_name] = _compute_baseline_signature(build_feature_vector, rail_inputs[rail_name])
            premium_results[rail_name] = _run_premium_estimator(
                runs_root=runs_root,
                top_run_id=args.run_id,
                rail_name=rail_name,
                event_id=f"{event_id}__{rail_name}",
                boundary_h5=rail_inputs[rail_name],
                logs_dir=logs_dir,
            )
    except Exception as exc:
        stage_summary = {
            "created_at": _utc_now_iso(),
            "stage_name": STAGE_NAME,
            "status": "FAIL",
            "event_id": event_id,
            "n_inputs": len(rail_inputs),
            "n_outputs": 0,
            "warnings": [],
            "blocking_reason": str(exc),
            "script": SCRIPT_VERSION,
        }
        manifest = {
            "created_at": _utc_now_iso(),
            "stage": STAGE_NAME,
            "script": SCRIPT_VERSION,
            "parameters": {
                "run_id": args.run_id,
                "canonical_input_dir": str(canonical_input_dir),
                "baseline_h5": str(baseline_h5),
            },
            "inputs": {
                "canonical_input_dir": str(canonical_input_dir),
                "baseline_h5": str(baseline_h5),
                "rail_inputs": {rail: str(path) for rail, path in rail_inputs.items()},
            },
            "outputs": {
                "logs_dir": str(logs_dir),
                "stage_summary_json": str(stage_dir / "stage_summary.json"),
            },
            "status": "FAIL",
        }
        _write_json_atomic(stage_dir / "stage_summary.json", stage_summary)
        _write_json_atomic(stage_dir / "manifest.json", manifest)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    outputs_dir.mkdir(parents=True, exist_ok=True)
    comparison_metrics, verdict, verdict_reason = _compute_comparison_metrics(
        event_id=event_id,
        baseline_results=baseline_results,
        premium_results=premium_results,
    )
    _write_json_atomic(outputs_dir / "comparison_metrics.json", comparison_metrics)

    comparison_report = {
        "created_at": _utc_now_iso(),
        "script": SCRIPT_VERSION,
        "event_id": event_id,
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "decision_rules": {
            "NO_ADVANTAGE": "premium fails minimum operational checks or adds no material controlled-rail discrimination beyond baseline signatures",
            "LIMITED_ADVANTAGE": "premium adds explicit operational discrimination under the four minimum rails, but the gain remains bounded",
            "CLEAR_ADVANTAGE": "premium adds robust controlled-rail discrimination and baseline misses at least one minimum control",
        },
        "rail_summaries": {
            rail: {
                "input_h5": str(rail_inputs[rail]),
                "baseline_signature": baseline_results[rail]["signature"],
                "premium_signature": premium_results[rail]["signature"],
            }
            for rail in EXPECTED_RAILS
        },
        "limits": [
            "Minimal four-rail operational comparison only",
            "No physical claim implied",
            "Baseline side is a feature-lane signature, not a trained baseline model",
        ],
    }
    _write_json_atomic(outputs_dir / "comparison_report.json", comparison_report)

    provenance = {
        "created_at": _utc_now_iso(),
        "script": SCRIPT_VERSION,
        "event_id": event_id,
        "inputs": {
            "canonical_input_dir": {
                "path": str(canonical_input_dir),
            },
            "baseline_h5": {
                "path": str(baseline_h5),
                "sha256": _sha256_file(baseline_h5),
            },
        },
        "rail_inputs": {
            rail: {
                "path": str(path),
                "sha256": _sha256_file(path),
            }
            for rail, path in rail_inputs.items()
        },
        "premium_commands": {
            rail: premium_results[rail]["command"]
            for rail in EXPECTED_RAILS
        },
        "baseline_feature_builder_source": "tools.g2_representation_contract._load_stage02_feature_builder",
    }
    _write_json_atomic(outputs_dir / "provenance.json", provenance)

    warnings: list[str] = []
    if verdict == "LIMITED_ADVANTAGE":
        warnings.append("premium advantage is bounded because baseline signatures already separate the minimum control rails")
    stage_summary = {
        "created_at": _utc_now_iso(),
        "stage_name": STAGE_NAME,
        "status": "PASS",
        "event_id": event_id,
        "n_inputs": len(EXPECTED_RAILS),
        "n_outputs": 3,
        "warnings": warnings,
        "blocking_reason": None,
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "script": SCRIPT_VERSION,
    }
    _write_json_atomic(stage_dir / "stage_summary.json", stage_summary)

    manifest = {
        "created_at": _utc_now_iso(),
        "stage": STAGE_NAME,
        "script": SCRIPT_VERSION,
        "parameters": {
            "run_id": args.run_id,
            "canonical_input_dir": str(canonical_input_dir),
            "baseline_h5": str(baseline_h5),
        },
        "inputs": {
            "canonical_input_dir": {
                "path": str(canonical_input_dir),
            },
            "baseline_h5": {
                "path": str(baseline_h5),
                "sha256": _sha256_file(baseline_h5),
            },
            "rail_inputs": {
                rail: {
                    "path": str(path),
                    "sha256": _sha256_file(path),
                }
                for rail, path in rail_inputs.items()
            },
        },
        "outputs": {
            "inputs_dir": str(inputs_dir),
            "logs_dir": str(logs_dir),
            "comparison_metrics_json": {
                "path": str(outputs_dir / "comparison_metrics.json"),
                "sha256": _sha256_file(outputs_dir / "comparison_metrics.json"),
            },
            "comparison_report_json": {
                "path": str(outputs_dir / "comparison_report.json"),
                "sha256": _sha256_file(outputs_dir / "comparison_report.json"),
            },
            "provenance_json": {
                "path": str(outputs_dir / "provenance.json"),
                "sha256": _sha256_file(outputs_dir / "provenance.json"),
            },
            "stage_summary_json": str(stage_dir / "stage_summary.json"),
        },
        "rails": {
            rail: {
                "baseline_signature": baseline_results[rail]["signature"],
                "premium_signature": premium_results[rail]["signature"],
                "premium_stage_dir": premium_results[rail]["stage_dir"],
            }
            for rail in EXPECTED_RAILS
        },
        "status": "PASS",
    }
    _write_json_atomic(stage_dir / "manifest.json", manifest)

    print(f"[OK] stage_dir: {stage_dir}")
    print(f"[OK] verdict: {verdict}")
    print(f"[OK] report: {outputs_dir / 'comparison_report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
