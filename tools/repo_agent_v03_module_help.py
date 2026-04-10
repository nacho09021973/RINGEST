from __future__ import annotations

import ast
import importlib.util
import json
import os
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

THIS_FILE = Path(__file__).resolve()
REPO_ROOT_DEFAULT = THIS_FILE.parents[1]
if str(REPO_ROOT_DEFAULT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_DEFAULT))

from tools.repo_contracts import load_repo_contract
from tools.repo_registry import discover_repo_registry
from tools.repo_router import resolve_need


@dataclass(frozen=True)
class ModuleCandidate:
    module_name: str
    module_path: Path
    source: str
    help_flag_used: str
    has_main_guard: bool
    uses_argparse: bool
    third_party_imports: List[str]
    imports_available: bool
    risk_rank: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_name": self.module_name,
            "module_path": str(self.module_path),
            "source": self.source,
            "help_flag_used": self.help_flag_used,
            "has_main_guard": self.has_main_guard,
            "uses_argparse": self.uses_argparse,
            "third_party_imports": list(self.third_party_imports),
            "imports_available": self.imports_available,
            "risk_rank": self.risk_rank,
        }


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def snapshot_repo_files(repo_path: Path) -> set[str]:
    return {
        str(path.relative_to(repo_path))
        for path in repo_path.rglob("*")
        if path.is_file()
    }


def load_pyproject_scripts(repo_path: Path) -> Dict[str, str]:
    pyproject_path = repo_path / "pyproject.toml"
    if not pyproject_path.exists():
        return {}
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)
    scripts = data.get("project", {}).get("scripts", {})
    return {str(k): str(v) for k, v in scripts.items()}


def module_name_to_path(repo_path: Path, module_name: str) -> Path:
    module_rel = Path(module_name.replace(".", "/"))
    module_py = repo_path / f"{module_rel}.py"
    module_pkg = repo_path / module_rel / "__init__.py"
    if module_py.exists():
        return module_py
    return module_pkg


def inspect_python_module(module_path: Path) -> Dict[str, Any]:
    source = module_path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(source)
    imported: List[str] = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported.append(node.module.split(".")[0])
    third_party = sorted(
        {
            name
            for name in imported
            if name not in {
                "argparse",
                "ast",
                "copy",
                "functools",
                "json",
                "math",
                "multiprocessing",
                "os",
                "pathlib",
                "pprint",
                "sys",
                "textwrap",
                "time",
                "typing",
            }
            and name != "dingo"
        }
    )
    imports_available = all(importlib.util.find_spec(name) is not None for name in third_party)
    has_main_guard = "__main__" in source
    uses_argparse = "argparse.ArgumentParser" in source or "ArgumentParser(" in source
    return {
        "has_main_guard": has_main_guard,
        "uses_argparse": uses_argparse,
        "third_party_imports": third_party,
        "imports_available": imports_available,
    }


def candidate_risk_rank(module_name: str, imports_available: bool) -> int:
    rank = 100
    if module_name.startswith("dingo.core.utils"):
        rank = 10
    elif module_name.startswith("dingo.gw.training"):
        rank = 90
    elif module_name.startswith("dingo.gw.importance_sampling"):
        rank = 80
    elif module_name.startswith("dingo.gw.dataset"):
        rank = 60
    elif module_name.startswith("dingo.gw.noise"):
        rank = 50
    elif module_name.startswith("dingo.pipe"):
        rank = 70
    if not imports_available:
        rank += 100
    return rank


def build_candidate(
    *,
    repo_path: Path,
    module_name: str,
    source: str,
    help_flag_used: str = "--help",
) -> ModuleCandidate | None:
    module_path = module_name_to_path(repo_path, module_name)
    if not module_path.exists():
        return None
    info = inspect_python_module(module_path)
    return ModuleCandidate(
        module_name=module_name,
        module_path=module_path,
        source=source,
        help_flag_used=help_flag_used,
        has_main_guard=bool(info["has_main_guard"]),
        uses_argparse=bool(info["uses_argparse"]),
        third_party_imports=list(info["third_party_imports"]),
        imports_available=bool(info["imports_available"]),
        risk_rank=candidate_risk_rank(module_name, bool(info["imports_available"])),
    )


def discover_candidate_modules(repo_path: Path, contract_selected_entrypoint: str) -> List[ModuleCandidate]:
    scripts = load_pyproject_scripts(repo_path)
    candidates: List[ModuleCandidate] = []

    target = scripts.get(contract_selected_entrypoint)
    if target and ":" in target:
        module_name, _ = target.split(":", 1)
        candidate = build_candidate(
            repo_path=repo_path,
            module_name=module_name,
            source=f"contract_entrypoint:{contract_selected_entrypoint}",
        )
        if candidate is not None:
            candidates.append(candidate)

    fallback_modules = [
        "dingo.core.utils.pt_to_hdf5",
        "dingo.gw.noise.synthetic.generate_dataset",
        "dingo.gw.dataset.generate_dataset_dag",
        "dingo.gw.training.train_pipeline_condor",
        "dingo.gw.importance_sampling.importance_weights",
    ]
    for module_name in fallback_modules:
        if any(c.module_name == module_name for c in candidates):
            continue
        candidate = build_candidate(repo_path=repo_path, module_name=module_name, source="fallback_scan")
        if candidate is not None:
            candidates.append(candidate)

    return sorted(candidates, key=lambda c: (c.risk_rank, c.module_name))


def select_module_candidate(candidates: List[ModuleCandidate]) -> ModuleCandidate | None:
    for candidate in candidates:
        if candidate.has_main_guard and candidate.uses_argparse:
            return candidate
    return None


def execute_module_help(
    *,
    python_executable: str,
    cwd: Path,
    module_name: str,
    help_flag_used: str,
    timeout_sec: int,
    stdout_path: Path,
    stderr_path: Path,
) -> Dict[str, Any]:
    command = [python_executable, "-m", module_name, help_flag_used]
    start = time.monotonic()
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=timeout_sec,
        check=False,
        env=env,
    )
    elapsed = time.monotonic() - start
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    return {
        "command_list": command,
        "exit_code": int(proc.returncode),
        "execution_time_sec": elapsed,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
    }


def run_v03_module_help(
    *,
    repo_root: Path,
    runs_root: Path,
    run_id: str,
    requested_need: str = "estimator_premium",
    timeout_sec: int = 10,
) -> int:
    repo_root = Path(repo_root).resolve(strict=False)
    runs_root = Path(runs_root).resolve(strict=False)
    repo_path = repo_root / "dingo"
    contract_path = repo_path / "repo_contract.json"
    output_root = runs_root / run_id / "repo_agent_v03"
    output_root.mkdir(parents=True, exist_ok=False)

    manifest_path = output_root / "manifest.json"
    stage_summary_path = output_root / "stage_summary.json"
    execution_path = output_root / "execution.json"
    command_log_path = output_root / "command.log"
    env_probe_path = output_root / "environment_probe.json"
    module_resolution_path = output_root / "module_resolution.json"
    stdout_path = output_root / "stdout.log"
    stderr_path = output_root / "stderr.log"

    contract = load_repo_contract(contract_path)
    registry = discover_repo_registry(repo_root)
    route = resolve_need(requested_need, registry, run_id=run_id)
    contract_selected_entrypoint = route.selected_entrypoint

    candidates = discover_candidate_modules(repo_path, contract_selected_entrypoint)
    selected = select_module_candidate(candidates)
    if selected is None:
        module_resolution = {
            "requested_need": requested_need,
            "selected_repo": contract.name,
            "contract_selected_entrypoint": contract_selected_entrypoint,
            "candidate_modules_considered": [c.to_dict() for c in candidates],
            "selected_module": "",
            "selection_reason": "no module with __main__ and argparse-compatible help was found",
            "help_flag_used": "--help",
            "module_exists": False,
            "module_invocable_strategy": "none",
            "verdict": "AGENT_V03_FAIL",
        }
        environment_probe = {
            "python_executable": sys.executable,
            "python_version": sys.version,
            "repo_present": repo_path.exists(),
            "contract_present": contract_path.exists(),
            "entrypoint_declared": True,
            "shell_entrypoint_resolved": False,
            "module_entrypoint_resolved": False,
            "chosen_strategy": "abort_no_module",
            "verdict": "AGENT_V03_FAIL",
        }
        execution = {
            "run_id": run_id,
            "repo_name": contract.name,
            "repo_path": str(repo_path),
            "contract_path": str(contract.contract_path),
            "requested_need": requested_need,
            "selected_capability": route.selected_capability,
            "contract_selected_entrypoint": contract_selected_entrypoint,
            "resolved_execution_mode": "none",
            "selected_module": "",
            "command_executed": "",
            "cwd": str(repo_path),
            "exit_code": None,
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "execution_time_sec": 0.0,
            "repo_mutated": False,
            "verdict": "AGENT_V03_FAIL",
            "conclusion_short": "No CLI module invocable with python -m <module> --help was found.",
        }
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        command_log_path.write_text("", encoding="utf-8")
        write_json(module_resolution_path, module_resolution)
        write_json(env_probe_path, environment_probe)
        write_json(execution_path, execution)
        write_json(
            stage_summary_path,
            {
                "created_at": utc_now_iso(),
                "stage": "repo_agent_v03",
                "status": "ERROR",
                "requested_need": requested_need,
                "selected_repo": contract.name,
                "verdict": "AGENT_V03_FAIL",
            },
        )
        write_json(
            manifest_path,
            {
                "created_at": utc_now_iso(),
                "run_id": run_id,
                "stage": "repo_agent_v03",
                "artifacts": [
                    str(manifest_path),
                    str(stage_summary_path),
                    str(execution_path),
                    str(command_log_path),
                    str(env_probe_path),
                    str(module_resolution_path),
                    str(stdout_path),
                    str(stderr_path),
                ],
            },
        )
        return 1

    module_resolution = {
        "requested_need": requested_need,
        "selected_repo": contract.name,
        "contract_selected_entrypoint": contract_selected_entrypoint,
        "candidate_modules_considered": [c.to_dict() for c in candidates],
        "selected_module": selected.module_name,
        "selection_reason": (
            "contract entrypoint could not be executed as python -m --help; "
            "selected the lowest-risk real module with __main__ and argparse support"
            if selected.source != f"contract_entrypoint:{contract_selected_entrypoint}"
            else "selected module comes directly from the contract-selected entrypoint"
        ),
        "help_flag_used": selected.help_flag_used,
        "module_exists": selected.module_path.exists(),
        "module_invocable_strategy": "python_module_help",
        "verdict": "PENDING",
    }

    before_snapshot = snapshot_repo_files(repo_path)
    command_list = [sys.executable, "-m", selected.module_name, selected.help_flag_used]
    command_log_path.write_text(
        json.dumps(
            {
                "created_at": utc_now_iso(),
                "cwd": str(repo_path),
                "command_executed": " ".join(command_list),
                "resolved_execution_mode": "python_module_help",
                "selected_module": selected.module_name,
                "selection_reason": module_resolution["selection_reason"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    execution_result = execute_module_help(
        python_executable=sys.executable,
        cwd=repo_path,
        module_name=selected.module_name,
        help_flag_used=selected.help_flag_used,
        timeout_sec=timeout_sec,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
    )
    after_snapshot = snapshot_repo_files(repo_path)
    repo_mutated = before_snapshot != after_snapshot

    verdict = "AGENT_V03_OK"
    conclusion_short = "Module help executed read-only and no repo mutation was detected."
    if repo_mutated:
        verdict = "AGENT_V03_FAIL"
        conclusion_short = "Repo mutation detected during module help execution."
    elif execution_result["exit_code"] != 0:
        verdict = "AGENT_V03_FAIL"
        conclusion_short = "Module help command failed."
    elif not Path(execution_result["stdout_path"]).read_text(encoding="utf-8").strip():
        verdict = "AGENT_V03_FAIL"
        conclusion_short = "Module help command returned empty stdout."

    module_resolution["verdict"] = verdict
    environment_probe = {
        "python_executable": sys.executable,
        "python_version": sys.version,
        "repo_present": repo_path.exists(),
        "contract_present": contract_path.exists(),
        "entrypoint_declared": True,
        "shell_entrypoint_resolved": False,
        "module_entrypoint_resolved": True,
        "chosen_strategy": "python_module_help",
        "verdict": verdict,
    }
    execution = {
        "run_id": run_id,
        "repo_name": contract.name,
        "repo_path": str(repo_path),
        "contract_path": str(contract.contract_path),
        "requested_need": requested_need,
        "selected_capability": route.selected_capability,
        "contract_selected_entrypoint": contract_selected_entrypoint,
        "resolved_execution_mode": "python_module_help",
        "selected_module": selected.module_name,
        "command_executed": " ".join(execution_result["command_list"]),
        "cwd": str(repo_path),
        "exit_code": execution_result["exit_code"],
        "stdout_path": execution_result["stdout_path"],
        "stderr_path": execution_result["stderr_path"],
        "execution_time_sec": execution_result["execution_time_sec"],
        "repo_mutated": repo_mutated,
        "verdict": verdict,
        "conclusion_short": conclusion_short,
    }
    stage_summary = {
        "created_at": utc_now_iso(),
        "stage": "repo_agent_v03",
        "status": "OK" if verdict == "AGENT_V03_OK" else "ERROR",
        "requested_need": requested_need,
        "selected_repo": contract.name,
        "selected_module": selected.module_name,
        "verdict": verdict,
    }
    manifest = {
        "created_at": utc_now_iso(),
        "run_id": run_id,
        "stage": "repo_agent_v03",
        "artifacts": [
            str(manifest_path),
            str(stage_summary_path),
            str(execution_path),
            str(command_log_path),
            str(env_probe_path),
            str(module_resolution_path),
            str(stdout_path),
            str(stderr_path),
        ],
    }
    write_json(module_resolution_path, module_resolution)
    write_json(env_probe_path, environment_probe)
    write_json(execution_path, execution)
    write_json(stage_summary_path, stage_summary)
    write_json(manifest_path, manifest)
    return 0 if verdict == "AGENT_V03_OK" else 1


def main() -> int:
    return run_v03_module_help(
        repo_root=REPO_ROOT_DEFAULT / "repo",
        runs_root=REPO_ROOT_DEFAULT / "runs",
        run_id="repo_agent_v03_dingo_module_help",
    )


if __name__ == "__main__":
    raise SystemExit(main())
