from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from ringest.exploratory_clustering import ExecutiveContractError, run_exploratory_clustering

STAGE_NAME = "exp003_exploratory_clustering"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _make_repo(tmp_path: Path) -> tuple[Path, Path]:
    repo_root = tmp_path / "repo"
    input_root = repo_root / "data" / "raw" / "ringhier_snapshot"
    source_relpath = "tables/cluster_source.json"
    _write_json(
        input_root / source_relpath,
        [
            {"event_id": "e01", "f1": 0.0, "f2": 0.0, "id_like": "id-01", "bad_field": None},
            {"event_id": "e02", "f1": 0.2, "f2": 0.1, "id_like": "id-02", "bad_field": None},
            {"event_id": "e03", "f1": 0.1, "f2": 0.2, "id_like": "id-03", "bad_field": None},
            {"event_id": "e04", "f1": 9.8, "f2": 10.0, "id_like": "id-04", "bad_field": None},
            {"event_id": "e05", "f1": 10.1, "f2": 9.9, "id_like": "id-05", "bad_field": None},
            {"event_id": "e06", "f1": 10.0, "f2": 10.2, "id_like": "id-06", "bad_field": None},
        ],
    )
    return repo_root, input_root


def _write_exp001(repo_root: Path, run_id: str, *, source_relpath: str = "tables/cluster_source.json") -> None:
    root = repo_root / "runs" / run_id / "experiment" / "exp001_feature_inventory"
    _write_json(root / "stage_summary.json", {"stage": "exp001_feature_inventory", "status": "PASS"})
    _write_json(
        root / "outputs" / "field_inventory.json",
        [
            {
                "field_name": "event_id",
                "source_file": "cluster_source.json",
                "source_relpath": source_relpath,
                "dtype_observed": "string",
                "nonnull_count": 6,
                "null_count": 0,
                "coverage_fraction": 1.0,
                "n_unique": 6,
                "all_null": False,
                "constant": False,
                "candidate_role": "identifier",
                "usability_class": "usable",
            },
            {
                "field_name": "f1",
                "source_file": "cluster_source.json",
                "source_relpath": source_relpath,
                "dtype_observed": "number",
                "nonnull_count": 6,
                "null_count": 0,
                "coverage_fraction": 1.0,
                "n_unique": 6,
                "all_null": False,
                "constant": False,
                "candidate_role": "numeric_feature",
                "usability_class": "usable",
            },
            {
                "field_name": "f2",
                "source_file": "cluster_source.json",
                "source_relpath": source_relpath,
                "dtype_observed": "number",
                "nonnull_count": 6,
                "null_count": 0,
                "coverage_fraction": 1.0,
                "n_unique": 6,
                "all_null": False,
                "constant": False,
                "candidate_role": "numeric_feature",
                "usability_class": "usable",
            },
            {
                "field_name": "id_like",
                "source_file": "cluster_source.json",
                "source_relpath": source_relpath,
                "dtype_observed": "string",
                "nonnull_count": 6,
                "null_count": 0,
                "coverage_fraction": 1.0,
                "n_unique": 6,
                "all_null": False,
                "constant": False,
                "candidate_role": "identifier",
                "usability_class": "usable",
            },
            {
                "field_name": "bad_field",
                "source_file": "cluster_source.json",
                "source_relpath": source_relpath,
                "dtype_observed": "null",
                "nonnull_count": 0,
                "null_count": 6,
                "coverage_fraction": 0.0,
                "n_unique": 0,
                "all_null": True,
                "constant": False,
                "candidate_role": "unknown",
                "usability_class": "unusable",
            },
        ],
    )


def _write_exp002(repo_root: Path, run_id: str, *, source_relpath: str = "tables/cluster_source.json") -> None:
    root = repo_root / "runs" / run_id / "experiment" / "exp002_pattern_scan_global_simple"
    _write_json(root / "stage_summary.json", {"stage": "exp002_pattern_scan_global_simple", "status": "PASS"})
    _write_json(
        root / "outputs" / "pattern_scan_summary.json",
        {
            "recommended_source_relpath": source_relpath,
            "recommended_row_id_field": "event_id",
            "row_id_field_candidates": ["event_id", "id_like"],
            "candidate_feature_fields": ["event_id", "f1", "f2", "bad_field", "id_like"],
        },
    )


def _stage_root(repo_root: Path, run_id: str) -> Path:
    return repo_root / "runs" / run_id / "experiment" / STAGE_NAME


def test_fail_if_required_exp001_outputs_missing(tmp_path: Path) -> None:
    repo_root, _ = _make_repo(tmp_path)
    _write_exp002(repo_root, "exp002")
    with pytest.raises(ExecutiveContractError):
        run_exploratory_clustering(run_id="exp003", exp001_run="exp001", exp002_run="exp002", repo_root=repo_root)


def test_fail_if_required_exp002_outputs_missing(tmp_path: Path) -> None:
    repo_root, _ = _make_repo(tmp_path)
    _write_exp001(repo_root, "exp001")
    with pytest.raises(ExecutiveContractError):
        run_exploratory_clustering(run_id="exp003", exp001_run="exp001", exp002_run="exp002", repo_root=repo_root)


def test_no_writes_outside_run_root(tmp_path: Path) -> None:
    repo_root, _ = _make_repo(tmp_path)
    _write_exp001(repo_root, "exp001")
    _write_exp002(repo_root, "exp002")
    run_id = "exp003"
    run_exploratory_clustering(run_id=run_id, exp001_run="exp001", exp002_run="exp002", repo_root=repo_root)
    generated = sorted(path for path in repo_root.rglob("*") if path.is_file())
    expected_prefix = (repo_root / "runs" / run_id).resolve()
    for path in generated:
        if path.is_relative_to((repo_root / "data").resolve()):
            continue
        if path.is_relative_to((repo_root / "runs" / "exp001").resolve()):
            continue
        if path.is_relative_to((repo_root / "runs" / "exp002").resolve()):
            continue
        assert path.resolve().is_relative_to(expected_prefix)


def test_rejects_existing_run_id_without_overwrite(tmp_path: Path) -> None:
    repo_root, _ = _make_repo(tmp_path)
    _write_exp001(repo_root, "exp001")
    _write_exp002(repo_root, "exp002")
    run_exploratory_clustering(run_id="exp003", exp001_run="exp001", exp002_run="exp002", repo_root=repo_root)
    with pytest.raises(ExecutiveContractError):
        run_exploratory_clustering(run_id="exp003", exp001_run="exp001", exp002_run="exp002", repo_root=repo_root)


def test_does_not_select_unusable_fields(tmp_path: Path) -> None:
    repo_root, _ = _make_repo(tmp_path)
    _write_exp001(repo_root, "exp001")
    _write_exp002(repo_root, "exp002")
    run_exploratory_clustering(run_id="exp003", exp001_run="exp001", exp002_run="exp002", repo_root=repo_root)
    with (_stage_root(repo_root, "exp003") / "outputs" / "feature_set_used.json").open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    selected = {item["field_name"] for item in payload["selected_features"]}
    assert "bad_field" not in selected


def test_excludes_obvious_identifiers_from_feature_set(tmp_path: Path) -> None:
    repo_root, _ = _make_repo(tmp_path)
    _write_exp001(repo_root, "exp001")
    _write_exp002(repo_root, "exp002")
    run_exploratory_clustering(run_id="exp003", exp001_run="exp001", exp002_run="exp002", repo_root=repo_root)
    with (_stage_root(repo_root, "exp003") / "outputs" / "feature_set_used.json").open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    selected = {item["field_name"] for item in payload["selected_features"]}
    assert "event_id" not in selected
    assert "id_like" not in selected


def test_same_input_and_seed_same_cluster_assignments(tmp_path: Path) -> None:
    repo_root, _ = _make_repo(tmp_path)
    _write_exp001(repo_root, "exp001")
    _write_exp002(repo_root, "exp002")
    run_exploratory_clustering(run_id="exp003_a", exp001_run="exp001", exp002_run="exp002", random_seed=19, repo_root=repo_root)
    run_exploratory_clustering(run_id="exp003_b", exp001_run="exp001", exp002_run="exp002", random_seed=19, repo_root=repo_root)
    a = (_stage_root(repo_root, "exp003_a") / "outputs" / "cluster_assignments.csv").read_text(encoding="utf-8")
    b = (_stage_root(repo_root, "exp003_b") / "outputs" / "cluster_assignments.csv").read_text(encoding="utf-8")
    assert a == b


def test_pass_always_emits_manifest_and_stage_summary(tmp_path: Path) -> None:
    repo_root, _ = _make_repo(tmp_path)
    _write_exp001(repo_root, "exp001")
    _write_exp002(repo_root, "exp002")
    run_exploratory_clustering(run_id="exp003", exp001_run="exp001", exp002_run="exp002", repo_root=repo_root)
    stage_root = _stage_root(repo_root, "exp003")
    assert (stage_root / "manifest.json").is_file()
    assert (stage_root / "stage_summary.json").is_file()


def test_fail_leaves_no_ambiguous_downstream_artifacts(tmp_path: Path) -> None:
    repo_root, _ = _make_repo(tmp_path)
    _write_exp001(repo_root, "exp001")
    _write_exp002(repo_root, "exp002")
    bad_root = repo_root / "runs" / "exp002" / "experiment" / "exp002_pattern_scan_global_simple" / "outputs" / "pattern_scan_summary.json"
    _write_json(
        bad_root,
        {
            "recommended_source_relpath": "tables/missing.json",
            "recommended_row_id_field": "event_id",
            "candidate_feature_fields": ["f1", "f2"],
        },
    )
    with pytest.raises(ExecutiveContractError):
        run_exploratory_clustering(run_id="exp003", exp001_run="exp001", exp002_run="exp002", repo_root=repo_root)
    assert not (repo_root / "runs" / "exp003").exists()


def test_analytical_verdict_does_not_alter_pass_fail_executive_status(tmp_path: Path) -> None:
    repo_root, _ = _make_repo(tmp_path)
    _write_exp001(repo_root, "exp001")
    _write_exp002(repo_root, "exp002")
    run_exploratory_clustering(run_id="exp003", exp001_run="exp001", exp002_run="exp002", repo_root=repo_root)
    with (_stage_root(repo_root, "exp003") / "stage_summary.json").open("r", encoding="utf-8") as handle:
        stage_summary = json.load(handle)
    assert stage_summary["status"] == "PASS"
    assert stage_summary["analytical_verdict"] in {
        "CLUSTER_STRUCTURE_DETECTED",
        "WEAK_CLUSTER_STRUCTURE",
        "NO_CLEAR_CLUSTER_STRUCTURE",
    }


def test_cluster_quality_metrics_and_assignments_are_coherent(tmp_path: Path) -> None:
    repo_root, _ = _make_repo(tmp_path)
    _write_exp001(repo_root, "exp001")
    _write_exp002(repo_root, "exp002")
    run_exploratory_clustering(run_id="exp003", exp001_run="exp001", exp002_run="exp002", repo_root=repo_root)
    stage_root = _stage_root(repo_root, "exp003")
    with (stage_root / "outputs" / "cluster_quality_metrics.json").open("r", encoding="utf-8") as handle:
        metrics = json.load(handle)
    with (stage_root / "outputs" / "cluster_assignments.csv").open("r", encoding="utf-8", newline="") as handle:
        assignments = list(csv.DictReader(handle))
    assert int(metrics["n_rows_used"]) == len(assignments)
    observed = {}
    for row in assignments:
        observed[row["cluster_label"]] = observed.get(row["cluster_label"], 0) + 1
    assert observed == metrics["cluster_size_distribution"]


def test_no_undeclared_artifacts_outside_experiment_folder(tmp_path: Path) -> None:
    repo_root, _ = _make_repo(tmp_path)
    _write_exp001(repo_root, "exp001")
    _write_exp002(repo_root, "exp002")
    run_exploratory_clustering(run_id="exp003", exp001_run="exp001", exp002_run="exp002", repo_root=repo_root)
    stage_root = _stage_root(repo_root, "exp003")
    actual = sorted(str(path.relative_to(stage_root)) for path in stage_root.rglob("*") if path.is_file())
    assert actual == sorted(
        [
            "manifest.json",
            "stage_summary.json",
            "outputs/cluster_assignments.csv",
            "outputs/cluster_quality_metrics.json",
            "outputs/embedding_2d.csv",
            "outputs/feature_set_used.json",
        ]
    )
