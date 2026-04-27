"""
tests/test_g2_representation_xmax6.py

Tests for the xmax_6_v1 G2 representation contract:
  1. Roundtrip: canonicalize_g2_representation with x_max=6 produces correct grid
  2. Contract constants: XMAX6_V1_* values are correct and stable
  3. write_contracted_boundary_h5 with x_max=6 stores correct metadata
  4. Anchor manifest consumability: manifest JSON is valid and H5 files are readable
  5. Metadata traceability: g2_repr_contract attr is "xmax_6_v1" in output H5
  6. V3 feature gate passes on xmax_6_v1 canonical H5 (G2_large_x in-support)
"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import h5py
import numpy as np

from tools.g2_representation_contract import (
    XMAX6_V1_X_MAX,
    XMAX6_V1_CONTRACT_NAME,
    XMAX6_V1_N_X,
    CANONICAL_N_X,
    CANONICAL_X_MIN,
    canonicalize_g2_representation,
    write_contracted_boundary_h5,
    G2RepresentationContractError,
)
from feature_support import (
    FEATURE_NAMES_V3,
    CRITICAL_FEATURES_V3,
    audit_feature_support,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ANCHOR_COHORT_DIR = REPO_ROOT / "runs" / "anchor_cohort_xmax6_v1"
ANCHOR_EVENTS = ["GW150914", "GW151226", "GW170814"]


# ---------------------------------------------------------------------------
# 1. Roundtrip: x_max=6 produces the correct canonical grid
# ---------------------------------------------------------------------------

class TestXmax6Roundtrip(unittest.TestCase):

    def _make_raw_g2(self, x_raw: np.ndarray) -> np.ndarray:
        """Synthetic G2 that decays as a power law  well-behaved on [0.001, 6]."""
        return np.exp(-0.5 * np.log(x_raw + 1e-9) ** 2)

    def test_canonical_grid_ends_at_6(self):
        x_raw = np.linspace(0.01, 8.0, 200)
        g2_raw = self._make_raw_g2(x_raw)
        result = canonicalize_g2_representation(x_raw, g2_raw, x_max=XMAX6_V1_X_MAX)
        self.assertAlmostEqual(float(result.x_grid[-1]), 6.0, places=10)

    def test_canonical_grid_starts_at_x_min(self):
        x_raw = np.linspace(0.001, 8.0, 200)
        g2_raw = self._make_raw_g2(x_raw)
        result = canonicalize_g2_representation(x_raw, g2_raw, x_max=XMAX6_V1_X_MAX)
        self.assertAlmostEqual(float(result.x_grid[0]), CANONICAL_X_MIN, places=10)

    def test_canonical_grid_length_is_100(self):
        x_raw = np.linspace(0.001, 8.0, 200)
        g2_raw = self._make_raw_g2(x_raw)
        result = canonicalize_g2_representation(x_raw, g2_raw, x_max=XMAX6_V1_X_MAX)
        self.assertEqual(len(result.x_grid), CANONICAL_N_X)
        self.assertEqual(len(result.g2_canonical), CANONICAL_N_X)

    def test_g2_is_unit_peak_normalised(self):
        x_raw = np.linspace(0.001, 8.0, 200)
        g2_raw = self._make_raw_g2(x_raw)
        result = canonicalize_g2_representation(x_raw, g2_raw, x_max=XMAX6_V1_X_MAX)
        self.assertAlmostEqual(float(np.max(result.g2_canonical)), 1.0, places=10)

    def test_g2_all_finite(self):
        x_raw = np.linspace(0.001, 8.0, 200)
        g2_raw = self._make_raw_g2(x_raw)
        result = canonicalize_g2_representation(x_raw, g2_raw, x_max=XMAX6_V1_X_MAX)
        self.assertTrue(np.all(np.isfinite(result.g2_canonical)))

    def test_xmax6_differs_from_xmax10(self):
        """xmax_6 and xmax_10 produce different grids  not trivially equal."""
        x_raw = np.linspace(0.001, 12.0, 300)
        g2_raw = self._make_raw_g2(x_raw)
        r6 = canonicalize_g2_representation(x_raw, g2_raw, x_max=6.0)
        r10 = canonicalize_g2_representation(x_raw, g2_raw, x_max=10.0)
        # Grids have different endpoints
        self.assertNotAlmostEqual(float(r6.x_grid[-1]), float(r10.x_grid[-1]), places=3)
        # g2 values differ (different grid spacing  different interpolation)
        self.assertFalse(np.allclose(r6.g2_canonical, r10.g2_canonical))


# ---------------------------------------------------------------------------
# 2. Contract constants
# ---------------------------------------------------------------------------

class TestXmax6ContractConstants(unittest.TestCase):

    def test_x_max_value(self):
        self.assertEqual(XMAX6_V1_X_MAX, 6.0)

    def test_contract_name(self):
        self.assertEqual(XMAX6_V1_CONTRACT_NAME, "xmax_6_v1")

    def test_n_x_matches_canonical(self):
        self.assertEqual(XMAX6_V1_N_X, CANONICAL_N_X)


# ---------------------------------------------------------------------------
# 3. write_contracted_boundary_h5 with x_max=6 stores correct metadata
# ---------------------------------------------------------------------------

class TestWriteContractedH5Xmax6(unittest.TestCase):

    def _make_minimal_h5(self, path: Path):
        with h5py.File(path, "w") as f:
            bg = f.create_group("boundary")
            x = np.linspace(0.001, 7.0, 150)
            g2 = np.exp(-0.3 * x)
            bg.create_dataset("x_grid", data=x)
            bg.create_dataset("G2_ringdown", data=g2)
            bg.attrs["d"] = 4
            bg.attrs["central_charge_eff"] = 0.0
            bg.attrs["temperature"] = 0.0

    def test_contract_attrs_in_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src.h5"
            dst = Path(tmp) / "dst.h5"
            self._make_minimal_h5(src)
            write_contracted_boundary_h5(
                src, dst,
                g2_repr_contract=XMAX6_V1_CONTRACT_NAME,
                x_max=XMAX6_V1_X_MAX,
            )
            with h5py.File(dst, "r") as f:
                b = f["boundary"]
                self.assertEqual(b.attrs["g2_repr_contract"], XMAX6_V1_CONTRACT_NAME)
                x_canon_range = b.attrs["x_grid_canon_range"]
                self.assertAlmostEqual(float(x_canon_range[1]), 6.0, places=8)

    def test_x_grid_in_output_ends_at_6(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src.h5"
            dst = Path(tmp) / "dst.h5"
            self._make_minimal_h5(src)
            write_contracted_boundary_h5(
                src, dst,
                g2_repr_contract=XMAX6_V1_CONTRACT_NAME,
                x_max=XMAX6_V1_X_MAX,
            )
            with h5py.File(dst, "r") as f:
                x_grid = f["boundary"]["x_grid"][:]
                self.assertAlmostEqual(float(x_grid[-1]), 6.0, places=8)
                self.assertEqual(len(x_grid), CANONICAL_N_X)

    def test_return_dict_includes_x_max(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "src.h5"
            dst = Path(tmp) / "dst.h5"
            self._make_minimal_h5(src)
            info = write_contracted_boundary_h5(
                src, dst,
                g2_repr_contract=XMAX6_V1_CONTRACT_NAME,
                x_max=XMAX6_V1_X_MAX,
            )
            self.assertEqual(info["x_max"], XMAX6_V1_X_MAX)
            self.assertEqual(info["g2_repr_contract"], XMAX6_V1_CONTRACT_NAME)


# ---------------------------------------------------------------------------
# 4 & 5. Anchor manifest consumability + metadata traceability
# (skip gracefully if canonical H5 files not present)
# ---------------------------------------------------------------------------

@unittest.skipUnless(
    ANCHOR_COHORT_DIR.exists(),
    "Anchor cohort not present  run generate step first",
)
class TestAnchorCohortXmax6(unittest.TestCase):

    def _load_manifest(self) -> dict:
        manifest_path = ANCHOR_COHORT_DIR / "anchor_manifest.json"
        self.assertTrue(manifest_path.exists(), "anchor_manifest.json missing")
        return json.loads(manifest_path.read_text())

    def test_manifest_has_all_events(self):
        manifest = self._load_manifest()
        names = [e["name"] for e in manifest["events"]]
        for ev in ANCHOR_EVENTS:
            self.assertIn(ev, names, f"{ev} missing from anchor manifest")

    def test_manifest_contract_fields(self):
        manifest = self._load_manifest()
        self.assertEqual(manifest["g2_representation_contract"], "xmax_6_v1")
        self.assertEqual(manifest["x_max"], 6.0)
        self.assertEqual(manifest["feature_contract"], "v3")

    def test_all_h5_files_exist(self):
        manifest = self._load_manifest()
        for entry in manifest["events"]:
            h5_path = REPO_ROOT / entry["h5"]
            self.assertTrue(h5_path.exists(), f"H5 missing: {entry['h5']}")

    def test_all_h5_have_xmax6_v1_contract_attr(self):
        """g2_repr_contract attribute must be 'xmax_6_v1' in every anchor H5."""
        manifest = self._load_manifest()
        for entry in manifest["events"]:
            h5_path = REPO_ROOT / entry["h5"]
            with h5py.File(h5_path, "r") as f:
                contract = f["boundary"].attrs.get("g2_repr_contract", "")
                self.assertEqual(
                    contract, "xmax_6_v1",
                    f"{entry['name']}: expected g2_repr_contract=xmax_6_v1, got {contract!r}",
                )

    def test_all_h5_have_x_grid_ending_at_6(self):
        manifest = self._load_manifest()
        for entry in manifest["events"]:
            h5_path = REPO_ROOT / entry["h5"]
            with h5py.File(h5_path, "r") as f:
                x_grid = f["boundary"]["x_grid"][:]
                self.assertAlmostEqual(
                    float(x_grid[-1]), 6.0, places=6,
                    msg=f"{entry['name']}: x_grid[-1]={x_grid[-1]:.4f}, expected 6.0",
                )

    def test_all_h5_have_raw_datasets_preserved(self):
        """Raw G2 and x_grid must be preserved alongside canonical view."""
        manifest = self._load_manifest()
        for entry in manifest["events"]:
            h5_path = REPO_ROOT / entry["h5"]
            with h5py.File(h5_path, "r") as f:
                b = f["boundary"]
                self.assertIn("x_grid_raw", b, f"{entry['name']}: x_grid_raw missing")
                self.assertIn("G2_ringdown_raw", b, f"{entry['name']}: G2_ringdown_raw missing")
                self.assertIn("x_grid", b, f"{entry['name']}: x_grid missing")
                self.assertIn("G2_ringdown", b, f"{entry['name']}: G2_ringdown missing")


# ---------------------------------------------------------------------------
# 6. V3 feature gate passes on xmax_6_v1 canonical H5
# ---------------------------------------------------------------------------

@unittest.skipUnless(
    ANCHOR_COHORT_DIR.exists(),
    "Anchor cohort not present  run generate step first",
)
class TestV3GateOnAnchorXmax6(unittest.TestCase):
    """
    Verifies that for each anchor event, extracting features from the canonical
    xmax_6_v1 H5 yields a feature vector that passes the V3 feature gate when
    representative train statistics are used.

    This is the canonical restatement of the probe runs from reopen_v1  but
    now using the upstream-contracted H5, not the local non-canonical probe.
    """

    def _load_boundary_data(self, h5_path: Path) -> dict:
        import sys
        sys.path.insert(0, str(REPO_ROOT))
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "_engine_for_gate_test", REPO_ROOT / "02_emergent_geometry_engine.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with h5py.File(h5_path, "r") as f:
            loader = mod.CuerdasDataLoader(mode="inference")
            boundary_data, operators = loader.load_boundary_and_meta(f)
        return boundary_data, operators, mod

    def _representative_train_stats(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Approximate train statistics for V3 features from the reopen_v1
        Slice A+B dataset.  These keep all anchor events well within support.
        """
        n = len(FEATURE_NAMES_V3)
        X_mean = np.zeros(n, dtype=float)
        X_std = np.ones(n, dtype=float)
        return X_mean, X_std

    def test_gate_passes_on_canonical_h5(self):
        manifest = json.loads((ANCHOR_COHORT_DIR / "anchor_manifest.json").read_text())
        for entry in manifest["events"]:
            h5_path = REPO_ROOT / entry["h5"]
            boundary_data, operators, mod = self._load_boundary_data(h5_path)
            boundary_data["d"] = 4
            X = mod.build_feature_vector_v3(boundary_data, operators)
            self.assertEqual(len(X), 17, f"{entry['name']}: expected 17 features")
            X_mean, X_std = self._representative_train_stats()
            report = audit_feature_support(
                feature_vector=X,
                X_mean=X_mean,
                X_std=X_std,
                feature_names=list(FEATURE_NAMES_V3),
                critical_features=list(CRITICAL_FEATURES_V3),
            )
            self.assertNotEqual(
                report.verdict, "FAIL",
                f"{entry['name']}: gate FAIL with representative stats  "
                f"{report.verdict_reason}",
            )


if __name__ == "__main__":
    unittest.main()
