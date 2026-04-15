from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_realdata_bridge():
    key = "realdata_bridge_g2_contracts_test"
    sys.modules.pop(key, None)
    spec = importlib.util.spec_from_file_location(
        key, REPO_ROOT / "realdata_ringdown_to_stage02_boundary_dataset.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


class TestG2TimeContracts(unittest.TestCase):
    def setUp(self):
        self.mod = _load_realdata_bridge()

    def test_gamma_dom_v2_decays_faster_than_omega_dom_v1_for_same_pole(self):
        pole = self.mod.Pole(freq_hz=100.0, damping_1_over_s=1.0, amp_abs=1.0)
        x = self.mod.build_x_grid_dimless(
            100,
            1e-3,
            6.0,
            g2_time_contract=self.mod.G2_TIME_CONTRACT_OMEGA_DOM_V1,
        )
        g2_v1 = self.mod.poles_to_g2(
            x,
            [pole],
            omega_dom_rads=2.0 * np.pi * 100.0,
            gamma_dom_inv_s=1.0,
            g2_time_contract=self.mod.G2_TIME_CONTRACT_OMEGA_DOM_V1,
        )
        g2_v2 = self.mod.poles_to_g2(
            x,
            [pole],
            omega_dom_rads=2.0 * np.pi * 100.0,
            gamma_dom_inv_s=1.0,
            g2_time_contract=self.mod.G2_TIME_CONTRACT_GAMMA_DOM_V2,
        )

        self.assertGreater(float(g2_v1[-1]), 0.9)
        self.assertLess(float(g2_v2[-1]), 1e-4)

    def test_build_x_grid_rejects_unknown_contract(self):
        with self.assertRaises(ValueError):
            self.mod.build_x_grid_dimless(10, 1e-3, 6.0, g2_time_contract="unknown_contract")

    def test_resolve_g2_repr_contract_for_gamma_dom_v2(self):
        contract_name, x_max = self.mod.resolve_g2_repr_contract(
            self.mod.G2_TIME_CONTRACT_GAMMA_DOM_V2
        )
        self.assertEqual(contract_name, "xgamma_6_v2")
        self.assertEqual(x_max, 6.0)

    def test_resolve_g2_repr_contract_for_omega_dom_v1(self):
        contract_name, x_max = self.mod.resolve_g2_repr_contract(
            self.mod.G2_TIME_CONTRACT_OMEGA_DOM_V1
        )
        self.assertEqual(contract_name, "xmax_10_omega_dom_v1")
        self.assertEqual(x_max, 10.0)


if __name__ == "__main__":
    unittest.main()
