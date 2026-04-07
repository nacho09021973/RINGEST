from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

STAGE_NAME = "exp001_feature_inventory"
PRIMARY_VERDICT_PASS = "SNAPSHOT_PROFILED"
PRIMARY_VERDICT_FAIL = "INVENTORY_FAILED"
COVERAGE_RULES_VERSION = "v1"
IMPORT_MANIFEST_DEFAULT = "data/manifests/import_from_ringhier.json"

REPO_ROOT = Path(__file__).resolve().parent.parent


class ExecutiveContractError(RuntimeError):
    """Raised when preflight or emission contracts fail."""


class InventoryError(RuntimeError):
    """Raised when the snapshot cannot be profiled deterministically."""


@dataclass(frozen=True)
class InventoryPaths:
    repo_root: Path
    run_root: Path
    experiment_root: Path
    outputs_root: Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=STAGE_NAME)
    parser.add_argument("--input-root", required=True, help="Snapshot root to profile.")
    parser.add_argument("--run-id", required=True, help="Run identifier under runs/.")
    return parser.parse_args(argv)


def run_feature_inventory(
    *,
    input_root: Path,
    run_id: str,
    repo_root: Path | None = None,
    import_manifest_path: Path | None = None,
) -> InventoryPaths:
    repo_root = (repo_root or REPO_ROOT).resolve()
    input_root = input_root.resolve()
    import_manifest_path = (import_manifest_path or (repo_root / IMPORT_MANIFEST_DEFAULT)).resolve()

    paths = _build_paths(repo_root=repo_root, run_id=run_id)
    _validate_preflight(
        input_root=input_root,
        import_manifest_path=import_manifest_path,
        paths=paths,
        run_id=run_id,
    )
    result = _profile_snapshot(input_root=input_root, import_manifest_path=import_manifest_path)

    created_run_root = False
    try:
        _mkdir(paths.outputs_root)
        created_run_root = True
        _write_json(paths.outputs_root / "field_inventory.json", result["field_inventory"])
        _write_csv(paths.outputs_root / "coverage_by_field.csv", result["coverage_rows"])
        _write_json(paths.outputs_root / "schema_profile.json", result["schema_profile"])
        _write_json(paths.experiment_root / "stage_summary.json", result["stage_summary"])
        _write_json(
            paths.experiment_root / "manifest.json",
            _build_manifest_payload(
                paths=paths,
                input_root=input_root,
                import_manifest_info=result["import_manifest_info"],
                stage_summary=result["stage_summary"],
                outputs={
                    "field_inventory": str((paths.outputs_root / "field_inventory.json").relative_to(paths.run_root)),
                    "coverage_by_field": str((paths.outputs_root / "coverage_by_field.csv").relative_to(paths.run_root)),
                    "schema_profile": str((paths.outputs_root / "schema_profile.json").relative_to(paths.run_root)),
                    "stage_summary": str((paths.experiment_root / "stage_summary.json").relative_to(paths.run_root)),
                },
            ),
        )
    except Exception as exc:  # pragma: no cover
        if created_run_root and paths.run_root.exists():
            shutil.rmtree(paths.run_root)
        raise ExecutiveContractError(f"failed to emit required artifacts: {exc}") from exc

    return paths


def _validate_preflight(
    *,
    input_root: Path,
    import_manifest_path: Path,
    paths: InventoryPaths,
    run_id: str,
) -> None:
    if not run_id or Path(run_id).name != run_id or run_id in {".", ".."}:
        raise ExecutiveContractError(f"invalid run_id: {run_id!r}")
    if not input_root.exists() or not input_root.is_dir():
        raise ExecutiveContractError(f"input_root does not exist: {input_root}")
    if not import_manifest_path.exists() or not import_manifest_path.is_file():
        raise ExecutiveContractError(f"import manifest does not exist: {import_manifest_path}")
    if paths.run_root.exists():
        raise ExecutiveContractError(f"run_id already exists: {paths.run_root}")


def _build_paths(*, repo_root: Path, run_id: str) -> InventoryPaths:
    run_root = (repo_root / "runs" / run_id).resolve()
    experiment_root = (run_root / "experiment" / STAGE_NAME).resolve()
    outputs_root = (experiment_root / "outputs").resolve()
    _ensure_within(run_root, repo_root / "runs")
    _ensure_within(experiment_root, run_root)
    _ensure_within(outputs_root, run_root)
    return InventoryPaths(
        repo_root=repo_root,
        run_root=run_root,
        experiment_root=experiment_root,
        outputs_root=outputs_root,
    )


def _profile_snapshot(*, input_root: Path, import_manifest_path: Path) -> dict[str, Any]:
    import_manifest_info = _read_import_manifest_info(import_manifest_path)
    structured_files = sorted(path for path in input_root.rglob("*.json") if path.is_file())

    per_file_field_counts: dict[str, int] = {}
    field_inventory: list[dict[str, Any]] = []
    schema_basis: list[dict[str, Any]] = []

    for path in structured_files:
        source_relpath = str(path.relative_to(input_root))
        records = _extract_records(path)
        field_names = sorted({key for record in records for key in record.keys()})
        per_file_field_counts[source_relpath] = len(field_names)
        schema_fields: list[dict[str, str]] = []

        for field_name in field_names:
            values = [record.get(field_name) for record in records]
            summary = _summarize_field(
                values=values,
                n_rows=len(records),
                field_name=field_name,
                source_file=path.name,
                source_relpath=source_relpath,
            )
            field_inventory.append(summary)
            schema_fields.append(
                {
                    "field_name": field_name,
                    "dtype_observed": summary["dtype_observed"],
                }
            )

        schema_basis.append(
            {
                "source_relpath": source_relpath,
                "n_rows": len(records),
                "fields": schema_fields,
            }
        )

    schema_hash = _sha256_json(schema_basis)
    n_fields_usable = sum(1 for row in field_inventory if row["usability_class"] == "usable")
    n_fields_partial = sum(1 for row in field_inventory if row["usability_class"] == "partial")
    n_fields_unusable = sum(1 for row in field_inventory if row["usability_class"] == "unusable")

    schema_profile = {
        "n_files_profiled": len(structured_files),
        "n_fields_total": len(field_inventory),
        "n_fields_usable": n_fields_usable,
        "n_fields_partial": n_fields_partial,
        "n_fields_unusable": n_fields_unusable,
        "per_file_field_counts": per_file_field_counts,
        "schema_hash": schema_hash,
        "coverage_rules_version": COVERAGE_RULES_VERSION,
    }
    stage_summary = {
        "stage": STAGE_NAME,
        "status": "PASS",
        "input_root": str(input_root),
        "import_manifest_path": str(import_manifest_path),
        "import_manifest_sha256": import_manifest_info["sha256"],
        "import_manifest_entries": import_manifest_info["entries_count"],
        "n_files_profiled": len(structured_files),
        "n_fields_total": len(field_inventory),
        "n_fields_usable": n_fields_usable,
        "n_fields_partial": n_fields_partial,
        "n_fields_unusable": n_fields_unusable,
        "schema_hash": schema_hash,
        "coverage_rules_version": COVERAGE_RULES_VERSION,
        "primary_verdict": PRIMARY_VERDICT_PASS,
    }
    coverage_rows = [
        {
            "source_relpath": row["source_relpath"],
            "field_name": row["field_name"],
            "nonnull_count": str(row["nonnull_count"]),
            "null_count": str(row["null_count"]),
            "coverage_fraction": _format_fraction(row["coverage_fraction"]),
            "usability_class": row["usability_class"],
        }
        for row in field_inventory
    ]
    return {
        "field_inventory": field_inventory,
        "coverage_rows": coverage_rows,
        "schema_profile": schema_profile,
        "stage_summary": stage_summary,
        "import_manifest_info": import_manifest_info,
    }


def _extract_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if isinstance(data, list):
        if not all(isinstance(row, dict) for row in data):
            raise InventoryError(f"unsupported list structure in {path}")
        return [dict(row) for row in data]

    if isinstance(data, dict):
        if "rows" in data:
            rows = data["rows"]
            if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
                raise InventoryError(f"unsupported rows structure in {path}")
            return [dict(row) for row in rows]
        if data and all(isinstance(value, dict) for value in data.values()):
            return [dict(data[key]) for key in sorted(data.keys())]
        return [dict(data)]

    raise InventoryError(f"unsupported JSON root type in {path}")


def _summarize_field(
    *,
    values: list[Any],
    n_rows: int,
    field_name: str,
    source_file: str,
    source_relpath: str,
) -> dict[str, Any]:
    nonnull_values = [value for value in values if value is not None]
    nonnull_count = len(nonnull_values)
    null_count = n_rows - nonnull_count
    coverage_fraction = 0.0 if n_rows == 0 else round(nonnull_count / n_rows, 6)
    dtype_observed = _dtype_observed(nonnull_values)
    unique_values = {_canonical_value(value) for value in nonnull_values}
    n_unique = len(unique_values)
    all_null = nonnull_count == 0
    constant = nonnull_count > 0 and n_unique == 1
    candidate_role = _candidate_role(
        field_name=field_name,
        dtype_observed=dtype_observed,
        nonnull_count=nonnull_count,
        n_rows=n_rows,
        n_unique=n_unique,
    )
    usability_class = _usability_class(
        coverage_fraction=coverage_fraction,
        all_null=all_null,
        constant=constant,
    )
    return {
        "field_name": field_name,
        "source_file": source_file,
        "source_relpath": source_relpath,
        "dtype_observed": dtype_observed,
        "nonnull_count": nonnull_count,
        "null_count": null_count,
        "coverage_fraction": coverage_fraction,
        "n_unique": n_unique,
        "all_null": all_null,
        "constant": constant,
        "candidate_role": candidate_role,
        "usability_class": usability_class,
    }


def _dtype_observed(values: list[Any]) -> str:
    if not values:
        return "null"
    observed = {_value_kind(value) for value in values}
    if observed == {"integer", "number"}:
        return "number"
    if len(observed) == 1:
        return next(iter(observed))
    return "mixed"


def _value_kind(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "unknown"


def _candidate_role(
    *,
    field_name: str,
    dtype_observed: str,
    nonnull_count: int,
    n_rows: int,
    n_unique: int,
) -> str:
    normalized = field_name.lower()
    if normalized in {"id", "event_id", "pipeline_event_id", "candidate_id", "run_id", "row_id"} or normalized.endswith("_id"):
        return "identifier"
    if any(token in normalized for token in ("verdict", "target", "status", "result", "label")):
        return "target"
    if dtype_observed in {"integer", "number"}:
        return "numeric_feature"
    if dtype_observed in {"string", "boolean"}:
        if any(token in normalized for token in ("source", "reason", "note", "path", "url", "version", "timestamp")):
            return "metadata"
        if nonnull_count > 0 and n_unique <= max(1, min(20, n_rows // 2)):
            return "categorical_feature"
        return "metadata"
    if dtype_observed in {"object", "array"}:
        return "metadata"
    return "unknown"


def _usability_class(*, coverage_fraction: float, all_null: bool, constant: bool) -> str:
    if coverage_fraction < 0.20 or all_null or constant:
        return "unusable"
    if 0.20 <= coverage_fraction < 0.95 and not all_null:
        return "partial"
    if coverage_fraction >= 0.95 and not all_null and not constant:
        return "usable"
    return "unusable"


def _read_import_manifest_info(import_manifest_path: Path) -> dict[str, Any]:
    raw_bytes = import_manifest_path.read_bytes()
    payload = json.loads(raw_bytes.decode("utf-8"))
    return {
        "path": str(import_manifest_path),
        "sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "manifest_name": payload.get("manifest_name"),
        "created_at_utc": payload.get("created_at_utc"),
        "raw_snapshot_root": payload.get("raw_snapshot_root"),
        "entries_count": len(payload.get("entries", [])),
    }


def _build_manifest_payload(
    *,
    paths: InventoryPaths,
    input_root: Path,
    import_manifest_info: dict[str, Any],
    stage_summary: dict[str, Any],
    outputs: dict[str, str],
) -> dict[str, Any]:
    return {
        "stage": STAGE_NAME,
        "run_id": paths.run_root.name,
        "run_root": str(paths.run_root),
        "experiment_root": str(paths.experiment_root),
        "input_root": str(input_root),
        "import_manifest": import_manifest_info,
        "stage_summary": stage_summary,
        "outputs": outputs,
    }


def _build_fail_stage_summary(
    *,
    input_root: Path,
    import_manifest_path: Path,
    error_message: str,
) -> dict[str, Any]:
    return {
        "stage": STAGE_NAME,
        "status": "FAIL",
        "input_root": str(input_root),
        "import_manifest_path": str(import_manifest_path),
        "n_files_profiled": 0,
        "n_fields_total": 0,
        "n_fields_usable": 0,
        "n_fields_partial": 0,
        "n_fields_unusable": 0,
        "schema_hash": None,
        "coverage_rules_version": COVERAGE_RULES_VERSION,
        "primary_verdict": PRIMARY_VERDICT_FAIL,
        "error_message": error_message,
    }


def _sha256_json(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _canonical_value(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _format_fraction(value: float) -> str:
    return f"{value:.6f}"


def _write_json(path: Path, payload: Any) -> None:
    _ensure_within(path, path.parents[2] if path.name in {"field_inventory.json", "coverage_by_field.csv", "schema_profile.json"} else path.parents[1])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    _ensure_within(path, path.parents[2])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["source_relpath", "field_name", "nonnull_count", "null_count", "coverage_fraction", "usability_class"],
        )
        writer.writeheader()
        writer.writerows(rows)


def _mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=False)


def _ensure_within(path: Path, root: Path) -> None:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    if resolved_root not in {resolved_path, *resolved_path.parents}:
        raise RuntimeError(f"path escapes root: {resolved_path} !<= {resolved_root}")
