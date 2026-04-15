from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_stage01():
    name = "stage01_ads_gkpw_mode_test"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / "01_generate_sandbox_geometries.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestStage01AdsGKPWMode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stage01 = _load_stage01()

    def _ads_geo(self):
        return self.stage01.HiddenGeometry(
            name="ads_unit",
            family="ads",
            category="known",
            d=3,
            z_h=1.0,
            theta=0.0,
            z_dyn=1.0,
            deformation=0.0,
            L=1.0,
        )

    def _operators(self):
        return [
            {"name": "O1", "Delta": 3.0, "m2L2": 0.0, "spin": 0},
            {"name": "O2", "Delta": 3.5, "m2L2": 1.75, "spin": 0},
        ]

    def test_ads_boundary_mode_default_is_gkpw(self):
        args = self.stage01.build_parser().parse_args([])
        self.assertEqual(args.ads_boundary_mode, "gkpw")

    def test_ads_gkpw_mode_generates_gate6_complete_metadata(self):
        rng = np.random.default_rng(123)
        z_grid = np.linspace(0.01, 0.999, 80)
        data, meta = self.stage01.generate_boundary_data(
            self._ads_geo(),
            self._operators(),
            n_samples=24,
            rng=rng,
            ads_boundary_mode="gkpw",
            z_grid=z_grid,
        )

        self.assertEqual(meta["correlator_type"], "GKPW_SOURCE_RESPONSE_NUMERICAL")
        self.assertEqual(meta["ads_pipeline_tier"], "canonical")
        self.assertEqual(meta["ads_boundary_mode"], "gkpw")
        self.assertEqual(meta["classification"], "ads_thermal")
        self.assertRegex(meta["config_hash"], r"^[0-9a-f]{64}$")
        self.assertRegex(meta["reproducibility_hash"], r"^[0-9a-f]{64}$")
        for key in (
            "bulk_field_name",
            "operator_name",
            "m2L2",
            "Delta",
            "bf_bound_pass",
            "uv_source_declared",
            "ir_bc_declared",
        ):
            self.assertIn(key, meta)
            self.assertIsNotNone(meta[key])
        self.assertTrue(meta["bf_bound_pass"])
        self.assertTrue(meta["uv_source_declared"])
        self.assertTrue(meta["ir_bc_declared"])
        self.assertIn("G_R_real", data)
        self.assertIn("G_R_imag", data)
        self.assertIn("G2_O1", data)
        self.assertTrue(np.all(np.isfinite(data["G_R_real"])))

    def test_ads_gkpw_mode_does_not_call_toy_correlator_helpers(self):
        rng = np.random.default_rng(123)
        z_grid = np.linspace(0.01, 0.999, 80)
        with mock.patch.object(
            self.stage01,
            "correlator_2pt_thermal",
            side_effect=AssertionError("thermal toy helper must not be used in ads gkpw mode"),
        ), mock.patch.object(
            self.stage01,
            "correlator_2pt_geodesic",
            side_effect=AssertionError("geodesic helper must not be used in ads gkpw mode"),
        ):
            data, meta = self.stage01.generate_boundary_data(
                self._ads_geo(),
                self._operators(),
                n_samples=24,
                rng=rng,
                ads_boundary_mode="gkpw",
                z_grid=z_grid,
            )
        self.assertEqual(meta["ads_pipeline_tier"], "canonical")
        self.assertEqual(meta["correlator_type"], "GKPW_SOURCE_RESPONSE_NUMERICAL")
        self.assertIn("G_R_real", data)

    def test_ads_gkpw_run_summary_contract(self):
        rng = np.random.default_rng(123)
        z_grid = np.linspace(0.01, 0.999, 80)
        _, meta = self.stage01.generate_boundary_data(
            self._ads_geo(),
            self._operators(),
            n_samples=16,
            rng=rng,
            ads_boundary_mode="gkpw",
            z_grid=z_grid,
        )
        manifest = {
            "geometries": [
                {
                    "name": "ads_unit",
                    "file": "ads_unit.h5",
                    "family": "ads",
                    "d": 3,
                    "z_h": 1.0,
                    "operators": ["O1", "O2"],
                    **meta,
                }
            ]
        }
        summary = self.stage01.build_ads_gkpw_run_summary(manifest)

        self.assertEqual(summary["ads_count"], 1)
        self.assertEqual(summary["canonical_ads_count"], 1)
        self.assertTrue(summary["canonical_ads_contract_pass"])
        self.assertTrue(summary["items"][0]["gate6_complete"])
        self.assertEqual(summary["items"][0]["agmoo_verdict"], "ADS_HOLOGRAPHIC_STRONG_PASS")
        self.assertRegex(summary["items"][0]["reproducibility_hash"], r"^[0-9a-f]{64}$")

    def test_ads_toy_mode_is_honestly_tagged_experimental(self):
        rng = np.random.default_rng(123)
        data, meta = self.stage01.generate_boundary_data(
            self._ads_geo(),
            self._operators(),
            n_samples=24,
            rng=rng,
            ads_boundary_mode="toy",
            z_grid=np.linspace(0.01, 0.999, 80),
        )

        self.assertEqual(meta["correlator_type"], "GEODESIC_APPROXIMATION")
        self.assertEqual(meta["ads_pipeline_tier"], "experimental")
        self.assertEqual(meta["ads_boundary_mode"], "toy")
        self.assertEqual(meta["g2_correlator_type"], "GEODESIC_APPROXIMATION")
        self.assertEqual(meta["gr_correlator_type"], "TOY_PHENOMENOLOGICAL")
        self.assertEqual(meta["bulk_field_name"], "TOY_NO_BULK_FIELD")
        self.assertFalse(meta["uv_source_declared"])
        self.assertFalse(meta["ir_bc_declared"])
        self.assertIn("G_R_real", data)
        self.assertIn("G2_O1", data)

    def test_non_ads_families_keep_toy_geodesic_compatibility(self):
        rng = np.random.default_rng(123)
        for family in ("lifshitz", "hyperscaling", "deformed", "dpbrane"):
            geo = self.stage01.HiddenGeometry(
                name=f"{family}_unit",
                family=family,
                category="known",
                d=3,
                z_h=1.0,
                theta=0.5 if family == "hyperscaling" else 0.0,
                z_dyn=2.0 if family == "lifshitz" else 1.0,
                deformation=0.2 if family == "deformed" else 0.0,
                L=1.0,
            )
            data, meta = self.stage01.generate_boundary_data(
                geo,
                self._operators(),
                n_samples=16,
                rng=rng,
                ads_boundary_mode="gkpw",
                z_grid=np.linspace(0.01, 0.999, 80),
            )
            self.assertEqual(meta["correlator_type"], "GEODESIC_APPROXIMATION")
            self.assertIsNone(meta["ads_classification"])
            self.assertIn("G_R_real", data)
            self.assertIn("G2_O1", data)


if __name__ == "__main__":
    unittest.main()
