from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

THIS_FILE = Path(__file__).resolve()
REPO_ROOT_DEFAULT = THIS_FILE.parents[1]
if str(REPO_ROOT_DEFAULT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_DEFAULT))

from tools.repo_adapters.bilby_adapter import inspect_repo as inspect_bilby_repo
from tools.repo_adapters.dingo_adapter import inspect_repo as inspect_dingo_repo
from tools.repo_registry import RepoRegistrySnapshot, discover_repo_registry


ROUTE_TABLE: Dict[str, Dict[str, str]] = {
    "estimator_premium": {"repo_name": "dingo", "capability": "estimator_premium"},
    "bayes_baseline": {"repo_name": "bilby", "capability": "bayes_baseline"},
}


class RepoRoutingError(RuntimeError):
    """Raised when a routing request cannot be resolved contractually."""


@dataclass(frozen=True)
class RouteResolution:
    run_id: str
    requested_need: str
    selected_repo: str
    selected_capability: str
    selected_entrypoint: str
    contract_path: Path
    read_only_default: bool
    allowed_commands: list[str]
    verdict: str

    def to_dict(self) -> dict:
        data = asdict(self)
        data["contract_path"] = str(self.contract_path)
        return data


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_need(
    requested_need: str,
    registry: RepoRegistrySnapshot,
    *,
    run_id: str,
) -> RouteResolution:
    if requested_need not in ROUTE_TABLE:
        raise RepoRoutingError(f"unsupported need '{requested_need}' for repo_agent_v0")

    route_spec = ROUTE_TABLE[requested_need]
    repo_name = route_spec["repo_name"]
    capability = route_spec["capability"]
    contract = registry.get_repo(repo_name)
    if contract is None:
        raise RepoRoutingError(
            f"no compatible repo found for need '{requested_need}': expected repo '{repo_name}'"
        )
    if capability not in contract.capabilities:
        raise RepoRoutingError(
            f"repo '{repo_name}' does not declare required capability '{capability}'"
        )

    if repo_name == "dingo":
        inspection = inspect_dingo_repo(contract, capability)
    elif repo_name == "bilby":
        inspection = inspect_bilby_repo(contract, capability)
    else:
        raise RepoRoutingError(f"no adapter registered for repo '{repo_name}'")

    return RouteResolution(
        run_id=run_id,
        requested_need=requested_need,
        selected_repo=inspection["repo_name"],
        selected_capability=inspection["selected_capability"],
        selected_entrypoint=inspection["selected_entrypoint"],
        contract_path=contract.contract_path,
        read_only_default=bool(inspection["read_only_default"]),
        allowed_commands=list(inspection["allowed_commands"]),
        verdict="ROUTE_OK",
    )


def write_resolution_artifacts(
    *,
    output_root: Path,
    resolution: RouteResolution,
    registry: RepoRegistrySnapshot,
) -> Path:
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=False)

    resolution_path = output_root / "resolution.json"
    stage_summary_path = output_root / "stage_summary.json"
    manifest_path = output_root / "manifest.json"

    resolution_path.write_text(
        json.dumps(resolution.to_dict(), indent=2) + "\n",
        encoding="utf-8",
    )
    stage_summary = {
        "created_at": _utc_now_iso(),
        "stage": "repo_agent_v0",
        "status": "OK",
        "requested_need": resolution.requested_need,
        "selected_repo": resolution.selected_repo,
        "selected_capability": resolution.selected_capability,
        "selected_entrypoint": resolution.selected_entrypoint,
        "ignored_dirs": [item.to_dict() for item in registry.ignored_dirs],
        "verdict": resolution.verdict,
    }
    stage_summary_path.write_text(json.dumps(stage_summary, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "created_at": _utc_now_iso(),
        "run_id": resolution.run_id,
        "stage": "repo_agent_v0",
        "repo_root": str(registry.root_dir),
        "artifacts": [
            str(manifest_path),
            str(stage_summary_path),
            str(resolution_path),
        ],
        "requested_need": resolution.requested_need,
        "selected_repo": resolution.selected_repo,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return output_root


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Resolve a local repo route for repo_agent_v0.")
    ap.add_argument("--need", required=True, choices=sorted(ROUTE_TABLE.keys()))
    ap.add_argument("--run-id", required=True)
    ap.add_argument(
        "--repo-root",
        default=str(REPO_ROOT_DEFAULT / "repo"),
        help="Root directory containing local repos with repo_contract.json files.",
    )
    ap.add_argument(
        "--runs-root",
        default=str(REPO_ROOT_DEFAULT / "runs"),
        help="Root directory under which runs/<run_id>/repo_agent_v0/ is created.",
    )
    return ap


def main() -> int:
    args = build_parser().parse_args()
    registry = discover_repo_registry(Path(args.repo_root))
    resolution = resolve_need(args.need, registry, run_id=args.run_id)
    output_root = Path(args.runs_root) / args.run_id / "repo_agent_v0"
    write_resolution_artifacts(output_root=output_root, resolution=resolution, registry=registry)
    print(json.dumps(resolution.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
