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

import h5py


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_stage08():
    sys.modules.pop("stage_utils", None)
    stage_utils_stub = types.ModuleType("stage_utils")
    stage_utils_stub.Path = Path
    stage_utils_stub.StageContext = object
    stage_utils_stub.add_standard_arguments = lambda parser: None
    stage_utils_stub.infer_experiment = lambda args: getattr(args, "experiment", None)
    stage_utils_stub.parse_stage_args = lambda parser: parser.parse_args([])
    stage_utils_stub.EXIT_OK = 0
    stage_utils_stub.EXIT_ERROR = 3
    stage_utils_stub.STATUS_OK = "OK"
    stage_utils_stub.STATUS_ERROR = "ERROR"
    sys.modules["stage_utils"] = stage_utils_stub

    key = "stage08_contract_runtime_test"
    sys.modules.pop(key, None)
    spec = importlib.util.spec_from_file_location(key, REPO_ROOT / "08_build_holographic_dictionary.py")
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


def _write_geometry_h5(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(path, "w") as f:
        f.attrs["family"] = "ads"
        f.attrs["d"] = 4
        boundary = f.create_group("boundary")
        boundary.attrs["Delta_mass_dict"] = json.dumps(
            {
                "op_a": {
                    "Delta": 3.0,
                    "m2L2": -3.0,
                }
            }
        )


class Stage08ContractRuntimeTests(unittest.TestCase):
    def test_missing_canonical_input_aborts_without_legacy_fallback(self):
        s08 = _load_stage08()
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "runs" / "exp1"
            legacy_dir = run_root / "geometry_emergent"
            legacy_dir.mkdir(parents=True, exist_ok=True)
            _write_geometry_h5(legacy_dir / "geo_a.h5")

            args = argparse.Namespace(data_dir=None)

            with self.assertRaisesRegex(FileNotFoundError, "Missing canonical geometry input"):
                s08.resolve_geometry_dir(args, None, run_root)

    def test_ctx_default_output_goes_to_stage_outputs_dir(self):
        s08 = _load_stage08()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ctx = _FakeCtx(root / "runs" / "exp1", root / "runs" / "exp1" / "08_build_holographic_dictionary")
            args = argparse.Namespace(output_summary=None)

            output = s08.resolve_output_file(args, ctx, ctx.run_root)

            self.assertEqual(
                output,
                ctx.stage_dir / "outputs" / "holographic_dictionary_v3_summary.json",
            )

    def test_main_with_ctx_writes_manifest_and_stage_summary(self):
        s08 = _load_stage08()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_root = root / "runs" / "exp1"
            geometry_dir = run_root / "02_emergent_geometry_engine" / "outputs" / "geometry_emergent"
            _write_geometry_h5(geometry_dir / "geo_a.h5")
            stage_dir = run_root / "08_build_holographic_dictionary"
            fake_ctx = _FakeCtx(run_root, stage_dir)

            args = argparse.Namespace(
                run_dir=str(run_root),
                experiment="exp1",
                runs_dir=str(root / "runs"),
                data_dir=None,
                output_summary=None,
                mass_source="hdf5",
                compute_m2_from_delta=False,
                seed=42,
            )
            fake_stage_context = type(
                "FakeStageContext",
                (),
                {"from_args": staticmethod(lambda *a, **k: fake_ctx)},
            )

            with mock.patch.object(s08, "parse_args", return_value=args), \
                 mock.patch.object(s08, "StageContext", fake_stage_context):
                exit_code = s08.main()

            self.assertEqual(exit_code, s08.EXIT_OK)

            manifest_path = stage_dir / "manifest.json"
            summary_path = stage_dir / "stage_summary.json"
            output_path = stage_dir / "outputs" / "holographic_dictionary_v3_summary.json"

            self.assertTrue(output_path.exists())
            self.assertTrue(manifest_path.exists())
            self.assertTrue(summary_path.exists())

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            summary = json.loads(summary_path.read_text(encoding="utf-8"))

            self.assertEqual(
                manifest["outputs"]["holographic_dictionary_summary"],
                "08_build_holographic_dictionary/outputs/holographic_dictionary_v3_summary.json",
            )
            self.assertEqual(manifest["metadata"]["experiment"], "exp1")
            self.assertEqual(summary["status"], s08.STATUS_OK)
            self.assertEqual(summary["counts"]["h5_files_scanned"], 1)


if __name__ == "__main__":
    unittest.main()
