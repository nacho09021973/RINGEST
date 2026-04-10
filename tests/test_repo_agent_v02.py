from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.repo_agent_v02_execute import (
    build_module_probe_command,
    choose_execution_plan,
    contract_allows_passive_python_probe,
    contract_allows_shell_help,
    derive_module_entrypoint,
    run_v02_execution,
)
from tools.repo_contracts import load_repo_contract


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "repo"


class RepoAgentV02Tests(unittest.TestCase):
    def _build_dingo_repo(self, tmpdir: str, *, allow_shell_help: bool = False) -> Path:
        repo_root = Path(tmpdir) / "repo"
        shutil.copytree(FIXTURE_ROOT / "dingo", repo_root / "dingo")
        (repo_root / "dingo" / "pyproject.toml").write_text(
            "\n".join(
                [
                    "[project]",
                    "name = 'dingo-gw'",
                    "[project.scripts]",
                    "dingo_train = 'dingo.gw.training:train_local'",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        module_path = repo_root / "dingo" / "dingo" / "gw" / "training.py"
        module_path.parent.mkdir(parents=True, exist_ok=True)
        module_path.write_text("def train_local():\n    return None\n", encoding="utf-8")
        payload = json.loads((repo_root / "dingo" / "repo_contract.json").read_text(encoding="utf-8"))
        payload["preferred_entrypoints"]["estimator_premium"] = ["dingo_train"]
        if allow_shell_help:
            payload["allowed_commands"] = ["dingo_train --help"]
        else:
            payload["allowed_commands"] = [
                "python3 - <<'PY' ... passive filesystem inspection only ... PY"
            ]
        (repo_root / "dingo" / "repo_contract.json").write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )
        return repo_root

    def test_repo_agent_v02_fails_cleanly_when_repo_or_contract_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "repo"
            repo_root.mkdir(parents=True, exist_ok=True)
            runs_root = Path(tmpdir) / "runs"
            exit_code = run_v02_execution(
                repo_root=repo_root,
                runs_root=runs_root,
                run_id="repo_agent_v02_missing",
            )
            self.assertEqual(exit_code, 1)
            execution = json.loads(
                (runs_root / "repo_agent_v02_missing" / "repo_agent_v02" / "execution.json").read_text(encoding="utf-8")
            )
            self.assertEqual(execution["verdict"], "AGENT_V02_FAIL")

    def test_strategy_selection_shell_help_vs_module_python(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = self._build_dingo_repo(tmpdir)
            contract = load_repo_contract(repo_root / "dingo" / "repo_contract.json")
            module_spec = derive_module_entrypoint(repo_root / "dingo", "dingo_train")
            self.assertFalse(contract_allows_shell_help(contract, "dingo_train"))
            self.assertTrue(contract_allows_passive_python_probe(contract))
            plan = choose_execution_plan(
                contract=contract,
                selected_entrypoint="dingo_train",
                shell_entrypoint_resolved=None,
                module_spec=module_spec,
            )
            self.assertEqual(plan.resolved_execution_mode, "module_entrypoint_probe")
            self.assertIn("python3 - <<'PY'", plan.command_executed)

    def test_writes_execution_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = self._build_dingo_repo(tmpdir)
            runs_root = Path(tmpdir) / "runs"
            exit_code = run_v02_execution(
                repo_root=repo_root,
                runs_root=runs_root,
                run_id="repo_agent_v02_artifacts",
            )
            self.assertEqual(exit_code, 0)
            out = runs_root / "repo_agent_v02_artifacts" / "repo_agent_v02"
            for name in ("manifest.json", "stage_summary.json", "execution.json", "command.log", "environment_probe.json"):
                self.assertTrue((out / name).exists())

    def test_forbids_commands_not_permitted(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = self._build_dingo_repo(tmpdir)
            payload = json.loads((repo_root / "dingo" / "repo_contract.json").read_text(encoding="utf-8"))
            payload["allowed_commands"] = []
            (repo_root / "dingo" / "repo_contract.json").write_text(
                json.dumps(payload, indent=2) + "\n",
                encoding="utf-8",
            )
            runs_root = Path(tmpdir) / "runs"
            exit_code = run_v02_execution(
                repo_root=repo_root,
                runs_root=runs_root,
                run_id="repo_agent_v02_forbidden",
            )
            self.assertEqual(exit_code, 1)
            execution = json.loads(
                (runs_root / "repo_agent_v02_forbidden" / "repo_agent_v02" / "execution.json").read_text(encoding="utf-8")
            )
            self.assertEqual(execution["verdict"], "AGENT_V02_FAIL")

    def test_pass_if_read_only_probe_captures_stdout_stderr(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = self._build_dingo_repo(tmpdir)
            runs_root = Path(tmpdir) / "runs"
            exit_code = run_v02_execution(
                repo_root=repo_root,
                runs_root=runs_root,
                run_id="repo_agent_v02_probe",
            )
            self.assertEqual(exit_code, 0)
            out = runs_root / "repo_agent_v02_probe" / "repo_agent_v02"
            execution = json.loads((out / "execution.json").read_text(encoding="utf-8"))
            self.assertEqual(execution["verdict"], "AGENT_V02_OK")
            self.assertTrue((out / "stdout.log").exists())
            self.assertTrue((out / "stderr.log").exists())


if __name__ == "__main__":
    unittest.main()
