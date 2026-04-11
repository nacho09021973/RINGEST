"""
feature_support.py — Feature support audit and inference gate for stage 02.

Contract-first, auditable, no side effects beyond returning structured reports.
Designed to be imported by 02_emergent_geometry_engine.py and tests.

Audit logic:
- TINY_STD  : train X_std < 1e-6  →  feature was operationally frozen in train
- OFF_SUPPORT: |z| > 5.0           →  inference point outside train distribution
- CLIP_RISK : |z| > 10.0           →  will be hard-clipped, prediction unreliable

Verdict rules (priority order):
  FAIL if any critical feature has tiny std
  FAIL if any critical feature has |z| > 5
  FAIL if any feature has |z| > 10
  WARN if any non-critical feature has tiny std
  PASS otherwise
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

# -----------------------------------------------------------------------
# Thresholds (all overridable via function args)
# -----------------------------------------------------------------------
TINY_STD_THRESHOLD: float = 1e-6
OFF_SUPPORT_THRESHOLD: float = 5.0
CLIP_RISK_THRESHOLD: float = 10.0

# -----------------------------------------------------------------------
# Critical features: gate fails if any of these misbehaves
# -----------------------------------------------------------------------
CRITICAL_FEATURES: Tuple[str, ...] = (
    "has_horizon",
    "qnm_Q0",
    "qnm_f1f0",
    "qnm_g1g0",
    "G2_large_x",
)

# -----------------------------------------------------------------------
# Canonical feature name list for build_feature_vector V2.5 (N=20)
# Must stay in sync with the ordering in build_feature_vector().
# -----------------------------------------------------------------------
FEATURE_NAMES_V2_5: Tuple[str, ...] = (
    # Correlator (9)
    "G2_log_slope",
    "G2_log_curvature",
    "G2_small_x",
    "G2_large_x",
    "slope_UV",
    "slope_IR",
    "slope_running",
    "G2_std",
    "G2_skew",
    # Thermal (4)
    "temperature",
    "has_horizon",
    "thermal_scale",
    "exponential_decay",
    # QNM (3)
    "qnm_Q0",
    "qnm_f1f0",
    "qnm_g1g0",
    # Response G_R (2)
    "GR_peak_height",
    "GR_peak_width",
    # Global scalars (2)
    "central_charge_eff",
    "d",
)

# -----------------------------------------------------------------------
# qnm_f1f0 semantic sanity bounds
# In Kerr QNM theory, f1/f0 is the ratio of the first overtone frequency
# to the fundamental.  Physical expectation: f1/f0 > 1 (overtone is faster).
# A value outside [QNM_F1F0_SANE_MIN, QNM_F1F0_SANE_MAX] suggests a
# pipeline error (pole-ordering inversion or wrong QNM assignment).
# NOTE: We do NOT assert theory here — only flag for human review.
# -----------------------------------------------------------------------
QNM_F1F0_SANE_MIN: float = 0.5
QNM_F1F0_SANE_MAX: float = 20.0

# -----------------------------------------------------------------------
# V3 contract — Camino C2 (drops QNM block, 17 features)
#
# qnm_Q0 / qnm_f1f0 / qnm_g1g0 are removed because they are not
# interoperable between the Kerr analytical sandbox (01b, Q0≈2–7) and the
# real ESPRIT bridge (02R, Q0≈100–10000).  See docs/qnm_contract_v3_spec.md.
#
# V2_5 and CRITICAL_FEATURES are kept frozen as evidence of the v1 block.
# -----------------------------------------------------------------------
FEATURE_NAMES_V3: Tuple[str, ...] = (
    # Correlator (9) — unchanged from V2_5
    "G2_log_slope",
    "G2_log_curvature",
    "G2_small_x",
    "G2_large_x",
    "slope_UV",
    "slope_IR",
    "slope_running",
    "G2_std",
    "G2_skew",
    # Thermal (4) — unchanged from V2_5
    "temperature",
    "has_horizon",
    "thermal_scale",
    "exponential_decay",
    # QNM block intentionally absent (C2 contract)
    # Response G_R (2) — unchanged from V2_5
    "GR_peak_height",
    "GR_peak_width",
    # Global scalars (2) — unchanged from V2_5
    "central_charge_eff",
    "d",
)

CRITICAL_FEATURES_V3: Tuple[str, ...] = (
    "has_horizon",
    "G2_large_x",
)


# -----------------------------------------------------------------------
# Data structures
# -----------------------------------------------------------------------

@dataclass
class FeatureRow:
    feature: str
    x_real: float
    x_mean: float
    x_std: float
    z_score: Optional[float]          # None when x_std is tiny
    train_std_tiny: bool
    off_support_abs_z_gt_5: bool
    clip_risk_abs_z_gt_10: bool
    semantic_warning: Optional[str]   # None when no semantic issue


@dataclass
class FeatureSupportReport:
    n_features: int
    n_tiny_std: int
    n_off_support: int
    n_clip_risk: int
    rows: List[FeatureRow] = field(default_factory=list)
    critical_features_triggered: List[str] = field(default_factory=list)
    verdict: str = "PASS"            # "PASS" | "WARN" | "FAIL"
    verdict_reason: str = ""

    def to_dict(self) -> Dict:
        return {
            "n_features": self.n_features,
            "n_tiny_std": self.n_tiny_std,
            "n_off_support": self.n_off_support,
            "n_clip_risk": self.n_clip_risk,
            "critical_features_triggered": self.critical_features_triggered,
            "verdict": self.verdict,
            "verdict_reason": self.verdict_reason,
            "rows": [
                {
                    "feature": r.feature,
                    "x_real": r.x_real,
                    "x_mean": r.x_mean,
                    "x_std": r.x_std,
                    "z_score": r.z_score,
                    "train_std_tiny": r.train_std_tiny,
                    "off_support_abs_z_gt_5": r.off_support_abs_z_gt_5,
                    "clip_risk_abs_z_gt_10": r.clip_risk_abs_z_gt_10,
                    "semantic_warning": r.semantic_warning,
                }
                for r in self.rows
            ],
        }


# -----------------------------------------------------------------------
# Core audit function (inference gate)
# -----------------------------------------------------------------------

def audit_feature_support(
    feature_vector: np.ndarray,
    X_mean: np.ndarray,
    X_std: np.ndarray,
    feature_names: Sequence[str],
    tiny_std_threshold: float = TINY_STD_THRESHOLD,
    off_support_threshold: float = OFF_SUPPORT_THRESHOLD,
    clip_risk_threshold: float = CLIP_RISK_THRESHOLD,
    critical_features: Sequence[str] = CRITICAL_FEATURES,
) -> FeatureSupportReport:
    """
    Audits whether a feature vector is within the training support.

    Parameters
    ----------
    feature_vector : array, shape (n_features,)
        The raw (un-normalised) feature vector from inference.
    X_mean : array, shape (n_features,)
        Per-feature training mean (from checkpoint).
    X_std : array, shape (n_features,)
        Per-feature training std (from checkpoint, before clipping normalisation).
    feature_names : sequence of str, length n_features
    tiny_std_threshold : float
        X_std values below this indicate a frozen feature.
    off_support_threshold : float
        |z| above this is off-support.
    clip_risk_threshold : float
        |z| above this will be hard-clipped by the normaliser.
    critical_features : sequence of str
        Feature names that trigger a FAIL verdict.

    Returns
    -------
    FeatureSupportReport
    """
    x = np.asarray(feature_vector, dtype=float).flatten()
    mu = np.asarray(X_mean, dtype=float).flatten()
    sigma = np.asarray(X_std, dtype=float).flatten()
    names = list(feature_names)
    n = len(names)

    if len(x) != n or len(mu) != n or len(sigma) != n:
        raise ValueError(
            f"Length mismatch: feature_vector={len(x)}, X_mean={len(mu)}, "
            f"X_std={len(sigma)}, feature_names={n}"
        )

    rows: List[FeatureRow] = []
    n_tiny_std = 0
    n_off_support = 0
    n_clip_risk = 0
    critical_triggered: List[str] = []
    crit_set = set(critical_features)

    for i, name in enumerate(names):
        x_real = float(x[i])
        x_mean = float(mu[i])
        x_std = float(sigma[i])

        tiny = x_std < tiny_std_threshold
        if tiny:
            z_score: Optional[float] = None
            off = False
            clip = False
            n_tiny_std += 1
        else:
            raw_z = (x_real - x_mean) / x_std
            if not math.isfinite(raw_z):
                z_score = None
                off = False
                clip = False
            else:
                z_score = raw_z
                off = abs(z_score) > off_support_threshold
                clip = abs(z_score) > clip_risk_threshold
                if off:
                    n_off_support += 1
                if clip:
                    n_clip_risk += 1

        # Semantic check for qnm_f1f0 (guardrail, not physics assertion)
        semantic_warning: Optional[str] = None
        if name == "qnm_f1f0" and not tiny and math.isfinite(x_real):
            if x_real < QNM_F1F0_SANE_MIN:
                semantic_warning = (
                    f"qnm_f1f0={x_real:.4f} < {QNM_F1F0_SANE_MIN}: possible pole-ordering "
                    "inversion (Kerr QNM expectation: f1/f0 > 0.5)"
                )
            elif x_real > QNM_F1F0_SANE_MAX:
                semantic_warning = (
                    f"qnm_f1f0={x_real:.4f} > {QNM_F1F0_SANE_MAX}: implausibly large ratio; "
                    "check QNM computation pipeline for ordering/normalisation errors"
                )

        # Critical gate: triggered by tiny std OR off-support on critical feature
        is_critical = name in crit_set
        gate_condition = tiny or (z_score is not None and abs(z_score) > off_support_threshold)
        if is_critical and gate_condition:
            critical_triggered.append(name)

        rows.append(FeatureRow(
            feature=name,
            x_real=x_real,
            x_mean=x_mean,
            x_std=x_std,
            z_score=z_score,
            train_std_tiny=tiny,
            off_support_abs_z_gt_5=off,
            clip_risk_abs_z_gt_10=clip,
            semantic_warning=semantic_warning,
        ))

    # Verdict determination
    if critical_triggered or n_clip_risk > 0:
        verdict = "FAIL"
        parts: List[str] = []
        if critical_triggered:
            parts.append(f"critical_features_triggered={critical_triggered}")
        if n_clip_risk > 0:
            parts.append(f"n_clip_risk={n_clip_risk}")
        verdict_reason = "UNSUPPORTED_FEATURE_REGIME: " + "; ".join(parts)
    elif n_tiny_std > 0:
        verdict = "WARN"
        verdict_reason = f"WARN: n_tiny_std={n_tiny_std} (non-critical features with frozen train std)"
    else:
        verdict = "PASS"
        verdict_reason = ""

    return FeatureSupportReport(
        n_features=n,
        n_tiny_std=n_tiny_std,
        n_off_support=n_off_support,
        n_clip_risk=n_clip_risk,
        rows=rows,
        critical_features_triggered=critical_triggered,
        verdict=verdict,
        verdict_reason=verdict_reason,
    )


# -----------------------------------------------------------------------
# Train audit (post-training checkpoint quality check)
# -----------------------------------------------------------------------

def audit_train_feature_support(
    feature_names: Sequence[str],
    X_mean: np.ndarray,
    X_std: np.ndarray,
    tiny_std_threshold: float = TINY_STD_THRESHOLD,
    critical_features: Sequence[str] = CRITICAL_FEATURES,
) -> Dict:
    """
    Audits training feature support quality immediately after fitting.

    Use the RAW per-feature std (before any floor like +1e-8) for an honest
    audit of which features were truly frozen during training.

    Returns a serialisable dict suitable for inclusion in the train summary JSON.

    Verdict:
    - FAIL if any critical feature has std < threshold
    - WARN if any non-critical feature has std < threshold
    - PASS otherwise
    """
    mu = np.asarray(X_mean, dtype=float).flatten()
    sigma = np.asarray(X_std, dtype=float).flatten()
    names = list(feature_names)
    crit_set = set(critical_features)

    tiny_features: List[str] = [
        name for name, s in zip(names, sigma) if s < tiny_std_threshold
    ]
    critical_tiny: List[str] = [n for n in tiny_features if n in crit_set]

    if critical_tiny:
        verdict = "FAIL"
        verdict_reason = (
            f"TRAIN_FEATURE_SUPPORT_FAIL: critical features with std < {tiny_std_threshold}: "
            f"{critical_tiny}"
        )
    elif tiny_features:
        verdict = "WARN"
        verdict_reason = (
            f"TRAIN_FEATURE_SUPPORT_WARN: non-critical features with std < {tiny_std_threshold}: "
            f"{tiny_features}"
        )
    else:
        verdict = "PASS"
        verdict_reason = ""

    return {
        "feature_names": names,
        "X_mean": [float(v) for v in mu],
        "X_std": [float(v) for v in sigma],
        "tiny_std_threshold": tiny_std_threshold,
        "tiny_std_features": tiny_features,
        "critical_tiny_std_features": critical_tiny,
        "verdict": verdict,
        "verdict_reason": verdict_reason,
    }
