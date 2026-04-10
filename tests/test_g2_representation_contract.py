from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np
from typing import Any, Dict, List

from tools.g2_representation_contract import (
    CANONICAL_N_X,
    CANONICAL_X_MAX,
    CANONICAL_X_MIN,
    G2RepresentationContractError,
    build_canonical_x_grid,
    canonicalize_g2_representation,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_stage02_feature_namespace() -> Dict[str, Any]:
    module_path = REPO_ROOT / "02_emergent_geometry_engine.py"
    source = module_path.read_text(encoding="utf-8")
    start = source.index("def extract_correlator_features")
    end = source.index("class CuerdasDataLoader")
    snippet = source[start:end]
    namespace: Dict[str, Any] = {
        "np": np,
        "Dict": Dict,
        "List": List,
        "Any": Any,
    }
    exec(snippet, namespace)
    return namespace


class G2RepresentationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = load_stage02_feature_namespace()

    def _make_raw_samples(self) -> tuple[np.ndarray, np.ndarray]:
        x_raw = np.array(
            [
                np.inf,
                -1.0,
                7.0,
                0.05,
                0.2,
                0.2,
                10.0,
                1e-3,
                0.9,
                2.5,
                1.3,
                np.nan,
            ],
            dtype=np.float64,
        )
        x_safe = np.clip(np.nan_to_num(x_raw, nan=1.0, posinf=1.0), 1e-3, None)
        log_x = np.log(x_safe)
        g2_raw = np.exp(-0.8 * log_x + 0.25 * log_x**2)
        g2_raw[0] = np.inf
        g2_raw[1] = 0.3
        g2_raw[4] *= 1.2
        g2_raw[5] *= 0.8
        g2_raw[11] = np.nan
        return x_raw, g2_raw.astype(np.float64)

    def _make_boundary_pair(self):
        x_raw, g2_raw = self._make_raw_samples()
        canonical = canonicalize_g2_representation(x_raw, g2_raw)

        omega = np.linspace(0.1, 3.0, 256, dtype=np.float64)
        g_r_real = np.tile(np.exp(-omega)[:, None], (1, 30))
        g_r_imag = np.tile((0.5 * np.exp(-0.5 * omega))[:, None], (1, 30))
        qnm = {
            "qnm_Q0": 2.75,
            "qnm_f1f0": 1.18,
            "qnm_g1g0": 1.11,
            "qnm_n_modes": 3,
            "d": 4,
            "T": 0.0,
            "temperature": 0.0,
            "central_charge_eff": np.array([0.0], dtype=np.float64),
        }

        raw_boundary = {
            "x_grid": x_raw,
            "G2_ringdown": g2_raw,
            "omega_grid": omega,
            "k_grid": np.linspace(0.0, 5.0, 30, dtype=np.float64),
            "G_R_real": g_r_real,
            "G_R_imag": g_r_imag,
            **qnm,
        }
        compat_boundary = {
            "x_grid": canonical.x_grid,
            "G2_ringdown": canonical.g2_canonical,
            "G2_O1": canonical.g2_canonical,
            "omega_grid": omega,
            "k_grid": np.linspace(0.0, 5.0, 30, dtype=np.float64),
            "G_R_real": g_r_real,
            "G_R_imag": g_r_imag,
            **qnm,
        }
        return raw_boundary, compat_boundary

    def test_canonical_xgrid_contract(self):
        x_grid = build_canonical_x_grid()
        self.assertEqual(x_grid.shape, (CANONICAL_N_X,))
        self.assertEqual(x_grid.dtype, np.float64)
        self.assertAlmostEqual(float(x_grid[0]), CANONICAL_X_MIN)
        self.assertAlmostEqual(float(x_grid[-1]), CANONICAL_X_MAX)
        self.assertTrue(np.all(np.isfinite(x_grid)))
        self.assertTrue(np.all(x_grid > 0.0))

    def test_nonfinite_or_invalid_x_fails_cleanly(self):
        x_raw = np.array([np.nan, -1.0, 0.0, np.inf], dtype=np.float64)
        g2_raw = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)
        with self.assertRaisesRegex(G2RepresentationContractError, "insufficient valid G2/x samples"):
            canonicalize_g2_representation(x_raw, g2_raw)

    def test_contract_feature_vector(self):
        _, compat_boundary = self._make_boundary_pair()
        features = np.asarray(self.engine["build_feature_vector"](compat_boundary, []), dtype=np.float64)
        self.assertEqual(features.shape, (20,))
        self.assertTrue(np.all(np.isfinite(features)))

    def test_qnm_invariance_under_compat_view(self):
        raw_boundary, compat_boundary = self._make_boundary_pair()
        raw_features = np.asarray(self.engine["build_feature_vector"](raw_boundary, []), dtype=np.float64)
        compat_features = np.asarray(self.engine["build_feature_vector"](compat_boundary, []), dtype=np.float64)
        self.assertTrue(np.array_equal(raw_features[13:16], compat_features[13:16]))

    def test_g2_block_changes_under_compat_view(self):
        raw_boundary, compat_boundary = self._make_boundary_pair()
        raw_features = np.asarray(self.engine["build_feature_vector"](raw_boundary, []), dtype=np.float64)
        compat_features = np.asarray(self.engine["build_feature_vector"](compat_boundary, []), dtype=np.float64)
        delta = np.abs(compat_features - raw_features)
        self.assertGreater(float(np.max(delta[0:9])), 1e-6)
        self.assertEqual(float(np.max(delta[9:13])), 0.0)
        self.assertEqual(float(np.max(delta[13:16])), 0.0)


if __name__ == "__main__":
    unittest.main()
