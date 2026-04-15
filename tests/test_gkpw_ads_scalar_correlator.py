from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import h5py
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.gkpw_ads_scalar_correlator import (  # noqa: E402
    CORRELATOR_TYPE,
    GKPWAdsError,
    GKPWConfig,
    build_correlator_grid,
    compute_stability_benchmarks,
    generate_to_run,
    load_ads_geometry,
    validate_gate6_metadata,
)
from tools.validate_agmoo_ads import validate_ads_geometry  # noqa: E402


REQUIRED_GATE6 = {
    "bulk_field_name",
    "operator_name",
    "m2L2",
    "Delta",
    "bf_bound_pass",
    "uv_source_declared",
    "ir_bc_declared",
}


def _write_ads_h5(path: Path, *, z_h: float = 1.0, include_bulk_truth: bool = False) -> None:
    d = 3
    z = np.linspace(0.01, z_h * 0.999, 80)
    A = -np.log(z)
    f = np.maximum(1.0 - (z / z_h) ** d, 1e-8)
    with h5py.File(path, "w") as h5:
        h5.attrs["system_name"] = path.stem
        h5.attrs["family"] = "ads"
        h5.attrs["d"] = d
        h5.attrs["z_h"] = z_h
        h5.create_dataset("z_grid", data=z)
        h5.create_dataset("A_of_z", data=A)
        h5.create_dataset("f_of_z", data=f)
        if include_bulk_truth:
            bulk = h5.create_group("bulk_truth")
            bulk.create_dataset("z_grid", data=z)
            bulk.create_dataset("A_truth", data=A + 999.0)
            bulk.create_dataset("f_truth", data=np.ones_like(f) * 999.0)


class TestGKPWAdsScalarCorrelator(unittest.TestCase):
    def _small_config(self, **overrides) -> GKPWConfig:
        values = {
            "m2L2": 0.0,
            "operator_name": "O_test",
            "bulk_field_name": "phi_test",
            "omega_min": 0.5,
            "omega_max": 1.0,
            "n_omega": 3,
            "k_min": 0.0,
            "k_max": 0.5,
            "n_k": 2,
            "uv_fit_points": 8,
            "rtol": 1e-7,
            "atol": 1e-9,
        }
        values.update(overrides)
        return GKPWConfig(**values)

    def test_ads_thermal_horizon_generates_gr_and_gate6_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            h5_path = Path(tmp) / "ads_thermal.h5"
            _write_ads_h5(h5_path, z_h=1.0)
            geo = load_ads_geometry(h5_path)
            result = build_correlator_grid(geo, self._small_config())

        self.assertEqual(result["G_R_real"].shape, (2, 3))
        self.assertEqual(result["G_R_imag"].shape, (2, 3))
        self.assertTrue(np.all(np.isfinite(result["G_R_real"])))
        self.assertTrue(np.all(np.isfinite(result["G_R_imag"])))
        meta = result["metadata"]
        self.assertEqual(meta["classification"], "ads_thermal")
        self.assertEqual(meta["correlator_type"], CORRELATOR_TYPE)
        self.assertEqual(meta["ir_bc_type"], "ingoing_horizon")
        for key in REQUIRED_GATE6:
            self.assertIn(key, meta)
            self.assertIsNotNone(meta[key])
        self.assertTrue(meta["bf_bound_pass"])
        self.assertTrue(meta["uv_source_declared"])
        self.assertTrue(meta["ir_bc_declared"])

    def test_bf_violation_fails_explicitly(self):
        with tempfile.TemporaryDirectory() as tmp:
            h5_path = Path(tmp) / "ads_bf_fail.h5"
            _write_ads_h5(h5_path)
            geo = load_ads_geometry(h5_path)
            with self.assertRaisesRegex(GKPWAdsError, "BF bound violated"):
                build_correlator_grid(geo, self._small_config(m2L2=-3.0))

    def test_generate_to_run_writes_summary_with_complete_gate6(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            h5_path = root / "ads_out.h5"
            run_dir = root / "runs" / "unit_run"
            _write_ads_h5(h5_path)
            summary = generate_to_run(h5_path, run_dir, self._small_config())

            artifact = Path(summary["artifact"])
            summary_path = artifact.with_name("ads_out__gkpw_scalar_correlator_summary.json")
            self.assertTrue(artifact.exists())
            self.assertTrue(summary_path.exists())
            persisted = json.loads(summary_path.read_text())
            self.assertTrue(persisted["gate6_complete"])
            self.assertEqual(persisted["agmoo_verdict"], "ADS_HOLOGRAPHIC_STRONG_PASS")
            self.assertEqual(persisted["correlator_type"], CORRELATOR_TYPE)
            self.assertEqual(persisted["classification"], "ads_thermal")
            self.assertTrue(persisted["bf_bound_pass"])
            self.assertRegex(persisted["config_hash"], r"^[0-9a-f]{64}$")
            self.assertRegex(persisted["reproducibility_hash"], r"^[0-9a-f]{64}$")
            self.assertEqual(persisted["metadata"]["correlator_type"], CORRELATOR_TYPE)
            self.assertIn(run_dir.resolve(), artifact.resolve().parents)

    def test_generate_to_run_can_emit_stability_benchmarks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            h5_path = root / "ads_bench.h5"
            run_dir = root / "runs" / "unit_run"
            _write_ads_h5(h5_path)
            summary = generate_to_run(
                h5_path,
                run_dir,
                self._small_config(n_omega=2, n_k=1),
                run_benchmarks=True,
            )

        benchmarks = summary["benchmarks"]
        self.assertEqual(benchmarks["status"], "PASS")
        for key in ("radial_discretization", "uv_cutoff", "frequency_resolution"):
            self.assertIn(key, benchmarks)
            self.assertTrue(np.isfinite(benchmarks[key]["relative_l2_delta"]))
            self.assertGreaterEqual(benchmarks[key]["relative_l2_delta"], 0.0)
            self.assertTrue(np.isfinite(benchmarks[key]["max_abs_delta"]))

    def test_stability_benchmark_changes_are_controlled(self):
        with tempfile.TemporaryDirectory() as tmp:
            h5_path = Path(tmp) / "ads_controlled.h5"
            _write_ads_h5(h5_path)
            geo = load_ads_geometry(h5_path)
            config = self._small_config(n_omega=2, n_k=1)
            base = build_correlator_grid(geo, config)
            benchmarks = compute_stability_benchmarks(geo, config, base_result=base)

        deltas = [
            benchmarks[key]["relative_l2_delta"]
            for key in ("radial_discretization", "uv_cutoff", "frequency_resolution")
        ]
        self.assertTrue(all(np.isfinite(delta) for delta in deltas))
        self.assertTrue(all(delta < 1e6 for delta in deltas))
        self.assertTrue(any(delta > 0.0 for delta in deltas))

    def test_missing_required_metadata_fails_gate6_validation(self):
        metadata = {
            "bulk_field_name": "phi_test",
            "operator_name": "O_test",
            "m2L2": 0.0,
            "Delta": 3.0,
            "bf_bound_pass": True,
            "uv_source_declared": True,
            # ir_bc_declared deliberately missing
            "correlator_type": CORRELATOR_TYPE,
        }
        with self.assertRaisesRegex(GKPWAdsError, "missing required Gate 6 metadata"):
            validate_gate6_metadata(metadata)

    def test_toy_correlator_type_fails_gate6_validation(self):
        metadata = {
            "bulk_field_name": "phi_test",
            "operator_name": "O_test",
            "m2L2": 0.0,
            "Delta": 3.0,
            "bf_bound_pass": True,
            "uv_source_declared": True,
            "ir_bc_declared": True,
            "correlator_type": "TOY_PHENOMENOLOGICAL",
        }
        with self.assertRaisesRegex(GKPWAdsError, "invalid GKPW correlator_type"):
            validate_gate6_metadata(metadata)

    def test_canonical_ads_missing_gate6_fails_agmoo_contract(self):
        verdict = validate_ads_geometry(
            {
                "family": "ads",
                "d": 3,
                "z_h": 1.0,
                "ads_pipeline_tier": "canonical",
                "ads_boundary_mode": "gkpw",
                "correlator_type": CORRELATOR_TYPE,
                "bulk_field_name": "phi_test",
                "operator_name": "O_test",
                "m2L2": 0.0,
                "Delta": 3.0,
                "bf_bound_pass": True,
                "uv_source_declared": True,
                # ir_bc_declared deliberately missing
            }
        )
        self.assertEqual(verdict["overall_verdict"], "ADS_CONTRACT_FAIL")

    def test_root_geometry_datasets_are_used_without_hidden_bulk_truth(self):
        with tempfile.TemporaryDirectory() as tmp:
            h5_path = Path(tmp) / "ads_no_bulk_truth_required.h5"
            _write_ads_h5(h5_path, include_bulk_truth=True)
            geo = load_ads_geometry(h5_path)

        self.assertLess(float(np.max(geo.A)), 10.0)
        self.assertLess(float(np.max(geo.f)), 2.0)

    def test_output_is_reproducible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            h5_path = root / "ads_repro.h5"
            _write_ads_h5(h5_path)
            config = self._small_config()
            summary_a = generate_to_run(h5_path, root / "runs" / "run_a", config)
            summary_b = generate_to_run(h5_path, root / "runs" / "run_b", config)

        hash_a = summary_a["metadata"]["reproducibility_hash"]
        hash_b = summary_b["metadata"]["reproducibility_hash"]
        self.assertEqual(hash_a, hash_b)

    def test_refuses_non_ads_family(self):
        with tempfile.TemporaryDirectory() as tmp:
            h5_path = Path(tmp) / "lifshitz.h5"
            _write_ads_h5(h5_path)
            with h5py.File(h5_path, "a") as h5:
                h5.attrs["family"] = "lifshitz"
            with self.assertRaisesRegex(GKPWAdsError, "family='ads'"):
                load_ads_geometry(h5_path)


if __name__ == "__main__":
    unittest.main()
