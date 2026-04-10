from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.estimator_tools_registry import (
    EstimatorToolsRegistryError,
    build_registry_summary,
    load_estimator_tools_registry,
)


REGISTRY_PATH = Path(__file__).resolve().parents[1] / "estimator_tools_registry.json"


def _load_payload() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


class EstimatorToolsRegistryTests(unittest.TestCase):
    def test_tools_registry_load_ok(self):
        registry = load_estimator_tools_registry(REGISTRY_PATH)
        self.assertEqual(registry.registry_name, "estimator_tools_registry_v1")
        self.assertEqual(registry.tools_for_estimator("E30")[0].tool_id, "dingo")
        self.assertEqual(
            sorted(tool.tool_id for tool in registry.tools_for_estimator("E40")),
            ["evidently", "scikit_learn"],
        )

    def test_tools_registry_duplicate_tool_id_fails(self):
        payload = _load_payload()
        payload["tools"].append(dict(payload["tools"][0]))
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_path = Path(tmpdir) / "estimator_tools_registry.json"
            bad_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(EstimatorToolsRegistryError, "duplicate tool id 'pydantic'"):
                load_estimator_tools_registry(bad_path)

    def test_tools_registry_invalid_local_path_fails(self):
        payload = _load_payload()
        payload["tools"][0]["local_repo_path"] = "/tmp/not_under_repo/pydantic"
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_path = Path(tmpdir) / "estimator_tools_registry.json"
            bad_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(EstimatorToolsRegistryError, "must live under"):
                load_estimator_tools_registry(bad_path)

    def test_tools_registry_reports_missing_local_tools(self):
        registry = load_estimator_tools_registry(REGISTRY_PATH)
        missing = registry.missing_local_tools()
        self.assertIn("pydantic", missing)
        self.assertIn("captum", missing)
        self.assertNotIn("dingo", missing)

    def test_tools_registry_reports_present_local_dingo(self):
        registry = load_estimator_tools_registry(REGISTRY_PATH)
        summary = build_registry_summary(registry)
        self.assertEqual(summary["present_local_tools"], ["dingo"])


if __name__ == "__main__":
    unittest.main()
