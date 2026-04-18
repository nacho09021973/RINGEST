#!/usr/bin/env python3
"""
04_kan_qnm_classifier.py  v1.0

KAN (Kolmogorov-Arnold Network) classifier on the dimensionless QNM plane.

Reads the kan_contract written by 03_discover_qnm_equations.py, loads the
QNM dataset, assigns unsupervised cluster labels with k-means, then trains a
KAN to learn the cluster boundary.  Calls model.auto_symbolic() to attempt
symbolic extraction of the learned map.

Chain:
    03_discover_qnm_equations.py  →  runs/qnm_symbolic/qnm_symbolic_summary.json
    THIS SCRIPT                   →  runs/qnm_kan/
                                        qnm_kan_summary.json      ← downstream contract
                                        cluster_labels.csv
                                        cluster_analysis.json

Default input features   : omega_re_norm, omega_im_norm  (from kan_contract)
Default task             : cluster_classification
Clustering               : k-means (unsupervised, no ground-truth labels required)

Usage
-----
    # Analysis only — cluster + profile, no KAN / no torch:
    python3 04_kan_qnm_classifier.py \\
        --summary runs/qnm_symbolic/qnm_symbolic_summary.json \\
        --analysis-only

    # Full KAN training + symbolic extraction:
    python3 04_kan_qnm_classifier.py \\
        --summary runs/qnm_symbolic/qnm_symbolic_summary.json \\
        --n-clusters 3 --kan-steps 100

    # Override dataset CSV directly (skip summary):
    python3 04_kan_qnm_classifier.py \\
        --dataset-csv runs/qnm_dataset/qnm_dataset.csv \\
        --features omega_re_norm omega_im_norm \\
        --n-clusters 3 --kan-steps 100
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

SCRIPT_VERSION = "04_kan_qnm_classifier.py v1.0"

# ---------------------------------------------------------------------------
# Lazy KAN import — keeps --analysis-only free of torch / Julia overhead
# ---------------------------------------------------------------------------
_KAN_IMPORT_ATTEMPTED: bool = False
_KAN_IMPORT_ERROR: Optional[str] = None
KAN = None  # populated by _ensure_kan()


def _ensure_kan() -> None:
    global _KAN_IMPORT_ATTEMPTED, _KAN_IMPORT_ERROR, KAN
    if _KAN_IMPORT_ATTEMPTED:
        return
    _KAN_IMPORT_ATTEMPTED = True
    try:
        from kan import KAN as _KAN  # noqa: PLC0415
        KAN = _KAN
    except Exception as exc:
        _KAN_IMPORT_ERROR = str(exc)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Contract loading
# ---------------------------------------------------------------------------

def load_kan_contract(summary_path: Path) -> Dict[str, Any]:
    """Read the kan_contract section from qnm_symbolic_summary.json."""
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    contract = payload.get("kan_contract")
    if contract is None:
        raise KeyError(
            f"'kan_contract' key not found in {summary_path}.\n"
            "Run 03_discover_qnm_equations.py first."
        )
    return contract


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


def extract_feature_matrix(
    rows: List[Dict[str, Any]],
    feature_cols: List[str],
) -> Tuple[np.ndarray, List[int]]:
    """
    Return (X, valid_indices) where X has shape (n_valid, n_features).
    Rows with any NaN in feature_cols are excluded.
    """
    valid_idx = []
    X_list = []
    for i, r in enumerate(rows):
        vals = []
        ok = True
        for c in feature_cols:
            raw = r.get(c)
            try:
                f = float(raw)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                ok = False
                break
            if not np.isfinite(f):
                ok = False
                break
            vals.append(f)
        if ok:
            valid_idx.append(i)
            X_list.append(vals)
    X = np.array(X_list, dtype=np.float32) if X_list else np.empty((0, len(feature_cols)), dtype=np.float32)
    return X, valid_idx


# ---------------------------------------------------------------------------
# Unsupervised clustering (k-means via scipy — no extra dep beyond numpy)
# ---------------------------------------------------------------------------

def kmeans_cluster(X: np.ndarray, n_clusters: int, seed: int) -> np.ndarray:
    """
    Simple k-means using scipy.  Falls back to a deterministic sign-based
    split when scipy is unavailable (e.g. pure analysis-only environments).
    Returns integer label array of shape (n,).
    """
    if X.shape[0] < n_clusters:
        return np.zeros(X.shape[0], dtype=int)

    try:
        from scipy.cluster.vq import kmeans2  # noqa: PLC0415
        rng = np.random.default_rng(seed)
        init_idx = rng.choice(X.shape[0], size=n_clusters, replace=False)
        centroids, labels = kmeans2(X, X[init_idx], iter=50, minit="matrix")
        return labels.astype(int)
    except ImportError:
        pass

    # Fallback: partition on first principal axis via sign of centered values
    labels = np.zeros(X.shape[0], dtype=int)
    for k in range(1, n_clusters):
        mask = labels == k - 1
        if mask.sum() < 2:
            break
        med = np.median(X[mask, 0])
        labels[mask & (X[:, 0] > med)] = k
    return labels


def cluster_stats(
    X: np.ndarray,
    labels: np.ndarray,
    feature_cols: List[str],
) -> Dict[str, Any]:
    unique = sorted(set(int(l) for l in labels))
    stats: Dict[str, Any] = {}
    for k in unique:
        mask = labels == k
        Xk = X[mask]
        stats[str(k)] = {
            "n": int(mask.sum()),
            "centroid": {c: float(np.mean(Xk[:, i])) for i, c in enumerate(feature_cols)},
            "std": {c: float(np.std(Xk[:, i])) for i, c in enumerate(feature_cols)},
        }
    return stats


# ---------------------------------------------------------------------------
# KAN training (classification via one-hot regression)
# ---------------------------------------------------------------------------

def train_kan(
    X: np.ndarray,
    labels: np.ndarray,
    n_clusters: int,
    hidden_width: int,
    steps: int,
    grid: int,
    seed: int,
    out_dir: Path,
) -> Dict[str, Any]:
    """
    Train a KAN [n_features, hidden_width, n_clusters] on one-hot labels.
    Returns a metrics dict.  Saves model state to out_dir/kan_model/.
    """
    _ensure_kan()
    if KAN is None:
        return {
            "status": "kan_unavailable",
            "error": _KAN_IMPORT_ERROR,
        }

    try:
        import torch  # noqa: PLC0415
    except ImportError as exc:
        return {"status": "torch_unavailable", "error": str(exc)}

    n_features = X.shape[1]

    # One-hot encode labels
    Y = np.zeros((len(labels), n_clusters), dtype=np.float32)
    for i, lbl in enumerate(labels):
        Y[i, int(lbl)] = 1.0

    # 80/20 split
    n_train = max(int(0.8 * len(X)), 1)
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(X))
    tr, te = idx[:n_train], idx[n_train:]

    dataset = {
        "train_input": torch.tensor(X[tr], dtype=torch.float32),
        "train_label": torch.tensor(Y[tr], dtype=torch.float32),
        "test_input":  torch.tensor(X[te] if len(te) > 0 else X[:1], dtype=torch.float32),
        "test_label":  torch.tensor(Y[te] if len(te) > 0 else Y[:1], dtype=torch.float32),
    }

    model = KAN(
        width=[n_features, hidden_width, n_clusters],
        grid=grid,
        k=3,
        seed=seed,
    )

    # pykan exposes the optimization entrypoint as `fit`, while some older
    # variants wrapped a custom `train`. Prefer `fit` when present and fall
    # back to `train` for compatibility with legacy installs.
    fit_fn = getattr(model, "fit", None)
    if callable(fit_fn):
        results = fit_fn(
            dataset,
            opt="LBFGS",
            steps=steps,
            lamb=0.01,
            lamb_entropy=2.0,
            loss_fn=torch.nn.MSELoss(),
        )
    else:
        results = model.train(
            dataset,
            opt="LBFGS",
            steps=steps,
            lamb=0.01,
            lamb_entropy=2.0,
            loss_fn=torch.nn.MSELoss(),
        )

    # Training accuracy on full dataset
    with torch.no_grad():
        preds = model(torch.tensor(X, dtype=torch.float32)).numpy()
    pred_labels = np.argmax(preds, axis=1)
    accuracy = float(np.mean(pred_labels == labels))

    # Final train/test loss
    train_loss = float(results["train_loss"][-1]) if results.get("train_loss") else float("nan")
    test_loss  = float(results["test_loss"][-1])  if results.get("test_loss")  else float("nan")

    # Save model
    model_dir = out_dir / "kan_model"
    model_dir.mkdir(parents=True, exist_ok=True)
    try:
        torch.save(model.state_dict(), model_dir / "model_state.pt")
        model_path = str(model_dir / "model_state.pt")
    except Exception:
        model_path = None

    # Symbolic extraction
    symbolic_formulas: List[str] = []
    try:
        model.auto_symbolic()
        for layer in model.symbolic_fun:
            for row in layer.funs_sympy:
                for expr in row:
                    s = str(expr)
                    if s not in ("0", ""):
                        symbolic_formulas.append(s)
    except Exception:
        pass

    return {
        "status": "ok",
        "architecture": [n_features, hidden_width, n_clusters],
        "grid": grid,
        "steps": steps,
        "n_train": int(n_train),
        "n_test": int(len(te)),
        "train_loss_final": train_loss,
        "test_loss_final": test_loss,
        "accuracy": accuracy,
        "model_path": model_path,
        "symbolic_formulas": symbolic_formulas,
    }


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_cluster_labels_csv(
    rows: List[Dict[str, Any]],
    valid_idx: List[int],
    labels: np.ndarray,
    path: Path,
) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["event", "ifo", "mode_rank", "cluster_id"])
        for pos, row_i in enumerate(valid_idx):
            r = rows[row_i]
            writer.writerow([
                r.get("event", ""),
                r.get("ifo", ""),
                int(r.get("mode_rank", -1)),
                int(labels[pos]),
            ])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description=(
            "KAN classifier on the dimensionless QNM plane "
            "(reads kan_contract from 03_discover_qnm_equations.py)."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    # Input — two mutually exclusive sources
    src = ap.add_mutually_exclusive_group()
    src.add_argument(
        "--summary",
        default="runs/qnm_symbolic/qnm_symbolic_summary.json",
        help="qnm_symbolic_summary.json written by 03_discover_qnm_equations.py",
    )
    src.add_argument(
        "--dataset-csv",
        default=None,
        help="Directly specify the dataset CSV (bypasses --summary contract)",
    )
    ap.add_argument(
        "--features", nargs="+",
        default=None,
        help="Feature columns (used only when --dataset-csv is given)",
    )
    # Output
    ap.add_argument(
        "--out-dir",
        default="runs/qnm_kan",
        help="Output directory",
    )
    # Mode
    ap.add_argument(
        "--analysis-only", action="store_true",
        help="Cluster the data and write the contract; skip KAN / torch",
    )
    # Clustering
    ap.add_argument(
        "--n-clusters", type=int, default=3,
        help="Number of k-means clusters",
    )
    # KAN hyperparameters
    ap.add_argument(
        "--kan-hidden", type=int, default=5,
        help="Hidden layer width for the KAN",
    )
    ap.add_argument(
        "--kan-steps", type=int, default=100,
        help="LBFGS optimisation steps",
    )
    ap.add_argument(
        "--kan-grid", type=int, default=5,
        help="KAN grid size (spline resolution)",
    )
    ap.add_argument(
        "--seed", type=int, default=42,
        help="Random seed",
    )
    ap.add_argument(
        "--min-rows", type=int, default=6,
        help="Minimum rows with finite features required to proceed",
    )
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir).resolve()

    print("=" * 60)
    print(f"QNM KAN CLASSIFIER  —  {SCRIPT_VERSION}")
    print(f"  out-dir : {out_dir}")
    print(f"  mode    : {'analysis-only' if args.analysis_only else 'kan-training'}")
    print("=" * 60)

    out_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Resolve dataset CSV + feature list
    # ------------------------------------------------------------------
    if args.dataset_csv:
        dataset_csv = Path(args.dataset_csv).resolve()
        feature_cols = args.features or ["omega_re_norm", "omega_im_norm"]
        kan_task = "cluster_classification"
        print(f"\n  dataset (direct): {dataset_csv}")
    else:
        summary_path = Path(args.summary).resolve()
        if not summary_path.exists():
            print(f"[ERROR] Summary not found: {summary_path}")
            print(
                "  Run 03_discover_qnm_equations.py first:\n"
                "    python3 03_discover_qnm_equations.py "
                "--dataset-csv runs/qnm_dataset/qnm_dataset.csv --analysis-only"
            )
            return 1
        contract = load_kan_contract(summary_path)
        dataset_csv = Path(contract["dataset_csv"]).resolve()
        feature_cols = contract.get("kan_input_features", ["omega_re_norm", "omega_im_norm"])
        kan_task = contract.get("kan_suggested_task", "cluster_classification")
        print(f"\n  contract  : {summary_path}")
        print(f"  dataset   : {dataset_csv}")
        print(f"  features  : {feature_cols}")
        print(f"  task      : {kan_task}")

    if not dataset_csv.exists():
        print(f"[ERROR] Dataset CSV not found: {dataset_csv}")
        return 1

    # ------------------------------------------------------------------
    # Load dataset
    # ------------------------------------------------------------------
    print("\nLoading dataset...")
    rows = load_dataset(dataset_csv)
    X, valid_idx = extract_feature_matrix(rows, feature_cols)
    print(f"  {len(rows)} total rows  →  {len(valid_idx)} with finite {feature_cols}")

    if len(valid_idx) < args.min_rows:
        print(
            f"[ERROR] Only {len(valid_idx)} finite rows "
            f"(need ≥ {args.min_rows}). "
            "Check that omega_re_norm / omega_im_norm are populated "
            "(requires M_final_Msun and chi_final in the dataset)."
        )
        return 1

    # ------------------------------------------------------------------
    # Unsupervised clustering
    # ------------------------------------------------------------------
    n_clusters = min(args.n_clusters, len(valid_idx))
    print(f"\nClustering ({n_clusters} k-means clusters)...")
    labels = kmeans_cluster(X, n_clusters, args.seed)
    stats = cluster_stats(X, labels, feature_cols)
    for k, s in stats.items():
        print(f"  cluster {k}: {s['n']} rows  centroid={s['centroid']}")

    cluster_csv_path = out_dir / "cluster_labels.csv"
    write_cluster_labels_csv(rows, valid_idx, labels, cluster_csv_path)
    print(f"  Labels → {cluster_csv_path}")

    cluster_analysis_path = out_dir / "cluster_analysis.json"
    cluster_analysis_path.write_text(
        json.dumps(
            {
                "n_clusters": n_clusters,
                "n_rows": len(valid_idx),
                "features": feature_cols,
                "clusters": stats,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    # ------------------------------------------------------------------
    # KAN training (skipped in analysis-only mode)
    # ------------------------------------------------------------------
    kan_result: Dict[str, Any] = {}

    if args.analysis_only:
        print("\n[analysis-only] Skipping KAN training.")
        kan_result = {"status": "skipped_analysis_only"}
    else:
        print(
            f"\nTraining KAN  "
            f"[{len(feature_cols)}, {args.kan_hidden}, {n_clusters}]  "
            f"grid={args.kan_grid}  steps={args.kan_steps}..."
        )
        (out_dir / "kan_model").mkdir(parents=True, exist_ok=True)
        kan_result = train_kan(
            X=X,
            labels=labels,
            n_clusters=n_clusters,
            hidden_width=args.kan_hidden,
            steps=args.kan_steps,
            grid=args.kan_grid,
            seed=args.seed,
            out_dir=out_dir,
        )
        status = kan_result.get("status", "?")
        if status == "ok":
            print(f"  accuracy  : {kan_result.get('accuracy', 0):.3f}")
            print(f"  train loss: {kan_result.get('train_loss_final', float('nan')):.4f}")
            print(f"  test  loss: {kan_result.get('test_loss_final', float('nan')):.4f}")
            syms = kan_result.get("symbolic_formulas", [])
            if syms:
                print(f"  symbolic  : {syms}")
        else:
            print(f"  Status: {status}  ({kan_result.get('error', '')})")

    # ------------------------------------------------------------------
    # Write qnm_kan_summary.json  (downstream contract)
    # ------------------------------------------------------------------
    summary = {
        "created_at": utc_now(),
        "script": SCRIPT_VERSION,
        "dataset_csv": str(dataset_csv),
        "out_dir": str(out_dir),
        "analysis_only": bool(args.analysis_only),
        "kan_import_attempted": bool(_KAN_IMPORT_ATTEMPTED),
        "kan_available": (
            bool(KAN is not None) if _KAN_IMPORT_ATTEMPTED else None
        ),
        "kan_import_error": _KAN_IMPORT_ERROR,
        "features": feature_cols,
        "task": kan_task,
        "n_clusters": n_clusters,
        "n_rows_total": len(rows),
        "n_rows_classified": len(valid_idx),
        "cluster_labels_csv": str(cluster_csv_path),
        "cluster_analysis": stats,
        "kan_training": kan_result,
        # Downstream contract for stage 05 (QNM–Kerr validation)
        "downstream_contract": {
            "schema_version": "1.0",
            "producer": SCRIPT_VERSION,
            "cluster_labels_csv": str(cluster_csv_path),
            "dataset_csv": str(dataset_csv),
            "n_clusters": n_clusters,
            "features_used": feature_cols,
            "symbolic_formulas": kan_result.get("symbolic_formulas", []),
            "note": (
                "Each row in cluster_labels.csv carries a cluster_id in "
                "[0, n_clusters). Use these together with the dataset CSV "
                "to validate cluster centroids against tabulated Kerr QNM "
                "values (Leaver / Berti tables)."
            ),
        },
    }

    summary_path = out_dir / "qnm_kan_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # ------------------------------------------------------------------
    # Final report
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("DONE")
    print(f"  Clusters       : {cluster_csv_path}")
    print(f"  Summary        : {summary_path}")
    print("=" * 60)
    print()
    print("Downstream contract written → downstream_contract")
    print(f"  cluster_labels_csv : {cluster_csv_path}")
    print(f"  n_clusters         : {n_clusters}")
    syms = kan_result.get("symbolic_formulas", [])
    if syms:
        print(f"  symbolic_formulas  : {syms}")
    print()
    print("Next step — Kerr QNM validation:")
    print("  python3 05_validate_qnm_kerr.py \\")
    print("      --summary runs/qnm_kan/qnm_kan_summary.json")

    return 0


if __name__ == "__main__":
    sys.exit(main())
