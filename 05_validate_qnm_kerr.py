#!/usr/bin/env python3
"""
05_validate_qnm_kerr.py  v1.0

Validate QNM cluster centroids (from 04_kan_qnm_classifier.py) against
tabulated Kerr QNM frequencies (Berti, Cardoso & Starinets 2009,
arXiv:0905.2975, Table VIII — l=m=2, n=0,1,2).

For each cluster centroid in the dimensionless plane (omega_re_norm,
omega_im_norm), this script finds the nearest Kerr reference mode and
reports the match quality and inferred overtone number.

Chain:
    04_kan_qnm_classifier.py  →  runs/qnm_kan/qnm_kan_summary.json
    THIS SCRIPT               →  runs/qnm_kerr_validation/
                                    qnm_kerr_validation_summary.json
                                    kerr_match_table.csv

Reference table: Kerr (l=2, m=2) modes for n=0,1,2 at chi ∈ [0, 0.99].
Units: M*omega (dimensionless), omega_im < 0 for decaying modes.

Usage
-----
    python3 05_validate_qnm_kerr.py \\
        --summary runs/qnm_kan/qnm_kan_summary.json

    # Or provide cluster analysis directly:
    python3 05_validate_qnm_kerr.py \\
        --cluster-analysis runs/qnm_kan/cluster_analysis.json \\
        --dataset-csv runs/qnm_dataset/qnm_dataset.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

SCRIPT_VERSION = "05_validate_qnm_kerr.py v1.0"


# ---------------------------------------------------------------------------
# Kerr QNM reference table  (Berti et al. 2009, arXiv:0905.2975, Table VIII)
# l = m = 2 dominant gravitational-wave modes, n = 0, 1, 2
# Columns: chi, omega_re_norm (M*Re[omega]), omega_im_norm (M*Im[omega])
# omega_im_norm is negative (damped oscillation convention)
# ---------------------------------------------------------------------------

KERR_TABLE: List[Dict[str, Any]] = [
    # ── n = 0 (fundamental tone) ──────────────────────────────────────────
    {"n": 0, "chi": 0.00, "omega_re": 0.37367, "omega_im": -0.08896},
    {"n": 0, "chi": 0.10, "omega_re": 0.38519, "omega_im": -0.08752},
    {"n": 0, "chi": 0.20, "omega_re": 0.39793, "omega_im": -0.08588},
    {"n": 0, "chi": 0.30, "omega_re": 0.41225, "omega_im": -0.08394},
    {"n": 0, "chi": 0.40, "omega_re": 0.42858, "omega_im": -0.08156},
    {"n": 0, "chi": 0.50, "omega_re": 0.44753, "omega_im": -0.07853},
    {"n": 0, "chi": 0.60, "omega_re": 0.47004, "omega_im": -0.07449},
    {"n": 0, "chi": 0.69, "omega_re": 0.49766, "omega_im": -0.06893},
    {"n": 0, "chi": 0.80, "omega_re": 0.53383, "omega_im": -0.06064},
    {"n": 0, "chi": 0.90, "omega_re": 0.58839, "omega_im": -0.04725},
    {"n": 0, "chi": 0.99, "omega_re": 0.67876, "omega_im": -0.02055},
    # ── n = 1 (first overtone) ────────────────────────────────────────────
    {"n": 1, "chi": 0.00, "omega_re": 0.34671, "omega_im": -0.27392},
    {"n": 1, "chi": 0.10, "omega_re": 0.35595, "omega_im": -0.27078},
    {"n": 1, "chi": 0.20, "omega_re": 0.36662, "omega_im": -0.26698},
    {"n": 1, "chi": 0.30, "omega_re": 0.37909, "omega_im": -0.26239},
    {"n": 1, "chi": 0.40, "omega_re": 0.39386, "omega_im": -0.25677},
    {"n": 1, "chi": 0.50, "omega_re": 0.41159, "omega_im": -0.24977},
    {"n": 1, "chi": 0.60, "omega_re": 0.43329, "omega_im": -0.24084},
    {"n": 1, "chi": 0.69, "omega_re": 0.46169, "omega_im": -0.22940},
    {"n": 1, "chi": 0.80, "omega_re": 0.50150, "omega_im": -0.21247},
    {"n": 1, "chi": 0.90, "omega_re": 0.55927, "omega_im": -0.18482},
    {"n": 1, "chi": 0.99, "omega_re": 0.65506, "omega_im": -0.13040},
    # ── n = 2 (second overtone) ───────────────────────────────────────────
    {"n": 2, "chi": 0.00, "omega_re": 0.30105, "omega_im": -0.47832},
    {"n": 2, "chi": 0.10, "omega_re": 0.30889, "omega_im": -0.47437},
    {"n": 2, "chi": 0.20, "omega_re": 0.31820, "omega_im": -0.46957},
    {"n": 2, "chi": 0.30, "omega_re": 0.32951, "omega_im": -0.46365},
    {"n": 2, "chi": 0.40, "omega_re": 0.34357, "omega_im": -0.45620},
    {"n": 2, "chi": 0.50, "omega_re": 0.36133, "omega_im": -0.44651},
    {"n": 2, "chi": 0.60, "omega_re": 0.38445, "omega_im": -0.43356},
    {"n": 2, "chi": 0.69, "omega_re": 0.41370, "omega_im": -0.41676},
    {"n": 2, "chi": 0.80, "omega_re": 0.45801, "omega_im": -0.39115},
    {"n": 2, "chi": 0.90, "omega_re": 0.52479, "omega_im": -0.35055},
    {"n": 2, "chi": 0.99, "omega_re": 0.63084, "omega_im": -0.28086},
]

# Pre-build arrays for fast nearest-neighbour lookup
_REF_RE  = np.array([r["omega_re"] for r in KERR_TABLE], dtype=np.float64)
_REF_IM  = np.array([r["omega_im"] for r in KERR_TABLE], dtype=np.float64)
_REF_N   = np.array([r["n"]        for r in KERR_TABLE], dtype=int)
_REF_CHI = np.array([r["chi"]      for r in KERR_TABLE], dtype=np.float64)

# Match-quality thresholds (Euclidean distance in the dimensionless plane)
THRESHOLD_GOOD = 0.05
THRESHOLD_FAIR = 0.15


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Reference table helpers
# ---------------------------------------------------------------------------

def nearest_kerr_mode(
    omega_re: float,
    omega_im: float,
) -> Dict[str, Any]:
    """
    Return the closest entry in KERR_TABLE and the Euclidean distance.
    Distance is computed in the (omega_re_norm, omega_im_norm) plane.
    """
    dre = _REF_RE - omega_re
    dim = _REF_IM - omega_im
    dist = np.sqrt(dre ** 2 + dim ** 2)
    idx = int(np.argmin(dist))
    d = float(dist[idx])

    quality: str
    if d < THRESHOLD_GOOD:
        quality = "good"
    elif d < THRESHOLD_FAIR:
        quality = "fair"
    else:
        quality = "poor"

    return {
        "ref_n": int(_REF_N[idx]),
        "ref_chi": float(_REF_CHI[idx]),
        "ref_omega_re": float(_REF_RE[idx]),
        "ref_omega_im": float(_REF_IM[idx]),
        "distance": d,
        "match_quality": quality,
    }


def overtone_band_stats() -> Dict[str, Dict[str, float]]:
    """Bounding box of each overtone band (for reporting)."""
    bands: Dict[str, Dict[str, float]] = {}
    for n in (0, 1, 2):
        mask = _REF_N == n
        bands[str(n)] = {
            "omega_re_min": float(_REF_RE[mask].min()),
            "omega_re_max": float(_REF_RE[mask].max()),
            "omega_im_min": float(_REF_IM[mask].min()),
            "omega_im_max": float(_REF_IM[mask].max()),
        }
    return bands


# ---------------------------------------------------------------------------
# Contract loading
# ---------------------------------------------------------------------------

def load_downstream_contract(summary_path: Path) -> Dict[str, Any]:
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    contract = payload.get("downstream_contract")
    if contract is None:
        raise KeyError(
            f"'downstream_contract' key not found in {summary_path}.\n"
            "Run 04_kan_qnm_classifier.py first."
        )
    return contract


def load_cluster_analysis(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Per-event validation
# ---------------------------------------------------------------------------

def validate_event_modes(
    rows: List[Dict[str, Any]],
    cluster_labels: Dict[Tuple[str, int], int],
    feature_cols: List[str],
) -> List[Dict[str, Any]]:
    """
    For every row that has finite feature values, look up its cluster
    centroid match and also compute a per-row nearest-Kerr distance.
    """
    results = []
    for r in rows:
        event = r.get("event", "")
        mode_rank = int(r.get("mode_rank", -1))
        cluster_id = cluster_labels.get((str(event), mode_rank))

        # Per-row match (direct, using individual QNM values)
        ore = r.get("omega_re_norm")
        oim = r.get("omega_im_norm")
        try:
            ore_f = float(ore)  # type: ignore[arg-type]
            oim_f = float(oim)  # type: ignore[arg-type]
            row_finite = np.isfinite(ore_f) and np.isfinite(oim_f)
        except (TypeError, ValueError):
            row_finite = False

        row_match: Optional[Dict[str, Any]] = None
        if row_finite:
            row_match = nearest_kerr_mode(ore_f, oim_f)

        results.append({
            "event": event,
            "mode_rank": mode_rank,
            "cluster_id": cluster_id,
            "omega_re_norm": float(ore_f) if row_finite else None,
            "omega_im_norm": float(oim_f) if row_finite else None,
            "kerr_match": row_match,
        })
    return results


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------

def load_dataset(csv_path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            parsed: Dict[str, Any] = {}
            for k, v in row.items():
                if v in ("", "nan", "NaN", "inf", "-inf"):
                    parsed[k] = float("nan")
                else:
                    try:
                        parsed[k] = float(v)
                    except (ValueError, TypeError):
                        parsed[k] = v
            rows.append(parsed)
    return rows


def load_cluster_labels_csv(path: Path) -> Dict[Tuple[str, int], int]:
    """Return {(event, mode_rank): cluster_id}."""
    labels: Dict[Tuple[str, int], int] = {}
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            event = row.get("event", "")
            try:
                mode_rank = int(float(row.get("mode_rank", -1)))
                cluster_id = int(float(row.get("cluster_id", -1)))
            except (ValueError, TypeError):
                continue
            labels[(event, mode_rank)] = cluster_id
    return labels


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_match_table_csv(
    cluster_matches: List[Dict[str, Any]],
    path: Path,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = [
        "cluster_id", "n_rows",
        "centroid_omega_re", "centroid_omega_im",
        "ref_n", "ref_chi", "ref_omega_re", "ref_omega_im",
        "distance", "match_quality",
    ]
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=cols)
        writer.writeheader()
        for m in cluster_matches:
            writer.writerow({c: m.get(c, "") for c in cols})


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description=(
            "Validate QNM cluster centroids against Kerr reference modes "
            "(Berti et al. 2009, l=m=2, n=0,1,2)."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    src = ap.add_mutually_exclusive_group()
    src.add_argument(
        "--summary",
        default="runs/qnm_kan/qnm_kan_summary.json",
        help="qnm_kan_summary.json written by 04_kan_qnm_classifier.py",
    )
    src.add_argument(
        "--cluster-analysis",
        default=None,
        help="cluster_analysis.json (bypasses --summary)",
    )
    ap.add_argument(
        "--cluster-csv",
        default=None,
        help="cluster_labels.csv (required when --cluster-analysis is used)",
    )
    ap.add_argument(
        "--dataset-csv",
        default=None,
        help="qnm_dataset.csv for per-event row-level validation",
    )
    ap.add_argument(
        "--out-dir",
        default="runs/qnm_kerr_validation",
        help="Output directory",
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir).resolve()

    print("=" * 60)
    print(f"QNM KERR VALIDATION  —  {SCRIPT_VERSION}")
    print(f"  out-dir : {out_dir}")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Resolve inputs
    # ------------------------------------------------------------------
    if args.cluster_analysis:
        cluster_analysis_path = Path(args.cluster_analysis).resolve()
        cluster_csv_path = Path(args.cluster_csv).resolve() if args.cluster_csv else None
        dataset_csv_path = Path(args.dataset_csv).resolve() if args.dataset_csv else None
    else:
        summary_path = Path(args.summary).resolve()
        if not summary_path.exists():
            print(f"[ERROR] Summary not found: {summary_path}")
            print(
                "  Run 04_kan_qnm_classifier.py first:\n"
                "    python3 04_kan_qnm_classifier.py "
                "--summary runs/qnm_symbolic/qnm_symbolic_summary.json"
            )
            return 1
        contract = load_downstream_contract(summary_path)
        cluster_analysis_path = (
            summary_path.parent / "cluster_analysis.json"
        )
        cluster_csv_path = Path(contract["cluster_labels_csv"]).resolve()
        dataset_csv_path = Path(contract["dataset_csv"]).resolve()

    print(f"\n  cluster analysis : {cluster_analysis_path}")
    if cluster_csv_path:
        print(f"  cluster labels   : {cluster_csv_path}")
    if dataset_csv_path:
        print(f"  dataset CSV      : {dataset_csv_path}")

    if not cluster_analysis_path.exists():
        print(f"[ERROR] cluster_analysis.json not found: {cluster_analysis_path}")
        return 1

    # ------------------------------------------------------------------
    # Load cluster centroids
    # ------------------------------------------------------------------
    cluster_analysis = load_cluster_analysis(cluster_analysis_path)
    clusters: Dict[str, Any] = cluster_analysis.get("clusters", {})
    feature_cols: List[str] = cluster_analysis.get(
        "features", ["omega_re_norm", "omega_im_norm"]
    )

    # Expect exactly 2 features: (omega_re_norm, omega_im_norm)
    re_col = feature_cols[0] if len(feature_cols) >= 1 else "omega_re_norm"
    im_col = feature_cols[1] if len(feature_cols) >= 2 else "omega_im_norm"

    print(f"\n  features : {re_col}, {im_col}")
    print(f"  clusters : {list(clusters.keys())}")

    # ------------------------------------------------------------------
    # Match each cluster centroid to Kerr reference
    # ------------------------------------------------------------------
    print("\nKerr reference matching (l=m=2, n=0,1,2):")
    cluster_matches: List[Dict[str, Any]] = []

    for cluster_id, info in sorted(clusters.items(), key=lambda x: int(x[0])):
        centroid = info.get("centroid", {})
        n_rows = info.get("n", 0)

        ore = centroid.get(re_col, float("nan"))
        oim = centroid.get(im_col, float("nan"))

        try:
            ore_f, oim_f = float(ore), float(oim)
            has_values = np.isfinite(ore_f) and np.isfinite(oim_f)
        except (TypeError, ValueError):
            has_values = False

        if not has_values:
            print(f"  cluster {cluster_id}: centroid has NaN — skipping")
            cluster_matches.append({
                "cluster_id": int(cluster_id),
                "n_rows": n_rows,
                "centroid_omega_re": None,
                "centroid_omega_im": None,
                "ref_n": None, "ref_chi": None,
                "ref_omega_re": None, "ref_omega_im": None,
                "distance": None, "match_quality": "no_data",
            })
            continue

        match = nearest_kerr_mode(ore_f, oim_f)

        print(
            f"  cluster {cluster_id}  ({n_rows} rows)  "
            f"centroid=({ore_f:.4f}, {oim_f:.4f})"
        )
        print(
            f"    → Kerr n={match['ref_n']}  chi={match['ref_chi']:.2f}  "
            f"({match['ref_omega_re']:.4f}, {match['ref_omega_im']:.4f})  "
            f"dist={match['distance']:.4f}  [{match['match_quality']}]"
        )

        cluster_matches.append({
            "cluster_id": int(cluster_id),
            "n_rows": n_rows,
            "centroid_omega_re": ore_f,
            "centroid_omega_im": oim_f,
            **match,
        })

    # ------------------------------------------------------------------
    # Per-row validation (if cluster CSV + dataset available)
    # ------------------------------------------------------------------
    row_validation: Optional[List[Dict[str, Any]]] = None
    n_good = n_fair = n_poor = 0

    if cluster_csv_path and cluster_csv_path.exists() and dataset_csv_path and dataset_csv_path.exists():
        print("\nPer-row Kerr distance (individual QNM values)...")
        rows = load_dataset(dataset_csv_path)
        label_map = load_cluster_labels_csv(cluster_csv_path)
        row_validation = validate_event_modes(rows, label_map, feature_cols)

        for rv in row_validation:
            m = rv.get("kerr_match")
            if m is None:
                continue
            q = m.get("match_quality", "poor")
            if q == "good":
                n_good += 1
            elif q == "fair":
                n_fair += 1
            else:
                n_poor += 1

        total_matched = n_good + n_fair + n_poor
        print(f"  {total_matched} rows matched  "
              f"good={n_good}  fair={n_fair}  poor={n_poor}")

    # ------------------------------------------------------------------
    # Write outputs
    # ------------------------------------------------------------------
    out_dir.mkdir(parents=True, exist_ok=True)

    match_csv_path = out_dir / "kerr_match_table.csv"
    write_match_table_csv(cluster_matches, match_csv_path)

    # Overall verdict
    good_clusters = sum(1 for m in cluster_matches if m.get("match_quality") == "good")
    fair_clusters = sum(1 for m in cluster_matches if m.get("match_quality") == "fair")
    total_clusters = len(cluster_matches)

    if good_clusters == total_clusters:
        verdict = "ALL_CLUSTERS_KERR_CONSISTENT"
    elif good_clusters + fair_clusters == total_clusters:
        verdict = "CLUSTERS_BROADLY_KERR_CONSISTENT"
    elif good_clusters > 0:
        verdict = "PARTIAL_KERR_CONSISTENCY"
    else:
        verdict = "NO_KERR_CONSISTENCY"

    print(f"\nVerdict: {verdict}")

    summary: Dict[str, Any] = {
        "created_at": utc_now(),
        "script": SCRIPT_VERSION,
        "cluster_analysis_path": str(cluster_analysis_path),
        "features": feature_cols,
        "reference": "Berti, Cardoso & Starinets 2009 (arXiv:0905.2975), l=m=2, n=0,1,2",
        "thresholds": {"good": THRESHOLD_GOOD, "fair": THRESHOLD_FAIR},
        "cluster_matches": cluster_matches,
        "n_clusters_good": good_clusters,
        "n_clusters_fair": fair_clusters,
        "n_clusters_poor": total_clusters - good_clusters - fair_clusters,
        "verdict": verdict,
        "kerr_match_table_csv": str(match_csv_path),
        "overtone_bands": overtone_band_stats(),
    }

    if row_validation is not None:
        summary["per_row_stats"] = {
            "n_matched": n_good + n_fair + n_poor,
            "n_good": n_good,
            "n_fair": n_fair,
            "n_poor": n_poor,
        }

    summary_path = out_dir / "qnm_kerr_validation_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # ------------------------------------------------------------------
    # Final report
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("DONE")
    print(f"  Match table : {match_csv_path}")
    print(f"  Summary     : {summary_path}")
    print(f"  Verdict     : {verdict}")
    print("=" * 60)
    print()
    print("Inferred overtone assignments:")
    for m in cluster_matches:
        if m.get("ref_n") is not None:
            print(
                f"  cluster {m['cluster_id']} → "
                f"n={m['ref_n']}  (chi≈{m.get('ref_chi', '?'):.2f}  "
                f"dist={m.get('distance', float('nan')):.4f}  "
                f"{m.get('match_quality', '?')})"
            )
    print()
    print("Next step — connect to Kerr QNM dictionary:")
    print("  python3 07K_kerr_qnm_dictionary.py \\")
    print("      --validation-summary runs/qnm_kerr_validation/"
          "qnm_kerr_validation_summary.json")

    return 0


if __name__ == "__main__":
    sys.exit(main())
