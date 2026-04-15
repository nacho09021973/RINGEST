from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.repo_contracts import RepoContractError, load_repo_contract
from tools.repo_registry import discover_repo_registry


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "repo"


class RepoContractsV0Tests(unittest.TestCase):
    def test_repo_contract_validation_ok(self):
        contract = load_repo_contract(FIXTURE_ROOT / "dingo" / "repo_contract.json")
        self.assertEqual(contract.name, "dingo")
        self.assertEqual(contract.capabilities, ["estimator_premium"])
        self.assertTrue(contract.read_only_default)

    def test_repo_contract_missing_field_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_dir = Path(tmpdir) / "dingo"
            repo_dir.mkdir(parents=True, exist_ok=True)
            payload = json.loads((FIXTURE_ROOT / "dingo" / "repo_contract.json").read_text(encoding="utf-8"))
            payload.pop("license")
            (repo_dir / "repo_contract.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(RepoContractError, "missing required field 'license'"):
                load_repo_contract(repo_dir / "repo_contract.json")

    def test_registry_discovers_only_valid_contracts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "repo"
            shutil.copytree(FIXTURE_ROOT / "dingo", root / "dingo")
            shutil.copytree(FIXTURE_ROOT / "bilby", root / "bilby")
            (root / "orphan").mkdir(parents=True, exist_ok=True)

            registry = discover_repo_registry(root)
            self.assertEqual(sorted(registry.repos.keys()), ["bilby", "dingo"])
            self.assertEqual(len(registry.ignored_dirs), 1)
            self.assertEqual(registry.ignored_dirs[0].path.name, "orphan")


if __name__ == "__main__":
    unittest.main()
