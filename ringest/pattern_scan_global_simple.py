from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ringest.feature_inventory import REPO_ROOT, _ensure_within

STAGE_NAME = "exp002_pattern_scan_global_simple"
UPSTREAM_STAGE_NAME = "exp001_feature_inventory"
SCHEMA_VERSION = "exp002-pattern-scan-0.1"
PRIMARY_VERDICT_PASS = "PATTERN_SCAN_READY"
PRIMARY_VERDICT_FAIL = "PATTERN_SCAN_FAILED"
INPUT_ROOT_DEFAULT = "data/raw/ringhier_snapshot"
MAX_CANDIDATE_FEATURES = 6
ROW_ID_FIELD_PREFERENCE = ["event_id", "pipeline_event_id", "row_id", "entity_id", "id"]
IDENTIFIER_FIELD_NAMES = {
    "candidate_id",
    "entity_id",
    "event_id",
    "id",
    "pipeline_event_id",
    "row_id",
    "run_id",
}


class ExecutiveContractError(RuntimeError):
    """Raised when preflight or deterministic execution contracts fail."""


@dataclass(frozen=True)
class PatternScanPaths:
    repo_root: Path
    input_root: Path
    run_root: Path
    experiment_root: Path
    outputs_root: Path
    exp001_root: Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=STAGE_NAME)
    parser.add_argument("--run-id", required=True, help="Run identifier under runs/.")
    parser.add_argument("--exp001-run", required=True, help="Upstream exp001 run identifier.")
    return parser.parse_args(argv)


def run_pattern_scan_global_simple(
    *,
    run_id: str,
    exp001_run: str,
    repo_root: Path | None = None,
) -> PatternScanPaths:
    repo_root = (repo_root or REPO_ROOT).resolve()
    paths = _build_paths(repo_root=repo_root, run_id=run_id, exp001_run=exp001_run)
    _validate_preflight(paths=paths, run_id=run_id)

    try:
        result = _derive_pattern_scan(paths=paths, exp001_run=exp001_run)
    except ExecutiveContractError as exc:
        _emit_fail_run(paths=paths, exp001_run=exp001_run, error_message=str(exc))
        raise

    created_run_root = False
    try:
        paths.outputs_root.mkdir(parents=True, exist_ok=False)
        created_run_root = True
        _write_json(paths.outputs_root / "pattern_scan_summary.json", result["pattern_scan_summary"], root=paths.run_root)
        _write_json(paths.experiment_root / "stage_summary.json", result["stage_summary"], root=paths.run_root)
        _write_json(paths.experiment_root / "manifest.json", _build_manifest(paths=paths, result=result), root=paths.run_root)
    except Exception as exc:  # pragma: no cover
        if created_run_root and paths.run_root.exists():
            shutil.rmtree(paths.run_root)
        raise ExecutiveContractError(f"failed to emit required artifacts: {exc}") from exc

    return paths


def _build_paths(*, repo_root: Path, run_id: str, exp001_run: str) -> PatternScanPaths:
    input_root = (repo_root / INPUT_ROOT_DEFAULT).resolve()
    run_root = (repo_root / "runs" / run_id).resolve()
    experiment_root = (run_root / "experiment" / STAGE_NAME).resolve()
    outputs_root = (experiment_root / "outputs").resolve()
    exp001_root = (repo_root / "runs" / exp001_run / "experiment" / UPSTREAM_STAGE_NAME).resolve()
    _ensure_within(run_root, repo_root / "runs")
    _ensure_within(experiment_root, run_root)
    _ensure_within(outputs_root, run_root)
    _ensure_within(exp001_root, repo_root / "runs")
    return PatternScanPaths(
        repo_root=repo_root,
        input_root=input_root,
        run_root=run_root,
        experiment_root=experiment_root,
        outputs_root=outputs_root,
        exp001_root=exp001_root,
    )


def _validate_preflight(*, paths: PatternScanPaths, run_id: str) -> None:
    if not run_id or Path(run_id).name != run_id or run_id in {".", ".."}:
        raise ExecutiveContractError(f"invalid run_id: {run_id!r}")
    if paths.run_root.exists():
        raise ExecutiveContractError(f"run_id already exists: {paths.run_root}")
    if not paths.input_root.exists() or not paths.input_root.is_dir():
        raise ExecutiveContractError(f"input_root does not exist: {paths.input_root}")
    if not paths.exp001_root.exists() or not paths.exp001_root.is_dir():
        raise ExecutiveContractError(f"missing exp001 root: {paths.exp001_root}")

    stage_summary_path = paths.exp001_root / "stage_summary.json"
    field_inventory_path = paths.exp001_root / "outputs" / "field_inventory.json"
    schema_profile_path = paths.exp001_root / "outputs" / "schema_profile.json"

    if not stage_summary_path.exists():
        raise ExecutiveContractError(f"missing exp001 stage_summary.json: {stage_summary_path}")
    if not field_inventory_path.exists():
        raise ExecutiveContractError(f"missing exp001 field_inventory.json: {field_inventory_path}")
    if not schema_profile_path.exists():
        raise ExecutiveContractError(f"missing exp001 schema_profile.json: {schema_profile_path}")

    stage_summary = _read_json(stage_summary_path)
    if stage_summary.get("status") != "PASS":
        raise ExecutiveContractError(f"exp001 stage_summary status is not PASS: {stage_summary.get('status')}")


def _derive_pattern_scan(*, paths: PatternScanPaths, exp001_run: str) -> dict[str, Any]:
    field_inventory = _read_json(paths.exp001_root / "outputs" / "field_inventory.json")
    if not isinstance(field_inventory, list):
        raise ExecutiveContractError("exp001 field_inventory.json is not a JSON list")

    candidates_by_source: dict[str, dict[str, Any]] = {}
    for row in sorted(field_inventory, key=lambda item: (item.get("source_relpath", ""), item.get("field_name", ""))):
        if not isinstance(row, dict):
            continue

        source_relpath = row.get("source_relpath")
        field_name = row.get("field_name")
        if not isinstance(source_relpath, str) or not source_relpath:
            continue
        if not isinstance(field_name, str) or not field_name:
            continue

        source_path = (paths.input_root / source_relpath).resolve()
        _ensure_within(source_path, paths.input_root)
        if not source_path.exists() or not source_path.is_file():
            continue

        bucket = candidates_by_source.setdefault(
            source_relpath,
            {
                "source_path": source_path,
                "feature_rows": [],
                "row_id_candidates": [],
            },
        )
        if _is_candidate_feature_row(row):
            bucket["feature_rows"].append(dict(row))
        if _is_row_id_candidate_row(row):
            bucket["row_id_candidates"].append(field_name)

    eligible_sources: list[dict[str, Any]] = []
    for source_relpath, bucket in sorted(candidates_by_source.items()):
        feature_rows = _select_candidate_feature_rows(bucket["feature_rows"])
        if len(feature_rows) < 2:
            continue

        records = _extract_records(bucket["source_path"])
        if len(records) < 2:
            continue

        selected_feature_names = [row["field_name"] for row in feature_rows]
        complete_rows = sum(
            1
            for record in records
            if all(record.get(field_name) is not None for field_name in selected_feature_names)
        )
        if complete_rows < 2:
            continue

        row_id_candidates = _ordered_row_id_candidates(bucket["row_id_candidates"])
        recommended_row_id_field = _resolve_recommended_row_id_field(records=records, candidates=row_id_candidates)
        eligible_sources.append(
            {
                "source_relpath": source_relpath,
                "source_path": bucket["source_path"],
                "candidate_feature_fields": selected_feature_names,
                "row_id_field_candidates": row_id_candidates,
                "recommended_row_id_field": recommended_row_id_field,
                "n_rows": len(records),
                "n_complete_rows": complete_rows,
            }
        )

    if not eligible_sources:
        raise ExecutiveContractError("no auditable source with >=2 usable non-identifier features and >=2 complete rows")

    best = sorted(
        eligible_sources,
        key=lambda item: (
            -item["n_complete_rows"],
            -len(item["candidate_feature_fields"]),
            -(1 if item["recommended_row_id_field"] else 0),
            -len(item["row_id_field_candidates"]),
            item["source_relpath"],
        ),
    )[0]

    pattern_scan_summary = {
        "schema_version": SCHEMA_VERSION,
        "recommended_source_relpath": best["source_relpath"],
        "candidate_feature_fields": best["candidate_feature_fields"],
        "recommended_row_id_field": best["recommended_row_id_field"],
        "row_id_field_candidates": best["row_id_field_candidates"],
    }
    _validate_pattern_scan_summary(pattern_scan_summary)

    stage_summary = {
        "stage": STAGE_NAME,
        "status": "PASS",
        "upstream_exp001_run": exp001_run,
        "schema_version": SCHEMA_VERSION,
        "n_candidate_features": len(best["candidate_feature_fields"]),
        "recommended_source_relpath": best["source_relpath"],
        "primary_verdict": PRIMARY_VERDICT_PASS,
    }
    return {
        "pattern_scan_summary": pattern_scan_summary,
        "stage_summary": stage_summary,
    }


def _is_candidate_feature_row(row: dict[str, Any]) -> bool:
    field_name = str(row.get("field_name", ""))
    normalized_name = field_name.lower()
    if normalized_name in IDENTIFIER_FIELD_NAMES or normalized_name.endswith("_id"):
        return False
    if row.get("usability_class") != "usable":
        return False
    if row.get("all_null") or row.get("constant"):
        return False
    if row.get("coverage_fraction", 0.0) < 0.95:
        return False
    if row.get("candidate_role") not in {"numeric_feature", "categorical_feature"}:
        return False
    if row.get("dtype_observed") not in {"integer", "number"}:
        return False
    return True


def _is_row_id_candidate_row(row: dict[str, Any]) -> bool:
    if row.get("candidate_role") != "identifier":
        return False
    if row.get("coverage_fraction", 0.0) < 0.95:
        return False
    if row.get("all_null") or row.get("constant"):
        return False
    field_name = str(row.get("field_name", ""))
    normalized_name = field_name.lower()
    return normalized_name in IDENTIFIER_FIELD_NAMES or normalized_name.endswith("_id")


def _select_candidate_feature_rows(feature_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[str, dict[str, Any]] = {}
    for row in feature_rows:
        deduped[row["field_name"]] = row

    base_names = set(deduped)
    selected = [
        row
        for row in deduped.values()
        if not _is_redundant_interval_variant(field_name=row["field_name"], known_fields=base_names)
    ]
    selected.sort(
        key=lambda row: (
            row.get("candidate_role") != "numeric_feature",
            _feature_priority(row["field_name"]),
            row["field_name"],
        )
    )
    return selected[:MAX_CANDIDATE_FEATURES]


def _is_redundant_interval_variant(*, field_name: str, known_fields: set[str]) -> bool:
    suffix_map = {
        "_ci_low": "",
        "_ci_high": "",
        "_lower": "",
        "_upper": "",
    }
    for suffix, replacement in suffix_map.items():
        if field_name.endswith(suffix):
            base_name = field_name[: -len(suffix)] + replacement
            return base_name in known_fields
    return False


def _feature_priority(field_name: str) -> tuple[int, int, str]:
    normalized = field_name.lower()
    proxy_penalty = 1 if "proxy" in normalized else 0
    uncertainty_penalty = 1 if "uncertainty" in normalized else 0
    return (proxy_penalty, uncertainty_penalty, normalized)


def _ordered_row_id_candidates(candidates: list[str]) -> list[str]:
    stable = sorted(set(candidates))
    preferred_present = [name for name in ROW_ID_FIELD_PREFERENCE if name in stable]
    remaining = [name for name in stable if name not in preferred_present]
    return preferred_present + remaining


def _resolve_recommended_row_id_field(*, records: list[dict[str, Any]], candidates: list[str]) -> str:
    for candidate in candidates:
        values = [record.get(candidate) for record in records]
        if any(value is None for value in values):
            continue
        if len({_canonical_value(value) for value in values}) != len(records):
            continue
        return candidate
    return ""


def _extract_records(path: Path) -> list[dict[str, Any]]:
    payload = _read_json(path)
    if isinstance(payload, list) and all(isinstance(row, dict) for row in payload):
        return [dict(row) for row in payload]
    if isinstance(payload, dict):
        rows = payload.get("rows")
        if isinstance(rows, list) and all(isinstance(row, dict) for row in rows):
            return [dict(row) for row in rows]
        if payload and all(isinstance(value, dict) for value in payload.values()):
            return [dict(payload[key]) for key in sorted(payload)]
        return [dict(payload)]
    raise ExecutiveContractError(f"recommended source is not a supported structured JSON table: {path}")


def _validate_pattern_scan_summary(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise ExecutiveContractError("pattern_scan_summary schema_version mismatch")
    if not isinstance(payload.get("recommended_source_relpath"), str) or not payload["recommended_source_relpath"]:
        raise ExecutiveContractError("pattern_scan_summary recommended_source_relpath must be a non-empty string")
    fields = payload.get("candidate_feature_fields")
    if not isinstance(fields, list) or not fields or not all(isinstance(item, str) and item for item in fields):
        raise ExecutiveContractError("pattern_scan_summary candidate_feature_fields must be a non-empty string list")
    row_id_candidates = payload.get("row_id_field_candidates")
    if not isinstance(row_id_candidates, list) or not all(isinstance(item, str) and item for item in row_id_candidates):
        raise ExecutiveContractError("pattern_scan_summary row_id_field_candidates must be a stable string list")
    recommended_row_id_field = payload.get("recommended_row_id_field")
    if recommended_row_id_field is not None and not isinstance(recommended_row_id_field, str):
        raise ExecutiveContractError("pattern_scan_summary recommended_row_id_field must be a string or null")


def _emit_fail_run(*, paths: PatternScanPaths, exp001_run: str, error_message: str) -> None:
    created_run_root = False
    try:
        paths.experiment_root.mkdir(parents=True, exist_ok=False)
        created_run_root = True
        stage_summary = _build_fail_stage_summary(exp001_run=exp001_run, error_message=error_message)
        _write_json(paths.experiment_root / "stage_summary.json", stage_summary, root=paths.run_root)
        _write_json(
            paths.experiment_root / "manifest.json",
            _build_fail_manifest(paths=paths, stage_summary=stage_summary),
            root=paths.run_root,
        )
    except Exception:
        if created_run_root and paths.run_root.exists():
            shutil.rmtree(paths.run_root)
        raise


def _build_fail_stage_summary(*, exp001_run: str, error_message: str) -> dict[str, Any]:
    return {
        "stage": STAGE_NAME,
        "status": "FAIL",
        "upstream_exp001_run": exp001_run,
        "schema_version": SCHEMA_VERSION,
        "n_candidate_features": 0,
        "recommended_source_relpath": "",
        "primary_verdict": PRIMARY_VERDICT_FAIL,
        "error_message": error_message,
    }


def _build_manifest(*, paths: PatternScanPaths, result: dict[str, Any]) -> dict[str, Any]:
    recommended_source_relpath = result["pattern_scan_summary"]["recommended_source_relpath"]
    recommended_source_path = (paths.input_root / recommended_source_relpath).resolve()
    _ensure_within(recommended_source_path, paths.input_root)
    outputs = {
        "manifest": str((paths.experiment_root / "manifest.json").relative_to(paths.run_root)),
        "stage_summary": str((paths.experiment_root / "stage_summary.json").relative_to(paths.run_root)),
        "pattern_scan_summary": str((paths.outputs_root / "pattern_scan_summary.json").relative_to(paths.run_root)),
    }
    return {
        "stage": STAGE_NAME,
        "run_id": paths.run_root.name,
        "run_root": str(paths.run_root),
        "experiment_root": str(paths.experiment_root),
        "schema_version": SCHEMA_VERSION,
        "inputs": {
            "input_root": str(paths.input_root),
            "upstream_exp001_root": str(paths.exp001_root),
            "upstream_exp001_stage_summary": _file_ref(paths.exp001_root / "stage_summary.json", paths.repo_root),
            "upstream_exp001_field_inventory": _file_ref(paths.exp001_root / "outputs" / "field_inventory.json", paths.repo_root),
            "upstream_exp001_schema_profile": _file_ref(paths.exp001_root / "outputs" / "schema_profile.json", paths.repo_root),
            "recommended_source": _file_ref(recommended_source_path, paths.input_root),
        },
        "outputs": outputs,
        "output_hashes": {
            key: _sha256_file(paths.run_root / relpath)
            for key, relpath in outputs.items()
            if (paths.run_root / relpath).exists()
        },
        "stage_summary": result["stage_summary"],
    }


def _build_fail_manifest(*, paths: PatternScanPaths, stage_summary: dict[str, Any]) -> dict[str, Any]:
    outputs = {
        "manifest": str((paths.experiment_root / "manifest.json").relative_to(paths.run_root)),
        "stage_summary": str((paths.experiment_root / "stage_summary.json").relative_to(paths.run_root)),
    }
    return {
        "stage": STAGE_NAME,
        "run_id": paths.run_root.name,
        "run_root": str(paths.run_root),
        "experiment_root": str(paths.experiment_root),
        "schema_version": SCHEMA_VERSION,
        "inputs": {
            "input_root": str(paths.input_root),
            "upstream_exp001_root": str(paths.exp001_root),
        },
        "outputs": outputs,
        "output_hashes": {
            key: _sha256_file(paths.run_root / relpath)
            for key, relpath in outputs.items()
            if (paths.run_root / relpath).exists()
        },
        "stage_summary": stage_summary,
    }


def _file_ref(path: Path, root: Path) -> dict[str, str]:
    return {
        "relpath": str(path.relative_to(root)),
        "sha256": _sha256_file(path),
    }


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: Any, *, root: Path) -> None:
    _ensure_within(path, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_value(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
