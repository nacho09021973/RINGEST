from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.repo_adapters.dingo_adapter import inspect_repo_read_only
from tools.repo_contracts import load_repo_contract
from tools.repo_agent_v01_validate import run_validation


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "repo"
REAL_DINGO_ROOT = Path("/home/ignac/RINGEST/repo/dingo")


class RepoAgentV01Tests(unittest.TestCase):
    def test_repo_agent_v01_fails_cleanly_when_repo_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "repo"
            repo_root.mkdir(parents=True, exist_ok=True)
            runs_root = Path(tmpdir) / "runs"
            exit_code = run_validation(
                repo_root=repo_root,
                runs_root=runs_root,
                run_id="repo_agent_v01_missing",
            )
            self.assertEqual(exit_code, 1)
            resolution = json.loads(
                (runs_root / "repo_agent_v01_missing" / "repo_agent_v0" / "resolution.json").read_text(encoding="utf-8")
            )
            inspection = json.loads(
                (runs_root / "repo_agent_v01_missing" / "repo_agent_v0" / "repo_inspection.json").read_text(encoding="utf-8")
            )
            self.assertEqual(resolution["verdict"], "ROUTE_ABORTED_REPO_MISSING")
            self.assertEqual(inspection["verdict"], "REPO_MISSING")

    def test_dingo_contract_coheres_with_passive_inspection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "repo"
            shutil.copytree(FIXTURE_ROOT / "dingo", repo_root / "dingo")
            (repo_root / "dingo" / "pyproject.toml").write_text("[project]\nname='dingo'\n", encoding="utf-8")
            (repo_root / "dingo" / "README.md").write_text("# dingo\n", encoding="utf-8")
            contract = load_repo_contract(repo_root / "dingo" / "repo_contract.json")
            inspection = inspect_repo_read_only(contract, "estimator_premium")
            self.assertIn("pyproject.toml", inspection["detected_entrypoints"])
            self.assertEqual(inspection["selected_entrypoint"], "python -m dingo.cli")
            self.assertEqual(inspection["verdict"], "INSPECTION_OK")

    @unittest.skipUnless(REAL_DINGO_ROOT.exists(), "real /repo/dingo is absent in this workspace")
    def test_real_dingo_repo_can_be_discovered_if_present(self):
        contract_path = REAL_DINGO_ROOT / "repo_contract.json"
        self.assertTrue(contract_path.exists())
        contract = load_repo_contract(contract_path)
        inspection = inspect_repo_read_only(contract, "estimator_premium")
        self.assertEqual(contract.name, "dingo")
        self.assertTrue(inspection["read_only_default"])


if __name__ == "__main__":
    unittest.main()
