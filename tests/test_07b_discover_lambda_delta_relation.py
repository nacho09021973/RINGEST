from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_stage07b():
    key = "stage07b_for_test"
    sys.modules.pop(key, None)
    spec = importlib.util.spec_from_file_location(
        key, REPO_ROOT / "07b_discover_lambda_delta_relation.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


class TestLoadGroundTruth(unittest.TestCase):
    def setUp(self):
        self.s07b = _load_stage07b()

    def _write_json(self, payload: dict) -> Path:
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        path = Path(tmpdir.name) / "input.json"
        path.write_text(json.dumps(payload))
        return path

    def test_load_ground_truth_accepts_legacy_schema(self):
        path = self._write_json(
            {
                "systems": [
                    {
                        "system": "ising_2d",
                        "d": 2,
                        "operators": [
                            {"name": "sigma", "lambda_sl": 0.125, "Delta": 0.125},
                            {"name": "epsilon", "lambda_sl": None, "Delta": 1.0},
                        ],
                    }
                ]
            }
        )

        pairs = self.s07b.load_ground_truth(path)

        self.assertEqual(
            pairs,
            [
                {
                    "system": "ising_2d",
                    "d": 2,
                    "lambda_sl": 0.125,
                    "Delta": 0.125,
                    "name": "sigma",
                }
            ],
        )

    def test_load_ground_truth_accepts_stage06_canonical_schema(self):
        path = self._write_json(
            {
                "systems": [
                    {
                        "geometry_name": "GW150914__ringdown",
                        "family": "kerr",
                        "d": 4,
                        "n_modes": 3,
                        "Delta_bulk_uv": [4.0, None, 6.5],
                        "lambda_sl_bulk": [1.25, 2.5, 3.75],
                        "lambda_source": "bulk_eigenmode",
                    }
                ]
            }
        )

        pairs = self.s07b.load_ground_truth(path)

        self.assertEqual(
            pairs,
            [
                {
                    "system": "GW150914__ringdown",
                    "d": 4,
                    "lambda_sl": 1.25,
                    "Delta": 4.0,
                    "name": "mode_0",
                },
                {
                    "system": "GW150914__ringdown",
                    "d": 4,
                    "lambda_sl": 3.75,
                    "Delta": 6.5,
                    "name": "mode_2",
                },
            ],
        )

    def test_load_ground_truth_raises_on_schema_mismatch(self):
        path = self._write_json(
            {
                "systems": [
                    {
                        "geometry_name": "bad_case",
                        "d": 4,
                        "operators": [],
                    }
                ]
            }
        )

        with self.assertRaisesRegex(RuntimeError, "INPUT_SCHEMA_MISMATCH"):
            self.s07b.load_ground_truth(path)

    def test_load_ground_truth_raises_on_length_mismatch(self):
        path = self._write_json(
            {
                "systems": [
                    {
                        "geometry_name": "GW150914__ringdown",
                        "d": 4,
                        "lambda_sl_bulk": [1.0, 2.0],
                        "Delta_bulk_uv": [4.0],
                    }
                ]
            }
        )

        with self.assertRaisesRegex(RuntimeError, "INPUT_SCHEMA_MISMATCH"):
            self.s07b.load_ground_truth(path)
