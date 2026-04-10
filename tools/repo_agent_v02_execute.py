from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import tomllib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

THIS_FILE = Path(__file__).resolve()
REPO_ROOT_DEFAULT = THIS_FILE.parents[1]
if str(REPO_ROOT_DEFAULT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_DEFAULT))

from tools.repo_contracts import RepoContract, RepoContractError, load_repo_contract
from tools.repo_registry import discover_repo_registry
from tools.repo_router import RepoRoutingError, resolve_need


class RepoExecutionError(RuntimeError):
    """Raised when a controlled repo execution cannot proceed safely."""


@dataclass(frozen=True)
class ExecutionPlan:
    selected_entrypoint: str
    resolved_execution_mode: str
    command_executed: str
    chosen_strategy: str
    selection_reason: str


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


def resolve_shell_entrypoint(entrypoint: str) -> str | None:
    return shutil.which(entrypoint)


def derive_module_entrypoint(repo_path: Path, entrypoint: str) -> Dict[str, str] | None:
    pyproject_path = repo_path / "pyproject.toml"
    if not pyproject_path.exists():
        return None
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)
    scripts = data.get("project", {}).get("scripts", {})
    target = scripts.get(entrypoint)
    if not isinstance(target, str) or ":" not in target:
        return None
    module_name, function_name = target.split(":", 1)
    module_rel = Path(module_name.replace(".", "/"))
    module_path_py = repo_path / (str(module_rel) + ".py")
    module_path_pkg = repo_path / module_rel / "__init__.py"
    module_path = module_path_py if module_path_py.exists() else module_path_pkg
    return {
        "module_name": module_name,
        "function_name": function_name,
        "module_path": str(module_path),
    }


def contract_allows_shell_help(contract: RepoContract, entrypoint: str) -> bool:
    return f"{entrypoint} --help" in contract.allowed_commands


def contract_allows_passive_python_probe(contract: RepoContract) -> bool:
    return any("passive filesystem inspection only" in item for item in contract.allowed_commands)


def build_module_probe_command(module_spec: Dict[str, str]) -> str:
    module_name = module_spec["module_name"]
    function_name = module_spec["function_name"]
    module_path = module_spec["module_path"]
    return "\n".join(
        [
            "python3 - <<'PY'",
            "import json",
            "from pathlib import Path",
            f"module_name = {module_name!r}",
            f"function_name = {function_name!r}",
            f"module_path = {module_path!r}",
            "payload = {",
            "    'module_name': module_name,",
            "    'function_name': function_name,",
            "    'module_path': module_path,",
            "    'module_path_exists': Path(module_path).exists(),",
            "}",
            "print(json.dumps(payload, indent=2))",
            "PY",
        ]
    )


def choose_execution_plan(
    *,
    contract: RepoContract,
    selected_entrypoint: str,
    shell_entrypoint_resolved: str | None,
    module_spec: Dict[str, str] | None,
) -> ExecutionPlan:
    if shell_entrypoint_resolved and contract_allows_shell_help(contract, selected_entrypoint):
        return ExecutionPlan(
            selected_entrypoint=selected_entrypoint,
            resolved_execution_mode="shell_help",
            command_executed=f"{selected_entrypoint} --help",
            chosen_strategy="shell_help",
            selection_reason="shell entrypoint resolved and explicit help command is allowed by contract",
        )
    if module_spec and contract_allows_passive_python_probe(contract):
        return ExecutionPlan(
            selected_entrypoint=selected_entrypoint,
            resolved_execution_mode="module_entrypoint_probe",
            command_executed=build_module_probe_command(module_spec),
            chosen_strategy="module_entrypoint_probe",
            selection_reason=(
                "shell help is unavailable or unpermitted; falling back to passive Python inspection "
                "derived from pyproject entrypoint mapping"
            ),
        )
    raise RepoExecutionError(
        f"no permitted read-only execution strategy for entrypoint '{selected_entrypoint}'"
    )


def execute_plan(
    *,
    plan: ExecutionPlan,
    cwd: Path,
    timeout_sec: int,
    stdout_path: Path,
    stderr_path: Path,
) -> Dict[str, Any]:
    start = time.monotonic()
    if plan.resolved_execution_mode == "shell_help":
        proc = subprocess.run(
            [plan.selected_entrypoint, "--help"],
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout_sec,
            check=False,
        )
    else:
        proc = subprocess.run(
            plan.command_executed,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout_sec,
            check=False,
            shell=True,
            executable="/bin/bash",
        )
    elapsed = time.monotonic() - start
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    return {
        "exit_code": int(proc.returncode),
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "execution_time_sec": elapsed,
    }


def run_v02_execution(
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
    output_root = runs_root / run_id / "repo_agent_v02"
    output_root.mkdir(parents=True, exist_ok=False)

    manifest_path = output_root / "manifest.json"
    stage_summary_path = output_root / "stage_summary.json"
    execution_path = output_root / "execution.json"
    command_log_path = output_root / "command.log"
    env_probe_path = output_root / "environment_probe.json"
    stdout_path = output_root / "stdout.log"
    stderr_path = output_root / "stderr.log"

    repo_present = repo_path.exists()
    contract_present = contract_path.exists()
    shell_entrypoint_resolved = False
    module_entrypoint_resolved = False
    chosen_strategy = ""

    if not repo_present or not contract_present:
        environment_probe = {
            "python_executable": sys.executable,
            "python_version": sys.version,
            "repo_present": repo_present,
            "contract_present": contract_present,
            "entrypoint_declared": False,
            "shell_entrypoint_resolved": False,
            "module_entrypoint_resolved": False,
            "chosen_strategy": "abort_missing_repo_or_contract",
            "verdict": "AGENT_V02_FAIL",
        }
        execution = {
            "run_id": run_id,
            "repo_name": "dingo",
            "repo_path": str(repo_path),
            "contract_path": str(contract_path),
            "requested_need": requested_need,
            "selected_capability": "",
            "selected_entrypoint": "",
            "resolved_execution_mode": "none",
            "command_executed": "",
            "cwd": str(repo_path),
            "exit_code": None,
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "execution_time_sec": 0.0,
            "read_only_default": True,
            "verdict": "AGENT_V02_FAIL",
            "conclusion_short": "Repo or contract missing. Execution aborted before command dispatch.",
        }
        stage_summary = {
            "created_at": utc_now_iso(),
            "stage": "repo_agent_v02",
            "status": "ERROR",
            "requested_need": requested_need,
            "selected_repo": "dingo" if repo_present else "",
            "verdict": "AGENT_V02_FAIL",
            "reason": "missing repo or contract",
        }
        manifest = {
            "created_at": utc_now_iso(),
            "run_id": run_id,
            "stage": "repo_agent_v02",
            "artifacts": [
                str(manifest_path),
                str(stage_summary_path),
                str(execution_path),
                str(command_log_path),
                str(env_probe_path),
                str(stdout_path),
                str(stderr_path),
            ],
        }
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        command_log_path.write_text("", encoding="utf-8")
        write_json(env_probe_path, environment_probe)
        write_json(execution_path, execution)
        write_json(stage_summary_path, stage_summary)
        write_json(manifest_path, manifest)
        return 1

    contract = load_repo_contract(contract_path)
    registry = discover_repo_registry(repo_root)
    route = resolve_need(requested_need, registry, run_id=run_id)
    selected_entrypoint = route.selected_entrypoint
    selected_capability = route.selected_capability
    if selected_capability != "estimator_premium":
        raise RepoExecutionError(f"unexpected capability resolved for v0.2: {selected_capability}")

    shell_path = resolve_shell_entrypoint(selected_entrypoint)
    shell_entrypoint_resolved = shell_path is not None
    module_spec = derive_module_entrypoint(repo_path, selected_entrypoint)
    module_entrypoint_resolved = module_spec is not None

    try:
        plan = choose_execution_plan(
            contract=contract,
            selected_entrypoint=selected_entrypoint,
            shell_entrypoint_resolved=shell_path,
            module_spec=module_spec,
        )
        chosen_strategy = plan.chosen_strategy
    except RepoExecutionError as exc:
        environment_probe = {
            "python_executable": sys.executable,
            "python_version": sys.version,
            "repo_present": True,
            "contract_present": True,
            "entrypoint_declared": True,
            "shell_entrypoint_resolved": shell_entrypoint_resolved,
            "module_entrypoint_resolved": module_entrypoint_resolved,
            "chosen_strategy": "abort_unpermitted_or_unresolved",
            "verdict": "AGENT_V02_FAIL",
        }
        execution = {
            "run_id": run_id,
            "repo_name": contract.name,
            "repo_path": str(repo_path),
            "contract_path": str(contract.contract_path),
            "requested_need": requested_need,
            "selected_capability": selected_capability,
            "selected_entrypoint": selected_entrypoint,
            "resolved_execution_mode": "none",
            "command_executed": "",
            "cwd": str(repo_path),
            "exit_code": None,
            "stdout_path": str(stdout_path),
            "stderr_path": str(stderr_path),
            "execution_time_sec": 0.0,
            "read_only_default": contract.read_only_default,
            "verdict": "AGENT_V02_FAIL",
            "conclusion_short": str(exc),
        }
        stage_summary = {
            "created_at": utc_now_iso(),
            "stage": "repo_agent_v02",
            "status": "ERROR",
            "requested_need": requested_need,
            "selected_repo": contract.name,
            "verdict": "AGENT_V02_FAIL",
            "reason": str(exc),
        }
        manifest = {
            "created_at": utc_now_iso(),
            "run_id": run_id,
            "stage": "repo_agent_v02",
            "artifacts": [
                str(manifest_path),
                str(stage_summary_path),
                str(execution_path),
                str(command_log_path),
                str(env_probe_path),
                str(stdout_path),
                str(stderr_path),
            ],
        }
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text("", encoding="utf-8")
        command_log_path.write_text("", encoding="utf-8")
        write_json(env_probe_path, environment_probe)
        write_json(execution_path, execution)
        write_json(stage_summary_path, stage_summary)
        write_json(manifest_path, manifest)
        return 1

    before_snapshot = snapshot_repo_files(repo_path)
    command_log_path.write_text(
        json.dumps(
            {
                "created_at": utc_now_iso(),
                "cwd": str(repo_path),
                "command_executed": plan.command_executed,
                "resolved_execution_mode": plan.resolved_execution_mode,
                "chosen_strategy": plan.chosen_strategy,
                "selection_reason": plan.selection_reason,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    execution_result = execute_plan(
        plan=plan,
        cwd=repo_path,
        timeout_sec=timeout_sec,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
    )
    after_snapshot = snapshot_repo_files(repo_path)
    repo_mutated = before_snapshot != after_snapshot

    verdict = "AGENT_V02_OK"
    conclusion = "Read-only execution completed and captured auditably."
    if repo_mutated:
        verdict = "AGENT_V02_FAIL"
        conclusion = "Repo filesystem changed during controlled execution."
    elif execution_result["exit_code"] != 0:
        verdict = "AGENT_V02_FAIL"
        conclusion = "Controlled execution returned non-zero exit code."

    environment_probe = {
        "python_executable": sys.executable,
        "python_version": sys.version,
        "repo_present": True,
        "contract_present": True,
        "entrypoint_declared": True,
        "shell_entrypoint_resolved": shell_entrypoint_resolved,
        "module_entrypoint_resolved": module_entrypoint_resolved,
        "chosen_strategy": chosen_strategy,
        "verdict": verdict,
    }
    execution = {
        "run_id": run_id,
        "repo_name": contract.name,
        "repo_path": str(repo_path),
        "contract_path": str(contract.contract_path),
        "requested_need": requested_need,
        "selected_capability": selected_capability,
        "selected_entrypoint": selected_entrypoint,
        "resolved_execution_mode": plan.resolved_execution_mode,
        "command_executed": plan.command_executed,
        "cwd": str(repo_path),
        "exit_code": execution_result["exit_code"],
        "stdout_path": execution_result["stdout_path"],
        "stderr_path": execution_result["stderr_path"],
        "execution_time_sec": execution_result["execution_time_sec"],
        "read_only_default": contract.read_only_default,
        "verdict": verdict,
        "conclusion_short": conclusion,
    }
    stage_summary = {
        "created_at": utc_now_iso(),
        "stage": "repo_agent_v02",
        "status": "OK" if verdict == "AGENT_V02_OK" else "ERROR",
        "requested_need": requested_need,
        "selected_repo": contract.name,
        "selected_entrypoint": selected_entrypoint,
        "resolved_execution_mode": plan.resolved_execution_mode,
        "verdict": verdict,
    }
    manifest = {
        "created_at": utc_now_iso(),
        "run_id": run_id,
        "stage": "repo_agent_v02",
        "artifacts": [
            str(manifest_path),
            str(stage_summary_path),
            str(execution_path),
            str(command_log_path),
            str(env_probe_path),
            str(stdout_path),
            str(stderr_path),
        ],
    }
    write_json(env_probe_path, environment_probe)
    write_json(execution_path, execution)
    write_json(stage_summary_path, stage_summary)
    write_json(manifest_path, manifest)
    return 0 if verdict == "AGENT_V02_OK" else 1


def main() -> int:
    return run_v02_execution(
        repo_root=REPO_ROOT_DEFAULT / "repo",
        runs_root=REPO_ROOT_DEFAULT / "runs",
        run_id="repo_agent_v02_dingo_exec",
    )


if __name__ == "__main__":
    raise SystemExit(main())
