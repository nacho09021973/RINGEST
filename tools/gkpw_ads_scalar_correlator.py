#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import h5py
import numpy as np
from scipy.integrate import solve_ivp
from scipy.interpolate import CubicSpline

try:
    from tools.validate_agmoo_ads import validate_ads_geometry
except ImportError:  # pragma: no cover - script execution fallback
    try:
        from validate_agmoo_ads import validate_ads_geometry  # type: ignore
    except ImportError:  # pragma: no cover - optional contract fallback
        validate_ads_geometry = None  # type: ignore

CORRELATOR_TYPE = "GKPW_SOURCE_RESPONSE_NUMERICAL"
SOLVER_VERSION = "gkpw_ads_scalar_correlator_v1"
GATE6_REQUIRED_FIELDS = (
    "bulk_field_name",
    "operator_name",
    "m2L2",
    "Delta",
    "bf_bound_pass",
    "uv_source_declared",
    "ir_bc_declared",
    "correlator_type",
)


class GKPWAdsError(RuntimeError):
    pass


@dataclass(frozen=True)
class GKPWConfig:
    m2L2: float = 0.0
    operator_name: str = "O_phi"
    bulk_field_name: str = "phi"
    omega_min: float = 0.2
    omega_max: float = 6.0
    n_omega: int = 32
    k_min: float = 0.0
    k_max: float = 2.0
    n_k: int = 8
    eps_horizon: float = 1e-4
    uv_fit_points: int = 10
    rtol: float = 1e-8
    atol: float = 1e-10


@dataclass(frozen=True)
class AdsGeometry:
    name: str
    family: str
    d: int
    z_h: Optional[float]
    z: np.ndarray
    A: np.ndarray
    f: np.ndarray


def check_bf_bound(m2L2: float, d: int) -> bool:
    return float(m2L2) >= -((float(d) / 2.0) ** 2)


def validate_gate6_metadata(metadata: Dict[str, Any]) -> None:
    missing = [key for key in GATE6_REQUIRED_FIELDS if metadata.get(key) is None]
    empty = [
        key for key in ("bulk_field_name", "operator_name", "correlator_type")
        if key in metadata and str(metadata.get(key, "")).strip() == ""
    ]
    if missing or empty:
        fields = sorted(set(missing + empty))
        raise GKPWAdsError(f"missing required Gate 6 metadata fields: {fields}")
    if metadata.get("correlator_type") in {"TOY_PHENOMENOLOGICAL", "GEODESIC_APPROXIMATION"}:
        raise GKPWAdsError(
            f"invalid GKPW correlator_type for strong rail: {metadata.get('correlator_type')}"
        )


def gate6_complete(metadata: Dict[str, Any]) -> bool:
    try:
        validate_gate6_metadata(metadata)
    except GKPWAdsError:
        return False
    return True


def delta_from_m2L2(m2L2: float, d: int) -> Tuple[float, float, float]:
    disc = float(d) ** 2 + 4.0 * float(m2L2)
    if disc < 0.0:
        raise GKPWAdsError(
            f"BF bound violated for d={d}: m2L2={m2L2} < {-((d / 2.0) ** 2)}"
        )
    nu = 0.5 * np.sqrt(disc)
    delta_plus = 0.5 * float(d) + nu
    delta_minus = 0.5 * float(d) - nu
    if abs(delta_plus - delta_minus) < 1e-10:
        raise GKPWAdsError("BF saturation with logarithmic UV branch is not implemented")
    return float(delta_plus), float(delta_minus), float(nu)


def _read_dataset(fh: h5py.File, candidates: Tuple[str, ...]) -> np.ndarray:
    for name in candidates:
        if name in fh:
            return np.asarray(fh[name][...], dtype=np.float64)
    raise GKPWAdsError(f"missing required geometry dataset; tried {list(candidates)}")


def load_ads_geometry(h5_path: Path) -> AdsGeometry:
    h5_path = Path(h5_path)
    with h5py.File(h5_path, "r") as fh:
        family = str(fh.attrs.get("family", "unknown"))
        if family != "ads":
            raise GKPWAdsError(f"GKPW ads scalar rail requires family='ads', got {family!r}")
        name = str(fh.attrs.get("system_name", fh.attrs.get("name", h5_path.stem)))
        d = int(fh.attrs.get("d", 3))
        z_h_raw = fh.attrs.get("z_h", 0.0)
        z_h = float(z_h_raw) if z_h_raw is not None and float(z_h_raw) > 0.0 else None
        z = _read_dataset(fh, ("z_grid", "bulk_truth/z_grid"))
        A = _read_dataset(fh, ("A_of_z", "bulk_truth/A_truth"))
        f = _read_dataset(fh, ("f_of_z", "bulk_truth/f_truth"))

    z = np.asarray(z, dtype=np.float64).reshape(-1)
    A = np.asarray(A, dtype=np.float64).reshape(-1)
    f = np.asarray(f, dtype=np.float64).reshape(-1)
    if not (z.size == A.size == f.size):
        raise GKPWAdsError(f"shape mismatch: z={z.shape}, A={A.shape}, f={f.shape}")
    if z.size < 20:
        raise GKPWAdsError(f"radial grid too coarse: {z.size} points")
    order = np.argsort(z)
    z, A, f = z[order], A[order], f[order]
    if np.any(np.diff(z) <= 0.0):
        raise GKPWAdsError("z grid must be strictly increasing after sorting")
    return AdsGeometry(name=name, family=family, d=d, z_h=z_h, z=z, A=A, f=f)


def _physical_domain(geo: AdsGeometry, eps_horizon: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray, bool]:
    has_horizon = geo.z_h is not None and geo.z_h > geo.z[0]
    if has_horizon:
        z_max = float(geo.z_h) * (1.0 - float(eps_horizon))
        mask = (geo.z > 0.0) & (geo.z <= z_max)
    else:
        mask = geo.z > 0.0
    z = geo.z[mask]
    A = geo.A[mask]
    f = geo.f[mask]
    if z.size < 20:
        raise GKPWAdsError("not enough radial points in physical integration domain")
    f = np.maximum(f, 1e-12)
    return z, A, f, bool(has_horizon)


def _rhs_factory(
    A_sp: CubicSpline,
    f_sp: CubicSpline,
    Ap_sp: CubicSpline,
    fp_sp: CubicSpline,
    d: int,
    m2L2: float,
    omega: float,
    k: float,
):
    omega_c = complex(omega)
    k2 = float(k) ** 2
    m2 = float(m2L2)

    def rhs(z_val: float, y: np.ndarray) -> np.ndarray:
        phi, dphi = y[0], y[1]
        A = float(A_sp(z_val))
        f = max(float(f_sp(z_val)), 1e-14)
        Ap = float(Ap_sp(z_val))
        fp = float(fp_sp(z_val))
        coeff_dphi = -((int(d) + 1) * Ap + fp / f)
        potential = (
            (omega_c ** 2) * np.exp(-2.0 * A) / (f ** 2)
            - k2 * np.exp(-2.0 * A) / f
            - m2 / f
        )
        return np.asarray([dphi, coeff_dphi * dphi - potential * phi], dtype=complex)

    return rhs


def _initial_conditions(
    geo: AdsGeometry,
    z: np.ndarray,
    A_sp: CubicSpline,
    f_sp: CubicSpline,
    fp_sp: CubicSpline,
    omega: float,
    has_horizon: bool,
) -> Tuple[complex, complex, str]:
    if has_horizon:
        z_start = float(z[-1])
        z_h = float(geo.z_h)
        eps = max(z_h - z_start, 1e-12)
        fp_raw = abs(float(fp_sp(z_start)))
        fp_eff = max(np.exp(float(A_sp(z_start))) * fp_raw, 1e-12)
        alpha = -1j * complex(omega) / fp_eff
        phi0 = 1.0 + 0.0j
        dphi0 = -alpha / eps
        return phi0, dphi0, "ingoing_horizon"
    return 1.0 + 0.0j, 0.0 + 0.0j, "regular_interior"


def _extract_source_response(
    z: np.ndarray,
    phi: np.ndarray,
    delta_minus: float,
    delta_plus: float,
    uv_fit_points: int,
) -> Tuple[complex, complex, float]:
    n_fit = min(max(int(uv_fit_points), 4), z.size)
    z_fit = np.asarray(z[:n_fit], dtype=np.float64)
    phi_fit = np.asarray(phi[:n_fit], dtype=complex)
    design = np.vstack([z_fit ** delta_minus, z_fit ** delta_plus]).T.astype(complex)
    coeffs, residuals, _, _ = np.linalg.lstsq(design, phi_fit, rcond=None)
    source = complex(coeffs[0])
    response = complex(coeffs[1])
    residual_norm = float(np.sqrt(np.sum(np.abs(residuals)))) if residuals.size else 0.0
    if abs(source) < 1e-14:
        raise GKPWAdsError("UV source coefficient is numerically zero; cannot form response/source")
    return source, response, residual_norm


def solve_frequency_point(
    geo: AdsGeometry,
    config: GKPWConfig,
    omega: float,
    k: float,
) -> Dict[str, Any]:
    delta_plus, delta_minus, nu = delta_from_m2L2(config.m2L2, geo.d)
    z, A, f, has_horizon = _physical_domain(geo, config.eps_horizon)
    A_sp = CubicSpline(z, A)
    f_sp = CubicSpline(z, f)
    Ap_sp = A_sp.derivative()
    fp_sp = f_sp.derivative()
    rhs = _rhs_factory(A_sp, f_sp, Ap_sp, fp_sp, geo.d, config.m2L2, omega, k)
    phi0, dphi0, ir_bc = _initial_conditions(geo, z, A_sp, f_sp, fp_sp, omega, has_horizon)
    y0 = np.asarray([phi0, dphi0], dtype=complex)
    sol = solve_ivp(
        rhs,
        (float(z[-1]), float(z[0])),
        y0,
        method="DOP853",
        rtol=float(config.rtol),
        atol=float(config.atol),
        max_step=max(float(z[-1] - z[0]) / 400.0, 1e-8),
    )
    if not sol.success:
        raise GKPWAdsError(f"ODE solve failed at omega={omega}, k={k}: {sol.message}")
    z_sol = sol.t[::-1]
    phi_sol = sol.y[0, ::-1]
    source, response, residual = _extract_source_response(
        z_sol,
        phi_sol,
        delta_minus,
        delta_plus,
        config.uv_fit_points,
    )
    green = (2.0 * nu) * response / source
    return {
        "G_R": complex(green),
        "source": source,
        "response": response,
        "uv_fit_residual_norm": residual,
        "ir_bc": ir_bc,
        "Delta": delta_plus,
        "Delta_minus": delta_minus,
        "nu": nu,
    }


def build_correlator_grid(geo: AdsGeometry, config: GKPWConfig) -> Dict[str, Any]:
    if not check_bf_bound(config.m2L2, geo.d):
        raise GKPWAdsError(
            f"BF bound violated for d={geo.d}: m2L2={config.m2L2} < {-((geo.d / 2.0) ** 2)}"
        )
    delta_plus, delta_minus, nu = delta_from_m2L2(config.m2L2, geo.d)
    omega_grid = np.linspace(config.omega_min, config.omega_max, int(config.n_omega), dtype=np.float64)
    k_grid = np.linspace(config.k_min, config.k_max, int(config.n_k), dtype=np.float64)
    gr = np.zeros((k_grid.size, omega_grid.size), dtype=np.complex128)
    source = np.zeros_like(gr)
    response = np.zeros_like(gr)
    residual = np.zeros(gr.shape, dtype=np.float64)
    ir_bc_declared = ""

    for ik, kval in enumerate(k_grid):
        for iw, oval in enumerate(omega_grid):
            point = solve_frequency_point(geo, config, float(oval), float(kval))
            gr[ik, iw] = point["G_R"]
            source[ik, iw] = point["source"]
            response[ik, iw] = point["response"]
            residual[ik, iw] = point["uv_fit_residual_norm"]
            ir_bc_declared = str(point["ir_bc"])

    classification = "ads_thermal" if geo.z_h is not None and geo.z_h > 0.0 else "ads_pure"
    metadata: Dict[str, Any] = {
        "solver_version": SOLVER_VERSION,
        "classification": classification,
        "ads_classification": classification,
        "correlator_type": CORRELATOR_TYPE,
        "bulk_field_name": config.bulk_field_name,
        "operator_name": config.operator_name,
        "m2L2": float(config.m2L2),
        "Delta": float(delta_plus),
        "Delta_minus": float(delta_minus),
        "nu": float(nu),
        "bf_bound_pass": True,
        "uv_source_declared": True,
        "ir_bc_declared": True,
        "ir_bc_type": ir_bc_declared,
        "source_response_extraction": "least_squares_uv_two_branch_fit",
        "normalization": "G_R=(2*nu)*response/source; contact terms not renormalized",
        "holographic_renormalization": "not_complete_contact_terms_not_subtracted",
        "rigor_note": (
            "Solves the linearized bulk scalar equation with declared UV source and IR "
            "condition, then extracts response/source numerically. It is not labeled as "
            "HOLOGRAPHIC_WITTEN_DIAGRAM because full holographic renormalization and "
            "contact-term subtraction are not implemented."
        ),
    }
    return {
        "omega_grid": omega_grid,
        "k_grid": k_grid,
        "G_R_real": gr.real.astype(np.float64),
        "G_R_imag": gr.imag.astype(np.float64),
        "source_real": source.real.astype(np.float64),
        "source_imag": source.imag.astype(np.float64),
        "response_real": response.real.astype(np.float64),
        "response_imag": response.imag.astype(np.float64),
        "uv_fit_residual_norm": residual,
        "metadata": metadata,
    }


def _json_default(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"not JSON serializable: {type(value).__name__}")


def config_hash(config: GKPWConfig, geometry_name: str) -> str:
    payload = {"config": asdict(config), "geometry_name": geometry_name, "solver_version": SOLVER_VERSION}
    raw = json.dumps(payload, sort_keys=True, default=_json_default).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def output_hash(result: Dict[str, Any]) -> str:
    h = hashlib.sha256()
    for key in ("omega_grid", "k_grid", "G_R_real", "G_R_imag"):
        arr = np.asarray(result[key], dtype=np.float64)
        h.update(key.encode("utf-8"))
        h.update(arr.tobytes(order="C"))
    return h.hexdigest()


def _agmoo_verdict(meta: Dict[str, Any]) -> str:
    if validate_ads_geometry is None:
        return "AGMOO_VALIDATOR_UNAVAILABLE"
    payload = dict(meta)
    payload.setdefault("ads_pipeline_tier", "canonical")
    payload.setdefault("ads_boundary_mode", "gkpw")
    payload.setdefault("operators", [
        {
            "name": payload.get("operator_name", "O_phi"),
            "Delta": payload.get("Delta"),
            "m2L2": payload.get("m2L2"),
        }
    ])
    return str(validate_ads_geometry(payload).get("overall_verdict", "UNKNOWN"))


def _relative_gr_delta(base_result: Dict[str, Any], variant_result: Dict[str, Any]) -> Dict[str, float]:
    base = np.asarray(base_result["G_R_real"], dtype=np.float64) + 1j * np.asarray(
        base_result["G_R_imag"], dtype=np.float64
    )
    variant = np.asarray(variant_result["G_R_real"], dtype=np.float64) + 1j * np.asarray(
        variant_result["G_R_imag"], dtype=np.float64
    )
    if base.shape != variant.shape:
        raise GKPWAdsError(f"benchmark shape mismatch: base={base.shape}, variant={variant.shape}")
    diff = variant - base
    denom = max(float(np.linalg.norm(base.ravel())), 1e-30)
    return {
        "relative_l2_delta": float(np.linalg.norm(diff.ravel()) / denom),
        "max_abs_delta": float(np.max(np.abs(diff))),
    }


def _resample_geometry(geo: AdsGeometry, *, n_points: int, z_min_index: int = 0) -> AdsGeometry:
    if n_points < 20:
        raise GKPWAdsError("benchmark geometry resampling requires at least 20 radial points")
    z_src = np.asarray(geo.z[z_min_index:], dtype=np.float64)
    if z_src.size < 20:
        raise GKPWAdsError("benchmark UV-cut geometry is too short")
    z_new = np.linspace(float(z_src[0]), float(z_src[-1]), int(n_points), dtype=np.float64)
    return AdsGeometry(
        name=f"{geo.name}__bench",
        family=geo.family,
        d=geo.d,
        z_h=geo.z_h,
        z=z_new,
        A=np.interp(z_new, geo.z, geo.A),
        f=np.interp(z_new, geo.z, geo.f),
    )


def _interpolate_frequency_result(
    dense_result: Dict[str, Any],
    target_omega: np.ndarray,
) -> Dict[str, Any]:
    dense_omega = np.asarray(dense_result["omega_grid"], dtype=np.float64)
    target = np.asarray(target_omega, dtype=np.float64)
    out = {
        "omega_grid": target,
        "k_grid": np.asarray(dense_result["k_grid"], dtype=np.float64),
    }
    for key in ("G_R_real", "G_R_imag"):
        arr = np.asarray(dense_result[key], dtype=np.float64)
        interp = np.vstack([np.interp(target, dense_omega, row) for row in arr])
        out[key] = interp
    return out


def compute_stability_benchmarks(
    geo: AdsGeometry,
    config: GKPWConfig,
    *,
    base_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Lightweight reproducibility checks for the numerical GKPW rail.

    These are not performance benchmarks. They are deterministic sensitivity
    probes against three discretization choices that should change the answer
    continuously, not switch provenance or metadata.
    """
    base = base_result if base_result is not None else build_correlator_grid(geo, config)
    checks: Dict[str, Any] = {}

    radial_points = max(20, int(round(float(geo.z.size) * 0.75)))
    radial_geo = _resample_geometry(geo, n_points=radial_points)
    radial_result = build_correlator_grid(radial_geo, config)
    checks["radial_discretization"] = {
        "base_n_z": int(geo.z.size),
        "variant_n_z": int(radial_points),
        **_relative_gr_delta(base, radial_result),
    }

    uv_drop = max(1, int(round(float(geo.z.size) * 0.05)))
    uv_points = max(20, int(geo.z.size - uv_drop))
    uv_geo = _resample_geometry(geo, n_points=uv_points, z_min_index=uv_drop)
    uv_result = build_correlator_grid(uv_geo, config)
    checks["uv_cutoff"] = {
        "base_z_min": float(geo.z[0]),
        "variant_z_min": float(uv_geo.z[0]),
        "dropped_points": int(uv_drop),
        **_relative_gr_delta(base, uv_result),
    }

    dense_n_omega = max(int(config.n_omega) * 2 - 1, int(config.n_omega) + 2)
    dense_config = replace(config, n_omega=dense_n_omega)
    dense_result = build_correlator_grid(geo, dense_config)
    dense_at_base = _interpolate_frequency_result(
        dense_result,
        np.asarray(base["omega_grid"], dtype=np.float64),
    )
    checks["frequency_resolution"] = {
        "base_n_omega": int(config.n_omega),
        "variant_n_omega": int(dense_n_omega),
        **_relative_gr_delta(base, dense_at_base),
    }

    checks["status"] = "PASS" if all(
        np.isfinite(v.get("relative_l2_delta", np.nan))
        for key, v in checks.items()
        if isinstance(v, dict) and key != "status"
    ) else "FAIL"
    return checks


def write_correlator_h5(
    result: Dict[str, Any],
    output_path: Path,
    *,
    geo: AdsGeometry,
    config: GKPWConfig,
) -> Dict[str, Any]:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_hash = config_hash(config, geo.name)
    out_hash = output_hash(result)
    meta = dict(result["metadata"])
    meta.update(
        {
            "geometry_name": geo.name,
            "family": geo.family,
            "d": int(geo.d),
            "z_h": float(geo.z_h) if geo.z_h is not None else 0.0,
            "config_hash": cfg_hash,
            "reproducibility_hash": out_hash,
        }
    )
    validate_gate6_metadata(meta)
    with h5py.File(output_path, "w") as fh:
        for key, value in meta.items():
            fh.attrs[key] = value
        fh.attrs["config_json"] = json.dumps(asdict(config), sort_keys=True)
        for key in (
            "omega_grid",
            "k_grid",
            "G_R_real",
            "G_R_imag",
            "source_real",
            "source_imag",
            "response_real",
            "response_imag",
            "uv_fit_residual_norm",
        ):
            fh.create_dataset(key, data=result[key])
    return meta


def generate_to_run(
    geometry_h5: Path,
    run_dir: Path,
    config: GKPWConfig,
    *,
    output_subdir: str = "gkpw_ads_scalar_correlator",
    run_benchmarks: bool = False,
) -> Dict[str, Any]:
    run_dir = Path(run_dir).resolve()
    output_dir = (run_dir / output_subdir).resolve()
    if run_dir not in output_dir.parents and output_dir != run_dir:
        raise GKPWAdsError(f"refusing to write outside run_dir: {output_dir}")
    geo = load_ads_geometry(Path(geometry_h5))
    result = build_correlator_grid(geo, config)
    h5_path = output_dir / f"{geo.name}__gkpw_scalar_correlator.h5"
    meta = write_correlator_h5(result, h5_path, geo=geo, config=config)
    complete = gate6_complete(meta)
    benchmarks = compute_stability_benchmarks(geo, config, base_result=result) if run_benchmarks else None
    summary = {
        "artifact": str(h5_path),
        "geometry_h5": str(Path(geometry_h5)),
        "correlator_type": meta["correlator_type"],
        "classification": meta["classification"],
        "gate6_complete": complete,
        "bf_bound_pass": bool(meta["bf_bound_pass"]),
        "agmoo_verdict": _agmoo_verdict(meta),
        "config_hash": meta["config_hash"],
        "reproducibility_hash": meta["reproducibility_hash"],
        "benchmarks": benchmarks,
        "metadata": meta,
    }
    summary_path = output_dir / f"{geo.name}__gkpw_scalar_correlator_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True, default=_json_default))
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate ads scalar GKPW source/response correlator.")
    parser.add_argument("--geometry-h5", required=True, type=Path)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--m2L2", type=float, default=0.0)
    parser.add_argument("--operator-name", default="O_phi")
    parser.add_argument("--bulk-field-name", default="phi")
    parser.add_argument("--omega-min", type=float, default=0.2)
    parser.add_argument("--omega-max", type=float, default=6.0)
    parser.add_argument("--n-omega", type=int, default=32)
    parser.add_argument("--k-min", type=float, default=0.0)
    parser.add_argument("--k-max", type=float, default=2.0)
    parser.add_argument("--n-k", type=int, default=8)
    parser.add_argument("--eps-horizon", type=float, default=1e-4)
    parser.add_argument("--uv-fit-points", type=int, default=10)
    parser.add_argument(
        "--run-benchmarks",
        action="store_true",
        help="Run deterministic radial/UV/frequency stability checks and include them in the summary JSON.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = GKPWConfig(
        m2L2=args.m2L2,
        operator_name=args.operator_name,
        bulk_field_name=args.bulk_field_name,
        omega_min=args.omega_min,
        omega_max=args.omega_max,
        n_omega=args.n_omega,
        k_min=args.k_min,
        k_max=args.k_max,
        n_k=args.n_k,
        eps_horizon=args.eps_horizon,
        uv_fit_points=args.uv_fit_points,
    )
    summary = generate_to_run(args.geometry_h5, args.run_dir, config, run_benchmarks=args.run_benchmarks)
    print(json.dumps(summary, indent=2, sort_keys=True, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
