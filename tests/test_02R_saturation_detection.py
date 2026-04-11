"""
Tests for saturation detection and automatic contract selection in 02R.

These tests cover:
- detect_saturation_risk() function
- Automatic contract selection for SATURATED_BY_CONSTRUCTION cases
- Regression tests ensuring PASS-25 corridor is not affected
"""
from __future__ import annotations

import importlib.util
import math
import sys
import unittest
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_02r():
    key = "stage02r_saturation_test"
    sys.modules.pop(key, None)
    spec = importlib.util.spec_from_file_location(
        key, REPO_ROOT / "02R_build_ringdown_boundary_dataset.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


class TestSaturationDetection(unittest.TestCase):
    """Tests for the detect_saturation_risk function."""

    def setUp(self):
        self.mod = _load_02r()

    def test_high_q_event_triggers_saturation_risk(self):
        """Events with high Q (low gamma/omega) should trigger saturation risk."""
        # Q = 10000 -> gamma/omega = 1/(2*Q) = 0.00005
        # exp(-2 * 0.00005 * 6) = exp(-0.0006) ≈ 0.9994
        omega_dom = 2.0 * math.pi * 100.0  # 100 Hz
        gamma_dom = omega_dom / (2.0 * 10000)  # Q = 10000
        x_max = 6.0

        is_at_risk, predicted_tail = self.mod.detect_saturation_risk(
            omega_dom, gamma_dom, x_max, threshold=0.99
        )

        self.assertTrue(is_at_risk, "High Q event should trigger saturation risk")
        self.assertGreater(predicted_tail, 0.99)

    def test_low_q_event_no_saturation_risk(self):
        """Events with low Q should not trigger saturation risk."""
        # Q = 5 -> gamma/omega = 0.1
        # exp(-2 * 0.1 * 6) = exp(-1.2) ≈ 0.30
        omega_dom = 2.0 * math.pi * 100.0
        gamma_dom = omega_dom / (2.0 * 5)  # Q = 5
        x_max = 6.0

        is_at_risk, predicted_tail = self.mod.detect_saturation_risk(
            omega_dom, gamma_dom, x_max, threshold=0.99
        )

        self.assertFalse(is_at_risk, "Low Q event should not trigger saturation risk")
        self.assertLess(predicted_tail, 0.5)

    def test_threshold_boundary(self):
        """Test the threshold boundary condition."""
        # Choose Q such that exp(-2 * (1/(2Q)) * 6) = 0.99
        # -2 * 6 / (2Q) = ln(0.99)
        # Q = -6 / ln(0.99) ≈ 597
        omega_dom = 2.0 * math.pi * 100.0
        Q_boundary = -6.0 / math.log(0.99)
        gamma_dom = omega_dom / (2.0 * Q_boundary)
        x_max = 6.0

        # Just below threshold
        is_at_risk, _ = self.mod.detect_saturation_risk(
            omega_dom, gamma_dom * 1.01, x_max, threshold=0.99
        )
        self.assertFalse(is_at_risk)

        # Just above threshold
        is_at_risk, _ = self.mod.detect_saturation_risk(
            omega_dom, gamma_dom * 0.99, x_max, threshold=0.99
        )
        self.assertTrue(is_at_risk)

    def test_invalid_inputs_return_no_risk(self):
        """Invalid inputs should return no risk, not raise errors."""
        is_at_risk, _ = self.mod.detect_saturation_risk(0, 1.0, 6.0)
        self.assertFalse(is_at_risk)

        is_at_risk, _ = self.mod.detect_saturation_risk(1.0, 0, 6.0)
        self.assertFalse(is_at_risk)

        is_at_risk, _ = self.mod.detect_saturation_risk(1.0, 1.0, 0)
        self.assertFalse(is_at_risk)


class TestSaturatedByConstructionRegime(unittest.TestCase):
    """Tests simulating the SATURATED_BY_CONSTRUCTION regime (8 events)."""

    def setUp(self):
        self.mod = _load_02r()

    def test_saturated_event_with_omega_v1_produces_flat_g2(self):
        """
        Simulate a SATURATED_BY_CONSTRUCTION event.
        With omega_dom_v1, G2 should be nearly flat (all values > 0.99).
        """
        # Simulate GW200129_065458-like: Q ~ 103000
        Q = 100000
        freq_hz = 250.0
        omega_dom = 2.0 * math.pi * freq_hz
        gamma_dom = omega_dom / (2.0 * Q)

        pole = self.mod.Pole(freq_hz=freq_hz, damping_1_over_s=gamma_dom, amp_abs=1.0)

        x_grid = self.mod.build_x_grid_dimless(
            100, 1e-3, 6.0, g2_time_contract=self.mod.G2_TIME_CONTRACT_OMEGA_DOM_V1
        )
        g2 = self.mod.poles_to_g2(
            x_grid,
            [pole],
            omega_dom,
            gamma_dom,
            g2_time_contract=self.mod.G2_TIME_CONTRACT_OMEGA_DOM_V1,
        )

        # With omega_dom_v1, G2 should be nearly constant (saturated)
        self.assertGreater(float(g2[-1]), 0.999, "G2 tail should be saturated > 0.999")
        self.assertGreater(float(np.min(g2)), 0.99, "All G2 values should be > 0.99")

    def test_saturated_event_with_gamma_v2_produces_proper_decay(self):
        """
        The same SATURATED_BY_CONSTRUCTION event with gamma_dom_v2
        should show proper exponential decay.
        """
        Q = 100000
        freq_hz = 250.0
        omega_dom = 2.0 * math.pi * freq_hz
        gamma_dom = omega_dom / (2.0 * Q)

        pole = self.mod.Pole(freq_hz=freq_hz, damping_1_over_s=gamma_dom, amp_abs=1.0)

        x_grid = self.mod.build_x_grid_dimless(
            100, 1e-3, 6.0, g2_time_contract=self.mod.G2_TIME_CONTRACT_GAMMA_DOM_V2
        )
        g2 = self.mod.poles_to_g2(
            x_grid,
            [pole],
            omega_dom,
            gamma_dom,
            g2_time_contract=self.mod.G2_TIME_CONTRACT_GAMMA_DOM_V2,
        )

        # With gamma_dom_v2, G2 should decay properly
        # exp(-2 * 1 * 6) = exp(-12) ~ 6e-6
        self.assertLess(float(g2[-1]), 1e-4, "G2 tail should be very small with gamma_v2")


class TestHighTailNonSaturatedRegime(unittest.TestCase):
    """Tests simulating the HIGH_TAIL_NON_SATURATED regime (55 events)."""

    def setUp(self):
        self.mod = _load_02r()

    def test_high_tail_event_has_intermediate_g2_last(self):
        """
        HIGH_TAIL events have G2_last in [0.12, 0.86], not saturated.
        This is typically due to multimodal content, not contract issues.
        """
        # Simulate a multimodal event with moderate Q
        freq_1 = 200.0
        freq_2 = 280.0  # qnm_f1f0 ~ 1.4
        omega_dom = 2.0 * math.pi * freq_1
        Q = 2000
        gamma_1 = omega_dom / (2.0 * Q)
        gamma_2 = gamma_1 * 1.5  # qnm_g1g0 ~ 1.5

        poles = [
            self.mod.Pole(freq_hz=freq_1, damping_1_over_s=gamma_1, amp_abs=1.0),
            self.mod.Pole(freq_hz=freq_2, damping_1_over_s=gamma_2, amp_abs=0.4),
        ]

        x_grid = self.mod.build_x_grid_dimless(
            100, 1e-3, 6.0, g2_time_contract=self.mod.G2_TIME_CONTRACT_OMEGA_DOM_V1
        )
        g2 = self.mod.poles_to_g2(
            x_grid,
            poles,
            omega_dom,
            gamma_1,
            g2_time_contract=self.mod.G2_TIME_CONTRACT_OMEGA_DOM_V1,
        )

        # Should have intermediate tail, not saturated
        g2_last = float(g2[-1])
        self.assertGreater(g2_last, 0.05, "G2 tail should be > 0.05")
        self.assertLess(g2_last, 0.99, "G2 tail should be < 0.99 (not saturated)")


class TestPassCorridorRegression(unittest.TestCase):
    """Regression tests to ensure PASS-25 corridor is not affected."""

    def setUp(self):
        self.mod = _load_02r()

    def test_gw150914_like_event_does_not_trigger_saturation(self):
        """
        GW150914 has Q ~ 2250, should not trigger saturation risk.
        """
        Q = 2250
        freq_hz = 250.0
        omega_dom = 2.0 * math.pi * freq_hz
        gamma_dom = omega_dom / (2.0 * Q)
        x_max = 6.0

        is_at_risk, predicted_tail = self.mod.detect_saturation_risk(
            omega_dom, gamma_dom, x_max, threshold=0.99
        )

        self.assertFalse(is_at_risk, "GW150914-like event should not trigger saturation")
        # exp(-2 * (1/(2*2250)) * 6) = exp(-0.00267) ~ 0.9973
        self.assertLess(predicted_tail, 0.998)

    def test_pass_event_g2_has_proper_decay(self):
        """
        A PASS event should show meaningful G2 decay, not saturation.
        GW150914 has G2_last ~ 0.006.
        """
        # Multimodal simulation
        freq_1 = 250.0
        omega_dom = 2.0 * math.pi * freq_1
        Q = 2000
        gamma_dom = omega_dom / (2.0 * Q)

        # Multiple modes cause faster effective decay
        poles = [
            self.mod.Pole(freq_hz=freq_1, damping_1_over_s=gamma_dom, amp_abs=1.0),
            self.mod.Pole(freq_hz=freq_1 * 0.8, damping_1_over_s=gamma_dom * 1.2, amp_abs=0.6),
            self.mod.Pole(freq_hz=freq_1 * 1.3, damping_1_over_s=gamma_dom * 0.9, amp_abs=0.3),
        ]

        x_grid = self.mod.build_x_grid_dimless(
            100, 1e-3, 6.0, g2_time_contract=self.mod.G2_TIME_CONTRACT_OMEGA_DOM_V1
        )
        g2 = self.mod.poles_to_g2(
            x_grid,
            poles,
            omega_dom,
            gamma_dom,
            g2_time_contract=self.mod.G2_TIME_CONTRACT_OMEGA_DOM_V1,
        )

        # Should have low tail due to modal interference
        self.assertLess(float(g2[-1]), 0.12, "PASS-like event should have G2_last < 0.12")


class TestContractConstants(unittest.TestCase):
    """Verify contract constants are correctly defined."""

    def setUp(self):
        self.mod = _load_02r()

    def test_saturation_threshold_is_099(self):
        """Default saturation threshold should be 0.99."""
        self.assertEqual(self.mod.SATURATION_RISK_THRESHOLD, 0.99)

    def test_resolve_contract_for_gamma_v2(self):
        """gamma_dom_v2 should resolve to xgamma_6_v2 contract."""
        contract, x_max = self.mod.resolve_g2_repr_contract(
            self.mod.G2_TIME_CONTRACT_GAMMA_DOM_V2
        )
        self.assertEqual(contract, "xgamma_6_v2")
        self.assertEqual(x_max, 6.0)


if __name__ == "__main__":
    unittest.main()
