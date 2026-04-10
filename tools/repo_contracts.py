from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping


REQUIRED_FIELDS: Dict[str, type] = {
    "name": str,
    "origin_url": str,
    "commit_pinned": str,
    "license": str,
    "domain": str,
    "capabilities": list,
    "preferred_entrypoints": dict,
    "read_only_default": bool,
    "allowed_commands": list,
    "allowed_paths": list,
    "artifact_exports": list,
    "status": str,
}


class RepoContractError(ValueError):
    """Raised when a local repo contract is malformed or unsafe."""


@dataclass(frozen=True)
class RepoContract:
    name: str
    origin_url: str
    commit_pinned: str
    license: str
    domain: str
    capabilities: List[str]
    preferred_entrypoints: Dict[str, List[str]]
    read_only_default: bool
    allowed_commands: List[str]
    allowed_paths: List[str]
    artifact_exports: List[str]
    status: str
    contract_path: Path
    repo_root: Path

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["contract_path"] = str(self.contract_path)
        data["repo_root"] = str(self.repo_root)
        return data


def _load_json(contract_path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(contract_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RepoContractError(f"repo contract not found: {contract_path}") from exc
    except json.JSONDecodeError as exc:
        raise RepoContractError(f"invalid JSON in repo contract {contract_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise RepoContractError(f"repo contract must be a JSON object: {contract_path}")
    return payload


def _require_type(payload: Mapping[str, Any], field_name: str, expected_type: type, contract_path: Path) -> Any:
    if field_name not in payload:
        raise RepoContractError(f"missing required field '{field_name}' in {contract_path}")
    value = payload[field_name]
    if not isinstance(value, expected_type):
        raise RepoContractError(
            f"field '{field_name}' in {contract_path} must be of type {expected_type.__name__}"
        )
    return value


def _validate_non_empty_strings(values: List[str], field_name: str, contract_path: Path) -> List[str]:
    cleaned: List[str] = []
    for idx, value in enumerate(values):
        if not isinstance(value, str) or not value.strip():
            raise RepoContractError(
                f"field '{field_name}[{idx}]' in {contract_path} must be a non-empty string"
            )
        cleaned.append(value)
    return cleaned


def _validate_allowed_paths(allowed_paths: List[str], repo_root: Path, contract_path: Path) -> List[str]:
    cleaned = _validate_non_empty_strings(allowed_paths, "allowed_paths", contract_path)
    resolved_cleaned: List[str] = []
    for rel_path in cleaned:
        p = Path(rel_path)
        if p.is_absolute():
            raise RepoContractError(
                f"allowed_paths entry '{rel_path}' in {contract_path} must be relative to {repo_root}"
            )
        resolved = (repo_root / p).resolve(strict=False)
        try:
            resolved.relative_to(repo_root.resolve(strict=False))
        except ValueError as exc:
            raise RepoContractError(
                f"allowed_paths entry '{rel_path}' escapes repo root {repo_root}"
            ) from exc
        resolved_cleaned.append(rel_path)
    return resolved_cleaned


def _validate_preferred_entrypoints(
    preferred_entrypoints: Mapping[str, Any],
    capabilities: List[str],
    contract_path: Path,
) -> Dict[str, List[str]]:
    if not preferred_entrypoints:
        raise RepoContractError(f"field 'preferred_entrypoints' in {contract_path} must not be empty")
    validated: Dict[str, List[str]] = {}
    for capability, entrypoints in preferred_entrypoints.items():
        if capability not in capabilities:
            raise RepoContractError(
                f"preferred_entrypoints capability '{capability}' in {contract_path} "
                f"is not declared in capabilities"
            )
        if not isinstance(entrypoints, list) or not entrypoints:
            raise RepoContractError(
                f"preferred_entrypoints['{capability}'] in {contract_path} must be a non-empty list"
            )
        validated[capability] = _validate_non_empty_strings(
            list(entrypoints), f"preferred_entrypoints['{capability}']", contract_path
        )
    return validated


def load_repo_contract(contract_path: Path) -> RepoContract:
    contract_path = Path(contract_path).resolve(strict=False)
    repo_root = contract_path.parent.resolve(strict=False)
    payload = _load_json(contract_path)

    for field_name, expected_type in REQUIRED_FIELDS.items():
        _require_type(payload, field_name, expected_type, contract_path)

    name = str(payload["name"]).strip()
    if not name:
        raise RepoContractError(f"field 'name' in {contract_path} must be non-empty")
    if name != repo_root.name:
        raise RepoContractError(
            f"contract name '{name}' does not match repo directory '{repo_root.name}' in {contract_path}"
        )

    capabilities = _validate_non_empty_strings(list(payload["capabilities"]), "capabilities", contract_path)
    if not capabilities:
        raise RepoContractError(f"field 'capabilities' in {contract_path} must not be empty")

    preferred_entrypoints = _validate_preferred_entrypoints(
        payload["preferred_entrypoints"], capabilities, contract_path
    )
    allowed_commands = _validate_non_empty_strings(
        list(payload["allowed_commands"]), "allowed_commands", contract_path
    )
    allowed_paths = _validate_allowed_paths(list(payload["allowed_paths"]), repo_root, contract_path)
    artifact_exports = _validate_non_empty_strings(
        list(payload["artifact_exports"]), "artifact_exports", contract_path
    )

    for field_name in ("origin_url", "commit_pinned", "license", "domain", "status"):
        if not str(payload[field_name]).strip():
            raise RepoContractError(f"field '{field_name}' in {contract_path} must be non-empty")

    return RepoContract(
        name=name,
        origin_url=str(payload["origin_url"]),
        commit_pinned=str(payload["commit_pinned"]),
        license=str(payload["license"]),
        domain=str(payload["domain"]),
        capabilities=capabilities,
        preferred_entrypoints=preferred_entrypoints,
        read_only_default=bool(payload["read_only_default"]),
        allowed_commands=allowed_commands,
        allowed_paths=allowed_paths,
        artifact_exports=artifact_exports,
        status=str(payload["status"]),
        contract_path=contract_path,
        repo_root=repo_root,
    )
