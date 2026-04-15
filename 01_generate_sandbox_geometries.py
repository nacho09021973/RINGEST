#!/usr/bin/env python3
from __future__ import annotations
# 01_generate_sandbox_geometries.py
# CUERDAS - Bloque A: Geometria emergente (generacion de sandbox)
#
# Objective:
#   Generar familys de "universes sandbox" controlados a partir de geometrias base
#   (AdS, Lifshitz, hyperscaling, deformed, ...) y producir datasets de:
#       - boundary/: datos CFT en el borde (entrada del learner)
#       - bulk_truth/: geometria de referencia (solo para validacion/contratos)
#
# PRINCIPALES CARACTERÍSTICAS
#   - Generacion de multiples universes por geometria base (jitter de parametros).
#   - Jitter de parametros fisicos (z_h, d, theta, z_dyn, deformation, ...).
#   - CLI escalable: p.ej. --n-known, --n-test, --n-unknown.
#   - Backend opcional EMD para familys tipo Lifshitz / hyperscaling.
#
# Inputs: (tipicas)
#   - Parametros de familys por CLI o fichero de configuracion:
#       * family ∈ {ads, lifshitz, hyperscaling, deformed, ...}
#       * d, z_dyn, theta, etc.
#
# Outputs: (estructura esperada)
#   runs/sandbox_geometries/
#     boundary/
#       <system_name>_boundary.h5
#         - x_grid, temperature, G2_<O>, omega_grid, k_grid, G_R_real, G_R_imag, ...
#     bulk_truth/
#       <system_name>_bulk_truth.h5
#         - z_grid, A_truth, f_truth, R_truth
#         - attrs: z_h, family, d, theta, z_dyn, ...
#     manifest.json
#       - Lista de "geometries" generadas y metadatos basicos.
#
# RELACIÓN CON OTROS SCRIPTS
#   - Entrada directa para:
#       * 02_emergent_geometry_engine.py       (reconstruye geometria a partir de boundary/)
#       * 04_geometry_physics_contracts.py    (usa bulk_truth/ para contratos fisicos)
#
# HONESTIDAD
#   - El learner NUNCA ve ni la metrica real ni el solver EMD.
#   - Solo se exponen datos CFT de boundary a los modelos de geometria.
#   - El bulk_truth se reserva exclusivamente para validacion y contratos fisicos.
#
# History:
#   - Anteriormente conocido como: 00_generate_fase_11_v3.py
#
# FIX 2025-12-21: Guardrail de d movido ANTES de generar boundary_data y bulk_truth
#   para asegurar consistencia entre nombre del file y datos generados.

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, List, Dict, Tuple, Optional

import numpy as np  # type: ignore
import h5py  # type: ignore

try:
    from tools.gkpw_ads_scalar_correlator import (
        CORRELATOR_TYPE as GKPW_ADS_CORRELATOR_TYPE,
        AdsGeometry as GKPWAdsGeometry,
        GKPWConfig,
        GATE6_REQUIRED_FIELDS as GKPW_GATE6_REQUIRED_FIELDS,
        build_correlator_grid as build_gkpw_ads_correlator_grid,
        config_hash as gkpw_config_hash,
        output_hash as gkpw_output_hash,
        validate_gate6_metadata as validate_gkpw_gate6_metadata,
    )
    HAS_GKPW_ADS = True
except ImportError:
    GKPW_ADS_CORRELATOR_TYPE = "GKPW_SOURCE_RESPONSE_NUMERICAL"
    GKPW_GATE6_REQUIRED_FIELDS = (
        "bulk_field_name",
        "operator_name",
        "m2L2",
        "Delta",
        "bf_bound_pass",
        "uv_source_declared",
        "ir_bc_declared",
        "correlator_type",
    )
    GKPWAdsGeometry = None  # type: ignore
    GKPWConfig = None  # type: ignore
    build_gkpw_ads_correlator_grid = None  # type: ignore
    gkpw_config_hash = None  # type: ignore
    gkpw_output_hash = None  # type: ignore
    validate_gkpw_gate6_metadata = None  # type: ignore
    HAS_GKPW_ADS = False

try:
    from tools.validate_agmoo_ads import validate_ads_geometry
except ImportError:
    validate_ads_geometry = None  # type: ignore

# Registro canónico de familias (contract-first)
try:
    from family_registry import (  # noqa: F401
        extra_attrs_for,
        FAMILY_MAP,
        classify_ads_geometry,
        get_correlator_type_for_geometry,
    )
    HAS_FAMILY_REGISTRY = True
except ImportError:
    HAS_FAMILY_REGISTRY = False
    FAMILY_MAP = {}  # type: ignore

    def classify_ads_geometry(family, z_h, deformation=0.0):  # type: ignore
        """Stub: family_registry no disponible."""
        if family != "ads":
            return None
        if abs(deformation) > 1e-8:
            return "ads_deformed"
        if z_h is not None and float(z_h) > 0.0:
            return "ads_thermal"
        return "ads_toy_boundary"

    def get_correlator_type_for_geometry(family, use_geodesic=True):  # type: ignore
        """Stub: family_registry no disponible."""
        return "GEODESIC_APPROXIMATION" if use_geodesic else "TOY_PHENOMENOLOGICAL"

# V3 INFRASTRUCTURE - PATCH
HAS_STAGE_UTILS = False
EXIT_OK = 0
EXIT_ERROR = 3
STATUS_OK = "OK"
STATUS_ERROR = "ERROR"
StageContext = None
add_standard_arguments = None
parse_stage_args = None

try:
    from stage_utils import (
        EXIT_ERROR, EXIT_OK, STATUS_ERROR, STATUS_OK,
        StageContext, add_standard_arguments, parse_stage_args,
    )
    HAS_STAGE_UTILS = True
except ImportError:
    pass

if not HAS_STAGE_UTILS:
    try:
        from tools.stage_utils import (
            EXIT_ERROR, EXIT_OK, STATUS_ERROR, STATUS_OK,
            StageContext, add_standard_arguments, parse_stage_args,
        )
        HAS_STAGE_UTILS = True
    except ImportError:
        print("[WARN] stage_utils not available")

# Backend opcional: soluciones EMD reales para Lifshitz / hyperscaling
try:
    from ecuaciones_emd import EMDLifshitzSolver  # type: ignore
    HAS_EMD = True
except ImportError:
    EMDLifshitzSolver = None  # type: ignore
    HAS_EMD = False


# ============================================================
#  NOTA SOBRE familyS, GAUGES Y FUENTES TEÓRICAS
# ============================================================
#
# familyS IMPLEMENTADAS:
#
#   TIER CANONICAL (soporte original):
#   - ads:            AdS puro, conforme a AGMOO Sec. 2
#   - lifshitz:       Extensión con exponente dinámico z (Kachru et al. 2008)
#   - hyperscaling:   Violación de hyperscaling θ (Huijse et al. 2011)
#   - dpbrane:        Métricas near-horizon de Dp-branas (AGMOO Sec. 6.1.3)
#   - deformed:       AdS con deformación suave fenomenológica
#   - unknown:        family de test sin garantía holográfica
#
#   TIER A (cohorte de expansión — encajan en gauge actual):
#   - rn_ads:         Reissner-Nordström AdS (BH cargado)
#   - gauss_bonnet:   Gauss-Bonnet AdS (corrección cuadrática en curvatura)
#   - massive_gravity: Massive gravity AdS tipo Vegh (disipación de momento)
#   - linear_axion:   Axiones lineales (disipación de momento, metal incoherente)
#   - charged_hvlif:  Hyperscaling-Violation Lifshitz cargado (EMD toy)
#   - gubser_rocha:   EMD Gubser-Rocha toy (dilatón corriendo, s(T=0)->0)
#   - soft_wall:      Soft-wall backreacted (deformación cuadrática IR del warp)
#
# NOTA HISTÓRICA:
#   Las familys Lifshitz y Hyperscaling son extensiones post-1999 del
#   paradigma AdS/CFT. El AGMOO (1999) cubre principalmente AdS puro y
#   Dp-branas. Usamos estas extensiones como familys de TEST para
#   evaluar la capacidad del pipeline de detectar/distinguir geometrías.
#
# GAUGE DE LA MÉTRICA:
#   Usamos el gauge conformal (Domain Wall):
#       ds² = e^{2A(z)} [ -f(z) dt² + dx² ] + dz²/f(z)
#   
#   NO el gauge de Poincaré estándar:
#       ds² = (L/z)² [ dz²/f + dx² - f dt² ]
#
#   En gauge conformal: A(z) = -log(z/L) para AdS puro
#   Esto afecta la forma funcional pero NO las relaciones físicas.
#
# CORRELADORES:
#   Los correladores de 2 puntos G₂(x) son TOY MODELS fenomenológicos:
#       T=0: G₂ ~ 1/|x|^{2Δ}
#       T>0: G₂ ~ (πT/sinh(πTx))^{2Δ}
#   
#   Esto captura el comportamiento CUALITATIVO (power-law UV, exponencial IR)
#   pero NO es la predicción exacta de AdS/CFT. Esto es DELIBERADO:
#   el pipeline debe descubrir relaciones desde datos imperfectos.
#
# ============================================================


# ============================================================
#  GEOMETRÍA OCULTA
# ============================================================

@dataclass
class HiddenGeometry:
    """
    Geometria del bulk que genera los datos CFT.
    NO se expone al learner (solo a bulk_truth para validacion).
    """
    name: str
    family: str           # ver family_registry.ALL_FAMILIES para valores válidos
    category: str         # "known", "test", "unknown"
    d: int                # dimension del boundary (CFT_d)
    z_h: Optional[float] = None  # posicion del horizonte (si hay BH)
    theta: float = 0.0           # exponente de hyperscaling
    z_dyn: float = 1.0           # exponente dinamico de Lifshitz
    deformation: float = 0.0     # deformacion generica de A(z)
    L: float = 1.0               # escala AdS
    # ── Tier A: campos de metadata canónica extra ──────────────────────────
    charge_Q: float = 0.0        # carga eléctrica adimensional (rn_ads, charged_hvlif)
    lambda_gb: float = 0.0       # acoplamiento Gauss-Bonnet (gauss_bonnet)
    m_g: float = 0.0             # masa del gravitón (massive_gravity)
    mg_c1: float = 1.0           # coeficiente c1 del potencial de masa (massive_gravity)
    mg_c2: float = 0.0           # coeficiente c2 del potencial de masa (massive_gravity)
    alpha_axion: float = 0.0     # pendiente del axión lineal (linear_axion)
    mu_GR: float = 0.0           # parámetro efectivo del toy Gubser-Rocha
    kappa_sw: float = 0.0        # escala de confinamiento soft-wall (Batell-Gherghetta)
    metadata: Dict = field(default_factory=dict)

    # ---------- Warp factor y blackening (toy) ----------

    def warp_factor(self, z: np.ndarray) -> np.ndarray:
        """
        A(z) tal que:
            ds² = e^{2A(z)} [ -f(z) dt² + dx_i² ] + dz² / f(z)
        Implementacion toy distinta por family.
        """
        eps = 1e-6
        z = np.clip(z, eps, None)

        if self.family == "ads":
            # AdS_{d+1} puro
            return -np.log(z / self.L)

        elif self.family == "lifshitz":
            # Lifshitz: parte espacial ~ AdS
            return -np.log(z / self.L)

        elif self.family == "hyperscaling":
            # HV: ds² ~ z^{-2(d-θ)/d}(...)
            return -(1.0 - self.theta / self.d) * np.log(z / self.L)

        elif self.family == "deformed":
            base = -np.log(z / self.L)
            deform = self.deformation * (z / self.L) ** 2
            return base + deform

        elif self.family == "dpbrane":
            # Dp-brane near-horizon (AGMOO Sec. 6.1.3)
            # La métrica near-horizon tiene la forma:
            #   ds² = H^{-1/2} dx_∥² + H^{1/2} (dr² + r²dΩ²)
            # donde H ~ (L/r)^{7-p} para p ≠ 3
            # En nuestra coordenada z ~ 1/r, y usando z_dyn como (7-p)/2:
            #   A(z) ~ -z_dyn * log(z/L)
            # Para D3-branas (p=3): z_dyn=2 recupera AdS₅
            # Para D2-branas (p=2): z_dyn=5/2
            # Para D4-branas (p=4): z_dyn=3/2
            effective_exp = self.z_dyn  # z_dyn codifica (7-p)/2
            return -effective_exp * np.log(z / self.L)

        # ── Tier A ────────────────────────────────────────────────────────────

        elif self.family == "rn_ads":
            # RN-AdS: misma A(z) que AdS puro; la carga solo entra en f(z).
            return -np.log(z / self.L)

        elif self.family == "gauss_bonnet":
            # GB: corrección perturbativa al warp factor.
            # Leading-order: A(z) = -(1 - lambda_gb/2)*log(z/L)
            correction = 1.0 - 0.5 * self.lambda_gb
            return -correction * np.log(z / self.L)

        elif self.family == "massive_gravity":
            # Massive gravity: A(z) = -log(z/L) como AdS (la masa entra en f).
            return -np.log(z / self.L)

        elif self.family == "linear_axion":
            # Linear axion: misma A(z) que AdS; el axión solo afecta f(z).
            return -np.log(z / self.L)

        elif self.family == "charged_hvlif":
            # Charged HV-Lifshitz: misma A(z) que hyperscaling.
            return -(1.0 - self.theta / self.d) * np.log(z / self.L)

        elif self.family == "gubser_rocha":
            # Gubser-Rocha toy: A(z) = -log(z/L) - (1/4)*log(1 + mu_GR * z/L)
            # UV (z->0): AdS puro. IR: corrección log del dilatón corriendo.
            # mu_GR = 0 reduce exactamente a AdS en A(z).
            base = -np.log(z / self.L)
            return base - 0.25 * np.log1p(self.mu_GR * z / self.L)

        elif self.family == "soft_wall":
            # Soft-wall backreacted (Batell-Gherghetta, Einstein frame):
            # A(z) = -log(z/L) - (kappa_sw/2) * (z/L)^2
            # UV: AdS puro. IR: deformación cuadrática -> Regge lineal.
            base = -np.log(z / self.L)
            return base - 0.5 * self.kappa_sw * (z / self.L) ** 2

        else:  # "unknown"
            base = -np.log(z / self.L)
            deform = self.deformation * np.sin(z / (self.L + 1e-3))
            return base + deform

    def blackening_factor(self, z: np.ndarray) -> np.ndarray:
        """
        f(z) que codifica horizonte/temperatura.
        """
        if self.z_h is None or self.z_h <= 0:
            return np.ones_like(z)

        ratio = np.clip(z / self.z_h, 0.0, 1.0)

        if self.family == "ads":
            return np.clip(1.0 - ratio ** self.d, 0.0, 1.0)
        elif self.family == "lifshitz":
            return np.clip(1.0 - ratio ** (self.d + self.z_dyn - 1), 0.0, 1.0)
        elif self.family == "hyperscaling":
            eff_d = max(1.0, self.d - self.theta)
            return np.clip(1.0 - ratio ** eff_d, 0.0, 1.0)
        elif self.family == "dpbrane":
            # Para Dp-branas, el exponente depende de p y d
            # Usamos z_dyn como proxy para (7-p)/2
            eff_exp = max(1.0, 2 * self.z_dyn)
            return np.clip(1.0 - ratio ** eff_exp, 0.0, 1.0)

        # ── Tier A ────────────────────────────────────────────────────────────

        elif self.family == "rn_ads":
            # RN-AdS: f(z) = 1 - (1+q²)(z/z_h)^d + q²(z/z_h)^{2(d-1)}
            # Satisface f(0)=1, f(z_h)=0 exactamente.
            q = self.charge_Q
            term1 = (1.0 + q * q) * ratio ** self.d
            term2 = q * q * ratio ** (2 * (self.d - 1))
            return np.clip(1.0 - term1 + term2, 0.0, 1.0)

        elif self.family == "gauss_bonnet":
            # GB toy: exponent efectivo d + lambda_gb.
            # Satisface f(0)=1, f(z_h)=0.
            eff_exp = max(1.0, float(self.d) + self.lambda_gb)
            return np.clip(1.0 - ratio ** eff_exp, 0.0, 1.0)

        elif self.family == "massive_gravity":
            # Massive gravity (Vegh-type) toy:
            # f(z) = 1 - (1 - m_g²*z_h²)(z/z_h)^d - m_g²*z²
            # Satisface f(0)=1, f(z_h)=0.
            mg2 = self.m_g * self.m_g * self.mg_c1
            coeff = 1.0 - mg2 * self.z_h * self.z_h
            term1 = coeff * ratio ** self.d
            term2 = mg2 * (z / self.z_h) ** 2 * self.z_h ** 2 * ratio ** 0  # m_g²·z²
            # rewrite: term2 = mg2 * z² → using z = ratio*z_h
            term2 = mg2 * (ratio * self.z_h) ** 2
            return np.clip(1.0 - term1 - term2, 0.0, 1.0)

        elif self.family == "linear_axion":
            # Linear axion toy:
            # f(z) = 1 - (1 + alpha²*z_h²/d)(z/z_h)^d + alpha²*z²/d
            # Satisface f(0)=1, f(z_h)=0.
            a2 = self.alpha_axion * self.alpha_axion
            coeff = 1.0 + a2 * self.z_h * self.z_h / float(self.d)
            term1 = coeff * ratio ** self.d
            term2 = a2 * (ratio * self.z_h) ** 2 / float(self.d)
            return np.clip(1.0 - term1 + term2, 0.0, 1.0)

        elif self.family == "charged_hvlif":
            # Charged HV-Lifshitz: como hyperscaling pero con carga.
            # f(z) = 1 - (1+q²)(z/z_h)^{eff_d} + q²(z/z_h)^{2(eff_d-1)}
            eff_d = max(1.0, float(self.d) - self.theta)
            q = self.charge_Q
            term1 = (1.0 + q * q) * ratio ** eff_d
            term2 = q * q * ratio ** (2.0 * (eff_d - 1.0))
            return np.clip(1.0 - term1 + term2, 0.0, 1.0)

        elif self.family == "gubser_rocha":
            # GR toy: f(z) = [1 - (z/z_h)^d] / (1 + mu_GR * z/z_h)
            # f(0)=1, f(z_h)=0. mu_GR=0 -> AdS-Schwarzschild.
            # Pendiente en horizonte: |f'(z_h)| = d / (z_h * (1 + mu_GR)).
            denom = 1.0 + self.mu_GR * ratio
            # denom > 0 garantizado si mu_GR > -1 (guardrail)
            denom = np.where(denom > 1e-6, denom, 1e-6)
            num = 1.0 - ratio ** self.d
            return np.clip(num / denom, 0.0, 1.0)

        elif self.family == "soft_wall":
            # Soft-wall: blackening puro tipo AdS-Schwarzschild.
            # Toda la física distintiva entra por el warp factor.
            return np.clip(1.0 - ratio ** self.d, 0.0, 1.0)

        else:
            return np.clip(1.0 - ratio ** 4, 0.0, 1.0)

    def ricci_scalar(self, z: np.ndarray) -> np.ndarray:
        """
        Escalar de Ricci R(z) aproximado numericamente a partir de A(z), f(z).
        Para AdS puro fijamos el valor constante exacto.
        """
        eps = 1e-4
        z = np.clip(z, eps, None)

        A = self.warp_factor(z)
        f = self.blackening_factor(z)

        if len(z) > 1:
            dz = z[1] - z[0]
        else:
            dz = eps

        dA = np.gradient(A, dz)
        d2A = np.gradient(dA, dz)
        df = np.gradient(f, dz)

        D = self.d + 1
        R = -2 * D * d2A - D * (D - 1) * dA ** 2 - (df * dA) / (f + 1e-10)

        if self.family == "ads":
            R_ads = -self.d * (self.d + 1) / (self.L ** 2)
            R = np.full_like(z, R_ads)

        return R

    def einstein_tensor_trace(self, z: np.ndarray) -> np.ndarray:
        """
        Traza del tensor de Einstein:
        """
        D = self.d + 1
        R = self.ricci_scalar(z)
        return (1.0 - D / 2.0) * R

    def effective_central_charge(self, n_points: int = 256) -> float:
        """
        Observable de borde tipo "central charge" toy.

        Definimos un escalar
            c_eff ∼ ∫ e^{(d-1) A(z)} dz

        integrado desde el UV hasta el horizonte (si existe) o hasta una
        escala IR tipica ~ L en geometrias sin horizonte.

        Este observable se usara solo como dato de boundary (visible al learner)
        y condensa informacion global sobre la forma de A(z) sin exponer A(z)
        punto a punto.
        """
        eps = 1e-4

        if self.z_h is not None and self.z_h > 0:
            z_max = float(self.z_h)
        else:
            # En geometrias sin horizonte usamos una escala IR razonable.
            z_max = float(self.L if self.L > 0 else 1.0)

        z = np.linspace(eps, z_max, n_points)
        A = self.warp_factor(z)

        integrand = np.exp((self.d - 1) * A)
        c_eff = float(np.trapezoid(integrand, z))
        return c_eff

# ============================================================
#  METADATA AGMOO: clasificación y tipo de correlador
# ============================================================

def get_ads_metadata_for_geometry(
    geo: HiddenGeometry,
    ads_boundary_mode: str = "toy",
    gkpw_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Retorna la metadata AGMOO para una geometría.

    Para familia ``ads``:
      - ``ads_classification``: sub-clasificación derivada del código
        (ads_thermal | ads_deformed | ads_toy_boundary | None si no es ads)
      - ``correlator_type``: tipo de correlador del observable de frontera.
        Actualmente siempre GEODESIC_APPROXIMATION, pues generate_boundary_data
        llama a correlator_2pt_geodesic para todos los G2.

    Para otras familias solo se emite ``correlator_type`` (el correlador
    geodésico es el mismo para todas las familias en este repo).
    """
    if geo.family == "ads" and ads_boundary_mode == "gkpw":
        correlator_type = GKPW_ADS_CORRELATOR_TYPE
    else:
        correlator_type = get_correlator_type_for_geometry(geo.family, use_geodesic=True)
    ads_cls: Optional[str] = None
    if geo.family == "ads":
        ads_cls = classify_ads_geometry(geo.family, geo.z_h, geo.deformation)
    result: Dict[str, Any] = {
        "correlator_type": correlator_type,
        "classification": ads_cls,
        "ads_classification": ads_cls,
    }
    if geo.family == "ads":
        result["ads_boundary_mode"] = ads_boundary_mode
        result["ads_pipeline_tier"] = "canonical" if ads_boundary_mode == "gkpw" else "experimental"
    if gkpw_meta:
        result.update(gkpw_meta)
    return result


def build_ads_gkpw_run_summary(manifest: Dict[str, Any]) -> Dict[str, Any]:
    ads_entries = [entry for entry in manifest.get("geometries", []) if entry.get("family") == "ads"]
    items: List[Dict[str, Any]] = []
    for entry in ads_entries:
        gate6_complete = all(entry.get(field) is not None for field in GKPW_GATE6_REQUIRED_FIELDS)
        validation_entry = dict(entry)
        operators = validation_entry.get("operators", [])
        if operators and all(isinstance(op, str) for op in operators):
            validation_entry["operators"] = [
                {
                    "name": validation_entry.get("operator_name", operators[0]),
                    "Delta": validation_entry.get("Delta"),
                    "m2L2": validation_entry.get("m2L2"),
                }
            ]
        validation = (
            validate_ads_geometry(validation_entry)
            if validate_ads_geometry is not None
            else {"overall_verdict": "AGMOO_VALIDATOR_UNAVAILABLE"}
        )
        items.append(
            {
                "name": entry.get("name"),
                "file": entry.get("file"),
                "ads_pipeline_tier": entry.get("ads_pipeline_tier"),
                "ads_boundary_mode": entry.get("ads_boundary_mode"),
                "correlator_type": entry.get("correlator_type"),
                "classification": entry.get("classification"),
                "gate6_complete": gate6_complete,
                "bf_bound_pass": bool(entry.get("bf_bound_pass", False)),
                "agmoo_verdict": validation.get("overall_verdict"),
                "reproducibility_hash": entry.get("reproducibility_hash"),
                "config_hash": entry.get("config_hash"),
            }
        )

    canonical = [item for item in items if item.get("ads_pipeline_tier") == "canonical"]
    canonical_ok = all(
        item.get("gate6_complete")
        and item.get("correlator_type") == GKPW_ADS_CORRELATOR_TYPE
        and item.get("agmoo_verdict") in {
            "ADS_HOLOGRAPHIC_STRONG_PASS",
            "ADS_HOLOGRAPHIC_PARTIAL_PASS",
        }
        for item in canonical
    )
    return {
        "summary_type": "ads_gkpw_migration_contract",
        "ads_count": len(items),
        "canonical_ads_count": len(canonical),
        "canonical_ads_contract_pass": bool(canonical_ok),
        "required_gate6_fields": list(GKPW_GATE6_REQUIRED_FIELDS),
        "items": items,
    }


# ============================================================
#  GEOMETRÍA BASE
# ============================================================

def get_phase11_geometries() -> List[Tuple[HiddenGeometry, str]]:
    """
    prototypes de geometria (base) para la Fase XI.
    Cada una se clonara con jitter para generar multiples universes.
    """
    geos: List[Tuple[HiddenGeometry, str]] = []

    # --- known ---
    geos.append((
        HiddenGeometry(
            name="ads_d3_Tfinite",
            family="ads",
            category="known",
            d=3,
            z_h=1.0,
            theta=0.0,
            z_dyn=1.0,
            deformation=0.0,
            L=1.0,
            metadata={"description": "AdS_4-Schwarzschild toy"}
        ),
        "known",
    ))

    # --- test (control positivo AdS) ---
    geos.append((
        HiddenGeometry(
            name="ads_d3_Tfinite_test",
            family="ads",
            category="test",
            d=3,
            z_h=1.0,
            theta=0.0,
            z_dyn=1.0,
            deformation=0.0,
            L=1.0,
            metadata={"description": "AdS_4-Schwarzschild toy (test)"}
        ),
        "test",
    ))

    geos.append((
        HiddenGeometry(
            name="lifshitz_d3_z2",
            family="lifshitz",
            category="known",
            d=3,
            z_h=1.0,
            theta=0.0,
            z_dyn=2.0,
            deformation=0.0,
            L=1.0,
            metadata={"description": "Lifshitz z=2, d=3"}
        ),
        "known",
    ))

    geos.append((
        HiddenGeometry(
            name="hvlf_d3_theta1",
            family="hyperscaling",
            category="known",
            d=3,
            z_h=1.2,
            theta=1.0,
            z_dyn=1.0,
            deformation=0.0,
            L=1.0,
            metadata={"description": "HV-Lifshitz theta=1, d=3"}
        ),
        "known",
    ))

    # --- test ---
    geos.append((
        HiddenGeometry(
            name="ads_deformed_d3",
            family="deformed",
            category="known",
            d=3,
            z_h=0.8,
            theta=0.0,
            z_dyn=1.0,
            deformation=0.5,
            L=1.0,
            metadata={"description": "AdS deformado suave"}
        ),
        "known",
    ))

    geos.append((
        HiddenGeometry(
            name="lifshitz_deformed_d3",
            family="lifshitz",
            category="test",
            d=3,
            z_h=1.1,
            theta=0.3,
            z_dyn=1.5,
            deformation=0.15,
            L=1.0,
            metadata={"description": "Lifshitz deformado, z≈1.5"}
        ),
        "test",
    ))

    # --- deformed test ---
    geos.append((
        HiddenGeometry(
            name="ads_deformed_d3_test",
            family="deformed",
            category="test",
            d=3,
            z_h=0.8,
            theta=0.0,
            z_dyn=1.0,
            deformation=0.5,
            L=1.0,
            metadata={"description": "AdS deformado suave (test)"}
        ),
        "test",
    ))
    # --- unknown ---
    geos.append((
        HiddenGeometry(
            name="unknown_family_1",
            family="unknown",
            category="unknown",
            d=3,
            z_h=1.0,
            theta=0.5,
            z_dyn=1.3,
            deformation=0.3,
            L=1.0,
            metadata={"description": "family desconocida 1"}
        ),
        "unknown",
    ))

    geos.append((
        HiddenGeometry(
            name="unknown_family_2",
            family="unknown",
            category="unknown",
            d=4,
            z_h=1.3,
            theta=0.2,
            z_dyn=1.1,
            deformation=0.4,
            L=1.0,
            metadata={"description": "family desconocida 2"}
        ),
        "unknown",
    ))

    # --- Dp-branas (AGMOO Sec. 6.1.3) ---
    # D3-brana: z_dyn=2 (recupera AdS₅)
    geos.append((
        HiddenGeometry(
            name="d3brane_d4",
            family="dpbrane",
            category="known",
            d=4,
            z_h=1.0,
            theta=0.0,
            z_dyn=1.0,  # Corregido: A = -ln(z) para AdS₅
            deformation=0.0,
            L=1.0,
            metadata={
                "description": "D3-brane near-horizon (AdS₅×S⁵)",
                "p": 3,
                "theory_ref": "AGMOO Sec. 6.1.3"
            }
        ),
        "known",
    ))

    # D2-brana: z_dyn=2.5 (no conformal)
    geos.append((
        HiddenGeometry(
            name="d2brane_d3",
            family="dpbrane",
            category="test",
            d=3,
            z_h=1.0,
            theta=0.0,
            z_dyn=2.5,  # (7-2)/2 = 2.5
            deformation=0.0,
            L=1.0,
            metadata={
                "description": "D2-brane near-horizon (no conformal)",
                "p": 2,
                "theory_ref": "AGMOO Sec. 6.1.3"
            }
        ),
        "test",
    ))

    # D4-brana: z_dyn=1.5 (no conformal)
    geos.append((
        HiddenGeometry(
            name="d4brane_d5",
            family="dpbrane",
            category="test",
            d=5,
            z_h=1.0,
            theta=0.0,
            z_dyn=1.5,  # (7-4)/2 = 1.5
            deformation=0.0,
            L=1.0,
            metadata={
                "description": "D4-brane near-horizon (no conformal)",
                "p": 4,
                "theory_ref": "AGMOO Sec. 6.1.3"
            }
        ),
        "test",
    ))

    # ── TIER A: RN-AdS ────────────────────────────────────────────────────────
    # Reissner-Nordström AdS_4 (d=3, carga moderada)
    geos.append((
        HiddenGeometry(
            name="rn_ads_d3_q05",
            family="rn_ads",
            category="known",
            d=3,
            z_h=1.0,
            theta=0.0,
            z_dyn=1.0,
            deformation=0.0,
            L=1.0,
            charge_Q=0.5,
            metadata={
                "description": "RN-AdS_4 con carga Q=0.5 (BH no extremal)",
                "theory_ref": "Hartnoll et al., Science of Black Holes (2016)",
            }
        ),
        "known",
    ))
    # RN-AdS_5 (d=4) — carga baja para control
    geos.append((
        HiddenGeometry(
            name="rn_ads_d4_q02",
            family="rn_ads",
            category="test",
            d=4,
            z_h=1.0,
            theta=0.0,
            z_dyn=1.0,
            deformation=0.0,
            L=1.0,
            charge_Q=0.2,
            metadata={
                "description": "RN-AdS_5 con carga Q=0.2 (carga baja, test)",
            }
        ),
        "test",
    ))

    # ── TIER A: Gauss-Bonnet AdS ──────────────────────────────────────────────
    geos.append((
        HiddenGeometry(
            name="gauss_bonnet_d4_lp2",
            family="gauss_bonnet",
            category="known",
            d=4,
            z_h=1.0,
            theta=0.0,
            z_dyn=1.0,
            deformation=0.0,
            L=1.0,
            lambda_gb=0.2,
            metadata={
                "description": "GB-AdS_5 con lambda_GB=0.2 (d>=4 requerido)",
                "theory_ref": "Brigante et al., PRL 100 (2008)",
                "guardrail": "d>=4, lambda_gb < 0.25",
            }
        ),
        "known",
    ))
    geos.append((
        HiddenGeometry(
            name="gauss_bonnet_d4_lm1",
            family="gauss_bonnet",
            category="test",
            d=4,
            z_h=1.0,
            theta=0.0,
            z_dyn=1.0,
            deformation=0.0,
            L=1.0,
            lambda_gb=-0.1,
            metadata={
                "description": "GB-AdS_5 con lambda_GB=-0.1 (acoplamiento negativo, test)",
            }
        ),
        "test",
    ))

    # ── TIER A: Massive gravity AdS ───────────────────────────────────────────
    geos.append((
        HiddenGeometry(
            name="massive_gravity_d3_mg03",
            family="massive_gravity",
            category="known",
            d=3,
            z_h=1.0,
            theta=0.0,
            z_dyn=1.0,
            deformation=0.0,
            L=1.0,
            m_g=0.3,
            mg_c1=1.0,
            mg_c2=0.0,
            metadata={
                "description": "Massive gravity AdS_4, m_g=0.3 (disipación de momento)",
                "theory_ref": "Vegh, arXiv:1301.0537; Blake & Tong, PRD 88 (2013)",
            }
        ),
        "known",
    ))
    geos.append((
        HiddenGeometry(
            name="massive_gravity_d4_mg05",
            family="massive_gravity",
            category="test",
            d=4,
            z_h=1.0,
            theta=0.0,
            z_dyn=1.0,
            deformation=0.0,
            L=1.0,
            m_g=0.5,
            mg_c1=1.0,
            mg_c2=0.0,
            metadata={
                "description": "Massive gravity AdS_5, m_g=0.5 (test d=4)",
            }
        ),
        "test",
    ))

    # ── TIER A: Linear axion ──────────────────────────────────────────────────
    geos.append((
        HiddenGeometry(
            name="linear_axion_d3_a05",
            family="linear_axion",
            category="known",
            d=3,
            z_h=1.0,
            theta=0.0,
            z_dyn=1.0,
            deformation=0.0,
            L=1.0,
            alpha_axion=0.5,
            metadata={
                "description": "Linear axion AdS_4, alpha=0.5 (metal incoherente leve)",
                "theory_ref": "Andrade & Withers, JHEP 2014",
            }
        ),
        "known",
    ))
    geos.append((
        HiddenGeometry(
            name="linear_axion_d3_a10",
            family="linear_axion",
            category="test",
            d=3,
            z_h=1.0,
            theta=0.0,
            z_dyn=1.0,
            deformation=0.0,
            L=1.0,
            alpha_axion=1.0,
            metadata={
                "description": "Linear axion AdS_4, alpha=1.0 (metal incoherente fuerte, test)",
            }
        ),
        "test",
    ))

    # ── TIER A: Charged hvLif ─────────────────────────────────────────────────
    geos.append((
        HiddenGeometry(
            name="charged_hvlif_d3_theta1_q04",
            family="charged_hvlif",
            category="known",
            d=3,
            z_h=1.2,
            theta=1.0,
            z_dyn=1.5,
            deformation=0.0,
            L=1.0,
            charge_Q=0.4,
            metadata={
                "description": "Charged HV-Lifshitz, theta=1, z_dyn=1.5, Q=0.4",
                "theory_ref": "Charmousis et al., JHEP 2010 (EMD)",
            }
        ),
        "known",
    ))
    geos.append((
        HiddenGeometry(
            name="charged_hvlif_d4_theta05_q03",
            family="charged_hvlif",
            category="test",
            d=4,
            z_h=1.0,
            theta=0.5,
            z_dyn=2.0,
            deformation=0.0,
            L=1.0,
            charge_Q=0.3,
            metadata={
                "description": "Charged HV-Lifshitz, d=4, theta=0.5, z_dyn=2, Q=0.3 (test)",
            }
        ),
        "test",
    ))

    # ── TIER A ext (2026-04): Gubser-Rocha ────────────────────────────────────
    geos.append((
        HiddenGeometry(
            name="gubser_rocha_d3_mu05",
            family="gubser_rocha",
            category="known",
            d=3,
            z_h=1.0,
            theta=0.0,
            z_dyn=1.0,
            deformation=0.0,
            L=1.0,
            mu_GR=0.5,
            metadata={
                "description": "Gubser-Rocha toy (EMD), d=3, mu=0.5 (strange metal)",
                "theory_ref": "Gubser-Rocha arXiv:0911.2898; Davison-Schalm-Zaanen arXiv:1311.2451",
                "guardrail": "mu_GR > -1 (denom > 0)",
            }
        ),
        "known",
    ))
    geos.append((
        HiddenGeometry(
            name="gubser_rocha_d4_mu08",
            family="gubser_rocha",
            category="test",
            d=4,
            z_h=1.0,
            theta=0.0,
            z_dyn=1.0,
            deformation=0.0,
            L=1.0,
            mu_GR=0.8,
            metadata={
                "description": "Gubser-Rocha toy, d=4, mu=0.8 (test)",
            }
        ),
        "test",
    ))

    # ── TIER A ext (2026-04): Soft-wall backreacted ───────────────────────────
    geos.append((
        HiddenGeometry(
            name="soft_wall_d3_k10",
            family="soft_wall",
            category="known",
            d=3,
            z_h=1.0,
            theta=0.0,
            z_dyn=1.0,
            deformation=0.0,
            L=1.0,
            kappa_sw=1.0,
            metadata={
                "description": "Soft-wall backreacted (Batell-Gherghetta), d=3, kappa=1.0",
                "theory_ref": "Batell-Gherghetta arXiv:0801.4383; He-Huang-Yan arXiv:1104.0940",
            }
        ),
        "known",
    ))
    geos.append((
        HiddenGeometry(
            name="soft_wall_d4_k05",
            family="soft_wall",
            category="test",
            d=4,
            z_h=1.0,
            theta=0.0,
            z_dyn=1.0,
            deformation=0.0,
            L=1.0,
            kappa_sw=0.5,
            metadata={
                "description": "Soft-wall backreacted, d=4, kappa=0.5 (test)",
            }
        ),
        "test",
    ))

    return geos


@dataclass(frozen=True)
class FocusedSamplingConfig:
    enabled: bool = False
    families: Tuple[str, ...] = ("ads", "lifshitz", "hyperscaling")
    d: int = 4
    zh_min: float = 1.0
    zh_max: float = 1.2
    out_of_support_frac: float = 0.0
    out_of_support_zh_min: float = 0.8
    out_of_support_zh_max: float = 2.0


DEFAULT_FOCUSED_FAMILIES: Tuple[str, ...] = ("ads", "lifshitz", "hyperscaling")


def jitter_geometry(
    base: HiddenGeometry,
    rng: np.random.Generator,
    z_h_jitter: float = 0.1,
    theta_jitter: float = 0.2,
    z_dyn_jitter: float = 0.3,
    deformation_jitter: float = 0.2,
) -> HiddenGeometry:
    """
    Copia la geometria base con ligeras variaciones de parametros.
    Sirve para generar muchos universes por family sin colapsar al learner
    en unos pocos casos finitos.
    """
    geo = HiddenGeometry(**asdict(base))

    if geo.z_h is not None:
        zh_factor = 1.0 + z_h_jitter * (2 * rng.random() - 1)
        geo.z_h = max(0.3, geo.z_h * zh_factor)

    geo.theta = geo.theta + theta_jitter * (2 * rng.random() - 1)
    geo.z_dyn = max(0.5, geo.z_dyn + z_dyn_jitter * (2 * rng.random() - 1))
    geo.deformation = geo.deformation + deformation_jitter * (2 * rng.random() - 1)

    geo.metadata["jittered"] = True
    return geo


# ============================================================
#  operators Y CORRELADORES EN EL BOUNDARY
# ============================================================

def generate_operators_for_geometry(
    geo: HiddenGeometry,
    n_ops: int,
    rng: np.random.Generator,
) -> List[Dict]:
    """
    Espectro toy de operators escalares O_i
    """
    deltas = np.sort(geo.d / 2 + 0.5 + 2.0 * rng.random(n_ops))
    ops: List[Dict] = []

    for i, Delta in enumerate(deltas):
        # Relacion masa-dimension AdS_{d+1}: m²L² = Δ(Δ-d)
        m2L2 = float(Delta * (Delta - geo.d))
        ops.append(
            {
                "name": f"O{i+1}",
                "Delta": float(Delta),
                "m2L2": m2L2,
                "spin": 0,
            }
        )

    return ops


def correlator_2pt_thermal(
    x: np.ndarray,
    Delta: float,
    d: int,
    T: float,
) -> np.ndarray:
    """
    <O(x)O(0)> a temperatura T:
        T = 0: G2 ~ 1/|x|^{2Δ}
        T > 0: G2 ~ (πT / sinh(πT x))^{2Δ}
    """
    x = np.asarray(x)
    x_safe = np.maximum(np.abs(x), 1e-8)
    prefactor = 1.0

    if T < 1e-12:
        return prefactor / (x_safe ** (2 * Delta))
    else:
        arg = np.pi * T * x_safe
        arg = np.clip(arg, 1e-6, 50.0)
        return prefactor * (np.pi * T / np.sinh(arg)) ** (2 * Delta)


def correlator_2pt_geodesic(
    x_grid: np.ndarray,
    Delta: float,
    geo: "HiddenGeometry",
    n_z_star: int = 30,
) -> np.ndarray:
    """
    Correlador holografico usando aproximacion de geodesica (AGMOO Sec. 3.5):
        G2(r) ~ exp(-Delta * L_reg(r))
    
    Donde L_reg(r) es la longitud de geodesica regularizada, que DEPENDE de A(z) y f(z).
    
    Parametros:
        x_grid: distancias en el boundary
        Delta: dimension conforme del operador
        geo: geometria (para acceder a A(z), f(z))
        n_z_star: numero de puntos de turning para muestrear
    
    Justificacion post-hoc: AGMOO Sec. 3.5.1 (Wilson loops y superficies minimas)
    Esta funcion hace que G2 dependa de la geometria bulk, lo cual es fisicamente correcto.
    El learner NO ve A(z) directamente - solo ve G2.
    
    Anadido 2024-12-30 para resolver el problema de que G2 no dependia de A(z).
    """
    from scipy.interpolate import interp1d
    from scipy.integrate import quad
    
    z_h = geo.z_h if geo.z_h is not None and geo.z_h > 0 else 1.0
    # V4 fix: epsilon más grande para evitar problemas de interpolación
    eps = 1e-4 * z_h
    
    # Grid de z para A(z), f(z) - empezar antes de eps
    z_min = eps * 0.5
    z_dense = np.linspace(z_min, 0.999 * z_h, 500)
    A_dense = geo.warp_factor(z_dense)
    f_dense = geo.blackening_factor(z_dense)
    
    # V4 fix: interpolación lineal para mejor comportamiento en bordes
    A_interp = interp1d(z_dense, A_dense, kind='linear', fill_value='extrapolate')
    f_interp = interp1d(z_dense, f_dense, kind='linear', fill_value='extrapolate')
    
    # Muestrear turning points z*
    z_star_grid = np.linspace(0.05 * z_h, 0.85 * z_h, n_z_star)
    r_computed = []
    L_computed = []
    
    for z_star in z_star_grid:
        A_star = float(A_interp(z_star))
        
        def integrand_r(z):
            """dx/dz = 1 / sqrt(f * (e^{2(A-A*)} - 1)) [V4 corregido]"""
            if z >= z_star - 1e-10:
                return 0.0
            A_z = float(A_interp(z))
            f_z = max(float(f_interp(z)), 1e-10)
            exp_diff = np.exp(2 * (A_z - A_star)) - 1.0
            if exp_diff <= 1e-12:
                return 0.0
            # V4 fix: sin e^{-A} en el numerador
            return 1.0 / np.sqrt(f_z * exp_diff)
        
        def integrand_L(z):
            """ds/dz = e^{2A-A*} / sqrt(f * (e^{2(A-A*)}-1)) [V4 corregido]"""
            if z >= z_star - 1e-10:
                return 0.0
            A_z = float(A_interp(z))
            f_z = max(float(f_interp(z)), 1e-10)
            exp_diff = np.exp(2 * (A_z - A_star)) - 1.0
            if exp_diff <= 1e-12:
                return 0.0
            # V4 fix: numerador e^{2A - A*}
            return np.exp(2*A_z - A_star) / np.sqrt(f_z * exp_diff)
        
        try:
            z_upper = z_star * 0.9999
            r_half, _ = quad(integrand_r, eps, z_upper, limit=200)
            L_half, _ = quad(integrand_L, eps, z_upper, limit=200)
            if np.isfinite(r_half) and np.isfinite(L_half) and r_half > 0:
                r_val = 2 * r_half
                L_total = 2 * L_half
                # V4 fix: regularización L_reg = L_total - L_div
                L_div = -2.0 * np.log(eps)
                L_reg = L_total - L_div
                # Sanity check
                if L_reg > -10 and L_reg < 30:
                    r_computed.append(r_val)
                    L_computed.append(L_reg)
        except Exception:
            continue
    
    if len(r_computed) < 3:
        # Fallback al correlador termico si falla el calculo geodesico
        T = geo.d / (4.0 * np.pi * z_h) if z_h > 0 else 0.0
        return correlator_2pt_thermal(x_grid, Delta, geo.d, T)
    
    # Interpolar L(r)
    r_arr = np.array(r_computed)
    L_arr = np.array(L_computed)
    sort_idx = np.argsort(r_arr)
    r_sorted = r_arr[sort_idx]
    L_sorted = L_arr[sort_idx]
    
    # Extender rango si es necesario
    r_min, r_max = r_sorted[0], r_sorted[-1]
    
    try:
        L_interp = interp1d(r_sorted, L_sorted, kind='cubic', 
                           bounds_error=False, fill_value='extrapolate')
    except Exception:
        T = geo.d / (4.0 * np.pi * z_h) if z_h > 0 else 0.0
        return correlator_2pt_thermal(x_grid, Delta, geo.d, T)
    
    # Calcular G2
    x_clipped = np.clip(x_grid, r_min * 0.9, r_max * 1.1)
    L_x = L_interp(x_clipped)
    G2 = np.exp(-Delta * np.clip(L_x, -50, 50))
    
    # Normalizar
    G2 = G2 / np.max(G2) if np.max(G2) > 0 else G2
    
    return G2.astype(np.float32)


def _compute_temperature(geo: HiddenGeometry) -> float:
    if geo.z_h is not None and geo.z_h > 0:
        return float(geo.d) / (4.0 * np.pi * float(geo.z_h))
    return 0.0


def _gkpw_config_from_operator(op: Dict[str, Any]) -> Any:
    if GKPWConfig is None:
        raise RuntimeError("GKPWConfig no disponible; no se puede activar ads_boundary_mode=gkpw")
    return GKPWConfig(
        m2L2=float(op["m2L2"]),
        operator_name=str(op["name"]),
        bulk_field_name=f"phi_{op['name']}",
        omega_min=0.2,
        omega_max=6.0,
        n_omega=32,
        k_min=0.0,
        k_max=2.0,
        n_k=8,
        uv_fit_points=10,
    )


def _g2_from_gkpw_spectral(
    x_grid: np.ndarray,
    omega_grid: np.ndarray,
    gr_imag: np.ndarray,
) -> np.ndarray:
    """
    Construye un G2 euclideo derivado del spectral density de G_R.

    No es una formula toy cerrada: usa la salida source/response numerica como
    entrada y aplica una representacion espectral discreta simple. La metadata
    del carril mantiene que el artefacto canonico fuerte es G_R.
    """
    spectral = np.mean(-2.0 * np.asarray(gr_imag, dtype=np.float64), axis=0)
    spectral = np.maximum(spectral, 0.0)
    if not np.any(spectral > 0.0):
        spectral = np.abs(np.mean(np.asarray(gr_imag, dtype=np.float64), axis=0))
    kernel = np.exp(-np.outer(np.asarray(x_grid, dtype=np.float64), omega_grid))
    g2 = np.trapezoid(kernel * spectral[None, :], omega_grid, axis=1)
    if not np.all(np.isfinite(g2)) or float(np.max(g2)) <= 0.0:
        raise RuntimeError("GKPW spectral G2 construction failed")
    return (g2 / np.max(g2)).astype(np.float32)


def generate_ads_gkpw_boundary_data(
    geo: HiddenGeometry,
    operators: List[Dict],
    n_samples: int,
    z_grid: np.ndarray,
) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
    if not HAS_GKPW_ADS or GKPWAdsGeometry is None or build_gkpw_ads_correlator_grid is None:
        raise RuntimeError("ads_boundary_mode=gkpw requiere tools.gkpw_ads_scalar_correlator importable")
    if not operators:
        raise RuntimeError("ads_boundary_mode=gkpw requiere al menos un operador")

    x_grid = np.linspace(0.1, 10.0, n_samples)
    A = geo.warp_factor(z_grid)
    f = geo.blackening_factor(z_grid)
    gkpw_geo = GKPWAdsGeometry(
        name=geo.name,
        family=geo.family,
        d=int(geo.d),
        z_h=geo.z_h if geo.z_h and geo.z_h > 0 else None,
        z=np.asarray(z_grid, dtype=np.float64),
        A=np.asarray(A, dtype=np.float64),
        f=np.asarray(f, dtype=np.float64),
    )

    op0 = operators[0]
    config = _gkpw_config_from_operator(op0)
    result = build_gkpw_ads_correlator_grid(gkpw_geo, config)
    meta = dict(result["metadata"])
    if gkpw_config_hash is not None:
        meta["config_hash"] = gkpw_config_hash(config, gkpw_geo.name)
    if gkpw_output_hash is not None:
        meta["reproducibility_hash"] = gkpw_output_hash(result)
    if validate_gkpw_gate6_metadata is not None:
        validate_gkpw_gate6_metadata(meta)

    data: Dict[str, np.ndarray] = {
        "x_grid": x_grid,
        "temperature": np.array([_compute_temperature(geo)], dtype=float),
        "d": np.array([geo.d], dtype=np.int32),
        "omega_grid": np.asarray(result["omega_grid"], dtype=np.float64),
        "k_grid": np.asarray(result["k_grid"], dtype=np.float64),
        "G_R_real": np.asarray(result["G_R_real"], dtype=np.float32),
        "G_R_imag": np.asarray(result["G_R_imag"], dtype=np.float32),
        "gkpw_source_real": np.asarray(result["source_real"], dtype=np.float32),
        "gkpw_source_imag": np.asarray(result["source_imag"], dtype=np.float32),
        "gkpw_response_real": np.asarray(result["response_real"], dtype=np.float32),
        "gkpw_response_imag": np.asarray(result["response_imag"], dtype=np.float32),
        "gkpw_uv_fit_residual_norm": np.asarray(result["uv_fit_residual_norm"], dtype=np.float32),
    }
    data[f"G2_{op0['name']}"] = _g2_from_gkpw_spectral(
        x_grid,
        data["omega_grid"],
        data["G_R_imag"],
    )
    for op in operators[1:]:
        data[f"G2_{op['name']}"] = data[f"G2_{op0['name']}"].copy()

    meta.update(
        {
            "classification": meta.get("classification") or classify_ads_geometry(
                geo.family, geo.z_h, geo.deformation
            ),
            "ads_boundary_mode": "gkpw",
            "ads_pipeline_tier": "canonical",
            "g2_construction": "spectral_laplace_from_gkpw_retarded_correlator",
            "gkpw_primary_operator": str(op0["name"]),
        }
    )
    return data, meta


def generate_boundary_data(
    geo: HiddenGeometry,
    operators: List[Dict],
    n_samples: int,
    rng: np.random.Generator,
    ads_boundary_mode: str = "toy",
    z_grid: Optional[np.ndarray] = None,
) -> Tuple[Dict[str, np.ndarray], Dict[str, Any]]:
    """
    Genera datos del boundary (LO ÚNICO visible al learner).

    Devuelve un dict con:
        - x_grid
        - temperature
        - G2_<O> para cada operador
        - omega_grid, k_grid, G_R_real, G_R_imag
    """
    if geo.family == "ads" and ads_boundary_mode == "gkpw":
        if z_grid is None:
            raise RuntimeError("ads_boundary_mode=gkpw requiere z_grid")
        return generate_ads_gkpw_boundary_data(geo, operators, n_samples, z_grid)

    d = geo.d

    # Temperatura aproximada a partir del horizonte
    if geo.z_h is not None and geo.z_h > 0:
        T = d / (4.0 * np.pi * geo.z_h)
    else:
        T = 0.0

    data: Dict[str, np.ndarray] = {}

    # Grid espacial
    x_grid = np.linspace(0.1, 10.0, n_samples)
    data["x_grid"] = x_grid
    data["temperature"] = np.array([T], dtype=float)
    data["x_grid"] = x_grid
    data["temperature"] = np.array([T], dtype=float)

    # Observable escalar de borde: "central charge" toy
    c_eff = geo.effective_central_charge()
    data["central_charge_eff"] = np.array([c_eff], dtype=float)

    # (opcional pero recomendable) exportar d explicito en boundary
    data["d"] = np.array([geo.d], dtype=np.int32)

    # 2-pt correlators para cada operador
    for op in operators:
        name = op["name"]
        Delta = op["Delta"]
        # V2.4: Usar correlador geodesico que depende de A(z)
        G2 = correlator_2pt_geodesic(x_grid, Delta, geo)
        data[f"G2_{name}"] = G2.astype(np.float32)

    # Respuesta lineal toy G_R(ω, k)
    omega_grid = np.linspace(0.1, 10.0, 50)
    k_grid = np.linspace(0.0, 5.0, 30)

    if T > 0:
        omega_qnm = 2 * np.pi * T * 0.5 - 1j * np.pi * T
    else:
        omega_qnm = 1.0 - 0.1j

    OMEGA, K = np.meshgrid(omega_grid, k_grid)
    G_R = 1.0 / (OMEGA - np.real(omega_qnm) - 1j * np.abs(np.imag(omega_qnm)) + 1e-3)

    data["omega_grid"] = omega_grid
    data["k_grid"] = k_grid
    data["G_R_real"] = np.real(G_R).astype(np.float32)
    data["G_R_imag"] = np.imag(G_R).astype(np.float32)

    meta = get_ads_metadata_for_geometry(geo, ads_boundary_mode="toy")
    if geo.family == "ads":
        first_op = operators[0] if operators else {"name": "O_unknown", "m2L2": np.nan, "Delta": np.nan}
        meta.update(
            {
                "ads_pipeline_tier": "experimental",
                "ads_boundary_mode": "toy",
                "gr_correlator_type": "TOY_PHENOMENOLOGICAL",
                "g2_correlator_type": "GEODESIC_APPROXIMATION",
                "bulk_field_name": "TOY_NO_BULK_FIELD",
                "operator_name": str(first_op["name"]),
                "m2L2": float(first_op["m2L2"]),
                "Delta": float(first_op["Delta"]),
                "bf_bound_pass": bool(float(first_op["m2L2"]) >= -((float(geo.d) / 2.0) ** 2)),
                "uv_source_declared": False,
                "ir_bc_declared": False,
            }
        )
    return data, meta


# ============================================================
#  BACKEND EMD (OPCIONAL)
# ============================================================

def _ricci_from_A_f(z: np.ndarray, A: np.ndarray, f: np.ndarray, d: int) -> np.ndarray:
    """
    Calcula el escalar de Ricci R para una metrica estatica plano-simetrica,
    usando el mismo esquema que HiddenGeometry.ricci_scalar pero con A,f explicitos.
    """
    D = d + 1
    if len(z) > 1:
        dz = z[1] - z[0]
    else:
        dz = 1e-3

    dA = np.gradient(A, dz)
    d2A = np.gradient(dA, dz)
    df = np.gradient(f, dz)

    R = -2.0 * D * d2A - D * (D - 1) * dA ** 2 - (df * dA) / (f + 1e-10)
    return R


def generate_lifshitz_from_emd(
    d: int,
    z_dyn: float,
    theta: float,
    r_h: float = 1.0,
    lam: float = 1.0,
    Q: float = 1.0,
    phi_h: float = 0.5,
    r_uv: float = 1e-3,
    n_points: int = 200,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Genera A(z), f(z) usando soluciones EMD reales.
    Retorna: (z_grid, A_z, f_z) en coordenada z = 1/r.
    """
    if not HAS_EMD or EMDLifshitzSolver is None:
        raise ImportError("EMDLifshitzSolver no disponible")

    solver = EMDLifshitzSolver(d=d, z=z_dyn, theta=theta, lam=lam, Q=Q, r_h=r_h)
    sol = solver.solve(phi_h=phi_h, r_uv=r_uv)

    if sol is None or getattr(sol, "success", True) is False:
        raise ValueError(f"EMD solver failed for d={d}, z={z_dyn}, θ={theta}")

    r_grid = np.asarray(sol.t)
    f_r = np.asarray(sol.y[0])

    # z = 1/r (boundary en z→0)
    z_grid = 1.0 / r_grid
    order = np.argsort(z_grid)
    z_grid = z_grid[order]
    f_z = f_r[order]

    # Warp factor compatible con Lifshitz/HV:
    # g_xx ~ z^{2θ/d} y g_tt ~ z^{-2z_dyn}, asi que:
    with np.errstate(divide="ignore"):
        A_z = (theta / d - z_dyn) * np.log(z_grid)

    return z_grid, A_z, f_z


def generate_bulk_truth(
    geo: HiddenGeometry,
    z_grid: np.ndarray,
    use_emd: bool = False,
) -> Dict[str, np.ndarray]:
    """
    Genera la "verdad" del bulk para validacion.
    El learner NO tiene acceso a esto durante el entrenamiento.

    Si use_emd=True y HAS_EMD=True y family ∈ {lifshitz,hyperscaling},
    se usa EMDLifshitzSolver como backend. En caso de fallo, hay fallback
    silencioso (con warning) al modo toy analitico.
    """
    # Por defecto: backend analitico toy
    A_truth = geo.warp_factor(z_grid)
    f_truth = geo.blackening_factor(z_grid)

    if use_emd and HAS_EMD and geo.family in ["lifshitz", "hyperscaling"]:
        try:
            z_emd, A_emd, f_emd = generate_lifshitz_from_emd(
                d=geo.d,
                z_dyn=geo.z_dyn,
                theta=geo.theta,
                r_h=geo.z_h if geo.z_h else 1.0,
            )
            # Interpola a la malla de z deseada
            A_truth = np.interp(z_grid, z_emd, A_emd)
            f_truth = np.interp(z_grid, z_emd, f_emd)
        except Exception as e:
            print(f"   [WARN] EMD fallback to toy for {geo.name}: {e}")

    # R y traza de Einstein consistentes con A,f
    R_truth = _ricci_from_A_f(z_grid, A_truth, f_truth, geo.d)
    D = geo.d + 1
    G_trace_truth = (1.0 - D / 2.0) * R_truth

    return {
        "z_grid": z_grid,
        "A_truth": A_truth,
        "f_truth": f_truth,
        "R_truth": R_truth,
        "G_trace_truth": G_trace_truth,
        "family": geo.family,
        "d": geo.d,
        "z_h": geo.z_h if geo.z_h else 0.0,
        "theta": geo.theta,
        "z_dyn": geo.z_dyn,
    }


# ============================================================
#  LOOP PRINCIPAL Y I/O
# ============================================================

def make_geometry_instance(
    base: HiddenGeometry,
    category: str,
    idx: int,
    rng: np.random.Generator,
    focused_config: Optional[FocusedSamplingConfig] = None,
) -> HiddenGeometry:
    """
    Crea una copia de `base` con nombre unico y pequenos jitters en parametros
    segun la family.

    Jitters aplicados:
    - z_h: factor multiplicativo [0.7, 1.3], clipped a [0.3, 3.0]
    - d: con prob 0.5, cambiar a otro valor en {3, 4, 5}
    - z_dyn (lifshitz): uniforme en [1.5, 3.0]
    - theta (hyperscaling): uniforme en [0.3, min(d-0.5, 2.0)]
    - deformation (deformed): uniforme en [0.05, 0.3]
    """

    # --- CONTROL EINSTEIN PURO (sin jitter) -----------------------------
    # Para las geometrias AdS puras conocidas (ads5_pure, ads4_pure)
    # queremos al menos una instancia EXACTAMENTE igual al prototipo:
    #   - z_h = None  → T = 0
    #   - family = "ads"
    #   - R(z) constante = -D(D-1)/L² (ver HiddenGeometry.ricci_scalar)
    if (
        base.family == "ads"
        and base.name in ("ads5_pure", "ads4_pure")
        and category == "known"
        and idx == 0
        and base.z_h is None
    ):
        params = asdict(base)
        params["name"] = f"{base.name}_{category}_{idx:03d}"
        return HiddenGeometry(**params)

    # --- CÓDIGO ORIGINAL DE JITTER -------------------------------------
    if focused_config is not None and focused_config.enabled:
        return make_focused_geometry_instance(base, category, idx, rng, focused_config)

    params = asdict(base)

    # Nombre unico: base_category_idx
    params["name"] = f"{base.name}_{category}_{idx:03d}"

    # Copia de trabajo
    d = params.get("d", base.d)

    # Jitters por family
    family = base.family

    # --- Horizonte ---
    z_h = params.get("z_h", base.z_h)
    if z_h is not None and z_h > 0:
        # Perturbacion suave multiplicativa
        factor = rng.uniform(0.7, 1.3)
        z_h = float(np.clip(z_h * factor, 0.3, 3.0))
    else:
        # A veces introducimos un pequeno horizonte en geometrias sin el
        if rng.random() < 0.3:
            z_h = float(rng.uniform(0.8, 2.0))
        else:
            z_h = None
    params["z_h"] = z_h

    # --- Dimension del boundary ---
    # Usamos valores razonables: 3, 4 o 5
    if rng.random() < 0.5:
        params["d"] = int(rng.choice([3, 4, 5]))
    else:
        params["d"] = int(d)

    # --- Jitters especificos por family ---
    if family == "lifshitz":
        # z_dyn > 1 tipico
        params["z_dyn"] = float(rng.uniform(1.5, 3.0))
    elif family == "hyperscaling":
        d_eff = params["d"]
        max_theta = max(0.5, min(d_eff - 0.5, 2.0))
        params["theta"] = float(rng.uniform(0.3, max_theta))
    elif family == "deformed":
        params["deformation"] = float(rng.uniform(0.05, 0.3))
    elif family == "ads":
        # Nada especial extra, ads ya se controla con d y z_h
        pass
    # ── Tier A jitters ────────────────────────────────────────────────────────
    elif family == "rn_ads":
        # Carga adimensional: 0 ≤ Q < Q_extremal ≈ sqrt(d/(d-2)).
        # Conservamos rango seguro [0.0, 0.8] para d=3.
        params["charge_Q"] = float(rng.uniform(0.0, 0.8))
    elif family == "gauss_bonnet":
        # λ ∈ [-0.2, 0.23]: límite superior < 1/4 (Causal constraint para d=4).
        params["lambda_gb"] = float(rng.uniform(-0.2, 0.23))
    elif family == "massive_gravity":
        params["m_g"] = float(rng.uniform(0.05, 0.5))
        params["mg_c1"] = float(rng.uniform(0.5, 2.0))
        params["mg_c2"] = float(rng.uniform(0.0, 0.5))
    elif family == "linear_axion":
        params["alpha_axion"] = float(rng.uniform(0.1, 1.5))
    elif family == "charged_hvlif":
        d_eff = params["d"]
        max_theta = max(0.5, min(d_eff - 0.5, 2.0))
        params["theta"] = float(rng.uniform(0.3, max_theta))
        params["z_dyn"] = float(rng.uniform(1.2, 2.5))
        params["charge_Q"] = float(rng.uniform(0.0, 0.6))
    elif family == "gubser_rocha":
        # mu_GR > -1 para mantener denominador positivo; rango físico positivo.
        params["mu_GR"] = float(rng.uniform(0.1, 1.2))
    elif family == "soft_wall":
        # kappa_sw > 0 produce deformación IR; cota superior suave para evitar
        # singularidades numéricas del warp factor cerca de z_h.
        params["kappa_sw"] = float(rng.uniform(0.2, 1.5))
    else:
        # unknown: solo tocamos z_h y d (ya hechos arriba)
        pass

    return HiddenGeometry(**params)


def sample_focused_zh(
    rng: np.random.Generator,
    config: FocusedSamplingConfig,
) -> Tuple[float, bool]:
    """
    Muestrea z_h en un soporte focalizado con una cola opcional fuera de soporte.
    """
    use_out_of_support = rng.random() < config.out_of_support_frac
    if use_out_of_support:
        side = rng.choice(["left", "right"])
        if side == "left":
            z_h = rng.uniform(config.out_of_support_zh_min, config.zh_min)
        else:
            z_h = rng.uniform(config.zh_max, config.out_of_support_zh_max)
        return float(z_h), True
    return float(rng.uniform(config.zh_min, config.zh_max)), False


def rewrite_geometry_name_for_dimension(name: str, d_value: int) -> str:
    dim_token_pattern = r"_d\d+(?=_|$)"
    if re.search(dim_token_pattern, name):
        replaced = False

        def _replace_or_drop(match: re.Match[str]) -> str:
            nonlocal replaced
            if not replaced:
                replaced = True
                return f"_d{d_value}"
            return ""

        return re.sub(dim_token_pattern, _replace_or_drop, name)
    return f"{name}_d{d_value}"


def make_focused_geometry_instance(
    base: HiddenGeometry,
    category: str,
    idx: int,
    rng: np.random.Generator,
    config: FocusedSamplingConfig,
) -> HiddenGeometry:
    """
    Variante conservadora para retarget del sandbox al régimen empírico.
    """
    params = asdict(base)
    metadata = dict(params.get("metadata") or {})

    focused_base_name = rewrite_geometry_name_for_dimension(base.name, int(config.d))
    params["name"] = f"{focused_base_name}_{category}_{idx:03d}"
    params["family"] = base.family
    params["d"] = int(config.d)

    z_h, is_out_of_support = sample_focused_zh(rng, config)
    params["z_h"] = z_h

    family = base.family
    if family == "lifshitz":
        params["z_dyn"] = float(rng.uniform(1.5, 2.5))
        params["theta"] = 0.0
        params["deformation"] = 0.0
    elif family == "hyperscaling":
        max_theta = max(0.5, min(config.d - 0.5, 2.0))
        params["theta"] = float(rng.uniform(0.3, max_theta))
        params["z_dyn"] = float(rng.uniform(1.0, 1.8))
        params["deformation"] = 0.0
    elif family == "ads":
        params["theta"] = 0.0
        params["z_dyn"] = 1.0
        params["deformation"] = 0.0

    metadata.update(
        {
            "sampling_regime": "focused_real_regime",
            "focused_family_source": base.family,
            "focused_d": int(config.d),
            "focused_zh_min": float(config.zh_min),
            "focused_zh_max": float(config.zh_max),
            "focused_out_of_support": bool(is_out_of_support),
            "focused_out_of_support_frac": float(config.out_of_support_frac),
        }
    )
    params["metadata"] = metadata
    return HiddenGeometry(**params)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fase XI v3: Generacion de datos para emergencia geometrica (escalable)"
    )
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--n-samples", type=int, default=100)
    parser.add_argument("--n-operators", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--z-max", type=float, default=5.0)
    parser.add_argument("--n-z", type=int, default=100)

    # nuevos argumentos v3
    parser.add_argument(
        "--n-known",
        type=int,
        default=20,
        help="Numero de universes por geometria base con category='known'",
    )
    parser.add_argument(
        "--n-test",
        type=int,
        default=10,
        help="Numero de universes por geometria base con category='test'",
    )
    parser.add_argument(
        "--n-unknown",
        type=int,
        default=5,
        help="Numero de universes por geometria base con category='unknown'",
    )
    parser.add_argument(
        "--use-emd-lifshitz",
        action="store_true",
        help="Usa EMDLifshitzSolver para familys lifshitz/hyperscaling si esta disponible",
    )
    parser.add_argument(
        "--ads-only",
        action="store_true",
        help=(
            "Si se activa, filtra las geometrias base para quedarse solo con "
            "family='ads' (control positivo AdS puro)."
        ),
    )
    parser.add_argument(
        "--ads-boundary-mode",
        choices=("gkpw", "toy"),
        default="gkpw",
        help=(
            "Modo de boundary para family='ads'. Default: gkpw (canonical). "
            "Use toy solo para compatibilidad experimental explicita."
        ),
    )
    parser.add_argument(
        "--quick-test",
        action="store_true",
        help="Modo rapido: reduce n-known=2, n-test=1, n-unknown=1 para smoke tests",
    )
    parser.add_argument(
        "--focused-real-regime",
        action="store_true",
        help=(
            "Retarget del sandbox al soporte empírico realista: filtra families, "
            "fija d y focaliza el muestreo de z_h sin cambiar el comportamiento por defecto."
        ),
    )
    parser.add_argument(
        "--focused-d",
        type=int,
        default=4,
        help="Valor de d a fijar cuando se activa --focused-real-regime.",
    )
    parser.add_argument(
        "--focused-families",
        nargs="+",
        default=list(DEFAULT_FOCUSED_FAMILIES),
        help="Families permitidas en modo focused.",
    )
    parser.add_argument(
        "--zh-min",
        type=float,
        default=1.0,
        help="Límite inferior del rango focalizado de z_h en modo focused.",
    )
    parser.add_argument(
        "--zh-max",
        type=float,
        default=1.2,
        help="Límite superior del rango focalizado de z_h en modo focused.",
    )
    parser.add_argument(
        "--out-of-support-frac",
        type=float,
        default=0.0,
        help="Fracción explícita de muestras de z_h fuera del rango focalizado.",
    )
    parser.add_argument(
        "--out-of-support-zh-min",
        type=float,
        default=0.8,
        help="Mínimo permitido para la cola fuera de soporte en modo focused.",
    )
    parser.add_argument(
        "--out-of-support-zh-max",
        type=float,
        default=2.0,
        help="Máximo permitido para la cola fuera de soporte en modo focused.",
    )
    add_standard_arguments(parser)
    return parser


def build_focused_sampling_config(args: argparse.Namespace) -> FocusedSamplingConfig:
    families = tuple(str(fam).lower() for fam in getattr(args, "focused_families", []))
    if not families:
        raise ValueError("focused_real_regime requiere al menos una family en --focused-families")
    if args.zh_min >= args.zh_max:
        raise ValueError("--zh-min debe ser menor que --zh-max")
    if not (0.0 <= args.out_of_support_frac <= 1.0):
        raise ValueError("--out-of-support-frac debe estar en [0, 1]")
    if args.out_of_support_zh_min < 0.3:
        raise ValueError("--out-of-support-zh-min debe ser >= 0.3")
    if args.out_of_support_zh_min > args.zh_min:
        raise ValueError("--out-of-support-zh-min no puede exceder --zh-min")
    if args.out_of_support_zh_max < args.zh_max:
        raise ValueError("--out-of-support-zh-max no puede ser menor que --zh-max")

    return FocusedSamplingConfig(
        enabled=bool(args.focused_real_regime),
        families=families,
        d=int(args.focused_d),
        zh_min=float(args.zh_min),
        zh_max=float(args.zh_max),
        out_of_support_frac=float(args.out_of_support_frac),
        out_of_support_zh_min=float(args.out_of_support_zh_min),
        out_of_support_zh_max=float(args.out_of_support_zh_max),
    )


def main():
    parser = build_parser()

    args = parse_stage_args(parser)
    focused_config = build_focused_sampling_config(args)
    
    # --quick-test: reducir cantidades para smoke tests rapidos
    if getattr(args, 'quick_test', False):
        args.n_known = 2
        args.n_test = 1
        args.n_unknown = 1
        print("[QUICK-TEST] Reduciendo a n_known=2, n_test=1, n_unknown=1")
    
    ctx = StageContext.from_args(args, stage_number="01", stage_slug="generate_sandbox_geometries")
    
    # IO CONTRACT: output en 01_generate_sandbox_geometries/: geometries/ es el subdir contractual
    # --output-dir esta DEPRECATED, se ignora si se pasa
    
    status = STATUS_OK
    exit_code = EXIT_OK
    error_message = None

    try:
        ctx.record_artifact(ctx.stage_dir)
    except Exception:
        pass

    try:
        import h5py  # type: ignore
        import numpy as np  # type: ignore

        rng = np.random.default_rng(args.seed)
        # IO CONTRACT: output en 01_generate_sandbox_geometries/ §2: escribir en geometries/
        output_dir = ctx.run_root / "01_generate_sandbox_geometries"
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"[ROUTING] writing geometrias en: {output_dir}")

        # malla en z comun a todos los universes
        z_grid = np.linspace(0.01, args.z_max, args.n_z)

        base_geometries = get_phase11_geometries()
        
        # Modo control positivo: solo geometrias AdS
        if args.ads_only:
            base_geometries = [
                (geo, cat)
                for (geo, cat) in base_geometries
                if geo.family == "ads"
            ]
            if not base_geometries:
                raise RuntimeError(
                    "ads-only solicitado, pero get_phase11_geometries() no contiene ninguna family='ads'."
                )
            print("[MODO CONTROL POSITIVO] Filtrando sandbox a family='ads' unicamente.")

        if focused_config.enabled:
            base_geometries = [
                (geo, cat)
                for (geo, cat) in base_geometries
                if geo.family in focused_config.families
            ]
            if not base_geometries:
                raise RuntimeError(
                    "focused_real_regime solicitado, pero no hay geometrias base "
                    f"para families={list(focused_config.families)}."
                )
            print("[MODO FOCUSED] Retarget del sandbox activado.")
            print(
                f"[MODO FOCUSED] families={list(focused_config.families)}, "
                f"d={focused_config.d}, z_h∈[{focused_config.zh_min:.3f}, {focused_config.zh_max:.3f}], "
                f"out_of_support_frac={focused_config.out_of_support_frac:.3f}"
            )

        geometries: List[Tuple[HiddenGeometry, str]] = []

        # expandir con jitter
        for base_geo, category in base_geometries:
            if category == "known":
                n_instances = args.n_known
            elif category == "test":
                n_instances = args.n_test
            else:
                n_instances = args.n_unknown

            for k in range(n_instances):
                geo = make_geometry_instance(base_geo, category, k, rng, focused_config=focused_config)
                geometries.append((geo, category))

        # resumen inicial
        n_known_total = sum(1 for _, cat in geometries if cat == "known")
        n_test_total = sum(1 for _, cat in geometries if cat == "test")
        n_unknown_total = sum(1 for _, cat in geometries if cat == "unknown")

        print("=" * 70)
        print("EMERGENT GEOMETRY ENGINE")
        print("=" * 70)
        print(f"Output:       {output_dir}")
        print(f"prototypes:   {len(base_geometries)}")
        print(f"Geometrias:   {len(geometries)} total")
        print(f"  - known:    {n_known_total}")
        print(f"  - test:     {n_test_total}")
        print(f"  - unknown:  {n_unknown_total}")
        print(f"operators:   {args.n_operators}")
        print(f"z grid:       [0.01, {args.z_max}]  {args.n_z}")
        print(f"EMD backend:  {'ON' if args.use_emd_lifshitz and HAS_EMD else 'OFF'}")
        print("=" * 70)

        manifest: Dict = {
            "geometries": [],
            "version": "v3",
            "config": {
                "n_known_per_base": args.n_known,
                "n_test_per_base": args.n_test,
                "n_unknown_per_base": args.n_unknown,
                "n_samples": args.n_samples,
                "n_operators": args.n_operators,
                "z_max": args.z_max,
                "n_z": args.n_z,
                "seed": args.seed,
                "use_emd_lifshitz": args.use_emd_lifshitz,
                "ads_boundary_mode": args.ads_boundary_mode,
                "focused_real_regime": focused_config.enabled,
                "focused_sampling": asdict(focused_config),
            },
        }

        # loop principal
        for idx, (geo, category) in enumerate(geometries):
            print(f"[{idx+1:04d}/{len(geometries):04d}] {geo.name} ({geo.family}, {category})")

            # operators
            operators = generate_operators_for_geometry(geo, args.n_operators, rng)
            deltas_str = ", ".join(f"{op['Delta']:.2f}" for op in operators)
            zh_display = geo.z_h if geo.z_h is not None else 0.0
            print(f"   d={geo.d}, z_h={zh_display:.3f}, θ={geo.theta:.2f}, z_dyn={geo.z_dyn:.2f}")
            print(f"   Δ: [{deltas_str}]")

            # ============================================================
            # FIX 2025-12-21: Guardrail IO v1 ANTES de generar datos
            # ============================================================
            # Si el nombre codifica "_d<k>_", debe coincidir con geo.d
            # IMPORTANTE: esto debe ejecutarse ANTES de generar boundary_data
            # y bulk_truth para que ambos usen el valor correcto de d.
            m_d = re.search(r"_d(\d+)_", geo.name)
            if m_d is not None:
                d_name = int(m_d.group(1))
                if int(geo.d) != d_name:
                    print(
                        f"[IO_CONTRACT][AUTO-FIX] d mismatch: {geo.name}: geo.d={geo.d} -> {d_name} (from name)"
                    )
                    geo.d = d_name

            # boundary (VISIBLE para el learner)
            boundary_data, boundary_meta = generate_boundary_data(
                geo,
                operators,
                args.n_samples,
                rng,
                ads_boundary_mode=args.ads_boundary_mode,
                z_grid=z_grid,
            )

            # bulk (solo para validacion/contratos)
            bulk_truth = generate_bulk_truth(geo, z_grid, use_emd=args.use_emd_lifshitz)

            # guardar en HDF5
            output_path = output_dir / f"{geo.name}.h5"
            with h5py.File(output_path, "w") as f:
                # attrs globales
                f.attrs["name"] = geo.name
                f.attrs["system_name"] = geo.name
                f.attrs["family"] = geo.family
                f.attrs["category"] = category
                f.attrs["d"] = geo.d
                f.attrs["z_h"] = geo.z_h if geo.z_h is not None else 0.0
                f.attrs["theta"] = geo.theta
                f.attrs["z_dyn"] = geo.z_dyn
                f.attrs["deformation"] = geo.deformation
                # ── Tier A: attrs canónicos extra ─────────────────────────────
                f.attrs["charge_Q"] = geo.charge_Q
                f.attrs["lambda_gb"] = geo.lambda_gb
                f.attrs["m_g"] = geo.m_g
                f.attrs["mg_c1"] = geo.mg_c1
                f.attrs["mg_c2"] = geo.mg_c2
                f.attrs["alpha_axion"] = geo.alpha_axion
                # ── Tier A ext (2026-04) ──────────────────────────────────────
                f.attrs["mu_GR"] = geo.mu_GR
                f.attrs["kappa_sw"] = geo.kappa_sw
                # ── AGMOO contract: clasificación ads y tipo de correlador ────
                agmoo_meta = get_ads_metadata_for_geometry(
                    geo,
                    ads_boundary_mode=args.ads_boundary_mode if geo.family == "ads" else "toy",
                    gkpw_meta=boundary_meta if geo.family == "ads" else None,
                )
                for key, value in agmoo_meta.items():
                    if value is not None:
                        f.attrs[key] = value
                f.attrs["operators"] = json.dumps(operators)
                f.attrs["sampling_regime"] = (
                    "focused_real_regime" if focused_config.enabled else "default"
                )
                if focused_config.enabled:
                    f.attrs["focused_sampling"] = json.dumps(asdict(focused_config))
                    f.attrs["focused_out_of_support"] = bool(
                        geo.metadata.get("focused_out_of_support", False)
                    )

                # boundary
                bgrp = f.create_group("boundary")
                for key, val in boundary_data.items():
                    if isinstance(val, np.ndarray):
                        bgrp.create_dataset(key, data=val)
                    else:
                        bgrp.attrs[key] = val
                bgrp.attrs["d"] = geo.d
                bgrp.attrs["family"] = geo.family
                for key, value in agmoo_meta.items():
                    if value is not None:
                        bgrp.attrs[key] = value

                # Delta_mass_dict para Stage 08 (holographic dictionary)
                Delta_mass_dict = {
                    op["name"]: {"Delta": op["Delta"], "m2L2": op["m2L2"]}
                    for op in operators
                }
                bgrp.attrs["Delta_mass_dict"] = json.dumps(Delta_mass_dict)

                # bulk_truth
                tgrp = f.create_group("bulk_truth")
                for key, val in bulk_truth.items():
                    if isinstance(val, np.ndarray):
                        tgrp.create_dataset(key, data=val)
                    else:
                        tgrp.attrs[key] = val
                
                # IO CONTRACT: Keys canonicos en raiz del H5
                # Permite que scripts downstream encuentren datos sin conocer estructura interna
                f.create_dataset("z_grid", data=bulk_truth["z_grid"])
                f.create_dataset("A_of_z", data=bulk_truth["A_truth"])
                f.create_dataset("f_of_z", data=bulk_truth["f_truth"])

            # entrada en manifest
            agmoo_manifest_meta = get_ads_metadata_for_geometry(
                geo,
                ads_boundary_mode=args.ads_boundary_mode if geo.family == "ads" else "toy",
                gkpw_meta=boundary_meta if geo.family == "ads" else None,
            )
            manifest_entry: Dict = {
                "name": geo.name,
                "family": geo.family,
                "category": category,
                "d": geo.d,
                "z_h": geo.z_h,
                "file": str(output_path.name),
                "operators": [op["name"] for op in operators],
                "sampling_regime": "focused_real_regime" if focused_config.enabled else "default",
                "correlator_type": agmoo_manifest_meta["correlator_type"],
                "classification": agmoo_manifest_meta.get("classification"),
                "metadata": geo.metadata,
            }
            if geo.family == "ads":
                manifest_entry["ads_classification"] = agmoo_manifest_meta["ads_classification"]
                manifest_entry["ads_boundary_mode"] = agmoo_manifest_meta.get("ads_boundary_mode")
                manifest_entry["ads_pipeline_tier"] = agmoo_manifest_meta.get("ads_pipeline_tier")
                for key in (
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
                    if key in agmoo_manifest_meta:
                        manifest_entry[key] = agmoo_manifest_meta[key]
            manifest["geometries"].append(manifest_entry)

        # escribir manifest de geometrías (nombre propio para no colisionar con stage_utils)
        manifest_path = output_dir / "geometries_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))
        ads_gkpw_summary = build_ads_gkpw_run_summary(manifest)
        ads_gkpw_summary_path = output_dir / "ads_gkpw_migration_summary.json"
        ads_gkpw_summary_path.write_text(json.dumps(ads_gkpw_summary, indent=2, sort_keys=True))

        # resumen final por family
        families: Dict[str, Dict[str, int]] = {}
        for geo, category in geometries:
            fam = geo.family
            if fam not in families:
                families[fam] = {"known": 0, "test": 0, "unknown": 0}
            families[fam][category] = families[fam].get(category, 0) + 1

        print("\n" + "=" * 70)
        print("SUMMARY BY FAMILY")
        for fam, counts in sorted(families.items()):
            print(
                f"  {fam:15s}: "
                f"known={counts.get('known', 0):3d}, "
                f"test={counts.get('test', 0):3d}, "
                f"unknown={counts.get('unknown', 0):3d}"
            )

        print("\n" + "=" * 70)
        print("✓ SANDBOX GEOMETRY GENERATION v3 COMPLETADA")
        print(f"  Manifest: {manifest_path}")
        print(f"  ADS GKPW summary: {ads_gkpw_summary_path}")
        print(f"  Total:    {len(geometries)} universes")
        print("=" * 70)
        print("Next step: 02_emergent_geometry_engine.py")
        print("The learner only sees boundary data - it must discover the geometry.")

        ctx.record_artifact(output_dir)
        ctx.record_artifact(manifest_path)
        ctx.record_artifact(ads_gkpw_summary_path)
        ctx.write_manifest(
            outputs={"sandbox_dir": "01_generate_sandbox_geometries"},
            metadata={"command": " ".join(sys.argv)},
        )
    except Exception as exc:  # pragma: no cover - infra guardrail
        status = STATUS_ERROR
        exit_code = EXIT_ERROR
        error_message = str(exc)
        raise
    finally:
        summary_path = ctx.stage_dir / "stage_summary.json"
        try:
            ctx.record_artifact(summary_path)
        except Exception:
            pass
        ctx.write_summary(status=status, exit_code=exit_code, error_message=error_message)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
