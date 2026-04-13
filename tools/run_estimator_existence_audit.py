#!/usr/bin/env python3
"""
Minimal BASURIN experiment closing the estimator existence gate.
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
RUNS_ROOT_DEFAULT = REPO_ROOT / "runs"
CANONICAL_INPUT_DIR_DEFAULT = REPO_ROOT / "runs" / "reopen_v1" / "33_event_effective_contract_pass_stage02_input"
PREMIUM_ESTIMATOR_SCRIPT = REPO_ROOT / "premium_estimator.py"
ESTIMATORS_REGISTRY = REPO_ROOT / "estimators_registry.json"
STAGE_NAME = "experiment/estimator_existence_audit"


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


def _copy_h5_with_g2_variant(source_h5: Path, target_h5: Path, rail_name: str) -> None:
    target_h5.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_h5, target_h5)
    with h5py.File(target_h5, "r+") as f:
        x = f["boundary/x_grid"][:]
        if rail_name == "null":
            g2 = np.zeros_like(x, dtype=np.float64)
        elif rail_name == "synthetic":
            g2 = np.exp(-0.9 * (x - x.min()))
            g2 = g2 / max(float(g2.max()), 1e-12)
        elif rail_name == "bias":
            src = f["boundary/G2_ringdown"][:].astype(np.float64)
            g2 = np.clip(np.power(src, 0.5), 0.0, None)
            g2 = g2 / max(float(g2.max()), 1e-12)
        else:
            raise ValueError(f"Unknown rail {rail_name}")

        del f["boundary/G2_ringdown"]
        f["boundary"].create_dataset("G2_ringdown", data=g2)
        f["boundary"].attrs["estimator_existence_audit_rail"] = rail_name


def _run_premium_estimator(
    *,
    runs_root: Path,
    top_run_id: str,
    rail_name: str,
    event_id: str,
    baseline_h5: Path,
    logs_dir: Path,
) -> dict[str, Any]:
    rail_run_id = f"{top_run_id}/experiment/estimator_existence_audit/rails/{rail_name}"
    cmd = [
        sys.executable,
        str(PREMIUM_ESTIMATOR_SCRIPT),
        "--run-id",
        rail_run_id,
        "--event-id",
        event_id,
        "--baseline-boundary-h5",
        str(baseline_h5),
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
        "is_placeholder": bool(estimate.get("summary_metrics", {}).get("is_placeholder", True)),
        "backend_enabled": bool(estimate.get("summary_metrics", {}).get("backend_enabled", False)),
        "n_features": int(estimate.get("summary_metrics", {}).get("n_features", 0)),
        "signal_class": estimate.get("summary_metrics", {}).get("signal_class", "unknown"),
    }
    return {
        "rail_name": rail_name,
        "command": cmd,
        "input_h5": str(baseline_h5),
        "stage_dir": str(rail_stage_dir),
        "stage_summary_path": str(stage_summary_path),
        "estimate_path": str(estimate_path),
        "provenance_path": str(provenance_path),
        "stage_summary": stage_summary,
        "estimate": estimate,
        "signature": signature,
    }


def _compute_verdict(rail_results: list[dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    by_name = {item["rail_name"]: item for item in rail_results}
    null_sig = by_name["null"]["signature"]
    synthetic_sig = by_name["synthetic"]["signature"]
    bias_sig = by_name["bias"]["signature"]

    synthetic_usable = (
        synthetic_sig["stage_status"] == "PASS"
        and synthetic_sig["estimate_status"] == "PASS"
        and not synthetic_sig["is_placeholder"]
    )
    null_false_positive = (
        null_sig["stage_status"] == "PASS"
        and null_sig["estimate_status"] == "PASS"
        and not null_sig["is_placeholder"]
    )
    distinct_signatures = len({
        json.dumps(null_sig, sort_keys=True),
        json.dumps(synthetic_sig, sort_keys=True),
        json.dumps(bias_sig, sort_keys=True),
    }) > 1
    bias_distinguishable = json.dumps(bias_sig, sort_keys=True) != json.dumps(synthetic_sig, sort_keys=True)

    if not synthetic_usable:
        verdict = "FAILS"
        reason = "synthetic rail did not produce a non-placeholder PASS result"
    elif null_false_positive:
        verdict = "FAILS"
        reason = "null rail produced a non-placeholder PASS result"
    elif not distinct_signatures or not bias_distinguishable:
        verdict = "BOUNDED"
        reason = "estimator response remains insufficiently sensitive across null/synthetic/bias rails"
    else:
        verdict = "SURVIVES"
        reason = "synthetic rail is usable, null does not raise a false positive, and bias is distinguishable"

    return verdict, {
        "synthetic_usable": synthetic_usable,
        "null_false_positive": null_false_positive,
        "distinct_signatures": distinct_signatures,
        "bias_distinguishable": bias_distinguishable,
        "verdict_reason": reason,
    }


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run BASURIN estimator existence audit with null/synthetic/bias rails.")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--runs-root", type=Path, default=RUNS_ROOT_DEFAULT)
    ap.add_argument("--canonical-input-dir", type=Path, default=CANONICAL_INPUT_DIR_DEFAULT)
    ap.add_argument("--baseline-h5", type=Path, default=None, help="Optional canonical H5 anchor. Defaults to first sorted H5 in canonical-input-dir.")
    return ap


def main() -> int:
    args = build_parser().parse_args()

    runs_root = Path(args.runs_root).resolve(strict=False)
    canonical_input_dir = Path(args.canonical_input_dir).resolve(strict=False)
    stage_dir = runs_root / args.run_id / "experiment" / "estimator_existence_audit"
    outputs_dir = stage_dir / "outputs"
    inputs_dir = stage_dir / "inputs"
    logs_dir = stage_dir / "logs"

    if not PREMIUM_ESTIMATOR_SCRIPT.exists():
        print(f"ERROR: missing premium estimator script: {PREMIUM_ESTIMATOR_SCRIPT}", file=sys.stderr)
        return 2
    if not ESTIMATORS_REGISTRY.exists():
        print(f"ERROR: missing estimators registry: {ESTIMATORS_REGISTRY}", file=sys.stderr)
        return 2
    if not canonical_input_dir.exists():
        print(f"ERROR: canonical input dir not found: {canonical_input_dir}", file=sys.stderr)
        return 2

    try:
        baseline_h5 = _resolve_canonical_h5(canonical_input_dir, args.baseline_h5)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if not baseline_h5.exists():
        print(f"ERROR: canonical baseline H5 not found: {baseline_h5}", file=sys.stderr)
        return 2

    event_id = baseline_h5.stem.replace("__ringdown", "")
    stage_dir.mkdir(parents=True, exist_ok=True)
    if outputs_dir.exists():
        print(f"ERROR: output directory already exists: {outputs_dir}", file=sys.stderr)
        return 2
    inputs_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    rail_inputs = {}
    for rail_name in ("null", "synthetic", "bias"):
        rail_h5 = inputs_dir / f"{event_id}__{rail_name}.h5"
        _copy_h5_with_g2_variant(baseline_h5, rail_h5, rail_name)
        rail_inputs[rail_name] = rail_h5

    rail_results = []
    try:
        for rail_name in ("null", "synthetic", "bias"):
            rail_results.append(
                _run_premium_estimator(
                    runs_root=runs_root,
                    top_run_id=args.run_id,
                    rail_name=rail_name,
                    event_id=f"{event_id}__{rail_name}",
                    baseline_h5=rail_inputs[rail_name],
                    logs_dir=logs_dir,
                )
            )
    except Exception as exc:
        stage_summary = {
            "created_at": _utc_now_iso(),
            "stage": STAGE_NAME,
            "status": "ERROR",
            "exit_code": 2,
            "error_message": str(exc),
            "input_root": str(canonical_input_dir),
            "output_dir": str(stage_dir),
        }
        manifest = {
            "created_at": _utc_now_iso(),
            "stage": STAGE_NAME,
            "script": str(Path(__file__).resolve()),
            "inputs": {
                "canonical_input_dir": str(canonical_input_dir),
                "baseline_h5": str(baseline_h5),
                "estimators_registry_json": str(ESTIMATORS_REGISTRY),
            },
            "outputs": {
                "stage_summary_json": str(stage_dir / "stage_summary.json"),
                "logs_dir": str(logs_dir),
            },
            "status": "ERROR",
        }
        _write_json_atomic(stage_dir / "stage_summary.json", stage_summary)
        _write_json_atomic(stage_dir / "manifest.json", manifest)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    outputs_dir.mkdir(parents=True, exist_ok=True)
    verdict, verdict_metrics = _compute_verdict(rail_results)
    outputs_payload = {
        "created_at": _utc_now_iso(),
        "baseline_h5": str(baseline_h5),
        "rail_results": rail_results,
        "verdict": verdict,
        "verdict_metrics": verdict_metrics,
    }
    _write_json_atomic(outputs_dir / "existence_audit_report.json", outputs_payload)

    stage_summary = {
        "created_at": _utc_now_iso(),
        "stage": STAGE_NAME,
        "status": "OK",
        "exit_code": 0,
        "verdict": verdict,
        "verdict_reason": verdict_metrics["verdict_reason"],
        "n_rails": len(rail_results),
        "baseline_event_id": event_id,
        "synthetic_usable": verdict_metrics["synthetic_usable"],
        "null_false_positive": verdict_metrics["null_false_positive"],
        "distinct_signatures": verdict_metrics["distinct_signatures"],
        "bias_distinguishable": verdict_metrics["bias_distinguishable"],
        "output_report": str(outputs_dir / "existence_audit_report.json"),
    }
    _write_json_atomic(stage_dir / "stage_summary.json", stage_summary)

    manifest = {
        "created_at": _utc_now_iso(),
        "stage": STAGE_NAME,
        "script": str(Path(__file__).resolve()),
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
            "estimators_registry_json": {
                "path": str(ESTIMATORS_REGISTRY),
                "sha256": _sha256_file(ESTIMATORS_REGISTRY),
            },
        },
        "outputs": {
            "inputs_dir": str(inputs_dir),
            "logs_dir": str(logs_dir),
            "report_json": {
                "path": str(outputs_dir / "existence_audit_report.json"),
                "sha256": _sha256_file(outputs_dir / "existence_audit_report.json"),
            },
            "stage_summary_json": str(stage_dir / "stage_summary.json"),
        },
        "rails": {
            item["rail_name"]: {
                "input_h5": item["input_h5"],
                "stage_dir": item["stage_dir"],
                "stage_summary_path": item["stage_summary_path"],
                "estimate_path": item["estimate_path"],
                "signature": item["signature"],
            }
            for item in rail_results
        },
        "status": "OK",
    }
    _write_json_atomic(stage_dir / "manifest.json", manifest)

    print(f"[OK] stage_dir: {stage_dir}")
    print(f"[OK] verdict: {verdict}")
    print(f"[OK] report: {outputs_dir / 'existence_audit_report.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
