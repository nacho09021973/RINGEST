#!/usr/bin/env python3
"""
generate_rn_ads_geometries.py

Emite H5 de familia RN-AdS (Reissner-Nordström-AdS planar, gauge domain-wall)
consumibles por `tools/gkpw_ads_scalar_correlator.py`.

NO sustituye Ruta A ni regenera training data sandbox. Produce miembros
del carril multi-familia previsto (ADS + RN-AdS + ...), pero NO declara
`canonical_strong`: en el contrato vivo del repo ese estatus sigue reservado
a `ads` con frontera GKPW. Estos H5 son geometrías raw para un banco GKPW y
para empaquetado posterior, no una promoción semántica de RN-AdS.

Métrica (L=1, gauge domain-wall, brana plana):

    ds² = e^{2A(z)}[-f(z)·dt² + dx_i²] + dz²/f(z)
    A(z) = -log(z)
    f(z) = 1 - (1+Q²)·(z/z_h)^d + Q²·(z/z_h)^{2(d-1)}

Notas:
  * Q=0 reduce a AdS-Schwarzschild planar.
  * La carga extremal satisface Q²_ext = d/(d-2); más allá aparece horizonte
    interior y f cambia de signo dentro de (0, z_h). El generador rechaza
    cualquier (d, Q) que viole f(z) > 0 en el dominio de integración.
  * El potencial de gauge A_μ se omite: el correlador escalar GKPW actual
    solo usa (A, f, d, z_h), pero se registra `charge_Q` para trazabilidad.

Uso:
  python3 tools/generate_rn_ads_geometries.py \\
      --out-dir runs/rn_ads_bank/geometries \\
      --d 3 --z-h 1.0 --Q 0.0 0.3 0.6 0.9 \\
      --n-points 256
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Tuple

import h5py
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from family_registry import get_family_status

FAMILY = "rn_ads"
FAMILY_STATUS = get_family_status(FAMILY, ads_boundary_mode="toy", source="sandbox")
METRIC_CONVENTION = "domain_wall_L1_planar"


class RNAdsGeometryError(RuntimeError):
    pass


@dataclass(frozen=True)
class RNAdsConfig:
    z_h: float
    Q: float
    d: int = 3
    n_points: int = 256
    z_frac_uv: float = 1e-3
    z_frac_ir: float = 1e-3


def extremal_Q_squared(d: int) -> float:
    if d <= 2:
        raise RNAdsGeometryError(f"RN-AdS planar requires d>=3; got d={d}")
    return float(d) / float(d - 2)


def _profiles(cfg: RNAdsConfig) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    if cfg.n_points < 64:
        raise RNAdsGeometryError(f"n_points={cfg.n_points} demasiado bajo; exige >=64")
    if not (0.0 < cfg.z_frac_uv < 0.5):
        raise RNAdsGeometryError(f"z_frac_uv={cfg.z_frac_uv} fuera de rango (0, 0.5)")
    if not (0.0 < cfg.z_frac_ir < 0.5):
        raise RNAdsGeometryError(f"z_frac_ir={cfg.z_frac_ir} fuera de rango (0, 0.5)")
    if cfg.z_h <= 0.0:
        raise RNAdsGeometryError(f"z_h={cfg.z_h} debe ser > 0")
    q2_ext = extremal_Q_squared(cfg.d)
    if cfg.Q < 0.0 or cfg.Q ** 2 >= q2_ext:
        raise RNAdsGeometryError(
            f"Q={cfg.Q} fuera de (0, Q_ext) para d={cfg.d}; Q²_ext={q2_ext}"
        )

    z_min = cfg.z_frac_uv * cfg.z_h
    z_max = (1.0 - cfg.z_frac_ir) * cfg.z_h
    z = np.linspace(z_min, z_max, int(cfg.n_points), dtype=np.float64)
    A = -np.log(z)
    u = z / cfg.z_h
    f = 1.0 - (1.0 + cfg.Q ** 2) * u ** cfg.d + (cfg.Q ** 2) * u ** (2 * (cfg.d - 1))
    if np.any(f <= 0.0):
        raise RNAdsGeometryError(
            f"f(z) no positivo en el dominio para cfg={cfg}; revisa Q vs extremal."
        )
    return z, A, f


def system_name(cfg: RNAdsConfig) -> str:
    def _fmt(x: float) -> str:
        return f"{x:.3f}".replace(".", "p")

    return f"rn_ads_d{cfg.d}_zh{_fmt(cfg.z_h)}_Q{_fmt(cfg.Q)}"


def write_h5(cfg: RNAdsConfig, out_dir: Path) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    z, A, f = _profiles(cfg)
    name = system_name(cfg)
    path = out_dir / f"{name}.h5"
    with h5py.File(path, "w") as h5:
        h5.attrs["system_name"] = name
        h5.attrs["family"] = FAMILY
        h5.attrs["family_status"] = FAMILY_STATUS
        h5.attrs["metric_convention"] = METRIC_CONVENTION
        h5.attrs["d"] = int(cfg.d)
        h5.attrs["z_h"] = float(cfg.z_h)
        h5.attrs["charge_Q"] = float(cfg.Q)
        h5.attrs["Q_squared"] = float(cfg.Q ** 2)
        h5.attrs["Q_squared_extremal"] = float(extremal_Q_squared(cfg.d))
        h5.attrs["n_points"] = int(cfg.n_points)
        h5.create_dataset("z_grid", data=z)
        h5.create_dataset("A_of_z", data=A)
        h5.create_dataset("f_of_z", data=f)
    return path


def _enumerate_configs(
    d: int, z_h_values: List[float], Q_values: List[float], n_points: int,
    z_frac_uv: float, z_frac_ir: float,
) -> List[RNAdsConfig]:
    configs = []
    for z_h in z_h_values:
        for Q in Q_values:
            configs.append(
                RNAdsConfig(
                    z_h=float(z_h), Q=float(Q), d=int(d),
                    n_points=int(n_points),
                    z_frac_uv=float(z_frac_uv),
                    z_frac_ir=float(z_frac_ir),
                )
            )
    return configs


def generate_bank(
    out_dir: Path,
    *,
    d: int,
    z_h_values: List[float],
    Q_values: List[float],
    n_points: int = 256,
    z_frac_uv: float = 1e-3,
    z_frac_ir: float = 1e-3,
) -> dict:
    out_dir = Path(out_dir)
    configs = _enumerate_configs(
        d, z_h_values, Q_values, n_points, z_frac_uv, z_frac_ir,
    )
    entries = []
    for cfg in configs:
        path = write_h5(cfg, out_dir)
        entries.append({
            "h5": str(path),
            "system_name": system_name(cfg),
            "family": FAMILY,
            "family_status": FAMILY_STATUS,
            "config": asdict(cfg),
        })

    manifest = {
        "family": FAMILY,
        "family_status": FAMILY_STATUS,
        "metric_convention": METRIC_CONVENTION,
        "d": int(d),
        "n_items": len(entries),
        "items": entries,
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return manifest


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generador de geometrías RN-AdS planar (raw geometry; family_status=toy_sandbox).",
    )
    p.add_argument("--out-dir", required=True, type=Path)
    p.add_argument("--d", type=int, default=3)
    p.add_argument("--z-h", type=float, nargs="+", default=[1.0])
    p.add_argument("--Q", type=float, nargs="+", required=True,
                   help="Lista de cargas Q (no Q²). 0 ≤ Q < Q_ext = sqrt(d/(d-2)).")
    p.add_argument("--n-points", type=int, default=256)
    p.add_argument("--z-frac-uv", type=float, default=1e-3)
    p.add_argument("--z-frac-ir", type=float, default=1e-3)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    manifest = generate_bank(
        args.out_dir,
        d=args.d,
        z_h_values=list(args.z_h),
        Q_values=list(args.Q),
        n_points=args.n_points,
        z_frac_uv=args.z_frac_uv,
        z_frac_ir=args.z_frac_ir,
    )
    print(json.dumps({
        "out_dir": str(Path(args.out_dir).resolve()),
        "n_items": manifest["n_items"],
        "manifest": str(Path(args.out_dir) / "manifest.json"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
