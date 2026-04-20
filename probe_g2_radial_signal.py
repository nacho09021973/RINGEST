#!/usr/bin/env python3
"""
probe_g2_radial_signal.py
Sonda mínima: ¿G2(x) raw contiene más señal sobre A(z) que los 9 escalares actuales?

Uso:
    python3 probe_g2_radial_signal.py --run-dir runs/ads_gkpw_20260416_091407

Requiere: numpy, h5py, scikit-learn
"""

import argparse
import json
from pathlib import Path

import numpy as np
import h5py
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score


# ── Replicar los 9 escalares de build_feature_vector ─────────────────────────

def _nine_scalars(G2: np.ndarray, x: np.ndarray) -> np.ndarray:
    """Los mismos 9 escalares que usa 02_emergent_geometry_engine.py V2.5."""
    feats = np.zeros(9, dtype=np.float32)
    mask = (G2 > 0) & np.isfinite(G2) & (x > 0) & np.isfinite(x)
    if mask.sum() < 6:
        return feats
    xl = np.log(x[mask])
    gl = np.log(G2[mask] + 1e-8)
    m2 = np.isfinite(xl) & np.isfinite(gl)
    if m2.sum() < 6:
        return feats
    xl, gl = xl[m2], gl[m2]
    # slope, curvature
    try:
        c1 = np.polyfit(xl, gl, 1)
        feats[0] = float(np.clip(c1[0], -20, 20))
    except Exception:
        pass
    if len(xl) >= 4:
        try:
            c2 = np.polyfit(xl, gl, 2)
            feats[1] = float(np.clip(c2[0], -10, 10))
        except Exception:
            pass
    # small_x, large_x (en espacio original)
    G2f = G2[np.isfinite(G2)]
    feats[2] = float(np.clip(G2f[0], 0, 1e6)) if len(G2f) else 0.0
    feats[3] = float(np.clip(G2f[-1], 0, 1e6)) if len(G2f) else 0.0
    # slope UV / IR
    n = len(xl)
    mid = n // 2
    try:
        feats[4] = float(np.clip(np.polyfit(xl[:mid], gl[:mid], 1)[0], -20, 20))
    except Exception:
        feats[4] = feats[0]
    try:
        feats[5] = float(np.clip(np.polyfit(xl[mid:], gl[mid:], 1)[0], -20, 20))
    except Exception:
        feats[5] = feats[0]
    feats[6] = float(np.clip(feats[5] - feats[4], -10, 10))  # running
    # std, skew en log-space
    G2v = G2[np.isfinite(G2) & (G2 > 0)]
    if len(G2v) >= 3:
        lg = np.log(G2v + 1e-8)
        std = float(np.std(lg))
        feats[7] = float(np.clip(std, 0, 20))
        if std > 1e-10:
            feats[8] = float(np.clip(np.mean(((lg - lg.mean()) / std) ** 3), -10, 10))
    return feats


# ── Carga de datos ────────────────────────────────────────────────────────────

def load_run(run_dir: Path):
    """
    Devuelve listas paralelas:
        g2_raw  : list[np.ndarray]  — G2(x) como vector (longitud variable, rellenado a común)
        scalars : list[np.ndarray]  — 9 escalares
        A_truth : list[np.ndarray]  — A(z) verdadero (longitud común n_z)
        f_truth : list[np.ndarray]  — f(z) verdadero (longitud común n_z)
        z_h     : list[float]       — horizonte verdadero
        x_grids : list[np.ndarray]  — grids x originales
        names   : list[str]
    """
    # Intentar encontrar los datos de Stage 01 dentro del run.
    # Soportamos dos layouts:
    # 1. legacy: boundary/ y bulk_truth/ separados
    # 2. actual Ruta A: .h5 únicos bajo 01_generate_sandbox_geometries/ con
    #    grupos internos boundary y bulk_truth
    candidates_boundary = [
        run_dir / "01_generate_sandbox_geometries" / "boundary",
        run_dir / "boundary",
    ]
    candidates_bulk = [
        run_dir / "01_generate_sandbox_geometries" / "bulk_truth",
        run_dir / "bulk_truth",
    ]
    candidates_stage01 = [
        run_dir / "01_generate_sandbox_geometries",
        run_dir,
    ]
    boundary_dir = next((p for p in candidates_boundary if p.exists()), None)
    bulk_dir = next((p for p in candidates_bulk if p.exists()), None)
    stage01_dir = next((p for p in candidates_stage01 if p.exists()), None)

    if boundary_dir is None and stage01_dir is None:
        raise FileNotFoundError(
            f"No se encontró ni boundary/ ni Stage-01 directo en {run_dir}. "
            f"Probé boundary={ [str(p) for p in candidates_boundary] }, "
            f"stage01={ [str(p) for p in candidates_stage01] }"
        )
    if bulk_dir is None and stage01_dir is None:
        raise FileNotFoundError(
            f"No se encontró ni bulk_truth/ ni Stage-01 directo en {run_dir}. "
            f"Probé bulk={ [str(p) for p in candidates_bulk] }, "
            f"stage01={ [str(p) for p in candidates_stage01] }"
        )

    use_embedded_layout = boundary_dir is None or bulk_dir is None
    if use_embedded_layout:
        boundary_files = sorted(
            p for p in stage01_dir.glob("*.h5")
            if p.is_file()
        )
        print(f"  stage01    : {len(boundary_files)} archivos en {stage01_dir}")
        print("  layout     : embedded boundary + bulk_truth en el mismo .h5")
    else:
        boundary_files = sorted(boundary_dir.glob("*.h5"))
        print(f"  boundary/  : {len(boundary_files)} archivos en {boundary_dir}")
        print(f"  bulk_truth/: {bulk_dir}")

    g2_raw, scalars, A_truth_list, f_truth_list, zh_list, names = [], [], [], [], [], []

    for bf in boundary_files:
        name = bf.stem.replace("_boundary", "")

        try:
            if use_embedded_layout:
                with h5py.File(bf, "r") as f:
                    if "boundary" not in f or "bulk_truth" not in f:
                        print(f"  [SKIP] Sin grupos boundary/bulk_truth en {name}")
                        continue
                    bnd = f["boundary"]
                    bt = f["bulk_truth"]
                    G2 = None
                    x = None
                    for key in bnd.keys():
                        if key.startswith("G2_"):
                            G2 = bnd[key][:]
                            break
                    if "x_grid" in bnd:
                        x = bnd["x_grid"][:]
                    elif "x_grid" in f:
                        x = f["x_grid"][:]
                    if G2 is None or x is None or "A_truth" not in bt or "f_truth" not in bt:
                        print(f"  [SKIP] Sin G2_* o x_grid o A_truth/f_truth en {name}")
                        continue
                    G2 = G2.astype(float).ravel()
                    x = x.astype(float).ravel()
                    A = bt["A_truth"][:].astype(float).ravel()
                    f_truth = bt["f_truth"][:].astype(float).ravel()
                    z_h = float(f.attrs.get("z_h", 0.0))
            else:
                bulk_candidates = [
                    bulk_dir / f"{name}_bulk_truth.h5",
                    bulk_dir / f"{name}.h5",
                ]
                bulk_f = next((p for p in bulk_candidates if p.exists()), None)
                if bulk_f is None:
                    print(f"  [SKIP] Sin bulk_truth para {name}")
                    continue

                with h5py.File(bf, "r") as f:
                    bnd = f["boundary"]
                    G2 = None
                    x = None
                    for key in bnd.keys():
                        if key.startswith("G2_"):
                            G2 = bnd[key][:]
                            break
                    if "x_grid" in bnd:
                        x = bnd["x_grid"][:]
                    elif "x_grid" in f:
                        x = f["x_grid"][:]
                    if G2 is None or x is None:
                        print(f"  [SKIP] Sin G2_* o x_grid en {name}")
                        continue
                    G2 = G2.astype(float).ravel()
                    x = x.astype(float).ravel()

                with h5py.File(bulk_f, "r") as f:
                    bt = f["bulk_truth"]
                    A = bt["A_truth"][:].astype(float).ravel()
                    f_truth = bt["f_truth"][:].astype(float).ravel()
                    z_h = float(f.attrs.get("z_h", 0.0))

        except Exception as e:
            print(f"  [SKIP] Error leyendo {name}: {e}")
            continue

        g2_raw.append((G2, x))
        scalars.append(_nine_scalars(G2, x))
        A_truth_list.append(A)
        f_truth_list.append(f_truth)
        zh_list.append(z_h)
        names.append(name)

    print(f"  Sistemas cargados: {len(names)}")
    return g2_raw, scalars, A_truth_list, f_truth_list, np.array(zh_list, dtype=np.float32), names


# ── Interpolación a grid común ────────────────────────────────────────────────

def interpolate_to_common_grid(arrays):
    """Interpola arrays de distinta longitud al grid del más corto."""
    min_len = min(len(a) for a in arrays)
    out = []
    for a in arrays:
        if len(a) == min_len:
            out.append(a)
        else:
            idx = np.round(np.linspace(0, len(a) - 1, min_len)).astype(int)
            out.append(a[idx])
    return np.array(out)


def pad_or_truncate_g2(g2_x_list, target_len=100):
    """Normaliza G2(x) a longitud fija interpolando."""
    out = []
    for G2, x in g2_x_list:
        if len(G2) == target_len:
            out.append(G2)
        else:
            idx = np.round(np.linspace(0, len(G2) - 1, target_len)).astype(int)
            out.append(G2[idx])
    return np.array(out, dtype=np.float32)


# ── Sonda de regresión ────────────────────────────────────────────────────────

def probe_features(X: np.ndarray, A: np.ndarray, train_idx, test_idx, label: str):
    """
    Ridge sobre X → A(z). Predice cada punto de z por separado.
    Devuelve R² medio y mediana sobre el grid de z.
    """
    X_tr, X_te = X[train_idx], X[test_idx]
    A_tr, A_te = A[train_idx], A[test_idx]

    sc = StandardScaler()
    X_tr_s = sc.fit_transform(X_tr)
    X_te_s = sc.transform(X_te)

    n_z = A.shape[1]
    r2s = []
    ridge = Ridge(alpha=1.0)
    for iz in range(n_z):
        ridge.fit(X_tr_s, A_tr[:, iz])
        y_pred = ridge.predict(X_te_s)
        r2 = r2_score(A_te[:, iz], y_pred)
        r2s.append(r2)

    r2s = np.array(r2s)
    print(f"\n  [{label}]")
    print(f"    n_features : {X.shape[1]}")
    print(f"    R²(A) medio  : {np.mean(r2s):.4f}")
    print(f"    R²(A) mediana: {np.median(r2s):.4f}")
    print(f"    R²(A) min    : {np.min(r2s):.4f}")
    print(f"    R²(A) max    : {np.max(r2s):.4f}")
    print(f"    % puntos R²>0: {100 * np.mean(r2s > 0):.1f}%")
    return r2s


def probe_scalar_target(X: np.ndarray, y: np.ndarray, train_idx, test_idx, label: str, target_name: str):
    """Ridge sobre X -> y escalar."""
    X_tr, X_te = X[train_idx], X[test_idx]
    y_tr, y_te = y[train_idx], y[test_idx]

    sc = StandardScaler()
    X_tr_s = sc.fit_transform(X_tr)
    X_te_s = sc.transform(X_te)

    ridge = Ridge(alpha=1.0)
    ridge.fit(X_tr_s, y_tr)
    y_pred = ridge.predict(X_te_s)
    r2 = r2_score(y_te, y_pred)
    mae = float(np.mean(np.abs(y_te - y_pred)))

    print(f"\n  [{label}]")
    print(f"    n_features : {X.shape[1]}")
    print(f"    target     : {target_name}")
    print(f"    R²         : {r2:.4f}")
    print(f"    MAE        : {mae:.4f}")
    return float(r2), mae


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True, help="Ruta al run de sandbox")
    parser.add_argument("--g2-len", type=int, default=100,
                        help="Longitud a la que se interpola G2(x) (default: 100)")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    print(f"\n=== probe_g2_radial_signal ===")
    print(f"  run_dir: {run_dir}")

    g2_x_list, scalars_list, A_list, f_list, zh, names = load_run(run_dir)

    if len(names) < 5:
        print(f"\n[ABORT] Solo {len(names)} sistemas. Insuficiente para sonda.")
        return

    # Matrices
    X_scalars = np.array(scalars_list, dtype=np.float32)          # (N, 9)
    X_g2_raw  = pad_or_truncate_g2(g2_x_list, args.g2_len)        # (N, g2_len)
    A_matrix  = interpolate_to_common_grid(A_list)                  # (N, n_z)
    f_matrix  = interpolate_to_common_grid(f_list)                  # (N, n_z)

    N = len(names)
    print(f"\n  Shapes:")
    print(f"    X_scalars : {X_scalars.shape}")
    print(f"    X_g2_raw  : {X_g2_raw.shape}")
    print(f"    A_matrix  : {A_matrix.shape}")
    print(f"    f_matrix  : {f_matrix.shape}")
    print(f"    z_h       : {zh.shape}")

    # Split train/test (mismo ratio que el run: 2/3 train, 1/3 test)
    rng = np.random.default_rng(args.seed)
    idx = rng.permutation(N)
    n_train = int(np.ceil(2 * N / 3))
    train_idx = idx[:n_train]
    test_idx  = idx[n_train:]
    print(f"\n  Split: {len(train_idx)} train / {len(test_idx)} test")

    # Sondas
    r2_scalars = probe_features(X_scalars, A_matrix, train_idx, test_idx,
                                 "9 ESCALARES (actual)")
    r2_g2raw   = probe_features(X_g2_raw,  A_matrix, train_idx, test_idx,
                                 f"G2 RAW {args.g2_len}pts (propuesta)")

    r2f_scalars = probe_features(X_scalars, f_matrix, train_idx, test_idx,
                                 "9 ESCALARES (actual) -> f(z)")
    r2f_g2raw   = probe_features(X_g2_raw, f_matrix, train_idx, test_idx,
                                 f"G2 RAW {args.g2_len}pts (propuesta) -> f(z)")

    r2zh_scalars, maezh_scalars = probe_scalar_target(
        X_scalars, zh, train_idx, test_idx, "9 ESCALARES (actual) -> z_h", "z_h"
    )
    r2zh_g2raw, maezh_g2raw = probe_scalar_target(
        X_g2_raw, zh, train_idx, test_idx, f"G2 RAW {args.g2_len}pts (propuesta) -> z_h", "z_h"
    )

    # Veredicto
    delta = np.mean(r2_g2raw) - np.mean(r2_scalars)
    print(f"\n=== VEREDICTO ===")
    print(f"  ΔR²(medio) = G2_raw - escalares = {delta:+.4f}")
    if delta > 0.10:
        print("  → G2 raw aporta señal radial clara. Rediseño del encoder justificado.")
    elif delta > 0.02:
        print("  → G2 raw aporta algo. Señal marginal; rediseño posible pero incierto.")
    else:
        print("  → G2 raw no aporta señal adicional. El problema no es la compresión.")
        print("    Hipótesis alternativa: la variabilidad de A(z) entre geometrías ads")
        print("    con parámetros similares es demasiado pequeña para recuperarse desde boundary.")

    delta_f = np.mean(r2f_g2raw) - np.mean(r2f_scalars)
    print(f"\n  ΔR²_f(medio) = G2_raw - escalares = {delta_f:+.4f}")
    if delta_f > 0.10:
        print("  → En f(z), G2 raw aporta señal radial clara.")
    elif delta_f > 0.02:
        print("  → En f(z), G2 raw aporta algo, pero marginal.")
    else:
        print("  → En f(z), G2 raw no mejora claramente sobre los 9 escalares.")

    delta_zh = r2zh_g2raw - r2zh_scalars
    print(f"\n  ΔR²_z_h = G2_raw - escalares = {delta_zh:+.4f}")
    print(f"  ΔMAE_z_h = G2_raw - escalares = {maezh_g2raw - maezh_scalars:+.4f}")


if __name__ == "__main__":
    main()
