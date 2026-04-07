from __future__ import annotations

import argparse
import csv
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from ringest.feature_inventory import REPO_ROOT, _ensure_within

STAGE_NAME = "exp003_exploratory_clustering"
PATTERN_SCAN_STAGE = "exp002_pattern_scan_global_simple"
FEATURE_INVENTORY_STAGE = "exp001_feature_inventory"
INPUT_ROOT_DEFAULT = "data/raw/ringhier_snapshot"
SELECTION_RULES_VERSION = "v1"
METHOD_NAME = "standard_scaler+pca2+kmeans"
DEFAULT_RANDOM_SEED = 17


class ExecutiveContractError(RuntimeError):
    """Raised when required contracts fail before or during deterministic execution."""


@dataclass(frozen=True)
class ClusteringPaths:
    repo_root: Path
    input_root: Path
    run_root: Path
    experiment_root: Path
    outputs_root: Path
    exp001_root: Path
    exp002_root: Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=STAGE_NAME)
    parser.add_argument("--run-id", required=True, help="Run identifier under runs/.")
    parser.add_argument("--exp001-run", required=True, help="Upstream exp001 run identifier.")
    parser.add_argument("--exp002-run", required=True, help="Upstream exp002 run identifier.")
    parser.add_argument("--random-seed", type=int, default=DEFAULT_RANDOM_SEED, help="Deterministic seed.")
    return parser.parse_args(argv)


def run_exploratory_clustering(
    *,
    run_id: str,
    exp001_run: str,
    exp002_run: str,
    random_seed: int = DEFAULT_RANDOM_SEED,
    repo_root: Path | None = None,
) -> ClusteringPaths:
    repo_root = (repo_root or REPO_ROOT).resolve()
    paths = _build_paths(repo_root=repo_root, run_id=run_id, exp001_run=exp001_run, exp002_run=exp002_run)
    _validate_preflight(paths=paths, run_id=run_id)

    result = _compute_clustering(paths=paths, exp001_run=exp001_run, exp002_run=exp002_run, random_seed=random_seed)

    created_run_root = False
    try:
        paths.outputs_root.mkdir(parents=True, exist_ok=False)
        created_run_root = True
        _write_json(paths.outputs_root / "feature_set_used.json", result["feature_set_used"])
        _write_csv(
            paths.outputs_root / "cluster_assignments.csv",
            ["row_id", "cluster_label", "embedding_x", "embedding_y"],
            result["cluster_assignments"],
        )
        _write_json(paths.outputs_root / "cluster_quality_metrics.json", result["cluster_quality_metrics"])
        _write_csv(
            paths.outputs_root / "embedding_2d.csv",
            ["row_id", "embedding_x", "embedding_y", "cluster_label"],
            result["embedding_rows"],
        )
        _write_json(paths.experiment_root / "stage_summary.json", result["stage_summary"])
        _write_json(paths.experiment_root / "manifest.json", _build_manifest(paths=paths, result=result))
    except Exception as exc:  # pragma: no cover
        if created_run_root and paths.run_root.exists():
            shutil.rmtree(paths.run_root)
        raise ExecutiveContractError(f"failed to emit required artifacts: {exc}") from exc

    return paths


def _build_paths(*, repo_root: Path, run_id: str, exp001_run: str, exp002_run: str) -> ClusteringPaths:
    input_root = (repo_root / INPUT_ROOT_DEFAULT).resolve()
    run_root = (repo_root / "runs" / run_id).resolve()
    experiment_root = (run_root / "experiment" / STAGE_NAME).resolve()
    outputs_root = (experiment_root / "outputs").resolve()
    exp001_root = (repo_root / "runs" / exp001_run / "experiment" / FEATURE_INVENTORY_STAGE).resolve()
    exp002_root = (repo_root / "runs" / exp002_run / "experiment" / PATTERN_SCAN_STAGE).resolve()
    _ensure_within(run_root, repo_root / "runs")
    _ensure_within(experiment_root, run_root)
    _ensure_within(outputs_root, run_root)
    _ensure_within(exp001_root, repo_root / "runs")
    _ensure_within(exp002_root, repo_root / "runs")
    return ClusteringPaths(
        repo_root=repo_root,
        input_root=input_root,
        run_root=run_root,
        experiment_root=experiment_root,
        outputs_root=outputs_root,
        exp001_root=exp001_root,
        exp002_root=exp002_root,
    )


def _validate_preflight(*, paths: ClusteringPaths, run_id: str) -> None:
    if not run_id or Path(run_id).name != run_id or run_id in {".", ".."}:
        raise ExecutiveContractError(f"invalid run_id: {run_id!r}")
    if paths.run_root.exists():
        raise ExecutiveContractError(f"run_id already exists: {paths.run_root}")
    if not paths.input_root.exists():
        raise ExecutiveContractError(f"input_root does not exist: {paths.input_root}")

    required_exp001 = [
        paths.exp001_root / "outputs" / "field_inventory.json",
        paths.exp001_root / "stage_summary.json",
    ]
    required_exp002 = [
        paths.exp002_root / "outputs" / "pattern_scan_summary.json",
        paths.exp002_root / "stage_summary.json",
    ]
    for path in required_exp001:
        if not path.exists():
            raise ExecutiveContractError(f"missing required exp001 output: {path}")
    for path in required_exp002:
        if not path.exists():
            raise ExecutiveContractError(f"missing required exp002 output: {path}")


def _compute_clustering(
    *,
    paths: ClusteringPaths,
    exp001_run: str,
    exp002_run: str,
    random_seed: int,
) -> dict[str, Any]:
    field_inventory = _read_json(paths.exp001_root / "outputs" / "field_inventory.json")
    pattern_summary = _read_json(paths.exp002_root / "outputs" / "pattern_scan_summary.json")

    recommended_source_relpath = pattern_summary.get("recommended_source_relpath")
    if not isinstance(recommended_source_relpath, str) or not recommended_source_relpath:
        raise ExecutiveContractError("exp002 pattern_scan_summary.json lacks recommended_source_relpath")
    source_path = (paths.input_root / recommended_source_relpath).resolve()
    _ensure_within(source_path, paths.input_root)
    if not source_path.exists():
        raise ExecutiveContractError(f"recommended source does not exist: {source_path}")

    candidate_feature_fields = pattern_summary.get("candidate_feature_fields")
    if not isinstance(candidate_feature_fields, list) or not candidate_feature_fields:
        raise ExecutiveContractError("exp002 pattern_scan_summary.json lacks candidate_feature_fields")
    candidate_feature_fields = [field for field in candidate_feature_fields if isinstance(field, str)]
    if not candidate_feature_fields:
        raise ExecutiveContractError("exp002 candidate_feature_fields is empty after validation")

    recommended_row_id_field = pattern_summary.get("recommended_row_id_field")
    row_id_candidates = pattern_summary.get("row_id_field_candidates", [])
    if not isinstance(row_id_candidates, list):
        row_id_candidates = []

    inventory_index = {
        (row["source_relpath"], row["field_name"]): row
        for row in field_inventory
        if isinstance(row, dict)
    }

    excluded_features: list[dict[str, str]] = []
    selected_features: list[dict[str, str]] = []
    allowed_feature_names: list[str] = []

    for field_name in sorted(set(candidate_feature_fields)):
        row = inventory_index.get((recommended_source_relpath, field_name))
        if row is None:
            excluded_features.append({"field_name": field_name, "source_relpath": recommended_source_relpath, "reason": "not_present_in_exp001"})
            continue
        if row.get("usability_class") != "usable":
            excluded_features.append({"field_name": field_name, "source_relpath": recommended_source_relpath, "reason": "not_usable_in_exp001"})
            continue
        if row.get("candidate_role") in {"identifier", "metadata", "unknown", "target"}:
            excluded_features.append({"field_name": field_name, "source_relpath": recommended_source_relpath, "reason": f"excluded_role:{row.get('candidate_role')}"})
            continue
        if row.get("dtype_observed") not in {"integer", "number"}:
            excluded_features.append({"field_name": field_name, "source_relpath": recommended_source_relpath, "reason": f"excluded_dtype:{row.get('dtype_observed')}"})
            continue
        allowed_feature_names.append(field_name)
        selected_features.append({"field_name": field_name, "source_relpath": recommended_source_relpath, "reason": "usable_numeric_feature_from_exp001_and_exp002"})

    if not allowed_feature_names:
        raise ExecutiveContractError("no valid auditable feature set could be constructed")

    records = _extract_records(source_path)
    row_id_field = _resolve_row_id_field(records=records, preferred=recommended_row_id_field, candidates=row_id_candidates)
    matrix_rows: list[list[float]] = []
    cluster_rows: list[dict[str, Any]] = []

    for index, record in enumerate(records):
        row_id = _build_row_id(record=record, row_id_field=row_id_field, row_index=index)
        feature_values = [record.get(name) for name in allowed_feature_names]
        if any(value is None for value in feature_values):
            continue
        try:
            numeric_values = [float(value) for value in feature_values]
        except (TypeError, ValueError) as exc:
            raise ExecutiveContractError(f"non-numeric value encountered in selected features: {exc}") from exc
        matrix_rows.append(numeric_values)
        cluster_rows.append({"row_id": row_id})

    if len(matrix_rows) < 3:
        raise ExecutiveContractError("not enough complete rows for deterministic clustering")

    X = np.array(matrix_rows, dtype=float)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    pca = PCA(n_components=2, svd_solver="full")
    embedding = pca.fit_transform(X_scaled)

    max_k = min(5, len(cluster_rows) - 1)
    k_tested = list(range(2, max_k + 1))
    if not k_tested:
        raise ExecutiveContractError("no valid k values available for clustering")

    evaluated: list[dict[str, Any]] = []
    for k in k_tested:
        model = KMeans(n_clusters=k, n_init=10, random_state=random_seed)
        labels = model.fit_predict(X_scaled)
        silhouette = float(silhouette_score(X_scaled, labels))
        evaluated.append(
            {
                "k": k,
                "inertia": float(model.inertia_),
                "silhouette": silhouette,
                "labels": labels,
            }
        )

    best = sorted(evaluated, key=lambda item: (-item["silhouette"], item["k"]))[0]
    labels = [int(label) for label in best["labels"]]

    for index, row in enumerate(cluster_rows):
        row["cluster_label"] = str(labels[index])
        row["embedding_x"] = _format_float(float(embedding[index, 0]))
        row["embedding_y"] = _format_float(float(embedding[index, 1]))

    cluster_assignments = [
        {
            "row_id": row["row_id"],
            "cluster_label": row["cluster_label"],
            "embedding_x": row["embedding_x"],
            "embedding_y": row["embedding_y"],
        }
        for row in cluster_rows
    ]
    embedding_rows = [
        {
            "row_id": row["row_id"],
            "embedding_x": row["embedding_x"],
            "embedding_y": row["embedding_y"],
            "cluster_label": row["cluster_label"],
        }
        for row in cluster_rows
    ]

    cluster_counts: dict[str, int] = {}
    for label in labels:
        label_str = str(label)
        cluster_counts[label_str] = cluster_counts.get(label_str, 0) + 1
    cluster_counts = {key: cluster_counts[key] for key in sorted(cluster_counts, key=int)}

    silhouette_value = float(best["silhouette"])
    analytical_verdict = _analytical_verdict(silhouette_value)

    feature_set_used = {
        "selected_features": selected_features,
        "excluded_features": excluded_features,
        "selection_rules_version": SELECTION_RULES_VERSION,
        "n_selected_features": len(selected_features),
        "source_exp001_run": exp001_run,
        "source_exp002_run": exp002_run,
        "source_relpath": recommended_source_relpath,
        "row_id_field": row_id_field or "synthetic_row_index",
    }
    cluster_quality_metrics = {
        "method_name": METHOD_NAME,
        "method_version": {
            "embedding": "pca_v1",
            "clustering": "kmeans_v1",
            "scaler": "standard_scaler_v1",
        },
        "random_seed": random_seed,
        "n_rows_used": len(cluster_rows),
        "n_features_used": len(selected_features),
        "k_tested": k_tested,
        "selected_k": best["k"],
        "inertia_by_k": {str(item["k"]): _format_float(item["inertia"]) for item in evaluated},
        "silhouette_score": _format_float(silhouette_value),
        "silhouette_by_k": {str(item["k"]): _format_float(item["silhouette"]) for item in evaluated},
        "cluster_size_distribution": cluster_counts,
        "analytical_verdict": analytical_verdict,
    }
    stage_summary = {
        "stage": STAGE_NAME,
        "status": "PASS",
        "source_exp001_run": exp001_run,
        "source_exp002_run": exp002_run,
        "n_rows_used": len(cluster_rows),
        "n_features_used": len(selected_features),
        "selected_k": best["k"],
        "analytical_verdict": analytical_verdict,
        "method_name": METHOD_NAME,
        "random_seed": random_seed,
    }
    return {
        "feature_set_used": feature_set_used,
        "cluster_assignments": cluster_assignments,
        "cluster_quality_metrics": cluster_quality_metrics,
        "embedding_rows": embedding_rows,
        "stage_summary": stage_summary,
    }


def _resolve_row_id_field(*, records: list[dict[str, Any]], preferred: Any, candidates: list[Any]) -> str | None:
    ordered_candidates: list[str] = []
    for value in [preferred, *candidates, "event_id", "pipeline_event_id", "row_id", "entity_id"]:
        if isinstance(value, str) and value and value not in ordered_candidates:
            ordered_candidates.append(value)

    for candidate in ordered_candidates:
        candidate_values = [record.get(candidate) for record in records]
        if all(value is not None for value in candidate_values) and len({str(value) for value in candidate_values}) == len(candidate_values):
            return candidate
    return None


def _build_row_id(*, record: dict[str, Any], row_id_field: str | None, row_index: int) -> str:
    if row_id_field is not None:
        return str(record[row_id_field])
    return f"row_{row_index:06d}"


def _extract_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if isinstance(data, list) and all(isinstance(row, dict) for row in data):
        return [dict(row) for row in data]
    if isinstance(data, dict) and isinstance(data.get("rows"), list) and all(isinstance(row, dict) for row in data["rows"]):
        return [dict(row) for row in data["rows"]]
    if isinstance(data, dict) and data and all(isinstance(value, dict) for value in data.values()):
        return [dict(data[key]) for key in sorted(data.keys())]
    raise ExecutiveContractError(f"unsupported source structure for clustering: {path}")


def _analytical_verdict(silhouette_value: float) -> str:
    if silhouette_value >= 0.50:
        return "CLUSTER_STRUCTURE_DETECTED"
    if silhouette_value >= 0.20:
        return "WEAK_CLUSTER_STRUCTURE"
    return "NO_CLEAR_CLUSTER_STRUCTURE"


def _build_manifest(*, paths: ClusteringPaths, result: dict[str, Any]) -> dict[str, Any]:
    return {
        "stage": STAGE_NAME,
        "run_id": paths.run_root.name,
        "run_root": str(paths.run_root),
        "experiment_root": str(paths.experiment_root),
        "input_root": str(paths.input_root),
        "source_exp001_root": str(paths.exp001_root),
        "source_exp002_root": str(paths.exp002_root),
        "outputs": {
            "feature_set_used": str((paths.outputs_root / "feature_set_used.json").relative_to(paths.run_root)),
            "cluster_assignments": str((paths.outputs_root / "cluster_assignments.csv").relative_to(paths.run_root)),
            "cluster_quality_metrics": str((paths.outputs_root / "cluster_quality_metrics.json").relative_to(paths.run_root)),
            "embedding_2d": str((paths.outputs_root / "embedding_2d.csv").relative_to(paths.run_root)),
            "stage_summary": str((paths.experiment_root / "stage_summary.json").relative_to(paths.run_root)),
        },
        "stage_summary": result["stage_summary"],
    }


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: Any) -> None:
    _ensure_within(path, path.parents[2] if path.name.startswith(("feature_set_used", "cluster_quality_metrics", "embedding_2d", "cluster_assignments")) else path.parents[1])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    _ensure_within(path, path.parents[2])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _format_float(value: float) -> str:
    return f"{value:.6f}"
