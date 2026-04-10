from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any, Dict, Tuple, Optional

import h5py
import numpy as np

DEFAULT_COMPAT_MODE = "stage02_sandbox_v5"
DEFAULT_COMPAT_CONTRACT = "sandbox_v5_stage02"
DEFAULT_G2_REPR_CONTRACT = "logx_logg2_interp_unit_peak_v1"
DEFAULT_EPS = 1e-12
DEFAULT_N_X = 100
DEFAULT_X_MIN = 1e-3
DEFAULT_X_MAX = 10.0
MIN_VALID_POINTS = 3


class G2RepresentationContractError(RuntimeError):
    pass


def canonical_x_grid(
    n_x: int = DEFAULT_N_X,
    x_min: float = DEFAULT_X_MIN,
    x_max: float = DEFAULT_X_MAX,
) -> np.ndarray:
    if int(n_x) != DEFAULT_N_X:
        raise G2RepresentationContractError(f"canonical x_grid length must be {DEFAULT_N_X}, got {n_x}")
    x_min = float(x_min)
    x_max = float(x_max)
    if not np.isfinite(x_min) or not np.isfinite(x_max) or not (x_max > x_min > 0.0):
        raise G2RepresentationContractError(
            f"invalid canonical x_grid range: x_min={x_min}, x_max={x_max}"
        )
    return np.linspace(x_min, x_max, int(n_x), dtype=np.float64)


def _to_1d_float64(name: str, values: Any) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64).reshape(-1)
    if arr.size == 0:
        raise G2RepresentationContractError(f"{name}: empty array")
    return arr


def _deduplicate_x_by_mean(x_sorted: np.ndarray, g2_sorted: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    unique_x = []
    unique_g2 = []
    i = 0
    n = x_sorted.size
    while i < n:
        x0 = x_sorted[i]
        j = i + 1
        while j < n and x_sorted[j] == x0:
            j += 1
        unique_x.append(x0)
        unique_g2.append(float(np.mean(g2_sorted[i:j], dtype=np.float64)))
        i = j
    return np.asarray(unique_x, dtype=np.float64), np.asarray(unique_g2, dtype=np.float64)


def canonicalize_g2_representation(
    x_grid_raw: Any,
    g2_raw: Any,
    *,
    eps: float = DEFAULT_EPS,
    n_x: int = DEFAULT_N_X,
    x_min: float = DEFAULT_X_MIN,
    x_max: float = DEFAULT_X_MAX,
    min_valid_points: int = MIN_VALID_POINTS,
) -> Dict[str, Any]:
    x_raw = _to_1d_float64("x_grid_raw", x_grid_raw)
    g2_raw_arr = _to_1d_float64("g2_raw", g2_raw)
    if x_raw.shape != g2_raw_arr.shape:
        raise G2RepresentationContractError(
            f"shape mismatch: x_grid_raw={x_raw.shape}, g2_raw={g2_raw_arr.shape}"
        )
    eps = float(eps)
    if not np.isfinite(eps) or eps <= 0.0:
        raise G2RepresentationContractError(f"eps must be positive finite, got {eps}")

    valid_mask = (
        np.isfinite(x_raw)
        & np.isfinite(g2_raw_arr)
        & (x_raw > 0.0)
        & ((g2_raw_arr + eps) > 0.0)
    )
    n_input = int(x_raw.size)
    n_valid = int(np.sum(valid_mask))
    if n_valid < int(min_valid_points):
        raise G2RepresentationContractError(
            f"insufficient valid points for G2 canonicalization: n_input={n_input}, n_valid={n_valid}, min_valid_points={min_valid_points}"
        )

    x_valid = x_raw[valid_mask]
    g2_valid = g2_raw_arr[valid_mask]
    order = np.argsort(x_valid, kind="mergesort")
    x_sorted = x_valid[order]
    g2_sorted = g2_valid[order]
    x_unique, g2_unique = _deduplicate_x_by_mean(x_sorted, g2_sorted)
    if x_unique.size < int(min_valid_points):
        raise G2RepresentationContractError(
            f"insufficient unique x points after deduplication: n_unique={int(x_unique.size)}, min_valid_points={min_valid_points}"
        )

    x_canon = canonical_x_grid(n_x=n_x, x_min=x_min, x_max=x_max)
    logx_unique = np.log(x_unique)
    logx_canon = np.log(x_canon)
    logg2_unique = np.log(g2_unique + eps)
    logg2_canon = np.interp(logx_canon, logx_unique, logg2_unique)
    g2_canon = np.exp(logg2_canon)

    peak = float(np.max(g2_canon)) if g2_canon.size else 0.0
    if not np.isfinite(peak) or peak <= 0.0:
        raise G2RepresentationContractError(f"invalid canonical G2 peak after interpolation: peak={peak}")
    g2_canon = (g2_canon / peak).astype(np.float64)

    return {
        "x_grid": x_canon.astype(np.float64),
        "G2_ringdown": g2_canon.astype(np.float64),
        "meta": {
            "eps": eps,
            "n_input": n_input,
            "n_valid_after_filter": n_valid,
            "n_unique_after_dedup": int(x_unique.size),
            "x_grid_raw_range": [float(np.nanmin(x_raw)), float(np.nanmax(x_raw))],
            "x_grid_canon_range": [float(x_canon[0]), float(x_canon[-1])],
            "g2_interp_mode": "interp_logx_logg2_edge_hold_numpy",
            "g2_norm_mode": "unit_peak",
        },
    }


def _copy_nonboundary_groups(src_file: h5py.File, dst_file: h5py.File) -> None:
    for key in src_file.keys():
        if key == "boundary":
            continue
        src_file.copy(key, dst_file)


def _copy_file_attrs(src_file: h5py.File, dst_file: h5py.File) -> None:
    for key, value in src_file.attrs.items():
        dst_file.attrs[key] = value


def contract_boundary_group(
    boundary_group: h5py.Group,
    *,
    compat_mode: str = DEFAULT_COMPAT_MODE,
    compat_contract: str = DEFAULT_COMPAT_CONTRACT,
    compat_note: str = "Preserve raw G2/x_grid view and expose canonical stage-02-compatible representation.",
    g2_repr_contract: str = DEFAULT_G2_REPR_CONTRACT,
    eps: float = DEFAULT_EPS,
    central_charge_fallback: float = 0.0,
) -> Dict[str, Any]:
    if "x_grid" not in boundary_group:
        raise G2RepresentationContractError("boundary/x_grid missing")
    if "G2_ringdown" not in boundary_group:
        raise G2RepresentationContractError("boundary/G2_ringdown missing")

    x_raw = np.asarray(boundary_group["x_grid"][...], dtype=np.float64)
    g2_raw = np.asarray(boundary_group["G2_ringdown"][...], dtype=np.float64)
    canon = canonicalize_g2_representation(x_raw, g2_raw, eps=eps)

    out = {
        "datasets": {},
        "attrs": {},
    }

    out["datasets"]["x_grid_raw"] = x_raw.astype(np.float64)
    out["datasets"]["G2_ringdown_raw"] = g2_raw.astype(np.float64)
    if "omega_grid" in boundary_group:
        omega_grid_raw = np.asarray(boundary_group["omega_grid"][...], dtype=np.float64)
        out["datasets"]["omega_grid_raw"] = omega_grid_raw
        out["datasets"]["omega_grid"] = omega_grid_raw.copy()
    if "G_R_real" in boundary_group:
        grr = np.asarray(boundary_group["G_R_real"][...], dtype=np.float64)
        out["datasets"]["G_R_real_raw"] = grr
        out["datasets"]["G_R_real"] = grr.copy()
    if "G_R_imag" in boundary_group:
        gri = np.asarray(boundary_group["G_R_imag"][...], dtype=np.float64)
        out["datasets"]["G_R_imag_raw"] = gri
        out["datasets"]["G_R_imag"] = gri.copy()
    if "k_grid" in boundary_group:
        out["datasets"]["k_grid"] = np.asarray(boundary_group["k_grid"][...], dtype=np.float64)

    out["datasets"]["x_grid"] = canon["x_grid"]
    out["datasets"]["G2_ringdown"] = canon["G2_ringdown"]
    out["datasets"]["G2_O1"] = canon["G2_ringdown"].copy()

    for key, value in boundary_group.attrs.items():
        out["attrs"][key] = value

    central_charge_eff = boundary_group.attrs.get("central_charge_eff", central_charge_fallback)
    d_value = boundary_group.attrs.get("d", 4)
    out["attrs"].update(
        {
            "central_charge_eff": float(np.asarray(central_charge_eff, dtype=np.float64).reshape(-1)[0]),
            "d": int(np.asarray(d_value).reshape(-1)[0]),
            "compat_mode": compat_mode,
            "compat_contract": compat_contract,
            "compat_note": compat_note,
            "g2_repr_contract": g2_repr_contract,
            "g2_interp_mode": canon["meta"]["g2_interp_mode"],
            "g2_norm_mode": canon["meta"]["g2_norm_mode"],
            "x_grid_raw_range": np.asarray(canon["meta"]["x_grid_raw_range"], dtype=np.float64),
            "x_grid_canon_range": np.asarray(canon["meta"]["x_grid_canon_range"], dtype=np.float64),
            "omega_grid_raw_range": np.asarray(
                [
                    float(np.nanmin(out["datasets"]["omega_grid_raw"])) if "omega_grid_raw" in out["datasets"] else np.nan,
                    float(np.nanmax(out["datasets"]["omega_grid_raw"])) if "omega_grid_raw" in out["datasets"] else np.nan,
                ],
                dtype=np.float64,
            ),
            "omega_grid_compat_range": np.asarray(
                [
                    float(np.nanmin(out["datasets"]["omega_grid"])) if "omega_grid" in out["datasets"] else np.nan,
                    float(np.nanmax(out["datasets"]["omega_grid"])) if "omega_grid" in out["datasets"] else np.nan,
                ],
                dtype=np.float64,
            ),
            "G_R_raw_shape": np.asarray(out["datasets"].get("G_R_real_raw", np.zeros((0,), dtype=np.float64)).shape, dtype=np.int64),
            "G_R_compat_shape": np.asarray(out["datasets"].get("G_R_real", np.zeros((0,), dtype=np.float64)).shape, dtype=np.int64),
        }
    )
    return out


def write_contracted_boundary_h5(
    source_h5: str | Path,
    output_h5: str | Path,
    *,
    compat_mode: str = DEFAULT_COMPAT_MODE,
    compat_contract: str = DEFAULT_COMPAT_CONTRACT,
    compat_note: str = "Preserve raw G2/x_grid view and expose canonical stage-02-compatible representation.",
    g2_repr_contract: str = DEFAULT_G2_REPR_CONTRACT,
    eps: float = DEFAULT_EPS,
    central_charge_fallback: float = 0.0,
) -> Dict[str, Any]:
    source_h5 = Path(source_h5)
    output_h5 = Path(output_h5)
    output_h5.parent.mkdir(parents=True, exist_ok=True)
    with h5py.File(source_h5, "r") as src, h5py.File(output_h5, "w") as dst:
        _copy_file_attrs(src, dst)
        _copy_nonboundary_groups(src, dst)
        if "boundary" not in src:
            raise G2RepresentationContractError(f"missing boundary group in {source_h5}")
        contract = contract_boundary_group(
            src["boundary"],
            compat_mode=compat_mode,
            compat_contract=compat_contract,
            compat_note=compat_note,
            g2_repr_contract=g2_repr_contract,
            eps=eps,
            central_charge_fallback=central_charge_fallback,
        )
        b = dst.create_group("boundary")
        for key, arr in contract["datasets"].items():
            b.create_dataset(key, data=arr)
        for key, value in contract["attrs"].items():
            b.attrs[key] = value
    return {
        "source_h5": str(source_h5),
        "output_h5": str(output_h5),
        "compat_mode": compat_mode,
        "contract_name": compat_contract,
        "g2_repr_contract": g2_repr_contract,
    }


def _load_stage02_feature_builder(engine_path: Optional[Path] = None):
    if engine_path is None:
        engine_path = Path(__file__).resolve().parents[1] / "02_emergent_geometry_engine.py"
    source = Path(engine_path).read_text(encoding="utf-8")
    tree = ast.parse(source)
    wanted = {
        "extract_correlator_features",
        "extract_thermal_features",
        "extract_response_features",
        "build_feature_vector",
    }
    segments = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name in wanted:
            segment = ast.get_source_segment(source, node)
            if segment:
                segments.append(segment)
    missing = wanted.difference({node.name for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in wanted})
    if missing:
        raise G2RepresentationContractError(f"missing stage-02 feature functions in {engine_path}: {sorted(missing)}")
    exec_source = (
        "from __future__ import annotations\n"
        "import numpy as np\n"
        "from typing import Dict, List, Any\n\n"
        + "\n\n".join(segments)
    )
    namespace: Dict[str, Any] = {}
    exec(exec_source, namespace, namespace)
    return namespace["build_feature_vector"]


def _boundary_to_dict(boundary_group: h5py.Group) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key in boundary_group.keys():
        out[key] = np.asarray(boundary_group[key][...])
    for key, value in boundary_group.attrs.items():
        out[key] = value
    return out


def compute_feature_diff(
    source_h5: str | Path,
    contracted_h5: str | Path,
    *,
    engine_path: Optional[str | Path] = None,
) -> Dict[str, Any]:
    build_feature_vector = _load_stage02_feature_builder(Path(engine_path) if engine_path else None)
    with h5py.File(source_h5, "r") as src, h5py.File(contracted_h5, "r") as dst:
        src_boundary = _boundary_to_dict(src["boundary"])
        dst_boundary = _boundary_to_dict(dst["boundary"])
    raw_features = np.asarray(build_feature_vector(src_boundary, []), dtype=np.float64)
    compat_features = np.asarray(build_feature_vector(dst_boundary, []), dtype=np.float64)
    if raw_features.shape != compat_features.shape:
        raise G2RepresentationContractError(
            f"feature shape mismatch: raw={raw_features.shape}, compat={compat_features.shape}"
        )
    delta = compat_features - raw_features
    return {
        "raw": raw_features.tolist(),
        "compat": compat_features.tolist(),
        "delta": delta.tolist(),
        "feature_vector_shape": list(raw_features.shape),
        "feature_vector_finite": bool(np.all(np.isfinite(compat_features))),
        "qnm_invariant": bool(np.array_equal(raw_features[13:16], compat_features[13:16])),
        "max_abs_delta_g2_block": float(np.max(np.abs(delta[0:9]))),
        "max_abs_delta_thermal_block": float(np.max(np.abs(delta[9:13]))),
        "max_abs_delta_qnm_block": float(np.max(np.abs(delta[13:16]))),
        "max_abs_delta_response_block": float(np.max(np.abs(delta[16:18]))),
        "max_abs_delta_global_block": float(np.max(np.abs(delta[18:20]))),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Canonical G2/x_grid representation contract adapter for stage 02")
    ap.add_argument("--source-h5", required=True)
    ap.add_argument("--output-h5", required=True)
    ap.add_argument("--feature-diff-json", default=None)
    ap.add_argument("--summary-json", default=None)
    ap.add_argument("--manifest-json", default=None)
    ap.add_argument("--source-used-txt", default=None)
    ap.add_argument("--engine-path", default=None)
    ap.add_argument("--compat-mode", default=DEFAULT_COMPAT_MODE, choices=["stage02_sandbox_v5"])
    ap.add_argument("--compat-contract", default=DEFAULT_COMPAT_CONTRACT)
    ap.add_argument("--g2-repr-contract", default=DEFAULT_G2_REPR_CONTRACT)
    ap.add_argument("--eps", type=float, default=DEFAULT_EPS)
    args = ap.parse_args()

    write_info = write_contracted_boundary_h5(
        args.source_h5,
        args.output_h5,
        compat_mode=args.compat_mode,
        compat_contract=args.compat_contract,
        g2_repr_contract=args.g2_repr_contract,
        eps=args.eps,
    )
    feature_diff = compute_feature_diff(args.source_h5, args.output_h5, engine_path=args.engine_path)
    summary = {
        "source_h5": str(Path(args.source_h5)),
        "files_created": [str(Path(args.output_h5))],
        "files_modified": [],
        "whether_02R_was_modified": False,
        "compat_mode": args.compat_mode,
        "contract_name": args.compat_contract,
        "feature_vector_shape": feature_diff["feature_vector_shape"],
        "feature_vector_finite": feature_diff["feature_vector_finite"],
        "qnm_invariant": feature_diff["qnm_invariant"],
        "max_abs_delta_g2_block": feature_diff["max_abs_delta_g2_block"],
        "max_abs_delta_thermal_block": feature_diff["max_abs_delta_thermal_block"],
        "max_abs_delta_qnm_block": feature_diff["max_abs_delta_qnm_block"],
        "max_abs_delta_response_block": feature_diff["max_abs_delta_response_block"],
        "max_abs_delta_global_block": feature_diff["max_abs_delta_global_block"],
        "verdict": "CONTRACT_OK" if feature_diff["feature_vector_finite"] and feature_diff["qnm_invariant"] else "CONTRACT_FAIL",
        "conclusion_short": "Canonical view changes the G2 representation block while preserving QNM invariants.",
    }
    manifest = {
        "contract": write_info,
        "artifacts": {
            "contracted_boundary_h5": str(Path(args.output_h5)),
            "summary_json": args.summary_json,
            "feature_diff_json": args.feature_diff_json,
            "source_used_txt": args.source_used_txt,
        },
    }
    if args.feature_diff_json:
        p = Path(args.feature_diff_json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(feature_diff, indent=2) + "\n", encoding="utf-8")
    if args.summary_json:
        p = Path(args.summary_json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if args.manifest_json:
        p = Path(args.manifest_json)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    if args.source_used_txt:
        p = Path(args.source_used_txt)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(str(Path(args.source_h5)) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
