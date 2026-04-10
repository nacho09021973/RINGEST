from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
REPO_ROOT_DEFAULT = THIS_FILE.parents[1]
if str(REPO_ROOT_DEFAULT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_DEFAULT))

from tools.repo_adapters.dingo_adapter import inspect_repo_read_only
from tools.repo_contracts import RepoContractError, load_repo_contract
from tools.repo_registry import discover_repo_registry
from tools.repo_router import RepoRoutingError, resolve_need


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def run_validation(
    *,
    repo_root: Path,
    runs_root: Path,
    run_id: str,
    requested_need: str = "estimator_premium",
) -> int:
    repo_root = Path(repo_root).resolve(strict=False)
    runs_root = Path(runs_root).resolve(strict=False)
    output_root = runs_root / run_id / "repo_agent_v0"
    output_root.mkdir(parents=True, exist_ok=False)

    dingo_repo = repo_root / "dingo"
    contract_path = dingo_repo / "repo_contract.json"
    files_created = [
        str(output_root / "manifest.json"),
        str(output_root / "stage_summary.json"),
        str(output_root / "resolution.json"),
        str(output_root / "repo_inspection.json"),
    ]

    if not dingo_repo.exists():
        repo_inspection = {
            "repo_name": "dingo",
            "repo_path": str(dingo_repo),
            "contract_path": str(contract_path),
            "detected_entrypoints": [],
            "selected_entrypoint": "",
            "allowed_commands": [],
            "allowed_paths": [],
            "read_only_default": True,
            "inspection_mode": "passive_filesystem_only",
            "files_examined": [],
            "verdict": "REPO_MISSING",
            "conclusion_short": "Local repo /repo/dingo is absent. Validation aborted cleanly before routing.",
        }
        resolution = {
            "run_id": run_id,
            "requested_need": requested_need,
            "selected_repo": "",
            "selected_capability": "",
            "selected_entrypoint": "",
            "contract_path": str(contract_path),
            "read_only_default": True,
            "allowed_commands": [],
            "verdict": "ROUTE_ABORTED_REPO_MISSING",
        }
        stage_summary = {
            "created_at": utc_now_iso(),
            "stage": "repo_agent_v01_validate",
            "status": "ERROR",
            "requested_need": requested_need,
            "selected_repo": "",
            "verdict": "AGENT_V01_FAIL",
            "reason": "missing /home/ignac/RINGEST/repo/dingo",
        }
        manifest = {
            "created_at": utc_now_iso(),
            "run_id": run_id,
            "stage": "repo_agent_v01_validate",
            "repo_root": str(repo_root),
            "files_created": files_created,
            "status": "ERROR",
        }
        _write_json(output_root / "repo_inspection.json", repo_inspection)
        _write_json(output_root / "resolution.json", resolution)
        _write_json(output_root / "stage_summary.json", stage_summary)
        _write_json(output_root / "manifest.json", manifest)
        return 1

    try:
        contract = load_repo_contract(contract_path)
    except RepoContractError as exc:
        repo_inspection = {
            "repo_name": "dingo",
            "repo_path": str(dingo_repo),
            "contract_path": str(contract_path),
            "detected_entrypoints": [],
            "selected_entrypoint": "",
            "allowed_commands": [],
            "allowed_paths": [],
            "read_only_default": True,
            "inspection_mode": "passive_filesystem_only",
            "files_examined": [],
            "verdict": "CONTRACT_INVALID",
            "conclusion_short": f"Contract validation failed: {exc}",
        }
        resolution = {
            "run_id": run_id,
            "requested_need": requested_need,
            "selected_repo": "",
            "selected_capability": "",
            "selected_entrypoint": "",
            "contract_path": str(contract_path),
            "read_only_default": True,
            "allowed_commands": [],
            "verdict": "ROUTE_ABORTED_CONTRACT_INVALID",
        }
        stage_summary = {
            "created_at": utc_now_iso(),
            "stage": "repo_agent_v01_validate",
            "status": "ERROR",
            "requested_need": requested_need,
            "selected_repo": "",
            "verdict": "AGENT_V01_FAIL",
            "reason": str(exc),
        }
        manifest = {
            "created_at": utc_now_iso(),
            "run_id": run_id,
            "stage": "repo_agent_v01_validate",
            "repo_root": str(repo_root),
            "files_created": files_created,
            "status": "ERROR",
        }
        _write_json(output_root / "repo_inspection.json", repo_inspection)
        _write_json(output_root / "resolution.json", resolution)
        _write_json(output_root / "stage_summary.json", stage_summary)
        _write_json(output_root / "manifest.json", manifest)
        return 1

    inspection = inspect_repo_read_only(contract, requested_need)
    registry = discover_repo_registry(repo_root)
    try:
        route = resolve_need(requested_need, registry, run_id=run_id)
    except RepoRoutingError as exc:
        resolution = {
            "run_id": run_id,
            "requested_need": requested_need,
            "selected_repo": "",
            "selected_capability": "",
            "selected_entrypoint": "",
            "contract_path": str(contract.contract_path),
            "read_only_default": contract.read_only_default,
            "allowed_commands": list(contract.allowed_commands),
            "verdict": f"ROUTE_ABORTED: {exc}",
        }
        stage_summary = {
            "created_at": utc_now_iso(),
            "stage": "repo_agent_v01_validate",
            "status": "ERROR",
            "requested_need": requested_need,
            "selected_repo": contract.name,
            "verdict": "AGENT_V01_FAIL",
            "reason": str(exc),
        }
        manifest = {
            "created_at": utc_now_iso(),
            "run_id": run_id,
            "stage": "repo_agent_v01_validate",
            "repo_root": str(repo_root),
            "files_created": files_created,
            "status": "ERROR",
        }
        _write_json(output_root / "repo_inspection.json", inspection)
        _write_json(output_root / "resolution.json", resolution)
        _write_json(output_root / "stage_summary.json", stage_summary)
        _write_json(output_root / "manifest.json", manifest)
        return 1

    resolution = route.to_dict()
    stage_summary = {
        "created_at": utc_now_iso(),
        "stage": "repo_agent_v01_validate",
        "status": "OK",
        "requested_need": requested_need,
        "selected_repo": route.selected_repo,
        "selected_capability": route.selected_capability,
        "selected_entrypoint": route.selected_entrypoint,
        "verdict": "AGENT_V01_OK",
    }
    manifest = {
        "created_at": utc_now_iso(),
        "run_id": run_id,
        "stage": "repo_agent_v01_validate",
        "repo_root": str(repo_root),
        "files_created": files_created,
        "status": "OK",
    }
    _write_json(output_root / "repo_inspection.json", inspection)
    _write_json(output_root / "resolution.json", resolution)
    _write_json(output_root / "stage_summary.json", stage_summary)
    _write_json(output_root / "manifest.json", manifest)
    return 0


def main() -> int:
    return run_validation(
        repo_root=REPO_ROOT_DEFAULT / "repo",
        runs_root=REPO_ROOT_DEFAULT / "runs",
        run_id="repo_agent_v01_dingo_real",
    )


if __name__ == "__main__":
    raise SystemExit(main())
