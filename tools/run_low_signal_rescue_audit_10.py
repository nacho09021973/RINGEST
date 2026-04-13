#!/usr/bin/env python3
"""
Run a non-canonical rescue audit over the 10 events classified as
low_signal_or_uninformative in the fullcohort_90 physics probe.

Strategy:
  - Re-run decay_type_discrimination with a relaxed window (x_min=3.0)
    on the 10 excluded events only.
  - Compare against original x_min=4.0 results.
  - Use stage04 correlator quality as a secondary rescue signal.
  - Rescue criterion:
      PRIMARY: at least one model achieves R² >= 0.3 at x_min=3.0
      SECONDARY: stage04 correlation_quality >= 0.3
      RESCUE requires PRIMARY pass. SECONDARY alone is insufficient.
  - Produce a taxonomic rescue decision per event and an aggregate cohort update.

Does NOT touch canonical stages, premium, or veredictos existentes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.decay_type_discrimination import process_event  # noqa: E402

RUNS_ROOT_DEFAULT = REPO_ROOT / "runs"
STAGE_NAME = "experiment/low_signal_rescue_audit_10"

# The 10 excluded events (from cohort_partition.json)
EXCLUDED_10 = [
    "GW170817__ringdown",
    "GW190412_053044__ringdown",
    "GW190517_055101__ringdown",
    "GW190521_030229__ringdown",
    "GW190707_093326__ringdown",
    "GW190708_232457__ringdown",
    "GW190910_112807__ringdown",
    "GW191109_010717__ringdown",
    "GW191216_213338__ringdown",
    "GW200224_222234__ringdown",
]

# Source paths
INPUT_DIR_DEFAULT = REPO_ROOT / "runs" / "reopen_v1" / "90_event_xmax6_stage02_input"
ORIGINAL_PROBE_DIR = (
    REPO_ROOT / "runs" / "fullcohort_90_physics_probe_20260413_rerun1"
    / "experiment" / "fullcohort_90_physics_probe" / "outputs"
)
COHORT_AUDIT_DIR = (
    REPO_ROOT / "runs" / "cohort_unification_audit_90_20260413"
    / "experiment" / "cohort_unification_audit_90" / "outputs"
)
GEOMETRY33_SUMMARY = (
    REPO_ROOT / "runs" / "reopen_v1"
    / "04_geometry_physics_contracts_33_event_effective_contract_pass_xmax6_v1"
    / "geometry_contracts_summary.json"
)
GEOMETRY55_SUMMARY = (
    REPO_ROOT / "runs" / "reopen_v1"
    / "04_geometry_physics_contracts_55_event_effective_ood_xmax6_v1"
    / "geometry_contracts_summary.json"
)

# Rescue thresholds
R2_RESCUE_THRESHOLD = 0.3
STAGE04_QUALITY_THRESHOLD = 0.3
X_MIN_RESCUE = 3.0
X_MIN_ORIGINAL = 4.0
G2_MIN = 1e-6


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp_", suffix=path.suffix or ".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(_jsonify(payload), indent=2, ensure_ascii=False))
            fh.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _jsonify(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonify(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonify(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def _stage04_contract_map(summary_path: Path) -> dict[str, dict[str, Any]]:
    payload = _load_json(summary_path)
    out: dict[str, dict[str, Any]] = {}
    for item in payload.get("contracts", []):
        out[item["name"]] = {
            "contract_mode": item.get("correlator_structure", {}).get("contract_mode"),
            "has_spatial_structure": item.get("correlator_structure", {}).get("has_spatial_structure"),
            "is_monotonic_decay": item.get("correlator_structure", {}).get("is_monotonic_decay"),
            "has_power_law": item.get("correlator_structure", {}).get("has_power_law"),
            "log_slope": item.get("correlator_structure", {}).get("log_slope"),
            "correlation_quality": item.get("correlator_structure", {}).get("correlation_quality"),
        }
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rescue audit for the 10 low-signal excluded events.")
    ap.add_argument("--run-id", required=True, help="Run identifier under runs/<run_id>/")
    ap.add_argument("--runs-root", type=Path, default=RUNS_ROOT_DEFAULT)
    ap.add_argument("--input-dir", type=Path, default=INPUT_DIR_DEFAULT)
    ap.add_argument("--x-min-rescue", type=float, default=X_MIN_RESCUE,
                    help="Relaxed window x_min for rescue attempt (default: 3.0)")
    ap.add_argument("--r2-threshold", type=float, default=R2_RESCUE_THRESHOLD)
    ap.add_argument("--stage04-quality-threshold", type=float, default=STAGE04_QUALITY_THRESHOLD)
    return ap


def main() -> int:
    args = build_parser().parse_args()
    runs_root = Path(args.runs_root).resolve(strict=False)
    input_dir = Path(args.input_dir).resolve(strict=False)
    stage_dir = runs_root / args.run_id / STAGE_NAME
    outputs_dir = stage_dir / "outputs"

    stdout_lines: list[str] = []

    def log(msg: str) -> None:
        stdout_lines.append(msg)
        print(msg)

    # --- Validate inputs ---
    required_paths = [input_dir, ORIGINAL_PROBE_DIR, COHORT_AUDIT_DIR, GEOMETRY33_SUMMARY, GEOMETRY55_SUMMARY]
    missing = [str(p) for p in required_paths if not p.exists()]
    if missing:
        print(f"FATAL: Missing required inputs: {missing}", file=sys.stderr)
        return 2
    if outputs_dir.exists():
        print(f"FATAL: Output directory already exists: {outputs_dir}", file=sys.stderr)
        return 2

    stage_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=False)

    # --- Load prior data ---
    original_probe = _load_json(ORIGINAL_PROBE_DIR / "per_event_physics_probe.json")
    recommended_cohort = _load_json(COHORT_AUDIT_DIR / "recommended_cohort.json")
    stage04_map = _stage04_contract_map(GEOMETRY33_SUMMARY)
    stage04_map.update(_stage04_contract_map(GEOMETRY55_SUMMARY))

    # --- Phase 1: Diagnostic of the 10 ---
    log(f"=== Phase 1: Diagnostic of {len(EXCLUDED_10)} excluded events ===")
    diagnostics = []
    for event_name in EXCLUDED_10:
        orig = original_probe.get(event_name, {})
        stage04 = stage04_map.get(event_name)
        diag = {
            "event_name": event_name,
            "event_id": event_name.replace("__ringdown", ""),
            "original_classification": orig.get("decay_classification", "UNKNOWN"),
            "original_reason": orig.get("decay_reason", "UNKNOWN"),
            "original_r2_exp": orig.get("r2_exponential", 0.0),
            "original_r2_pow": orig.get("r2_power_law", 0.0),
            "original_r2_max": max(orig.get("r2_exponential", 0.0), orig.get("r2_power_law", 0.0)),
            "original_n_points_valid": orig.get("n_points_valid", 0),
            "original_monotonicity": orig.get("monotonicity_fraction", 0.0),
            "original_has_oscillations": orig.get("has_oscillations", False),
            "original_x_min": X_MIN_ORIGINAL,
            "stage04_available": stage04 is not None,
            "stage04_correlation_quality": stage04.get("correlation_quality", 0.0) if stage04 else None,
            "stage04_has_spatial_structure": stage04.get("has_spatial_structure") if stage04 else None,
            "stage04_is_monotonic_decay": stage04.get("is_monotonic_decay") if stage04 else None,
            "stage04_has_power_law": stage04.get("has_power_law") if stage04 else None,
            "failure_tier": "UNKNOWN",
        }
        # Classify failure tier
        if orig.get("n_points_valid", 0) == 0:
            diag["failure_tier"] = "C_NO_DATA"
        elif max(orig.get("r2_exponential", 0.0), orig.get("r2_power_law", 0.0)) >= 0.10:
            diag["failure_tier"] = "A_NEAR_THRESHOLD"
        else:
            diag["failure_tier"] = "B_FLAT_NOISE"

        diagnostics.append(diag)
        log(f"  {event_name}: tier={diag['failure_tier']}, R2_max={diag['original_r2_max']:.3f}, "
            f"n_pts={diag['original_n_points_valid']}, "
            f"s04_q={diag['stage04_correlation_quality']}")

    _write_json_atomic(outputs_dir / "excluded10_diagnostic.json", {
        "created_at": _utc_now_iso(),
        "n_excluded": len(diagnostics),
        "original_x_min": X_MIN_ORIGINAL,
        "r2_threshold": R2_RESCUE_THRESHOLD,
        "tier_counts": {
            "A_NEAR_THRESHOLD": sum(1 for d in diagnostics if d["failure_tier"] == "A_NEAR_THRESHOLD"),
            "B_FLAT_NOISE": sum(1 for d in diagnostics if d["failure_tier"] == "B_FLAT_NOISE"),
            "C_NO_DATA": sum(1 for d in diagnostics if d["failure_tier"] == "C_NO_DATA"),
        },
        "pattern_summary": (
            "All 10 events have decay_classification=NEITHER_GOOD. "
            "3 are near-threshold (R2 0.15-0.29, may benefit from relaxed window), "
            "5 have essentially flat/noisy signal (R2<0.08), "
            "2 have zero valid points at x_min=4.0 (G2 collapses below threshold in deep tail)."
        ),
        "events": diagnostics,
    })
    log(f"  -> Wrote excluded10_diagnostic.json")

    # --- Phase 2: Rescue attempts with relaxed window ---
    log(f"\n=== Phase 2: Rescue attempts with x_min={args.x_min_rescue} ===")
    rescue_attempts = []
    for event_name in EXCLUDED_10:
        h5_path = input_dir / f"{event_name}.h5"
        if not h5_path.exists():
            rescue_attempts.append({
                "event_name": event_name,
                "rescue_attempted": False,
                "rescue_reason": "H5 file not found",
                "rescue_result": "FAILED",
            })
            log(f"  {event_name}: H5 not found, skip")
            continue

        # Run with relaxed window
        result_relaxed = process_event(h5_path, x_min_window=args.x_min_rescue, g2_min_threshold=G2_MIN)

        r2_max_relaxed = max(result_relaxed.r2_exponential, result_relaxed.r2_power_law)
        primary_pass = r2_max_relaxed >= args.r2_threshold

        stage04 = stage04_map.get(event_name)
        s04_quality = stage04.get("correlation_quality", 0.0) if stage04 else 0.0
        secondary_pass = s04_quality >= args.stage04_quality_threshold

        # Determine rescue outcome
        if primary_pass:
            rescue_result = "RESCUED"
            rescue_reason = (
                f"Relaxed window (x_min={args.x_min_rescue}) yields "
                f"R2_max={r2_max_relaxed:.3f} >= {args.r2_threshold}, "
                f"classification={result_relaxed.classification}"
            )
            if secondary_pass:
                rescue_reason += f"; stage04 quality={s04_quality:.3f} confirms signal"
        elif secondary_pass and r2_max_relaxed >= 0.15:
            # Secondary-only rescue: NOT sufficient on its own, just noted
            rescue_result = "MARGINAL_NOT_RESCUED"
            rescue_reason = (
                f"Stage04 quality={s04_quality:.3f} is decent but R2_max={r2_max_relaxed:.3f} < {args.r2_threshold} "
                f"even at x_min={args.x_min_rescue}; insufficient primary evidence for rescue"
            )
        else:
            rescue_result = "FAILED"
            rescue_reason = (
                f"R2_max={r2_max_relaxed:.3f} < {args.r2_threshold} at x_min={args.x_min_rescue}"
            )
            if result_relaxed.n_points_valid == 0:
                rescue_reason = f"Still 0 valid points at x_min={args.x_min_rescue}"

        # Find the original diagnostic for this event
        orig_diag = next(d for d in diagnostics if d["event_name"] == event_name)

        attempt = {
            "event_name": event_name,
            "event_id": event_name.replace("__ringdown", ""),
            "failure_tier": orig_diag["failure_tier"],
            "rescue_attempted": True,
            "rescue_x_min": args.x_min_rescue,
            "rescue_n_points_valid": result_relaxed.n_points_valid,
            "rescue_classification": result_relaxed.classification,
            "rescue_classification_reason": result_relaxed.classification_reason,
            "rescue_r2_exp": result_relaxed.r2_exponential,
            "rescue_r2_pow": result_relaxed.r2_power_law,
            "rescue_r2_max": r2_max_relaxed,
            "rescue_delta_bic": result_relaxed.delta_bic,
            "rescue_monotonicity": result_relaxed.monotonicity_fraction,
            "rescue_has_oscillations": result_relaxed.has_oscillations,
            "original_r2_max": orig_diag["original_r2_max"],
            "r2_improvement": r2_max_relaxed - orig_diag["original_r2_max"],
            "primary_pass": primary_pass,
            "secondary_pass": secondary_pass,
            "stage04_correlation_quality": s04_quality,
            "rescue_result": rescue_result,
            "rescue_reason": rescue_reason,
        }
        rescue_attempts.append(attempt)
        log(f"  {event_name}: {rescue_result} "
            f"(R2_max: {orig_diag['original_r2_max']:.3f} -> {r2_max_relaxed:.3f}, "
            f"pts: {orig_diag['original_n_points_valid']} -> {result_relaxed.n_points_valid})")

    _write_json_atomic(outputs_dir / "rescue_attempts_summary.json", {
        "created_at": _utc_now_iso(),
        "rescue_parameters": {
            "x_min_rescue": args.x_min_rescue,
            "x_min_original": X_MIN_ORIGINAL,
            "r2_threshold": args.r2_threshold,
            "stage04_quality_threshold": args.stage04_quality_threshold,
            "g2_min": G2_MIN,
        },
        "rescue_criteria": {
            "primary": f"At least one model achieves R2 >= {args.r2_threshold} at x_min={args.x_min_rescue}",
            "secondary": f"stage04 correlation_quality >= {args.stage04_quality_threshold} (informational, not sufficient alone)",
            "rescue_requires": "PRIMARY pass. SECONDARY alone does not rescue.",
        },
        "n_attempted": sum(1 for a in rescue_attempts if a.get("rescue_attempted", False)),
        "n_rescued": sum(1 for a in rescue_attempts if a.get("rescue_result") == "RESCUED"),
        "n_marginal": sum(1 for a in rescue_attempts if a.get("rescue_result") == "MARGINAL_NOT_RESCUED"),
        "n_failed": sum(1 for a in rescue_attempts if a.get("rescue_result") == "FAILED"),
        "attempts": rescue_attempts,
    })
    log(f"  -> Wrote rescue_attempts_summary.json")

    # --- Phase 3: Decisions ---
    log(f"\n=== Phase 3: Rescue decision ===")
    rescued_ids = [a["event_name"] for a in rescue_attempts if a.get("rescue_result") == "RESCUED"]
    failed_ids = [a["event_name"] for a in rescue_attempts if a.get("rescue_result") != "RESCUED"]
    n_rescued = len(rescued_ids)

    if n_rescued == 0:
        rescue_decision = "RESCUE_NONE"
        cohort_decision = "KEEP_UNIFY_80_ONLY"
        recommended_count = 80
    elif n_rescued == 10:
        rescue_decision = "RESCUE_ALL_UNSUPPORTED"
        cohort_decision = "UNIFY_90_UNSUPPORTED"
        recommended_count = 80 + n_rescued
    else:
        rescue_decision = "RESCUE_SOME"
        cohort_decision = f"PROMOTE_TO_UNIFY_80_PLUS_{n_rescued}"
        recommended_count = 80 + n_rescued

    decision_reason = (
        f"{n_rescued}/10 events pass the primary rescue criterion "
        f"(R2 >= {args.r2_threshold} at x_min={args.x_min_rescue}). "
    )
    if n_rescued == 0:
        decision_reason += (
            "No event recovers sufficient decay structure with the relaxed window. "
            "The UNIFY_80_ONLY decision stands."
        )
    elif n_rescued < 10:
        decision_reason += (
            f"The rescued events can be added to the expanded cohort as 80+{n_rescued}. "
            f"Full UNIFY_90 remains unsupported because {10 - n_rescued} events still lack minimum signal."
        )
    else:
        decision_reason += "All 10 pass at relaxed window. UNIFY_90 would need independent confirmation."

    supports_unify_90 = n_rescued == 10

    rescue_decision_payload = {
        "created_at": _utc_now_iso(),
        "n_excluded_initial": 10,
        "n_rescued": n_rescued,
        "rescued_event_ids": rescued_ids,
        "failed_event_ids": failed_ids,
        "decision": rescue_decision,
        "cohort_decision": cohort_decision,
        "decision_reason": decision_reason,
        "recommended_unified_count": recommended_count,
        "supports_unify_90": supports_unify_90,
        "non_canonical": True,
        "automatic_promotion": False,
        "rescue_method": f"relaxed_window_x_min_{args.x_min_rescue}",
        "rescue_parameters": {
            "x_min_rescue": args.x_min_rescue,
            "x_min_original": X_MIN_ORIGINAL,
            "r2_threshold": args.r2_threshold,
            "stage04_quality_threshold": args.stage04_quality_threshold,
        },
    }
    _write_json_atomic(outputs_dir / "rescue_decision.json", rescue_decision_payload)
    log(f"  rescue_decision={rescue_decision}, cohort_decision={cohort_decision}")
    log(f"  n_rescued={n_rescued}, recommended_count={recommended_count}")
    log(f"  supports_unify_90={supports_unify_90}")

    # --- Phase 4: Updated cohort recommendation ---
    prior_recommended = recommended_cohort.get("recommended_events", [])
    updated_events = sorted(set(prior_recommended) | set(rescued_ids))
    still_excluded = []
    for event_name in EXCLUDED_10:
        attempt = next((a for a in rescue_attempts if a["event_name"] == event_name), None)
        if attempt and attempt.get("rescue_result") == "RESCUED":
            continue
        still_excluded.append({
            "event_name": event_name,
            "exclusion_class": "low_signal_or_uninformative",
            "rescue_attempted": True,
            "rescue_result": attempt.get("rescue_result", "FAILED") if attempt else "NOT_ATTEMPTED",
            "reason": attempt.get("rescue_reason", "unknown") if attempt else "H5 not found",
        })

    rescued_detail = []
    for event_name in rescued_ids:
        attempt = next(a for a in rescue_attempts if a["event_name"] == event_name)
        rescued_detail.append({
            "event_name": event_name,
            "rescue_reason": attempt["rescue_reason"],
            "rescue_r2_max": attempt["rescue_r2_max"],
            "rescue_classification": attempt["rescue_classification"],
            "promotion_class": "rescued_low_signal",
            "non_canonical": True,
        })

    cohort_update = {
        "created_at": _utc_now_iso(),
        "prior_decision": "UNIFY_80_ONLY",
        "prior_recommended_count": len(prior_recommended),
        "updated_decision": cohort_decision,
        "updated_recommended_count": len(updated_events),
        "recommended_events": updated_events,
        "rescued_events": rescued_detail,
        "still_excluded_events": still_excluded,
        "non_canonical": True,
        "automatic_promotion": False,
    }
    _write_json_atomic(outputs_dir / "recommended_cohort_update.json", cohort_update)
    log(f"  -> Wrote recommended_cohort_update.json ({len(updated_events)} recommended)")

    # --- Stage summary and manifest ---
    stage_summary = {
        "created_at": _utc_now_iso(),
        "stage": STAGE_NAME,
        "status": "PASS",
        "purpose": "low_signal_rescue_audit",
        "non_canonical": True,
        "automatic_downstream_promotion": False,
        "n_excluded_initial": 10,
        "n_rescued": n_rescued,
        "rescued_event_ids": rescued_ids,
        "failed_event_ids": failed_ids,
        "decision": rescue_decision,
        "cohort_decision": cohort_decision,
        "decision_reason": decision_reason,
        "recommended_unified_count": recommended_count,
        "supports_unify_90": supports_unify_90,
        "rescue_parameters": {
            "x_min_rescue": args.x_min_rescue,
            "x_min_original": X_MIN_ORIGINAL,
            "r2_threshold": args.r2_threshold,
            "stage04_quality_threshold": args.stage04_quality_threshold,
            "g2_min": G2_MIN,
        },
        "warnings": [
            "Non-canonical rescue audit; does not override prior UNIFY_80_ONLY decision",
            "Rescued events carry promotion_class=rescued_low_signal, not canonical",
            "automatic_promotion=false: human review required before any cohort change",
        ],
    }
    _write_json_atomic(stage_dir / "stage_summary.json", stage_summary)

    manifest = {
        "created_at": _utc_now_iso(),
        "stage": STAGE_NAME,
        "script": str(Path(__file__).resolve()),
        "command": [
            sys.executable, str(Path(__file__).resolve()),
            "--run-id", args.run_id,
            "--runs-root", str(runs_root),
            "--input-dir", str(input_dir),
            "--x-min-rescue", str(args.x_min_rescue),
            "--r2-threshold", str(args.r2_threshold),
            "--stage04-quality-threshold", str(args.stage04_quality_threshold),
        ],
        "parameters": {
            "run_id": args.run_id,
            "x_min_rescue": args.x_min_rescue,
            "x_min_original": X_MIN_ORIGINAL,
            "r2_threshold": args.r2_threshold,
            "stage04_quality_threshold": args.stage04_quality_threshold,
            "g2_min": G2_MIN,
            "purpose": "low_signal_rescue_audit",
            "non_canonical": True,
            "automatic_downstream_promotion": False,
        },
        "inputs": {
            "input_dir": {"path": str(input_dir)},
            "original_probe_dir": {"path": str(ORIGINAL_PROBE_DIR)},
            "cohort_audit_dir": {"path": str(COHORT_AUDIT_DIR)},
            "geometry_33_summary": {"path": str(GEOMETRY33_SUMMARY), "sha256": _sha256_file(GEOMETRY33_SUMMARY)},
            "geometry_55_summary": {"path": str(GEOMETRY55_SUMMARY), "sha256": _sha256_file(GEOMETRY55_SUMMARY)},
        },
        "outputs": {
            "excluded10_diagnostic_json": str(outputs_dir / "excluded10_diagnostic.json"),
            "rescue_attempts_summary_json": str(outputs_dir / "rescue_attempts_summary.json"),
            "rescue_decision_json": str(outputs_dir / "rescue_decision.json"),
            "recommended_cohort_update_json": str(outputs_dir / "recommended_cohort_update.json"),
            "stage_summary_json": str(stage_dir / "stage_summary.json"),
            "manifest_json": str(stage_dir / "manifest.json"),
            "stdout_log": str(stage_dir / "stdout.log"),
        },
    }
    _write_json_atomic(stage_dir / "manifest.json", manifest)

    # Write stdout log
    (stage_dir / "stdout.log").write_text("\n".join(stdout_lines) + "\n", encoding="utf-8")

    log(f"\n=== Done. Outputs in {outputs_dir} ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
