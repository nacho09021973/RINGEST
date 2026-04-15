#!/usr/bin/env python3
"""
validate_agmoo_ads.py — Validador AGMOO para familia ``ads``.

Consume metadata de una geometría/run ``ads`` y emite un dict/JSON con:

  family                  str
  classification          str   (sub-clasificación ads)
  correlator_type         str
  geometry_gate_status    str   PASS | MISSING_FIELDS
  holographic_gate_status str   PASS | MISSING_FIELDS
  uv_ir_gate_status       str   PASS | FRAGILE | MISSING
  bf_check                dict
  missing_fields          list
  overall_verdict         str   (uno de ADS_VERDICT_STATES)

Para familias distintas de ``ads`` retorna overall_verdict = "NOT_ADS".

Uso como script::

    python tools/validate_agmoo_ads.py --meta '{"family":"ads","d":3,"z_h":1.0}'
    python tools/validate_agmoo_ads.py --h5 path/to/geometry.h5

Ver docs/checklist_agmoo_ads.md para el contrato completo.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Imports desde family_registry (tolerante a distintos CWD)
# ---------------------------------------------------------------------------
try:
    from family_registry import (
        ADS_CLASSIFICATIONS,
        ADS_VERDICT_STATES,
        CORRELATOR_TYPES,
        classify_ads_geometry,
        get_correlator_type_for_geometry,
    )
except ImportError:
    _repo_root = Path(__file__).resolve().parent.parent
    if str(_repo_root) not in sys.path:
        sys.path.insert(0, str(_repo_root))
    from family_registry import (
        ADS_CLASSIFICATIONS,
        ADS_VERDICT_STATES,
        CORRELATOR_TYPES,
        classify_ads_geometry,
        get_correlator_type_for_geometry,
    )


# ---------------------------------------------------------------------------
# Campos de los gates
# ---------------------------------------------------------------------------

#: Campos requeridos por el Gate geométrico mínimo.
GEOMETRY_REQUIRED_FIELDS: List[str] = ["family", "d", "z_h"]

#: Campos requeridos por el Gate 6 holográfico.
GATE6_REQUIRED_FIELDS: List[str] = [
    "bulk_field_name",
    "operator_name",
    "m2L2",
    "Delta",
    "bf_bound_pass",
    "uv_source_declared",
    "ir_bc_declared",
]


# ---------------------------------------------------------------------------
# Cota de Breitenlöhner-Freedman
# ---------------------------------------------------------------------------

def check_bf_bound(m2L2: float, d: int) -> bool:
    """
    Cota BF para AdS_{d+1}: m²L² ≥ -(d/2)².

    Una violación implica inestabilidad taquiónica → ADS_CONTRACT_FAIL.
    """
    return float(m2L2) >= -((d / 2.0) ** 2)


def check_bf_from_operators(operators: List[Dict], d: int) -> Dict:
    """
    Comprueba la cota BF para todos los operadores de la lista.

    Parameters
    ----------
    operators : list de dicts con claves ``name`` y ``m2L2``
    d         : dimensión del boundary

    Returns
    -------
    dict con ``status``, ``pass``, ``details``
    """
    if not operators:
        return {"status": "NO_OPERATORS", "pass": None, "details": []}

    details = []
    all_pass = True
    for op in operators:
        m2L2 = op.get("m2L2", None)
        name = op.get("name", "?")
        if m2L2 is None:
            details.append({
                "operator": name,
                "m2L2": None,
                "bf_pass": None,
                "reason": "m2L2 missing",
            })
            all_pass = False
            continue
        bf_ok = check_bf_bound(float(m2L2), d)
        details.append({
            "operator": name,
            "m2L2": float(m2L2),
            "bf_pass": bf_ok,
        })
        if not bf_ok:
            all_pass = False

    return {
        "status": "PASS" if all_pass else "FAIL",
        "pass": all_pass,
        "details": details,
    }


# ---------------------------------------------------------------------------
# Gate checks
# ---------------------------------------------------------------------------

_SENTINEL = object()


def check_geometry_gate(meta: Dict) -> Dict:
    """
    Comprueba los campos geométricos mínimos (family, d, z_h).

    Nota: z_h = None es un valor válido (T=0, sin horizonte). Se distingue
    entre clave ausente del dict y clave presente con valor None.
    Las claves ``family`` y ``d`` deben ser no-None para que el gate pase.

    Returns
    -------
    dict con ``status``, ``present``, ``missing``
    """
    missing: List[str] = []
    present: Dict[str, Any] = {}
    for field in GEOMETRY_REQUIRED_FIELDS:
        raw = meta.get(field, _SENTINEL)
        if raw is _SENTINEL:
            # Clave completamente ausente del dict
            missing.append(field)
            continue
        if field in ("family", "d") and raw is None:
            # family y d deben ser no-None (z_h puede ser None: T=0 válido)
            missing.append(field)
        else:
            present[field] = raw
    status = "PASS" if not missing else "MISSING_FIELDS"
    return {"status": status, "present": present, "missing": missing}


def check_holographic_gate(meta: Dict) -> Dict:
    """
    Comprueba los campos del Gate 6 holográfico.

    Returns
    -------
    dict con ``status``, ``present``, ``missing``
    """
    missing: List[str] = []
    present: Dict[str, Any] = {}
    for field in GATE6_REQUIRED_FIELDS:
        val = meta.get(field)
        if val is None:
            missing.append(field)
        else:
            present[field] = val
    status = "PASS" if not missing else "MISSING_FIELDS"
    return {"status": status, "present": present, "missing": missing}


def check_uv_ir_gate(meta: Dict) -> Dict:
    """
    Comprueba que la fuente UV y la condición de contorno IR estén declaradas.

    Returns
    -------
    dict con ``status`` (PASS | FRAGILE | MISSING), más los valores leídos
    """
    uv = meta.get("uv_source_declared", None)
    ir = meta.get("ir_bc_declared", None)

    if uv is None and ir is None:
        return {
            "status": "MISSING",
            "uv_source_declared": None,
            "ir_bc_declared": None,
        }

    issues: List[str] = []
    if uv is None:
        issues.append("uv_source_declared missing")
    elif not bool(uv):
        issues.append("uv_source_declared=False")

    if ir is None:
        issues.append("ir_bc_declared missing")
    elif not bool(ir):
        issues.append("ir_bc_declared=False")

    if issues:
        return {
            "status": "FRAGILE",
            "issues": issues,
            "uv_source_declared": uv,
            "ir_bc_declared": ir,
        }

    return {
        "status": "PASS",
        "uv_source_declared": uv,
        "ir_bc_declared": ir,
    }


# ---------------------------------------------------------------------------
# Lógica de veredicto
# ---------------------------------------------------------------------------

def compute_ads_verdict(
    classification: str,
    correlator_type: str,
    geometry_gate: Dict,
    holographic_gate: Dict,
    uv_ir_gate: Dict,
    bf_check: Dict,
) -> str:
    """
    Emite exactamente uno de los ADS_VERDICT_STATES.

    Orden de prioridad (ver docs/checklist_agmoo_ads.md):

    1. BF bound violada o campos geométricos críticos ausentes → ADS_CONTRACT_FAIL
    2. correlator_type = UNKNOWN o Gate 6 ausente → ADS_TEMPLATE_ONLY
       (Gate 6 ausente bloquea CUALQUIER lectura holográfica, incluso la térmica)
    3. Gate 6 presente + caso térmico + correlador no-Witten → ADS_THERMAL_TOY_ONLY
    4. Gate UV/IR = FRAGILE → ADS_UV_IR_FRAGILE
    5. Gate UV/IR = PASS → ADS_HOLOGRAPHIC_STRONG_PASS
    6. Default (Gate 6 OK, UV/IR no declarado) → ADS_HOLOGRAPHIC_PARTIAL_PASS
    """
    # 1. BF bound violation
    if bf_check.get("pass") is False:
        return "ADS_CONTRACT_FAIL"

    # 1b. Geometry gate: campos críticos ausentes
    geo_missing = set(geometry_gate.get("missing", []))
    if "family" in geo_missing or "d" in geo_missing:
        return "ADS_CONTRACT_FAIL"

    # 2. correlator_type UNKNOWN → ADS_TEMPLATE_ONLY
    if correlator_type == "UNKNOWN":
        return "ADS_TEMPLATE_ONLY"

    # 2b. Gate 6 incompleto → ADS_TEMPLATE_ONLY (sin excepción térmica)
    # La ausencia de Gate 6 bloquea cualquier lectura holográfica más fuerte,
    # incluido ADS_THERMAL_TOY_ONLY. Este estado requiere Gate 6 presente.
    holo_gate_ok = holographic_gate.get("status") == "PASS"
    if not holo_gate_ok:
        return "ADS_TEMPLATE_ONLY"

    # 3. Gate 6 presente: discriminar caso térmico + no-Witten
    is_thermal = classification == "ads_thermal"
    is_witten = correlator_type == "HOLOGRAPHIC_WITTEN_DIAGRAM"
    if is_thermal and not is_witten:
        return "ADS_THERMAL_TOY_ONLY"

    # 4. UV/IR gate fragile
    if uv_ir_gate.get("status") == "FRAGILE":
        return "ADS_UV_IR_FRAGILE"

    # 5. Todos los gates pasan
    if uv_ir_gate.get("status") == "PASS":
        return "ADS_HOLOGRAPHIC_STRONG_PASS"

    # 6. Default (Gate 6 OK pero UV/IR no declarado)
    return "ADS_HOLOGRAPHIC_PARTIAL_PASS"


# ---------------------------------------------------------------------------
# Validador principal
# ---------------------------------------------------------------------------

def validate_ads_geometry(meta: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida una geometría/run ads contra el contrato AGMOO.

    Parameters
    ----------
    meta : dict
        Metadata de la geometría. Claves esperadas:
        ``family``, ``d``, ``z_h``, ``deformation``, ``correlator_type``,
        ``ads_classification``, ``operators`` (lista), ``bf_bound_pass``,
        ``uv_source_declared``, ``ir_bc_declared``, ``bulk_field_name``,
        ``operator_name``, ``m2L2``, ``Delta``.

    Returns
    -------
    dict serializable a JSON con el resultado de la validación.

    Para familias distintas de ``ads``, retorna overall_verdict = "NOT_ADS".
    """
    family = meta.get("family", "unknown")

    # Familia distinta de ads → skip
    if family != "ads":
        return {
            "family": family,
            "classification": None,
            "correlator_type": None,
            "geometry_gate_status": "NOT_APPLICABLE",
            "holographic_gate_status": "NOT_APPLICABLE",
            "uv_ir_gate_status": "NOT_APPLICABLE",
            "bf_check": {"status": "NOT_APPLICABLE", "pass": None, "details": []},
            "missing_fields": [],
            "overall_verdict": "NOT_ADS",
        }

    # Sub-clasificación
    z_h_raw = meta.get("z_h", None)
    z_h: Optional[float] = float(z_h_raw) if z_h_raw is not None else None
    deformation = float(meta.get("deformation", 0.0))
    classification = meta.get("ads_classification") or classify_ads_geometry(
        family, z_h, deformation
    )
    if classification not in ADS_CLASSIFICATIONS:
        classification = "ads_toy_boundary"  # conservador si valor inválido

    # Tipo de correlador
    correlator_type = meta.get("correlator_type", "UNKNOWN")
    if correlator_type not in CORRELATOR_TYPES:
        correlator_type = "UNKNOWN"

    # Dimensión del boundary
    d_raw = meta.get("d", None)
    d_int = int(d_raw) if d_raw is not None else 3

    # Operadores para la cota BF
    operators = meta.get("operators", [])
    if isinstance(operators, str):
        try:
            operators = json.loads(operators)
        except Exception:
            operators = []

    # Cota BF
    bf_check = check_bf_from_operators(operators, d_int)
    # Sobreescribir con campo explícito si está presente
    explicit_bf = meta.get("bf_bound_pass")
    if explicit_bf is not None:
        bf_pass = bool(explicit_bf)
        bf_check["pass"] = bf_pass
        bf_check["status"] = "PASS" if bf_pass else "FAIL"

    # Gates
    geometry_gate = check_geometry_gate(meta)
    holographic_gate = check_holographic_gate(meta)
    uv_ir_gate = check_uv_ir_gate(meta)

    # Campos faltantes agregados
    missing_fields = sorted(set(
        holographic_gate.get("missing", []) + geometry_gate.get("missing", [])
    ))

    # Veredicto
    verdict = compute_ads_verdict(
        classification=classification,
        correlator_type=correlator_type,
        geometry_gate=geometry_gate,
        holographic_gate=holographic_gate,
        uv_ir_gate=uv_ir_gate,
        bf_check=bf_check,
    )

    return {
        "family": family,
        "classification": classification,
        "correlator_type": correlator_type,
        "geometry_gate_status": geometry_gate["status"],
        "holographic_gate_status": holographic_gate["status"],
        "uv_ir_gate_status": uv_ir_gate["status"],
        "bf_check": bf_check,
        "missing_fields": missing_fields,
        "overall_verdict": verdict,
    }


# ---------------------------------------------------------------------------
# Utilidad: leer metadata de un HDF5 generado por Stage 01
# ---------------------------------------------------------------------------

def read_meta_from_h5(h5_path: str) -> Dict[str, Any]:
    """
    Lee los attrs de un HDF5 de Stage 01 y devuelve un dict de metadata.

    Requiere h5py. Si no está disponible, lanza ImportError.
    """
    import h5py  # type: ignore

    meta: Dict[str, Any] = {}
    with h5py.File(h5_path, "r") as f:
        for k, v in f.attrs.items():
            # Decodificar bytes si viene de HDF5 string encoding
            if isinstance(v, bytes):
                v = v.decode("utf-8")
            meta[k] = v

        # Intentar leer operadores del boundary group
        if "boundary" in f:
            bgrp = f["boundary"]
            delta_mass_raw = bgrp.attrs.get("Delta_mass_dict", None)
            if delta_mass_raw is not None:
                if isinstance(delta_mass_raw, bytes):
                    delta_mass_raw = delta_mass_raw.decode("utf-8")
                try:
                    delta_mass_dict = json.loads(delta_mass_raw)
                    operators_from_h5 = [
                        {"name": k, "Delta": v["Delta"], "m2L2": v["m2L2"]}
                        for k, v in delta_mass_dict.items()
                    ]
                    meta["operators"] = operators_from_h5
                except Exception:
                    pass

        # Intentar leer operadores del attr operators JSON
        if "operators" not in meta:
            ops_raw = f.attrs.get("operators", None)
            if ops_raw is not None:
                if isinstance(ops_raw, bytes):
                    ops_raw = ops_raw.decode("utf-8")
                try:
                    meta["operators"] = json.loads(ops_raw)
                except Exception:
                    pass

    return meta


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Validador AGMOO para familia ads. "
                    "Emite JSON con clasificación, gates y veredicto."
    )
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--meta",
        type=str,
        help="JSON string con la metadata de la geometría.",
    )
    group.add_argument(
        "--h5",
        type=str,
        help="Ruta a un HDF5 generado por Stage 01.",
    )
    p.add_argument(
        "--output",
        type=str,
        default=None,
        help="Ruta de salida para escribir el JSON de validación (opcional).",
    )
    p.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indentación del JSON de salida.",
    )
    return p


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.h5:
        try:
            meta = read_meta_from_h5(args.h5)
        except ImportError:
            print("[ERROR] h5py no disponible. Instalar con: pip install h5py", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"[ERROR] No se pudo leer {args.h5}: {e}", file=sys.stderr)
            return 1
    else:
        try:
            meta = json.loads(args.meta)
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON inválido en --meta: {e}", file=sys.stderr)
            return 1

    result = validate_ads_geometry(meta)
    output_str = json.dumps(result, indent=args.indent, ensure_ascii=False)

    if args.output:
        Path(args.output).write_text(output_str, encoding="utf-8")
        print(f"[OK] Resultado escrito en: {args.output}")
    else:
        print(output_str)

    # Exit code: 0 si el veredicto no es CONTRACT_FAIL, 1 si lo es
    return 1 if result.get("overall_verdict") == "ADS_CONTRACT_FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
