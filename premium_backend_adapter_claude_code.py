#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

SCRIPT_VERSION = "premium_backend_adapter_claude_code.py v0.2-beta"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def load_boundary_h5(path: Path) -> dict:
    """
    Abre baseline_boundary_h5 y enumera todos los datasets presentes.
    No asume estructura de claves — itera lo que existe.
    Devuelve dict con 'path', 'datasets', 'attrs'.
    """
    import h5py  # lazy: no falla en entornos sin h5py hasta que se invoca

    result: dict[str, Any] = {
        "path": str(path),
        "datasets": {},
        "attrs": {},
    }

    def _visit(name: str, obj: Any) -> None:
        if isinstance(obj, h5py.Dataset):
            try:
                arr = np.asarray(obj[()])
                if arr.dtype.kind in ("O", "S", "U"):
                    arr = np.array(
                        [x.decode() if isinstance(x, bytes) else str(x) for x in arr.flat],
                        dtype=object,
                    ).reshape(arr.shape)
                result["datasets"][name] = arr
            except Exception as exc:
                result["datasets"][name] = f"<unreadable: {exc}>"

    with h5py.File(path, "r") as f:
        for k, v in f.attrs.items():
            try:
                result["attrs"][k] = v.item() if hasattr(v, "item") else str(v)
            except Exception:
                result["attrs"][k] = str(v)
        f.visititems(_visit)

    return result


def extract_premium_features(
    boundary_data: dict,
) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    """
    Deriva features mínimas y auditables de boundary_data.
    Solo usa campos presentes en el h5 — no inventa datos.
    Devuelve (feature_dict, summary_metrics).
    """
    feature_dict: dict[str, np.ndarray] = {}
    feature_names: list[str] = []

    datasets = boundary_data.get("datasets", {})
    attrs = boundary_data.get("attrs", {})

    # Metadatos escalares presentes en attrs (sample_rate, t_start, etc.)
    for meta_key in ("sample_rate", "t_start", "t_end", "duration", "event_id"):
        if meta_key in attrs:
            val = attrs[meta_key]
            if isinstance(val, (int, float)):
                feat = f"meta__{meta_key}"
                feature_dict[feat] = np.array([val], dtype=np.float64)
                feature_names.append(feat)

    # Features por dataset numérico
    for ds_name, arr in datasets.items():
        if isinstance(arr, str):  # unreadable — omitir
            continue
        if not isinstance(arr, np.ndarray):
            continue
        if arr.dtype.kind not in ("f", "i", "u", "c"):
            continue
        if arr.size == 0:
            continue

        if arr.dtype.kind == "c":
            flat = np.abs(arr).astype(np.float64).ravel()
        else:
            flat = arr.astype(np.float64).ravel()
        safe = ds_name.replace("/", "__")

        for feat, val in (
            (f"{safe}__n_samples", np.array([float(flat.size)])),
            (f"{safe}__mean",      np.array([float(np.mean(flat))])),
            (f"{safe}__std",       np.array([float(np.std(flat))])),
            (f"{safe}__peak_abs",  np.array([float(np.max(np.abs(flat)))])),
        ):
            feature_dict[feat] = val.astype(np.float64)
            feature_names.append(feat)

        if flat.size > 16:
            feat_rms = f"{safe}__rms"
            feature_dict[feat_rms] = np.array([float(np.sqrt(np.mean(flat**2)))], dtype=np.float64)
            feature_names.append(feat_rms)

    # Puntero auditable a la fuente — sin object arrays
    feature_dict["source_boundary_h5"] = np.array([str(boundary_data["path"])], dtype=str)

    n_real = len([k for k in feature_dict if k != "source_boundary_h5"])
    summary_metrics: dict[str, Any] = {
        "n_features": n_real,
        "is_placeholder": False,
        "compute_ran": True,
        "feature_names": feature_names,
    }
    return feature_dict, summary_metrics


def run_local_compute(stage_dir: Path, request: dict) -> dict:
    """
    Extrae features reales del h5.
    Escribe premium_features.npz y actualiza provenance.json y premium_estimate.json.
    NO toca stage_summary.json — sigue siendo DEGRADED (gate de gobernanza).
    Devuelve un dict de resultados para trazabilidad.
    """
    outputs_dir = stage_dir / "outputs"
    h5_path = Path(request["input_artifacts"]["baseline_boundary_h5"]).resolve()

    started_at = utc_now()
    boundary_data = load_boundary_h5(h5_path)
    feature_dict, summary_metrics = extract_premium_features(boundary_data)
    finished_at = utc_now()

    # Escribir premium_features.npz real
    feature_path = outputs_dir / "premium_features.npz"
    np.savez(feature_path, **feature_dict)

    # Actualizar provenance.json con trazabilidad de compute
    provenance_path = outputs_dir / "provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance["compute_started_at"] = started_at
    provenance["compute_finished_at"] = finished_at
    provenance["n_datasets_found"] = len(boundary_data.get("datasets", {}))
    provenance["n_features_extracted"] = summary_metrics["n_features"]
    provenance["notes"] = [
        "Compute real ejecutado por premium_backend_adapter_claude_code",
        "Backend aún deshabilitado — stage permanece DEGRADED",
        "Features son reales y auditables, no placeholders",
    ]
    write_json(provenance_path, provenance)

    # Actualizar premium_estimate.json con summary_metrics reales
    # status permanece DEGRADED — lo controla el gate de backend_enabled
    estimate_path = outputs_dir / "premium_estimate.json"
    estimate = json.loads(estimate_path.read_text(encoding="utf-8"))
    estimate["summary_metrics"] = {
        **summary_metrics,
        "backend_enabled": bool(request.get("backend_enabled", False)),
    }
    estimate["feature_paths"]["premium_features_npz"] = str(feature_path)
    estimate["provenance_hash"] = hashlib.sha256(
        json.dumps(provenance, sort_keys=True).encode("utf-8")
    ).hexdigest()
    # status no se toca: sigue siendo DEGRADED
    write_json(estimate_path, estimate)

    return {
        "compute_started_at": started_at,
        "compute_finished_at": finished_at,
        "n_datasets": len(boundary_data.get("datasets", {})),
        "n_features": summary_metrics["n_features"],
        "feature_path": str(feature_path),
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Materialize a canonical Claude Code handoff from backend_request.json"
    )
    ap.add_argument("--stage-dir", required=True, help="runs/<run_id>/premium_estimator")
    args = ap.parse_args()

    stage_dir = Path(args.stage_dir).resolve()
    outputs_dir = stage_dir / "outputs"
    request_path = outputs_dir / "backend_request.json"
    estimate_path = outputs_dir / "premium_estimate.json"
    provenance_path = outputs_dir / "provenance.json"
    handoff_dir = outputs_dir / "claude_code_handoff"

    if not request_path.exists():
        raise SystemExit(f"[ERROR] Missing contractual input: {request_path}")
    if not estimate_path.exists():
        raise SystemExit(f"[ERROR] Missing contractual input: {estimate_path}")
    if not provenance_path.exists():
        raise SystemExit(f"[ERROR] Missing contractual input: {provenance_path}")

    request = json.loads(request_path.read_text(encoding="utf-8"))
    estimate = json.loads(estimate_path.read_text(encoding="utf-8"))
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))

    backend_enabled = bool(request.get("backend_enabled", False))
    request_status = request.get("request_status", "DISABLED")

    # --- Compute real (siempre, independiente del gate) ---
    compute_results = run_local_compute(stage_dir, request)
    print(
        f"[COMPUTE] Features extraídas: {compute_results['n_features']} "
        f"de {compute_results['n_datasets']} datasets h5"
    )

    # --- Gate de gobernanza: PASS prohibido mientras backend deshabilitado ---
    gate_open = backend_enabled and request_status != "DISABLED"
    if not gate_open:
        print(
            "[DEGRADED] Backend deshabilitado (backend_enabled=False o "
            "request_status=DISABLED). stage_summary.json permanece DEGRADED. "
            "Downstream bloqueado."
        )
    # stage_summary.json no se toca aquí — el gate lo gestiona premium_estimator.py

    # Re-leer artefactos actualizados por run_local_compute para el handoff
    estimate = json.loads(estimate_path.read_text(encoding="utf-8"))
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))

    handoff_dir.mkdir(parents=True, exist_ok=True)

    invocation = {
        "created_at": utc_now(),
        "script": SCRIPT_VERSION,
        "backend_name": request.get("backend_name"),
        "request_status": request_status,
        "stage_dir": str(stage_dir),
        "allowed_root": request.get("write_constraints", {}).get("allowed_root"),
        "input_artifacts": request.get("input_artifacts", {}),
        "required_outputs": request.get("required_outputs", []),
        "compute_results": compute_results,
        "notes": [
            "This handoff package is canonical and auditable",
            "External backend must not write outside allowed_root",
            "Downstream remains blocked unless premium_estimator stage reaches PASS",
        ],
    }
    write_json(handoff_dir / "backend_invocation.json", invocation)

    prompt = f"""# Claude Code handoff

## Goal
Produce a premium event-level estimate for:
- event_id: {request.get("event_id")}
- backend_name: {request.get("backend_name")}

## Contract
- Allowed root: {request.get("write_constraints", {}).get("allowed_root")}
- Do not write outside the allowed root
- Do not enable downstream unless stage_summary.json is PASS
- Preserve provenance and estimator identity
- Do not invent ambiguous intermediate datasets

## Available canonical inputs
- backend_request.json
- premium_estimate.json
- provenance.json

## Current stage status
- premium_estimate.status = {estimate.get("status")}
- estimator_name = {estimate.get("estimator_name")}
- estimator_version = {estimate.get("estimator_version")}
- compute_ran = {estimate.get("summary_metrics", {}).get("compute_ran", False)}
- n_features = {estimate.get("summary_metrics", {}).get("n_features", 0)}

## Required canonical outputs
"""
    for item in request.get("required_outputs", []):
        prompt += f"- {item}\n"

    prompt += """
## Expected behavior
If the backend is disabled or not implemented, leave the stage in DEGRADED.
If a real premium estimate is produced, update only canonical artifacts under the allowed root.
"""
    (handoff_dir / "claude_code_task.md").write_text(prompt, encoding="utf-8")

    manifest = {
        "created_at": utc_now(),
        "script": SCRIPT_VERSION,
        "stage_dir": str(stage_dir),
        "handoff_dir": str(handoff_dir),
        "compute_results": compute_results,
        "artifacts": {
            "backend_invocation_json": str(handoff_dir / "backend_invocation.json"),
            "claude_code_task_md": str(handoff_dir / "claude_code_task.md"),
        },
    }
    write_json(handoff_dir / "handoff_manifest.json", manifest)

    print(f"[OK] Claude Code handoff written under: {handoff_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
