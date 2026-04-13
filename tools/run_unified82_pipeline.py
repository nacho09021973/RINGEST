#!/usr/bin/env python3
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


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT_DEFAULT = REPO_ROOT / "runs"
INPUT_DIR_DEFAULT = REPO_ROOT / "runs" / "reopen_v1" / "82_event_unified_stage02_input"
FULLCOHORT_WRAPPER = REPO_ROOT / "tools" / "run_fullcohort_90_physics_probe.py"
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
REQUIRED_INCLUDED = {
    "GW170817__ringdown.h5",
    "GW190517_055101__ringdown.h5",
}


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
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _relative_to(path: Path, parent: Path) -> str:
    try:
        return str(path.relative_to(parent))
    except ValueError:
        return str(path)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run the minimal useful pipeline rail over the unified 82-event cohort.")
    ap.add_argument("--run-id", required=True, help="Top-level run id under runs/<run_id>/experiment/unified82_pipeline_run")
    ap.add_argument("--runs-root", type=Path, default=RUNS_ROOT_DEFAULT)
    ap.add_argument("--input-dir", type=Path, default=INPUT_DIR_DEFAULT)
    ap.add_argument("--python-bin", type=Path, default=Path(sys.executable))
    ap.add_argument("--x-min", type=float, default=4.0)
    ap.add_argument("--g2-min", type=float, default=1e-6)
    return ap


def main() -> int:
    args = build_parser().parse_args()
    runs_root = Path(args.runs_root).resolve(strict=False)
    input_dir = Path(args.input_dir).resolve(strict=False)
    python_bin = Path(args.python_bin).resolve(strict=False)

    final_stage_dir = runs_root / args.run_id / "experiment" / "unified82_pipeline_run"
    tmp_stage_dir = runs_root / args.run_id / "experiment" / f".tmp_unified82_pipeline_run_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}"
    rail_run_id = f"{args.run_id}/experiment/{tmp_stage_dir.name}/rails/fullcohort82_probe"
    rail_stage_dir = runs_root / rail_run_id / "experiment" / "fullcohort_90_physics_probe"

    required_inputs = [
        input_dir,
        input_dir / "cohort_summary.json",
        input_dir / "geometries_manifest.json",
        FULLCOHORT_WRAPPER,
        CANONICAL33_INPUT_DIR,
        OOD55_INPUT_DIR,
        CANONICAL33_SUMMARY,
        GEOMETRY33_SUMMARY,
        GEOMETRY55_SUMMARY,
        GATE90_SUMMARY,
        PREMIUM33_PER_EVENT,
        PREMIUM33_AGGREGATE,
    ]
    missing = [str(path) for path in required_inputs if not path.exists()]
    if missing:
        raise SystemExit(f"FATAL: missing required contractual input: {missing[0]}")
    if final_stage_dir.exists():
        raise SystemExit(f"FATAL: final output dir already exists: {final_stage_dir}")
    if tmp_stage_dir.exists():
        raise SystemExit(f"FATAL: temporary output dir already exists: {tmp_stage_dir}")

    h5_files = sorted(input_dir.glob("*.h5"))
    if len(h5_files) != 82:
        raise SystemExit(f"FATAL: input cohort must contain exactly 82 H5 files (found {len(h5_files)})")
    for required_name in sorted(REQUIRED_INCLUDED):
        if not (input_dir / required_name).exists():
            raise SystemExit(f"FATAL: required rescued input missing from cohort: {required_name}")

    tmp_stage_dir.mkdir(parents=True, exist_ok=False)
    wrapper_stdout = tmp_stage_dir / "logs" / "wrapper_stdout.log"
    wrapper_stderr = tmp_stage_dir / "logs" / "wrapper_stderr.log"
    wrapper_stdout.parent.mkdir(parents=True, exist_ok=True)

    command = [
        str(python_bin),
        str(FULLCOHORT_WRAPPER),
        "--run-id",
        rail_run_id,
        "--runs-root",
        str(runs_root),
        "--input-dir",
        str(input_dir),
        "--x-min",
        str(args.x_min),
        "--g2-min",
        str(args.g2_min),
    ]

    try:
        proc = subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        wrapper_stdout.write_text(proc.stdout, encoding="utf-8")
        wrapper_stderr.write_text(proc.stderr, encoding="utf-8")
        if proc.returncode != 0:
            raise RuntimeError(
                f"wrapped pipeline failed with exit code {proc.returncode}; see {wrapper_stderr}"
            )

        rail_stage_summary_path = rail_stage_dir / "stage_summary.json"
        rail_manifest_path = rail_stage_dir / "manifest.json"
        rail_outputs_dir = rail_stage_dir / "outputs"
        required_outputs = [
            rail_stage_summary_path,
            rail_manifest_path,
            rail_outputs_dir / "aggregate_probe_summary.json",
            rail_outputs_dir / "per_event_physics_probe.json",
            rail_outputs_dir / "cohort_partition.json",
            rail_stage_dir / "stdout.log",
            rail_stage_dir / "stderr.log",
        ]
        missing_outputs = [str(path) for path in required_outputs if not path.exists()]
        if missing_outputs:
            raise RuntimeError(f"wrapped pipeline did not produce required output: {missing_outputs[0]}")

        rail_stage_summary = _load_json(rail_stage_summary_path)
        if rail_stage_summary.get("status") != "PASS":
            raise RuntimeError(
                "wrapped pipeline did not finish in PASS "
                f"(status={rail_stage_summary.get('status')})"
            )

        root_outputs_dir = tmp_stage_dir / "outputs"
        root_outputs_dir.mkdir(parents=True, exist_ok=False)
        for src_name in (
            "aggregate_probe_summary.json",
            "per_event_physics_probe.json",
            "cohort_partition.json",
        ):
            src = rail_outputs_dir / src_name
            dst = root_outputs_dir / src_name
            shutil.copy2(src, dst)

        stage_summary = {
            "created_at": _utc_now_iso(),
            "stage": "experiment/unified82_pipeline_run",
            "status": "PASS",
            "pipeline_kind": "minimal_useful_rail",
            "wrapped_stage": "experiment/fullcohort_90_physics_probe",
            "wrapped_stage_status": rail_stage_summary.get("status"),
            "run_id": args.run_id,
            "n_input_h5": len(h5_files),
            "input_dir": str(input_dir),
            "outputs_dir": str(final_stage_dir / "outputs"),
            "rails_root": str(final_stage_dir / "rails"),
            "warnings": [
                "This wrapper reuses the existing fullcohort physics probe over the materialized 82-event cohort",
                "No canonical stages were modified",
            ],
            "wrapped_stage_summary": {
                "n_events_total": rail_stage_summary.get("n_events_total"),
                "n_usable_for_mainline": rail_stage_summary.get("n_usable_for_mainline"),
                "n_ood_but_informative": rail_stage_summary.get("n_ood_but_informative"),
                "n_low_signal_or_uninformative": rail_stage_summary.get("n_low_signal_or_uninformative"),
                "premium_advantage_scope": rail_stage_summary.get("premium_advantage_scope"),
            },
        }

        manifest = {
            "created_at": _utc_now_iso(),
            "stage": "experiment/unified82_pipeline_run",
            "script": str(Path(__file__).resolve()),
            "command": command,
            "parameters": {
                "run_id": args.run_id,
                "x_min": args.x_min,
                "g2_min": args.g2_min,
                "python_bin": str(python_bin),
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
                "geometries_manifest_json": {
                    "path": str(input_dir / "geometries_manifest.json"),
                    "sha256": _sha256_file(input_dir / "geometries_manifest.json"),
                },
            },
            "outputs": {
                "manifest_json": "manifest.json",
                "stage_summary_json": "stage_summary.json",
                "outputs_dir": "outputs",
                "logs_dir": "logs",
                "rail_stage_dir": _relative_to(rail_stage_dir, tmp_stage_dir),
                "rail_manifest_json": _relative_to(rail_manifest_path, tmp_stage_dir),
                "rail_stage_summary_json": _relative_to(rail_stage_summary_path, tmp_stage_dir),
            },
        }

        _write_json_atomic(tmp_stage_dir / "stage_summary.json", stage_summary)
        _write_json_atomic(tmp_stage_dir / "manifest.json", manifest)
        os.replace(tmp_stage_dir, final_stage_dir)
    except Exception as exc:
        if tmp_stage_dir.exists():
            shutil.rmtree(tmp_stage_dir)
        raise SystemExit(f"FATAL: {exc}")

    print(f"[OK] pipeline run published at {final_stage_dir}")
    print(f"[OK] wrapped rail stage: {final_stage_dir / 'rails' / 'fullcohort82_probe' / 'experiment' / 'fullcohort_90_physics_probe'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
