from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_stage04():
    sys.modules.pop("stage_utils", None)
    stage_utils_stub = types.ModuleType("stage_utils")
    stage_utils_stub.Path = Path
    stage_utils_stub.StageContext = object
    stage_utils_stub.add_standard_arguments = lambda parser: None
    stage_utils_stub.parse_stage_args = lambda parser: parser.parse_args([])
    stage_utils_stub.EXIT_OK = 0
    stage_utils_stub.EXIT_ERROR = 3
    stage_utils_stub.STATUS_OK = "OK"
    stage_utils_stub.STATUS_ERROR = "ERROR"
    sys.modules["stage_utils"] = stage_utils_stub

    key = "stage04_contract_runtime_test"
    sys.modules.pop(key, None)
    spec = importlib.util.spec_from_file_location(key, REPO_ROOT / "04_geometry_physics_contracts.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


class _FakeCtx:
    def __init__(self, run_root: Path, stage_dir: Path, experiment: str = "exp1"):
        self.run_root = run_root
        self.stage_dir = stage_dir
        self.experiment = experiment
        self.artifacts = {}

    def record_artifact(self, key, path=None):
        if path is None:
            p = Path(key)
            self.artifacts[p.name] = str(p)
        else:
            self.artifacts[str(key)] = str(path)

    def write_manifest(self, outputs=None, metadata=None):
        payload = {
            "experiment": self.experiment,
            "run_root": str(self.run_root),
            "stage_dir": str(self.stage_dir),
            "outputs": outputs or {},
            "metadata": metadata or {},
            "artifacts": self.artifacts,
        }
        path = self.stage_dir / "manifest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def write_summary(self, status, exit_code=0, error_message=None, counts=None):
        payload = {
            "status": status,
            "exit_code": exit_code,
            "error_message": error_message,
            "counts": counts or {},
        }
        path = self.stage_dir / "stage_summary.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class Stage04ContractRuntimeTests(unittest.TestCase):
    def test_missing_manifest_in_data_dir_aborts_without_autodiscovery(self):
        s04 = _load_stage04()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"
            data_dir.mkdir()
            predictions_dir = root / "predictions"
            predictions_dir.mkdir()
            (predictions_dir / "geo_a_geometry.npz").write_text("placeholder", encoding="utf-8")

            with self.assertRaisesRegex(FileNotFoundError, "Missing canonical manifest"):
                s04.load_geometries_from_data_dir(data_dir)

    def test_ctx_default_output_goes_to_stage_outputs_dir(self):
        s04 = _load_stage04()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _FakeCtx(root / "runs" / "exp1", root / "runs" / "exp1" / "04_geometry_physics_contracts")
            args = argparse.Namespace(output_file=None)

            output = s04.resolve_output_file(args, ctx, ctx.run_root)

            self.assertEqual(
                output,
                ctx.stage_dir / "outputs" / "geometry_contracts_summary.json",
            )

    def test_main_with_ctx_writes_manifest_and_stage_summary(self):
        s04 = _load_stage04()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_root = root / "runs" / "exp1"
            stage_dir = run_root / "04_geometry_physics_contracts"
            data_dir = run_root / "data_boundary"
            data_dir.mkdir(parents=True, exist_ok=True)
            (data_dir / "manifest.json").write_text(
                json.dumps({"geometries": [{"name": "geo_a"}]}, indent=2) + "\n",
                encoding="utf-8",
            )
            geometry_dir = run_root / "02_emergent_geometry_engine"
            geometry_dir.mkdir(parents=True, exist_ok=True)
            (geometry_dir / "geo_a_geometry.npz").write_text("placeholder", encoding="utf-8")
            (geometry_dir / "geo_a_emergent.h5").write_text("placeholder", encoding="utf-8")
            einstein_dir = run_root / "03_discover_bulk_equations"
            einstein_dir.mkdir(parents=True, exist_ok=True)

            fake_ctx = _FakeCtx(run_root, stage_dir)
            args = argparse.Namespace(
                data_dir=str(data_dir),
                geometry_dir=str(geometry_dir),
                einstein_dir=str(einstein_dir),
                dictionary_file=None,
                run_dir=str(run_root),
                output_file=None,
                d=4,
                experiment="exp1",
                runs_dir=str(root / "runs"),
            )

            contract = s04.PhaseXIContractV2(
                name="geo_a",
                family="ads",
                category="ringdown",
                d=4,
                regularity=s04.GenericRegularityContract(True, True, True, True),
                causality=s04.GenericCausalityContract(True, True, True, skipped=False),
                unitarity=s04.BoundaryUnitarityContract(True, 1, 0, 3.0, 1.0, [], skipped=False),
                correlator_structure=s04.CorrelatorStructureContract(
                    True, True, True, -2.0, 0.9, skipped=False
                ),
                ads_einstein=s04.AdSEinsteinContract(True, True, True, -12.0, -12.0),
                ads_asymptotic=s04.AdSAsymptoticContract(True, True, True),
                holographic=s04.HolographicDictionaryContract(True, False, True),
                A_r2=0.9,
                f_r2=0.9,
                R_r2=0.9,
                family_accuracy=1.0,
                mode="inference",
                errors=[],
                warnings=[],
            )

            with mock.patch.object(s04, "HAS_STAGE_UTILS", True), \
                 mock.patch.object(s04, "add_standard_arguments", lambda parser: None), \
                 mock.patch.object(s04, "parse_stage_args", return_value=args), \
                 mock.patch.object(s04, "StageContext") as mock_stage_context, \
                 mock.patch.object(s04, "process_geometry", return_value=contract):
                mock_stage_context.from_args.return_value = fake_ctx
                exit_code = s04.main()

            self.assertEqual(exit_code, s04.EXIT_OK)
            self.assertTrue((stage_dir / "manifest.json").exists())
            self.assertTrue((stage_dir / "stage_summary.json").exists())
            self.assertTrue((stage_dir / "outputs" / "geometry_contracts_summary.json").exists())


if __name__ == "__main__":
    unittest.main()
