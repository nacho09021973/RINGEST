#!/usr/bin/env python3
"""
run_softwall_gubserrocha_baseline.py

Baseline runner for the preregistered soft_wall vs gubser_rocha experiment.

This tool executes only the canonical baseline block described in:
  docs/preregister_softwall_vs_gubserrocha.md

It does NOT finalize the full preregistered verdict, because the one-at-a-time
sensitivity blocks (resolution / hyperparameters / cohort / normalization) are
outside this baseline runner.  Its purpose is to:

  - freeze the canonical d=4/test cohort from a concrete run
  - compute the provisional primary observable BA_binaria_test_d4
  - compute bootstrap and permutation uncertainty summaries
  - compute preregistered integral secondary observables over boundary/bulk
  - emit a structured report that downstream sensitivity rails can reuse
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import h5py
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUN_ROOT = REPO_ROOT / "runs" / "tier_a_ext_discrim_20260414_codex_run1"
DEFAULT_SANDBOX_DIR = DEFAULT_RUN_ROOT / "01_generate_sandbox_geometries"
DEFAULT_ENGINE_SUMMARY = DEFAULT_RUN_ROOT / "02_emergent_geometry_engine" / "emergent_geometry_summary.json"
DEFAULT_OUTPUT_DIR = DEFAULT_RUN_ROOT / "experiment" / "softwall_vs_gubserrocha_baseline"
CANONICAL_FAMILIES = ("gubser_rocha", "soft_wall")
CANONICAL_CATEGORY = "test"
CANONICAL_D = 4


@dataclass(frozen=True)
class CohortMember:
    name: str
    family_truth: str
    family_pred: str
    category: str
    h5_path: Path


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _safe_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Run the baseline preregistered soft_wall vs gubser_rocha experiment.")
    ap.add_argument("--sandbox-dir", type=Path, default=DEFAULT_SANDBOX_DIR)
    ap.add_argument("--engine-summary-json", type=Path, default=DEFAULT_ENGINE_SUMMARY)
    ap.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    ap.add_argument("--n-bootstrap", type=int, default=2000, help="Number of stratified bootstrap resamples.")
    ap.add_argument("--n-permutation", type=int, default=2000, help="Number of label permutations.")
    ap.add_argument("--seed", type=int, default=42)
    return ap.parse_args(argv)


def _load_engine_summary(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"engine summary not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid engine summary JSON at {path}: {exc}") from exc


def _detect_canonical_members(sandbox_dir: Path, engine_summary: Dict[str, Any]) -> List[CohortMember]:
    systems = engine_summary.get("systems", [])
    if not isinstance(systems, list):
        raise ValueError("engine summary must contain a top-level 'systems' list")

    by_name: Dict[str, Dict[str, Any]] = {}
    for item in systems:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("system_name")
        if isinstance(name, str):
            by_name[name] = item

    members: List[CohortMember] = []
    for h5_path in sorted(sandbox_dir.glob("*.h5")):
        name = h5_path.stem
        if name not in by_name:
            continue
        item = by_name[name]
        family_truth = str(item.get("family_truth", ""))
        family_pred = str(item.get("family_pred", ""))
        category = str(item.get("category", ""))
        if family_truth not in CANONICAL_FAMILIES:
            continue
        if category != CANONICAL_CATEGORY:
            continue
        with h5py.File(h5_path, "r") as h5f:
            d_val = int(h5f.attrs.get("d", -1))
        if d_val != CANONICAL_D:
            continue
        members.append(
            CohortMember(
                name=name,
                family_truth=family_truth,
                family_pred=family_pred,
                category=category,
                h5_path=h5_path,
            )
        )

    counts = defaultdict(int)
    for m in members:
        counts[m.family_truth] += 1
    if tuple(sorted(counts.keys())) != tuple(sorted(CANONICAL_FAMILIES)):
        raise ValueError(f"canonical cohort detection failed; found family counts={dict(counts)}")
    return members


def _balanced_accuracy(y_true: Iterable[str], y_pred: Iterable[str]) -> Tuple[float, Dict[str, float]]:
    truth = list(y_true)
    pred = list(y_pred)
    sens: Dict[str, float] = {}
    for fam in CANONICAL_FAMILIES:
        idx = [i for i, y in enumerate(truth) if y == fam]
        if not idx:
            raise ValueError(f"family {fam} absent from canonical cohort")
        ok = sum(1 for i in idx if pred[i] == fam)
        sens[fam] = ok / len(idx)
    ba = 0.5 * (sens[CANONICAL_FAMILIES[0]] + sens[CANONICAL_FAMILIES[1]])
    return float(ba), sens


def _bootstrap_ba(members: List[CohortMember], n_bootstrap: int, seed: int) -> Dict[str, Any]:
    rng = np.random.default_rng(seed)
    fam_to_members: Dict[str, List[CohortMember]] = {fam: [m for m in members if m.family_truth == fam] for fam in CANONICAL_FAMILIES}
    bas: List[float] = []
    for _ in range(n_bootstrap):
        sample: List[CohortMember] = []
        for fam in CANONICAL_FAMILIES:
            group = fam_to_members[fam]
            indices = rng.integers(0, len(group), size=len(group))
            sample.extend(group[i] for i in indices)
        ba, _ = _balanced_accuracy((m.family_truth for m in sample), (m.family_pred for m in sample))
        bas.append(ba)
    arr = np.asarray(bas, dtype=float)
    return {
        "n_bootstrap": n_bootstrap,
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "q025": float(np.quantile(arr, 0.025)),
        "q50": float(np.quantile(arr, 0.5)),
        "q975": float(np.quantile(arr, 0.975)),
    }


def _permutation_ba(members: List[CohortMember], n_perm: int, seed: int, observed_ba: float) -> Dict[str, Any]:
    rng = np.random.default_rng(seed + 1)
    truth = np.asarray([m.family_truth for m in members], dtype=object)
    pred = np.asarray([m.family_pred for m in members], dtype=object)
    vals: List[float] = []
    for _ in range(n_perm):
        perm = truth.copy()
        rng.shuffle(perm)
        ba, _ = _balanced_accuracy(perm.tolist(), pred.tolist())
        vals.append(ba)
    arr = np.asarray(vals, dtype=float)
    p_ge = float((np.sum(arr >= observed_ba) + 1) / (len(arr) + 1))
    return {
        "n_permutation": n_perm,
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "q95": float(np.quantile(arr, 0.95)),
        "p_value_ge_observed": p_ge,
    }


def _region_masks(grid: np.ndarray) -> Dict[str, np.ndarray]:
    lo = float(np.min(grid))
    hi = float(np.max(grid))
    span = hi - lo
    t1 = lo + span / 3.0
    t2 = lo + 2.0 * span / 3.0
    uv = grid <= t1
    mid = (grid > t1) & (grid <= t2)
    ir = grid > t2
    return {"UV": uv, "MID": mid, "IR": ir}


def _area_abs_diff(grid: np.ndarray, a: np.ndarray, b: np.ndarray, mask: np.ndarray) -> float:
    x = np.asarray(grid[mask], dtype=float)
    if x.size < 2:
        return 0.0
    ya = np.asarray(a[mask], dtype=float)
    yb = np.asarray(b[mask], dtype=float)
    return float(np.trapezoid(np.abs(ya - yb), x))


def _load_family_arrays(members: List[CohortMember]) -> Dict[str, Any]:
    by_family: Dict[str, Dict[str, List[np.ndarray]]] = {
        fam: {"x_grid": [], "z_grid": [], "G2_O1": [], "G2_O2": [], "G2_O3": [], "A_truth": [], "f_truth": []}
        for fam in CANONICAL_FAMILIES
    }
    for m in members:
        with h5py.File(m.h5_path, "r") as h5f:
            boundary = h5f["boundary"]
            by_family[m.family_truth]["x_grid"].append(np.asarray(boundary["x_grid"][()], dtype=float))
            by_family[m.family_truth]["G2_O1"].append(np.asarray(boundary["G2_O1"][()], dtype=float))
            by_family[m.family_truth]["G2_O2"].append(np.asarray(boundary["G2_O2"][()], dtype=float))
            by_family[m.family_truth]["G2_O3"].append(np.asarray(boundary["G2_O3"][()], dtype=float))
            by_family[m.family_truth]["z_grid"].append(np.asarray(h5f["z_grid"][()], dtype=float))
            by_family[m.family_truth]["A_truth"].append(np.asarray(h5f["bulk_truth"]["A_truth"][()], dtype=float))
            by_family[m.family_truth]["f_truth"].append(np.asarray(h5f["bulk_truth"]["f_truth"][()], dtype=float))
    return by_family


def _normalize_log_g2(g2: np.ndarray, x_grid: np.ndarray) -> np.ndarray:
    masks = _region_masks(x_grid)
    uv = masks["UV"]
    uv_mean = float(np.mean(g2[uv])) if np.any(uv) else float(np.mean(g2))
    uv_mean = max(uv_mean, 1e-12)
    return np.log(np.clip(g2 / uv_mean, 1e-12, None))


def _secondary_metrics(members: List[CohortMember]) -> Dict[str, Any]:
    family_data = _load_family_arrays(members)
    g2_regions: Dict[str, Dict[str, float]] = {}

    fam_ref = CANONICAL_FAMILIES[0]
    x_ref = family_data[fam_ref]["x_grid"][0]
    z_ref = family_data[fam_ref]["z_grid"][0]
    x_masks = _region_masks(x_ref)
    z_masks = _region_masks(z_ref)

    for op in ("G2_O1", "G2_O2", "G2_O3"):
        per_family_mean: Dict[str, np.ndarray] = {}
        for fam in CANONICAL_FAMILIES:
            curves = []
            for x_grid, g2 in zip(family_data[fam]["x_grid"], family_data[fam][op]):
                if not np.allclose(x_grid, x_ref):
                    g2 = np.interp(x_ref, x_grid, g2, left=g2[0], right=g2[-1])
                curves.append(_normalize_log_g2(np.asarray(g2, dtype=float), x_ref))
            per_family_mean[fam] = np.mean(np.stack(curves, axis=0), axis=0)
        op_metrics: Dict[str, float] = {}
        for region, mask in x_masks.items():
            op_metrics[region] = _area_abs_diff(x_ref, per_family_mean["soft_wall"], per_family_mean["gubser_rocha"], mask)
        g2_regions[op] = op_metrics

    g2_total = float(np.mean([sum(v.values()) for v in g2_regions.values()]))
    g2_region_mean = {
        region: float(np.mean([g2_regions[op][region] for op in g2_regions]))
        for region in ("UV", "MID", "IR")
    }

    bulk_regions: Dict[str, Dict[str, float]] = {}
    for field in ("A_truth", "f_truth"):
        per_family_mean = {}
        for fam in CANONICAL_FAMILIES:
            curves = []
            for z_grid, arr in zip(family_data[fam]["z_grid"], family_data[fam][field]):
                if not np.allclose(z_grid, z_ref):
                    arr = np.interp(z_ref, z_grid, arr, left=arr[0], right=arr[-1])
                curves.append(np.asarray(arr, dtype=float))
            per_family_mean[fam] = np.mean(np.stack(curves, axis=0), axis=0)
        field_metrics: Dict[str, float] = {}
        for region, mask in z_masks.items():
            field_metrics[region] = _area_abs_diff(z_ref, per_family_mean["soft_wall"], per_family_mean["gubser_rocha"], mask)
        bulk_regions[field] = field_metrics

    bulk_total = float(sum(sum(v.values()) for v in bulk_regions.values()))
    region_shares = {}
    denom = g2_total + bulk_total
    for region in ("UV", "MID", "IR"):
        contrib = g2_region_mean[region] + bulk_regions["A_truth"][region] + bulk_regions["f_truth"][region]
        region_shares[region] = float(contrib / denom) if denom > 0 else 0.0

    return {
        "g2_by_operator": g2_regions,
        "g2_region_mean": g2_region_mean,
        "D_G2_total": g2_total,
        "bulk_by_field": bulk_regions,
        "D_bulk_total": bulk_total,
        "region_share_of_total": region_shares,
    }


def _baseline_status(primary_ba: float, bootstrap_q025: float) -> str:
    if primary_ba >= 0.75 and bootstrap_q025 > 0.50:
        return "SEPARATION_SIGNAL_PRESENT"
    return "NO_BASELINE_SIGNAL"


def _write_cohort_csv(path: Path, members: List[CohortMember]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["name", "family_truth", "family_pred", "category", "h5_path"],
        )
        writer.writeheader()
        for m in members:
            writer.writerow(
                {
                    "name": m.name,
                    "family_truth": m.family_truth,
                    "family_pred": m.family_pred,
                    "category": m.category,
                    "h5_path": str(m.h5_path),
                }
            )


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    sandbox_dir = args.sandbox_dir.resolve()
    engine_summary_json = args.engine_summary_json.resolve()
    output_dir = args.output_dir.resolve()

    if not sandbox_dir.exists():
        print(f"ERROR: sandbox dir not found: {sandbox_dir}", file=sys.stderr)
        return 2
    if not engine_summary_json.exists():
        print(f"ERROR: engine summary not found: {engine_summary_json}", file=sys.stderr)
        return 2

    engine_summary = _load_engine_summary(engine_summary_json)
    members = _detect_canonical_members(sandbox_dir, engine_summary)
    if len(members) == 0:
        print("ERROR: canonical cohort is empty", file=sys.stderr)
        return 2

    ba, sensitivity = _balanced_accuracy((m.family_truth for m in members), (m.family_pred for m in members))
    bootstrap = _bootstrap_ba(members, n_bootstrap=args.n_bootstrap, seed=args.seed)
    permutation = _permutation_ba(members, n_perm=args.n_permutation, seed=args.seed, observed_ba=ba)
    secondary = _secondary_metrics(members)
    status = _baseline_status(ba, bootstrap["q025"])

    output_dir.mkdir(parents=True, exist_ok=True)
    cohort_csv = output_dir / "canonical_cohort_members.csv"
    report_json = output_dir / "baseline_report.json"
    manifest_json = output_dir / "manifest.json"

    _write_cohort_csv(cohort_csv, members)

    report = {
        "schema_version": "softwall-gubserrocha-baseline-v1",
        "created_at": _utc_now_iso(),
        "mode": "baseline_only",
        "cohort_definition": {
            "families": list(CANONICAL_FAMILIES),
            "category": CANONICAL_CATEGORY,
            "d": CANONICAL_D,
            "n_members": len(members),
            "n_by_family": {
                fam: sum(1 for m in members if m.family_truth == fam)
                for fam in CANONICAL_FAMILIES
            },
        },
        "primary_observable": {
            "name": "BA_binaria_test_d4",
            "value": ba,
            "sensitivity_by_family": sensitivity,
            "bootstrap": bootstrap,
            "permutation": permutation,
            "decision_thresholds": {
                "ba_min": 0.75,
                "bootstrap_q025_min": 0.50,
            },
        },
        "secondary_observables": secondary,
        "baseline_status": status,
        "preregister_final_verdict": "PENDING_SENSITIVITY_BLOCKS",
        "notes": [
            "This runner executes only the canonical baseline block.",
            "The full preregistered verdict remains pending until one-at-a-time sensitivity rails are executed.",
        ],
    }
    manifest = {
        "created_at": _utc_now_iso(),
        "script": _safe_rel(Path(__file__)),
        "command": " ".join(sys.argv),
        "inputs": {
            "sandbox_dir": _safe_rel(sandbox_dir),
            "engine_summary_json": _safe_rel(engine_summary_json),
        },
        "outputs": {
            "canonical_cohort_members_csv": _safe_rel(cohort_csv),
            "baseline_report_json": _safe_rel(report_json),
        },
    }

    _write_json(report_json, report)
    _write_json(manifest_json, manifest)
    print(f"[OK] baseline_status={status}  BA_binaria_test_d4={ba:.6f}")
    print(f"[OK] report: {report_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
