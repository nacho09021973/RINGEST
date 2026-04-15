#!/usr/bin/env python3
"""
family_registry.py  —  CUERDAS-MALDACENA
Registro canónico de familias holográficas.

PROPÓSITO
---------
Centralizar en un único módulo la fuente de verdad sobre qué familias
existen, qué campos de metadata canónica requieren, y qué índice entero
se les asigna para el clasificador de Stage 02.

Antes de este módulo, la taxonomía vivía dispersa en:
  - 01_generate_sandbox_geometries.py  (HiddenGeometry, get_phase11_geometries)
  - 02_emergent_geometry_engine.py     (family_map hardcoded ×2)
  - 06_holographic_eigenmode_dataset.py (docstring)
  - 00_compute_sandbox_qnms.py         (fp_horizon_analytic branches)

Cualquier nuevo stage que necesite interpretar el campo `family` de un
HDF5 debe importar las constantes de aquí.

CONTRATO DE FAMILIAS
--------------------
Para que una familia sea "canónica holográfica" debe satisfacer:

  1. Gauge domain-wall:
       ds² = e^{2A(z)}[-f(z)dt² + dx_i²] + dz²/f(z)
  2. HDF5 raíz contiene: z_grid, A_of_z, f_of_z, family (attr)
  3. HDF5 contiene grupo bulk_truth/ con A_truth, f_truth, R_truth, z_grid
  4. HDF5 boundary/ contiene Delta_mass_dict (JSON) en sus attrs
  5. fp_horizon_analytic() en 00_compute_sandbox_qnms.py tiene rama explícita
  6. family_map en 02_emergent_geometry_engine.py incluye la familia
  7. La familia aparece en el docstring de 06_holographic_eigenmode_dataset.py

TIERS
-----
  TIER_CANONICAL: familias base originales (siempre soportadas)
  TIER_A:         cohorte de expansión Tier A (RN-AdS, GB, massive gravity,
                  linear axion, charged hvLif)
  TIER_SPECIAL:   carriles no holográficos (Kerr); no usan bulk_truth

FAMILY STATUS
-------------
  canonical_strong:          carril físico fuerte actualmente aceptado
  toy_sandbox:               geometría/observable sintético o fenomenológico
  realdata_surrogate:        embedding derivado de datos reales, no dual fuerte
  non_holographic_surrogate: carril especial sin bulk holográfico

METADATA CANÓNICA POR FAMILIA
------------------------------
Cada familia declara los campos de metadata adicionales que escribe Stage 01
en los attrs del HDF5 raíz. Los campos base (d, z_h, theta, z_dyn, family,
deformation, L) son comunes a todas.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, List, Mapping, NamedTuple, Optional

# ──────────────────────────────────────────────────────────────────────────────
#  Constantes de tier
# ──────────────────────────────────────────────────────────────────────────────

#: Familias base originales del pipeline (Stage 01 v1).
TIER_CANONICAL: FrozenSet[str] = frozenset({
    "ads",
    "lifshitz",
    "hyperscaling",
    "deformed",
    "dpbrane",
    "unknown",
})

#: Cohorte de expansión Tier A — encajan en el gauge actual sin subcontrato nuevo.
TIER_A: FrozenSet[str] = frozenset({
    "rn_ads",          # Reissner-Nordström AdS
    "gauss_bonnet",    # Gauss-Bonnet AdS
    "massive_gravity", # Massive gravity AdS (Vegh-type)
    "linear_axion",    # Linear axion / momentum dissipation
    "charged_hvlif",   # Charged hyperscaling-violation Lifshitz
    "gubser_rocha",    # Gubser-Rocha EMD (strange metal, s(T=0)=0)
    "soft_wall",       # Soft-wall backreacted (IR confinement via warp factor)
})

#: Carriles no holográficos (sin bulk_truth holográfico).
TIER_SPECIAL: FrozenSet[str] = frozenset({
    "kerr",
})

#: Unión de todas las familias holográficas reconocidas.
HOLOGRAPHIC_FAMILIES: FrozenSet[str] = TIER_CANONICAL | TIER_A

#: Todas las familias reconocidas (incluyendo carriles especiales).
ALL_FAMILIES: FrozenSet[str] = HOLOGRAPHIC_FAMILIES | TIER_SPECIAL


# ──────────────────────────────────────────────────────────────────────────────
#  Estado físico-operativo de familias
# ──────────────────────────────────────────────────────────────────────────────

FAMILY_STATUS_STATES: FrozenSet[str] = frozenset({
    "canonical_strong",
    "toy_sandbox",
    "realdata_surrogate",
    "non_holographic_surrogate",
})

FAMILY_STATUS_DESCRIPTIONS: Dict[str, str] = {
    "canonical_strong": (
        "Carril físico fuerte. En este repo actualmente solo aplica a ads "
        "cuando Stage 01 corre con ads_boundary_mode=gkpw."
    ),
    "toy_sandbox": (
        "Familia sintética/sandbox: warp, blackening u observable de frontera "
        "son analíticos, geodésicos o fenomenológicos."
    ),
    "realdata_surrogate": (
        "Embedding derivado de datos reales/ringdown; no constituye por sí solo "
        "un dual holográfico fuerte."
    ),
    "non_holographic_surrogate": (
        "Carril especial no holográfico dentro de este gauge, por ejemplo Kerr."
    ),
}


# ──────────────────────────────────────────────────────────────────────────────
#  Contrato AGMOO para familia ads
# ──────────────────────────────────────────────────────────────────────────────

#: Sub-clasificaciones canónicas de la familia ads.
#: Las condiciones de asignación viven en el validador AGMOO ADS.
ADS_CLASSIFICATIONS: FrozenSet[str] = frozenset({
    "ads_pure",          # AdS puro: T=0, sin deformación, Gate 6 completo
    "ads_thermal",       # AdS con horizonte (temperatura finita)
    "ads_deformed",      # AdS con deformación explícita del warp factor
    "ads_toy_boundary",  # AdS T=0 sin deformación pero sin Gate 6 completo
})

#: Tipos de correlador para el observable de frontera.
CORRELATOR_TYPES: FrozenSet[str] = frozenset({
    "HOLOGRAPHIC_WITTEN_DIAGRAM",  # Diagrama de Witten completo (AdS/CFT exacto)
    "GKPW_SOURCE_RESPONSE_NUMERICAL", # Source/response bulk numerico sin renormalizacion completa
    "GEODESIC_APPROXIMATION",      # Aproximación geodésica (AGMOO Sec. 3.5.1)
    "QNM_SURROGATE",               # Surrogate basado en QNMs
    "TOY_PHENOMENOLOGICAL",        # Modelo fenomenológico toy
    "UNKNOWN",                     # No inferible del código disponible
})

#: Estados de veredicto AGMOO para familia ads.
ADS_VERDICT_STATES: FrozenSet[str] = frozenset({
    "ADS_HOLOGRAPHIC_STRONG_PASS",  # Todos los gates pasan completamente
    "ADS_HOLOGRAPHIC_PARTIAL_PASS", # Gates geométrico y holográfico pasan; UV/IR parcial
    "ADS_TEMPLATE_ONLY",            # Gate 6 ausente en experimental/legacy, o correlador UNKNOWN
    "ADS_THERMAL_TOY_ONLY",         # Térmico + correlador no fuerte (compatibilidad histórica)
    "ADS_EXPERIMENTAL_TOY_ONLY",    # Tier experimental con correlador toy/geodésico/QNM
    "ADS_UV_IR_FRAGILE",            # Gates anteriores OK, UV/IR gate FRAGILE
    "ADS_CONTRACT_FAIL",            # Cota BF violada o campos geométricos críticos ausentes
})


# ──────────────────────────────────────────────────────────────────────────────
#  FAMILY_MAP: entero para el clasificador de Stage 02
# ──────────────────────────────────────────────────────────────────────────────
#
# Orden determinista: primero TIER_CANONICAL en orden original, luego TIER_A
# en orden alfabético, finalmente TIER_SPECIAL.
# Los índices NO deben cambiar entre versiones una vez que hay checkpoints
# entrenados; añadir familias nuevas solo extiende el mapa.

FAMILY_MAP: Dict[str, int] = {
    # TIER_CANONICAL (índices 0-5, orden histórico)
    "ads":            0,
    "lifshitz":       1,
    "hyperscaling":   2,
    "deformed":       3,
    "dpbrane":        4,
    "unknown":        5,
    # TIER_SPECIAL (índice 6)
    "kerr":           6,
    # TIER_A (índices 7-11, orden alfabético original; extensión 12-13 estable)
    "charged_hvlif":  7,
    "gauss_bonnet":   8,
    "linear_axion":   9,
    "massive_gravity":10,
    "rn_ads":         11,
    # Extensión Tier A (2026-04) — índices nuevos, no colisionan con checkpoints previos
    "gubser_rocha":   12,
    "soft_wall":      13,
}

#: Mapa inverso entero → nombre de familia.
FAMILY_MAP_INV: Dict[int, str] = {v: k for k, v in FAMILY_MAP.items()}


# ──────────────────────────────────────────────────────────────────────────────
#  Metadata canónica adicional por familia
# ──────────────────────────────────────────────────────────────────────────────

class FamilyMetaSpec(NamedTuple):
    """Especificación de un campo de metadata canónica para una familia."""
    h5_attr: str            # nombre del attr en el HDF5 raíz
    dtype: type             # float o int
    default: float          # valor por defecto si el campo no existe
    description: str        # descripción física breve


#: Campos de metadata canónica ADICIONALES por familia.
#: Los campos base (d, z_h, theta, z_dyn, family, deformation) son comunes
#: a todas las familias y no se repiten aquí.
FAMILY_EXTRA_ATTRS: Dict[str, List[FamilyMetaSpec]] = {
    # ── TIER_CANONICAL ──────────────────────────────────────────────────────
    "ads": [],
    "lifshitz": [],
    "hyperscaling": [],
    "deformed": [],
    "dpbrane": [],
    "unknown": [],
    # ── TIER_SPECIAL ────────────────────────────────────────────────────────
    "kerr": [],  # carril separado, sin bulk_truth holográfico
    # ── TIER_A ──────────────────────────────────────────────────────────────
    "rn_ads": [
        FamilyMetaSpec(
            h5_attr="charge_Q",
            dtype=float,
            default=0.0,
            description=(
                "Carga eléctrica adimensional Q (≡ Q/z_h^{d-1}). "
                "0 → AdS-Schwarzschild; cerca de Q_ext → BH extremal."
            ),
        ),
    ],
    "gauss_bonnet": [
        FamilyMetaSpec(
            h5_attr="lambda_gb",
            dtype=float,
            default=0.0,
            description=(
                "Acoplamiento de Gauss-Bonnet λ. "
                "Rango físico: λ < 1/4 (d≥4). λ=0 → AdS puro."
            ),
        ),
    ],
    "massive_gravity": [
        FamilyMetaSpec(
            h5_attr="m_g",
            dtype=float,
            default=0.0,
            description="Masa del gravitón m_g (unidades de 1/L). m_g=0 → AdS puro.",
        ),
        FamilyMetaSpec(
            h5_attr="mg_c1",
            dtype=float,
            default=1.0,
            description="Coeficiente c1 en el potencial de masa de gravitón.",
        ),
        FamilyMetaSpec(
            h5_attr="mg_c2",
            dtype=float,
            default=0.0,
            description="Coeficiente c2 en el potencial de masa de gravitón.",
        ),
    ],
    "linear_axion": [
        FamilyMetaSpec(
            h5_attr="alpha_axion",
            dtype=float,
            default=0.0,
            description=(
                "Pendiente del axión lineal α (disipación de momento). "
                "α=0 → AdS-Schwarzschild. α grande → metal incoherente."
            ),
        ),
    ],
    "charged_hvlif": [
        FamilyMetaSpec(
            h5_attr="charge_Q",
            dtype=float,
            default=0.0,
            description="Carga eléctrica adimensional Q para hvLif cargado.",
        ),
    ],
    "gubser_rocha": [
        FamilyMetaSpec(
            h5_attr="mu_GR",
            dtype=float,
            default=0.0,
            description=(
                "Parámetro efectivo mu del toy Gubser-Rocha (dilatón corriendo). "
                "mu=0 reduce a AdS-Schwarzschild; mu>0 activa correcciones IR "
                "tipo EMD con s(T=0)->0 (opuesto a RN-AdS)."
            ),
        ),
    ],
    "soft_wall": [
        FamilyMetaSpec(
            h5_attr="kappa_sw",
            dtype=float,
            default=0.0,
            description=(
                "Escala de confinamiento soft-wall κ (Batell-Gherghetta). "
                "A(z) = -log(z/L) - (κ/2)(z/L)^2. κ=0 reduce a AdS; κ>0 "
                "produce deformación cuadrática IR (Regge lineal)."
            ),
        ),
    ],
}


# ──────────────────────────────────────────────────────────────────────────────
#  Helpers públicos
# ──────────────────────────────────────────────────────────────────────────────

def is_holographic(family: str) -> bool:
    """True si la familia pertenece al carril holográfico (tiene bulk_truth)."""
    return family in HOLOGRAPHIC_FAMILIES


def is_canonical(family: str) -> bool:
    """True si la familia es Tier Canonical (soporte original, siempre disponible)."""
    return family in TIER_CANONICAL


def is_tier_a(family: str) -> bool:
    """True si la familia es Tier A (cohorte de expansión)."""
    return family in TIER_A


def family_index(family: str) -> int:
    """
    Retorna el índice entero de la familia para el clasificador de Stage 02.
    Lanza KeyError si la familia no está registrada.
    """
    if family not in FAMILY_MAP:
        raise KeyError(
            f"Familia '{family}' no registrada en family_registry.FAMILY_MAP. "
            f"Familias válidas: {sorted(FAMILY_MAP)}"
        )
    return FAMILY_MAP[family]


def family_from_index(idx: int) -> str:
    """Retorna el nombre de familia a partir del índice entero."""
    if idx not in FAMILY_MAP_INV:
        raise KeyError(f"Índice {idx} no registrado en FAMILY_MAP_INV.")
    return FAMILY_MAP_INV[idx]


def extra_attrs_for(family: str) -> List[FamilyMetaSpec]:
    """
    Retorna la lista de FamilyMetaSpec adicionales para la familia dada.
    Para familias sin metadata extra (o no registradas) retorna lista vacía.
    """
    return FAMILY_EXTRA_ATTRS.get(family, [])


def get_family_status(
    family: str,
    *,
    ads_boundary_mode: str = "toy",
    source: str = "sandbox",
) -> str:
    """
    Retorna el estado físico-operativo de una familia en este repo.

    `family` por sí sola no basta para ads: ads es fuerte solo cuando el
    observable de frontera se genera por el carril GKPW.
    """
    if source == "realdata":
        return "realdata_surrogate"
    if family == "kerr":
        return "non_holographic_surrogate"
    if family == "ads" and ads_boundary_mode == "gkpw":
        return "canonical_strong"
    return "toy_sandbox"


def get_family_status_description(status: str) -> str:
    """Descripcion humana corta de un family_status."""
    return FAMILY_STATUS_DESCRIPTIONS.get(status, "Estado de familia desconocido.")


def read_extra_attrs_from_h5(h5_attrs: Mapping, family: str) -> Dict[str, float]:
    """
    Lee los attrs extra canónicos de un HDF5 attrs-dict para la familia dada.
    Usa los defaults si el campo no está presente.

    Parameters
    ----------
    h5_attrs : h5py.AttributeManager o dict-like con .get()
    family   : nombre de la familia

    Returns
    -------
    dict con {h5_attr: valor_float}
    """
    result: Dict[str, float] = {}
    for spec in extra_attrs_for(family):
        raw = h5_attrs.get(spec.h5_attr, None)
        if raw is None:
            result[spec.h5_attr] = spec.default
        else:
            result[spec.h5_attr] = spec.dtype(raw)
    return result


def classify_ads_geometry(
    family: str,
    z_h: Optional[float],
    deformation: float = 0.0,
) -> Optional[str]:
    """
    Retorna la sub-clasificación ads para una geometría, o None si no es ads.

    Reglas (conservadoras, derivadas del código):
      - family != "ads"          → None
      - deformation ≠ 0          → "ads_deformed"
      - z_h > 0                  → "ads_thermal"
      - z_h is None o z_h <= 0   → "ads_toy_boundary"
        (ads_pure requiere Gate 6 completo, que se verifica en validate_agmoo_ads)

    Parameters
    ----------
    family      : nombre de la familia
    z_h         : posición del horizonte (None o 0.0 → sin horizonte)
    deformation : valor del campo deformation en HiddenGeometry

    Returns
    -------
    str con la sub-clasificación ads, o None si family != "ads".
    """
    if family != "ads":
        return None
    if abs(deformation) > 1e-8:
        return "ads_deformed"
    if z_h is not None and float(z_h) > 0.0:
        return "ads_thermal"
    # T=0, sin deformación: no se puede confirmar ads_pure sin Gate 6
    return "ads_toy_boundary"


def get_correlator_type_for_geometry(family: str, use_geodesic: bool = True) -> str:
    """
    Retorna el correlator_type basado en el camino real del observable en el repo.

    En el estado actual del repo, todos los correladores G2 se calculan
    mediante correlator_2pt_geodesic (AGMOO Sec. 3.5.1), con fallback interno
    al correlador térmico fenomenológico si el cálculo geodésico falla.

    El campo G_R (respuesta lineal) es un polo Lorentziano toy, pero no es
    el observable principal para la reconstrucción de Stage 02.

    Parameters
    ----------
    family       : nombre de la familia (solo documentativo aquí)
    use_geodesic : True si el script usa correlator_2pt_geodesic (default)

    Returns
    -------
    str con el correlator_type canónico.
    """
    if use_geodesic:
        return "GEODESIC_APPROXIMATION"
    return "TOY_PHENOMENOLOGICAL"


def validate_family(family: str, *, strict: bool = False) -> bool:
    """
    Comprueba si una familia es válida.

    Parameters
    ----------
    family : nombre a validar
    strict : si True, solo acepta familias holográficas (no Kerr/special)

    Returns
    -------
    True si válida, False si no.
    """
    if strict:
        return family in HOLOGRAPHIC_FAMILIES
    return family in ALL_FAMILIES


# ──────────────────────────────────────────────────────────────────────────────
#  Registro de sincronización entre stages
# ──────────────────────────────────────────────────────────────────────────────
#
# Esta sección documenta EXPLÍCITAMENTE qué stages deben actualizarse cuando
# se añade una familia nueva. Es la "checklist de contrato" para futuras
# extensiones.
#
# PARA AÑADIR UNA FAMILIA NUEVA (checklist):
#   □ 1. Añadir a TIER_A (o TIER_CANONICAL si es fundacional) en este módulo
#   □ 2. Añadir a FAMILY_MAP con índice único y estable
#   □ 3. Declarar FamilyMetaSpec en FAMILY_EXTRA_ATTRS si tiene metadata nueva
#   □ 4. 01_generate_sandbox_geometries.py:
#          - Añadir campo en HiddenGeometry dataclass (si metadata nueva)
#          - Añadir rama en warp_factor()
#          - Añadir rama en blackening_factor()
#          - Añadir prototipo en get_phase11_geometries()
#          - Añadir jitter en make_geometry_instance()
#          - Añadir escritura de attrs extra en el bloque HDF5
#   □ 5. 00_compute_sandbox_qnms.py:
#          - Añadir rama explícita en fp_horizon_analytic() (no fallback)
#   □ 6. 02_emergent_geometry_engine.py:
#          - Importar FAMILY_MAP desde family_registry y eliminar hardcoding
#   □ 7. 06_holographic_eigenmode_dataset.py:
#          - Actualizar docstring con la nueva familia
#   □ 8. Test de regresión en 00_validate_io_contracts.py:
#          - Verificar que la familia pasa el contrato H5
#

STAGE_SYNC_REQUIREMENTS: Dict[str, List[str]] = {
    "01_generate_sandbox_geometries.py": [
        "HiddenGeometry.warp_factor() branch",
        "HiddenGeometry.blackening_factor() branch",
        "get_phase11_geometries() prototype",
        "make_geometry_instance() jitter",
        "HDF5 extra attrs write",
    ],
    "00_compute_sandbox_qnms.py": [
        "fp_horizon_analytic() explicit branch (no fallback to else)",
    ],
    "02_emergent_geometry_engine.py": [
        "FAMILY_MAP import or inline dict (both occurrences at lines ~1511 and ~1847)",
    ],
    "06_holographic_eigenmode_dataset.py": [
        "Module docstring family list",
    ],
    "00_validate_io_contracts.py": [
        "H5 contract test for new family",
    ],
}
