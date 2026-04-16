"""
Tests for tools/experiment_g2_representation_stability.py

Verifies CLI safety, cohort mode, and absence of top-level hardcodes.
"""
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
SCRIPT = REPO_ROOT / "tools" / "experiment_g2_representation_stability.py"


def _load_module():
    name = "experiment_g2_repr_stability_test"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _make_minimal_h5(path: Path) -> None:
    """Write a minimal boundary H5 with G2_ringdown + x_grid."""
    with h5py.File(path, "w") as f:
        f.attrs["operators"] = "[]"
        f.attrs["system_name"] = path.stem
        f.attrs["family"] = "test_family"
        f.attrs["d"] = 4
        b = f.create_group("boundary")
        b.attrs["d"] = 4
        b.create_dataset("x_grid", data=np.linspace(1e-3, 10.0, 100))
        b.create_dataset("G2_ringdown", data=np.ones(100) * 0.5)
        b.create_dataset("G2_O1", data=np.ones(100) * 0.5)


class TestHelpDoesNotTouchHardcodedSource(unittest.TestCase):
    """--help must exit cleanly without touching any on-disk path."""

    def test_help_exits_zero_without_disk_access(self):
        # argparse --help raises SystemExit(0)
        with self.assertRaises(SystemExit) as ctx:
            with patch.object(sys, "argv", [str(SCRIPT), "--help"]):
                _load_module()  # reload so parse_args is fresh
                mod = _load_module()
                mod.parse_args(["--help"])
        self.assertEqual(ctx.exception.code, 0)


class TestCliAcceptsInputDirAndOutputDir(unittest.TestCase):
    """parse_args must accept --input-dir and --output-dir without side effects."""

    def test_parse_required_args(self):
        mod = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            args = mod.parse_args([
                "--input-dir", tmp,
                "--output-dir", tmp,
            ])
        self.assertEqual(args.input_dir, Path(tmp))
        self.assertEqual(args.output_dir, Path(tmp))

    def test_parse_optional_args(self):
        mod = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            args = mod.parse_args([
                "--input-dir", tmp,
                "--output-dir", tmp,
                "--limit", "3",
                "--variants", "baseline_v2_like",
                "--baseline-variant", "baseline_v2_like",
            ])
        self.assertEqual(args.limit, 3)
        self.assertEqual(args.variants, ["baseline_v2_like"])
        self.assertEqual(args.baseline_variant, "baseline_v2_like")


class TestNoTopLevelHardcodedProjectRootRequired(unittest.TestCase):
    """The module must import successfully without /home/ignac/RINGEST existing."""

    def test_import_does_not_require_old_paths(self):
        mod = _load_module()
        # Old constants must not exist at module level
        self.assertFalse(hasattr(mod, "PROJECT_ROOT"), "PROJECT_ROOT should not exist at module level")
        self.assertFalse(hasattr(mod, "EVENT_ROOT"), "EVENT_ROOT should not exist at module level")
        self.assertFalse(hasattr(mod, "SOURCE_H5"), "SOURCE_H5 should not exist at module level")
        self.assertFalse(hasattr(mod, "CHECKPOINT"), "CHECKPOINT should not exist at module level")
        self.assertFalse(hasattr(mod, "SYSTEM_NAME"), "SYSTEM_NAME should not exist at module level")

    def test_variants_list_is_present(self):
        mod = _load_module()
        self.assertTrue(hasattr(mod, "VARIANTS"))
        self.assertGreater(len(mod.VARIANTS), 0)


class TestRunsOnMinimalFixtureCohort(unittest.TestCase):
    """
    With a minimal fixture and stubbed inference, main() must:
    - return 0
    - write manifest.json and cohort_summary.json under --output-dir
    - produce per-event summary.json
    """

    def _stub_inference(self, variant_dir, inference_script, checkpoint, cwd=None):
        """Fake run_inference: writes the minimal emergent_geometry_summary.json."""
        inference_dir = variant_dir / "inference"
        inference_dir.mkdir(parents=True, exist_ok=True)
        summary = {
            "systems": [{"family_pred": "kerr", "zh_pred": 0.5}]
        }
        (inference_dir / "emergent_geometry_summary.json").write_text(
            json.dumps(summary), encoding="utf-8"
        )
        return summary["systems"][0]

    def _stub_load_features(self, stage02_module, h5_path):
        return np.zeros(20, dtype=float)

    def test_main_produces_output_artifacts(self):
        mod = _load_module()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_dir = tmp_path / "input"
            output_dir = tmp_path / "output"
            input_dir.mkdir()

            # Write two minimal H5 fixtures
            for name in ["EVT_A__ringdown", "EVT_B__ringdown"]:
                _make_minimal_h5(input_dir / f"{name}.h5")

            # Fake checkpoint and inference script (just need to exist)
            ckpt = tmp_path / "model.pt"
            ckpt.write_bytes(b"fake")
            infer_script = tmp_path / "02_emergent_geometry_engine.py"
            infer_script.write_text("# stub\n")

            # Patch the two I/O-heavy functions
            mod.run_inference = self._stub_inference.__get__(self, type(self))
            mod.load_features = lambda stage02_module, h5_path: np.zeros(20, dtype=float)
            mod.load_stage02_module = lambda inference_script: types.SimpleNamespace(
                build_feature_vector=lambda *a, **kw: [0.0] * 20
            )

            argv = [
                "--input-dir", str(input_dir),
                "--output-dir", str(output_dir),
                "--checkpoint", str(ckpt),
                "--inference-script", str(infer_script),
                "--variants", "baseline_v2_like",
            ]
            with patch.object(sys, "argv", [str(SCRIPT)] + argv):
                exit_code = mod.main()

            self.assertEqual(exit_code, 0)
            self.assertTrue((output_dir / "manifest.json").exists())
            self.assertTrue((output_dir / "cohort_summary.json").exists())

            cohort = json.loads((output_dir / "cohort_summary.json").read_text())
            self.assertEqual(cohort["n_sources"], 2)
            self.assertEqual(cohort["n_ok"], 2)
            self.assertEqual(cohort["n_errors"], 0)

            # Each event must have a summary.json
            for name in ["EVT_A__ringdown", "EVT_B__ringdown"]:
                summary_path = output_dir / name / "summary.json"
                self.assertTrue(summary_path.exists(), f"Missing {summary_path}")
                s = json.loads(summary_path.read_text())
                self.assertEqual(s["system_name"], name)
                self.assertIn("overall_verdict", s)


class TestMakeVariantH5SkipsMissingDatasets(unittest.TestCase):
    """make_variant_h5 must return None (not crash) when source datasets are absent."""

    def test_returns_none_for_missing_source_key(self):
        mod = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            h5_path = tmp_path / "test.h5"
            _make_minimal_h5(h5_path)  # has G2_ringdown, x_grid; NOT G2_ringdown_raw

            raw_variant = next(v for v in mod.VARIANTS if v.source_g2_key == "G2_ringdown_raw")
            result = mod.make_variant_h5(h5_path, tmp_path / "vdir", raw_variant, "test")
        self.assertIsNone(result)

    def test_returns_path_when_datasets_present(self):
        mod = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            h5_path = tmp_path / "test.h5"
            _make_minimal_h5(h5_path)

            baseline_variant = next(v for v in mod.VARIANTS if v.name == "baseline_v2_like")
            result = mod.make_variant_h5(h5_path, tmp_path / "vdir", baseline_variant, "test")
            self.assertIsNotNone(result)
            self.assertTrue(result.exists())


if __name__ == "__main__":
    unittest.main()
