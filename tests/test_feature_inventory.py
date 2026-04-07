from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from ringest.feature_inventory import ExecutiveContractError, InventoryError, run_feature_inventory

STAGE_DIRNAME = "exp001_feature_inventory"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _make_repo(
    tmp_path: Path,
    *,
    with_input: bool = True,
    with_import_manifest: bool = True,
    unsupported: bool = False,
) -> tuple[Path, Path]:
    repo_root = tmp_path / "repo"
    input_root = repo_root / "data" / "raw" / "ringhier_snapshot"
    if with_input:
        input_root.mkdir(parents=True, exist_ok=True)
        _write_json(
            input_root / "tables" / "events.json",
            [
                {"event_id": "A", "full_value": 1.0, "const_field": "same", "all_null": None, "partial_field": "x"},
                {"event_id": "B", "full_value": 2.0, "const_field": "same", "all_null": None, "partial_field": None},
                {"event_id": "C", "full_value": 3.0, "const_field": "same", "all_null": None, "partial_field": None},
                {"event_id": "D", "full_value": 4.0, "const_field": "same", "all_null": None, "partial_field": "y"},
                {"event_id": "E", "full_value": 5.0, "const_field": "same", "all_null": None, "partial_field": None},
            ],
        )
        _write_json(
            input_root / "tables" / "residual_feature_table.json",
            {
                "artifact_name": "residual_feature_table",
                "rows": [
                    {"row_id": "r1", "score": 10.0, "class_label": "alpha"},
                    {"row_id": "r2", "score": 11.0, "class_label": "beta"},
                ],
            },
        )
        _write_json(
            input_root / "catalogs" / "catalog.json",
            {
                "GW150914": {"Mf_source": 61.5, "source": "catalog"},
                "GW170104": {"Mf_source": 47.5, "source": "catalog"},
            },
        )
        _write_json(input_root / "verdicts" / "verdict.json", {"primary_verdict": "OK", "n_events": 5})
        if unsupported:
            _write_json(input_root / "bad" / "unsupported.json", [1, 2, 3])

    if with_import_manifest:
        _write_json(
            repo_root / "data" / "manifests" / "import_from_ringhier.json",
            {
                "manifest_name": "import_from_ringhier",
                "created_at_utc": "2026-04-07T00:00:00+00:00",
                "raw_snapshot_root": str(input_root),
                "entries": [
                    {
                        "destination_path": str(input_root / "tables" / "events.json"),
                        "sha256": "abc123",
                    }
                ],
            },
        )

    return repo_root, input_root


def _stage_root(repo_root: Path, run_id: str) -> Path:
    return repo_root / "runs" / run_id / "experiment" / STAGE_DIRNAME


def _load_pass_outputs(repo_root: Path, run_id: str) -> tuple[dict, list[dict], dict, dict]:
    stage_root = _stage_root(repo_root, run_id)
    with (stage_root / "manifest.json").open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    with (stage_root / "outputs" / "field_inventory.json").open("r", encoding="utf-8") as handle:
        field_inventory = json.load(handle)
    with (stage_root / "outputs" / "schema_profile.json").open("r", encoding="utf-8") as handle:
        schema_profile = json.load(handle)
    with (stage_root / "stage_summary.json").open("r", encoding="utf-8") as handle:
        stage_summary = json.load(handle)
    return manifest, field_inventory, schema_profile, stage_summary


def test_fail_if_input_root_missing(tmp_path: Path) -> None:
    repo_root, input_root = _make_repo(tmp_path, with_input=False)
    with pytest.raises(ExecutiveContractError):
        run_feature_inventory(input_root=input_root, run_id="missing-input", repo_root=repo_root)
    assert not (repo_root / "runs" / "missing-input").exists()


def test_fail_if_import_manifest_missing(tmp_path: Path) -> None:
    repo_root, input_root = _make_repo(tmp_path, with_import_manifest=False)
    with pytest.raises(ExecutiveContractError):
        run_feature_inventory(input_root=input_root, run_id="missing-manifest", repo_root=repo_root)
    assert not (repo_root / "runs" / "missing-manifest").exists()


def test_no_writes_outside_run_root(tmp_path: Path) -> None:
    repo_root, input_root = _make_repo(tmp_path)
    run_id = "write-scope"
    run_feature_inventory(input_root=input_root, run_id=run_id, repo_root=repo_root)
    generated = sorted(path for path in repo_root.rglob("*") if path.is_file())
    expected_prefix = (repo_root / "runs" / run_id).resolve()
    for path in generated:
        if path.is_relative_to((repo_root / "data").resolve()):
            continue
        assert path.resolve().is_relative_to(expected_prefix)


def test_rejects_existing_run_id_without_overwrite(tmp_path: Path) -> None:
    repo_root, input_root = _make_repo(tmp_path)
    run_id = "already-there"
    run_feature_inventory(input_root=input_root, run_id=run_id, repo_root=repo_root)
    with pytest.raises(ExecutiveContractError):
        run_feature_inventory(input_root=input_root, run_id=run_id, repo_root=repo_root)


def test_all_null_field_is_unusable(tmp_path: Path) -> None:
    repo_root, input_root = _make_repo(tmp_path)
    run_id = "all-null"
    run_feature_inventory(input_root=input_root, run_id=run_id, repo_root=repo_root)
    _, field_inventory, _, _ = _load_pass_outputs(repo_root, run_id)
    row = next(item for item in field_inventory if item["source_relpath"] == "tables/events.json" and item["field_name"] == "all_null")
    assert row["all_null"] is True
    assert row["usability_class"] == "unusable"


def test_constant_field_is_unusable(tmp_path: Path) -> None:
    repo_root, input_root = _make_repo(tmp_path)
    run_id = "constant"
    run_feature_inventory(input_root=input_root, run_id=run_id, repo_root=repo_root)
    _, field_inventory, _, _ = _load_pass_outputs(repo_root, run_id)
    row = next(item for item in field_inventory if item["source_relpath"] == "tables/events.json" and item["field_name"] == "const_field")
    assert row["constant"] is True
    assert row["usability_class"] == "unusable"


def test_full_coverage_nonconstant_field_is_usable(tmp_path: Path) -> None:
    repo_root, input_root = _make_repo(tmp_path)
    run_id = "usable"
    run_feature_inventory(input_root=input_root, run_id=run_id, repo_root=repo_root)
    _, field_inventory, _, _ = _load_pass_outputs(repo_root, run_id)
    row = next(item for item in field_inventory if item["source_relpath"] == "tables/events.json" and item["field_name"] == "full_value")
    assert row["coverage_fraction"] == 1.0
    assert row["constant"] is False
    assert row["usability_class"] == "usable"


def test_same_input_same_schema_hash(tmp_path: Path) -> None:
    repo_root, input_root = _make_repo(tmp_path)
    run_feature_inventory(input_root=input_root, run_id="hash-a", repo_root=repo_root)
    run_feature_inventory(input_root=input_root, run_id="hash-b", repo_root=repo_root)
    _, _, schema_profile_a, _ = _load_pass_outputs(repo_root, "hash-a")
    _, _, schema_profile_b, _ = _load_pass_outputs(repo_root, "hash-b")
    assert schema_profile_a["schema_hash"] == schema_profile_b["schema_hash"]


def test_field_inventory_and_coverage_csv_are_coherent(tmp_path: Path) -> None:
    repo_root, input_root = _make_repo(tmp_path)
    run_id = "coherent"
    run_feature_inventory(input_root=input_root, run_id=run_id, repo_root=repo_root)
    stage_root = _stage_root(repo_root, run_id)
    with (stage_root / "outputs" / "field_inventory.json").open("r", encoding="utf-8") as handle:
        inventory = json.load(handle)
    with (stage_root / "outputs" / "coverage_by_field.csv").open("r", encoding="utf-8", newline="") as handle:
        coverage_rows = list(csv.DictReader(handle))

    inventory_index = {
        (item["source_relpath"], item["field_name"]): (
            str(item["nonnull_count"]),
            str(item["null_count"]),
            f'{item["coverage_fraction"]:.6f}',
            item["usability_class"],
        )
        for item in inventory
    }
    coverage_index = {
        (item["source_relpath"], item["field_name"]): (
            item["nonnull_count"],
            item["null_count"],
            item["coverage_fraction"],
            item["usability_class"],
        )
        for item in coverage_rows
    }
    assert inventory_index == coverage_index


def test_pass_always_emits_manifest_and_stage_summary(tmp_path: Path) -> None:
    repo_root, input_root = _make_repo(tmp_path)
    run_id = "pass-files"
    run_feature_inventory(input_root=input_root, run_id=run_id, repo_root=repo_root)
    stage_root = _stage_root(repo_root, run_id)
    assert (stage_root / "manifest.json").is_file()
    assert (stage_root / "stage_summary.json").is_file()


def test_fail_status_sets_inventory_failed_primary_verdict(tmp_path: Path) -> None:
    repo_root, input_root = _make_repo(tmp_path, unsupported=True)
    run_id = "fail-verdict"
    with pytest.raises(InventoryError):
        run_feature_inventory(input_root=input_root, run_id=run_id, repo_root=repo_root)
    assert not (repo_root / "runs" / run_id).exists()


def test_pass_status_sets_snapshot_profiled_primary_verdict(tmp_path: Path) -> None:
    repo_root, input_root = _make_repo(tmp_path)
    run_id = "pass-verdict"
    run_feature_inventory(input_root=input_root, run_id=run_id, repo_root=repo_root)
    _, _, _, stage_summary = _load_pass_outputs(repo_root, run_id)
    assert stage_summary["status"] == "PASS"
    assert stage_summary["primary_verdict"] == "SNAPSHOT_PROFILED"


def test_no_undeclared_artifacts_are_generated_outside_experiment_folder(tmp_path: Path) -> None:
    repo_root, input_root = _make_repo(tmp_path)
    run_id = "declared-only"
    run_feature_inventory(input_root=input_root, run_id=run_id, repo_root=repo_root)
    stage_root = _stage_root(repo_root, run_id)
    actual = sorted(str(path.relative_to(stage_root)) for path in stage_root.rglob("*") if path.is_file())
    assert actual == sorted(
        [
            "manifest.json",
            "stage_summary.json",
            "outputs/coverage_by_field.csv",
            "outputs/field_inventory.json",
            "outputs/schema_profile.json",
        ]
    )
