#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import h5py
import numpy as np


PROJECT_ROOT = Path("/home/ignac/RINGEST")
EVENT_ROOT = PROJECT_ROOT / "runs" / "gwosc_all" / "GW150914"
EXPERIMENT_ROOT = EVENT_ROOT / "experiment_g2_representation_stability"
CHECKPOINT = PROJECT_ROOT / "runs" / "sandbox_v5_b3" / "02_emergent_geometry_engine" / "emergent_geometry_model.pt"
SOURCE_H5 = EVENT_ROOT / "boundary_dataset_v2" / "GW150914__ringdown.h5"
SYSTEM_NAME = "GW150914__ringdown"
INFERENCE_SCRIPT = PROJECT_ROOT / "02_emergent_geometry_engine.py"


@dataclass(frozen=True)
class VariantSpec:
    name: str
    source_g2_key: str
    source_x_key: str
    n_x: int
    x_max: float
    interpolation: str
    note: str


VARIANTS: List[VariantSpec] = [
    VariantSpec("baseline_v2_like", "G2_ringdown", "x_grid", 100, 10.0, "source", "Canonical compat view preserved from boundary_dataset_v2."),
    VariantSpec("raw_like", "G2_ringdown_raw", "x_grid_raw", 256, 10.0, "source", "Closest to original raw ringdown representation."),
    VariantSpec("nx_64", "G2_ringdown_raw", "x_grid_raw", 64, 10.0, "linear", "Raw G2 resampled to n_x=64."),
    VariantSpec("nx_128", "G2_ringdown_raw", "x_grid_raw", 128, 10.0, "linear", "Raw G2 resampled to n_x=128."),
    VariantSpec("xmax_6", "G2_ringdown_raw", "x_grid_raw", 100, 6.0, "linear", "Raw G2 resampled to x_max=6."),
    VariantSpec("xmax_14", "G2_ringdown_raw", "x_grid_raw", 100, 14.0, "linear", "Raw G2 resampled to x_max=14."),
    VariantSpec("interp_linear", "G2_ringdown_raw", "x_grid_raw", 100, 10.0, "linear", "Explicit linear interpolation on x."),
    VariantSpec("interp_logx", "G2_ringdown_raw", "x_grid_raw", 100, 10.0, "logx", "Interpolation in log(x)."),
]


def load_stage02_module():
    spec = importlib.util.spec_from_file_location("stage02_module", INFERENCE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def resample_g2(x_src: np.ndarray, g2_src: np.ndarray, n_x: int, x_max: float, interpolation: str) -> tuple[np.ndarray, np.ndarray]:
    x_target = np.linspace(1e-3, float(x_max), int(n_x), dtype=np.float64)
    x_src = np.asarray(x_src, dtype=np.float64).reshape(-1)
    g2_src = np.asarray(g2_src, dtype=np.float64).reshape(-1)

    if interpolation == "source":
        return x_src.copy(), g2_src.copy()

    if interpolation == "linear":
        g2_target = np.interp(x_target, x_src, g2_src, left=g2_src[0], right=g2_src[-1])
        return x_target, g2_target

    if interpolation == "logx":
        log_src = np.log(np.clip(x_src, 1e-12, None))
        log_target = np.log(np.clip(x_target, 1e-12, None))
        g2_target = np.interp(log_target, log_src, g2_src, left=g2_src[0], right=g2_src[-1])
        return x_target, g2_target

    raise ValueError(f"Unsupported interpolation mode: {interpolation}")


def copy_attrs(src, dst) -> None:
    for key, value in src.attrs.items():
        dst.attrs[key] = value


def make_variant_h5(source_h5: Path, variant_dir: Path, spec: VariantSpec) -> Path:
    variant_dir.mkdir(parents=True, exist_ok=True)
    input_dir = variant_dir / "input_h5"
    input_dir.mkdir(parents=True, exist_ok=True)
    out_h5 = input_dir / f"{SYSTEM_NAME}.h5"

    with h5py.File(source_h5, "r") as src, h5py.File(out_h5, "w") as dst:
        copy_attrs(src, dst)
        boundary_src = src["boundary"]
        boundary_dst = dst.create_group("boundary")
        copy_attrs(boundary_src, boundary_dst)

        x_src = boundary_src[spec.source_x_key][()]
        g2_src = boundary_src[spec.source_g2_key][()]
        x_new, g2_new = resample_g2(x_src, g2_src, spec.n_x, spec.x_max, spec.interpolation)

        for key in boundary_src.keys():
            if key in {"x_grid", "G2_ringdown", "G2_O1"}:
                continue
            boundary_dst.create_dataset(key, data=boundary_src[key][()])

        boundary_dst.create_dataset("x_grid", data=x_new.astype(np.float64))
        boundary_dst.create_dataset("G2_ringdown", data=g2_new.astype(np.float64))
        boundary_dst.create_dataset("G2_O1", data=g2_new.astype(np.float64))

        boundary_dst.attrs["g2_experiment_variant"] = spec.name
        boundary_dst.attrs["g2_source_dataset"] = spec.source_g2_key
        boundary_dst.attrs["x_source_dataset"] = spec.source_x_key
        boundary_dst.attrs["g2_interpolation"] = spec.interpolation
        boundary_dst.attrs["g2_target_n_x"] = int(x_new.size)
        boundary_dst.attrs["g2_target_x_max"] = float(x_new[-1])
        boundary_dst.attrs["g2_variant_note"] = spec.note
        boundary_dst.attrs["compat_mode"] = "standalone_g2_representation_stability"

        if "ringdown_raw" in src:
            src.copy("ringdown_raw", dst)

    manifest = {
        "source_h5": str(source_h5),
        "variant": spec.name,
        "geometries": [
            {
                "name": SYSTEM_NAME,
                "family": "unknown",
                "category": "ringdown",
                "d": int(boundary_dst.attrs.get("d", 4)) if False else 4,
                "file": out_h5.name,
            }
        ],
    }
    # Re-open to read d safely from written file.
    with h5py.File(out_h5, "r") as f:
        manifest["geometries"][0]["d"] = int(f["boundary"].attrs.get("d", 4))
    (input_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return out_h5


def load_features(stage02_module, h5_path: Path) -> np.ndarray:
    with h5py.File(h5_path, "r") as f:
        b = f["boundary"]
        boundary_data: Dict[str, Any] = {}
        for key in b.keys():
            boundary_data[key] = b[key][:]
        for key in b.attrs.keys():
            boundary_data[key] = b.attrs[key]
        operators_raw = f.attrs.get("operators", "[]")
        if isinstance(operators_raw, bytes):
            operators_raw = operators_raw.decode("utf-8")
        operators = json.loads(operators_raw)
    return np.asarray(stage02_module.build_feature_vector(boundary_data, operators), dtype=float)


def run_inference(variant_dir: Path) -> dict[str, Any]:
    input_dir = variant_dir / "input_h5"
    inference_dir = variant_dir / "inference"
    inference_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(INFERENCE_SCRIPT),
        "--mode",
        "inference",
        "--data-dir",
        str(input_dir),
        "--output-dir",
        str(inference_dir),
        "--checkpoint",
        str(CHECKPOINT),
        "--device",
        "cpu",
    ]
    proc = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    (variant_dir / "inference_stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (variant_dir / "inference_stderr.txt").write_text(proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"inference failed for {variant_dir.name}: {proc.stderr or proc.stdout}")

    summary_path = inference_dir / "emergent_geometry_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    return summary["systems"][0]


def block_max_abs(delta: np.ndarray, start: int, end: int) -> float:
    return float(np.max(np.abs(delta[start:end]))) if end > start else 0.0


def main() -> int:
    if not SOURCE_H5.exists():
        raise SystemExit(f"Source H5 not found: {SOURCE_H5}")
    if not CHECKPOINT.exists():
        raise SystemExit(f"Checkpoint not found: {CHECKPOINT}")

    EXPERIMENT_ROOT.mkdir(parents=True, exist_ok=True)
    stage02_module = load_stage02_module()

    manifest = {
        "created_at": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], text=True, capture_output=True, check=True).stdout.strip(),
        "source_h5": str(SOURCE_H5),
        "checkpoint": str(CHECKPOINT),
        "variants": [spec.__dict__ for spec in VARIANTS],
        "note": "Standalone experiment varying only G2/x_grid representation while keeping QNM fixed.",
    }
    (EXPERIMENT_ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    per_variant: Dict[str, Any] = {}
    baseline_name = "baseline_v2_like"
    baseline_vector: np.ndarray | None = None
    baseline_family: str | None = None

    for spec in VARIANTS:
        variant_dir = EXPERIMENT_ROOT / "variants" / spec.name
        input_h5 = make_variant_h5(SOURCE_H5, variant_dir, spec)
        feature_vector = load_features(stage02_module, input_h5)
        inference_result = run_inference(variant_dir)
        per_variant[spec.name] = {
            "variant": spec.__dict__,
            "input_h5": str(input_h5),
            "family_pred": inference_result["family_pred"],
            "zh_pred": inference_result["zh_pred"],
            "feature_vector": feature_vector.tolist(),
        }
        (variant_dir / "features.json").write_text(
            json.dumps(
                {
                    "variant": spec.__dict__,
                    "input_h5": str(input_h5),
                    "feature_vector": feature_vector.tolist(),
                    "family_pred": inference_result["family_pred"],
                    "zh_pred": inference_result["zh_pred"],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

        if spec.name == baseline_name:
            baseline_vector = feature_vector
            baseline_family = inference_result["family_pred"]

    assert baseline_vector is not None
    assert baseline_family is not None

    results_rows: List[Dict[str, Any]] = []
    family_preds = set()
    for spec in VARIANTS:
        rec = per_variant[spec.name]
        vec = np.asarray(rec["feature_vector"], dtype=float)
        delta = vec - baseline_vector
        rec["feature_delta_vs_baseline"] = delta.tolist()
        rec["max_abs_delta_g2"] = block_max_abs(delta, 0, 9)
        rec["max_abs_delta_thermal"] = block_max_abs(delta, 9, 13)
        rec["max_abs_delta_qnm"] = block_max_abs(delta, 13, 16)
        rec["max_abs_delta_response"] = block_max_abs(delta, 16, 18)
        rec["max_abs_delta_global"] = block_max_abs(delta, 18, 20)
        family_preds.add(rec["family_pred"])
        results_rows.append(
            {
                "variant": spec.name,
                "family_pred": rec["family_pred"],
                "zh_pred": rec["zh_pred"],
                "max_abs_delta_g2": rec["max_abs_delta_g2"],
                "max_abs_delta_thermal": rec["max_abs_delta_thermal"],
                "max_abs_delta_qnm": rec["max_abs_delta_qnm"],
                "max_abs_delta_response": rec["max_abs_delta_response"],
                "max_abs_delta_global": rec["max_abs_delta_global"],
            }
        )
        (EXPERIMENT_ROOT / "variants" / spec.name / "features.json").write_text(
            json.dumps(rec, indent=2) + "\n",
            encoding="utf-8",
        )

    overall_verdict = "STABLE" if len(family_preds) == 1 else "UNSTABLE"
    conclusion = (
        "family_pred unchanged across G2/x_grid variants; representation appears operationally stable."
        if overall_verdict == "STABLE"
        else "family_pred changes across G2/x_grid variants; representation sensitivity confirmed."
    )

    summary = {
        "source_h5": str(SOURCE_H5),
        "checkpoint": str(CHECKPOINT),
        "variants_run": [spec.name for spec in VARIANTS],
        "baseline_variant": baseline_name,
        "per_variant": per_variant,
        "overall_verdict": overall_verdict,
        "conclusion_short": conclusion,
        "interpretation_note": "This experiment measures representation robustness only; it is not a physical interpretation of family_pred.",
    }
    (EXPERIMENT_ROOT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    with (EXPERIMENT_ROOT / "results.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "variant",
                "family_pred",
                "zh_pred",
                "max_abs_delta_g2",
                "max_abs_delta_thermal",
                "max_abs_delta_qnm",
                "max_abs_delta_response",
                "max_abs_delta_global",
            ],
        )
        writer.writeheader()
        writer.writerows(results_rows)

    print(f"[OK] source_h5: {SOURCE_H5}")
    print(f"[OK] wrote: {(EXPERIMENT_ROOT / 'manifest.json')}")
    print(f"[OK] wrote: {(EXPERIMENT_ROOT / 'summary.json')}")
    print(f"[OK] wrote: {(EXPERIMENT_ROOT / 'results.csv')}")
    print(f"[OK] overall_verdict: {overall_verdict}")
    print(f"[OK] conclusion_short: {conclusion}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
