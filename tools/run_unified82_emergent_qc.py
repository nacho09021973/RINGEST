#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT_DEFAULT = REPO_ROOT / "runs"
INPUT_OUTPUTS_DEFAULT = (
    REPO_ROOT
    / "runs"
    / "unified82_emergent_geometry_20260413_run2"
    / "experiment"
    / "emergent_geometry_engine_on_unified82"
    / "outputs"
)
CONTROL33_SUMMARY_DEFAULT = (
    REPO_ROOT
    / "runs"
    / "reopen_v1"
    / "33_event_effective_contract_pass_strict_validation"
    / "emergent_geometry_summary.json"
)
STAGE_NAME = "experiment/unified82_emergent_qc"


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


def _family_counts(summary_payload: dict[str, Any]) -> dict[str, int]:
    counter = Counter()
    for item in summary_payload.get("systems", []):
        counter[str(item.get("family_pred", "unknown"))] += 1
    return dict(sorted(counter.items()))


def _zh_values(summary_payload: dict[str, Any]) -> list[float]:
    values: list[float] = []
    for item in summary_payload.get("systems", []):
        zh = item.get("zh_pred")
        if zh is None:
            continue
        values.append(float(zh))
    return values


def _zh_stats(values: list[float]) -> dict[str, float | None]:
    finite_values = [value for value in values if math.isfinite(value)]
    if not finite_values:
        return {"min": None, "max": None, "mean": None}
    return {
        "min": min(finite_values),
        "max": max(finite_values),
        "mean": sum(finite_values) / len(finite_values),
    }


def _confidence_values(summary_payload: dict[str, Any], key: str) -> list[float]:
    values: list[float] = []
    for item in summary_payload.get("systems", []):
        value = item.get(key)
        if value is None:
            continue
        values.append(float(value))
    return values


def _simple_stats(values: list[float]) -> dict[str, float | None]:
    finite_values = [value for value in values if math.isfinite(value)]
    if not finite_values:
        return {"min": None, "max": None, "mean": None}
    return {
        "min": min(finite_values),
        "max": max(finite_values),
        "mean": sum(finite_values) / len(finite_values),
    }


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Minimal post-inference QC for unified82 emergent geometry outputs.")
    ap.add_argument("--run-id", required=True, help="Run identifier under runs/<run_id>/experiment/unified82_emergent_qc/")
    ap.add_argument("--runs-root", type=Path, default=RUNS_ROOT_DEFAULT)
    ap.add_argument("--input-outputs-dir", type=Path, default=INPUT_OUTPUTS_DEFAULT)
    ap.add_argument("--control33-summary", type=Path, default=CONTROL33_SUMMARY_DEFAULT)
    return ap


def main() -> int:
    args = build_parser().parse_args()
    runs_root = Path(args.runs_root).resolve(strict=False)
    input_outputs_dir = Path(args.input_outputs_dir).resolve(strict=False)
    control33_summary = Path(args.control33_summary).resolve(strict=False)

    final_stage_dir = runs_root / args.run_id / "experiment" / "unified82_emergent_qc"
    tmp_stage_dir = runs_root / args.run_id / "experiment" / f".tmp_unified82_emergent_qc_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    outputs_dir = tmp_stage_dir / "outputs"
    logs_dir = tmp_stage_dir / "logs"

    emergent_summary_path = input_outputs_dir / "emergent_geometry_summary.json"
    required = [input_outputs_dir, emergent_summary_path]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit(f"FATAL: missing required input: {missing[0]}")
    if final_stage_dir.exists():
        raise SystemExit(f"FATAL: output dir already exists: {final_stage_dir}")
    if tmp_stage_dir.exists():
        raise SystemExit(f"FATAL: temporary output dir already exists: {tmp_stage_dir}")

    outputs_dir.mkdir(parents=True, exist_ok=False)
    logs_dir.mkdir(parents=True, exist_ok=False)

    try:
        emergent_summary = _load_json(emergent_summary_path)
        family_counts = _family_counts(emergent_summary)
        zh_values = _zh_values(emergent_summary)
        n_total = int(emergent_summary.get("n_systems", len(zh_values)))
        n_nonfinite = sum(1 for value in zh_values if not math.isfinite(value))
        n_negative = sum(1 for value in zh_values if math.isfinite(value) and value < 0.0)
        n_zero = sum(1 for value in zh_values if math.isfinite(value) and value == 0.0)
        family_top1_scores = _confidence_values(emergent_summary, "family_top1_score")
        family_top2_scores = _confidence_values(emergent_summary, "family_top2_score")
        family_margins = _confidence_values(emergent_summary, "family_margin")
        family_entropies = _confidence_values(emergent_summary, "family_entropy")
        dominant_family, dominant_count = max(family_counts.items(), key=lambda kv: kv[1])
        dominant_fraction = dominant_count / n_total if n_total else 0.0
        family_collapse = len(family_counts) == 1 or dominant_fraction >= 0.95
        confidence_available = len(family_top1_scores) == n_total and len(family_margins) == n_total
        low_confidence_fraction = (
            sum(1 for score, margin in zip(family_top1_scores, family_margins) if score < 0.6 or margin < 0.2) / n_total
            if confidence_available and n_total
            else None
        )
        family_collapse_due_to_low_confidence = bool(family_collapse and low_confidence_fraction is not None and low_confidence_fraction >= 0.5)
        family_collapse_true_confident = bool(family_collapse and low_confidence_fraction is not None and low_confidence_fraction < 0.5)

        if n_nonfinite > 0:
            verdict = "NEEDS_REVIEW"
            verdict_reason = f"{n_nonfinite} zh_pred values are non-finite"
        elif n_total and (n_negative / n_total) >= 0.05:
            verdict = "NEEDS_REVIEW"
            verdict_reason = f"{n_negative}/{n_total} zh_pred values are negative"
        elif family_collapse or n_negative > 0 or n_zero > 0:
            verdict = "USABLE_WITH_WARNINGS"
            issues = []
            if family_collapse:
                issues.append(f"family collapse to {dominant_family} ({dominant_count}/{n_total})")
            if n_negative > 0:
                issues.append(f"{n_negative} negative zh_pred values")
            if n_zero > 0:
                issues.append(f"{n_zero} zero zh_pred values")
            verdict_reason = "; ".join(issues)
        else:
            verdict = "USABLE_FOR_DOWNSTREAM"
            verdict_reason = "no relevant aggregated anomalies detected"

        control_summary = _load_json(control33_summary) if control33_summary.exists() else None
        family_report = {
            "created_at": _utc_now_iso(),
            "n_systems": n_total,
            "family_pred_counts": family_counts,
            "dominant_family": dominant_family,
            "dominant_family_fraction": dominant_fraction,
            "family_collapse": family_collapse,
            "family_confidence_available": confidence_available,
            "family_top1_score_stats": _simple_stats(family_top1_scores),
            "family_top2_score_stats": _simple_stats(family_top2_scores),
            "family_margin_stats": _simple_stats(family_margins),
            "family_entropy_stats": _simple_stats(family_entropies),
            "low_confidence_fraction": low_confidence_fraction,
            "family_collapse_true_confident": family_collapse_true_confident,
            "family_collapse_due_to_low_confidence": family_collapse_due_to_low_confidence,
        }
        zh_report = {
            "created_at": _utc_now_iso(),
            "n_systems": n_total,
            "stats": _zh_stats(zh_values),
            "n_negative": n_negative,
            "n_zero": n_zero,
            "n_nonfinite": n_nonfinite,
            "negative_fraction": (n_negative / n_total) if n_total else None,
        }
        qc_summary = {
            "created_at": _utc_now_iso(),
            "stage": STAGE_NAME,
            "input_outputs_dir": str(input_outputs_dir),
            "n_systems": n_total,
            "verdict": verdict,
            "verdict_reason": verdict_reason,
            "family_pred_counts": family_counts,
            "dominant_family": dominant_family,
            "dominant_family_fraction": dominant_fraction,
            "family_collapse": family_collapse,
            "family_confidence_available": confidence_available,
            "family_top1_score_stats": _simple_stats(family_top1_scores),
            "family_top2_score_stats": _simple_stats(family_top2_scores),
            "family_margin_stats": _simple_stats(family_margins),
            "family_entropy_stats": _simple_stats(family_entropies),
            "low_confidence_fraction": low_confidence_fraction,
            "family_collapse_true_confident": family_collapse_true_confident,
            "family_collapse_due_to_low_confidence": family_collapse_due_to_low_confidence,
            "zh_pred_stats": zh_report["stats"],
            "n_negative_zh_pred": n_negative,
            "n_zero_zh_pred": n_zero,
            "n_nonfinite_zh_pred": n_nonfinite,
            "control33_comparison": {
                "available": control_summary is not None,
                "n_systems": control_summary.get("n_systems") if control_summary else None,
                "family_pred_counts": _family_counts(control_summary) if control_summary else None,
                "zh_pred_stats": _zh_stats(_zh_values(control_summary)) if control_summary else None,
            },
        }
        stage_summary = {
            "created_at": _utc_now_iso(),
            "stage": STAGE_NAME,
            "status": "PASS",
            "n_systems": n_total,
            "verdict": verdict,
            "verdict_reason": verdict_reason,
            "family_collapse": family_collapse,
            "family_confidence_available": confidence_available,
            "family_collapse_true_confident": family_collapse_true_confident,
            "family_collapse_due_to_low_confidence": family_collapse_due_to_low_confidence,
            "n_negative_zh_pred": n_negative,
            "n_zero_zh_pred": n_zero,
            "n_nonfinite_zh_pred": n_nonfinite,
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
                "--input-outputs-dir",
                str(input_outputs_dir),
                "--control33-summary",
                str(control33_summary),
            ],
            "inputs": {
                "input_outputs_dir": str(input_outputs_dir),
                "emergent_geometry_summary_json": {
                    "path": str(emergent_summary_path),
                    "sha256": _sha256_file(emergent_summary_path),
                },
                "control33_summary_json": {
                    "path": str(control33_summary),
                    "sha256": _sha256_file(control33_summary),
                } if control33_summary.exists() else None,
            },
            "outputs": {
                "manifest_json": "manifest.json",
                "stage_summary_json": "stage_summary.json",
                "qc_summary_json": "outputs/qc_summary.json",
                "family_pred_report_json": "outputs/family_pred_report.json",
                "zh_pred_report_json": "outputs/zh_pred_report.json",
                "stdout_log": "logs/stdout.log",
                "stderr_log": "logs/stderr.log",
            },
        }

        _write_json_atomic(outputs_dir / "qc_summary.json", qc_summary)
        _write_json_atomic(outputs_dir / "family_pred_report.json", family_report)
        _write_json_atomic(outputs_dir / "zh_pred_report.json", zh_report)
        _write_json_atomic(tmp_stage_dir / "stage_summary.json", stage_summary)
        _write_json_atomic(tmp_stage_dir / "manifest.json", manifest)
        (logs_dir / "stdout.log").write_text(
            f"verdict={verdict}\nverdict_reason={verdict_reason}\nn_systems={n_total}\n",
            encoding="utf-8",
        )
        (logs_dir / "stderr.log").write_text("", encoding="utf-8")
        os.replace(tmp_stage_dir, final_stage_dir)
    except Exception as exc:
        if tmp_stage_dir.exists():
            shutil.rmtree(tmp_stage_dir)
        raise SystemExit(f"FATAL: {exc}")

    print(f"[OK] QC run published at {final_stage_dir}")
    print(f"[OK] verdict: {verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
