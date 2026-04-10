from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from tools.repo_contracts import RepoContract, load_repo_contract


@dataclass(frozen=True)
class RegistryIgnoredDir:
    path: Path
    reason: str

    def to_dict(self) -> dict:
        return {"path": str(self.path), "reason": self.reason}


@dataclass(frozen=True)
class RepoRegistrySnapshot:
    root_dir: Path
    repos: Dict[str, RepoContract]
    ignored_dirs: List[RegistryIgnoredDir]

    def get_repo(self, repo_name: str) -> RepoContract | None:
        return self.repos.get(repo_name)

    def to_dict(self) -> dict:
        return {
            "root_dir": str(self.root_dir),
            "repos": {name: contract.to_dict() for name, contract in self.repos.items()},
            "ignored_dirs": [item.to_dict() for item in self.ignored_dirs],
        }


def discover_repo_registry(root_dir: Path) -> RepoRegistrySnapshot:
    root_dir = Path(root_dir).resolve(strict=False)
    repos: Dict[str, RepoContract] = {}
    ignored_dirs: List[RegistryIgnoredDir] = []

    if not root_dir.exists():
        return RepoRegistrySnapshot(root_dir=root_dir, repos=repos, ignored_dirs=ignored_dirs)

    for child in sorted(root_dir.iterdir(), key=lambda p: p.name):
        if not child.is_dir():
            continue
        contract_path = child / "repo_contract.json"
        if not contract_path.exists():
            ignored_dirs.append(
                RegistryIgnoredDir(path=child, reason="missing repo_contract.json")
            )
            continue
        contract = load_repo_contract(contract_path)
        repos[contract.name] = contract

    return RepoRegistrySnapshot(root_dir=root_dir, repos=repos, ignored_dirs=ignored_dirs)
