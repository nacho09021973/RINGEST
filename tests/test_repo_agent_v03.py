from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.repo_agent_v03_module_help import (
    discover_candidate_modules,
    run_v03_module_help,
    select_module_candidate,
)


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "repo"


class RepoAgentV03Tests(unittest.TestCase):
    def _build_repo(self, tmpdir: str, *, with_invocable_module: bool = True, mutates_repo: bool = False) -> Path:
        repo_root = Path(tmpdir) / "repo"
        shutil.copytree(FIXTURE_ROOT / "dingo", repo_root / "dingo")
        pyproject = "\n".join(
            [
                "[project]",
                "name = 'dingo-gw'",
                "[project.scripts]",
                "dingo_train = 'dingo.gw.training:train_local'",
            ]
        )
        (repo_root / "dingo" / "pyproject.toml").write_text(pyproject + "\n", encoding="utf-8")
        payload = json.loads((repo_root / "dingo" / "repo_contract.json").read_text(encoding="utf-8"))
        payload["preferred_entrypoints"]["estimator_premium"] = ["dingo_train"]
        (repo_root / "dingo" / "repo_contract.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        pkg = repo_root / "dingo" / "dingo" / "core" / "utils"
        pkg.mkdir(parents=True, exist_ok=True)
        for init_path in [
            repo_root / "dingo" / "dingo" / "__init__.py",
            repo_root / "dingo" / "dingo" / "core" / "__init__.py",
            repo_root / "dingo" / "dingo" / "core" / "utils" / "__init__.py",
        ]:
            init_path.write_text("", encoding="utf-8")

        if with_invocable_module:
            body = [
                "import argparse",
                "from pathlib import Path",
                "",
                "def main():",
                "    parser = argparse.ArgumentParser(description='safe help cli')",
                "    parser.parse_args()",
                "    print('safe help cli')",
                "",
                "if __name__ == '__main__':",
                "    main()",
            ]
            if mutates_repo:
                body = [
                    "import argparse",
                    "from pathlib import Path",
                    "Path('MUTATED.txt').write_text('boom', encoding='utf-8')",
                    "",
                    "def main():",
                    "    parser = argparse.ArgumentParser(description='mutating cli')",
                    "    parser.parse_args()",
                    "    print('mutating cli')",
                    "",
                    "if __name__ == '__main__':",
                    "    main()",
                ]
            (pkg / "pt_to_hdf5.py").write_text("\n".join(body) + "\n", encoding="utf-8")
        else:
            (pkg / "pt_to_hdf5.py").write_text("x = 1\n", encoding="utf-8")
        return repo_root

    def test_resolves_real_cli_module_from_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = self._build_repo(tmpdir)
            candidates = discover_candidate_modules(repo_root / "dingo", "dingo_train")
            selected = select_module_candidate(candidates)
            self.assertIsNotNone(selected)
            self.assertEqual(selected.module_name, "dingo.core.utils.pt_to_hdf5")

    def test_aborts_cleanly_if_no_invocable_module_with_help(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = self._build_repo(tmpdir, with_invocable_module=False)
            runs_root = Path(tmpdir) / "runs"
            exit_code = run_v03_module_help(
                repo_root=repo_root,
                runs_root=runs_root,
                run_id="repo_agent_v03_abort",
            )
            self.assertEqual(exit_code, 1)
            execution = json.loads(
                (runs_root / "repo_agent_v03_abort" / "repo_agent_v03" / "execution.json").read_text(encoding="utf-8")
            )
            self.assertEqual(execution["verdict"], "AGENT_V03_FAIL")

    def test_writes_execution_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = self._build_repo(tmpdir)
            runs_root = Path(tmpdir) / "runs"
            exit_code = run_v03_module_help(
                repo_root=repo_root,
                runs_root=runs_root,
                run_id="repo_agent_v03_artifacts",
            )
            self.assertEqual(exit_code, 0)
            out = runs_root / "repo_agent_v03_artifacts" / "repo_agent_v03"
            for name in ("manifest.json", "stage_summary.json", "execution.json", "command.log", "environment_probe.json", "module_resolution.json", "stdout.log", "stderr.log"):
                self.assertTrue((out / name).exists())

    def test_fails_if_repo_mutates(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = self._build_repo(tmpdir, mutates_repo=True)
            runs_root = Path(tmpdir) / "runs"
            exit_code = run_v03_module_help(
                repo_root=repo_root,
                runs_root=runs_root,
                run_id="repo_agent_v03_mutation",
            )
            self.assertEqual(exit_code, 1)
            execution = json.loads(
                (runs_root / "repo_agent_v03_mutation" / "repo_agent_v03" / "execution.json").read_text(encoding="utf-8")
            )
            self.assertTrue(execution["repo_mutated"])

    def test_pass_if_real_help_returns_output_and_no_mutation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = self._build_repo(tmpdir)
            runs_root = Path(tmpdir) / "runs"
            exit_code = run_v03_module_help(
                repo_root=repo_root,
                runs_root=runs_root,
                run_id="repo_agent_v03_pass",
            )
            self.assertEqual(exit_code, 0)
            out = runs_root / "repo_agent_v03_pass" / "repo_agent_v03"
            execution = json.loads((out / "execution.json").read_text(encoding="utf-8"))
            self.assertEqual(execution["verdict"], "AGENT_V03_OK")
            self.assertFalse(execution["repo_mutated"])
            self.assertTrue((out / "stdout.log").read_text(encoding="utf-8").strip())


if __name__ == "__main__":
    unittest.main()
