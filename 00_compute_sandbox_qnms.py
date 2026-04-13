#!/usr/bin/env python3
"""
00_compute_sandbox_qnms.py — CUERDAS-MALDACENA

Calcula numéricamente los modos quasinormales (QNMs) de cada geometría
sandbox usando el **método de shooting**.

Para cada HDF5 en sandbox_v1/01_generate_sandbox_geometries/:
  1. Carga A(z), f(z), z_h, d desde bulk_truth
  2. Plantea la ecuación de perturbación escalar:
       ∂_z[e^{(d+1)A} f φ'] + ω² e^{(d-1)A}/f φ = 0
  3. Impone condición entrante en el horizonte:
       φ ~ (z_h - z)^{-iω/|f'_h|}
  4. Integra numéricamente hacia el boundary (z → 0)
  5. Busca ω complejo tal que φ(z_min) → 0 (condición QNM)

Guarda los QNMs en:
  - runs/sandbox_v1/qnm_numerical.json  (resumen de todos)
  - Grupo 'qnm_numerical' en cada HDF5 (ω_real, ω_imag por modo n)

Uso:
    python malda/00_compute_sandbox_qnms.py [--sandbox-dir RUNS/SANDBOX_V1]
                                             [--n-modes 3]
                                             [--eps-horizon 1e-4]
                                             [--output-json OUTPUT.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional, Tuple

import h5py
import numpy as np
from scipy.integrate import solve_ivp
from scipy.interpolate import CubicSpline
from scipy.optimize import fsolve


# ─────────────────────────────────────────────────────────────────────────────
# Geometría: |f'(z_h)| analítico por familia
# ─────────────────────────────────────────────────────────────────────────────

def fp_horizon_analytic(
    family: str,
    z_h: float,
    d: int,
    z_dyn: float,
    theta: float,
    # Tier A extra params (keyword-only, con defaults para compatibilidad)
    charge_Q: float = 0.0,
    lambda_gb: float = 0.0,
    m_g: float = 0.0,
    mg_c1: float = 1.0,
    alpha_axion: float = 0.0,
) -> float:
    """
    |f'(z_h)| analítico para cada familia.
    Derivado directamente de la expresión de f(z) en 01_generate_sandbox_geometries.py.

    Cada rama tiene su propia derivación desde f(z) analítico — no hay fallback
    silencioso al else para familias reconocidas.

    Tier Canonical:
      ads:            f = 1 - (z/z_h)^d
      lifshitz:       f = 1 - (z/z_h)^{d+z_dyn-1}
      hyperscaling:   f = 1 - (z/z_h)^{max(1,d-theta)}
      dpbrane:        f = 1 - (z/z_h)^{max(1,2*z_dyn)}
      deformed/unknown: f = 1 - (z/z_h)^4 (toy)

    Tier A:
      rn_ads:         f = 1 - (1+q²)(z/z_h)^d + q²(z/z_h)^{2(d-1)}
      gauss_bonnet:   f = 1 - (z/z_h)^{d+lambda_gb}
      massive_gravity: f = 1 - (1-mg2·z_h²)(z/z_h)^d - mg2·z²  (mg2=m_g²·mg_c1)
      linear_axion:   f = 1 - (1+a2·z_h²/d)(z/z_h)^d + a2·z²/d  (a2=alpha²)
      charged_hvlif:  f = 1 - (1+q²)(z/z_h)^{eff_d} + q²(z/z_h)^{2(eff_d-1)}
    """
    # ── Tier Canonical ────────────────────────────────────────────────────────
    if family == "ads":
        exponent = float(d)
        return exponent / z_h

    elif family == "lifshitz":
        exponent = float(d) + z_dyn - 1.0
        return exponent / z_h

    elif family == "hyperscaling":
        exponent = max(1.0, float(d) - theta)
        return exponent / z_h

    elif family == "dpbrane":
        exponent = max(1.0, 2.0 * z_dyn)
        return exponent / z_h

    elif family in ("deformed", "unknown"):
        # f = 1 - (z/z_h)^4  (toy para familias deformadas/desconocidas)
        return 4.0 / z_h

    # ── Tier A ────────────────────────────────────────────────────────────────

    elif family == "rn_ads":
        # f(z) = 1 - (1+q²)(z/z_h)^d + q²(z/z_h)^{2(d-1)}
        # f'(z_h) = [-(1+q²)·d + q²·2(d-1)] / z_h = (-d + q²(d-2)) / z_h
        q = charge_Q
        df = -float(d) + q * q * (float(d) - 2.0)
        return abs(df) / z_h

    elif family == "gauss_bonnet":
        # f(z) = 1 - (z/z_h)^{eff_exp},  eff_exp = max(1, d + lambda_gb)
        # f'(z_h) = -eff_exp/z_h
        eff_exp = max(1.0, float(d) + lambda_gb)
        return eff_exp / z_h

    elif family == "massive_gravity":
        # f(z) = 1 - (1-mg2·z_h²)(z/z_h)^d - mg2·z²,  mg2 = m_g²·mg_c1
        # f'(z) = -d(1-mg2·z_h²)·z^{d-1}/z_h^d - 2·mg2·z
        # f'(z_h) = [-d(1-mg2·z_h²) - 2·mg2·z_h²] / z_h
        #          = [-d + mg2·z_h²(d-2)] / z_h
        mg2 = m_g * m_g * mg_c1
        df = (-float(d) + mg2 * z_h * z_h * (float(d) - 2.0)) / z_h
        return abs(df)

    elif family == "linear_axion":
        # f(z) = 1 - (1+a2·z_h²/d)(z/z_h)^d + a2·z²/d,  a2 = alpha_axion²
        # f'(z_h) = [-d - a2·z_h² + 2·a2·z_h²/d] / z_h
        #          = [-d + a2·z_h²(2/d - 1)] / z_h
        #          = [-d - a2·z_h²(d-2)/d] / z_h
        a2 = alpha_axion * alpha_axion
        df = (-float(d) - a2 * z_h * z_h * (float(d) - 2.0) / float(d)) / z_h
        return abs(df)

    elif family == "charged_hvlif":
        # Como rn_ads pero con eff_d = max(1, d-theta)
        eff_d = max(1.0, float(d) - theta)
        q = charge_Q
        df = -eff_d + q * q * (eff_d - 2.0)
        return abs(df) / z_h

    else:
        # Fallback genérico solo para familias no registradas (e.g. test nuevas)
        return 4.0 / z_h


def fp_horizon_effective(
    family: str,
    z_h: float,
    d: int,
    z_dyn: float,
    theta: float,
    A_spline: CubicSpline,
    # Tier A extra params (keyword-only)
    charge_Q: float = 0.0,
    lambda_gb: float = 0.0,
    m_g: float = 0.0,
    mg_c1: float = 1.0,
    alpha_axion: float = 0.0,
) -> float:
    """
    Denominador correcto para el exponente α = -iω / fp_eff en la BC entrante.

    Del análisis de la ecuación near-horizon en gauge domain-wall
        ds² = e^{2A}(-f dt² + dx²) + dz²/f
    se obtiene que la exponente del modo entrante es:
        α = -iω / (e^{A(z_h)} × |f'(z_h)|)
    donde el factor e^{A(z_h)} proviene de la ecuación de Euler-Cauchy
    que aparece al expandir cerca del horizonte.

    Retorna e^{A(z_h)} × |f'(z_h)|.
    """
    fp_raw = fp_horizon_analytic(
        family, z_h, d, z_dyn, theta,
        charge_Q=charge_Q, lambda_gb=lambda_gb,
        m_g=m_g, mg_c1=mg_c1, alpha_axion=alpha_axion,
    )
    # Evalúa A ligeramente antes del horizonte para evitar f=0
    A_h = float(A_spline(z_h * (1.0 - 1e-5)))
    return float(np.exp(A_h)) * fp_raw


# ─────────────────────────────────────────────────────────────────────────────
# Integrador ODE
# ─────────────────────────────────────────────────────────────────────────────

def make_ode(A_spline: CubicSpline, f_spline: CubicSpline,
             Ap_spline: CubicSpline, fp_spline: CubicSpline,
             d: int, omega: complex):
    """
    Retorna rhs(z, u) para el sistema:
        u = [φ, φ']
        dφ/dz  = φ'
        dφ'/dz = -[(d+1)A'(z) + f'(z)/f(z)] φ' - [ω² e^{-2A(z)} / f(z)²] φ

    Trabaja con arrays complejos.
    """
    om2 = omega ** 2

    def rhs(z: float, u: np.ndarray) -> np.ndarray:
        phi, dphi = u[0], u[1]
        Az  = float(A_spline(z))
        fz  = float(f_spline(z))
        Apz = float(Ap_spline(z))
        fpz = float(fp_spline(z))

        # Clip para evitar división por cero lejos del horizonte
        fz = max(fz, 1e-14)

        coeff_dphi = -((d + 1) * Apz + fpz / fz)
        coeff_phi  = -om2 * np.exp(-2.0 * Az) / (fz ** 2)

        return np.array([dphi, coeff_dphi * dphi + coeff_phi * phi],
                        dtype=complex)

    return rhs


# ─────────────────────────────────────────────────────────────────────────────
# Condición inicial en el horizonte (BC entrante)
# ─────────────────────────────────────────────────────────────────────────────

def horizon_ic(omega: complex, fp_h: float, eps: float) -> Tuple[complex, complex]:
    """
    Condición inicial para φ a z_start = z_h - eps.

    Solución entrante: φ ~ (z_h-z)^α, α = -iω/|f'_h|
    Normalizado: φ(z_start) = 1
    dφ/dz(z_start) = -α / eps
    """
    alpha = -1j * omega / fp_h
    phi0  = 1.0 + 0j
    dphi0 = -alpha / eps
    return phi0, dphi0


# ─────────────────────────────────────────────────────────────────────────────
# Función de shooting: integra y devuelve φ(z_min)
# ─────────────────────────────────────────────────────────────────────────────

def shoot(omega: complex,
          A_spline: CubicSpline, f_spline: CubicSpline,
          Ap_spline: CubicSpline, fp_spline: CubicSpline,
          d: int, fp_h: float,
          z_start: float, z_min: float,
          eps_horizon: float) -> complex:
    """
    Integra desde z_start (cerca del horizonte) hasta z_min (boundary).
    Retorna φ(z_min) — debe ser ~ 0 en un QNM.
    """
    phi0, dphi0 = horizon_ic(omega, fp_h, eps_horizon)
    u0 = np.array([phi0, dphi0], dtype=complex)

    rhs = make_ode(A_spline, f_spline, Ap_spline, fp_spline, d, omega)

    # Integrar de z_start → z_min (orden decreciente de z)
    sol = solve_ivp(
        rhs,
        [z_start, z_min],
        u0,
        method="RK45",
        rtol=1e-9,
        atol=1e-12,
        dense_output=False,
        max_step=(z_start - z_min) / 200.0,
    )

    if not sol.success:
        return np.nan + 1j * np.nan

    return complex(sol.y[0, -1])


# ─────────────────────────────────────────────────────────────────────────────
# Búsqueda de un QNM a partir de un guess inicial
# ─────────────────────────────────────────────────────────────────────────────

def find_qnm(omega_guess: complex,
             A_spline: CubicSpline, f_spline: CubicSpline,
             Ap_spline: CubicSpline, fp_spline: CubicSpline,
             d: int, fp_h: float,
             z_start: float, z_min: float,
             eps_horizon: float,
             ftol: float = 1e-7) -> Optional[complex]:
    """
    Usa fsolve para encontrar el QNM más cercano a omega_guess.
    Retorna ω complejo si converge, None si no.
    """

    def objective(x):
        om = x[0] + 1j * x[1]
        val = shoot(om, A_spline, f_spline, Ap_spline, fp_spline,
                    d, fp_h, z_start, z_min, eps_horizon)
        if np.isnan(val.real) or np.isnan(val.imag):
            return [1e6, 1e6]
        return [val.real, val.imag]

    x0 = [omega_guess.real, omega_guess.imag]
    try:
        sol, info, ier, _ = fsolve(objective, x0, full_output=True)
    except Exception:
        return None

    if ier != 1:
        return None

    # Verificar que realmente es un cero
    residual = np.linalg.norm(info["fvec"])
    if residual > ftol:
        return None

    omega_sol = sol[0] + 1j * sol[1]
    # QNMs tienen Im(ω) < 0 (modos que decaen)
    if omega_sol.imag > 0.1:
        return None

    return omega_sol


# ─────────────────────────────────────────────────────────────────────────────
# Guesses iniciales
# ─────────────────────────────────────────────────────────────────────────────

def initial_guesses(T: float, family: str, z_dyn: float, theta: float,
                    d: int, n_mode: int) -> List[complex]:
    """
    Genera guesses iniciales para el modo n_mode.

    Los QNMs del gauge domain-wall están en torno a:
        ω_R ~ (2n+3) × 4πT  (escala empírica)
        γ   ~ (0.5..1) × 4πT
    Por eso usamos 4πT = d/z_h como escala base (no 2πT).
    """
    scale = 4.0 * np.pi * T   # escala base = 4πT
    if scale < 1e-8:
        scale = 1.0

    guesses: List[complex] = []

    # Empíricamente, en gauge domain-wall el modo n-ésimo está en torno a:
    #   ω_R ≈ (3 + 4×n) × 4πT,  γ ≈ (0.5..1) × 4πT
    # para AdS. Otras familias tendrán escala diferente pero similar estructura.
    base_re = 3.0 + 4.0 * n_mode   # en unidades de scale = 4πT

    for re_shift in [base_re, base_re-1, base_re+1, base_re-2, base_re+2,
                     base_re+0.5, base_re-0.5]:
        for im_fac in [-0.5, -0.4, -0.6, -0.7, -0.3, -1.0]:
            guesses.append(re_shift * scale + 1j * im_fac * scale)

    return guesses


# ─────────────────────────────────────────────────────────────────────────────
# Procesamiento de un HDF5
# ─────────────────────────────────────────────────────────────────────────────

def process_geometry(h5path: Path, n_modes: int,
                     eps_horizon: float) -> Optional[dict]:
    """
    Carga la geometría, corre el shooting y retorna un dict con los QNMs.
    """
    with h5py.File(h5path, "r") as h:
        z_grid = h["bulk_truth/z_grid"][:]
        A_arr  = h["bulk_truth/A_truth"][:]
        f_arr  = h["bulk_truth/f_truth"][:]
        z_h    = float(h.attrs.get("z_h", 0.0))
        d      = int(h.attrs.get("d", 3))
        z_dyn  = float(h.attrs.get("z_dyn", 1.0))
        theta  = float(h.attrs.get("theta", 0.0))
        family = str(h.attrs.get("family", "unknown"))
        name   = str(h.attrs.get("name", h5path.stem))
        T      = float(h["boundary/temperature"][0])
        # Tier A: leer attrs canónicos extra (con defaults para H5 legacy)
        charge_Q    = float(h.attrs.get("charge_Q", 0.0))
        lambda_gb   = float(h.attrs.get("lambda_gb", 0.0))
        m_g         = float(h.attrs.get("m_g", 0.0))
        mg_c1       = float(h.attrs.get("mg_c1", 1.0))
        alpha_axion = float(h.attrs.get("alpha_axion", 0.0))

    if z_h <= 0:
        print(f"  [SKIP] {name}: z_h={z_h} (sin horizonte)")
        return None

    # ── Recortar a z ∈ [z_min, z_h] ──────────────────────────────────────
    mask   = (z_grid > 0) & (z_grid < z_h * 1.001)
    z_phys = z_grid[mask]
    A_phys = A_arr[mask]
    f_phys = f_arr[mask]

    if len(z_phys) < 10:
        print(f"  [SKIP] {name}: muy pocos puntos en [0, z_h]")
        return None

    # Asegurar que f > 0 en z_phys (puede haber pequeños negativos por el clip)
    f_phys = np.clip(f_phys, 0.0, None)

    # ── Splines ──────────────────────────────────────────────────────────
    A_sp  = CubicSpline(z_phys, A_phys)
    f_sp  = CubicSpline(z_phys, f_phys)
    Ap_sp = A_sp.derivative()
    fp_sp = f_sp.derivative()

    # ── Denominador correcto para α = -iω/fp_h ───────────────────────────
    # fp_h = e^{A(z_h)} × |f'(z_h)|  (ver fp_horizon_effective)
    fp_h = fp_horizon_effective(
        family, z_h, d, z_dyn, theta, A_sp,
        charge_Q=charge_Q, lambda_gb=lambda_gb,
        m_g=m_g, mg_c1=mg_c1, alpha_axion=alpha_axion,
    )

    z_min   = float(z_phys[0])          # boundary (z ~ 0.01)
    z_start = z_h - eps_horizon * z_h   # cerca del horizonte

    if z_start <= z_min:
        print(f"  [SKIP] {name}: z_start={z_start:.4f} <= z_min={z_min:.4f}")
        return None

    # ── Búsqueda de QNMs ─────────────────────────────────────────────────
    qnms: List[complex] = []

    for n in range(n_modes):
        guesses = initial_guesses(T, family, z_dyn, theta, d, n)
        found: Optional[complex] = None

        for g in guesses:
            om = find_qnm(g, A_sp, f_sp, Ap_sp, fp_sp,
                          d, fp_h, z_start, z_min, eps_horizon * z_h)
            if om is not None:
                # Evitar duplicados (mismo modo que ya encontramos)
                is_dup = any(abs(om - prev) < 0.05 * abs(prev) for prev in qnms)
                if not is_dup:
                    found = om
                    break

        if found is None:
            print(f"  [WARN] {name}: no convergió modo n={n}")
            qnms.append(np.nan + 1j * np.nan)
        else:
            qnms.append(found)

    # ── Ratios espectrales ────────────────────────────────────────────────
    om0 = qnms[0] if qnms else None
    om1 = qnms[1] if len(qnms) > 1 else None

    freq_ratio = np.nan
    damp_ratio = np.nan
    if (om0 is not None and not np.isnan(om0.real)
            and om1 is not None and not np.isnan(om1.real)
            and abs(om0.real) > 1e-8 and abs(om0.imag) > 1e-8):
        freq_ratio = float(om1.real / om0.real)
        damp_ratio = float(om1.imag / om0.imag)   # ambos negativos → ratio > 0

    result = {
        "name":       name,
        "family":     family,
        "d":          d,
        "z_h":        z_h,
        "z_dyn":      z_dyn,
        "theta":      theta,
        "T":          T,
        "fp_h_eff":   fp_h,   # e^{A_h} × |f'_h| = denominador de alpha
        "qnms_re":    [float(q.real) if not np.isnan(q.real) else None for q in qnms],
        "qnms_im":    [float(q.imag) if not np.isnan(q.imag) else None for q in qnms],
        "freq_ratio": freq_ratio,   # f1/f0
        "damp_ratio": damp_ratio,   # γ1/γ0
    }

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Escritura de QNMs en HDF5
# ─────────────────────────────────────────────────────────────────────────────

def write_qnms_to_h5(h5path: Path, result: dict) -> None:
    """
    Escribe grupo 'qnm_numerical' en el HDF5 con los QNMs encontrados.
    """
    qnms_re = result["qnms_re"]
    qnms_im = result["qnms_im"]

    omega_re = np.array([x if x is not None else np.nan for x in qnms_re])
    omega_im = np.array([x if x is not None else np.nan for x in qnms_im])

    with h5py.File(h5path, "a") as h:
        if "qnm_numerical" in h:
            del h["qnm_numerical"]
        grp = h.create_group("qnm_numerical")
        grp.create_dataset("omega_re", data=omega_re)
        grp.create_dataset("omega_im", data=omega_im)
        grp.attrs["fp_h_eff"]   = result["fp_h_eff"]
        grp.attrs["freq_ratio"] = result["freq_ratio"]
        grp.attrs["damp_ratio"] = result["damp_ratio"]
        grp.attrs["method"]     = "shooting_rk45"


# ─────────────────────────────────────────────────────────────────────────────
# Summary por familia
# ─────────────────────────────────────────────────────────────────────────────

def print_family_summary(results: List[dict]) -> None:
    from collections import defaultdict
    import statistics

    by_family: dict = defaultdict(list)
    for r in results:
        if r is None:
            continue
        freq_r = r["freq_ratio"]
        damp_r = r["damp_ratio"]
        if not np.isnan(freq_r) and not np.isnan(damp_r):
            by_family[r["family"]].append((freq_r, damp_r))

    print("\n" + "=" * 62)
    print(f"{'Familia':<16} {'N':>3}  {'f1/f0':>10}  {'γ1/γ0':>10}  {'Q0':>8}")
    print("=" * 62)

    for fam, vals in sorted(by_family.items()):
        f_ratios = [v[0] for v in vals]
        d_ratios = [v[1] for v in vals]
        f_mean = statistics.mean(f_ratios)
        d_mean = statistics.mean(d_ratios)

        # Q del modo fundamental de los resultados que lo tienen
        q_vals = []
        for r in results:
            if r is None or r["family"] != fam:
                continue
            qr = r["qnms_re"]
            qi = r["qnms_im"]
            if qr and qi and qr[0] is not None and qi[0] is not None:
                re, im = qr[0], qi[0]
                if abs(im) > 1e-8:
                    q_vals.append(abs(re / (2 * im)))
        q_mean = statistics.mean(q_vals) if q_vals else float("nan")

        print(f"{fam:<16} {len(vals):>3}  {f_mean:>10.3f}  {d_mean:>10.3f}  {q_mean:>8.2f}")

    print("=" * 62)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sandbox-dir",
                   default="runs/sandbox_v1/01_generate_sandbox_geometries",
                   help="Directorio con los HDF5 de sandbox (default: %(default)s)")
    p.add_argument("--n-modes", type=int, default=3,
                   help="Número de modos QNM a buscar por geometría (default: %(default)s)")
    p.add_argument("--eps-horizon", type=float, default=1e-3,
                   help="ε como fracción de z_h para el punto de inicio cerca del horizonte")
    p.add_argument("--output-json",
                   default="runs/sandbox_v1/qnm_numerical.json",
                   help="Ruta del JSON de salida")
    p.add_argument("--no-write-h5", action="store_true",
                   help="No escribir resultados en los HDF5 (solo JSON)")
    p.add_argument("--max-files", type=int, default=0,
                   help="Limitar a los primeros N archivos (0 = todos)")
    return p.parse_args()


def main():
    args = parse_args()

    sandbox_dir = Path(args.sandbox_dir)
    if not sandbox_dir.exists():
        print(f"[ERROR] Directorio no encontrado: {sandbox_dir}", file=sys.stderr)
        sys.exit(1)

    h5_files = sorted(sandbox_dir.glob("*.h5"))
    if not h5_files:
        print(f"[ERROR] No hay archivos .h5 en {sandbox_dir}", file=sys.stderr)
        sys.exit(1)

    if args.max_files > 0:
        h5_files = h5_files[: args.max_files]

    print(f"Procesando {len(h5_files)} geometrías  "
          f"(n_modes={args.n_modes}, eps={args.eps_horizon})\n")

    results = []
    for i, h5p in enumerate(h5_files):
        family_hint = h5p.stem.split("_")[0]
        print(f"[{i+1:03d}/{len(h5_files)}] {h5p.name[:55]:<55}", end="  ", flush=True)
        r = process_geometry(h5p, args.n_modes, args.eps_horizon)
        if r is None:
            print("SKIP")
            results.append(None)
            continue

        # Formatear salida en línea
        modes_str = "  ".join(
            f"ω{n}=({r['qnms_re'][n]:.2f}{r['qnms_im'][n]:+.2f}i)"
            if (r["qnms_re"][n] is not None and not np.isnan(r["qnms_re"][n]))
            else f"ω{n}=NaN"
            for n in range(len(r["qnms_re"]))
        )
        ratio_str = (f"  f1/f0={r['freq_ratio']:.3f}  γ1/γ0={r['damp_ratio']:.3f}"
                     if not np.isnan(r["freq_ratio"]) else "")
        print(f"{modes_str}{ratio_str}")

        if not args.no_write_h5:
            write_qnms_to_h5(h5p, r)

        results.append(r)

    # ── JSON de salida ────────────────────────────────────────────────────
    out_json = Path(args.output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    with open(out_json, "w") as fp:
        json.dump([r for r in results if r is not None], fp, indent=2)
    print(f"\nResultados guardados en: {out_json}")

    # ── Resumen por familia ───────────────────────────────────────────────
    print_family_summary([r for r in results if r is not None])


if __name__ == "__main__":
    main()
