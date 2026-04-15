from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import h5py
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "tools" / "run_softwall_gubserrocha_baseline.py"


def _load_module():
    name = "softwall_gubserrocha_baseline_test"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _write_fixture_h5(path: Path, family: str, scale: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    x = np.linspace(0.1, 9.0, 9, dtype=float)
    z = np.linspace(0.01, 1.0, 9, dtype=float)
    with h5py.File(path, "w") as f:
        f.attrs["family"] = family
        f.attrs["d"] = 4
        f.create_dataset("z_grid", data=z)
        bt = f.create_group("bulk_truth")
        bt.create_dataset("A_truth", data=scale * (1.0 + z))
        bt.create_dataset("f_truth", data=np.clip(1.0 - 0.2 * scale * z, 0.0, 1.0))
        b = f.create_group("boundary")
        b.create_dataset("x_grid", data=x)
        for idx, op in enumerate(("G2_O1", "G2_O2", "G2_O3"), start=1):
            b.create_dataset(op, data=np.exp(-(scale + 0.1 * idx) * x))


class TestBaselineExperimentRunner(unittest.TestCase):
    def test_cli_runs_and_writes_report(self):
        mod = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sandbox_dir = root / "01_generate_sandbox_geometries"
            output_dir = root / "out"
            for i in range(2):
                _write_fixture_h5(sandbox_dir / f"gubser_rocha_d4_mu08_test_{i:03d}.h5", "gubser_rocha", 0.8)
                _write_fixture_h5(sandbox_dir / f"soft_wall_d4_k05_test_{i:03d}.h5", "soft_wall", 1.4)

            summary = {
                "systems": [
                    {
                        "name": f"gubser_rocha_d4_mu08_test_{i:03d}",
                        "family_truth": "gubser_rocha",
                        "family_pred": "gubser_rocha",
                        "category": "test",
                    }
                    for i in range(2)
                ] + [
                    {
                        "name": f"soft_wall_d4_k05_test_{i:03d}",
                        "family_truth": "soft_wall",
                        "family_pred": "soft_wall",
                        "category": "test",
                    }
                    for i in range(2)
                ]
            }
            summary_path = root / "emergent_geometry_summary.json"
            summary_path.write_text(json.dumps(summary), encoding="utf-8")

            exit_code = mod.main(
                [
                    "--sandbox-dir",
                    str(sandbox_dir),
                    "--engine-summary-json",
                    str(summary_path),
                    "--output-dir",
                    str(output_dir),
                    "--n-bootstrap",
                    "50",
                    "--n-permutation",
                    "50",
                    "--seed",
                    "7",
                ]
            )
            self.assertEqual(exit_code, 0)

            report = json.loads((output_dir / "baseline_report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["primary_observable"]["value"], 1.0)
            self.assertEqual(report["baseline_status"], "SEPARATION_SIGNAL_PRESENT")
            self.assertEqual(report["preregister_final_verdict"], "PENDING_SENSITIVITY_BLOCKS")
            self.assertGreater(report["secondary_observables"]["D_G2_total"], 0.0)
            self.assertGreater(report["secondary_observables"]["D_bulk_total"], 0.0)
            self.assertTrue((output_dir / "canonical_cohort_members.csv").exists())
            self.assertTrue((output_dir / "manifest.json").exists())


if __name__ == "__main__":
    unittest.main()
