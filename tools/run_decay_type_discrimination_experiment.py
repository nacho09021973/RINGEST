#!/usr/bin/env python3
"""
Minimal BASURIN wrapper for tools/decay_type_discrimination.py.
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


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT_DEFAULT = REPO_ROOT / "runs"
INPUT_DIR_DEFAULT = REPO_ROOT / "runs" / "reopen_v1" / "33_event_effective_contract_pass_stage02_input"
COHORT_SUMMARY_DEFAULT = REPO_ROOT / "runs" / "reopen_v1" / "33_event_effective_contract_pass_summary.json"
GEOMETRY_CONTRACTS_SUMMARY_DEFAULT = REPO_ROOT / "runs" / "reopen_v1" / "04_geometry_physics_contracts_33_event_effective_contract_pass_xmax6_v1" / "geometry_contracts_summary.json"
ENTRYPOINT = REPO_ROOT / "tools" / "decay_type_discrimination.py"
STAGE_NAME = "experiment/decay_type_discrimination"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _fingerprint_h5_inputs(input_dir: Path) -> tuple[str, list[str]]:
    h5_files = sorted(input_dir.glob("*.h5"))
    rel_paths = [p.name for p in h5_files]
    payload = "\n".join(rel_paths).encode("utf-8")
    return _sha256_bytes(payload), rel_paths


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Run decay_type_discrimination.py under BASURIN experiment layout.")
    ap.add_argument("--run-id", required=True, help="Run identifier under runs/<run_id>/experiment/decay_type_discrimination/")
    ap.add_argument("--parent-run-id", required=True, help="Parent run id that must contain RUN_VALID/verdict.json with verdict=PASS")
    ap.add_argument("--runs-root", type=Path, default=RUNS_ROOT_DEFAULT)
    ap.add_argument("--input-dir", type=Path, default=INPUT_DIR_DEFAULT)
    ap.add_argument("--cohort-summary-json", type=Path, default=COHORT_SUMMARY_DEFAULT)
    ap.add_argument("--geometry-contracts-summary-json", type=Path, default=GEOMETRY_CONTRACTS_SUMMARY_DEFAULT)
    ap.add_argument("--x-min", type=float, default=2.0)
    ap.add_argument("--suffix", type=str, default="")
    ap.add_argument("--g2-min", type=float, default=1e-6)
    ap.add_argument("--bic-threshold", type=float, default=2.0)
    ap.add_argument("--r2-min", type=float, default=0.3)
    return ap


def main() -> int:
    args = build_parser().parse_args()

    input_dir = Path(args.input_dir).resolve(strict=False)
    cohort_summary_json = Path(args.cohort_summary_json).resolve(strict=False)
    geometry_contracts_summary_json = Path(args.geometry_contracts_summary_json).resolve(strict=False)
    runs_root = Path(args.runs_root).resolve(strict=False)
    parent_run_root = runs_root / args.parent_run_id
    run_valid_verdict_json = parent_run_root / "RUN_VALID" / "verdict.json"
    stage_dir = runs_root / args.run_id / "experiment" / "decay_type_discrimination"
    outputs_dir = stage_dir / "outputs"
    tmp_outputs_dir = stage_dir / ".tmp_outputs"
    stdout_log = stage_dir / "stdout.log"
    stderr_log = stage_dir / "stderr.log"

    if not ENTRYPOINT.exists():
        print(f"ERROR: entrypoint not found: {ENTRYPOINT}", file=sys.stderr)
        return 2
    if not input_dir.exists():
        print(f"ERROR: input directory not found: {input_dir}", file=sys.stderr)
        return 2
    if not input_dir.is_dir():
        print(f"ERROR: input path is not a directory: {input_dir}", file=sys.stderr)
        return 2
    if not run_valid_verdict_json.exists():
        print(f"ERROR: parent RUN_VALID verdict not found: {run_valid_verdict_json}", file=sys.stderr)
        return 2
    try:
        run_valid_payload = json.loads(run_valid_verdict_json.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid RUN_VALID verdict JSON at {run_valid_verdict_json}: {exc}", file=sys.stderr)
        return 2
    if run_valid_payload.get("verdict") != "PASS":
        print(f"ERROR: parent RUN_VALID verdict is not PASS at {run_valid_verdict_json}", file=sys.stderr)
        return 2
    if not cohort_summary_json.exists():
        print(f"ERROR: cohort_summary_json not found: {cohort_summary_json}", file=sys.stderr)
        return 2
    if not geometry_contracts_summary_json.exists():
        print(f"ERROR: geometry_contracts_summary_json not found: {geometry_contracts_summary_json}", file=sys.stderr)
        return 2

    input_fingerprint, input_h5_files = _fingerprint_h5_inputs(input_dir)
    if not input_h5_files:
        print(f"ERROR: No H5 files found in input directory: {input_dir}", file=sys.stderr)
        return 2

    stage_dir.mkdir(parents=True, exist_ok=True)
    if outputs_dir.exists():
        print(f"ERROR: output directory already exists: {outputs_dir}", file=sys.stderr)
        return 2
    if tmp_outputs_dir.exists():
        shutil.rmtree(tmp_outputs_dir)

    suffix = args.suffix
    file_suffix = f"_{suffix}" if suffix else ""
    output_csv = outputs_dir / f"decay_type_discrimination_33_event_canonical{file_suffix}.csv"
    output_json = outputs_dir / f"decay_type_discrimination_33_event_canonical{file_suffix}.json"

    command = [
        sys.executable,
        str(ENTRYPOINT),
        "--input-dir",
        str(input_dir),
        "--output-dir",
        str(tmp_outputs_dir),
        "--x-min",
        str(args.x_min),
        "--g2-min",
        str(args.g2_min),
        "--bic-threshold",
        str(args.bic_threshold),
        "--r2-min",
        str(args.r2_min),
    ]
    if suffix:
        command.extend(["--suffix", suffix])

    proc = subprocess.run(
        command,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    stdout_log.write_text(proc.stdout, encoding="utf-8")
    stderr_log.write_text(proc.stderr, encoding="utf-8")

    if proc.returncode != 0:
        shutil.rmtree(tmp_outputs_dir, ignore_errors=True)
        stage_summary = {
            "created_at": _utc_now_iso(),
            "status": "ERROR",
            "exit_code": proc.returncode,
            "stage": STAGE_NAME,
            "script": str(Path(__file__).resolve()),
            "run_id": args.run_id,
            "input_root": str(input_dir),
            "output_dir": str(stage_dir),
            "error_message": (proc.stderr or proc.stdout).strip() or "experiment failed",
        }
        manifest = {
            "created_at": _utc_now_iso(),
            "stage": STAGE_NAME,
            "script": str(Path(__file__).resolve()),
            "entrypoint": str(ENTRYPOINT),
            "timestamp": _utc_now_iso(),
            "parameters": {
                "run_id": args.run_id,
                "parent_run_id": args.parent_run_id,
                "x_min": args.x_min,
                "suffix": args.suffix,
                "g2_min": args.g2_min,
                "bic_threshold": args.bic_threshold,
                "r2_min": args.r2_min,
            },
            "inputs": {
                "parent_run_valid_verdict_json": {
                    "path": str(run_valid_verdict_json),
                    "sha256": _sha256_file(run_valid_verdict_json),
                },
                "input_dir": {
                    "path": str(input_dir),
                    "input_h5_count": len(input_h5_files),
                    "input_h5_listing_sha256": input_fingerprint,
                    "input_h5_files": input_h5_files,
                },
                "cohort_summary_json": {
                    "path": str(cohort_summary_json),
                    "sha256": _sha256_file(cohort_summary_json),
                },
                "geometry_contracts_summary_json": {
                    "path": str(geometry_contracts_summary_json),
                    "sha256": _sha256_file(geometry_contracts_summary_json),
                },
            },
            "outputs": {
                "stdout_log": str(stdout_log),
                "stderr_log": str(stderr_log),
                "stage_summary": str(stage_dir / "stage_summary.json"),
            },
            "status": "ERROR",
        }
        _write_json_atomic(stage_dir / "stage_summary.json", stage_summary)
        _write_json_atomic(stage_dir / "manifest.json", manifest)
        print(stage_summary["error_message"], file=sys.stderr)
        return proc.returncode

    if not tmp_outputs_dir.exists():
        print("ERROR: experiment succeeded but temporary outputs directory is missing", file=sys.stderr)
        return 2
    if not (tmp_outputs_dir / output_csv.name).exists() or not (tmp_outputs_dir / output_json.name).exists():
        print("ERROR: experiment succeeded but expected CSV/JSON outputs are missing", file=sys.stderr)
        shutil.rmtree(tmp_outputs_dir, ignore_errors=True)
        return 2

    tmp_outputs_dir.rename(outputs_dir)

    summary_payload = json.loads(output_json.read_text(encoding="utf-8"))
    stage_summary = {
        "created_at": _utc_now_iso(),
        "status": "OK",
        "exit_code": 0,
        "stage": STAGE_NAME,
        "script": str(Path(__file__).resolve()),
        "run_id": args.run_id,
        "parent_run_validated": True,
        "n_events": summary_payload["n_events"],
        "n_exponential_preferred": summary_payload["n_exponential_preferred"],
        "n_powerlaw_preferred": summary_payload["n_powerlaw_preferred"],
        "n_ambiguous": summary_payload["n_ambiguous"],
        "n_neither_good": summary_payload["n_neither_good"],
        "powerlaw_majority_observed": summary_payload["powerlaw_majority_observed"],
        "exponential_tilt_observed": summary_payload["exponential_tilt_observed"],
        "dominant_decay_type": summary_payload["dominant_decay_type"],
        "output_csv": str(output_csv),
        "output_json": str(output_json),
    }
    manifest = {
        "created_at": _utc_now_iso(),
        "stage": STAGE_NAME,
        "script": str(Path(__file__).resolve()),
        "entrypoint": str(ENTRYPOINT),
        "timestamp": _utc_now_iso(),
        "parameters": {
            "run_id": args.run_id,
            "parent_run_id": args.parent_run_id,
            "x_min": args.x_min,
            "suffix": args.suffix,
            "g2_min": args.g2_min,
            "bic_threshold": args.bic_threshold,
            "r2_min": args.r2_min,
        },
        "inputs": {
            "parent_run_valid_verdict_json": {
                "path": str(run_valid_verdict_json),
                "sha256": _sha256_file(run_valid_verdict_json),
            },
            "input_dir": {
                "path": str(input_dir),
                "input_h5_count": len(input_h5_files),
                "input_h5_listing_sha256": input_fingerprint,
                "input_h5_files": input_h5_files,
            },
            "cohort_summary_json": {
                "path": str(cohort_summary_json),
                "sha256": _sha256_file(cohort_summary_json),
            },
            "geometry_contracts_summary_json": {
                "path": str(geometry_contracts_summary_json),
                "sha256": _sha256_file(geometry_contracts_summary_json),
            },
        },
        "outputs": {
            "output_dir": str(outputs_dir),
            "per_event_csv": {
                "path": str(output_csv),
                "sha256": _sha256_file(output_csv),
            },
            "summary_json": {
                "path": str(output_json),
                "sha256": _sha256_file(output_json),
            },
            "stdout_log": {
                "path": str(stdout_log),
                "sha256": _sha256_file(stdout_log),
            },
            "stderr_log": {
                "path": str(stderr_log),
                "sha256": _sha256_file(stderr_log),
            },
            "stage_summary": str(stage_dir / "stage_summary.json"),
            "manifest": str(stage_dir / "manifest.json"),
        },
        "status": "OK",
    }

    _write_json_atomic(stage_dir / "stage_summary.json", stage_summary)
    _write_json_atomic(stage_dir / "manifest.json", manifest)

    print(f"[OK] stage_dir: {stage_dir}")
    print(f"[OK] outputs: {outputs_dir}")
    print(f"[OK] stage_summary: {stage_dir / 'stage_summary.json'}")
    print(f"[OK] manifest: {stage_dir / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
