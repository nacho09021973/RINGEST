from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator, model_validator


class ContractValidationError(ValueError):
    """Raised when a manifest or stage summary violates its declared contract."""


def _validate_iso8601(value: str) -> str:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("must be a valid ISO-8601 datetime string") from exc
    return value


def _validate_non_empty(value: str) -> str:
    if not value.strip():
        raise ValueError("must be a non-empty string")
    return value


def _raise_contract_error(kind: str, path: Path, exc: ValidationError) -> ContractValidationError:
    return ContractValidationError(f"{kind} contract validation failed at {path}: {exc}")


class ManifestArtifactModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    path: str
    sha256: str

    @field_validator("path", "sha256")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        return _validate_non_empty(value)


class ManifestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    created_at: str
    stage: str
    script: str
    inputs: dict[str, ManifestArtifactModel]
    outputs: dict[str, ManifestArtifactModel]
    input_root: str | None = None
    notes: list[str] | None = None

    @field_validator("created_at")
    @classmethod
    def _created_at_iso8601(cls, value: str) -> str:
        return _validate_iso8601(value)

    @field_validator("stage", "script", "input_root")
    @classmethod
    def _non_empty_optional_strings(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _validate_non_empty(value)

    @model_validator(mode="after")
    def _require_non_empty_io(self) -> "ManifestModel":
        if not self.inputs:
            raise ValueError("inputs must contain at least one artifact")
        if not self.outputs:
            raise ValueError("outputs must contain at least one artifact")
        return self


class StageRuntimeManifestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    created_at: str
    experiment: str
    stage: str
    stage_dir: str
    run_root: str
    outputs: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None
    artifacts: dict[str, str] | None = None

    @field_validator("created_at")
    @classmethod
    def _runtime_created_at_iso8601(cls, value: str) -> str:
        return _validate_iso8601(value)

    @field_validator("experiment", "stage", "stage_dir", "run_root")
    @classmethod
    def _runtime_non_empty_strings(cls, value: str) -> str:
        return _validate_non_empty(value)


class StageSummaryModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    created_at: str
    status: str
    exit_code: int
    stage: str | None = None
    stage_name: str | None = None
    script: str | None = None
    experiment: str | None = None
    counts: dict[str, Any] | None = None
    output_dir: str | None = None
    input_root: str | None = None
    notes: list[str] | None = None
    error_message: str | None = None
    n_theories: int | None = None
    n_evaluable: int | None = None
    n_not_evaluable: int | None = None
    verdict_counts: dict[str, int] | None = None
    post_hoc_only: bool | None = None
    upstream_training_contamination: str | None = None

    @field_validator("created_at")
    @classmethod
    def _summary_created_at_iso8601(cls, value: str) -> str:
        return _validate_iso8601(value)

    @field_validator(
        "status",
        "stage",
        "stage_name",
        "script",
        "experiment",
        "output_dir",
        "input_root",
        "error_message",
        "upstream_training_contamination",
    )
    @classmethod
    def _summary_non_empty_optional_strings(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _validate_non_empty(value)

    @model_validator(mode="after")
    def _require_stage_identifier(self) -> "StageSummaryModel":
        if not self.stage and not self.stage_name:
            raise ValueError("either 'stage' or 'stage_name' must be present")
        return self


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp_", suffix=path.suffix or ".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True))
            fh.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def load_manifest(path: str | Path) -> ManifestModel:
    manifest_path = Path(path)
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except json.JSONDecodeError as exc:
        raise ContractValidationError(f"manifest JSON decode failed at {manifest_path}: {exc}") from exc
    try:
        return ManifestModel.model_validate(payload)
    except ValidationError as exc:
        raise _raise_contract_error("manifest", manifest_path, exc) from exc


def load_stage_runtime_manifest(path: str | Path) -> StageRuntimeManifestModel:
    manifest_path = Path(path)
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except json.JSONDecodeError as exc:
        raise ContractValidationError(f"stage runtime manifest JSON decode failed at {manifest_path}: {exc}") from exc
    try:
        return StageRuntimeManifestModel.model_validate(payload)
    except ValidationError as exc:
        raise _raise_contract_error("stage runtime manifest", manifest_path, exc) from exc


def write_manifest(model: ManifestModel, path: str | Path) -> None:
    try:
        validated = ManifestModel.model_validate(model)
    except ValidationError as exc:
        raise ContractValidationError(f"manifest contract validation failed before write: {exc}") from exc
    _atomic_write_json(Path(path), validated.model_dump(mode="json"))


def write_stage_runtime_manifest(model: StageRuntimeManifestModel, path: str | Path) -> None:
    try:
        validated = StageRuntimeManifestModel.model_validate(model)
    except ValidationError as exc:
        raise ContractValidationError(f"stage runtime manifest contract validation failed before write: {exc}") from exc
    _atomic_write_json(Path(path), validated.model_dump(mode="json"))


def load_stage_summary(path: str | Path) -> StageSummaryModel:
    summary_path = Path(path)
    try:
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise
    except json.JSONDecodeError as exc:
        raise ContractValidationError(f"stage_summary JSON decode failed at {summary_path}: {exc}") from exc
    try:
        return StageSummaryModel.model_validate(payload)
    except ValidationError as exc:
        raise _raise_contract_error("stage_summary", summary_path, exc) from exc


def write_stage_summary(model: StageSummaryModel, path: str | Path) -> None:
    try:
        validated = StageSummaryModel.model_validate(model)
    except ValidationError as exc:
        raise ContractValidationError(f"stage_summary contract validation failed before write: {exc}") from exc
    _atomic_write_json(Path(path), validated.model_dump(mode="json"))
