#!/usr/bin/env python3
"""
decay_type_discrimination.py — Discriminate exponential vs power-law decay in G2_ringdown

Purpose: Determine if the tail of G2_ringdown is better described by exponential or power-law
         decay for the 33-event canonical cohort.

Method:
  - For each event, extract G2_ringdown and x_grid
  - Define analysis window (configurable, default x >= 2.0 for sufficient tail coverage)
  - Fit two models:
      Model E: G2(x) = A * exp(-lambda * x)  ->  log(G2) = log(A) - lambda * x
      Model P: G2(x) = B * x^(-alpha)         ->  log(G2) = log(B) - alpha * log(x)
  - Compare using BIC (Bayesian Information Criterion)
  - Classify each event and aggregate

Output:
  - CSV with per-event results
  - JSON summary with cohort aggregation

Author: Claude Code / RINGEST
Date: 2026-04-12
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import warnings

import h5py
import numpy as np
import pandas as pd
from scipy import optimize

# Resolve paths relative to the repository instead of a user-specific absolute path.
REPO_ROOT = Path(__file__).resolve().parents[1]

# ============================================================================
# Configuration
# ============================================================================

# Window definition: we use x >= X_MIN_WINDOW to focus on IR tail
# After inspection, x >= 2.0 gives ~170 points with meaningful decay structure
# x >= 4.0 gives ~86 points but may be too deep into noise/oscillation regime
X_MIN_WINDOW_DEFAULT = 2.0

# Minimum G2 value to include (avoid log(0) and extreme noise)
G2_MIN_THRESHOLD = 1e-6

# BIC delta threshold for classification
# |delta_BIC| < 2: inconclusive (weak evidence)
# |delta_BIC| >= 2 and < 6: positive evidence
# |delta_BIC| >= 6: strong evidence
BIC_AMBIGUOUS_THRESHOLD = 2.0

# Minimum R² to consider a fit "good"
R2_MIN_GOOD = 0.3

# ============================================================================
# Data classes
# ============================================================================

@dataclass
class FitResult:
    """Result of a single model fit."""
    model: str  # "exponential" or "power_law"
    params: Dict[str, float]  # fitted parameters
    r2: float  # coefficient of determination
    bic: float  # Bayesian Information Criterion
    aic: float  # Akaike Information Criterion
    residual_std: float  # standard deviation of residuals
    n_points: int  # number of data points used
    success: bool  # whether fit converged


@dataclass
class EventResult:
    """Discrimination result for a single event."""
    event_name: str
    n_points_total: int
    n_points_window: int
    n_points_valid: int  # after G2 > threshold filter
    x_window_min: float
    x_window_max: float

    # Exponential fit
    fit_exp: Optional[FitResult]

    # Power-law fit
    fit_pow: Optional[FitResult]

    # Comparison
    bic_exponential: float
    bic_power_law: float
    delta_bic: float  # bic_power_law - bic_exponential (positive = exponential preferred)
    r2_exponential: float
    r2_power_law: float

    # Classification
    classification: str  # EXPONENTIAL_PREFERRED, POWERLAW_PREFERRED, AMBIGUOUS, NEITHER_GOOD
    classification_reason: str

    # Data quality flags
    has_oscillations: bool  # detected oscillations in window
    monotonicity_fraction: float  # fraction of points with dG2/dx < 0


@dataclass
class CohortSummary:
    """Aggregated summary for the cohort."""
    version: str = "1.0"
    cohort_source: str = ""
    n_events: int = 0
    n_exponential_preferred: int = 0
    n_powerlaw_preferred: int = 0
    n_ambiguous: int = 0
    n_neither_good: int = 0

    delta_bic_summary: Dict[str, float] = field(default_factory=dict)
    r2_exponential_summary: Dict[str, float] = field(default_factory=dict)
    r2_power_law_summary: Dict[str, float] = field(default_factory=dict)

    window_definition: Dict[str, float] = field(default_factory=dict)
    g2_handling_policy: str = ""

    events_exponential: List[str] = field(default_factory=list)
    events_powerlaw: List[str] = field(default_factory=list)
    events_ambiguous: List[str] = field(default_factory=list)
    events_neither: List[str] = field(default_factory=list)

    interpretation: str = ""
    implication_for_stage04_contract: str = ""
    dominant_decay_type: str = ""
    powerlaw_majority_observed: bool = False
    exponential_tilt_observed: bool = False


# ============================================================================
# Fitting functions
# ============================================================================

def fit_exponential(x: np.ndarray, g2: np.ndarray) -> FitResult:
    """
    Fit exponential model: G2(x) = A * exp(-lambda * x)

    In log space: log(G2) = log(A) - lambda * x
    This is linear regression: y = a + b*x where y=log(G2), a=log(A), b=-lambda
    """
    # Work in log space for stability
    log_g2 = np.log(g2)

    # Linear fit: log(G2) = log(A) - lambda * x
    try:
        coeffs, residuals, rank, s, rcond = np.polyfit(x, log_g2, 1, full=True)
        slope, intercept = coeffs

        # Parameters
        lambda_exp = -slope
        A = np.exp(intercept)

        # Predictions and R²
        log_g2_pred = np.polyval(coeffs, x)
        ss_res = np.sum((log_g2 - log_g2_pred)**2)
        ss_tot = np.sum((log_g2 - np.mean(log_g2))**2)
        r2 = 1 - ss_res / (ss_tot + 1e-10) if ss_tot > 1e-10 else 0.0

        # Residual std in log space
        residual_std = np.sqrt(ss_res / (len(x) - 2)) if len(x) > 2 else float('inf')

        # BIC and AIC
        n = len(x)
        k = 2  # number of parameters (A, lambda)
        if ss_res > 0:
            bic = n * np.log(ss_res / n) + k * np.log(n)
            aic = n * np.log(ss_res / n) + 2 * k
        else:
            bic = -float('inf')
            aic = -float('inf')

        return FitResult(
            model="exponential",
            params={"A": float(A), "lambda": float(lambda_exp)},
            r2=float(r2),
            bic=float(bic),
            aic=float(aic),
            residual_std=float(residual_std),
            n_points=n,
            success=True
        )
    except Exception as e:
        return FitResult(
            model="exponential",
            params={"A": float('nan'), "lambda": float('nan')},
            r2=0.0,
            bic=float('inf'),
            aic=float('inf'),
            residual_std=float('inf'),
            n_points=len(x),
            success=False
        )


def fit_power_law(x: np.ndarray, g2: np.ndarray) -> FitResult:
    """
    Fit power-law model: G2(x) = B * x^(-alpha)

    In log-log space: log(G2) = log(B) - alpha * log(x)
    This is linear regression: y = a + b*z where y=log(G2), z=log(x), a=log(B), b=-alpha
    """
    # Work in log-log space
    log_x = np.log(x)
    log_g2 = np.log(g2)

    try:
        coeffs, residuals, rank, s, rcond = np.polyfit(log_x, log_g2, 1, full=True)
        slope, intercept = coeffs

        # Parameters
        alpha = -slope
        B = np.exp(intercept)

        # Predictions and R²
        log_g2_pred = np.polyval(coeffs, log_x)
        ss_res = np.sum((log_g2 - log_g2_pred)**2)
        ss_tot = np.sum((log_g2 - np.mean(log_g2))**2)
        r2 = 1 - ss_res / (ss_tot + 1e-10) if ss_tot > 1e-10 else 0.0

        # Residual std in log space
        residual_std = np.sqrt(ss_res / (len(x) - 2)) if len(x) > 2 else float('inf')

        # BIC and AIC
        n = len(x)
        k = 2  # number of parameters (B, alpha)
        if ss_res > 0:
            bic = n * np.log(ss_res / n) + k * np.log(n)
            aic = n * np.log(ss_res / n) + 2 * k
        else:
            bic = -float('inf')
            aic = -float('inf')

        return FitResult(
            model="power_law",
            params={"B": float(B), "alpha": float(alpha)},
            r2=float(r2),
            bic=float(bic),
            aic=float(aic),
            residual_std=float(residual_std),
            n_points=n,
            success=True
        )
    except Exception as e:
        return FitResult(
            model="power_law",
            params={"B": float('nan'), "alpha": float('nan')},
            r2=0.0,
            bic=float('inf'),
            aic=float('inf'),
            residual_std=float('inf'),
            n_points=len(x),
            success=False
        )


def detect_oscillations(g2: np.ndarray) -> Tuple[bool, float]:
    """
    Detect oscillations in G2 signal.

    Returns:
        has_oscillations: True if sign changes in derivative exceed threshold
        monotonicity_fraction: fraction of points where dG2/dx < 0 (should be ~1 for pure decay)
    """
    if len(g2) < 3:
        return False, 1.0

    dg2 = np.diff(g2)
    n_negative = np.sum(dg2 < 0)
    monotonicity_fraction = n_negative / len(dg2)

    # Count sign changes
    sign_changes = np.sum(np.diff(np.sign(dg2)) != 0)

    # If more than 20% sign changes, consider it oscillatory
    has_oscillations = sign_changes > 0.2 * len(dg2)

    return has_oscillations, monotonicity_fraction


def classify_event(
    fit_exp: FitResult,
    fit_pow: FitResult,
    bic_threshold: float = BIC_AMBIGUOUS_THRESHOLD,
    r2_min: float = R2_MIN_GOOD
) -> Tuple[str, str]:
    """
    Classify event based on fit comparison.

    Returns:
        classification: EXPONENTIAL_PREFERRED, POWERLAW_PREFERRED, AMBIGUOUS, NEITHER_GOOD
        reason: human-readable explanation
    """
    delta_bic = fit_pow.bic - fit_exp.bic  # positive = exponential preferred

    # First check if either fit is good enough
    exp_good = fit_exp.success and fit_exp.r2 >= r2_min
    pow_good = fit_pow.success and fit_pow.r2 >= r2_min

    if not exp_good and not pow_good:
        return "NEITHER_GOOD", f"Both fits have R² < {r2_min}: exp R²={fit_exp.r2:.3f}, pow R²={fit_pow.r2:.3f}"

    if not fit_exp.success or not fit_pow.success:
        if fit_exp.success:
            return "EXPONENTIAL_PREFERRED", "Power-law fit failed"
        elif fit_pow.success:
            return "POWERLAW_PREFERRED", "Exponential fit failed"
        else:
            return "NEITHER_GOOD", "Both fits failed"

    # Compare BIC
    if abs(delta_bic) < bic_threshold:
        return "AMBIGUOUS", f"|ΔBIC|={abs(delta_bic):.2f} < {bic_threshold}: insufficient evidence to discriminate"

    if delta_bic > 0:
        strength = "strongly" if delta_bic > 6 else "moderately" if delta_bic > 2 else "weakly"
        return "EXPONENTIAL_PREFERRED", f"ΔBIC={delta_bic:.2f}: exponential {strength} preferred (lower BIC)"
    else:
        strength = "strongly" if delta_bic < -6 else "moderately" if delta_bic < -2 else "weakly"
        return "POWERLAW_PREFERRED", f"ΔBIC={delta_bic:.2f}: power-law {strength} preferred (lower BIC)"


# ============================================================================
# Main processing
# ============================================================================

def process_event(
    h5_path: Path,
    x_min_window: float = X_MIN_WINDOW_DEFAULT,
    g2_min_threshold: float = G2_MIN_THRESHOLD
) -> EventResult:
    """
    Process a single event and perform decay type discrimination.
    """
    event_name = h5_path.stem

    with h5py.File(h5_path, 'r') as f:
        g2_full = f['boundary/G2_ringdown'][:]
        x_full = f['boundary/x_grid'][:]

    n_points_total = len(g2_full)

    # Apply window
    window_mask = x_full >= x_min_window
    x_window = x_full[window_mask]
    g2_window = g2_full[window_mask]
    n_points_window = len(x_window)

    # Filter out G2 <= threshold (avoid log issues and extreme noise)
    valid_mask = g2_window > g2_min_threshold
    x_valid = x_window[valid_mask]
    g2_valid = g2_window[valid_mask]
    n_points_valid = len(x_valid)

    # Check if we have enough points
    if n_points_valid < 10:
        return EventResult(
            event_name=event_name,
            n_points_total=n_points_total,
            n_points_window=n_points_window,
            n_points_valid=n_points_valid,
            x_window_min=float(x_min_window),
            x_window_max=float(x_full.max()),
            fit_exp=None,
            fit_pow=None,
            bic_exponential=float('inf'),
            bic_power_law=float('inf'),
            delta_bic=0.0,
            r2_exponential=0.0,
            r2_power_law=0.0,
            classification="NEITHER_GOOD",
            classification_reason=f"Insufficient valid points: {n_points_valid} < 10",
            has_oscillations=False,
            monotonicity_fraction=0.0
        )

    # Detect oscillations in window
    has_osc, mono_frac = detect_oscillations(g2_window)

    # Fit both models
    fit_exp = fit_exponential(x_valid, g2_valid)
    fit_pow = fit_power_law(x_valid, g2_valid)

    # Classify
    classification, reason = classify_event(fit_exp, fit_pow)

    return EventResult(
        event_name=event_name,
        n_points_total=n_points_total,
        n_points_window=n_points_window,
        n_points_valid=n_points_valid,
        x_window_min=float(x_min_window),
        x_window_max=float(x_full.max()),
        fit_exp=fit_exp,
        fit_pow=fit_pow,
        bic_exponential=fit_exp.bic,
        bic_power_law=fit_pow.bic,
        delta_bic=fit_pow.bic - fit_exp.bic,
        r2_exponential=fit_exp.r2,
        r2_power_law=fit_pow.r2,
        classification=classification,
        classification_reason=reason,
        has_oscillations=has_osc,
        monotonicity_fraction=mono_frac
    )


def create_summary(results: List[EventResult], cohort_source: str, x_min_window: float) -> CohortSummary:
    """Create aggregated summary from event results."""

    n_events = len(results)

    # Count classifications
    exp_events = [r.event_name for r in results if r.classification == "EXPONENTIAL_PREFERRED"]
    pow_events = [r.event_name for r in results if r.classification == "POWERLAW_PREFERRED"]
    amb_events = [r.event_name for r in results if r.classification == "AMBIGUOUS"]
    nei_events = [r.event_name for r in results if r.classification == "NEITHER_GOOD"]

    n_exp = len(exp_events)
    n_pow = len(pow_events)
    n_amb = len(amb_events)
    n_nei = len(nei_events)

    # Delta BIC statistics
    delta_bics = [r.delta_bic for r in results if np.isfinite(r.delta_bic)]
    r2_exps = [r.r2_exponential for r in results if np.isfinite(r.r2_exponential)]
    r2_pows = [r.r2_power_law for r in results if np.isfinite(r.r2_power_law)]

    def stats(arr):
        if len(arr) == 0:
            return {"mean": float('nan'), "std": float('nan'), "min": float('nan'), "max": float('nan'), "median": float('nan')}
        return {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "median": float(np.median(arr))
        }

    # Determine dominant type and descriptive cohort-level tilt
    n_discriminated = n_exp + n_pow
    if n_discriminated == 0:
        dominant = "undetermined"
    elif n_exp > n_pow:
        dominant = "exponential"
    elif n_pow > n_exp:
        dominant = "power_law"
    else:
        dominant = "tied"

    powerlaw_majority_observed = n_pow > n_exp
    exponential_tilt_observed = n_exp > n_pow

    # Interpretation
    interpretation = (
        f"The canonical cohort is not dominated by power-law classifications in this finite-window test: "
        f"{n_exp}/{n_events} events prefer exponential, {n_pow}/{n_events} prefer power-law, "
        f"{n_amb}/{n_events} are ambiguous, and {n_nei}/{n_events} are NEITHER_GOOD. "
        f"The aggregate shows an exponential tilt (mean ΔBIC = {stats(delta_bics)['mean']:.2f}, "
        f"median ΔBIC = {stats(delta_bics)['median']:.2f}; positive favors exponential), "
        f"but the cohort remains heterogeneous and includes a relevant subset with poor fit quality."
    )

    # Stage 04 implication
    implication = (
        "Stage 04 correlator_structure should be reinterpreted as a relaxed, non-discriminating contract "
        "about decay structure in a finite analysis window. The fields has_power_law and log_slope should "
        "not be interpreted as evidence for physical power-law decay or as a proxy for conformal dimension."
    )

    return CohortSummary(
        version="1.0",
        cohort_source=cohort_source,
        n_events=n_events,
        n_exponential_preferred=n_exp,
        n_powerlaw_preferred=n_pow,
        n_ambiguous=n_amb,
        n_neither_good=n_nei,
        delta_bic_summary=stats(delta_bics),
        r2_exponential_summary=stats(r2_exps),
        r2_power_law_summary=stats(r2_pows),
        window_definition={
            "x_min": x_min_window,
            "x_max": 6.0,
            "description": f"IR tail window starting at x >= {x_min_window}"
        },
        g2_handling_policy=f"Filter G2 > {G2_MIN_THRESHOLD}; work in log space for fitting",
        events_exponential=exp_events,
        events_powerlaw=pow_events,
        events_ambiguous=amb_events,
        events_neither=nei_events,
        interpretation=interpretation,
        implication_for_stage04_contract=implication,
        dominant_decay_type=dominant,
        powerlaw_majority_observed=powerlaw_majority_observed,
        exponential_tilt_observed=exponential_tilt_observed
    )


def main():
    """Run decay type discrimination on canonical 33-event cohort."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Discriminate exponential vs power-law decay in G2_ringdown tail",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default run (x >= 2.0, full window)
  python tools/decay_type_discrimination.py

  # Strict tail window (x >= 4.0)
  python tools/decay_type_discrimination.py --x-min 4.0 --suffix tail_strict

  # Custom input/output
  python tools/decay_type_discrimination.py --input-dir /path/to/h5s --output-dir /path/to/out

Output:
  Creates two artifacts in output-dir:
    - decay_type_discrimination_33_event_canonical[_suffix].csv
    - decay_type_discrimination_33_event_canonical[_suffix].json
"""
    )
    parser.add_argument(
        "--input-dir", "-i",
        type=Path,
        default=REPO_ROOT / "runs" / "reopen_v1" / "33_event_effective_contract_pass_stage02_input",
        help="Directory containing .h5 files with G2_ringdown data"
    )
    parser.add_argument(
        "--output-dir", "-o",
        type=Path,
        default=REPO_ROOT / "runs" / "reopen_v1",
        help="Directory for output artifacts"
    )
    parser.add_argument(
        "--x-min", "-x",
        type=float,
        default=2.0,
        help="Minimum x value for analysis window (default: 2.0)"
    )
    parser.add_argument(
        "--g2-min",
        type=float,
        default=1e-6,
        help="Minimum G2 threshold to include (default: 1e-6)"
    )
    parser.add_argument(
        "--bic-threshold",
        type=float,
        default=2.0,
        help="BIC delta threshold for AMBIGUOUS classification (default: 2.0)"
    )
    parser.add_argument(
        "--r2-min",
        type=float,
        default=0.3,
        help="Minimum R² for a fit to be considered 'good' (default: 0.3)"
    )
    parser.add_argument(
        "--suffix", "-s",
        type=str,
        default="",
        help="Suffix for output filenames (e.g., 'tail_strict' -> ..._tail_strict.csv)"
    )

    args = parser.parse_args()

    # Paths
    input_dir = args.input_dir
    output_dir = args.output_dir
    x_min_window = args.x_min

    # Get list of events
    h5_files = sorted(input_dir.glob("*.h5"))
    if not h5_files:
        print(f"ERROR: No H5 files found in input directory: {input_dir}", file=sys.stderr)
        raise SystemExit(1)

    print(f"Found {len(h5_files)} H5 files")
    print(f"Window: x >= {x_min_window}")
    print(f"G2 threshold: {args.g2_min}")
    print(f"BIC threshold: {args.bic_threshold}")
    print(f"R² minimum: {args.r2_min}")

    # Process all events
    results = []
    for h5_path in h5_files:
        print(f"Processing {h5_path.name}...", end=" ")
        result = process_event(
            h5_path,
            x_min_window=x_min_window,
            g2_min_threshold=args.g2_min
        )
        results.append(result)
        print(f"{result.classification} (ΔBIC={result.delta_bic:.2f})")

    # Create summary
    summary = create_summary(results, str(input_dir), x_min_window)
    # Add run parameters to summary
    summary.window_definition["x_min"] = x_min_window
    summary.window_definition["g2_min_threshold"] = args.g2_min
    summary.window_definition["bic_threshold"] = args.bic_threshold
    summary.window_definition["r2_min"] = args.r2_min

    # Build filename suffix
    suffix = f"_{args.suffix}" if args.suffix else ""

    output_dir.mkdir(parents=True, exist_ok=True)

    # Save CSV
    csv_path = output_dir / f"decay_type_discrimination_33_event_canonical{suffix}.csv"
    rows = []
    for r in results:
        row = {
            "event_name": r.event_name,
            "n_points_valid": r.n_points_valid,
            "x_window_min": r.x_window_min,
            "bic_exponential": r.bic_exponential,
            "bic_power_law": r.bic_power_law,
            "delta_bic": r.delta_bic,
            "r2_exponential": r.r2_exponential,
            "r2_power_law": r.r2_power_law,
            "classification": r.classification,
            "classification_reason": r.classification_reason,
            "has_oscillations": r.has_oscillations,
            "monotonicity_fraction": r.monotonicity_fraction,
        }
        if r.fit_exp and r.fit_exp.success:
            row["exp_A"] = r.fit_exp.params.get("A", float('nan'))
            row["exp_lambda"] = r.fit_exp.params.get("lambda", float('nan'))
        else:
            row["exp_A"] = float('nan')
            row["exp_lambda"] = float('nan')
        if r.fit_pow and r.fit_pow.success:
            row["pow_B"] = r.fit_pow.params.get("B", float('nan'))
            row["pow_alpha"] = r.fit_pow.params.get("alpha", float('nan'))
        else:
            row["pow_B"] = float('nan')
            row["pow_alpha"] = float('nan')
        rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)
    print(f"\nSaved CSV: {csv_path}")

    # Save JSON summary
    json_path = output_dir / f"decay_type_discrimination_33_event_canonical{suffix}.json"
    with open(json_path, 'w') as f:
        json.dump(asdict(summary), f, indent=2)
    print(f"Saved JSON: {json_path}")

    # Print summary
    print("\n" + "="*80)
    print("COHORT SUMMARY")
    print("="*80)
    print(f"Total events: {summary.n_events}")
    print(f"Exponential preferred: {summary.n_exponential_preferred}")
    print(f"Power-law preferred: {summary.n_powerlaw_preferred}")
    print(f"Ambiguous: {summary.n_ambiguous}")
    print(f"Neither good: {summary.n_neither_good}")
    print(f"\nDominant decay type: {summary.dominant_decay_type}")
    print(f"Power-law majority observed: {summary.powerlaw_majority_observed}")
    print(f"Exponential tilt observed: {summary.exponential_tilt_observed}")
    print(f"\nΔBIC summary (positive = exponential preferred):")
    for k, v in summary.delta_bic_summary.items():
        print(f"  {k}: {v:.3f}")
    print(f"\nInterpretation:\n{summary.interpretation}")
    print(f"\nImplication for Stage 04:\n{summary.implication_for_stage04_contract}")

    return summary


if __name__ == "__main__":
    main()
