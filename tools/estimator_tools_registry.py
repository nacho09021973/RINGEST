from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping


THIS_FILE = Path(__file__).resolve()
REPO_ROOT_DEFAULT = THIS_FILE.parents[1]
TOOLS_REGISTRY_PATH_DEFAULT = REPO_ROOT_DEFAULT / "estimator_tools_registry.json"
LOCAL_REPOS_ROOT_DEFAULT = REPO_ROOT_DEFAULT / "repo"
RUNS_ROOT_DEFAULT = REPO_ROOT_DEFAULT / "runs"

REQUIRED_TOP_LEVEL_FIELDS: Dict[str, type] = {
    "registry_name": str,
    "schema_version": str,
    "repo_root": str,
    "freeze_policy_default": str,
    "integration_mode_default": str,
    "tools": list,
}

REQUIRED_TOOL_FIELDS: Dict[str, type] = {
    "tool_id": str,
    "repo_name": str,
    "local_repo_path": str,
    "required_for_estimators": list,
    "role": str,
    "repo_expected": bool,
    "status": str,
    "freeze_policy": str,
    "integration_mode": str,
    "notes": str,
}


class EstimatorToolsRegistryError(ValueError):
    """Raised when the estimator tools registry is malformed or inconsistent."""


@dataclass(frozen=True)
class ToolSpec:
    tool_id: str
    repo_name: str
    local_repo_path: Path
    required_for_estimators: List[str]
    role: str
    repo_expected: bool
    status: str
    freeze_policy: str
    integration_mode: str
    notes: str

    def is_present_local(self) -> bool:
        return self.local_repo_path.exists()

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["local_repo_path"] = str(self.local_repo_path)
        data["present_local"] = self.is_present_local()
        return data


@dataclass(frozen=True)
class EstimatorToolsRegistry:
    registry_name: str
    schema_version: str
    repo_root: Path
    freeze_policy_default: str
    integration_mode_default: str
    tools: Dict[str, ToolSpec]
    registry_path: Path

    def get_tool(self, tool_id: str) -> ToolSpec:
        try:
            return self.tools[tool_id]
        except KeyError as exc:
            raise EstimatorToolsRegistryError(
                f"tool id '{tool_id}' not found in {self.registry_path}"
            ) from exc

    def tools_for_estimator(self, estimator_id: str) -> List[ToolSpec]:
        return [tool for tool in self.tools.values() if estimator_id in tool.required_for_estimators]

    def present_local_tools(self) -> List[str]:
        return sorted(tool.tool_id for tool in self.tools.values() if tool.is_present_local())

    def missing_local_tools(self) -> List[str]:
        return sorted(tool.tool_id for tool in self.tools.values() if not tool.is_present_local())

    def estimator_to_tools(self) -> Dict[str, List[str]]:
        mapping: Dict[str, List[str]] = {}
        for tool in self.tools.values():
            for estimator_id in tool.required_for_estimators:
                mapping.setdefault(estimator_id, []).append(tool.tool_id)
        return {key: sorted(value) for key, value in sorted(mapping.items())}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EstimatorToolsRegistryError(f"estimator tools registry not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise EstimatorToolsRegistryError(f"invalid JSON in estimator tools registry {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise EstimatorToolsRegistryError(f"estimator tools registry must be a JSON object: {path}")
    return payload


def _require_type(payload: Mapping[str, Any], field_name: str, expected_type: type, path: Path) -> Any:
    if field_name not in payload:
        raise EstimatorToolsRegistryError(f"missing required field '{field_name}' in {path}")
    value = payload[field_name]
    if not isinstance(value, expected_type):
        raise EstimatorToolsRegistryError(
            f"field '{field_name}' in {path} must be of type {expected_type.__name__}"
        )
    return value


def _validate_non_empty_string(value: Any, label: str, path: Path) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EstimatorToolsRegistryError(f"{label} in {path} must be a non-empty string")
    return value


def _validate_string_list(value: Any, label: str, path: Path) -> List[str]:
    if not isinstance(value, list) or not value:
        raise EstimatorToolsRegistryError(f"{label} in {path} must be a non-empty list")
    cleaned: List[str] = []
    for idx, item in enumerate(value):
        cleaned.append(_validate_non_empty_string(item, f"{label}[{idx}]", path))
    return cleaned


def _validate_local_repo_path(local_repo_path: str, repo_name: str, repo_root: Path, path: Path) -> Path:
    candidate = Path(local_repo_path)
    if not candidate.is_absolute():
        raise EstimatorToolsRegistryError(
            f"local_repo_path '{local_repo_path}' in {path} must be an absolute path"
        )
    resolved = candidate.resolve(strict=False)
    repo_root_resolved = repo_root.resolve(strict=False)
    try:
        resolved.relative_to(repo_root_resolved)
    except ValueError as exc:
        raise EstimatorToolsRegistryError(
            f"local_repo_path '{local_repo_path}' in {path} must live under {repo_root_resolved}"
        ) from exc
    if resolved.name != repo_name:
        raise EstimatorToolsRegistryError(
            f"local_repo_path '{local_repo_path}' in {path} is not coherent with repo_name '{repo_name}'"
        )
    return resolved


def _validate_status(status: str, local_repo_path: Path, registry_path: Path) -> None:
    expected_status = "present_local" if local_repo_path.exists() else "missing_local"
    if status != expected_status:
        raise EstimatorToolsRegistryError(
            f"status '{status}' in {registry_path} is inconsistent with local repo path "
            f"'{local_repo_path}' (expected '{expected_status}')"
        )


def load_estimator_tools_registry(registry_path: Path | None = None) -> EstimatorToolsRegistry:
    registry_path = Path(registry_path or TOOLS_REGISTRY_PATH_DEFAULT).resolve(strict=False)
    payload = _load_json(registry_path)
    for field_name, expected_type in REQUIRED_TOP_LEVEL_FIELDS.items():
        _require_type(payload, field_name, expected_type, registry_path)

    repo_root = Path(_validate_non_empty_string(payload["repo_root"], "repo_root", registry_path))
    if not repo_root.is_absolute():
        raise EstimatorToolsRegistryError(f"repo_root in {registry_path} must be an absolute path")

    tools_payload = payload["tools"]
    if not isinstance(tools_payload, list) or not tools_payload:
        raise EstimatorToolsRegistryError(f"field 'tools' in {registry_path} must be a non-empty list")

    tools: Dict[str, ToolSpec] = {}
    for idx, item in enumerate(tools_payload):
        if not isinstance(item, dict):
            raise EstimatorToolsRegistryError(f"tools[{idx}] in {registry_path} must be a JSON object")
        for field_name, expected_type in REQUIRED_TOOL_FIELDS.items():
            _require_type(item, field_name, expected_type, registry_path)
        tool_id = _validate_non_empty_string(item["tool_id"], f"tools[{idx}].tool_id", registry_path)
        if tool_id in tools:
            raise EstimatorToolsRegistryError(f"duplicate tool id '{tool_id}' in {registry_path}")
        repo_name = _validate_non_empty_string(item["repo_name"], f"tools[{idx}].repo_name", registry_path)
        local_repo_path = _validate_local_repo_path(item["local_repo_path"], repo_name, repo_root, registry_path)
        required_for_estimators = _validate_string_list(
            item["required_for_estimators"], f"tools[{idx}].required_for_estimators", registry_path
        )
        status = _validate_non_empty_string(item["status"], f"tools[{idx}].status", registry_path)
        _validate_status(status, local_repo_path, registry_path)

        tools[tool_id] = ToolSpec(
            tool_id=tool_id,
            repo_name=repo_name,
            local_repo_path=local_repo_path,
            required_for_estimators=required_for_estimators,
            role=_validate_non_empty_string(item["role"], f"tools[{idx}].role", registry_path),
            repo_expected=bool(item["repo_expected"]),
            status=status,
            freeze_policy=_validate_non_empty_string(
                item["freeze_policy"], f"tools[{idx}].freeze_policy", registry_path
            ),
            integration_mode=_validate_non_empty_string(
                item["integration_mode"], f"tools[{idx}].integration_mode", registry_path
            ),
            notes=_validate_non_empty_string(item["notes"], f"tools[{idx}].notes", registry_path),
        )

    return EstimatorToolsRegistry(
        registry_name=_validate_non_empty_string(payload["registry_name"], "registry_name", registry_path),
        schema_version=_validate_non_empty_string(payload["schema_version"], "schema_version", registry_path),
        repo_root=repo_root.resolve(strict=False),
        freeze_policy_default=_validate_non_empty_string(
            payload["freeze_policy_default"], "freeze_policy_default", registry_path
        ),
        integration_mode_default=_validate_non_empty_string(
            payload["integration_mode_default"], "integration_mode_default", registry_path
        ),
        tools=tools,
        registry_path=registry_path,
    )


def build_registry_summary(registry: EstimatorToolsRegistry) -> Dict[str, Any]:
    return {
        "registry_path": str(registry.registry_path),
        "n_tools": len(registry.tools),
        "estimator_to_tools": registry.estimator_to_tools(),
        "present_local_tools": registry.present_local_tools(),
        "missing_local_tools": registry.missing_local_tools(),
        "freeze_policy": registry.freeze_policy_default,
        "verdict": "ESTIMATOR_TOOLS_REGISTRY_OK",
    }


def write_smoke_artifacts(
    *,
    registry: EstimatorToolsRegistry,
    run_id: str,
    runs_root: Path,
) -> Path:
    output_root = Path(runs_root) / run_id / "estimator_tools_registry_v1"
    output_root.mkdir(parents=True, exist_ok=False)

    manifest_path = output_root / "manifest.json"
    stage_summary_path = output_root / "stage_summary.json"
    registry_summary_path = output_root / "registry_summary.json"

    registry_summary = build_registry_summary(registry)
    registry_summary_path.write_text(json.dumps(registry_summary, indent=2) + "\n", encoding="utf-8")

    stage_summary = {
        "created_at": _utc_now_iso(),
        "stage": "estimator_tools_registry_v1",
        "registry_name": registry.registry_name,
        "schema_version": registry.schema_version,
        "n_tools": len(registry.tools),
        "present_local_tools": registry.present_local_tools(),
        "missing_local_tools": registry.missing_local_tools(),
        "status": "OK",
        "verdict": "ESTIMATOR_TOOLS_REGISTRY_OK",
    }
    stage_summary_path.write_text(json.dumps(stage_summary, indent=2) + "\n", encoding="utf-8")

    manifest = {
        "created_at": _utc_now_iso(),
        "run_id": run_id,
        "stage": "estimator_tools_registry_v1",
        "registry_path": str(registry.registry_path),
        "artifacts": [
            str(manifest_path),
            str(stage_summary_path),
            str(registry_summary_path)
        ],
        "verdict": "ESTIMATOR_TOOLS_REGISTRY_OK"
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return output_root


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Validate and summarize estimator_tools_registry.json.")
    ap.add_argument("--registry-path", default=str(TOOLS_REGISTRY_PATH_DEFAULT))
    ap.add_argument("--run-id", default="estimator_tools_registry_smoke")
    ap.add_argument("--runs-root", default=str(RUNS_ROOT_DEFAULT))
    return ap


def main() -> int:
    args = build_parser().parse_args()
    registry = load_estimator_tools_registry(Path(args.registry_path))
    write_smoke_artifacts(registry=registry, run_id=args.run_id, runs_root=Path(args.runs_root))
    print(json.dumps(build_registry_summary(registry), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
