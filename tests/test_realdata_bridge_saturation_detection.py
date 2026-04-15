"""
Tests for observed saturation detection and automatic contract selection in real-data bridge.

These tests cover:
- detect_observed_saturation() function (post-hoc on constructed G2)
- Automatic contract selection for SATURATED_BY_CONSTRUCTION cases
- Regression tests ensuring PASS-25 and HIGH_TAIL_55 corridors are not affected
"""
from __future__ import annotations

import importlib.util
import math
import sys
import unittest
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_realdata_bridge():
    key = "realdata_bridge_saturation_test"
    sys.modules.pop(key, None)
    spec = importlib.util.spec_from_file_location(
        key, REPO_ROOT / "realdata_ringdown_to_stage02_boundary_dataset.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


class TestObservedSaturationDetection(unittest.TestCase):
    """Tests for the detect_observed_saturation function."""

    def setUp(self):
        self.mod = _load_realdata_bridge()

    def test_all_ones_array_is_saturated(self):
        """Array with all values >= 0.99 should be detected as saturated."""
        g2 = np.ones(100, dtype=np.float64) * 0.995
        is_saturated, meta = self.mod.detect_observed_saturation(g2)

        self.assertTrue(is_saturated, "All-ones array should be saturated")
        self.assertEqual(meta["n_ge_threshold"], 100)
        self.assertAlmostEqual(meta["fraction_ge_threshold"], 1.0)

    def test_decaying_array_is_not_saturated(self):
        """Array with proper decay (typical PASS case) should not be saturated."""
        # Simulate PASS-like decay: starts at 1, decays to ~0.05
        x = np.linspace(0, 6, 100)
        g2 = np.exp(-2 * x / 3)  # Moderate decay, ends at ~0.018

        is_saturated, meta = self.mod.detect_observed_saturation(g2)

        self.assertFalse(is_saturated, "Decaying array should not be saturated")
        self.assertLess(meta["g2_last"], 0.1)

    def test_high_tail_array_is_not_saturated(self):
        """Array with high tail but not fully saturated should not trigger."""
        # HIGH_TAIL case: g2_last in [0.12, 0.86], some points >= 0.99 but not all
        g2 = np.linspace(1.0, 0.3, 100)  # Ends at 0.3, starts at 1.0

        is_saturated, meta = self.mod.detect_observed_saturation(g2)

        self.assertFalse(is_saturated, "High-tail array should not be saturated")
        self.assertLess(meta["fraction_ge_threshold"], 1.0)

    def test_threshold_boundary_tail(self):
        """Test behavior at the tail threshold boundary."""
        g2 = np.ones(100, dtype=np.float64)

        # Just below threshold at tail
        g2[-1] = 0.989
        is_saturated, _ = self.mod.detect_observed_saturation(g2)
        self.assertFalse(is_saturated, "g2[-1] < 0.99 should not be saturated")

        # At threshold
        g2[-1] = 0.99
        is_saturated, _ = self.mod.detect_observed_saturation(g2)
        self.assertTrue(is_saturated, "g2[-1] >= 0.99 with all points >= 0.99 should be saturated")

    def test_fraction_threshold_requirement(self):
        """Saturation requires ALL points >= 0.99, not just the tail."""
        g2 = np.ones(100, dtype=np.float64) * 0.995
        g2[0] = 0.5  # One point below threshold

        is_saturated, meta = self.mod.detect_observed_saturation(g2)

        self.assertFalse(is_saturated, "Array with one point < 0.99 should not be saturated")
        self.assertEqual(meta["n_ge_threshold"], 99)

    def test_empty_array_returns_no_saturation(self):
        """Empty array should return no saturation, not raise errors."""
        g2 = np.array([], dtype=np.float64)
        is_saturated, meta = self.mod.detect_observed_saturation(g2)
        self.assertFalse(is_saturated)


class TestSaturatedByConstructionRegime(unittest.TestCase):
    """Tests simulating the SATURATED_BY_CONSTRUCTION regime (8 events)."""

    def setUp(self):
        self.mod = _load_realdata_bridge()

    def test_monomodal_high_q_with_omega_v1_produces_saturated_g2(self):
        """
        A monomodal high-Q event with omega_dom_v1 produces saturated G2.
        This simulates SATURATED_BY_CONSTRUCTION like GW200129_065458.
        """
        # Single pole, very high Q (effectively monomodal)
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

        # Should be detected as saturated
        is_saturated, meta = self.mod.detect_observed_saturation(g2)

        self.assertTrue(is_saturated, "Monomodal high-Q with omega_v1 should be saturated")
        self.assertGreater(meta["g2_last"], 0.99)
        self.assertEqual(meta["n_ge_threshold"], meta["n_points"])

    def test_monomodal_high_q_with_gamma_v2_produces_decay(self):
        """
        The same monomodal high-Q event with gamma_dom_v2 shows proper decay.
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

        # Should NOT be saturated
        is_saturated, meta = self.mod.detect_observed_saturation(g2)

        self.assertFalse(is_saturated, "Monomodal high-Q with gamma_v2 should decay properly")
        self.assertLess(meta["g2_last"], 1e-4)


class TestHighTailNonSaturatedRegime(unittest.TestCase):
    """Tests simulating the HIGH_TAIL_NON_SATURATED regime (55 events)."""

    def setUp(self):
        self.mod = _load_realdata_bridge()

    def test_high_tail_multimodal_is_not_detected_as_saturated(self):
        """
        HIGH_TAIL events have g2_last in [0.12, 0.86].
        They should NOT trigger autoselect because they are not fully saturated.
        """
        # Multimodal with interference causing some decay but high tail
        freq_1 = 200.0
        omega_dom = 2.0 * math.pi * freq_1
        Q = 15000  # High Q but multimodal
        gamma_1 = omega_dom / (2.0 * Q)

        poles = [
            self.mod.Pole(freq_hz=freq_1, damping_1_over_s=gamma_1, amp_abs=1.0),
            self.mod.Pole(freq_hz=freq_1 * 1.05, damping_1_over_s=gamma_1 * 1.1, amp_abs=0.8),
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

        is_saturated, meta = self.mod.detect_observed_saturation(g2)

        # Even if g2_last is high, if not ALL points are >= 0.99, not saturated
        # The multimodal interference should cause some oscillation/decay
        self.assertFalse(is_saturated, "HIGH_TAIL multimodal should not be detected as saturated")


class TestPassCorridorRegression(unittest.TestCase):
    """Regression tests to ensure PASS-25 corridor is not affected."""

    def setUp(self):
        self.mod = _load_realdata_bridge()

    def test_multimodal_event_with_high_q_not_saturated(self):
        """
        PASS events can have high Q but multimodal content causes decay.
        GW200302_015811 has Q=327989 but is PASS with g2_last=0.09.
        The key is multimodal interference breaking coherence.
        """
        # Simulate multimodal high-Q event that decays due to interference
        freq_1 = 100.0
        omega_dom = 2.0 * math.pi * freq_1
        Q = 50000  # Very high Q
        gamma_dom = omega_dom / (2.0 * Q)

        # Multiple modes with different frequencies cause beating/interference
        poles = [
            self.mod.Pole(freq_hz=freq_1, damping_1_over_s=gamma_dom, amp_abs=1.0),
            self.mod.Pole(freq_hz=freq_1 * 0.7, damping_1_over_s=gamma_dom * 1.5, amp_abs=0.7),
            self.mod.Pole(freq_hz=freq_1 * 1.4, damping_1_over_s=gamma_dom * 0.8, amp_abs=0.5),
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

        is_saturated, meta = self.mod.detect_observed_saturation(g2)

        self.assertFalse(is_saturated, "Multimodal high-Q should NOT be detected as saturated")
        # The interference should cause enough variation that not all points are >= 0.99
        self.assertLess(meta["fraction_ge_threshold"], 1.0)

    def test_typical_pass_event_shows_clear_decay(self):
        """
        Typical PASS events (like GW150914) show clear decay with g2_last << 0.12.
        """
        # Simulate typical BBH merger with moderate Q and clear multimodal structure
        freq_1 = 250.0
        omega_dom = 2.0 * math.pi * freq_1
        Q = 2000
        gamma_dom = omega_dom / (2.0 * Q)

        # Rich multimodal structure
        poles = [
            self.mod.Pole(freq_hz=freq_1, damping_1_over_s=gamma_dom, amp_abs=1.0),
            self.mod.Pole(freq_hz=freq_1 * 0.6, damping_1_over_s=gamma_dom * 2.0, amp_abs=0.5),
            self.mod.Pole(freq_hz=freq_1 * 1.5, damping_1_over_s=gamma_dom * 0.7, amp_abs=0.3),
            self.mod.Pole(freq_hz=freq_1 * 0.8, damping_1_over_s=gamma_dom * 1.3, amp_abs=0.4),
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

        is_saturated, meta = self.mod.detect_observed_saturation(g2)

        self.assertFalse(is_saturated, "Typical PASS should not be saturated")
        # Should have meaningful decay
        self.assertLess(meta["g2_last"], 0.5, "PASS-like event should show decay")


class TestContractConstants(unittest.TestCase):
    """Verify contract constants are correctly defined."""

    def setUp(self):
        self.mod = _load_realdata_bridge()

    def test_saturation_thresholds(self):
        """Default saturation thresholds should be 0.99 and 1.0."""
        self.assertEqual(self.mod.SATURATION_TAIL_THRESHOLD, 0.99)
        self.assertEqual(self.mod.SATURATION_FRACTION_THRESHOLD, 1.0)

    def test_resolve_contract_for_gamma_v2(self):
        """gamma_dom_v2 should resolve to xgamma_6_v2 contract."""
        contract, x_max = self.mod.resolve_g2_repr_contract(
            self.mod.G2_TIME_CONTRACT_GAMMA_DOM_V2
        )
        self.assertEqual(contract, "xgamma_6_v2")
        self.assertEqual(x_max, 6.0)


class TestTracingAttributes(unittest.TestCase):
    """Verify that tracing attributes are correctly set."""

    def setUp(self):
        self.mod = _load_realdata_bridge()

    def test_saturation_meta_contains_expected_keys(self):
        """Saturation metadata should contain all expected keys."""
        g2 = np.ones(100, dtype=np.float64) * 0.995
        _, meta = self.mod.detect_observed_saturation(g2)

        expected_keys = [
            "g2_last",
            "n_points",
            "n_ge_threshold",
            "fraction_ge_threshold",
            "tail_threshold",
            "fraction_threshold",
        ]
        for key in expected_keys:
            self.assertIn(key, meta, f"Missing key: {key}")


if __name__ == "__main__":
    unittest.main()
