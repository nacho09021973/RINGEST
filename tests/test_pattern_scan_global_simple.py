from __future__ import annotations

import json
from pathlib import Path

import pytest

from ringest.pattern_scan_global_simple import ExecutiveContractError, run_pattern_scan_global_simple

STAGE_NAME = "exp002_pattern_scan_global_simple"
SCHEMA_VERSION = "exp002-pattern-scan-0.1"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _make_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    input_root = repo_root / "data" / "raw" / "ringhier_snapshot"
    _write_json(
        input_root / "tables" / "cluster_source.json",
        [
            {"event_id": "e01", "f1": 1.0, "f2": 2.0, "f2_ci_low": 1.8, "f2_ci_high": 2.2, "sample_id": "s01"},
            {"event_id": "e02", "f1": 2.0, "f2": 3.0, "f2_ci_low": 2.8, "f2_ci_high": 3.2, "sample_id": "s02"},
            {"event_id": "e03", "f1": 3.0, "f2": 4.0, "f2_ci_low": 3.8, "f2_ci_high": 4.2, "sample_id": "s03"},
        ],
    )
    _write_json(
        input_root / "tables" / "weaker_source.json",
        [
            {"pipeline_event_id": "p01", "g1": 1.0, "label": "A"},
            {"pipeline_event_id": "p02", "g1": 2.0, "label": "B"},
        ],
    )
    return repo_root


def _write_exp001(
    repo_root: Path,
    run_id: str,
    *,
    status: str = "PASS",
    field_inventory: list[dict[str, object]] | None = None,
) -> None:
    root = repo_root / "runs" / run_id / "experiment" / "exp001_feature_inventory"
    _write_json(root / "stage_summary.json", {"stage": "exp001_feature_inventory", "status": status})
    _write_json(root / "outputs" / "schema_profile.json", {"schema_hash": "abc"})
    _write_json(root / "outputs" / "field_inventory.json", field_inventory or _default_field_inventory())


def _default_field_inventory() -> list[dict[str, object]]:
    return [
        {
            "field_name": "event_id",
            "source_file": "cluster_source.json",
            "source_relpath": "tables/cluster_source.json",
            "dtype_observed": "string",
            "nonnull_count": 3,
            "null_count": 0,
            "coverage_fraction": 1.0,
            "n_unique": 3,
            "all_null": False,
            "constant": False,
            "candidate_role": "identifier",
            "usability_class": "usable",
        },
        {
            "field_name": "sample_id",
            "source_file": "cluster_source.json",
            "source_relpath": "tables/cluster_source.json",
            "dtype_observed": "string",
            "nonnull_count": 3,
            "null_count": 0,
            "coverage_fraction": 1.0,
            "n_unique": 3,
            "all_null": False,
            "constant": False,
            "candidate_role": "identifier",
            "usability_class": "usable",
        },
        {
            "field_name": "f1",
            "source_file": "cluster_source.json",
            "source_relpath": "tables/cluster_source.json",
            "dtype_observed": "number",
            "nonnull_count": 3,
            "null_count": 0,
            "coverage_fraction": 1.0,
            "n_unique": 3,
            "all_null": False,
            "constant": False,
            "candidate_role": "numeric_feature",
            "usability_class": "usable",
        },
        {
            "field_name": "f2",
            "source_file": "cluster_source.json",
            "source_relpath": "tables/cluster_source.json",
            "dtype_observed": "number",
            "nonnull_count": 3,
            "null_count": 0,
            "coverage_fraction": 1.0,
            "n_unique": 3,
            "all_null": False,
            "constant": False,
            "candidate_role": "numeric_feature",
            "usability_class": "usable",
        },
        {
            "field_name": "f2_ci_low",
            "source_file": "cluster_source.json",
            "source_relpath": "tables/cluster_source.json",
            "dtype_observed": "number",
            "nonnull_count": 3,
            "null_count": 0,
            "coverage_fraction": 1.0,
            "n_unique": 3,
            "all_null": False,
            "constant": False,
            "candidate_role": "numeric_feature",
            "usability_class": "usable",
        },
        {
            "field_name": "f2_ci_high",
            "source_file": "cluster_source.json",
            "source_relpath": "tables/cluster_source.json",
            "dtype_observed": "number",
            "nonnull_count": 3,
            "null_count": 0,
            "coverage_fraction": 1.0,
            "n_unique": 3,
            "all_null": False,
            "constant": False,
            "candidate_role": "numeric_feature",
            "usability_class": "usable",
        },
        {
            "field_name": "drop_me",
            "source_file": "cluster_source.json",
            "source_relpath": "tables/cluster_source.json",
            "dtype_observed": "null",
            "nonnull_count": 0,
            "null_count": 3,
            "coverage_fraction": 0.0,
            "n_unique": 0,
            "all_null": True,
            "constant": False,
            "candidate_role": "unknown",
            "usability_class": "unusable",
        },
        {
            "field_name": "constant_feature",
            "source_file": "cluster_source.json",
            "source_relpath": "tables/cluster_source.json",
            "dtype_observed": "number",
            "nonnull_count": 3,
            "null_count": 0,
            "coverage_fraction": 1.0,
            "n_unique": 1,
            "all_null": False,
            "constant": True,
            "candidate_role": "numeric_feature",
            "usability_class": "unusable",
        },
        {
            "field_name": "pipeline_event_id",
            "source_file": "weaker_source.json",
            "source_relpath": "tables/weaker_source.json",
            "dtype_observed": "string",
            "nonnull_count": 2,
            "null_count": 0,
            "coverage_fraction": 1.0,
            "n_unique": 2,
            "all_null": False,
            "constant": False,
            "candidate_role": "identifier",
            "usability_class": "usable",
        },
        {
            "field_name": "g1",
            "source_file": "weaker_source.json",
            "source_relpath": "tables/weaker_source.json",
            "dtype_observed": "number",
            "nonnull_count": 2,
            "null_count": 0,
            "coverage_fraction": 1.0,
            "n_unique": 2,
            "all_null": False,
            "constant": False,
            "candidate_role": "numeric_feature",
            "usability_class": "usable",
        },
        {
            "field_name": "label",
            "source_file": "weaker_source.json",
            "source_relpath": "tables/weaker_source.json",
            "dtype_observed": "string",
            "nonnull_count": 2,
            "null_count": 0,
            "coverage_fraction": 1.0,
            "n_unique": 2,
            "all_null": False,
            "constant": False,
            "candidate_role": "target",
            "usability_class": "usable",
        },
    ]


def _stage_root(repo_root: Path, run_id: str) -> Path:
    return repo_root / "runs" / run_id / "experiment" / STAGE_NAME


def _read_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_fail_if_upstream_exp001_missing(tmp_path: Path) -> None:
    repo_root = _make_repo(tmp_path)
    with pytest.raises(ExecutiveContractError):
        run_pattern_scan_global_simple(run_id="exp002", exp001_run="missing", repo_root=repo_root)


def test_fail_if_exp001_stage_summary_missing(tmp_path: Path) -> None:
    repo_root = _make_repo(tmp_path)
    root = repo_root / "runs" / "exp001" / "experiment" / "exp001_feature_inventory"
    _write_json(root / "outputs" / "schema_profile.json", {"schema_hash": "abc"})
    _write_json(root / "outputs" / "field_inventory.json", [])
    with pytest.raises(ExecutiveContractError):
        run_pattern_scan_global_simple(run_id="exp002", exp001_run="exp001", repo_root=repo_root)


def test_fail_if_exp001_status_not_pass(tmp_path: Path) -> None:
    repo_root = _make_repo(tmp_path)
    _write_exp001(repo_root, "exp001", status="FAIL")
    with pytest.raises(ExecutiveContractError):
        run_pattern_scan_global_simple(run_id="exp002", exp001_run="exp001", repo_root=repo_root)


def test_no_writes_outside_run_root(tmp_path: Path) -> None:
    repo_root = _make_repo(tmp_path)
    _write_exp001(repo_root, "exp001")
    run_pattern_scan_global_simple(run_id="exp002", exp001_run="exp001", repo_root=repo_root)
    generated = sorted(path for path in repo_root.rglob("*") if path.is_file())
    expected_prefix = (repo_root / "runs" / "exp002").resolve()
    for path in generated:
        if path.resolve().is_relative_to((repo_root / "data").resolve()):
            continue
        if path.resolve().is_relative_to((repo_root / "runs" / "exp001").resolve()):
            continue
        assert path.resolve().is_relative_to(expected_prefix)


def test_no_run_created_on_precheck_failure(tmp_path: Path) -> None:
    repo_root = _make_repo(tmp_path)
    with pytest.raises(ExecutiveContractError):
        run_pattern_scan_global_simple(run_id="exp002", exp001_run="missing", repo_root=repo_root)
    assert not (repo_root / "runs" / "exp002").exists()


def test_pass_always_emits_manifest_json(tmp_path: Path) -> None:
    repo_root = _make_repo(tmp_path)
    _write_exp001(repo_root, "exp001")
    run_pattern_scan_global_simple(run_id="exp002", exp001_run="exp001", repo_root=repo_root)
    assert (_stage_root(repo_root, "exp002") / "manifest.json").is_file()


def test_pass_always_emits_stage_summary_json(tmp_path: Path) -> None:
    repo_root = _make_repo(tmp_path)
    _write_exp001(repo_root, "exp001")
    run_pattern_scan_global_simple(run_id="exp002", exp001_run="exp001", repo_root=repo_root)
    assert (_stage_root(repo_root, "exp002") / "stage_summary.json").is_file()


def test_pass_always_emits_pattern_scan_summary_json(tmp_path: Path) -> None:
    repo_root = _make_repo(tmp_path)
    _write_exp001(repo_root, "exp001")
    run_pattern_scan_global_simple(run_id="exp002", exp001_run="exp001", repo_root=repo_root)
    assert (_stage_root(repo_root, "exp002") / "outputs" / "pattern_scan_summary.json").is_file()


def test_pattern_scan_summary_contains_schema_version(tmp_path: Path) -> None:
    repo_root = _make_repo(tmp_path)
    _write_exp001(repo_root, "exp001")
    run_pattern_scan_global_simple(run_id="exp002", exp001_run="exp001", repo_root=repo_root)
    payload = _read_json(_stage_root(repo_root, "exp002") / "outputs" / "pattern_scan_summary.json")
    assert payload["schema_version"] == SCHEMA_VERSION


def test_recommended_source_relpath_exists_in_snapshot(tmp_path: Path) -> None:
    repo_root = _make_repo(tmp_path)
    _write_exp001(repo_root, "exp001")
    run_pattern_scan_global_simple(run_id="exp002", exp001_run="exp001", repo_root=repo_root)
    payload = _read_json(_stage_root(repo_root, "exp002") / "outputs" / "pattern_scan_summary.json")
    assert (repo_root / "data" / "raw" / "ringhier_snapshot" / payload["recommended_source_relpath"]).is_file()


def test_candidate_feature_fields_non_empty_on_pass(tmp_path: Path) -> None:
    repo_root = _make_repo(tmp_path)
    _write_exp001(repo_root, "exp001")
    run_pattern_scan_global_simple(run_id="exp002", exp001_run="exp001", repo_root=repo_root)
    payload = _read_json(_stage_root(repo_root, "exp002") / "outputs" / "pattern_scan_summary.json")
    assert payload["candidate_feature_fields"]


def test_candidate_feature_fields_exclude_identifiers_and_unusable_fields(tmp_path: Path) -> None:
    repo_root = _make_repo(tmp_path)
    _write_exp001(repo_root, "exp001")
    run_pattern_scan_global_simple(run_id="exp002", exp001_run="exp001", repo_root=repo_root)
    payload = _read_json(_stage_root(repo_root, "exp002") / "outputs" / "pattern_scan_summary.json")
    assert payload["candidate_feature_fields"] == ["f1", "f2"]
    assert "event_id" not in payload["candidate_feature_fields"]
    assert "sample_id" not in payload["candidate_feature_fields"]
    assert "drop_me" not in payload["candidate_feature_fields"]
    assert "constant_feature" not in payload["candidate_feature_fields"]


def test_row_id_field_candidates_are_stable_and_auditable(tmp_path: Path) -> None:
    repo_root = _make_repo(tmp_path)
    _write_exp001(repo_root, "exp001")
    run_pattern_scan_global_simple(run_id="exp002", exp001_run="exp001", repo_root=repo_root)
    payload = _read_json(_stage_root(repo_root, "exp002") / "outputs" / "pattern_scan_summary.json")
    assert payload["row_id_field_candidates"] == ["event_id", "sample_id"]
    assert payload["recommended_row_id_field"] == "event_id"


def test_same_input_same_output(tmp_path: Path) -> None:
    repo_root = _make_repo(tmp_path)
    _write_exp001(repo_root, "exp001")
    run_pattern_scan_global_simple(run_id="exp002_a", exp001_run="exp001", repo_root=repo_root)
    run_pattern_scan_global_simple(run_id="exp002_b", exp001_run="exp001", repo_root=repo_root)
    a = (_stage_root(repo_root, "exp002_a") / "outputs" / "pattern_scan_summary.json").read_text(encoding="utf-8")
    b = (_stage_root(repo_root, "exp002_b") / "outputs" / "pattern_scan_summary.json").read_text(encoding="utf-8")
    assert a == b


def test_no_extra_artifacts_generated(tmp_path: Path) -> None:
    repo_root = _make_repo(tmp_path)
    _write_exp001(repo_root, "exp001")
    run_pattern_scan_global_simple(run_id="exp002", exp001_run="exp001", repo_root=repo_root)
    stage_root = _stage_root(repo_root, "exp002")
    actual = sorted(str(path.relative_to(stage_root)) for path in stage_root.rglob("*") if path.is_file())
    assert actual == [
        "manifest.json",
        "outputs/pattern_scan_summary.json",
        "stage_summary.json",
    ]


def test_fail_stage_summary_uses_pattern_scan_failed_verdict(tmp_path: Path) -> None:
    repo_root = _make_repo(tmp_path)
    only_one_feature_inventory = [row for row in _default_field_inventory() if row["field_name"] not in {"f2", "f2_ci_low", "f2_ci_high"}]
    _write_exp001(repo_root, "exp001", field_inventory=only_one_feature_inventory)
    with pytest.raises(ExecutiveContractError):
        run_pattern_scan_global_simple(run_id="exp002", exp001_run="exp001", repo_root=repo_root)
    stage_summary = _read_json(_stage_root(repo_root, "exp002") / "stage_summary.json")
    assert stage_summary["status"] == "FAIL"
    assert stage_summary["primary_verdict"] == "PATTERN_SCAN_FAILED"


def test_pass_stage_summary_uses_pattern_scan_ready_verdict(tmp_path: Path) -> None:
    repo_root = _make_repo(tmp_path)
    _write_exp001(repo_root, "exp001")
    run_pattern_scan_global_simple(run_id="exp002", exp001_run="exp001", repo_root=repo_root)
    stage_summary = _read_json(_stage_root(repo_root, "exp002") / "stage_summary.json")
    assert stage_summary["status"] == "PASS"
    assert stage_summary["primary_verdict"] == "PATTERN_SCAN_READY"
