"""
tests/test_feature_support.py

Regression tests for the feature support audit and inference gate.

All tests use synthetic data — no real checkpoints or H5 files required.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# Bootstrap: ensure repo root is on sys.path so feature_support is importable
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from feature_support import (
    CRITICAL_FEATURES,
    FEATURE_NAMES_V2_5,
    QNM_F1F0_SANE_MAX,
    QNM_F1F0_SANE_MIN,
    TINY_STD_THRESHOLD,
    audit_feature_support,
    audit_train_feature_support,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

N = len(FEATURE_NAMES_V2_5)  # 20

def _make_normal_stats() -> tuple[np.ndarray, np.ndarray]:
    """Return (X_mean, X_std) where all stds are well above tiny threshold."""
    mu = np.ones(N, dtype=float)
    sigma = np.ones(N, dtype=float)  # std=1 for all features
    return mu, sigma


def _feature_idx(name: str) -> int:
    return list(FEATURE_NAMES_V2_5).index(name)


# ---------------------------------------------------------------------------
# Test 1: tiny std flags correctly for QNM + has_horizon
# ---------------------------------------------------------------------------

class TestTinyStdFlagsQNMAndHorizon(unittest.TestCase):
    """
    Synthetic case where has_horizon, qnm_Q0, qnm_f1f0, qnm_g1g0 have tiny
    train std.  The audit must mark each as train_std_tiny=True and the
    verdict must be FAIL (they are critical features).
    """

    def setUp(self):
        self.mu, self.sigma = _make_normal_stats()
        # Freeze the four critical features to near-zero std
        for name in ("has_horizon", "qnm_Q0", "qnm_f1f0", "qnm_g1g0"):
            self.sigma[_feature_idx(name)] = 1e-9  # well below TINY_STD_THRESHOLD

        # A plausible feature vector (values don't matter much — std is tiny)
        self.x = np.ones(N, dtype=float)

    def test_tiny_std_marked_per_feature(self):
        report = audit_feature_support(
            feature_vector=self.x,
            X_mean=self.mu,
            X_std=self.sigma,
            feature_names=FEATURE_NAMES_V2_5,
        )
        tiny_names = {r.feature for r in report.rows if r.train_std_tiny}
        for name in ("has_horizon", "qnm_Q0", "qnm_f1f0", "qnm_g1g0"):
            self.assertIn(name, tiny_names, f"{name} should be marked train_std_tiny")

    def test_n_tiny_std_count(self):
        report = audit_feature_support(
            feature_vector=self.x,
            X_mean=self.mu,
            X_std=self.sigma,
            feature_names=FEATURE_NAMES_V2_5,
        )
        self.assertGreaterEqual(report.n_tiny_std, 4)

    def test_verdict_is_fail(self):
        report = audit_feature_support(
            feature_vector=self.x,
            X_mean=self.mu,
            X_std=self.sigma,
            feature_names=FEATURE_NAMES_V2_5,
        )
        self.assertEqual(report.verdict, "FAIL")

    def test_critical_features_triggered(self):
        report = audit_feature_support(
            feature_vector=self.x,
            X_mean=self.mu,
            X_std=self.sigma,
            feature_names=FEATURE_NAMES_V2_5,
        )
        for name in ("has_horizon", "qnm_Q0", "qnm_f1f0", "qnm_g1g0"):
            self.assertIn(name, report.critical_features_triggered)

    def test_verdict_reason_contains_unsupported(self):
        report = audit_feature_support(
            feature_vector=self.x,
            X_mean=self.mu,
            X_std=self.sigma,
            feature_names=FEATURE_NAMES_V2_5,
        )
        self.assertIn("UNSUPPORTED_FEATURE_REGIME", report.verdict_reason)

    def test_z_score_is_none_for_tiny_std(self):
        report = audit_feature_support(
            feature_vector=self.x,
            X_mean=self.mu,
            X_std=self.sigma,
            feature_names=FEATURE_NAMES_V2_5,
        )
        for r in report.rows:
            if r.feature in ("has_horizon", "qnm_Q0", "qnm_f1f0", "qnm_g1g0"):
                self.assertIsNone(r.z_score, f"{r.feature} z_score should be None")


# ---------------------------------------------------------------------------
# Test 2: off-support and clip_risk for G2_large_x
# ---------------------------------------------------------------------------

class TestOffSupportG2LargeX(unittest.TestCase):
    """
    Synthetic case where G2_large_x has |z| > 5 (off-support) or |z| > 10 (clip_risk).
    """

    def _report_with_z(self, z_target: float):
        mu, sigma = _make_normal_stats()
        idx = _feature_idx("G2_large_x")
        x_mean = 1.0
        x_std = 1.0
        mu[idx] = x_mean
        sigma[idx] = x_std
        x = np.ones(N, dtype=float)
        x[idx] = x_mean + z_target * x_std  # ensures exact z
        return audit_feature_support(
            feature_vector=x,
            X_mean=mu,
            X_std=sigma,
            feature_names=FEATURE_NAMES_V2_5,
        )

    def test_off_support_at_z_6(self):
        report = self._report_with_z(6.0)
        row = next(r for r in report.rows if r.feature == "G2_large_x")
        self.assertTrue(row.off_support_abs_z_gt_5)
        self.assertFalse(row.clip_risk_abs_z_gt_10)

    def test_clip_risk_at_z_11(self):
        report = self._report_with_z(11.0)
        row = next(r for r in report.rows if r.feature == "G2_large_x")
        self.assertTrue(row.off_support_abs_z_gt_5)
        self.assertTrue(row.clip_risk_abs_z_gt_10)

    def test_verdict_fail_at_z_6_because_critical(self):
        # G2_large_x is critical; |z|=6 > 5 → FAIL
        report = self._report_with_z(6.0)
        self.assertEqual(report.verdict, "FAIL")
        self.assertIn("G2_large_x", report.critical_features_triggered)

    def test_verdict_fail_at_z_11_clip_risk(self):
        report = self._report_with_z(11.0)
        self.assertEqual(report.verdict, "FAIL")

    def test_pass_at_z_3(self):
        report = self._report_with_z(3.0)
        row = next(r for r in report.rows if r.feature == "G2_large_x")
        self.assertFalse(row.off_support_abs_z_gt_5)
        self.assertFalse(row.clip_risk_abs_z_gt_10)
        self.assertEqual(report.verdict, "PASS")

    def test_z_score_value_matches(self):
        report = self._report_with_z(6.0)
        row = next(r for r in report.rows if r.feature == "G2_large_x")
        self.assertAlmostEqual(row.z_score, 6.0, places=10)


# ---------------------------------------------------------------------------
# Test 3: inference gate blocks on unsupported regime
# ---------------------------------------------------------------------------

class TestInferenceGateBlocks(unittest.TestCase):
    """
    The gate must return FAIL when a critical feature has tiny std OR abs(z) > 5.
    """

    def test_blocks_on_critical_tiny_std(self):
        mu, sigma = _make_normal_stats()
        sigma[_feature_idx("has_horizon")] = 1e-12  # tiny
        x = np.ones(N, dtype=float)
        report = audit_feature_support(
            feature_vector=x, X_mean=mu, X_std=sigma, feature_names=FEATURE_NAMES_V2_5
        )
        self.assertEqual(report.verdict, "FAIL")
        self.assertIn("UNSUPPORTED_FEATURE_REGIME", report.verdict_reason)
        self.assertIn("has_horizon", report.critical_features_triggered)

    def test_blocks_on_critical_off_support(self):
        mu, sigma = _make_normal_stats()
        idx = _feature_idx("qnm_Q0")
        mu[idx] = 0.0
        sigma[idx] = 1.0
        x = np.ones(N, dtype=float)
        x[idx] = 7.0  # z = 7 > 5
        report = audit_feature_support(
            feature_vector=x, X_mean=mu, X_std=sigma, feature_names=FEATURE_NAMES_V2_5
        )
        self.assertEqual(report.verdict, "FAIL")
        self.assertIn("qnm_Q0", report.critical_features_triggered)

    def test_blocks_on_any_clip_risk(self):
        # Non-critical feature but |z| > 10 → FAIL
        mu, sigma = _make_normal_stats()
        idx = _feature_idx("G2_log_slope")  # non-critical
        mu[idx] = 0.0
        sigma[idx] = 1.0
        x = np.ones(N, dtype=float)
        x[idx] = 15.0  # z = 15 > 10
        report = audit_feature_support(
            feature_vector=x, X_mean=mu, X_std=sigma, feature_names=FEATURE_NAMES_V2_5
        )
        self.assertEqual(report.verdict, "FAIL")

    def test_warn_on_noncritical_tiny_std_only(self):
        mu, sigma = _make_normal_stats()
        # Freeze a non-critical feature
        sigma[_feature_idx("G2_log_slope")] = 1e-12
        x = np.ones(N, dtype=float)
        report = audit_feature_support(
            feature_vector=x, X_mean=mu, X_std=sigma, feature_names=FEATURE_NAMES_V2_5
        )
        self.assertEqual(report.verdict, "WARN")

    def test_pass_on_normal_data(self):
        mu, sigma = _make_normal_stats()
        x = np.ones(N, dtype=float)  # all z-scores = 0
        report = audit_feature_support(
            feature_vector=x, X_mean=mu, X_std=sigma, feature_names=FEATURE_NAMES_V2_5
        )
        self.assertEqual(report.verdict, "PASS")

    def test_to_dict_is_serialisable(self):
        import json
        mu, sigma = _make_normal_stats()
        x = np.ones(N, dtype=float)
        report = audit_feature_support(
            feature_vector=x, X_mean=mu, X_std=sigma, feature_names=FEATURE_NAMES_V2_5
        )
        d = report.to_dict()
        # Should not raise
        json.dumps(d)
        self.assertIn("verdict", d)
        self.assertIn("rows", d)
        self.assertEqual(len(d["rows"]), N)


# ---------------------------------------------------------------------------
# Test 4: train summary contains feature support audit section
# ---------------------------------------------------------------------------

class TestTrainSummaryContainsAudit(unittest.TestCase):
    """
    audit_train_feature_support must return a dict with all required keys.
    When critical features have tiny std, verdict must be FAIL.
    """

    def test_audit_contains_all_keys(self):
        mu = np.ones(N, dtype=float)
        sigma = np.ones(N, dtype=float)
        result = audit_train_feature_support(
            feature_names=FEATURE_NAMES_V2_5,
            X_mean=mu,
            X_std=sigma,
        )
        for key in (
            "feature_names",
            "X_mean",
            "X_std",
            "tiny_std_features",
            "critical_tiny_std_features",
            "verdict",
            "verdict_reason",
        ):
            self.assertIn(key, result, f"Missing key: {key}")

    def test_feature_names_match(self):
        mu = np.ones(N, dtype=float)
        sigma = np.ones(N, dtype=float)
        result = audit_train_feature_support(
            feature_names=FEATURE_NAMES_V2_5,
            X_mean=mu,
            X_std=sigma,
        )
        self.assertEqual(result["feature_names"], list(FEATURE_NAMES_V2_5))

    def test_x_std_listed_per_feature(self):
        mu = np.ones(N, dtype=float)
        sigma = np.linspace(0.5, 2.0, N)
        result = audit_train_feature_support(
            feature_names=FEATURE_NAMES_V2_5,
            X_mean=mu,
            X_std=sigma,
        )
        self.assertEqual(len(result["X_std"]), N)
        np.testing.assert_allclose(result["X_std"], sigma.tolist(), rtol=1e-10)

    def test_pass_when_all_stds_healthy(self):
        mu = np.ones(N, dtype=float)
        sigma = np.ones(N, dtype=float)
        result = audit_train_feature_support(
            feature_names=FEATURE_NAMES_V2_5,
            X_mean=mu,
            X_std=sigma,
        )
        self.assertEqual(result["verdict"], "PASS")
        self.assertEqual(result["tiny_std_features"], [])
        self.assertEqual(result["critical_tiny_std_features"], [])

    def test_fail_when_critical_std_tiny(self):
        mu = np.ones(N, dtype=float)
        sigma = np.ones(N, dtype=float)
        for name in ("qnm_Q0", "has_horizon"):
            sigma[_feature_idx(name)] = 0.0  # frozen in train
        result = audit_train_feature_support(
            feature_names=FEATURE_NAMES_V2_5,
            X_mean=mu,
            X_std=sigma,
        )
        self.assertEqual(result["verdict"], "FAIL")
        self.assertIn("qnm_Q0", result["critical_tiny_std_features"])
        self.assertIn("has_horizon", result["critical_tiny_std_features"])

    def test_warn_when_only_noncritical_std_tiny(self):
        mu = np.ones(N, dtype=float)
        sigma = np.ones(N, dtype=float)
        sigma[_feature_idx("G2_log_slope")] = 0.0  # non-critical, frozen
        result = audit_train_feature_support(
            feature_names=FEATURE_NAMES_V2_5,
            X_mean=mu,
            X_std=sigma,
        )
        self.assertEqual(result["verdict"], "WARN")
        self.assertIn("G2_log_slope", result["tiny_std_features"])
        self.assertEqual(result["critical_tiny_std_features"], [])


# ---------------------------------------------------------------------------
# Test 5: qnm_f1f0 semantic sanity guardrail
# ---------------------------------------------------------------------------

class TestQnmF1F0SemanticGuardrail(unittest.TestCase):
    """
    The audit must emit a semantic_warning for qnm_f1f0 when the value is
    outside plausible physical bounds (possible pole-ordering inversion).
    This is a guardrail, not a physics assertion — it does not trigger FAIL
    on its own (the verdict depends on other gate rules).
    """

    def _report_with_f1f0(self, value: float):
        mu, sigma = _make_normal_stats()
        idx = _feature_idx("qnm_f1f0")
        mu[idx] = 5.0   # plausible training mean
        sigma[idx] = 1.0
        x = np.ones(N, dtype=float)
        x[idx] = value
        return audit_feature_support(
            feature_vector=x, X_mean=mu, X_std=sigma, feature_names=FEATURE_NAMES_V2_5
        )

    def test_no_warning_in_sane_range(self):
        # 8.4 is the observed GW150914 value — within [0.5, 20]
        report = self._report_with_f1f0(8.4068)
        row = next(r for r in report.rows if r.feature == "qnm_f1f0")
        self.assertIsNone(row.semantic_warning)

    def test_warning_below_min(self):
        report = self._report_with_f1f0(QNM_F1F0_SANE_MIN - 0.1)
        row = next(r for r in report.rows if r.feature == "qnm_f1f0")
        self.assertIsNotNone(row.semantic_warning)
        self.assertIn("pole-ordering", row.semantic_warning)

    def test_warning_above_max(self):
        report = self._report_with_f1f0(QNM_F1F0_SANE_MAX + 1.0)
        row = next(r for r in report.rows if r.feature == "qnm_f1f0")
        self.assertIsNotNone(row.semantic_warning)
        self.assertIn("QNM computation pipeline", row.semantic_warning)

    def test_value_8_4_produces_large_z_from_zero_mean_train(self):
        """
        Reproduce the GW150914 audit finding: if qnm_f1f0 has tiny train std
        (mean=0, std~1e-8), the gate must flag it as critical train_std_tiny.
        This is the exact scenario observed in the audit.
        """
        mu, sigma = _make_normal_stats()
        idx = _feature_idx("qnm_f1f0")
        mu[idx] = 0.0
        sigma[idx] = 1e-8  # frozen in train (TINY_STD)
        x = np.ones(N, dtype=float)
        x[idx] = 8.4068  # real GW150914 value
        report = audit_feature_support(
            feature_vector=x, X_mean=mu, X_std=sigma, feature_names=FEATURE_NAMES_V2_5
        )
        row = next(r for r in report.rows if r.feature == "qnm_f1f0")
        self.assertTrue(row.train_std_tiny)
        self.assertIsNone(row.z_score)
        self.assertEqual(report.verdict, "FAIL")
        self.assertIn("qnm_f1f0", report.critical_features_triggered)


# ---------------------------------------------------------------------------
# Test 6: stage-level hard-fail contract (inference + train raise on failure)
# ---------------------------------------------------------------------------

def _load_engine():
    """Load 02_emergent_geometry_engine as a module (cached after first load)."""
    key = "engine_stage02_for_contract_test"
    if key not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            key, REPO_ROOT / "02_emergent_geometry_engine.py"
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules[key] = mod
        spec.loader.exec_module(mod)
    return sys.modules[key]


class TestStageLevelHardFail(unittest.TestCase):
    """
    Verify that:
    - run_inference_mode raises RuntimeError("UNSUPPORTED_FEATURE_REGIME…")
      when _n_gate_fail > 0 (gate blocked ≥1 system).
    - run_train_mode raises RuntimeError("TRAIN_FEATURE_SUPPORT_FAIL…")
      when audit verdict == "FAIL" (critical feature frozen in train).

    Both tests use synthetic in-memory data — no real checkpoints or H5 files.
    The RuntimeError propagates to main()'s except block, which sets
    STATUS_ERROR + EXIT_ERROR and writes stage_summary with status=ERROR.
    """

    # ------------------------------------------------------------------
    # Inference: run_inference_mode raises on gate fail
    # ------------------------------------------------------------------

    def test_inference_raises_on_gate_fail(self):
        """
        Build a minimal synthetic scenario (tempdir + manifest + H5 + checkpoint)
        where audit_feature_support returns FAIL for every system.
        run_inference_mode must raise RuntimeError containing
        "UNSUPPORTED_FEATURE_REGIME".
        """
        import json
        import tempfile
        import types
        import unittest.mock as mock
        import torch
        import h5py

        engine = _load_engine()

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            data_dir = tmp / "data"
            data_dir.mkdir()
            out_dir = tmp / "out"
            out_dir.mkdir()

            # Minimal H5 with a boundary group
            h5_path = data_dir / "sys_a.h5"
            with h5py.File(h5_path, "w") as f:
                bg = f.create_group("boundary")
                bg.create_dataset("x_grid", data=np.linspace(0.1, 10, 10))
                bg.create_dataset("G2_scalar", data=np.ones(10))
                bg.attrs["temperature"] = 0.0
                bg.attrs["qnm_Q0"] = 0.0
                bg.attrs["qnm_f1f0"] = 0.0
                bg.attrs["qnm_g1g0"] = 0.0
                f.attrs["operators"] = "[]"

            # Manifest pointing to sys_a
            (data_dir / "geometries_manifest.json").write_text(
                json.dumps({"geometries": [{"name": "sys_a", "d": 4}]})
            )

            # Minimal checkpoint (hidden_dim/n_layers must match the saved state_dict)
            ckpt_path = tmp / "model.pt"
            n_features = N  # 20
            n_z = 50
            _hidden_dim = 64
            _n_layers = 2
            torch.save({
                "model_state_dict": engine.EmergentGeometryNet(
                    n_features=n_features, n_z=n_z,
                    hidden_dim=_hidden_dim, n_layers=_n_layers,
                ).state_dict(),
                "n_features": n_features,
                "n_z": n_z,
                "hidden_dim": _hidden_dim,
                "n_layers": _n_layers,
                "family_map": {"ads": 0, "lifshitz": 1, "hyperscaling": 2,
                               "deformed": 3, "unknown": 4},
                "X_mean": np.zeros((1, n_features)),
                "X_std": np.ones((1, n_features)),
                "normalizer": {},
                "z_grid": np.linspace(0.01, 5.0, n_z),
                "d": 4,
            }, ckpt_path)

            # Fake args
            args = types.SimpleNamespace(
                checkpoint=str(ckpt_path),
                data_dir=str(data_dir),
                output_dir=str(out_dir),
                device="cpu",
                verbose=False,
                mode="inference",
            )

            # Patch audit_feature_support (in engine's namespace) to always FAIL
            fail_report = engine.audit_feature_support(
                feature_vector=np.ones(n_features),
                X_mean=np.zeros(n_features),
                X_std=np.full(n_features, 1e-9),   # all tiny → FAIL
                feature_names=list(FEATURE_NAMES_V2_5),
            )
            self.assertEqual(fail_report.verdict, "FAIL")  # sanity-check fixture

            # h5py is normally imported into engine globals by main(); inject it here
            import h5py as _h5py
            engine.h5py = _h5py

            with mock.patch.object(engine, "audit_feature_support",
                                   return_value=fail_report):
                with self.assertRaises(RuntimeError) as ctx:
                    engine.run_inference_mode(args)

        self.assertIn("UNSUPPORTED_FEATURE_REGIME", str(ctx.exception))

    # ------------------------------------------------------------------
    # Train: run_train_mode raises on audit fail
    # ------------------------------------------------------------------

    def test_train_raises_on_audit_fail(self):
        """
        Build a minimal synthetic training set where a critical feature
        (has_horizon, index 10) is constant → X_std_raw[10] = 0.
        run_train_mode must raise RuntimeError containing
        "TRAIN_FEATURE_SUPPORT_FAIL".
        """
        import json
        import tempfile
        import types
        import h5py

        engine = _load_engine()

        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            data_dir = tmp / "data"
            data_dir.mkdir()
            out_dir = tmp / "out"
            out_dir.mkdir()

            n_z = 20
            z_grid = np.linspace(0.01, 1.0, n_z).astype(np.float32)

            # Two "known" geometries: has_horizon=0 in both → std=0
            names = ["geo_0", "geo_1"]
            for name in names:
                h5_path = data_dir / f"{name}.h5"
                with h5py.File(h5_path, "w") as f:
                    bg = f.create_group("boundary")
                    bg.create_dataset("x_grid", data=np.linspace(0.1, 10, 30))
                    g2 = np.exp(-np.linspace(0.1, 10, 30))
                    bg.create_dataset("G2_scalar", data=g2)
                    # has_horizon intentionally constant (0) across all samples
                    bg.attrs["temperature"] = 0.0
                    bg.attrs["qnm_Q0"] = 0.0
                    bg.attrs["qnm_f1f0"] = 0.0
                    bg.attrs["qnm_g1g0"] = 0.0
                    f.attrs["operators"] = "[]"
                    f.attrs["family"] = b"ads"
                    f.attrs["d"] = 4

                    bt = f.create_group("bulk_truth")
                    bt.create_dataset("A_truth", data=np.ones(n_z, dtype=np.float32))
                    bt.create_dataset("f_truth", data=np.ones(n_z, dtype=np.float32) * 0.8)
                    bt.create_dataset("R_truth", data=np.ones(n_z, dtype=np.float32) * -12.0)
                    bt.create_dataset("z_grid", data=z_grid)
                    bt.attrs["z_h"] = 0.0
                    bt.attrs["family"] = b"ads"
                    bt.attrs["d"] = 4

            (data_dir / "geometries_manifest.json").write_text(json.dumps({
                "geometries": [
                    {"name": "geo_0", "category": "known"},
                    {"name": "geo_1", "category": "known"},
                ]
            }))

            args = types.SimpleNamespace(
                data_dir=str(data_dir),
                output_dir=str(out_dir),
                n_epochs=1,
                device="cpu",
                hidden_dim=32,
                n_layers=1,
                batch_size=2,
                seed=0,
                verbose=False,
                lr=1e-3,
                mode="train",
            )

            # h5py is normally imported into engine globals by main(); inject it here
            import h5py as _h5py
            engine.h5py = _h5py

            with self.assertRaises(RuntimeError) as ctx:
                engine.run_train_mode(args)

        self.assertIn("TRAIN_FEATURE_SUPPORT_FAIL", str(ctx.exception))


# ---------------------------------------------------------------------------
# Test 7: main() exits with EXIT_ERROR (3), not with the generic code 1
# ---------------------------------------------------------------------------

class TestMainExitCode(unittest.TestCase):
    """
    Verify that main() calls sys.exit(EXIT_ERROR=3) — not leaves an unhandled
    exception that Python maps to exit code 1 — when run_inference_mode raises
    RuntimeError("UNSUPPORTED_FEATURE_REGIME…").

    The fix: the except block in main() must NOT re-raise after setting
    exit_code = EXIT_ERROR, so the finally block can write the summary and
    sys.exit(EXIT_ERROR) can execute.
    """

    def test_main_exits_with_EXIT_ERROR_not_1(self):
        import types
        import unittest.mock as mock

        engine = _load_engine()

        # Fake StageContext: enough to let main() run through try/except/finally
        fake_ctx = mock.MagicMock()
        fake_ctx.stage_dir = Path("/tmp")
        fake_ctx.run_root = Path("/tmp")

        with mock.patch.object(
                engine, "parse_stage_args",
                return_value=types.SimpleNamespace(
                    mode="inference",
                    data_dir="/tmp",
                    output_dir="/tmp",
                )), \
             mock.patch.object(engine, "StageContext") as mock_ctx_cls, \
             mock.patch.object(
                engine, "run_inference_mode",
                side_effect=RuntimeError("UNSUPPORTED_FEATURE_REGIME: test")), \
             mock.patch("sys.exit") as mock_exit:

            mock_ctx_cls.from_args.return_value = fake_ctx

            engine.main()

        mock_exit.assert_called_once_with(engine.EXIT_ERROR)
        self.assertEqual(mock_exit.call_args[0][0], 3,
                         "EXIT_ERROR must be 3, not the generic 1")


# ---------------------------------------------------------------------------
# Tests 8–11: V3 contract (Camino C2 — QNM block removed)
# ---------------------------------------------------------------------------

from feature_support import (  # noqa: E402 (after conditional imports above)
    FEATURE_NAMES_V3,
    CRITICAL_FEATURES_V3,
)

N_V3 = len(FEATURE_NAMES_V3)  # must be 17


def _make_normal_stats_v3() -> tuple[np.ndarray, np.ndarray]:
    mu = np.ones(N_V3, dtype=float)
    sigma = np.ones(N_V3, dtype=float)
    return mu, sigma


def _feature_idx_v3(name: str) -> int:
    return list(FEATURE_NAMES_V3).index(name)


class TestFeatureVectorV3ExcludesQNMBlock(unittest.TestCase):
    """
    build_feature_vector_v3 must:
    - return exactly 17 features
    - not include qnm_Q0, qnm_f1f0, qnm_g1g0 in FEATURE_NAMES_V3
    """

    def test_feature_names_v3_length(self):
        self.assertEqual(N_V3, 17)

    def test_qnm_names_absent_from_v3(self):
        for name in ("qnm_Q0", "qnm_f1f0", "qnm_g1g0"):
            self.assertNotIn(name, FEATURE_NAMES_V3,
                             f"{name} must not appear in FEATURE_NAMES_V3")

    def test_build_feature_vector_v3_returns_17(self):
        engine = _load_engine()
        bd = {
            "x_grid": np.linspace(0.1, 10, 30),
            "G2_scalar": np.exp(-np.linspace(0.1, 10, 30)),
            "temperature": 0.0,
            # qnm attrs present in boundary data but must NOT be picked up
            "qnm_Q0": 1124.9,
            "qnm_f1f0": 8.41,
            "qnm_g1g0": 1.58,
            "d": 4,
        }
        X = engine.build_feature_vector_v3(bd, [])
        self.assertEqual(len(X), 17,
                         f"build_feature_vector_v3 returned {len(X)} features, expected 17")

    def test_build_feature_vector_v3_ignores_qnm_values(self):
        """
        Even when qnm_* attrs are present with extreme values (GW150914 regime),
        the V3 vector must be unaffected.
        """
        engine = _load_engine()
        bd_base = {
            "x_grid": np.linspace(0.1, 10, 30),
            "G2_scalar": np.exp(-np.linspace(0.1, 10, 30)),
            "temperature": 0.5,
            "d": 4,
        }
        bd_with_qnm = dict(bd_base, qnm_Q0=1124.9, qnm_f1f0=8.41, qnm_g1g0=1.58)
        X_base = engine.build_feature_vector_v3(bd_base, [])
        X_qnm  = engine.build_feature_vector_v3(bd_with_qnm, [])
        np.testing.assert_array_equal(
            X_base, X_qnm,
            err_msg="V3 vector must not change when qnm_* attrs are present",
        )


class TestFeatureSupportV3CriticalSetUpdated(unittest.TestCase):
    """
    CRITICAL_FEATURES_V3 must:
    - contain has_horizon and G2_large_x
    - not contain qnm_Q0, qnm_f1f0, qnm_g1g0
    """

    def test_has_horizon_is_critical_v3(self):
        self.assertIn("has_horizon", CRITICAL_FEATURES_V3)

    def test_G2_large_x_is_critical_v3(self):
        self.assertIn("G2_large_x", CRITICAL_FEATURES_V3)

    def test_qnm_features_not_critical_v3(self):
        for name in ("qnm_Q0", "qnm_f1f0", "qnm_g1g0"):
            self.assertNotIn(name, CRITICAL_FEATURES_V3,
                             f"{name} must not be critical under V3 contract")

    def test_gate_fails_on_has_horizon_freeze_v3(self):
        """has_horizon is still critical in V3 — tiny std must FAIL."""
        mu, sigma = _make_normal_stats_v3()
        sigma[_feature_idx_v3("has_horizon")] = 1e-9
        x = np.ones(N_V3, dtype=float)
        report = audit_feature_support(
            feature_vector=x, X_mean=mu, X_std=sigma,
            feature_names=FEATURE_NAMES_V3,
            critical_features=CRITICAL_FEATURES_V3,
        )
        self.assertEqual(report.verdict, "FAIL")
        self.assertIn("has_horizon", report.critical_features_triggered)

    def test_gate_fails_on_G2_large_x_off_support_v3(self):
        mu, sigma = _make_normal_stats_v3()
        idx = _feature_idx_v3("G2_large_x")
        x = np.ones(N_V3, dtype=float)
        x[idx] = 1.0 + 7.0 * 1.0  # z = 7 > 5
        report = audit_feature_support(
            feature_vector=x, X_mean=mu, X_std=sigma,
            feature_names=FEATURE_NAMES_V3,
            critical_features=CRITICAL_FEATURES_V3,
        )
        self.assertEqual(report.verdict, "FAIL")
        self.assertIn("G2_large_x", report.critical_features_triggered)


class TestTrainFeatureSupportV3PassesWithoutQNMFreeze(unittest.TestCase):
    """
    Under V3, a dataset where qnm_* would have been frozen (all zeros)
    must NOT cause a FAIL verdict — because qnm_* are absent from the contract.
    Under V2_5, the same dataset would have caused FAIL.
    """

    def _make_dataset_with_frozen_qnm(self):
        """
        Simulate: all holographic training data, has_horizon varies, qnm all zero.
        Under V2_5 this causes FAIL (qnm_Q0/f1f0/g1g0 frozen in critical features).
        Under V3 this must PASS (those features are not in the contract).
        """
        rng = np.random.default_rng(42)
        n = 80
        # 17 features: 9 correlator + 4 thermal + 2 GR + 2 global
        X = rng.normal(size=(n, N_V3))
        # has_horizon (index 10 in V3) has real variance
        X[:, _feature_idx_v3("has_horizon")] = rng.integers(0, 2, size=n).astype(float)
        # G2_large_x has real variance
        X[:, _feature_idx_v3("G2_large_x")] = rng.uniform(0.0, 1.0, size=n)
        return X

    def test_v3_audit_passes_when_qnm_would_have_frozen_under_v2(self):
        X = self._make_dataset_with_frozen_qnm()
        result = audit_train_feature_support(
            feature_names=FEATURE_NAMES_V3,
            X_mean=X.mean(axis=0),
            X_std=X.std(axis=0),
            critical_features=CRITICAL_FEATURES_V3,
        )
        self.assertEqual(result["verdict"], "PASS",
                         f"V3 audit must PASS; got {result['verdict_reason']}")
        self.assertEqual(result["critical_tiny_std_features"], [])

    def test_v2_audit_would_have_failed_same_data(self):
        """
        Confirm the V2_5 equivalent dataset (same layout, qnm cols at zero std)
        WOULD fail under V2_5 — proving V3 is a genuine fix, not an accidental pass.
        """
        rng = np.random.default_rng(42)
        n = 80
        X_v2 = rng.normal(size=(n, N))  # N=20 (V2_5)
        # Freeze qnm_* (all zeros → std=0)
        for name in ("qnm_Q0", "qnm_f1f0", "qnm_g1g0"):
            X_v2[:, _feature_idx(name)] = 0.0
        result_v2 = audit_train_feature_support(
            feature_names=FEATURE_NAMES_V2_5,
            X_mean=X_v2.mean(axis=0),
            X_std=X_v2.std(axis=0),
        )
        self.assertEqual(result_v2["verdict"], "FAIL",
                         "V2_5 audit must FAIL with frozen qnm_* — sanity check")


class TestInferenceProbeV3ContractNoQNMDependency(unittest.TestCase):
    """
    Minimal pipeline test: run_inference_mode under V3 contract must complete
    without raising RuntimeError when the feature vector is within support,
    even if qnm_* boundary attrs have extreme values (GW150914 regime).
    """

    def test_inference_passes_with_real_like_qnm_values(self):
        """
        Boundary data with qnm_Q0=1124, qnm_f1f0=8.4 (GW150914 regime).
        Under V3 the gate does not see those values — must not FAIL.
        """
        import json, tempfile, types, torch, h5py

        engine = _load_engine()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_p = Path(tmp)
            data_dir = tmp_p / "data"
            data_dir.mkdir()
            out_dir = tmp_p / "out"
            out_dir.mkdir()

            # H5 with real-like qnm values but well-behaved G2
            h5_path = data_dir / "real_like.h5"
            x_grid = np.linspace(0.1, 10, 30)
            g2 = np.exp(-x_grid)
            with h5py.File(h5_path, "w") as f:
                bg = f.create_group("boundary")
                bg.create_dataset("x_grid", data=x_grid)
                bg.create_dataset("G2_scalar", data=g2)
                bg.attrs["temperature"] = 0.0
                bg.attrs["qnm_Q0"]   = 1124.9   # GW150914 value — must be ignored by V3
                bg.attrs["qnm_f1f0"] = 8.41
                bg.attrs["qnm_g1g0"] = 1.58
                bg.attrs["d"]        = 4
                f.attrs["operators"] = "[]"

            (data_dir / "geometries_manifest.json").write_text(
                json.dumps({"geometries": [{"name": "real_like", "d": 4}]})
            )

            # Checkpoint sized for 17 features (V3)
            n_features = N_V3
            n_z = 30
            _hidden_dim = 32
            _n_layers = 1
            # Build X_mean / X_std that keep the probe in-support
            X_mean_ckpt = np.zeros((1, n_features))
            X_std_ckpt  = np.ones((1, n_features))

            _family_map = {"ads": 0, "lifshitz": 1, "hyperscaling": 2, "deformed": 3, "unknown": 4}
            ckpt_path = tmp_p / "model_v3.pt"
            torch.save({
                "model_state_dict": engine.EmergentGeometryNet(
                    n_features=n_features, n_z=n_z,
                    hidden_dim=_hidden_dim, n_layers=_n_layers,
                    n_families=len(_family_map),
                ).state_dict(),
                "n_features": n_features,
                "n_z": n_z,
                "hidden_dim": _hidden_dim,
                "n_layers": _n_layers,
                "family_map": _family_map,
                "X_mean": X_mean_ckpt,
                "X_std":  X_std_ckpt,
                "normalizer": {},
                "z_grid": np.linspace(0.01, 5.0, n_z),
                "d": 4,
            }, ckpt_path)

            args = types.SimpleNamespace(
                checkpoint=str(ckpt_path),
                data_dir=str(data_dir),
                output_dir=str(out_dir),
                device="cpu",
                verbose=False,
                mode="inference",
            )

            import h5py as _h5py
            engine.h5py = _h5py

            # Must not raise — gate should PASS because G2/thermal features are in-support
            # and qnm_* values are invisible to the V3 gate
            try:
                engine.run_inference_mode(args)
            except RuntimeError as exc:
                self.fail(f"run_inference_mode raised unexpectedly under V3 contract: {exc}")

    def test_inference_summary_records_feature_contract_v3(self):
        """
        emergent_geometry_summary.json written by run_inference_mode must
        include feature_contract == 'v3'.
        """
        import json, tempfile, types, torch, h5py

        engine = _load_engine()

        with tempfile.TemporaryDirectory() as tmp:
            tmp_p = Path(tmp)
            data_dir = tmp_p / "data"
            data_dir.mkdir()
            out_dir = tmp_p / "out"
            out_dir.mkdir()

            h5_path = data_dir / "geo.h5"
            x_grid = np.linspace(0.1, 10, 30)
            with h5py.File(h5_path, "w") as f:
                bg = f.create_group("boundary")
                bg.create_dataset("x_grid", data=x_grid)
                bg.create_dataset("G2_scalar", data=np.exp(-x_grid))
                bg.attrs["temperature"] = 0.0
                bg.attrs["d"] = 4
                f.attrs["operators"] = "[]"

            (data_dir / "geometries_manifest.json").write_text(
                json.dumps({"geometries": [{"name": "geo", "d": 4}]})
            )

            n_features = N_V3
            n_z = 20
            _fm2 = {"ads": 0, "lifshitz": 1, "hyperscaling": 2, "deformed": 3, "unknown": 4}
            ckpt_path = tmp_p / "model_v3.pt"
            torch.save({
                "model_state_dict": engine.EmergentGeometryNet(
                    n_features=n_features, n_z=n_z, hidden_dim=32, n_layers=1,
                    n_families=len(_fm2),
                ).state_dict(),
                "n_features": n_features, "n_z": n_z,
                "hidden_dim": 32, "n_layers": 1,
                "family_map": _fm2, "X_mean": np.zeros((1, n_features)),
                "X_std": np.ones((1, n_features)), "normalizer": {},
                "z_grid": np.linspace(0.01, 5.0, n_z), "d": 4,
            }, ckpt_path)

            args = types.SimpleNamespace(
                checkpoint=str(ckpt_path), data_dir=str(data_dir),
                output_dir=str(out_dir), device="cpu", verbose=False, mode="inference",
            )

            import h5py as _h5py
            engine.h5py = _h5py

            try:
                engine.run_inference_mode(args)
            except RuntimeError:
                pass  # gate fail is OK for this test — we just check the summary

            summary_path = out_dir / "emergent_geometry_summary.json"
            self.assertTrue(summary_path.exists(), "summary JSON must be written")
            summary = json.loads(summary_path.read_text())
            self.assertEqual(summary.get("feature_contract"), "v3",
                             "summary must record feature_contract = 'v3'")
            self.assertEqual(summary.get("n_features"), N_V3,
                             f"summary n_features must be {N_V3}")


if __name__ == "__main__":
    unittest.main()
