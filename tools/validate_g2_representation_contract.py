#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import h5py
import numpy as np

THIS_FILE = Path(__file__).resolve()
REPO_ROOT_DEFAULT = THIS_FILE.parents[1]
if str(REPO_ROOT_DEFAULT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT_DEFAULT))

from tools.g2_representation_contract import (
    DEFAULT_COMPAT_CONTRACT,
    DEFAULT_COMPAT_MODE,
    DEFAULT_G2_REPR_CONTRACT,
    build_stage02_contract_attrs,
    canonicalize_g2_representation,
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_stage02_feature_namespace(module_path: Path) -> Dict[str, Any]:
    source = module_path.read_text(encoding="utf-8")
    start = source.index("def extract_correlator_features")
    end = source.index("class CuerdasDataLoader")
    snippet = source[start:end]
    namespace: Dict[str, Any] = {
        "np": np,
        "Dict": Dict,
        "List": List,
        "Any": Any,
    }
    exec(snippet, namespace)
    return namespace


def copy_attrs(src, dst) -> None:
    for key, value in src.attrs.items():
        dst.attrs[key] = value


def load_boundary_data(boundary_group: h5py.Group) -> Dict[str, Any]:
    boundary_data: Dict[str, Any] = {}
    for key in boundary_group.keys():
        boundary_data[key] = boundary_group[key][:]
    for key in boundary_group.attrs.keys():
        boundary_data[key] = boundary_group.attrs[key]
    return boundary_data


def build_raw_boundary_view(boundary_group: h5py.Group) -> Dict[str, Any]:
    boundary_data: Dict[str, Any] = {}
    dataset_map = {
        "x_grid": "x_grid_raw" if "x_grid_raw" in boundary_group else "x_grid",
        "omega_grid": "omega_grid_raw" if "omega_grid_raw" in boundary_group else "omega_grid",
        "k_grid": "k_grid_raw" if "k_grid_raw" in boundary_group else "k_grid",
        "G_R_real": "G_R_real_raw" if "G_R_real_raw" in boundary_group else "G_R_real",
        "G_R_imag": "G_R_imag_raw" if "G_R_imag_raw" in boundary_group else "G_R_imag",
        "G2_ringdown": "G2_ringdown_raw" if "G2_ringdown_raw" in boundary_group else "G2_ringdown",
    }
    for dst_key, src_key in dataset_map.items():
        if src_key in boundary_group:
            boundary_data[dst_key] = boundary_group[src_key][:]
    if "central_charge_eff" in boundary_group:
        boundary_data["central_charge_eff"] = boundary_group["central_charge_eff"][:]
    else:
        boundary_data["central_charge_eff"] = np.array([0.0], dtype=np.float64)
    for key in boundary_group.attrs.keys():
        boundary_data[key] = boundary_group.attrs[key]
    return boundary_data


def block_max_abs(delta: np.ndarray, start: int, end: int) -> float:
    return float(np.max(np.abs(delta[start:end]))) if end > start else 0.0


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Validate the canonical G2 representation contract on a boundary HDF5.")
    ap.add_argument("--repo-root", required=True, type=Path)
    ap.add_argument("--source-h5", required=True, type=Path)
    ap.add_argument("--output-dir", required=True, type=Path)
    ap.add_argument("--modified-file", action="append", default=[])
    ap.add_argument("--whether-realdata-bridge-was-modified", action="store_true")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    source_h5 = args.source_h5.resolve()
    output_dir = args.output_dir.resolve()
    contracted_dir = output_dir / "contracted_boundary"
    contracted_dir.mkdir(parents=True, exist_ok=True)
    out_h5 = contracted_dir / source_h5.name

    stage02 = load_stage02_feature_namespace(repo_root / "02_emergent_geometry_engine.py")

    with h5py.File(source_h5, "r") as src, h5py.File(out_h5, "w") as dst:
        copy_attrs(src, dst)
        boundary_src = src["boundary"]
        boundary_dst = dst.create_group("boundary")
        copy_attrs(boundary_src, boundary_dst)

        x_grid_raw = boundary_src["x_grid_raw"][:] if "x_grid_raw" in boundary_src else boundary_src["x_grid"][:]
        g2_raw = boundary_src["G2_ringdown_raw"][:] if "G2_ringdown_raw" in boundary_src else boundary_src["G2_ringdown"][:]
        omega_grid_raw = boundary_src["omega_grid_raw"][:] if "omega_grid_raw" in boundary_src else boundary_src["omega_grid"][:]
        k_grid_raw = boundary_src["k_grid_raw"][:] if "k_grid_raw" in boundary_src else boundary_src["k_grid"][:]
        g_r_real_raw = boundary_src["G_R_real_raw"][:] if "G_R_real_raw" in boundary_src else boundary_src["G_R_real"][:]
        g_r_imag_raw = boundary_src["G_R_imag_raw"][:] if "G_R_imag_raw" in boundary_src else boundary_src["G_R_imag"][:]

        omega_grid_compat = boundary_src["omega_grid"][:] if "omega_grid" in boundary_src else omega_grid_raw
        k_grid_compat = boundary_src["k_grid"][:] if "k_grid" in boundary_src else k_grid_raw
        g_r_real_compat = boundary_src["G_R_real"][:] if "G_R_real" in boundary_src else g_r_real_raw
        g_r_imag_compat = boundary_src["G_R_imag"][:] if "G_R_imag" in boundary_src else g_r_imag_raw
        c_eff = boundary_src["central_charge_eff"][:] if "central_charge_eff" in boundary_src else np.array([0.0], dtype=np.float64)

        g2_contract = canonicalize_g2_representation(x_grid_raw, g2_raw)
        contract_attrs = build_stage02_contract_attrs(
            x_grid_raw=x_grid_raw,
            x_grid_canon=g2_contract.x_grid,
            omega_grid_raw=omega_grid_raw,
            omega_grid_compat=omega_grid_compat,
            g_r_raw_shape=tuple(g_r_real_raw.shape),
            g_r_compat_shape=tuple(g_r_real_compat.shape),
        )

        boundary_dst.create_dataset("omega_grid_raw", data=np.asarray(omega_grid_raw, dtype=np.float64))
        boundary_dst.create_dataset("k_grid_raw", data=np.asarray(k_grid_raw, dtype=np.float64))
        boundary_dst.create_dataset("G_R_real_raw", data=np.asarray(g_r_real_raw, dtype=np.float64))
        boundary_dst.create_dataset("G_R_imag_raw", data=np.asarray(g_r_imag_raw, dtype=np.float64))
        boundary_dst.create_dataset("x_grid_raw", data=np.asarray(x_grid_raw, dtype=np.float64))
        boundary_dst.create_dataset("G2_ringdown_raw", data=np.asarray(g2_raw, dtype=np.float64))

        boundary_dst.create_dataset("omega_grid", data=np.asarray(omega_grid_compat, dtype=np.float64))
        boundary_dst.create_dataset("k_grid", data=np.asarray(k_grid_compat, dtype=np.float64))
        boundary_dst.create_dataset("G_R_real", data=np.asarray(g_r_real_compat, dtype=np.float64))
        boundary_dst.create_dataset("G_R_imag", data=np.asarray(g_r_imag_compat, dtype=np.float64))
        boundary_dst.create_dataset("x_grid", data=g2_contract.x_grid.astype(np.float64))
        boundary_dst.create_dataset("G2_ringdown", data=g2_contract.g2_canonical.astype(np.float64))
        boundary_dst.create_dataset("G2_O1", data=g2_contract.g2_canonical.astype(np.float64))
        boundary_dst.create_dataset("central_charge_eff", data=np.asarray(c_eff, dtype=np.float64))

        for key, value in contract_attrs.items():
            boundary_dst.attrs[key] = value
        boundary_dst.attrs["compat_mode"] = DEFAULT_COMPAT_MODE
        boundary_dst.attrs["compat_contract"] = DEFAULT_COMPAT_CONTRACT
        boundary_dst.attrs["g2_repr_contract"] = DEFAULT_G2_REPR_CONTRACT
        boundary_dst.attrs["g2_eps"] = float(g2_contract.eps)
        boundary_dst.attrs["g2_valid_points"] = int(g2_contract.n_valid_points)
        boundary_dst.attrs["g2_unique_points"] = int(g2_contract.n_unique_points)

        for key in src.keys():
            if key != "boundary":
                src.copy(key, dst)

    with h5py.File(source_h5, "r") as src:
        raw_boundary_data = build_raw_boundary_view(src["boundary"])
    with h5py.File(out_h5, "r") as contracted:
        compat_boundary_data = load_boundary_data(contracted["boundary"])
        operators = []

    raw_features = np.asarray(stage02["build_feature_vector"](raw_boundary_data, []), dtype=np.float64)
    compat_features = np.asarray(stage02["build_feature_vector"](compat_boundary_data, operators), dtype=np.float64)
    delta = compat_features - raw_features

    feature_vector_shape = list(compat_features.shape)
    feature_vector_finite = bool(np.all(np.isfinite(compat_features)))
    qnm_invariant = bool(np.array_equal(raw_features[13:16], compat_features[13:16]))

    max_abs_delta_g2_block = block_max_abs(delta, 0, 9)
    max_abs_delta_thermal_block = block_max_abs(delta, 9, 13)
    max_abs_delta_qnm_block = block_max_abs(delta, 13, 16)
    max_abs_delta_response_block = block_max_abs(delta, 16, 18)
    max_abs_delta_global_block = block_max_abs(delta, 18, 20)

    verdict = "CONTRACT_OK"
    if feature_vector_shape != [20] or (not feature_vector_finite) or (not qnm_invariant):
        verdict = "CONTRACT_FAIL"
    if max_abs_delta_g2_block <= 0.0:
        verdict = "CONTRACT_FAIL"

    source_note = (
        f"source_h5={source_h5}\n"
        "used boundary_dataset_v2 because the contract requires preserving *_raw alongside the canonical view.\n"
    )
    (output_dir / "source_used.txt").write_text(source_note, encoding="utf-8")

    feature_diff = {
        "source_h5": str(source_h5),
        "contracted_h5": str(out_h5),
        "raw_feature_vector": raw_features.tolist(),
        "compat_feature_vector": compat_features.tolist(),
        "delta": delta.tolist(),
        "max_abs_delta_g2_block": max_abs_delta_g2_block,
        "max_abs_delta_thermal_block": max_abs_delta_thermal_block,
        "max_abs_delta_qnm_block": max_abs_delta_qnm_block,
        "max_abs_delta_response_block": max_abs_delta_response_block,
        "max_abs_delta_global_block": max_abs_delta_global_block,
    }
    (output_dir / "feature_diff.json").write_text(json.dumps(feature_diff, indent=2) + "\n", encoding="utf-8")

    files_created = [
        str(output_dir / "manifest.json"),
        str(output_dir / "summary.json"),
        str(output_dir / "source_used.txt"),
        str(output_dir / "feature_diff.json"),
        str(out_h5),
    ]
    summary = {
        "source_h5": str(source_h5),
        "files_created": files_created,
        "files_modified": args.modified_file,
        "whether_realdata_bridge_was_modified": bool(args.whether_realdata_bridge_was_modified),
        "compat_mode": DEFAULT_COMPAT_MODE,
        "contract_name": DEFAULT_G2_REPR_CONTRACT,
        "feature_vector_shape": feature_vector_shape,
        "feature_vector_finite": feature_vector_finite,
        "qnm_invariant": qnm_invariant,
        "max_abs_delta_g2_block": max_abs_delta_g2_block,
        "max_abs_delta_thermal_block": max_abs_delta_thermal_block,
        "max_abs_delta_qnm_block": max_abs_delta_qnm_block,
        "max_abs_delta_response_block": max_abs_delta_response_block,
        "max_abs_delta_global_block": max_abs_delta_global_block,
        "verdict": verdict,
        "conclusion_short": (
            "Canonicalization changes the representation gauge in the G2 block while leaving QNM features invariant; "
            "this is a representation-contract fix, not a new physical interpretation."
        ),
    }
    (output_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    manifest = {
        "created_at": utc_now_iso(),
        "source_h5": str(source_h5),
        "contracted_h5": str(out_h5),
        "compat_mode": DEFAULT_COMPAT_MODE,
        "compat_contract": DEFAULT_COMPAT_CONTRACT,
        "g2_repr_contract": DEFAULT_G2_REPR_CONTRACT,
        "files_created": files_created,
        "files_modified": args.modified_file,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return 0 if verdict == "CONTRACT_OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
