#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


import h5py
import numpy as np


# ---------------------------------------------------------------------------
# Variant catalogue  pure config, no paths
# ---------------------------------------------------------------------------

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
    #  Variants requiring G2_ringdown_raw (full-range raw data) 
    # These only work when the source H5 contains G2_ringdown_raw / x_grid_raw.
    VariantSpec("baseline_v2_like",  "G2_ringdown",     "x_grid",     100, 10.0, "source", "Canonical compat view preserved from boundary_dataset_v2."),
    VariantSpec("raw_like",          "G2_ringdown_raw", "x_grid_raw", 256, 10.0, "source", "Closest to original raw ringdown representation."),
    VariantSpec("nx_64",             "G2_ringdown_raw", "x_grid_raw",  64, 10.0, "linear", "Raw G2 resampled to n_x=64."),
    VariantSpec("nx_128",            "G2_ringdown_raw", "x_grid_raw", 128, 10.0, "linear", "Raw G2 resampled to n_x=128."),
    VariantSpec("xmax_6",            "G2_ringdown_raw", "x_grid_raw", 100,  6.0, "linear", "Raw G2 resampled to x_max=6."),
    VariantSpec("xmax_14",           "G2_ringdown_raw", "x_grid_raw", 100, 14.0, "linear", "Raw G2 resampled to x_max=14."),
    VariantSpec("interp_linear",     "G2_ringdown_raw", "x_grid_raw", 100, 10.0, "linear", "Explicit linear interpolation on x."),
    VariantSpec("interp_logx",       "G2_ringdown_raw", "x_grid_raw", 100, 10.0, "logx",   "Interpolation in log(x)."),
    #  Variants using only G2_ringdown (processed) 
    # These work on any source H5 that has G2_ringdown + x_grid (the standard
    # processed representation).  They test whether truncating x_max from the
    # processed correlator changes the gate outcome.
    VariantSpec("processed_xmax_6",  "G2_ringdown",     "x_grid",     100,  6.0, "linear", "Processed G2 resampled to x_max=6 (gate sensitivity test)."),
    VariantSpec("processed_xmax_8",  "G2_ringdown",     "x_grid",     100,  8.0, "linear", "Processed G2 resampled to x_max=8 (gate sensitivity test)."),
    VariantSpec("processed_xmax_14", "G2_ringdown",     "x_grid",     100, 14.0, "linear", "Processed G2 resampled to x_max=14 (gate sensitivity test)."),
    VariantSpec("processed_logx",    "G2_ringdown",     "x_grid",     100, 10.0, "logx",   "Processed G2 with log(x) interpolation."),
]

# Default inference script: sibling of tools/
_DEFAULT_INFERENCE_SCRIPT = Path(__file__).resolve().parent.parent / "02_emergent_geometry_engine.py"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "G2 representation stability experiment.\n"
            "Generates variant H5s from source files in --input-dir, runs stage-02\n"
            "inference on each variant, and compares feature vectors across variants."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--input-dir",
        required=True,
        type=Path,
        metavar="DIR",
        help="Directory containing source .h5 files (one per event).",
    )
    p.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        metavar="DIR",
        help="Root output directory; per-event subdirectories are created here.",
    )
    p.add_argument(
        "--checkpoint",
        type=Path,
        default=None,
        metavar="FILE",
        help="Path to stage-02 model checkpoint (.pt). Required for inference.",
    )
    p.add_argument(
        "--inference-script",
        type=Path,
        default=_DEFAULT_INFERENCE_SCRIPT,
        metavar="FILE",
        help=(
            f"Path to 02_emergent_geometry_engine.py "
            f"(default: {_DEFAULT_INFERENCE_SCRIPT})."
        ),
    )
    p.add_argument(
        "--variants",
        nargs="*",
        default=None,
        metavar="NAME",
        help=(
            "Subset of variant names to run "
            f"(default: all  {[v.name for v in VARIANTS]})."
        ),
    )
    p.add_argument(
        "--baseline-variant",
        default="baseline_v2_like",
        metavar="NAME",
        help="Variant to use as baseline for delta computation (default: baseline_v2_like).",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Process only the first N source H5 files (useful for debug).",
    )
    return p.parse_args(argv)


# ---------------------------------------------------------------------------
# Science helpers (unchanged logic, paths threaded as params)
# ---------------------------------------------------------------------------

def load_stage02_module(inference_script: Path):
    spec = importlib.util.spec_from_file_location("stage02_module", inference_script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["stage02_module"] = module
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


def make_variant_h5(
    source_h5: Path,
    variant_dir: Path,
    spec: VariantSpec,
    system_name: str,  # derived from source_h5.stem at call site
) -> Optional[Path]:
    """
    Build a variant H5 from *source_h5* according to *spec*.

    Returns the path to the written H5, or None if the required source
    datasets are missing (e.g. G2_ringdown_raw not present in older files).
    """
    variant_dir.mkdir(parents=True, exist_ok=True)
    input_dir = variant_dir / "input_h5"
    input_dir.mkdir(parents=True, exist_ok=True)
    out_h5 = input_dir / f"{system_name}.h5"

    try:
        with h5py.File(source_h5, "r") as src, h5py.File(out_h5, "w") as dst:
            copy_attrs(src, dst)
            boundary_src = src["boundary"]
            boundary_dst = dst.create_group("boundary")
            copy_attrs(boundary_src, boundary_dst)

            if spec.source_x_key not in boundary_src or spec.source_g2_key not in boundary_src:
                raise KeyError(
                    f"Source datasets missing: {spec.source_x_key!r} or {spec.source_g2_key!r} "
                    f"not found in {source_h5.name}"
                )

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

    except KeyError as exc:
        print(f"   [SKIP] variant={spec.name}: {exc}")
        if out_h5.exists():
            out_h5.unlink()
        return None

    manifest = {
        "source_h5": str(source_h5),
        "variant": spec.name,
        "geometries": [
            {
                "name": system_name,
                "family": "unknown",
                "category": "ringdown",
                "d": 4,
                "file": out_h5.name,
            }
        ],
    }
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


def run_inference(
    variant_dir: Path,
    inference_script: Path,
    checkpoint: Path,
    cwd: Optional[Path] = None,
) -> dict[str, Any]:
    """
    Run stage-02 inference for a single variant directory.

    Returns a dict that always contains:
      - gate_fail: bool   True when the feature gate blocked the event
      - gate_reason: str  human-readable reason (empty string when gate_fail=False)
      - family_pred: str | None
      - zh_pred: float | None

    A gate_fail is a RESULT, not an error. It means the representation
    produced features outside the training support. The caller should record
    it and continue with other variants.

    Raises RuntimeError only for genuine infrastructure failures (crash, missing
    output file when gate did not trigger, etc.).
    """
    import re

    input_dir = variant_dir / "input_h5"
    inference_dir = variant_dir / "inference"
    inference_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(inference_script),
        "--mode", "inference",
        "--data-dir", str(input_dir),
        "--output-dir", str(inference_dir),
        "--checkpoint", str(checkpoint),
        "--device", "cpu",
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        check=False,
    )
    (variant_dir / "inference_stdout.txt").write_text(proc.stdout, encoding="utf-8")
    (variant_dir / "inference_stderr.txt").write_text(proc.stderr, encoding="utf-8")

    if proc.returncode != 0:
        combined = proc.stdout + proc.stderr
        # GATE_FAIL is a known, expected outcome for out-of-support inputs.
        if "[GATE FAIL]" in combined:
            gate_lines = [l for l in combined.splitlines() if "[GATE FAIL]" in l]
            # Collect all gate reasons (may be one per system)
            reasons = []
            for line in gate_lines:
                m = re.search(r"\[GATE FAIL\][^:]*:\s*(.+)", line)
                reasons.append(m.group(1).strip() if m else line.strip())
            return {
                "gate_fail": True,
                "gate_reason": "; ".join(reasons),
                "family_pred": None,
                "zh_pred": None,
            }
        # Genuine infrastructure failure
        raise RuntimeError(
            f"inference failed for {variant_dir.name}: {proc.stderr or proc.stdout}"
        )

    summary_path = inference_dir / "emergent_geometry_summary.json"
    result = json.loads(summary_path.read_text(encoding="utf-8"))["systems"][0]
    result.setdefault("gate_fail", False)
    result.setdefault("gate_reason", "")
    return result


def block_max_abs(delta: np.ndarray, start: int, end: int) -> float:
    return float(np.max(np.abs(delta[start:end]))) if end > start else 0.0


# ---------------------------------------------------------------------------
# Per-source processing
# ---------------------------------------------------------------------------

def process_source(
    source_h5: Path,
    output_dir: Path,
    variants: List[VariantSpec],
    baseline_name: str,
    stage02_module,
    inference_script: Path,
    checkpoint: Path,
) -> Dict[str, Any]:
    """
    Run the full variant experiment for a single source H5.

    GATE_FAIL is a first-class result: it means the representation produced
    features outside the training support. The experiment records it per-variant
    so the caller can ask "does any x_max variant pass the gate?".

    Returns summary dict (always, even when all variants gate_fail).
    """
    system_name = source_h5.stem
    event_root = output_dir / system_name
    event_root.mkdir(parents=True, exist_ok=True)

    print(f"\n>> {system_name}")

    per_variant: Dict[str, Any] = {}
    baseline_vector: Optional[np.ndarray] = None

    #  Step 1: build variant H5s, compute feature vectors, run inference 
    for spec in variants:
        variant_dir = event_root / "variants" / spec.name
        input_h5 = make_variant_h5(source_h5, variant_dir, spec, system_name)
        if input_h5 is None:
            continue  # source dataset missing, already warned

        # Feature vector: computed from H5 regardless of gate outcome
        try:
            feature_vector = load_features(stage02_module, input_h5)
        except Exception as exc:
            print(f"   [WARN] variant={spec.name}: load_features failed: {exc}")
            feature_vector = None

        # Inference: gate_fail is a result, not an exception
        inference_result = run_inference(variant_dir, inference_script, checkpoint)

        rec: Dict[str, Any] = {
            "variant": spec.__dict__,
            "input_h5": str(input_h5),
            "gate_fail": inference_result.get("gate_fail", False),
            "gate_reason": inference_result.get("gate_reason", ""),
            "family_pred": inference_result.get("family_pred"),
            "zh_pred": inference_result.get("zh_pred"),
            "feature_vector": feature_vector.tolist() if feature_vector is not None else None,
        }
        per_variant[spec.name] = rec

        (variant_dir / "features.json").write_text(
            json.dumps(rec, indent=2) + "\n", encoding="utf-8",
        )

        if spec.name == baseline_name and feature_vector is not None:
            baseline_vector = feature_vector

        gate_tag = " [GATE_FAIL]" if rec["gate_fail"] else ""
        fv_tag = f"  -feats=?" if feature_vector is None else ""
        print(f"   variant={spec.name}{gate_tag}{fv_tag}")

    #  Step 2: compute feature deltas vs baseline 
    results_rows: List[Dict[str, Any]] = []
    gate_outcomes: Dict[str, bool] = {}  # variant_name  gate_fail

    for spec in variants:
        if spec.name not in per_variant:
            continue
        rec = per_variant[spec.name]
        gate_outcomes[spec.name] = rec["gate_fail"]

        vec_raw = rec.get("feature_vector")
        if vec_raw is not None and baseline_vector is not None:
            vec = np.asarray(vec_raw, dtype=float)
            delta = vec - baseline_vector
            rec["feature_delta_vs_baseline"] = delta.tolist()
            rec["max_abs_delta_g2"] = block_max_abs(delta, 0, 9)
            rec["max_abs_delta_thermal"] = block_max_abs(delta, 9, 13)
            rec["max_abs_delta_qnm"] = block_max_abs(delta, 13, 16)
            rec["max_abs_delta_response"] = block_max_abs(delta, 16, 18)
            rec["max_abs_delta_global"] = block_max_abs(delta, 18, 20)
        else:
            rec["feature_delta_vs_baseline"] = None
            rec["max_abs_delta_g2"] = None
            rec["max_abs_delta_thermal"] = None
            rec["max_abs_delta_qnm"] = None
            rec["max_abs_delta_response"] = None
            rec["max_abs_delta_global"] = None

        results_rows.append(
            {
                "variant": spec.name,
                "gate_fail": int(rec["gate_fail"]),
                "gate_reason": rec["gate_reason"],
                "family_pred": rec["family_pred"] or "",
                "zh_pred": rec["zh_pred"] if rec["zh_pred"] is not None else "",
                "max_abs_delta_g2": rec["max_abs_delta_g2"] if rec["max_abs_delta_g2"] is not None else "",
                "max_abs_delta_thermal": rec["max_abs_delta_thermal"] if rec["max_abs_delta_thermal"] is not None else "",
                "max_abs_delta_qnm": rec["max_abs_delta_qnm"] if rec["max_abs_delta_qnm"] is not None else "",
                "max_abs_delta_response": rec["max_abs_delta_response"] if rec["max_abs_delta_response"] is not None else "",
                "max_abs_delta_global": rec["max_abs_delta_global"] if rec["max_abs_delta_global"] is not None else "",
            }
        )
        (event_root / "variants" / spec.name / "features.json").write_text(
            json.dumps(rec, indent=2) + "\n", encoding="utf-8"
        )

    #  Step 3: overall verdict 
    n_pass = sum(1 for v in gate_outcomes.values() if not v)
    n_gate_fail = sum(1 for v in gate_outcomes.values() if v)
    passed_variants = [k for k, v in gate_outcomes.items() if not v]
    failed_variants = [k for k, v in gate_outcomes.items() if v]

    if n_pass == 0 and n_gate_fail > 0:
        overall_verdict = "ALL_GATE_FAIL"
        conclusion = (
            f"All {n_gate_fail} variant(s) blocked by feature gate. "
            "Reducing x_max does not help this event pass the support gate."
        )
    elif n_pass > 0 and n_gate_fail > 0:
        overall_verdict = "MIXED_GATE"
        conclusion = (
            f"{n_pass} variant(s) passed gate ({passed_variants}), "
            f"{n_gate_fail} gate_failed ({failed_variants}). "
            "Representation choice affects gate outcome  x_max sensitivity confirmed."
        )
    elif n_pass > 0 and n_gate_fail == 0:
        # All passed: check family stability among passing variants
        family_preds = {per_variant[k]["family_pred"] for k in passed_variants}
        overall_verdict = "STABLE" if len(family_preds) == 1 else "UNSTABLE"
        conclusion = (
            "All variants passed gate; family_pred unchanged."
            if overall_verdict == "STABLE"
            else f"All variants passed gate; family_pred varies: {sorted(family_preds)}."
        )
    else:
        overall_verdict = "NO_VARIANTS"
        conclusion = "No variants were produced (all source datasets missing)."

    summary: Dict[str, Any] = {
        "system_name": system_name,
        "source_h5": str(source_h5),
        "checkpoint": str(checkpoint),
        "variants_attempted": list(per_variant.keys()),
        "variants_passed_gate": passed_variants,
        "variants_gate_failed": failed_variants,
        "n_pass": n_pass,
        "n_gate_fail": n_gate_fail,
        "baseline_variant": baseline_name,
        "per_variant": per_variant,
        "overall_verdict": overall_verdict,
        "conclusion_short": conclusion,
        "interpretation_note": (
            "This experiment measures representation robustness and gate sensitivity. "
            "GATE_FAIL means the variant's G2 features are outside the model's training support. "
            "MIXED_GATE means the gate outcome depends on the representation choice (x_max, interpolation)."
        ),
    }
    (event_root / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    with (event_root / "results.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "variant", "gate_fail", "gate_reason",
                "family_pred", "zh_pred",
                "max_abs_delta_g2", "max_abs_delta_thermal",
                "max_abs_delta_qnm", "max_abs_delta_response", "max_abs_delta_global",
            ],
        )
        writer.writeheader()
        writer.writerows(results_rows)

    print(f"   verdict={overall_verdict}  pass={n_pass}  gate_fail={n_gate_fail}")
    return summary


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    args = parse_args()

    input_dir: Path = args.input_dir.resolve()
    output_dir: Path = args.output_dir.resolve()
    checkpoint: Optional[Path] = args.checkpoint.resolve() if args.checkpoint else None
    inference_script: Path = args.inference_script.resolve()

    #  Validate inputs (after argparse, so --help always works) 
    if not input_dir.is_dir():
        print(f"[ERROR] --input-dir not found: {input_dir}", file=sys.stderr)
        return 2

    h5_files = sorted(input_dir.glob("*.h5"))
    if not h5_files:
        print(f"[ERROR] No .h5 files found in {input_dir}", file=sys.stderr)
        return 2

    if args.limit is not None:
        h5_files = h5_files[: args.limit]

    if checkpoint is None:
        print("[ERROR] --checkpoint is required for inference.", file=sys.stderr)
        print("        Example: runs/reopen_v1/02_emergent_geometry_engine/emergent_geometry_model.pt", file=sys.stderr)
        return 2
    if not checkpoint.exists():
        print(f"[ERROR] Checkpoint not found: {checkpoint}", file=sys.stderr)
        return 2
    if not inference_script.exists():
        print(f"[ERROR] Inference script not found: {inference_script}", file=sys.stderr)
        return 2

    #  Resolve variant subset 
    if args.variants is not None:
        variant_names = set(args.variants)
        unknown = variant_names - {v.name for v in VARIANTS}
        if unknown:
            print(f"[ERROR] Unknown variant names: {sorted(unknown)}", file=sys.stderr)
            print(f"        Available: {[v.name for v in VARIANTS]}", file=sys.stderr)
            return 2
        active_variants = [v for v in VARIANTS if v.name in variant_names]
    else:
        active_variants = list(VARIANTS)

    baseline_name = args.baseline_variant
    if baseline_name not in {v.name for v in active_variants}:
        print(f"[ERROR] --baseline-variant {baseline_name!r} is not in the active variant set.", file=sys.stderr)
        return 2

    output_dir.mkdir(parents=True, exist_ok=True)

    #  Load stage02 module once 
    print(f"Loading inference module: {inference_script}")
    stage02_module = load_stage02_module(inference_script)

    #  Top-level manifest 
    experiment_manifest = {
        "created_at": datetime.utcnow().isoformat() + "Z",
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "checkpoint": str(checkpoint),
        "inference_script": str(inference_script),
        "n_sources": len(h5_files),
        "variants": [v.__dict__ for v in active_variants],
        "baseline_variant": baseline_name,
        "note": "Standalone experiment varying only G2/x_grid representation while keeping QNM fixed.",
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(experiment_manifest, indent=2) + "\n", encoding="utf-8"
    )

    #  Process each source 
    print(f"\nProcessing {len(h5_files)} source(s) from {input_dir}")
    per_source_summaries: List[Dict[str, Any]] = []
    errors: List[str] = []

    for source_h5 in h5_files:
        try:
            summary = process_source(
                source_h5=source_h5,
                output_dir=output_dir,
                variants=active_variants,
                baseline_name=baseline_name,
                stage02_module=stage02_module,
                inference_script=inference_script,
                checkpoint=checkpoint,
            )
            per_source_summaries.append(summary)
        except Exception as exc:
            msg = f"{source_h5.stem}: {exc}"
            print(f"   [ERROR] {msg}")
            errors.append(msg)

    #  Cohort-level summary 
    verdict_counts: Dict[str, int] = {}
    for s in per_source_summaries:
        v = s.get("overall_verdict", "UNKNOWN")
        verdict_counts[v] = verdict_counts.get(v, 0) + 1

    # Events where at least one variant passed the gate
    events_with_any_pass = [
        s["system_name"] for s in per_source_summaries if s.get("n_pass", 0) > 0
    ]

    cohort_summary = {
        "created_at": datetime.utcnow().isoformat() + "Z",
        "input_dir": str(input_dir),
        "n_sources": len(h5_files),
        "n_ok": len(per_source_summaries),
        "n_errors": len(errors),
        "verdict_counts": verdict_counts,
        "n_events_any_pass": len(events_with_any_pass),
        "events_with_any_pass": events_with_any_pass,
        "errors": errors,
        "per_source": per_source_summaries,
    }
    (output_dir / "cohort_summary.json").write_text(
        json.dumps(cohort_summary, indent=2) + "\n", encoding="utf-8"
    )

    print(f"\n{'=' * 60}")
    print(f"[OK] output_dir:  {output_dir}")
    print(f"[OK] manifest:    {output_dir / 'manifest.json'}")
    print(f"[OK] cohort_summary: {output_dir / 'cohort_summary.json'}")
    print(f"[OK] sources processed: {len(per_source_summaries)}/{len(h5_files)}")
    print(f"[OK] verdict breakdown: {verdict_counts}")
    if events_with_any_pass:
        print(f"[OK] events where 1 variant passed gate ({len(events_with_any_pass)}): {events_with_any_pass}")
    else:
        print(f"[INFO] no event had any variant pass the gate  all blocked by G2_large_x")
    if errors:
        print(f"[WARN] {len(errors)} infrastructure error(s)  see cohort_summary.json")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
