from __future__ import annotations

import unittest
from pathlib import Path

from tools.repo_adapters.bilby_adapter import inspect_repo as inspect_bilby_repo
from tools.repo_adapters.dingo_adapter import inspect_repo as inspect_dingo_repo
from tools.repo_contracts import load_repo_contract


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "repo"


class RepoAdaptersV0Tests(unittest.TestCase):
    def test_dingo_adapter_inspection_only(self):
        contract = load_repo_contract(FIXTURE_ROOT / "dingo" / "repo_contract.json")
        inspection = inspect_dingo_repo(contract, "estimator_premium")
        self.assertEqual(inspection["repo_name"], "dingo")
        self.assertEqual(inspection["selected_capability"], "estimator_premium")
        self.assertTrue(inspection["read_only_default"])
        self.assertIn("Inspection only", inspection["notes"])

    def test_bilby_adapter_inspection_only(self):
        contract = load_repo_contract(FIXTURE_ROOT / "bilby" / "repo_contract.json")
        inspection = inspect_bilby_repo(contract, "bayes_baseline")
        self.assertEqual(inspection["repo_name"], "bilby")
        self.assertEqual(inspection["selected_capability"], "bayes_baseline")
        self.assertTrue(inspection["read_only_default"])
        self.assertIn("Inspection only", inspection["notes"])


if __name__ == "__main__":
    unittest.main()
