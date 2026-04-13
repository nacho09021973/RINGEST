"""
Tests for the Delta_UV contract in 06_build_bulk_eigenmodes_dataset.py.

Verifies that:
  - No fallback silencioso a Δ = d when uv_exponents is missing
  - No fallback silencioso a Δ = d when uv_exponents collapses to d (near-zero eigenvalues)
  - Real UV values propagate correctly when present
  - JSON output preserves None / null (no replacement by d)
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
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _load_stage06():
    name = "stage06_delta_uv_contract_test"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(
        name, REPO_ROOT / "06_build_bulk_eigenmodes_dataset.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _make_h5(path: Path, d: int = 4) -> None:
    with h5py.File(path, "w") as f:
        f.attrs["system_name"] = path.stem
        f.attrs["family"] = "test_family"
        f.attrs["d"] = d
        f.attrs["z_dyn"] = 1.0
        f.attrs["theta"] = 0.0
        f.create_dataset("z_grid", data=np.linspace(0.01, 1.0, 50))
        f.create_dataset("A_emergent", data=np.linspace(0.0, 0.5, 50))
        f.create_dataset("f_emergent", data=np.linspace(1.0, 0.8, 50))


def _run_stage06(stage06, tmp_root: Path, solver_stub, n_eigs: int = 2, delta_uv_source: str = "solver"):
    """Helper: wires a solver stub, runs main(), returns (exit_code, meta, json_data)."""
    stage06.bss = solver_stub

    runs_dir = tmp_root / "runs"
    geom_dir = runs_dir / "test_exp" / "02_emergent_geometry_engine" / "geometry_emergent"
    geom_dir.mkdir(parents=True, exist_ok=True)

    h5_path = geom_dir / "sys_a.h5"
    _make_h5(h5_path, d=4)

    out_dir = runs_dir / "test_exp" / "06_build_bulk_eigenmodes_dataset"
    out_json = out_dir / "bulk_modes_dataset.json"

    argv = [
        "06_build_bulk_eigenmodes_dataset.py",
        "--runs-dir", str(runs_dir),
        "--experiment", "test_exp",
        "--n-eigs", str(n_eigs),
        "--delta-uv-source", delta_uv_source,
        "--output-json", str(out_json),
    ]
    with patch.object(sys, "argv", argv):
        exit_code = stage06.main()

    meta_path = out_dir / "bulk_modes_meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
    json_data = json.loads(out_json.read_text()) if out_json.exists() else {}
    return exit_code, meta, json_data


class TestSolverDeltaDoesNotDefaultToD(unittest.TestCase):
    """When uv_exponents is missing from the solver spec, Delta_UV must be None."""

    def test_solver_delta_does_not_default_to_d(self):
        stage06 = _load_stage06()
        stub = types.SimpleNamespace(
            __name__="stub_no_uv",
            solve_geometry=lambda **_: {
                "lambda_sl": [1.5, 3.7],
                # uv_exponents deliberately absent
            },
        )
        with tempfile.TemporaryDirectory() as tmp:
            ec, meta, jdata = _run_stage06(stage06, Path(tmp), stub)

        self.assertEqual(ec, 0)
        # Every Delta_bulk_uv entry must be None
        for sys_entry in jdata.get("systems", []):
            for delta in sys_entry.get("Delta_bulk_uv", []):
                self.assertIsNone(delta, f"Expected None but got {delta!r}")

        # delta_source in stats: solver_extractions must be 0
        stats = meta.get("delta_extraction", {}).get("stats", {})
        self.assertEqual(stats.get("solver_extractions", -1), 0)
        self.assertGreater(stats.get("no_delta", 0), 0)


class TestSolverDeltaNoneWhenUVMissing(unittest.TestCase):
    """Near-zero eigenvalues produce uv_exponents == [d, d, …] → must become None."""

    def test_solver_delta_none_when_eigenvalues_near_zero(self):
        stage06 = _load_stage06()
        # Eigenvalues so small that (d + sqrt(d² + 4λ))/2 == d in float64
        near_zero_lambdas = [7.878e-24, 5.119e-23, 2.3e-22, 1.1e-21]
        d = 4
        uv_collapsed = [float(d)] * len(near_zero_lambdas)

        stub = types.SimpleNamespace(
            __name__="stub_collapsed_uv",
            solve_geometry=lambda **_: {
                "lambda_sl": near_zero_lambdas,
                "uv_exponents": uv_collapsed,
            },
        )
        with tempfile.TemporaryDirectory() as tmp:
            ec, meta, jdata = _run_stage06(stage06, Path(tmp), stub, n_eigs=4)

        self.assertEqual(ec, 0)

        # All deltas must be None
        for sys_entry in jdata.get("systems", []):
            for delta in sys_entry.get("Delta_bulk_uv", []):
                self.assertIsNone(delta, f"Got {delta!r}, expected None for collapsed uv_exponents")

        # Audit metadata must flag the system as collapsed
        audit = meta.get("uv_exponents_audit", {})
        self.assertTrue(audit, "uv_exponents_audit must be present in meta")
        for sys_name, sys_audit in audit.items():
            self.assertTrue(sys_audit["suspicious"], f"{sys_name}: audit should be suspicious")
            self.assertTrue(sys_audit["all_equal_d"])
            self.assertIn("all_values_equal_d", sys_audit["reason"])

        # solver_uv_collapsed counter must be > 0
        stats = meta.get("delta_extraction", {}).get("stats", {})
        self.assertGreater(stats.get("solver_uv_collapsed", 0), 0)


class TestSolverDeltaUsesUVExponentsWhenPresent(unittest.TestCase):
    """When uv_exponents has real (non-d) values, they must propagate to Delta_UV."""

    def test_solver_delta_uses_uv_exponents_when_present(self):
        stage06 = _load_stage06()
        real_deltas = [4.5, 5.2]  # above d=4, genuinely different
        stub = types.SimpleNamespace(
            __name__="stub_real_uv",
            solve_geometry=lambda **_: {
                "lambda_sl": [1.5, 3.7],
                "uv_exponents": real_deltas,
            },
        )
        with tempfile.TemporaryDirectory() as tmp:
            ec, meta, jdata = _run_stage06(stage06, Path(tmp), stub)

        self.assertEqual(ec, 0)

        collected = []
        for sys_entry in jdata.get("systems", []):
            collected.extend(sys_entry.get("Delta_bulk_uv", []))

        self.assertTrue(len(collected) > 0, "Should have at least one Delta entry")
        for delta in collected:
            self.assertIsNotNone(delta)
            self.assertIn(round(delta, 6), [round(v, 6) for v in real_deltas])

        stats = meta.get("delta_extraction", {}).get("stats", {})
        self.assertGreater(stats.get("solver_extractions", 0), 0)
        self.assertEqual(stats.get("solver_uv_collapsed", 0), 0)


class TestBulkModesJsonPreservesNoneDelta(unittest.TestCase):
    """The JSON aggregator must keep None/null, never replace with a numeric default."""

    def test_bulk_modes_json_preserves_none_delta(self):
        stage06 = _load_stage06()
        # No uv_exponents — all deltas should be null in the output JSON
        stub = types.SimpleNamespace(
            __name__="stub_no_delta_json",
            solve_geometry=lambda **_: {
                "lambda_sl": [2.0, 3.5, 5.1],
            },
        )
        with tempfile.TemporaryDirectory() as tmp:
            ec, meta, jdata = _run_stage06(stage06, Path(tmp), stub, n_eigs=3)

        self.assertEqual(ec, 0)

        # Check raw JSON text: no occurrence of "4.0" as a delta value
        # (the lambdas may contain floats, but delta should be null)
        for sys_entry in jdata.get("systems", []):
            delta_list = sys_entry.get("Delta_bulk_uv", [])
            self.assertTrue(
                all(v is None for v in delta_list),
                f"Delta_bulk_uv should be all null, got: {delta_list}",
            )


class TestAuditUVExponents(unittest.TestCase):
    """Unit tests for the audit_uv_exponents helper itself."""

    def setUp(self):
        self.stage06 = _load_stage06()

    def test_empty_list(self):
        r = self.stage06.audit_uv_exponents([], 4)
        self.assertFalse(r["suspicious"])
        self.assertEqual(r["n_values"], 0)

    def test_all_equal_d_is_suspicious(self):
        r = self.stage06.audit_uv_exponents([4.0, 4.0, 4.0], 4)
        self.assertTrue(r["suspicious"])
        self.assertTrue(r["all_equal_d"])
        self.assertEqual(r["n_equal_d"], 3)

    def test_real_values_not_suspicious(self):
        r = self.stage06.audit_uv_exponents([4.5, 5.2, 6.1], 4)
        self.assertFalse(r["suspicious"])
        self.assertEqual(r["n_equal_d"], 0)

    def test_all_identical_not_d_is_suspicious(self):
        r = self.stage06.audit_uv_exponents([5.5, 5.5, 5.5], 4)
        self.assertTrue(r["suspicious"])
        self.assertTrue(r["all_identical"])
        self.assertFalse(r["all_equal_d"])

    def test_mixed_partial_d_not_suspicious(self):
        # Only some are d — not flagged as suspicious (mixed data may be legit)
        r = self.stage06.audit_uv_exponents([4.0, 5.2], 4)
        self.assertFalse(r["suspicious"])
        self.assertEqual(r["n_equal_d"], 1)


if __name__ == "__main__":
    unittest.main()
