from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping


THIS_FILE = Path(__file__).resolve()
REPO_ROOT_DEFAULT = THIS_FILE.parents[1]
REGISTRY_PATH_DEFAULT = REPO_ROOT_DEFAULT / "estimators_registry.json"
RUNS_ROOT_DEFAULT = REPO_ROOT_DEFAULT / "runs"

REQUIRED_TOP_LEVEL_FIELDS: Dict[str, type] = {
    "registry_name": str,
    "schema_version": str,
    "governance_mode": str,
    "summary": dict,
    "execution_order": list,
    "global_blocking_rules": list,
    "estimators": list,
}

REQUIRED_ESTIMATOR_FIELDS: Dict[str, type] = {
    "id": str,
    "name": str,
    "role": str,
    "stage_kind": str,
    "primary_inputs": list,
    "primary_outputs": list,
    "artifacts": list,
}

REQUIRED_BLOCKING_RULE_FIELDS: Dict[str, type] = {
    "if": str,
    "then": str,
}


class EstimatorsRegistryError(ValueError):
    """Raised when the estimators registry is malformed or inconsistent."""


@dataclass(frozen=True)
class BlockingRule:
    condition: str
    action: str

    def to_dict(self) -> Dict[str, str]:
        return {"if": self.condition, "then": self.action}


@dataclass(frozen=True)
class EstimatorSpec:
    estimator_id: str
    name: str
    role: str
    stage_kind: str
    primary_inputs: List[str]
    primary_outputs: List[str]
    artifacts: List[str]
    raw_spec: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["id"] = data.pop("estimator_id")
        return data


@dataclass(frozen=True)
class EstimatorsRegistry:
    registry_name: str
    schema_version: str
    governance_mode: str
    summary: Dict[str, Any]
    execution_order: List[str]
    blocking_rules: List[BlockingRule]
    estimators: Dict[str, EstimatorSpec]
    registry_path: Path

    def get_estimator(self, estimator_id: str) -> EstimatorSpec:
        try:
            return self.estimators[estimator_id]
        except KeyError as exc:
            raise EstimatorsRegistryError(
                f"estimator id '{estimator_id}' not found in {self.registry_path}"
            ) from exc

    def ordered_estimators(self) -> List[EstimatorSpec]:
        return [self.get_estimator(estimator_id) for estimator_id in self.execution_order]

    def blocking_estimators(self) -> List[str]:
        blocking_actions = {"abort_run", "block_interpretation"}
        ordered_unique: List[str] = []
        for rule in self.blocking_rules:
            if rule.action not in blocking_actions:
                continue
            estimator_id = _extract_estimator_id_from_condition(rule.condition)
            if estimator_id not in ordered_unique:
                ordered_unique.append(estimator_id)
        return ordered_unique


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise EstimatorsRegistryError(f"estimators registry not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise EstimatorsRegistryError(f"invalid JSON in estimators registry {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise EstimatorsRegistryError(f"estimators registry must be a JSON object: {path}")
    return payload


def _require_type(payload: Mapping[str, Any], field_name: str, expected_type: type, path: Path) -> Any:
    if field_name not in payload:
        raise EstimatorsRegistryError(f"missing required field '{field_name}' in {path}")
    value = payload[field_name]
    if not isinstance(value, expected_type):
        raise EstimatorsRegistryError(
            f"field '{field_name}' in {path} must be of type {expected_type.__name__}"
        )
    return value


def _validate_non_empty_string(value: Any, label: str, path: Path) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EstimatorsRegistryError(f"{label} in {path} must be a non-empty string")
    return value


def _validate_string_list(values: Any, label: str, path: Path) -> List[str]:
    if not isinstance(values, list) or not values:
        raise EstimatorsRegistryError(f"{label} in {path} must be a non-empty list")
    cleaned: List[str] = []
    for idx, value in enumerate(values):
        cleaned.append(_validate_non_empty_string(value, f"{label}[{idx}]", path))
    return cleaned


def _extract_estimator_id_from_condition(condition: str) -> str:
    estimator_id = condition.split(".", 1)[0].strip()
    if not estimator_id:
        raise EstimatorsRegistryError(f"blocking rule condition has no estimator id prefix: {condition!r}")
    return estimator_id


def _validate_blocking_rules(
    rules_payload: Any,
    estimator_ids: List[str],
    path: Path,
) -> List[BlockingRule]:
    if not isinstance(rules_payload, list):
        raise EstimatorsRegistryError(f"field 'global_blocking_rules' in {path} must be of type list")
    validated: List[BlockingRule] = []
    for idx, item in enumerate(rules_payload):
        if not isinstance(item, dict):
            raise EstimatorsRegistryError(
                f"global_blocking_rules[{idx}] in {path} must be a JSON object"
            )
        for field_name, expected_type in REQUIRED_BLOCKING_RULE_FIELDS.items():
            _require_type(item, field_name, expected_type, path)
        condition = _validate_non_empty_string(item["if"], f"global_blocking_rules[{idx}].if", path)
        action = _validate_non_empty_string(item["then"], f"global_blocking_rules[{idx}].then", path)
        estimator_id = _extract_estimator_id_from_condition(condition)
        if estimator_id not in estimator_ids:
            raise EstimatorsRegistryError(
                f"blocking rule references unknown estimator id '{estimator_id}' in {path}"
            )
        validated.append(BlockingRule(condition=condition, action=action))
    return validated


def _validate_estimators(estimators_payload: Any, path: Path) -> Dict[str, EstimatorSpec]:
    if not isinstance(estimators_payload, list) or not estimators_payload:
        raise EstimatorsRegistryError(f"field 'estimators' in {path} must be a non-empty list")
    validated: Dict[str, EstimatorSpec] = {}
    for idx, item in enumerate(estimators_payload):
        if not isinstance(item, dict):
            raise EstimatorsRegistryError(f"estimators[{idx}] in {path} must be a JSON object")
        for field_name, expected_type in REQUIRED_ESTIMATOR_FIELDS.items():
            _require_type(item, field_name, expected_type, path)
        estimator_id = _validate_non_empty_string(item["id"], f"estimators[{idx}].id", path)
        if estimator_id in validated:
            raise EstimatorsRegistryError(f"duplicate estimator id '{estimator_id}' in {path}")
        validated[estimator_id] = EstimatorSpec(
            estimator_id=estimator_id,
            name=_validate_non_empty_string(item["name"], f"estimators[{idx}].name", path),
            role=_validate_non_empty_string(item["role"], f"estimators[{idx}].role", path),
            stage_kind=_validate_non_empty_string(item["stage_kind"], f"estimators[{idx}].stage_kind", path),
            primary_inputs=_validate_string_list(item["primary_inputs"], f"estimators[{idx}].primary_inputs", path),
            primary_outputs=_validate_string_list(
                item["primary_outputs"], f"estimators[{idx}].primary_outputs", path
            ),
            artifacts=_validate_string_list(item["artifacts"], f"estimators[{idx}].artifacts", path),
            raw_spec=dict(item),
        )
    return validated


def _validate_execution_order(order_payload: Any, estimator_ids: List[str], path: Path) -> List[str]:
    execution_order = _validate_string_list(order_payload, "execution_order", path)
    if len(set(execution_order)) != len(execution_order):
        raise EstimatorsRegistryError(f"execution_order in {path} must not contain duplicates")
    unknown = [item for item in execution_order if item not in estimator_ids]
    if unknown:
        raise EstimatorsRegistryError(
            f"execution_order in {path} references unknown estimator ids: {unknown}"
        )
    missing = [item for item in estimator_ids if item not in execution_order]
    if missing:
        raise EstimatorsRegistryError(
            f"execution_order in {path} is missing estimator ids: {missing}"
        )
    return execution_order


def load_estimators_registry(registry_path: Path | None = None) -> EstimatorsRegistry:
    registry_path = Path(registry_path or REGISTRY_PATH_DEFAULT).resolve(strict=False)
    payload = _load_json(registry_path)
    for field_name, expected_type in REQUIRED_TOP_LEVEL_FIELDS.items():
        _require_type(payload, field_name, expected_type, registry_path)

    estimators = _validate_estimators(payload["estimators"], registry_path)
    estimator_ids = list(estimators.keys())
    execution_order = _validate_execution_order(payload["execution_order"], estimator_ids, registry_path)
    blocking_rules = _validate_blocking_rules(payload["global_blocking_rules"], estimator_ids, registry_path)

    summary = payload["summary"]
    if not summary:
        raise EstimatorsRegistryError(f"field 'summary' in {registry_path} must not be empty")

    return EstimatorsRegistry(
        registry_name=_validate_non_empty_string(payload["registry_name"], "registry_name", registry_path),
        schema_version=_validate_non_empty_string(payload["schema_version"], "schema_version", registry_path),
        governance_mode=_validate_non_empty_string(payload["governance_mode"], "governance_mode", registry_path),
        summary=dict(summary),
        execution_order=execution_order,
        blocking_rules=blocking_rules,
        estimators=estimators,
        registry_path=registry_path,
    )


def build_registry_summary(registry: EstimatorsRegistry) -> Dict[str, Any]:
    estimator_e20 = registry.get_estimator("E20")
    estimator_e30 = registry.get_estimator("E30")
    return {
        "registry_path": str(registry.registry_path),
        "n_estimators": len(registry.estimators),
        "execution_order": registry.execution_order,
        "blocking_estimators": registry.blocking_estimators(),
        "estimator_e20": estimator_e20.to_dict(),
        "estimator_e30": estimator_e30.to_dict(),
        "verdict": "ESTIMATORS_REGISTRY_OK",
    }


def write_smoke_artifacts(
    *,
    registry: EstimatorsRegistry,
    run_id: str,
    runs_root: Path,
) -> Path:
    output_root = Path(runs_root) / run_id / "estimators_registry_v1"
    output_root.mkdir(parents=True, exist_ok=False)

    manifest_path = output_root / "manifest.json"
    stage_summary_path = output_root / "stage_summary.json"
    registry_summary_path = output_root / "registry_summary.json"

    registry_summary = build_registry_summary(registry)
    registry_summary_path.write_text(json.dumps(registry_summary, indent=2) + "\n", encoding="utf-8")

    stage_summary = {
        "created_at": _utc_now_iso(),
        "stage": "estimators_registry_v1",
        "registry_name": registry.registry_name,
        "schema_version": registry.schema_version,
        "n_estimators": len(registry.estimators),
        "execution_order": registry.execution_order,
        "blocking_estimators": registry.blocking_estimators(),
        "status": "OK",
        "verdict": "ESTIMATORS_REGISTRY_OK",
    }
    stage_summary_path.write_text(json.dumps(stage_summary, indent=2) + "\n", encoding="utf-8")

    manifest = {
        "created_at": _utc_now_iso(),
        "run_id": run_id,
        "stage": "estimators_registry_v1",
        "registry_path": str(registry.registry_path),
        "artifacts": [
            str(manifest_path),
            str(stage_summary_path),
            str(registry_summary_path),
        ],
        "verdict": "ESTIMATORS_REGISTRY_OK",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return output_root


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Validate and summarize estimators_registry.json.")
    ap.add_argument("--registry-path", default=str(REGISTRY_PATH_DEFAULT))
    ap.add_argument("--run-id", default="estimators_registry_smoke")
    ap.add_argument("--runs-root", default=str(RUNS_ROOT_DEFAULT))
    return ap


def main() -> int:
    args = build_parser().parse_args()
    registry = load_estimators_registry(Path(args.registry_path))
    write_smoke_artifacts(registry=registry, run_id=args.run_id, runs_root=Path(args.runs_root))
    print(json.dumps(build_registry_summary(registry), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
