from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tools.repo_registry import discover_repo_registry
from tools.repo_router import RepoRoutingError, resolve_need


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "repo"


class RepoRouterV0Tests(unittest.TestCase):
    def _build_registry(self, repo_names: list[str]):
        tmpdir = tempfile.TemporaryDirectory()
        root = Path(tmpdir.name) / "repo"
        for repo_name in repo_names:
            shutil.copytree(FIXTURE_ROOT / repo_name, root / repo_name)
        self.addCleanup(tmpdir.cleanup)
        return discover_repo_registry(root)

    def test_router_selects_dingo_for_estimator_premium(self):
        registry = self._build_registry(["dingo", "bilby"])
        resolution = resolve_need("estimator_premium", registry, run_id="router_test")
        self.assertEqual(resolution.selected_repo, "dingo")
        self.assertEqual(resolution.selected_capability, "estimator_premium")

    def test_router_selects_bilby_for_bayes_baseline(self):
        registry = self._build_registry(["dingo", "bilby"])
        resolution = resolve_need("bayes_baseline", registry, run_id="router_test")
        self.assertEqual(resolution.selected_repo, "bilby")
        self.assertEqual(resolution.selected_capability, "bayes_baseline")

    def test_router_fails_cleanly_when_repo_missing(self):
        registry = self._build_registry(["dingo"])
        with self.assertRaisesRegex(RepoRoutingError, "expected repo 'bilby'"):
            resolve_need("bayes_baseline", registry, run_id="router_test")


if __name__ == "__main__":
    unittest.main()
