from __future__ import annotations

from typing import Any, Dict

from tools.repo_contracts import RepoContract


def resolve_entrypoint(contract: RepoContract, capability: str) -> str:
    if contract.name != "bilby":
        raise ValueError(f"bilby adapter cannot inspect repo '{contract.name}'")
    if capability not in contract.capabilities:
        raise ValueError(f"capability '{capability}' not declared for repo '{contract.name}'")
    entrypoints = contract.preferred_entrypoints.get(capability, [])
    if not entrypoints:
        raise ValueError(
            f"no preferred entrypoints declared for capability '{capability}' in repo '{contract.name}'"
        )
    return entrypoints[0]


def summarize_capabilities(contract: RepoContract) -> Dict[str, Any]:
    if contract.name != "bilby":
        raise ValueError(f"bilby adapter cannot summarize repo '{contract.name}'")
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
        "notes": "Inspection only adapter for Bilby. Sampling/execution remain out of scope in v0.",
    }
