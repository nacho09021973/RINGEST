from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.estimators_registry import (
    EstimatorsRegistryError,
    build_registry_summary,
    load_estimators_registry,
)


REGISTRY_PATH = Path(__file__).resolve().parents[1] / "estimators_registry.json"


def _load_payload() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


class EstimatorsRegistryTests(unittest.TestCase):
    def test_registry_load_ok(self):
        registry = load_estimators_registry(REGISTRY_PATH)
        self.assertEqual(registry.registry_name, "estimators_v1")
        self.assertEqual(registry.get_estimator("E20").name, "baseline_features_v1")
        self.assertEqual(registry.get_estimator("E30").name, "premium_posterior_estimator_v1")

    def test_registry_duplicate_id_fails(self):
        payload = _load_payload()
        payload["estimators"].append(dict(payload["estimators"][0]))
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_path = Path(tmpdir) / "estimators_registry.json"
            bad_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(EstimatorsRegistryError, "duplicate estimator id 'E00'"):
                load_estimators_registry(bad_path)

    def test_registry_missing_required_field_fails(self):
        payload = _load_payload()
        payload["estimators"][0].pop("name")
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_path = Path(tmpdir) / "estimators_registry.json"
            bad_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(EstimatorsRegistryError, "missing required field 'name'"):
                load_estimators_registry(bad_path)

    def test_registry_execution_order_ok(self):
        registry = load_estimators_registry(REGISTRY_PATH)
        ordered_ids = [item.estimator_id for item in registry.ordered_estimators()]
        self.assertEqual(ordered_ids, ["E00", "E10", "E20", "E30", "E40", "E50", "E60"])

    def test_registry_blocking_rules_ok(self):
        registry = load_estimators_registry(REGISTRY_PATH)
        summary = build_registry_summary(registry)
        self.assertEqual(summary["blocking_estimators"], ["E00", "E10", "E40", "E50"])


if __name__ == "__main__":
    unittest.main()
