#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
import shutil
import sys
import tempfile
from collections import Counter
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import h5py


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT_DEFAULT = REPO_ROOT / "runs"
INPUT_DIR_DEFAULT = REPO_ROOT / "runs" / "reopen_v1" / "82_event_unified_stage02_input"
CHECKPOINT_DEFAULT = REPO_ROOT / "runs" / "reopen_v1" / "02_emergent_geometry_engine" / "emergent_geometry_model.pt"
CONTROL33_SUMMARY_DEFAULT = (
    REPO_ROOT / "runs" / "reopen_v1" / "33_event_effective_contract_pass_strict_validation" / "emergent_geometry_summary.json"
)
ENGINE_SCRIPT = REPO_ROOT / "02_emergent_geometry_engine.py"
STAGE_NAME = "experiment/emergent_geometry_engine_on_unified82"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _write_json_atomic(path: Path, payload: Any) -> None:
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


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_engine_module(script_path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("basurin_stage02_engine", script_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load engine module from {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _family_counts(summary_payload: dict[str, Any]) -> dict[str, int]:
    counter = Counter()
    for item in summary_payload.get("systems", []):
        counter[str(item.get("family_pred", "unknown"))] += 1
    return dict(sorted(counter.items()))


def _family_mode_counts(summary_payload: dict[str, Any]) -> dict[str, int]:
    counter = Counter()
    for item in summary_payload.get("systems", []):
        counter[str(item.get("family_classification_mode", "unknown"))] += 1
    return dict(sorted(counter.items()))


def _family_abstention_stats(summary_payload: dict[str, Any]) -> dict[str, Any]:
    systems = summary_payload.get("systems", [])
    n_total = len(systems)
    n_abstained = sum(1 for item in systems if bool(item.get("family_pred_was_abstained", False)))
    n_confident = sum(1 for item in systems if bool(item.get("family_pred_confident", False)))
    return {
        "family_output_semantics": str(summary_payload.get("systems", [{}])[0].get("family_output_semantics", "unknown")) if systems else "unknown",
        "family_classification_mode_counts": _family_mode_counts(summary_payload),
        "n_abstained": n_abstained,
        "n_confident": n_confident,
        "abstained_fraction": (n_abstained / n_total) if n_total else None,
        "confident_fraction": (n_confident / n_total) if n_total else None,
    }


def _zh_stats(summary_payload: dict[str, Any]) -> dict[str, float | None]:
    values = [float(item["zh_pred"]) for item in summary_payload.get("systems", []) if item.get("zh_pred") is not None]
    if not values:
        return {"min": None, "max": None, "mean": None}
    return {
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
    }


def _rewrite_stage_paths(value: Any, src_root: Path, dst_root: Path) -> Any:
    src_str = str(src_root)
    dst_str = str(dst_root)
    if isinstance(value, dict):
        return {k: _rewrite_stage_paths(v, src_root, dst_root) for k, v in value.items()}
    if isinstance(value, list):
        return [_rewrite_stage_paths(v, src_root, dst_root) for v in value]
    if isinstance(value, str):
        return value.replace(src_str, dst_str)
    return value


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run stage 02 emergent geometry inference on the unified 82-event cohort.")
    ap.add_argument("--run-id", required=True, help="Run identifier under runs/<run_id>/experiment/emergent_geometry_engine_on_unified82/")
    ap.add_argument("--runs-root", type=Path, default=RUNS_ROOT_DEFAULT)
    ap.add_argument("--input-dir", type=Path, default=INPUT_DIR_DEFAULT)
    ap.add_argument("--checkpoint", type=Path, default=CHECKPOINT_DEFAULT)
    ap.add_argument("--control33-summary", type=Path, default=CONTROL33_SUMMARY_DEFAULT)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--support-mode", choices=("strict", "permissive_ood"), default="permissive_ood")
    return ap


def main() -> int:
    args = build_parser().parse_args()
    runs_root = Path(args.runs_root).resolve(strict=False)
    input_dir = Path(args.input_dir).resolve(strict=False)
    checkpoint = Path(args.checkpoint).resolve(strict=False)
    control33_summary = Path(args.control33_summary).resolve(strict=False)

    final_stage_dir = runs_root / args.run_id / "experiment" / "emergent_geometry_engine_on_unified82"
    tmp_stage_dir = runs_root / args.run_id / "experiment" / f".tmp_emergent_geometry_engine_on_unified82_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    outputs_dir = tmp_stage_dir / "outputs"
    logs_dir = tmp_stage_dir / "logs"

    required_inputs = [
        input_dir,
        input_dir / "cohort_summary.json",
        input_dir / "geometries_manifest.json",
        checkpoint,
        control33_summary,
        ENGINE_SCRIPT,
    ]
    missing = [str(path) for path in required_inputs if not path.exists()]
    if missing:
        raise SystemExit(f"FATAL: missing required contractual input: {missing[0]}")
    if final_stage_dir.exists():
        raise SystemExit(f"FATAL: output dir already exists: {final_stage_dir}")
    if tmp_stage_dir.exists():
        raise SystemExit(f"FATAL: temporary output dir already exists: {tmp_stage_dir}")

    h5_files = sorted(input_dir.glob("*.h5"))
    if len(h5_files) != 82:
        raise SystemExit(f"FATAL: expected 82 H5 inputs in {input_dir}, found {len(h5_files)}")

    outputs_dir.mkdir(parents=True, exist_ok=False)
    logs_dir.mkdir(parents=True, exist_ok=False)
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()

    engine_args = SimpleNamespace(
        checkpoint=str(checkpoint),
        data_dir=str(input_dir),
        output_dir=str(outputs_dir),
        device=args.device,
        verbose=True,
        support_mode=args.support_mode,
    )

    try:
        engine_module = _load_engine_module(ENGINE_SCRIPT)
        if getattr(engine_module, "h5py", None) is None:
            engine_module.h5py = h5py
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            engine_module.run_inference_mode(engine_args)

        summary_path = outputs_dir / "emergent_geometry_summary.json"
        geom_dir = outputs_dir / "geometry_emergent"
        preds_dir = outputs_dir / "predictions"
        required_outputs = [summary_path, geom_dir, preds_dir]
        missing_outputs = [str(path) for path in required_outputs if not path.exists()]
        if missing_outputs:
            raise RuntimeError(f"engine did not produce required output: {missing_outputs[0]}")

        emergent_summary = _load_json(summary_path)
        emergent_h5_count = len(list(geom_dir.glob("*_emergent.h5")))
        prediction_count = len(list(preds_dir.glob("*_geometry.npz")))
        if emergent_summary.get("n_systems") != 82:
            raise RuntimeError(
                "engine summary did not report 82 systems "
                f"(reported {emergent_summary.get('n_systems')})"
            )
        if emergent_h5_count != 82:
            raise RuntimeError(f"engine produced {emergent_h5_count} emergent H5 files, expected 82")
        if prediction_count != 82:
            raise RuntimeError(f"engine produced {prediction_count} prediction NPZ files, expected 82")

        emergent_summary = _rewrite_stage_paths(emergent_summary, tmp_stage_dir, final_stage_dir)
        _write_json_atomic(summary_path, emergent_summary)

        control33 = _load_json(control33_summary)
        aggregate_summary = {
            "created_at": _utc_now_iso(),
            "stage": STAGE_NAME,
            "lane": "02_emergent_geometry_engine",
            "cohort_role": "operational_mainline",
            "input_dir": str(input_dir),
            "checkpoint": str(checkpoint),
            "support_mode": args.support_mode,
            "n_input_h5": len(h5_files),
            "n_systems_inferred": emergent_summary.get("n_systems"),
            "n_emergent_h5": emergent_h5_count,
            "n_prediction_npz": prediction_count,
            "family_pred_counts": _family_counts(emergent_summary),
            **_family_abstention_stats(emergent_summary),
            "zh_pred_stats": _zh_stats(emergent_summary),
            "control33_comparison": {
                "control_n_systems": control33.get("n_systems"),
                "control_family_pred_counts": _family_counts(control33),
                "control_zh_pred_stats": _zh_stats(control33),
            },
        }

        stage_summary = {
            "created_at": _utc_now_iso(),
            "stage": STAGE_NAME,
            "status": "PASS",
            "lane": "02_emergent_geometry_engine",
            "cohort_role": "operational_mainline",
            "support_mode": args.support_mode,
            "n_input_h5": len(h5_files),
            "n_systems_inferred": emergent_summary.get("n_systems"),
            "n_emergent_h5": emergent_h5_count,
            "n_prediction_npz": prediction_count,
            **_family_abstention_stats(emergent_summary),
            "checkpoint": str(checkpoint),
            "comparison_control33_available": True,
            "warnings": [
                "Inference-only run using the frozen sandbox checkpoint",
                "Permissive OOD support mode is used to keep the unified82 cohort operational",
                "Family output is exposed as compatibility_with_abstention; strong family labels are emitted only when confidence thresholds are met",
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
                "--checkpoint",
                str(checkpoint),
                "--control33-summary",
                str(control33_summary),
                "--device",
                args.device,
                "--support-mode",
                args.support_mode,
            ],
            "engine_delegate": {
                "script": str(ENGINE_SCRIPT),
                "function": "run_inference_mode",
                "checkpoint": str(checkpoint),
                "data_dir": str(input_dir),
                "output_dir": str(final_stage_dir / "outputs"),
            },
            "inputs": {
                "input_dir": {
                    "path": str(input_dir),
                    "h5_listing_sha256": hashlib.sha256(
                        "\n".join(sorted(path.name for path in h5_files)).encode("utf-8")
                    ).hexdigest(),
                },
                "cohort_summary_json": {
                    "path": str(input_dir / "cohort_summary.json"),
                    "sha256": _sha256_file(input_dir / "cohort_summary.json"),
                },
                "checkpoint": {
                    "path": str(checkpoint),
                    "sha256": _sha256_file(checkpoint),
                },
                "control33_summary": {
                    "path": str(control33_summary),
                    "sha256": _sha256_file(control33_summary),
                },
            },
            "outputs": {
                "manifest_json": "manifest.json",
                "stage_summary_json": "stage_summary.json",
                "aggregate_summary_json": "outputs/aggregate_unified82_emergent_summary.json",
                "engine_summary_json": "outputs/emergent_geometry_summary.json",
                "geometry_emergent_dir": "outputs/geometry_emergent",
                "predictions_dir": "outputs/predictions",
                "stdout_log": "logs/stdout.log",
                "stderr_log": "logs/stderr.log",
            },
        }

        _write_json_atomic(outputs_dir / "aggregate_unified82_emergent_summary.json", aggregate_summary)
        _write_json_atomic(tmp_stage_dir / "stage_summary.json", stage_summary)
        _write_json_atomic(tmp_stage_dir / "manifest.json", manifest)
        (logs_dir / "stdout.log").write_text(stdout_buffer.getvalue(), encoding="utf-8")
        (logs_dir / "stderr.log").write_text(stderr_buffer.getvalue(), encoding="utf-8")
        os.replace(tmp_stage_dir, final_stage_dir)
    except Exception as exc:
        if tmp_stage_dir.exists():
            shutil.rmtree(tmp_stage_dir)
        raise SystemExit(f"FATAL: {exc}")

    print(f"[OK] emergent geometry run published at {final_stage_dir}")
    print(f"[OK] engine outputs: {final_stage_dir / 'outputs'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
