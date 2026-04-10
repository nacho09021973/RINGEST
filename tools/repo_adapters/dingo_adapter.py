from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from tools.repo_contracts import RepoContract


def resolve_entrypoint(contract: RepoContract, capability: str) -> str:
    if contract.name != "dingo":
        raise ValueError(f"dingo adapter cannot inspect repo '{contract.name}'")
    if capability not in contract.capabilities:
        raise ValueError(f"capability '{capability}' not declared for repo '{contract.name}'")
    entrypoints = contract.preferred_entrypoints.get(capability, [])
    if not entrypoints:
        raise ValueError(
            f"no preferred entrypoints declared for capability '{capability}' in repo '{contract.name}'"
        )
    return entrypoints[0]


def summarize_capabilities(contract: RepoContract) -> Dict[str, Any]:
    if contract.name != "dingo":
        raise ValueError(f"dingo adapter cannot summarize repo '{contract.name}'")
    return {
        "repo_name": contract.name,
        "contract_name": contract.name,
        "capabilities": list(contract.capabilities),
        "preferred_entrypoints": dict(contract.preferred_entrypoints),
        "read_only_default": contract.read_only_default,
        "notes": "Inspection only. No external commands are executed in repo_agent_v0.",
    }


def inspect_repo(contract: RepoContract, capability: str) -> Dict[str, Any]:
    return {
        "repo_name": contract.name,
        "contract_name": contract.name,
        "selected_capability": capability,
        "selected_entrypoint": resolve_entrypoint(contract, capability),
        "allowed_commands": list(contract.allowed_commands),
        "read_only_default": contract.read_only_default,
        "notes": "Inspection only adapter for DINGO. Training/inference remain out of scope in v0.",
    }


def detect_entrypoints(repo_root: Path) -> List[str]:
    repo_root = Path(repo_root)
    candidates: List[str] = []
    if (repo_root / "pyproject.toml").exists():
        candidates.append("pyproject.toml")
    if (repo_root / "setup.py").exists():
        candidates.append("setup.py")
    if (repo_root / "setup.cfg").exists():
        candidates.append("setup.cfg")
    for rel_path in ("dingo/__main__.py", "dingo/cli.py", "scripts/train.py", "scripts/inference.py"):
        if (repo_root / rel_path).exists():
            candidates.append(rel_path)
    return candidates


def inspect_repo_read_only(contract: RepoContract, capability: str) -> Dict[str, Any]:
    repo_root = contract.repo_root
    files_examined: List[str] = []
    for rel_path in ("pyproject.toml", "setup.py", "setup.cfg", "README.md", "dingo/__main__.py", "dingo/cli.py"):
        if (repo_root / rel_path).exists():
            files_examined.append(rel_path)

    detected_entrypoints = detect_entrypoints(repo_root)
    selected_entrypoint = resolve_entrypoint(contract, capability)
    verdict = "INSPECTION_OK" if selected_entrypoint in contract.preferred_entrypoints.get(capability, []) else "INSPECTION_FAIL"
    return {
        "repo_name": contract.name,
        "repo_path": str(repo_root),
        "contract_path": str(contract.contract_path),
        "detected_entrypoints": detected_entrypoints,
        "selected_entrypoint": selected_entrypoint,
        "allowed_commands": list(contract.allowed_commands),
        "allowed_paths": list(contract.allowed_paths),
        "read_only_default": contract.read_only_default,
        "inspection_mode": "passive_filesystem_only",
        "files_examined": files_examined,
        "verdict": verdict,
        "conclusion_short": (
            "Passive read-only inspection only. No DINGO training, inference, installation or network access was performed."
        ),
    }
