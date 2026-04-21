#!/usr/bin/env python3
"""
build_multifamily_gkpw_bank.py

Itera sobre un conjunto de geometrías H5 (ads + rn_ads + ...) y produce,
familia a familia, el banco GKPW de correlators fuente/respuesta escritos
en disco. Cada correlator es un H5 canonical_strong consumible por
auditoría downstream.

Entrada admitida:
  --sources <PATH>...  cada PATH puede ser:
    - un fichero H5 de geometría (raíz con z_grid/A_of_z/f_of_z)
    - un directorio (se toman todos los *.h5 directos)
    - un manifest.json (p.ej. el emitido por generate_rn_ads_geometries.py)

El bank queda organizado como:
  <bank-dir>/
      <family>/
          <geo_name>__gkpw_scalar_correlator.h5
          <geo_name>__gkpw_scalar_correlator_summary.json
      bank_manifest.json

No sustituye el checkpoint congelado de Ruta A ni retraina Stage 02. Solo
produce el banco GKPW sobre el que se apoyaría cualquier retraining futuro.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import h5py  # noqa: E402

from tools.gkpw_ads_scalar_correlator import (  # noqa: E402
    GKPWAdsError,
    GKPWConfig,
    generate_to_run,
)

DEFAULT_ALLOWED_FAMILIES = frozenset({"ads", "rn_ads"})


def _expand_source(path: Path) -> List[Path]:
    path = Path(path).resolve()
    if path.is_dir():
        return sorted(p for p in path.glob("*.h5") if p.is_file())
    if path.is_file():
        if path.suffix == ".h5":
            return [path]
        if path.name == "manifest.json" or path.suffix == ".json":
            data = json.loads(path.read_text())
            items = data.get("items", []) if isinstance(data, dict) else []
            out: List[Path] = []
            for item in items:
                raw = item.get("h5") if isinstance(item, dict) else None
                if raw:
                    cand = Path(raw).resolve()
                    if cand.is_file() and cand.suffix == ".h5":
                        out.append(cand)
            return out
    return []


def _peek_family(h5_path: Path) -> str:
    with h5py.File(h5_path, "r") as fh:
        fam = fh.attrs.get("family", "unknown")
    if isinstance(fam, bytes):
        fam = fam.decode("utf-8")
    return str(fam)


def build_bank(
    sources: Iterable[Path],
    bank_dir: Path,
    config: GKPWConfig,
    *,
    allowed_families=DEFAULT_ALLOWED_FAMILIES,
    run_benchmarks: bool = False,
    on_error: str = "continue",
) -> Dict[str, Any]:
    if on_error not in ("continue", "raise"):
        raise ValueError(f"on_error must be 'continue' or 'raise', got {on_error!r}")

    bank_dir = Path(bank_dir).resolve()
    bank_dir.mkdir(parents=True, exist_ok=True)
    allowed = frozenset(allowed_families)

    collected: List[Path] = []
    for src in sources:
        collected.extend(_expand_source(Path(src)))
    # Deduplicate while preserving order.
    seen: set = set()
    unique: List[Path] = []
    for p in collected:
        rp = p.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        unique.append(rp)

    entries: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []
    t0 = time.time()

    for h5_path in unique:
        try:
            family = _peek_family(h5_path)
            if family not in allowed:
                failures.append({
                    "h5": str(h5_path),
                    "family": family,
                    "error": f"family not in allowed_families={sorted(allowed)!r}",
                })
                continue
            summary = generate_to_run(
                h5_path,
                bank_dir,
                config,
                output_subdir=family,
                run_benchmarks=run_benchmarks,
                allowed_families=allowed,
            )
            entries.append({
                "geometry_h5": str(h5_path),
                "family": family,
                "artifact": summary["artifact"],
                "classification": summary["classification"],
                "bf_bound_pass": summary["bf_bound_pass"],
                "gate6_complete": summary["gate6_complete"],
                "agmoo_verdict": summary["agmoo_verdict"],
                "config_hash": summary["config_hash"],
                "reproducibility_hash": summary["reproducibility_hash"],
            })
        except (GKPWAdsError, OSError, ValueError) as err:
            failures.append({
                "h5": str(h5_path),
                "error": f"{type(err).__name__}: {err}",
                "traceback": traceback.format_exc().splitlines()[-1],
            })
            if on_error == "raise":
                raise

    by_family: Dict[str, int] = {}
    for entry in entries:
        by_family[entry["family"]] = by_family.get(entry["family"], 0) + 1

    manifest = {
        "bank_dir": str(bank_dir),
        "n_sources_seen": len(unique),
        "n_entries": len(entries),
        "n_failures": len(failures),
        "by_family": by_family,
        "allowed_families": sorted(allowed),
        "elapsed_seconds": float(time.time() - t0),
        "config": asdict(config),
        "entries": entries,
        "failures": failures,
    }
    manifest_path = bank_dir / "bank_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True))
    return manifest


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Construye un banco GKPW multi-familia a partir de geometrías H5.",
    )
    p.add_argument("--sources", required=True, nargs="+", type=Path,
                   help="H5 / directorios / manifest.json con geometrías de entrada.")
    p.add_argument("--bank-dir", required=True, type=Path)
    p.add_argument("--allowed-families", default="ads,rn_ads",
                   help="Familias permitidas, coma-separadas.")
    p.add_argument("--run-benchmarks", action="store_true")
    p.add_argument("--on-error", choices=("continue", "raise"), default="continue")

    p.add_argument("--m2L2", type=float, default=0.0)
    p.add_argument("--operator-name", default="O_phi")
    p.add_argument("--bulk-field-name", default="phi")
    p.add_argument("--omega-min", type=float, default=0.2)
    p.add_argument("--omega-max", type=float, default=6.0)
    p.add_argument("--n-omega", type=int, default=32)
    p.add_argument("--k-min", type=float, default=0.0)
    p.add_argument("--k-max", type=float, default=2.0)
    p.add_argument("--n-k", type=int, default=8)
    p.add_argument("--eps-horizon", type=float, default=1e-4)
    p.add_argument("--uv-fit-points", type=int, default=10)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
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
    allowed = frozenset(
        s.strip() for s in str(args.allowed_families).split(",") if s.strip()
    )
    if not allowed:
        allowed = DEFAULT_ALLOWED_FAMILIES
    manifest = build_bank(
        args.sources,
        args.bank_dir,
        config,
        allowed_families=allowed,
        run_benchmarks=args.run_benchmarks,
        on_error=args.on_error,
    )
    print(json.dumps({
        "bank_dir": manifest["bank_dir"],
        "n_entries": manifest["n_entries"],
        "n_failures": manifest["n_failures"],
        "by_family": manifest["by_family"],
        "manifest": str(Path(manifest["bank_dir"]) / "bank_manifest.json"),
    }, indent=2))
    return 0 if manifest["n_failures"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
