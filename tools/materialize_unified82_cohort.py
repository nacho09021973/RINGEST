#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNS_ROOT_DEFAULT = REPO_ROOT / "runs"
SOURCE_INPUT_DEFAULT = REPO_ROOT / "runs" / "reopen_v1" / "90_event_xmax6_stage02_input"
RESCUE_UPDATE_DEFAULT = (
    REPO_ROOT
    / "runs"
    / "low_signal_rescue_audit_10_20260413"
    / "experiment"
    / "low_signal_rescue_audit_10"
    / "outputs"
    / "recommended_cohort_update.json"
)
OUTPUT_DIR_DEFAULT = REPO_ROOT / "runs" / "reopen_v1" / "82_event_unified_stage02_input"
REQUIRED_INCLUDED = {
    "GW170817__ringdown.h5",
    "GW190517_055101__ringdown.h5",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _symlink_or_copy(src: Path, dst: Path, mode: str) -> str:
    if mode == "copy2":
        shutil.copy2(src, dst)
        return "copy2"
    dst.symlink_to(src.resolve())
    return "symlink"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Materialize the recommended unified 82-event stage02 cohort.")
    ap.add_argument("--source-input-dir", type=Path, default=SOURCE_INPUT_DEFAULT)
    ap.add_argument("--recommended-cohort-update", type=Path, default=RESCUE_UPDATE_DEFAULT)
    ap.add_argument("--output-dir", type=Path, default=OUTPUT_DIR_DEFAULT)
    ap.add_argument(
        "--link-mode",
        choices=("symlink", "copy2"),
        default="symlink",
        help="How to materialize H5 files. Default keeps the smallest auditable footprint.",
    )
    return ap


def main() -> int:
    args = build_parser().parse_args()
    source_input_dir = Path(args.source_input_dir).resolve(strict=False)
    recommended_update = Path(args.recommended_cohort_update).resolve(strict=False)
    output_dir = Path(args.output_dir).resolve(strict=False)

    if not source_input_dir.exists():
        raise SystemExit(f"FATAL: source input dir not found: {source_input_dir}")
    if not recommended_update.exists():
        raise SystemExit(f"FATAL: recommended cohort update not found: {recommended_update}")
    if output_dir.exists():
        raise SystemExit(f"FATAL: output dir already exists: {output_dir}")
    if RUNS_ROOT_DEFAULT.resolve() not in output_dir.parents:
        raise SystemExit(f"FATAL: output dir must stay under runs/: {output_dir}")

    source_manifest_path = source_input_dir / "geometries_manifest.json"
    if not source_manifest_path.exists():
        raise SystemExit(f"FATAL: missing source geometries manifest: {source_manifest_path}")

    update_payload = _load_json(recommended_update)
    source_manifest = _load_json(source_manifest_path)

    recommended_events = update_payload.get("recommended_events", [])
    if len(recommended_events) != 82:
        raise SystemExit(
            "FATAL: recommended_cohort_update.json does not contain exactly 82 recommended events "
            f"(found {len(recommended_events)})"
        )

    recommended_files = sorted(f"{event_name}.h5" for event_name in recommended_events)
    missing_source = [name for name in recommended_files if not (source_input_dir / name).exists()]
    if missing_source:
        raise SystemExit(f"FATAL: recommended source H5 missing: {missing_source[0]}")

    missing_required = sorted(name for name in REQUIRED_INCLUDED if name not in recommended_files)
    if missing_required:
        raise SystemExit(f"FATAL: required rescued events missing from recommended list: {missing_required}")

    geometries_by_name = {item["name"]: item for item in source_manifest.get("geometries", [])}
    filtered_geometries = []
    for event_name in recommended_events:
        geometry = geometries_by_name.get(event_name)
        if geometry is None:
            raise SystemExit(f"FATAL: source geometries_manifest.json missing event: {event_name}")
        filtered_geometries.append(geometry)

    output_dir.mkdir(parents=True, exist_ok=False)
    materialized_entries: list[dict[str, Any]] = []
    total_bytes = 0
    for file_name in recommended_files:
        src = source_input_dir / file_name
        dst = output_dir / file_name
        materialization = _symlink_or_copy(src, dst, args.link_mode)
        total_bytes += src.stat().st_size
        materialized_entries.append(
            {
                "file": file_name,
                "event_name": file_name.removesuffix(".h5"),
                "source_path": str(src),
                "materialized_path": str(dst),
                "materialization": materialization,
                "source_sha256": _sha256_file(src),
                "size_bytes": src.stat().st_size,
            }
        )

    h5_count = len(list(output_dir.glob("*.h5")))
    if h5_count != 82:
        raise SystemExit(f"FATAL: materialized cohort has {h5_count} H5 files, expected 82")
    for required_name in sorted(REQUIRED_INCLUDED):
        if not (output_dir / required_name).exists():
            raise SystemExit(f"FATAL: required H5 missing after materialization: {required_name}")

    filtered_manifest = dict(source_manifest)
    filtered_manifest["version"] = "82-event-unified-stage02-input-v1"
    filtered_manifest["n_systems"] = 82
    filtered_manifest["source_stage02_dir"] = str(source_input_dir)
    filtered_manifest["recommended_cohort_update_json"] = str(recommended_update)
    filtered_manifest["geometries"] = filtered_geometries

    cohort_manifest = {
        "created_at": _utc_now_iso(),
        "script": str(Path(__file__).resolve()),
        "command": [
            str(Path(__file__).resolve()),
            "--source-input-dir",
            str(source_input_dir),
            "--recommended-cohort-update",
            str(recommended_update),
            "--output-dir",
            str(output_dir),
            "--link-mode",
            args.link_mode,
        ],
        "source_input_dir": str(source_input_dir),
        "recommended_cohort_update_json": str(recommended_update),
        "recommended_update_sha256": _sha256_file(recommended_update),
        "source_geometries_manifest_sha256": _sha256_file(source_manifest_path),
        "n_h5": h5_count,
        "link_mode": args.link_mode,
        "entries": materialized_entries,
    }

    cohort_summary = {
        "created_at": _utc_now_iso(),
        "status": "PASS",
        "cohort_name": "unified82_stage02_input",
        "n_h5": h5_count,
        "recommended_decision": update_payload.get("updated_decision"),
        "recommended_count": update_payload.get("updated_recommended_count"),
        "rescued_event_ids": [item["event_name"].replace("__ringdown", "") for item in update_payload.get("rescued_events", [])],
        "required_included": sorted(REQUIRED_INCLUDED),
        "materialization_mode": args.link_mode,
        "source_input_dir": str(source_input_dir),
        "output_dir": str(output_dir),
        "total_source_bytes": total_bytes,
    }

    _write_json_atomic(output_dir / "geometries_manifest.json", filtered_manifest)
    _write_json_atomic(output_dir / "cohort_manifest.json", cohort_manifest)
    _write_json_atomic(output_dir / "cohort_summary.json", cohort_summary)

    print(f"[OK] materialized {h5_count} H5 files into {output_dir}")
    print(f"[OK] wrote {output_dir / 'cohort_manifest.json'}")
    print(f"[OK] wrote {output_dir / 'cohort_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
