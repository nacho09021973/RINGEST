from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_module(module_name: str, relative_path: str):
    module_path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class FocusedSandboxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sandbox = load_module("sandbox_stage01", "01_generate_sandbox_geometries.py")
        cls.engine = load_module("engine_stage02", "02_emergent_geometry_engine.py")

    def test_sandbox_cli_defaults_preserve_retrocompatibility(self):
        args = self.sandbox.build_parser().parse_args([])
        self.assertFalse(args.focused_real_regime)
        self.assertEqual(args.focused_d, 4)
        self.assertEqual(tuple(args.focused_families), self.sandbox.DEFAULT_FOCUSED_FAMILIES)
        self.assertEqual(args.zh_min, 1.0)
        self.assertEqual(args.zh_max, 1.2)
        self.assertEqual(args.out_of_support_frac, 0.0)

    def test_focused_mode_restricts_families_and_fixes_d(self):
        rng = np.random.default_rng(7)
        cfg = self.sandbox.FocusedSamplingConfig(
            enabled=True,
            families=("ads", "lifshitz", "hyperscaling"),
            d=4,
            zh_min=1.0,
            zh_max=1.2,
            out_of_support_frac=0.0,
            out_of_support_zh_min=0.8,
            out_of_support_zh_max=2.0,
        )
        base_geometries = [
            (geo, cat)
            for (geo, cat) in self.sandbox.get_phase11_geometries()
            if geo.family in cfg.families
        ]

        self.assertTrue(base_geometries)
        self.assertTrue(all(geo.family in cfg.families for geo, _ in base_geometries))

        focused_instances = [
            self.sandbox.make_geometry_instance(geo, cat, idx, rng, focused_config=cfg)
            for idx, (geo, cat) in enumerate(base_geometries)
        ]

        self.assertTrue(all(geo.family in cfg.families for geo in focused_instances))
        self.assertTrue(all(geo.d == 4 for geo in focused_instances))
        self.assertTrue(all(1.0 <= geo.z_h <= 1.2 for geo in focused_instances if geo.z_h is not None))
        self.assertTrue(all("_d4_" in geo.name or geo.name.endswith("_d4") for geo in focused_instances))
        self.assertTrue(
            all(geo.metadata.get("sampling_regime") == "focused_real_regime" for geo in focused_instances)
        )

    def test_focused_out_of_support_fraction_is_explicit_and_bounded(self):
        rng = np.random.default_rng(11)
        cfg = self.sandbox.FocusedSamplingConfig(
            enabled=True,
            families=("ads",),
            d=4,
            zh_min=1.0,
            zh_max=1.2,
            out_of_support_frac=0.25,
            out_of_support_zh_min=0.8,
            out_of_support_zh_max=1.4,
        )

        samples = [self.sandbox.sample_focused_zh(rng, cfg) for _ in range(200)]
        zh_values = [zh for zh, _ in samples]
        focused_values = [zh for zh, is_oos in samples if not is_oos]
        oos_values = [zh for zh, is_oos in samples if is_oos]

        self.assertTrue(all(0.8 <= zh <= 1.4 for zh in zh_values))
        self.assertTrue(all(1.0 <= zh <= 1.2 for zh in focused_values))
        self.assertTrue(all((0.8 <= zh < 1.0) or (1.2 < zh <= 1.4) for zh in oos_values))
        self.assertGreater(len(oos_values), 0)

    def test_engine_cli_and_finetune_hook(self):
        parser = self.engine.build_parser()
        args_train = parser.parse_args(["--mode", "train"])
        args_inference = parser.parse_args(["--mode", "inference"])
        args_finetune = parser.parse_args(["--mode", "finetune_physics"])

        self.assertEqual(args_train.mode, "train")
        self.assertEqual(args_inference.mode, "inference")
        self.assertEqual(args_finetune.mode, "finetune_physics")

        with self.assertRaisesRegex(NotImplementedError, "finetune_physics not implemented yet"):
            self.engine.run_finetune_physics_mode(args_finetune)


if __name__ == "__main__":
    unittest.main()
