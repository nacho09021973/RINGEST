#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import h5py
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if not hasattr(np, "trapezoid"):
    np.trapezoid = np.trapz  # type: ignore[attr-defined]

from family_registry import get_family_status, get_family_status_description
from tools.gkpw_ads_scalar_correlator import CORRELATOR_TYPE, validate_gate6_metadata


class PackTrainingH5Error(RuntimeError):
    pass


def _load_stage01_helpers() -> Tuple[Any, Any]:
    stage01_path = REPO_ROOT / "01_generate_sandbox_geometries.py"
    spec = importlib.util.spec_from_file_location("stage01_pack_training_h5", stage01_path)
    if spec is None or spec.loader is None:
        raise PackTrainingH5Error(f"No se pudo cargar {stage01_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    try:
        return module._g2_from_gkpw_spectral, module._ricci_from_A_f
    except AttributeError as exc:
        raise PackTrainingH5Error(
            "Stage 01 no expone _g2_from_gkpw_spectral/_ricci_from_A_f; "
            "no se puede empaquetar sin duplicar logica viva."
        ) from exc


_G2_FROM_GKPW_SPECTRAL, _RICCI_FROM_A_F = _load_stage01_helpers()


def _expand_source(path: Path) -> List[Path]:
    path = Path(path).resolve()
    if path.is_dir():
        return sorted(p for p in path.glob("*.h5") if p.is_file())
    if path.is_file():
        if path.suffix == ".h5":
            return [path]
        if path.suffix == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                items = data.get("items") or data.get("entries") or data.get("geometries") or []
                out: List[Path] = []
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    raw = item.get("h5") or item.get("artifact") or item.get("geometry_h5") or item.get("file")
                    if not raw:
                        continue
                    cand = Path(raw)
                    if not cand.is_absolute():
                        cand = (path.parent / cand).resolve()
                    else:
                        cand = cand.resolve()
                    if cand.is_file() and cand.suffix == ".h5":
                        out.append(cand)
                return out
    return []


def _decode_attr(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if isinstance(value, np.generic):
        return value.item()
    return value


def _load_geometry_catalog(sources: Iterable[Path]) -> Dict[str, Path]:
    catalog: Dict[str, Path] = {}
    for src in sources:
        for h5_path in _expand_source(Path(src)):
            with h5py.File(h5_path, "r") as fh:
                name = _decode_attr(fh.attrs.get("system_name", fh.attrs.get("name", h5_path.stem)))
            catalog[str(name)] = h5_path
    return catalog


def _load_gkpw_catalog(sources: Iterable[Path]) -> Dict[str, Path]:
    catalog: Dict[str, Path] = {}
    for src in sources:
        for h5_path in _expand_source(Path(src)):
            with h5py.File(h5_path, "r") as fh:
                geometry_name = _decode_attr(fh.attrs.get("geometry_name", ""))
            if geometry_name:
                catalog[str(geometry_name)] = h5_path
    return catalog


def _require_dataset(fh: h5py.File, name: str) -> np.ndarray:
    if name not in fh:
        raise PackTrainingH5Error(f"dataset obligatorio ausente: {fh.filename}:{name}")
    return np.asarray(fh[name][...], dtype=np.float64)


def _sorted_profiles(geometry_h5: Path) -> Tuple[Dict[str, Any], Dict[str, np.ndarray]]:
    with h5py.File(geometry_h5, "r") as fh:
        attrs = {key: _decode_attr(value) for key, value in fh.attrs.items()}
        z = _require_dataset(fh, "z_grid").reshape(-1)
        A = _require_dataset(fh, "A_of_z").reshape(-1)
        f = _require_dataset(fh, "f_of_z").reshape(-1)
    if not (z.size == A.size == f.size):
        raise PackTrainingH5Error(
            f"shape mismatch en {geometry_h5}: z={z.shape}, A={A.shape}, f={f.shape}"
        )
    if z.size < 20:
        raise PackTrainingH5Error(f"grid radial demasiado corto en {geometry_h5}: {z.size}")
    order = np.argsort(z)
    z = z[order]
    A = A[order]
    f = f[order]
    if np.any(np.diff(z) <= 0.0):
        raise PackTrainingH5Error(f"z_grid no estrictamente creciente en {geometry_h5}")
    return attrs, {"z_grid": z, "A_truth": A, "f_truth": f}


def _compute_temperature(z: np.ndarray, A: np.ndarray, f: np.ndarray, z_h: float) -> float:
    if not np.isfinite(z_h) or z_h <= 0.0:
        return 0.0
    if z.size < 3:
        raise PackTrainingH5Error("no hay puntos suficientes para estimar la temperatura")
    df_dz = np.gradient(f, z, edge_order=2)
    A_h = float(A[-1])
    fp_h = float(df_dz[-1])
    T = np.exp(A_h) * abs(fp_h) / (4.0 * np.pi)
    return float(T) if np.isfinite(T) else 0.0


def _operator_payload(corr_attrs: Dict[str, Any]) -> List[Dict[str, Any]]:
    operator_name = str(corr_attrs.get("operator_name", "")).strip()
    if not operator_name:
        raise PackTrainingH5Error("operator_name ausente en correlator GKPW")
    return [{
        "name": operator_name,
        "Delta": float(corr_attrs["Delta"]),
        "m2L2": float(corr_attrs["m2L2"]),
        "spin": 0,
    }]


def _boundary_payload(
    geometry_attrs: Dict[str, Any],
    profiles: Dict[str, np.ndarray],
    correlator_h5: Path,
    n_x: int,
    x_min: float,
    x_max: float,
) -> Tuple[Dict[str, Any], Dict[str, Any], List[Dict[str, Any]]]:
    with h5py.File(correlator_h5, "r") as fh:
        corr_attrs = {key: _decode_attr(value) for key, value in fh.attrs.items()}
        validate_gate6_metadata(corr_attrs)
        omega_grid = _require_dataset(fh, "omega_grid").reshape(-1)
        k_grid = _require_dataset(fh, "k_grid").reshape(-1)
        gr_real = _require_dataset(fh, "G_R_real")
        gr_imag = _require_dataset(fh, "G_R_imag")
        extra = {}
        for name in ("source_real", "source_imag", "response_real", "response_imag", "uv_fit_residual_norm"):
            if name in fh:
                extra[name] = np.asarray(fh[name][...], dtype=np.float64)

    family = str(geometry_attrs.get("family", "unknown"))
    z_h = float(geometry_attrs.get("z_h", 0.0) or 0.0)
    d = int(geometry_attrs.get("d", 4))
    ads_boundary_mode = "gkpw" if family == "ads" and corr_attrs.get("correlator_type") == CORRELATOR_TYPE else "toy"
    family_status = get_family_status(family, ads_boundary_mode=ads_boundary_mode, source="sandbox")

    x_grid = np.linspace(float(x_min), float(x_max), int(n_x), dtype=np.float64)
    g2 = _G2_FROM_GKPW_SPECTRAL(x_grid, omega_grid, gr_imag).astype(np.float64)
    operators = _operator_payload(corr_attrs)
    operator_name = str(operators[0]["name"])
    temperature = _compute_temperature(
        profiles["z_grid"], profiles["A_truth"], profiles["f_truth"], z_h,
    )

    boundary_data: Dict[str, Any] = {
        "x_grid": x_grid,
        f"G2_{operator_name}": g2,
        "omega_grid": omega_grid.astype(np.float64),
        "k_grid": k_grid.astype(np.float64),
        "G_R_real": gr_real.astype(np.float64),
        "G_R_imag": gr_imag.astype(np.float64),
        "temperature": np.asarray([temperature], dtype=np.float64),
        "T": np.asarray([temperature], dtype=np.float64),
        "d": np.asarray([d], dtype=np.int32),
    }
    boundary_data.update(extra)

    boundary_attrs: Dict[str, Any] = dict(corr_attrs)
    boundary_attrs.update(
        {
            "d": d,
            "family": family,
            "family_status": family_status,
            "family_status_description": get_family_status_description(family_status),
            "temperature": float(temperature),
            "T": float(temperature),
            "has_horizon": int(z_h > 0.0),
            "g2_construction": "spectral_laplace_from_gkpw_retarded_correlator",
            "gkpw_primary_operator": operator_name,
        }
    )
    return boundary_data, boundary_attrs, operators


def _bulk_truth_payload(
    geometry_attrs: Dict[str, Any],
    profiles: Dict[str, np.ndarray],
) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
    d = int(geometry_attrs.get("d", 4))
    R_truth = _RICCI_FROM_A_F(
        profiles["z_grid"],
        profiles["A_truth"],
        profiles["f_truth"],
        d,
    ).astype(np.float64)
    if not np.all(np.isfinite(R_truth)):
        raise PackTrainingH5Error("R_truth no finito tras reconstruccion desde A/f")
    D = d + 1
    G_trace_truth = ((1.0 - D / 2.0) * R_truth).astype(np.float64)

    bulk_truth = dict(profiles)
    bulk_truth["R_truth"] = R_truth
    bulk_truth["G_trace_truth"] = G_trace_truth

    bulk_attrs: Dict[str, Any] = {}
    for key, value in geometry_attrs.items():
        if isinstance(value, (str, int, float, bool, np.generic)):
            bulk_attrs[key] = _decode_attr(value)
    bulk_attrs["d"] = d
    bulk_attrs["z_h"] = float(geometry_attrs.get("z_h", 0.0) or 0.0)
    return bulk_truth, bulk_attrs


def pack_one(
    geometry_h5: Path,
    correlator_h5: Path,
    out_dir: Path,
    *,
    category: str,
    n_x: int,
    x_min: float,
    x_max: float,
) -> Dict[str, Any]:
    geometry_attrs, profiles = _sorted_profiles(geometry_h5)
    system_name = str(geometry_attrs.get("system_name", geometry_attrs.get("name", geometry_h5.stem)))
    family = str(geometry_attrs.get("family", "unknown"))
    boundary_data, boundary_attrs, operators = _boundary_payload(
        geometry_attrs, profiles, correlator_h5, n_x=n_x, x_min=x_min, x_max=x_max,
    )
    bulk_truth, bulk_attrs = _bulk_truth_payload(geometry_attrs, profiles)

    ads_boundary_mode = "gkpw" if family == "ads" else "toy"
    family_status = get_family_status(family, ads_boundary_mode=ads_boundary_mode, source="sandbox")

    out_path = Path(out_dir) / f"{system_name}.h5"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(out_path, "w") as fh:
        for key, value in geometry_attrs.items():
            if isinstance(value, (str, int, float, bool, np.generic)):
                fh.attrs[key] = _decode_attr(value)
        fh.attrs["name"] = system_name
        fh.attrs["system_name"] = system_name
        fh.attrs["category"] = category
        fh.attrs["family"] = family
        fh.attrs["family_status"] = family_status
        fh.attrs["family_status_description"] = get_family_status_description(family_status)
        fh.attrs["operators"] = json.dumps(operators)
        for key in (
            "correlator_type",
            "classification",
            "bulk_field_name",
            "operator_name",
            "m2L2",
            "Delta",
            "bf_bound_pass",
            "uv_source_declared",
            "ir_bc_declared",
            "config_hash",
            "reproducibility_hash",
        ):
            if key in boundary_attrs:
                fh.attrs[key] = boundary_attrs[key]

        bgrp = fh.create_group("boundary")
        for key, value in boundary_data.items():
            bgrp.create_dataset(key, data=value)
        for key, value in boundary_attrs.items():
            bgrp.attrs[key] = value
        delta_mass_dict = {
            op["name"]: {"Delta": op["Delta"], "m2L2": op["m2L2"]}
            for op in operators
        }
        bgrp.attrs["Delta_mass_dict"] = json.dumps(delta_mass_dict)

        tgrp = fh.create_group("bulk_truth")
        for key, value in bulk_truth.items():
            tgrp.create_dataset(key, data=value)
        for key, value in bulk_attrs.items():
            tgrp.attrs[key] = value

        fh.create_dataset("z_grid", data=bulk_truth["z_grid"])
        fh.create_dataset("A_of_z", data=bulk_truth["A_truth"])
        fh.create_dataset("f_of_z", data=bulk_truth["f_truth"])

    return {
        "name": system_name,
        "family": family,
        "category": category,
        "d": int(geometry_attrs.get("d", 4)),
        "z_h": float(geometry_attrs.get("z_h", 0.0) or 0.0),
        "file": out_path.name,
        "operators": [op["name"] for op in operators],
        "correlator_type": boundary_attrs.get("correlator_type"),
        "classification": boundary_attrs.get("classification"),
        "family_status": family_status,
        "metadata": {
            "geometry_h5": str(Path(geometry_h5).resolve()),
            "gkpw_h5": str(Path(correlator_h5).resolve()),
            "g2_construction": boundary_attrs["g2_construction"],
        },
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Empaqueta geometrias raw + correlators GKPW en H5 training-ready "
            "para 02_emergent_geometry_engine.py --mode train."
        ),
    )
    p.add_argument("--geometry-sources", required=True, nargs="+", type=Path)
    p.add_argument("--gkpw-sources", required=True, nargs="+", type=Path)
    p.add_argument("--out-dir", required=True, type=Path)
    p.add_argument("--category", default="known", choices=("known", "test", "unknown"))
    p.add_argument("--n-x", type=int, default=100)
    p.add_argument("--x-min", type=float, default=0.1)
    p.add_argument("--x-max", type=float, default=10.0)
    return p


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    geometry_catalog = _load_geometry_catalog(args.geometry_sources)
    gkpw_catalog = _load_gkpw_catalog(args.gkpw_sources)
    names = sorted(set(geometry_catalog) & set(gkpw_catalog))
    if not names:
        raise PackTrainingH5Error("No hay interseccion geometry_name entre geometry-sources y gkpw-sources")

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest: Dict[str, Any] = {"geometries": []}

    missing_geometry = sorted(set(gkpw_catalog) - set(geometry_catalog))
    missing_gkpw = sorted(set(geometry_catalog) - set(gkpw_catalog))
    if missing_geometry or missing_gkpw:
        print(
            json.dumps(
                {
                    "warning": "match_incompleto",
                    "missing_geometry": missing_geometry,
                    "missing_gkpw": missing_gkpw,
                },
                indent=2,
            )
        )

    for name in names:
        entry = pack_one(
            geometry_catalog[name],
            gkpw_catalog[name],
            out_dir,
            category=args.category,
            n_x=args.n_x,
            x_min=args.x_min,
            x_max=args.x_max,
        )
        manifest["geometries"].append(entry)

    manifest_path = out_dir / "geometries_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "out_dir": str(out_dir),
                "n_geometries": len(manifest["geometries"]),
                "manifest": str(manifest_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
