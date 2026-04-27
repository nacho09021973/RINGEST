from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import h5py
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from contracts.common_models import (
    ContractValidationError,
    ManifestArtifactModel,
    ManifestModel,
    StageRuntimeManifestModel,
    StageSummaryModel,
    load_manifest,
    load_stage_runtime_manifest,
    load_stage_summary,
    write_manifest,
    write_stage_runtime_manifest,
    write_stage_summary,
)


def _load_module(module_name: str, relative_path: str):
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, REPO_ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class TestCommonContractModels(unittest.TestCase):
    def test_manifest_model_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            model = ManifestModel(
                created_at="2026-04-11T12:00:00Z",
                stage="08_theory_dictionary_contrast",
                script="08_theory_dictionary_contrast.py v1.0",
                input_root="/tmp/input",
                inputs={
                    "stage03": ManifestArtifactModel(
                        path="/tmp/input/03/einstein_discovery_summary.json",
                        sha256="a" * 64,
                    )
                },
                outputs={
                    "stage_summary_json": ManifestArtifactModel(
                        path="/tmp/output/stage_summary.json",
                        sha256="b" * 64,
                    )
                },
                notes=["contract test"],
            )

            write_manifest(model, path)
            loaded = load_manifest(path)

            self.assertEqual(loaded.model_dump(mode="json"), model.model_dump(mode="json"))

    def test_stage_summary_model_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "stage_summary.json"
            model = StageSummaryModel(
                created_at="2026-04-11T12:00:00Z",
                stage_name="08_theory_dictionary_contrast",
                script="08_theory_dictionary_contrast.py v1.0",
                status="OK",
                exit_code=0,
                input_root="/tmp/input",
                output_dir="/tmp/output",
                n_theories=5,
                n_evaluable=3,
                n_not_evaluable=2,
                verdict_counts={"supported": 1, "not_evaluable": 2},
                post_hoc_only=True,
                upstream_training_contamination="forbidden_by_design",
            )

            write_stage_summary(model, path)
            loaded = load_stage_summary(path)

            self.assertEqual(loaded.model_dump(mode="json"), model.model_dump(mode="json"))

    def test_stage_runtime_manifest_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            model = StageRuntimeManifestModel(
                created_at="2026-04-11T12:00:00+00:00",
                experiment="contract_exp",
                stage="06_build_bulk_eigenmodes_dataset",
                stage_dir="/tmp/runs/contract_exp/06_build_bulk_eigenmodes_dataset",
                run_root="/tmp/runs/contract_exp",
                artifacts={"bulk_modes_csv": "/tmp/runs/contract_exp/06/bulk_modes_dataset.csv"},
            )

            write_stage_runtime_manifest(model, path)
            loaded = load_stage_runtime_manifest(path)

            self.assertEqual(loaded.model_dump(mode="json"), model.model_dump(mode="json"))

    def test_invalid_manifest_fails_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            _write_json(
                path,
                {
                    "created_at": "2026-04-11T12:00:00Z",
                    "stage": "08_theory_dictionary_contrast",
                    "inputs": {},
                    "outputs": {},
                },
            )

            with self.assertRaises(ContractValidationError):
                load_manifest(path)

    def test_invalid_stage_summary_fails_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "stage_summary.json"
            _write_json(
                path,
                {
                    "created_at": "2026-04-11T12:00:00Z",
                    "status": "OK",
                },
            )

            with self.assertRaises(ContractValidationError):
                load_stage_summary(path)

    def _skip_test_stage08_writes_valid_manifest_and_stage_summary(self):
        # 08_theory_dictionary_contrast.py archived  test disabled
        stage08 = _load_module("stage08_contract_test", "08_theory_dictionary_contrast.py")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_root = root / "runs" / "reopen_v1"
            output_dir = root / "runs" / "reopen_v1" / "08_theory_dictionary_contrast"

            _write_json(
                input_root / "03_discover_bulk_equations" / "einstein_discovery_summary.json",
                {
                    "geometries": [
                        {
                            "validation": {
                                "verdict": "POSSIBLY_EINSTEIN_WITH_MATTER",
                                "einstein_score": 0.55,
                                "R_constant": True,
                                "R_negative": True,
                                "einstein_vacuum_compatible": False,
                            }
                        }
                    ]
                },
            )
            _write_json(
                input_root / "04_geometry_physics_contracts" / "geometry_contracts_summary.json",
                {
                    "contracts": [
                        {
                            "category": "ringdown",
                            "mode": "inference",
                            "correlator_structure": {
                                "contract_mode": "ringdown_inference_relaxed_v1"
                            },
                            "ads_einstein": {"R_is_constant": True},
                            "ads_asymptotic": {"A_logarithmic_uv": False},
                            "holographic": {
                                "mass_dimension_ok": True,
                                "conformal_symmetry_ok": True,
                            },
                        }
                    ]
                },
            )
            _write_json(
                input_root / "05_analyze_bulk_equations" / "bulk_equations_analysis.json",
                {
                    "by_family": {
                        "test_family": [
                            {
                                "structure": {
                                    "complexity": 2.0,
                                    "has_d2A": True,
                                    "has_cross_terms": False,
                                }
                            }
                        ]
                    },
                    "patterns": {
                        "universal_terms": ["has_d2A"],
                        "family_specific_terms": {"test_family": ["term_x"]},
                    },
                },
            )
            _write_json(
                input_root / "06_build_bulk_eigenmodes_dataset" / "bulk_modes_dataset.json",
                {
                    "systems": [
                        {
                            "n_modes": 2,
                            "family": "test_family",
                            "lambda_source": "solver",
                        }
                    ]
                },
            )
            _write_json(
                input_root / "07b_discover_lambda_delta_relation" / "lambda_delta_discovery_report.json",
                {
                    "preliminary_analysis": {
                        "d_values": [4],
                        "lambda_sl_range": [1.0, 2.0],
                        "Delta_range": [3.0, 4.0],
                    },
                    "pairs": [
                        {"Delta": 3.0, "lambda_sl": 1.0},
                        {"Delta": 4.0, "lambda_sl": 2.0},
                    ],
                    "pysr_results": {"best_equation": "lambda_sl + 1"},
                },
            )

            argv = [
                "08_theory_dictionary_contrast.py",
                "--input-root",
                str(input_root),
                "--output-dir",
                str(output_dir),
                "--dictionary-config",
                str(REPO_ROOT / "configs" / "theory_dictionary" / "theory_dictionary_v1.json"),
            ]
            with patch.object(sys, "argv", argv):
                exit_code = stage08.main()

            self.assertEqual(exit_code, 0)

            manifest = load_manifest(output_dir / "manifest.json")
            stage_summary = load_stage_summary(output_dir / "stage_summary.json")

            self.assertEqual(manifest.stage, "08_theory_dictionary_contrast")
            self.assertEqual(stage_summary.stage_name, "08_theory_dictionary_contrast")
            self.assertEqual(stage_summary.exit_code, 0)

    def test_stage06_writes_valid_stage_summary(self):
        stage06 = _load_module("stage06_contract_test", "06_build_bulk_eigenmodes_dataset.py")
        stage06.bss = types.SimpleNamespace(
            __name__="stub_bulk_scalar_solver",
            solve_geometry=lambda **_: {
                "lambda_sl": [1.0, 2.0],
                "uv_exponents": [3.0, 4.0],
            },
        )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runs_dir = root / "runs"
            geom_dir = (
                runs_dir
                / "contract_exp"
                / "02_emergent_geometry_engine"
                / "geometry_emergent"
            )
            geom_dir.mkdir(parents=True, exist_ok=True)

            h5_path = geom_dir / "synthetic_geometry.h5"
            with h5py.File(h5_path, "w") as h5f:
                h5f.attrs["system_name"] = "synthetic_geometry"
                h5f.attrs["family"] = "test_family"
                h5f.attrs["d"] = 4
                h5f.attrs["z_dyn"] = 1.0
                h5f.attrs["theta"] = 0.0
                h5f.create_dataset("z_grid", data=np.array([0.0, 0.5, 1.0]))
                h5f.create_dataset("A_emergent", data=np.array([0.0, 0.1, 0.2]))
                h5f.create_dataset("f_emergent", data=np.array([1.0, 0.9, 0.8]))

            argv = [
                "06_build_bulk_eigenmodes_dataset.py",
                "--runs-dir",
                str(runs_dir),
                "--experiment",
                "contract_exp",
                "--n-eigs",
                "2",
            ]
            with patch.object(sys, "argv", argv):
                exit_code = stage06.main()

            self.assertEqual(exit_code, 0)

            summary = load_stage_summary(
                runs_dir
                / "contract_exp"
                / "06_build_bulk_eigenmodes_dataset"
                / "stage_summary.json"
            )
            manifest = load_stage_runtime_manifest(
                runs_dir
                / "contract_exp"
                / "06_build_bulk_eigenmodes_dataset"
                / "manifest.json"
            )
            self.assertEqual(summary.stage, "06_build_bulk_eigenmodes_dataset")
            self.assertEqual(summary.status, "OK")
            self.assertEqual(summary.exit_code, 0)
            self.assertEqual(manifest.stage, "06_build_bulk_eigenmodes_dataset")
            self.assertEqual(manifest.experiment, "contract_exp")


if __name__ == "__main__":
    unittest.main()
