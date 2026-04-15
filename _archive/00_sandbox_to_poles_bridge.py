#!/usr/bin/env python3
"""
00_sandbox_to_poles_bridge.py — CUERDAS-MALDACENA

Genera embeddings tipo-polo para cada geometría del sandbox, usando
fórmulas analíticas de QNM (AdS, Lifshitz, hyperscaling).

Para cada HDF5 sandbox produce un gemelo con:
  - G2_ringdown = |Σ aₙ exp((-γ̃ₙ + iω̃ₙ) x̃)|²   (x̃ = t × ω_dom)
  - G_R_real/imag del mismo estilo que 02R
  - operators = [] (vacío, igual que datos LIGO)
  - temperature = 0.0

Esto crea un training set donde el modelo aprende a distinguir familias
desde la ESTRUCTURA DE POLOS (Q-factor, spacing), no desde los operadores.

Además genera geometrías "high-Q" sintéticas para cubrir el rango Kerr (Q~20).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import h5py
import numpy as np


# ── Embedding functions (same logic as 02R) ──────────────────────────────────

@dataclass
class Pole:
    freq_hz: float
    damping_1_over_s: float
    amp_abs: float


def get_normalization_scales(poles: List[Pole]) -> Tuple[float, float]:
    if not poles:
        return 2.0 * math.pi * 1.0, 0.5
    dom = max(poles, key=lambda p: p.amp_abs)
    return 2.0 * math.pi * float(dom.freq_hz), max(float(dom.damping_1_over_s), 1e-6)


def build_omega_grid_dimless(poles, n_omega, omega_dom):
    if poles:
        freqs = np.array([2 * math.pi * p.freq_hz for p in poles]) / omega_dom
        lo = max(1e-3, 0.5 * float(freqs.min()))
        hi = max(lo + 1e-3, 1.5 * float(freqs.max()))
    else:
        lo, hi = 0.1, 10.0
    return np.linspace(lo, hi, int(n_omega), dtype=np.float64)


def poles_to_gr(omega_grid_dimless, poles, omega_dom, normalization="unit_peak"):
    Nw = int(omega_grid_dimless.size)
    if not poles or Nw <= 0:
        return np.zeros((Nw, 1)), np.zeros((Nw, 1))
    amps = np.array([max(p.amp_abs, 0.0) for p in poles])
    if not np.any(amps > 0):
        amps = np.ones_like(amps)
    amps = amps / (amps.max() + 1e-12)
    omega = omega_grid_dimless.reshape(-1, 1).astype(complex)
    GR = np.zeros((Nw, 1), dtype=complex)
    for p, a in zip(poles, amps):
        w = (2 * math.pi * p.freq_hz - 1j * p.damping_1_over_s) / omega_dom
        GR[:, 0] += a / (omega[:, 0] - w)
    if normalization == "unit_peak":
        m = float(np.abs(GR[:, 0]).max())
        if m > 0:
            GR[:, 0] /= m
    return np.real(GR).astype(np.float64), np.imag(GR).astype(np.float64)


def build_x_grid(n_x, x_max=10.0):
    return np.linspace(1e-3, x_max, int(n_x), dtype=np.float64)


def poles_to_g2(x_grid, poles, omega_dom, normalization="unit_peak"):
    """x̃ = t × omega_dom  →  decay rate = γ/ω_dom = 1/Q"""
    Nx = int(x_grid.size)
    if not poles or Nx <= 0:
        return np.zeros(Nx)
    amps = np.array([max(p.amp_abs, 0.0) for p in poles])
    if not np.any(amps > 0):
        amps = np.ones_like(amps)
    amps = amps / (amps.max() + 1e-12)
    x = x_grid.reshape(-1, 1).astype(complex)
    s = np.zeros((Nx, 1), dtype=complex)
    for p, a in zip(poles, amps):
        g_d = p.damping_1_over_s / omega_dom   # = 1/Q
        w_d = 2 * math.pi * p.freq_hz / omega_dom  # = 1 for dominant
        s[:, 0] += a * np.exp((-g_d + 1j * w_d) * x[:, 0])
    G2 = np.abs(s[:, 0]) ** 2
    if normalization == "unit_peak":
        m = float(G2.max())
        if m > 0:
            G2 = G2 / m
    return G2.astype(np.float64)


# ── Analytic QNM estimates ────────────────────────────────────────────────────

def estimate_qnm_poles(family: str, T: float, z_dyn: float, theta: float,
                       d: int, delta_mean: float) -> List[Pole]:
    """
    Estima los 2 modos QNM dominantes (n=0, n=1) usando fórmulas analíticas.

    AdS:          ω_n = 2πT(2Δ + 2n + 1),   γ_n = 2πT(2n+1)
    Lifshitz z:   ω_n = 2πT(2Δ + 2n + 1)/z, γ_n = 2πT(2n+1)/z
    Hyperscaling: z_eff = z_dyn/(1 - θ/d),   igual que Lifshitz con z_eff
    Deformed:     como AdS pero γ × 1.5 (mayor anchura por deformación)
    Dpbrane:      como Lifshitz con z=1.5
    """
    if T < 1e-8:
        T = 0.2  # fallback razonable si T≈0

    z = z_dyn
    if family == "hyperscaling":
        z = z_dyn / max(1.0 - theta / max(d, 1), 0.1)
    elif family == "dpbrane":
        z = 1.5

    w0 = 2 * math.pi * T * (2 * delta_mean + 1) / z
    g0 = 2 * math.pi * T / z

    w1 = 2 * math.pi * T * (2 * delta_mean + 3) / z
    g1 = 2 * math.pi * T * 3 / z

    if family == "deformed":
        g0 *= 1.5
        g1 *= 1.5

    # Convertir rad/s → Hz (el embedding usa freq_hz)
    f0 = w0 / (2 * math.pi)
    f1 = w1 / (2 * math.pi)

    return [
        Pole(freq_hz=f0, damping_1_over_s=g0, amp_abs=1.0),
        Pole(freq_hz=f1, damping_1_over_s=g1, amp_abs=0.35),
    ]


# ── Conversión de un fichero ──────────────────────────────────────────────────

def convert_h5(src: Path, dst: Path, n_omega: int, n_x: int) -> dict:
    with h5py.File(src, "r") as f:
        T      = float(np.asarray(f["boundary/temperature"]).ravel()[0])
        ops    = json.loads(f.attrs.get("operators", "[]"))
        z_dyn  = float(f.attrs.get("z_dyn", 1.0) or 1.0)
        theta  = float(f.attrs.get("theta", 0.0) or 0.0)
        d      = int(f.attrs.get("d", 3))
        family = str(f.attrs.get("family", "unknown"))
        root_attrs    = dict(f.attrs)
        boundary_attrs = dict(f["boundary"].attrs)
        groups_to_copy = [k for k in f.keys() if k != "boundary"]

    delta_mean = float(np.mean([op["Delta"] for op in ops])) if ops else 3.0

    poles = estimate_qnm_poles(family, T, z_dyn, theta, d, delta_mean)

    omega_dom, _ = get_normalization_scales(poles)
    omega_grid   = build_omega_grid_dimless(poles, n_omega, omega_dom)
    GR_real, GR_imag = poles_to_gr(omega_grid, poles, omega_dom)
    x_grid = build_x_grid(n_x)
    G2     = poles_to_g2(x_grid, poles, omega_dom)

    dst.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(src, "r") as fsrc, h5py.File(dst, "w") as fdst:
        for k, v in root_attrs.items():
            fdst.attrs[k] = v

        for grp in groups_to_copy:
            fsrc.copy(grp, fdst)

        b = fdst.create_group("boundary")
        b.create_dataset("omega_grid",  data=omega_grid)
        b.create_dataset("k_grid",      data=np.array([0.0]))
        b.create_dataset("G_R_real",    data=GR_real)
        b.create_dataset("G_R_imag",    data=GR_imag)
        b.create_dataset("x_grid",      data=x_grid)
        b.create_dataset("G2_ringdown", data=G2)

        for k, v in boundary_attrs.items():
            b.attrs[k] = v
        b.attrs["operators"]       = "[]"
        b.attrs["temperature"]     = 0.0
        b.attrs["T"]               = 0.0
        b.attrs["embedding_space"] = "dimensionless_omega_dom"
        b.attrs["omega_dom_rads"]  = float(omega_dom)
        b.attrs["n_poles"]         = len(poles)
        b.attrs["bridge_script"]   = "00_sandbox_to_poles_bridge.py"

    Q = poles[0].freq_hz / (poles[0].damping_1_over_s / (2 * math.pi))
    return {"family": family, "Q": Q, "n_poles": len(poles)}


# ── High-Q synthetic geometries ───────────────────────────────────────────────

HIGH_Q_SPECS = {
    # family, Q_target, f0_hz, n_samples
    "ads":          [(12.0, 0.5), (18.0, 0.5), (22.0, 0.5)],
    "lifshitz":     [(10.0, 0.5), (15.0, 0.5), (20.0, 0.5)],
    "hyperscaling": [(11.0, 0.5), (16.0, 0.5), (21.0, 0.5)],
    "deformed":     [(8.0,  0.5), (12.0, 0.5), (16.0, 0.5)],
}


def generate_high_q_h5(out_dir: Path, family: str, Q: float, tag: str,
                        n_omega: int, n_x: int):
    """Genera un HDF5 sintético con Q-factor especificado."""
    f0 = 1.0  # freq normalizada arbitraria (1.0 rad/(2π))
    gamma0 = f0 * (2 * math.pi) / Q  # γ = ω/Q
    poles = [
        Pole(freq_hz=f0,          damping_1_over_s=gamma0,        amp_abs=1.0),
        Pole(freq_hz=f0 * 1.48,   damping_1_over_s=gamma0 * 2.88, amp_abs=0.35),
    ]
    omega_dom, _ = get_normalization_scales(poles)
    omega_grid   = build_omega_grid_dimless(poles, n_omega, omega_dom)
    GR_real, GR_imag = poles_to_gr(omega_grid, poles, omega_dom)
    x_grid = build_x_grid(n_x)
    G2     = poles_to_g2(x_grid, poles, omega_dom)

    name = f"highQ_{family}_{tag}"
    dst  = out_dir / f"{name}.h5"
    with h5py.File(dst, "w") as f:
        f.attrs["name"]     = name
        f.attrs["family"]   = family
        f.attrs["category"] = "known"
        f.attrs["d"]        = 4
        f.attrs["z_dyn"]    = 1.0
        f.attrs["theta"]    = 0.0
        f.attrs["z_h"]      = 1.0
        f.attrs["operators"] = "[]"

        b = f.create_group("boundary")
        b.create_dataset("omega_grid",  data=omega_grid)
        b.create_dataset("k_grid",      data=np.array([0.0]))
        b.create_dataset("G_R_real",    data=GR_real)
        b.create_dataset("G_R_imag",    data=GR_imag)
        b.create_dataset("x_grid",      data=x_grid)
        b.create_dataset("G2_ringdown", data=G2)
        b.attrs["d"]               = 4
        b.attrs["temperature"]     = 0.0
        b.attrs["T"]               = 0.0
        b.attrs["operators"]       = "[]"
        b.attrs["family"]          = family
        b.attrs["embedding_space"] = "dimensionless_omega_dom"
        b.attrs["omega_dom_rads"]  = float(omega_dom)
        b.attrs["Q_target"]        = float(Q)
        b.attrs["synthetic_highQ"] = True

        # bulk_truth dummy (requerido por 02_emergent_geometry_engine loader)
        z_grid = np.linspace(0.01, 5.0, 100)
        bt = f.create_group("bulk_truth")
        bt.create_dataset("z_grid",        data=z_grid)
        bt.create_dataset("A_truth",        data=np.log(z_grid))        # AdS placeholder
        bt.create_dataset("f_truth",        data=1.0 - (z_grid/3.0)**3) # placeholder
        bt.create_dataset("R_truth",        data=np.full_like(z_grid, -6.0))
        bt.create_dataset("G_trace_truth",  data=np.zeros_like(z_grid))
        bt.attrs["family"] = family
        bt.attrs["d"]      = 4
        bt.attrs["z_h"]    = 1.0
        bt.attrs["z_dyn"]  = 1.0
        bt.attrs["theta"]  = 0.0

    return name, Q


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Genera sandbox v3: embeddings polo-derivados con QNMs analíticos."
    )
    ap.add_argument("--src-dir",  required=True)
    ap.add_argument("--out-dir",  required=True)
    ap.add_argument("--n-omega",  type=int, default=256)
    ap.add_argument("--n-x",      type=int, default=256)
    ap.add_argument("--no-highq", action="store_true",
                    help="Omitir geometrías high-Q sintéticas")
    args = ap.parse_args()

    src_dir = Path(args.src_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    h5_files = sorted(src_dir.glob("*.h5"))
    print(f"[bridge] Convirtiendo {len(h5_files)} ficheros sandbox → polo-derivado")

    manifest_entries = []
    q_by_family = {}

    for h5f in h5_files:
        dst = out_dir / h5f.name
        try:
            meta = convert_h5(h5f, dst, args.n_omega, args.n_x)
            with h5py.File(h5f, "r") as fck:
                manifest_entries.append({
                    "name":     str(fck.attrs.get("name", h5f.stem)),
                    "family":   meta["family"],
                    "category": str(fck.attrs.get("category", "unknown")),
                    "d":        int(fck.attrs.get("d", 3)),
                    "file":     h5f.name,
                    "Q":        round(meta["Q"], 2),
                })
            q_by_family.setdefault(meta["family"], []).append(meta["Q"])
        except Exception as e:
            print(f"  [ERR] {h5f.name}: {e}")

    # Resumen de Q por familia
    print("\nQ-factor por familia (training):")
    for fam, qs in sorted(q_by_family.items()):
        print(f"  {fam:15s}  Q_mean={np.mean(qs):.1f}  range=[{min(qs):.1f}, {max(qs):.1f}]")

    # High-Q sintéticas
    if not args.no_highq:
        print("\nGenerando geometrías high-Q sintéticas (rango Kerr Q=8-22)...")
        for fam, specs in HIGH_Q_SPECS.items():
            for i, (Q, _) in enumerate(specs):
                name, q = generate_high_q_h5(out_dir, fam, Q, f"hq{i:02d}", args.n_omega, args.n_x)
                manifest_entries.append({
                    "name": name, "family": fam, "category": "known", "d": 4,
                    "file": f"{name}.h5", "Q": round(q, 1), "synthetic": True,
                })
                print(f"  {name}  Q={q:.1f}")

    manifest = {"geometries": manifest_entries, "version": "v3-poles-analytic"}
    (out_dir / "geometries_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\n[bridge] done → {out_dir}  ({len(manifest_entries)} ficheros totales)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
