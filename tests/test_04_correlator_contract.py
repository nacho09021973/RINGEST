"""
tests/test_04_correlator_contract.py

Tests for the ringdown-inference relaxed correlator contract in stage 04.

Contract: when mode="inference" and category="ringdown", has_power_law and
is_monotonic_decay are WARN/N_A and do not block generic_passed.
has_spatial_structure remains required for all modes.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_stage04():
    key = "stage04_for_test"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            key, REPO_ROOT / "04_geometry_physics_contracts.py"
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return sys.modules[key]


def _make_correlator_contract(
    has_spatial_structure: bool,
    is_monotonic_decay: bool,
    has_power_law: bool,
    contract_mode: str = None,
):
    s04 = _load_stage04()
    mode = contract_mode or s04.CORRELATOR_CONTRACT_STANDARD
    return s04.CorrelatorStructureContract(
        has_spatial_structure=has_spatial_structure,
        is_monotonic_decay=is_monotonic_decay,
        has_power_law=has_power_law,
        log_slope=-0.05,
        correlation_quality=0.3,
        skipped=False,
        contract_mode=mode,
    )


# ---------------------------------------------------------------------------
# 1. Ringdown inference: has_power_law=False is NOT blocking
# ---------------------------------------------------------------------------

class TestRingdownInferencePowerLawNotBlocking(unittest.TestCase):
    """
    When contract_mode=ringdown_inference_relaxed_v1:
    - passed = has_spatial_structure only
    - has_power_law=False does NOT cause failure
    - is_monotonic_decay=False does NOT cause failure
    """

    def setUp(self):
        self.s04 = _load_stage04()
        self.relaxed = self.s04.CORRELATOR_CONTRACT_RINGDOWN_INFERENCE

    def test_power_law_false_does_not_fail_in_relaxed_mode(self):
        c = _make_correlator_contract(
            has_spatial_structure=True,
            is_monotonic_decay=True,
            has_power_law=False,
            contract_mode=self.relaxed,
        )
        self.assertTrue(c.passed,
                        "has_power_law=False must not block in ringdown_inference_relaxed mode")

    def test_monotonic_decay_false_does_not_fail_in_relaxed_mode(self):
        c = _make_correlator_contract(
            has_spatial_structure=True,
            is_monotonic_decay=False,
            has_power_law=False,
            contract_mode=self.relaxed,
        )
        self.assertTrue(c.passed,
                        "is_monotonic_decay=False must not block in ringdown_inference_relaxed mode")

    def test_no_spatial_structure_still_fails_in_relaxed_mode(self):
        """has_spatial_structure=False must block even in relaxed mode."""
        c = _make_correlator_contract(
            has_spatial_structure=False,
            is_monotonic_decay=True,
            has_power_law=False,
            contract_mode=self.relaxed,
        )
        self.assertFalse(c.passed,
                         "has_spatial_structure=False must block even in relaxed mode")

    def test_contract_mode_field_is_preserved(self):
        c = _make_correlator_contract(
            has_spatial_structure=True,
            is_monotonic_decay=True,
            has_power_law=False,
            contract_mode=self.relaxed,
        )
        self.assertEqual(c.contract_mode, self.relaxed)


# ---------------------------------------------------------------------------
# 2. Standard mode keeps original strictness
# ---------------------------------------------------------------------------

class TestStandardModeKeepsStrictness(unittest.TestCase):
    """
    Outside ringdown inference:
    - has_power_law=False causes failure
    - This verifies the relaxation is scoped correctly
    """

    def setUp(self):
        self.s04 = _load_stage04()

    def test_power_law_false_fails_in_standard_mode(self):
        c = _make_correlator_contract(
            has_spatial_structure=True,
            is_monotonic_decay=True,
            has_power_law=False,
            contract_mode=self.s04.CORRELATOR_CONTRACT_STANDARD,
        )
        self.assertFalse(c.passed,
                         "has_power_law=False must FAIL in standard mode")

    def test_power_law_true_passes_in_standard_mode(self):
        c = _make_correlator_contract(
            has_spatial_structure=True,
            is_monotonic_decay=True,
            has_power_law=True,
            contract_mode=self.s04.CORRELATOR_CONTRACT_STANDARD,
        )
        self.assertTrue(c.passed)

    def test_default_contract_mode_is_standard(self):
        c = _make_correlator_contract(
            has_spatial_structure=True,
            is_monotonic_decay=True,
            has_power_law=False,
        )
        self.assertEqual(c.contract_mode, self.s04.CORRELATOR_CONTRACT_STANDARD)
        self.assertFalse(c.passed)


# ---------------------------------------------------------------------------
# 3. Output JSON marks relaxed contract mode
# ---------------------------------------------------------------------------

class TestContractSummaryMarksRelaxedMode(unittest.TestCase):
    """
    The serialised output (via asdict) must include contract_mode per geometry.
    The summary must include n_ringdown_inference_relaxed_correlator.
    """

    def setUp(self):
        self.s04 = _load_stage04()

    def test_contract_mode_survives_asdict(self):
        from dataclasses import asdict
        c = _make_correlator_contract(
            has_spatial_structure=True,
            is_monotonic_decay=True,
            has_power_law=False,
            contract_mode=self.s04.CORRELATOR_CONTRACT_RINGDOWN_INFERENCE,
        )
        d = asdict(c)
        self.assertIn("contract_mode", d)
        self.assertEqual(d["contract_mode"], self.s04.CORRELATOR_CONTRACT_RINGDOWN_INFERENCE)

    def test_summary_json_has_n_ringdown_inference_field(self):
        """
        The canonical anchor cohort summary must include the traceability field.
        (Skipped if file not present  integration test.)
        """
        summary_path = (
            REPO_ROOT
            / "runs/reopen_v1/04_geometry_physics_contracts/geometry_contracts_summary.json"
        )
        if not summary_path.exists():
            self.skipTest("Anchor cohort summary not generated yet")
        summary = json.loads(summary_path.read_text())
        self.assertIn(
            "n_ringdown_inference_relaxed_correlator",
            summary,
            "summary must include n_ringdown_inference_relaxed_correlator",
        )
        self.assertEqual(
            summary["n_ringdown_inference_relaxed_correlator"],
            summary["n_total"],
            "all anchor events must use relaxed correlator contract",
        )

    def test_summary_json_phase_passed(self):
        summary_path = (
            REPO_ROOT
            / "runs/reopen_v1/04_geometry_physics_contracts/geometry_contracts_summary.json"
        )
        if not summary_path.exists():
            self.skipTest("Anchor cohort summary not generated yet")
        summary = json.loads(summary_path.read_text())
        self.assertTrue(summary["phase_passed"])
        self.assertEqual(summary["n_generic_passed"], summary["n_total"])
        self.assertEqual(summary["n_overall_passed"], summary["n_total"])

    def test_each_contract_has_relaxed_mode_and_warning(self):
        summary_path = (
            REPO_ROOT
            / "runs/reopen_v1/04_geometry_physics_contracts/geometry_contracts_summary.json"
        )
        if not summary_path.exists():
            self.skipTest("Anchor cohort summary not generated yet")
        summary = json.loads(summary_path.read_text())
        relaxed = self.s04.CORRELATOR_CONTRACT_RINGDOWN_INFERENCE
        for c in summary["contracts"]:
            cs = c["correlator_structure"]
            self.assertEqual(
                cs["contract_mode"], relaxed,
                f"{c['name']}: expected contract_mode={relaxed}, got {cs['contract_mode']}",
            )
            warning_texts = " ".join(c.get("warnings", []))
            self.assertIn(
                relaxed, warning_texts,
                f"{c['name']}: warning must mention {relaxed}",
            )


# ---------------------------------------------------------------------------
# 4. Manifest: geometries_manifest.json accepted (E)
# ---------------------------------------------------------------------------

class TestGeometriesManifestAccepted(unittest.TestCase):
    """
    Stage 04 must accept geometries_manifest.json (stage-02 convention)
    in addition to manifest.json, without emitting a warning.
    """

    def test_geometries_manifest_path_checked_first(self):
        import tempfile, types
        s04 = _load_stage04()
        # Verify the code path: if geometries_manifest.json exists, it's found before manifest.json
        with tempfile.TemporaryDirectory() as tmp:
            tmp_p = Path(tmp)
            (tmp_p / "geometries_manifest.json").write_text(
                json.dumps({"geometries": [{"name": "test_geo"}]})
            )
            # Read the source to confirm geometries_manifest is checked first
            src = (REPO_ROOT / "04_geometry_physics_contracts.py").read_text()
            # The check must appear before manifest.json in source order
            idx_geo = src.index("geometries_manifest.json")
            idx_man = src.index('"manifest.json"')
            self.assertLess(
                idx_geo, idx_man,
                "geometries_manifest.json must be checked before manifest.json in source",
            )


if __name__ == "__main__":
    unittest.main()
