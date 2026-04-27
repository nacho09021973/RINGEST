"""
tests/test_agmoo_ads_contract.py
=================================
Tests de contrato AGMOO para familia ``ads``.

Cobertura minima obligatoria:

  1. ads sin metadata del Gate 6 (T=0, no deformacion)  ADS_TEMPLATE_ONLY
  2. ads termico + correlador no-Witten + sin Gate 6  ADS_TEMPLATE_ONLY
  3. Violacion explicita de cota BF  ADS_CONTRACT_FAIL
  4. Familia no-ads  NOT_ADS (validador no rompe nada)
  5. correlator_type se escribe correctamente en metadata generada por Stage 01

Tests adicionales:
  6. ads_thermal con correlador GEODESIC_APPROXIMATION (repo actual)  ADS_EXPERIMENTAL_TOY_ONLY si Gate 6 esta presente
  7. ads_deformed sin Gate 6  ADS_TEMPLATE_ONLY
  8. Todos los gates completos  ADS_HOLOGRAPHIC_STRONG_PASS
  9. classify_ads_geometry retorna los valores correctos
 10. get_correlator_type_for_geometry retorna GEODESIC_APPROXIMATION por defecto
 11. ADS_CLASSIFICATIONS y CORRELATOR_TYPES son frozensets con los valores esperados
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Anadir raiz del repo al path para encontrar los modulos
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from family_registry import (
    ADS_CLASSIFICATIONS,
    ADS_VERDICT_STATES,
    CORRELATOR_TYPES,
    FAMILY_STATUS_STATES,
    classify_ads_geometry,
    get_correlator_type_for_geometry,
    get_family_status,
)
from tools.validate_agmoo_ads import (
    check_bf_bound,
    check_bf_from_operators,
    check_geometry_gate,
    check_holographic_gate,
    check_uv_ir_gate,
    compute_ads_verdict,
    validate_ads_geometry,
)


# ---------------------------------------------------------------------------
# Fixtures: metadata base reutilizable
# ---------------------------------------------------------------------------

def _meta_ads_toy_boundary() -> dict:
    """ads T=0, sin deformacion, sin Gate 6  ads_toy_boundary."""
    return {
        "family": "ads",
        "d": 3,
        "z_h": None,
        "deformation": 0.0,
        "correlator_type": "GEODESIC_APPROXIMATION",
    }


def _meta_ads_thermal_no_gate6() -> dict:
    """ads termico, correlador geodesico, sin Gate 6."""
    return {
        "family": "ads",
        "d": 3,
        "z_h": 1.0,
        "deformation": 0.0,
        "correlator_type": "GEODESIC_APPROXIMATION",
        "operators": [
            {"name": "O1", "Delta": 2.5, "m2L2": 2.5 * (2.5 - 3)},   # m2L2 = -1.25
            {"name": "O2", "Delta": 3.5, "m2L2": 3.5 * (3.5 - 3)},   # m2L2 = 1.75
        ],
    }


def _meta_ads_all_gates() -> dict:
    """ads con todos los gates completos  ADS_HOLOGRAPHIC_STRONG_PASS."""
    return {
        "family": "ads",
        "d": 4,
        "z_h": None,
        "deformation": 0.0,
        "correlator_type": "HOLOGRAPHIC_WITTEN_DIAGRAM",
        "ads_classification": "ads_pure",
        "operators": [
            {"name": "O1", "Delta": 4.0, "m2L2": 4.0 * (4.0 - 4)},  # m2L2 = 0.0
        ],
        "bulk_field_name": "phi",
        "operator_name": "O",
        "m2L2": 0.0,
        "Delta": 4.0,
        "bf_bound_pass": True,
        "uv_source_declared": True,
        "ir_bc_declared": True,
    }


# ---------------------------------------------------------------------------
# 1. ads T=0 sin Gate 6  ADS_TEMPLATE_ONLY
# ---------------------------------------------------------------------------

class TestAdsTemplateOnly:
    def test_ads_toy_boundary_no_gate6(self):
        meta = _meta_ads_toy_boundary()
        result = validate_ads_geometry(meta)
        assert result["overall_verdict"] == "ADS_TEMPLATE_ONLY", (
            f"Expected ADS_TEMPLATE_ONLY, got {result['overall_verdict']}"
        )

    def test_classification_is_ads_toy_boundary(self):
        meta = _meta_ads_toy_boundary()
        result = validate_ads_geometry(meta)
        assert result["classification"] == "ads_toy_boundary"

    def test_holographic_gate_missing(self):
        meta = _meta_ads_toy_boundary()
        result = validate_ads_geometry(meta)
        assert result["holographic_gate_status"] == "MISSING_FIELDS"

    def test_missing_fields_contains_gate6_keys(self):
        meta = _meta_ads_toy_boundary()
        result = validate_ads_geometry(meta)
        expected_missing = {
            "bulk_field_name", "operator_name", "m2L2", "Delta",
            "bf_bound_pass", "uv_source_declared", "ir_bc_declared",
        }
        for field in expected_missing:
            assert field in result["missing_fields"], (
                f"Expected '{field}' in missing_fields, got {result['missing_fields']}"
            )

    def test_ads_deformed_no_gate6_template_only(self):
        meta = {
            "family": "ads",
            "d": 3,
            "z_h": None,
            "deformation": 0.5,
            "correlator_type": "GEODESIC_APPROXIMATION",
        }
        result = validate_ads_geometry(meta)
        assert result["classification"] == "ads_deformed"
        assert result["overall_verdict"] == "ADS_TEMPLATE_ONLY"


# ---------------------------------------------------------------------------
# 2. ads termico + Gate 6 ausente  ADS_TEMPLATE_ONLY
#    (la ausencia de Gate 6 bloquea antes que el origen fenomenologico)
#
# `ADS_THERMAL_TOY_ONLY` queda como estado legacy del registro, pero no debe
# aparecer como veredicto esperado en la logica viva.
# ---------------------------------------------------------------------------

class TestAdsThermalToyOnly:
    # -- Regresion critica: Gate 6 ausente bloquea antes de cualquier lectura experimental --

    def test_thermal_geodesic_no_gate6_gives_template_only(self):
        """
        REGRESION: ads_thermal + GEODESIC_APPROXIMATION + Gate 6 ausente
         ADS_TEMPLATE_ONLY.

        Gate 6 ausente bloquea cualquier lectura holografica mas fuerte,
        incluyendo cualquier veredicto experimental toy. (contrato sec. 2b)
        """
        meta = _meta_ads_thermal_no_gate6()
        result = validate_ads_geometry(meta)
        assert result["overall_verdict"] == "ADS_TEMPLATE_ONLY", (
            f"Gate 6 ausente debe dar ADS_TEMPLATE_ONLY, got {result['overall_verdict']}"
        )

    def test_thermal_toy_phenomenological_no_gate6_gives_template_only(self):
        """TOY_PHENOMENOLOGICAL + thermal + Gate 6 ausente  ADS_TEMPLATE_ONLY."""
        meta = dict(_meta_ads_thermal_no_gate6())
        meta["correlator_type"] = "TOY_PHENOMENOLOGICAL"
        result = validate_ads_geometry(meta)
        assert result["overall_verdict"] == "ADS_TEMPLATE_ONLY", (
            f"Gate 6 ausente debe dar ADS_TEMPLATE_ONLY, got {result['overall_verdict']}"
        )

    def test_thermal_witten_no_gate6_gives_template_only(self):
        """HOLOGRAPHIC_WITTEN_DIAGRAM + thermal + Gate 6 ausente  ADS_TEMPLATE_ONLY."""
        meta = dict(_meta_ads_thermal_no_gate6())
        meta["correlator_type"] = "HOLOGRAPHIC_WITTEN_DIAGRAM"
        result = validate_ads_geometry(meta)
        assert result["overall_verdict"] == "ADS_TEMPLATE_ONLY"

    # -- Campos de clasificacion se preservan aunque el veredicto sea TEMPLATE_ONLY --

    def test_classification_is_ads_thermal_regardless_of_verdict(self):
        """La clasificacion geometrica es ads_thermal independientemente del veredicto."""
        meta = _meta_ads_thermal_no_gate6()
        result = validate_ads_geometry(meta)
        assert result["classification"] == "ads_thermal"

    def test_correlator_type_preserved_in_output(self):
        """correlator_type se preserva en la salida aunque el veredicto sea TEMPLATE_ONLY."""
        meta = _meta_ads_thermal_no_gate6()
        result = validate_ads_geometry(meta)
        assert result["correlator_type"] == "GEODESIC_APPROXIMATION"

    # -- Gate 6 presente + carril experimental no fuerte colapsa en ADS_EXPERIMENTAL_TOY_ONLY --

    def test_thermal_geodesic_with_gate6_gives_experimental_toy_only(self):
        """
        ads_thermal + GEODESIC_APPROXIMATION + Gate 6 PRESENTE
         ADS_EXPERIMENTAL_TOY_ONLY.
        En ausencia de ads_pipeline_tier, los H5 legacy se tratan como experimental.
        """
        meta = {
            "family": "ads",
            "d": 3,
            "z_h": 1.0,
            "deformation": 0.0,
            "correlator_type": "GEODESIC_APPROXIMATION",
            # Gate 6 completo
            "bulk_field_name": "phi",
            "operator_name": "O1",
            "m2L2": -1.25,
            "Delta": 2.5,
            "bf_bound_pass": True,
            "uv_source_declared": True,
            "ir_bc_declared": True,
        }
        result = validate_ads_geometry(meta)
        assert result["overall_verdict"] == "ADS_EXPERIMENTAL_TOY_ONLY", (
            f"Gate 6 presente + thermal + GEODESIC  ADS_EXPERIMENTAL_TOY_ONLY, "
            f"got {result['overall_verdict']}"
        )

    def test_thermal_toy_with_gate6_gives_experimental_toy_only(self):
        """TOY_PHENOMENOLOGICAL + thermal + Gate 6 presente  ADS_EXPERIMENTAL_TOY_ONLY."""
        meta = {
            "family": "ads",
            "d": 3,
            "z_h": 1.0,
            "deformation": 0.0,
            "correlator_type": "TOY_PHENOMENOLOGICAL",
            "bulk_field_name": "phi",
            "operator_name": "O1",
            "m2L2": -1.25,
            "Delta": 2.5,
            "bf_bound_pass": True,
            "uv_source_declared": True,
            "ir_bc_declared": True,
        }
        result = validate_ads_geometry(meta)
        assert result["overall_verdict"] == "ADS_EXPERIMENTAL_TOY_ONLY"

    def test_ads_d3_tfinite_without_gate6_is_template_only(self):
        """
        REGRESION: caso ads_d3_Tfinite con z_h=1.0.
        Gate 6 ausente  ADS_TEMPLATE_ONLY.
        """
        meta = {
            "family": "ads",
            "d": 3,
            "z_h": 1.0,
            "deformation": 0.0,
            "correlator_type": "GEODESIC_APPROXIMATION",
        }
        result = validate_ads_geometry(meta)
        assert result["classification"] == "ads_thermal"
        assert result["correlator_type"] == "GEODESIC_APPROXIMATION"
        assert result["overall_verdict"] == "ADS_TEMPLATE_ONLY", (
            f"ads_d3_Tfinite sin Gate 6 debe ser ADS_TEMPLATE_ONLY, "
            f"got {result['overall_verdict']}"
        )


# ---------------------------------------------------------------------------
# 3. Violacion explicita de cota BF  ADS_CONTRACT_FAIL
# ---------------------------------------------------------------------------

class TestAdsContractFail:
    def test_explicit_bf_fail(self):
        """bf_bound_pass=False fuerza ADS_CONTRACT_FAIL."""
        meta = {
            "family": "ads",
            "d": 3,
            "z_h": 1.0,
            "deformation": 0.0,
            "correlator_type": "GEODESIC_APPROXIMATION",
            "bf_bound_pass": False,
        }
        result = validate_ads_geometry(meta)
        assert result["overall_verdict"] == "ADS_CONTRACT_FAIL"

    def test_operator_with_bf_violation(self):
        """m2L2 < -(d/2)2 para d=3: limite es -2.25."""
        meta = {
            "family": "ads",
            "d": 3,
            "z_h": 1.0,
            "deformation": 0.0,
            "correlator_type": "GEODESIC_APPROXIMATION",
            "operators": [
                {"name": "O1", "m2L2": -3.0},  # -3.0 < -2.25  BF violada
            ],
        }
        result = validate_ads_geometry(meta)
        assert result["overall_verdict"] == "ADS_CONTRACT_FAIL"
        assert result["bf_check"]["pass"] is False

    def test_missing_family_gives_contract_fail(self):
        """Sin campo 'family' en metadata  ADS_CONTRACT_FAIL."""
        meta = {
            "family": "ads",
            "d": None,  # d ausente
            "z_h": 1.0,
            "deformation": 0.0,
            "correlator_type": "GEODESIC_APPROXIMATION",
        }
        result = validate_ads_geometry(meta)
        assert result["overall_verdict"] == "ADS_CONTRACT_FAIL"

    def test_bf_check_function_directly(self):
        """check_bf_bound: limite exacto d=3 es m2L2  -2.25."""
        assert check_bf_bound(-2.25, 3) is True   # exactamente en el limite
        assert check_bf_bound(-2.24, 3) is True   # justo encima
        assert check_bf_bound(-2.26, 3) is False  # violacion

    def test_bf_check_function_d4(self):
        """check_bf_bound: limite d=4 es m2L2  -4.0."""
        assert check_bf_bound(-4.0, 4) is True
        assert check_bf_bound(-4.01, 4) is False


# ---------------------------------------------------------------------------
# 4. Familia no-ads  NOT_ADS (sin errores)
# ---------------------------------------------------------------------------

class TestNonAdsFamily:
    @pytest.mark.parametrize("family", [
        "lifshitz", "hyperscaling", "deformed", "dpbrane",
        "unknown", "rn_ads", "gauss_bonnet", "massive_gravity",
        "linear_axion", "charged_hvlif", "gubser_rocha", "soft_wall",
        "kerr",
    ])
    def test_non_ads_returns_not_ads(self, family):
        meta = {"family": family, "d": 3, "z_h": 1.0}
        result = validate_ads_geometry(meta)
        assert result["overall_verdict"] == "NOT_ADS", (
            f"family={family}: expected NOT_ADS, got {result['overall_verdict']}"
        )

    @pytest.mark.parametrize("family", [
        "lifshitz", "hyperscaling", "dpbrane", "rn_ads",
    ])
    def test_non_ads_classification_is_none(self, family):
        meta = {"family": family, "d": 3, "z_h": 1.0}
        result = validate_ads_geometry(meta)
        assert result["classification"] is None

    def test_non_ads_toy_provenance_is_none_for_stable_schema(self):
        meta = {"family": "kerr", "d": 3, "z_h": 1.0}
        result = validate_ads_geometry(meta)
        assert result["overall_verdict"] == "NOT_ADS"
        assert "toy_provenance" in result
        assert result["toy_provenance"] is None

    def test_non_ads_does_not_raise(self):
        """Validador no lanza excepcion para ninguna familia registrada."""
        for family in [
            "ads", "lifshitz", "hyperscaling", "deformed", "dpbrane",
            "unknown", "rn_ads", "gauss_bonnet", "massive_gravity",
            "linear_axion", "charged_hvlif", "gubser_rocha", "soft_wall",
            "kerr",
        ]:
            meta = {"family": family, "d": 3, "z_h": 1.0}
            result = validate_ads_geometry(meta)
            assert "overall_verdict" in result


# ---------------------------------------------------------------------------
# 5. correlator_type se produce correctamente para la metadata de Stage 01
#    (verificado a traves de family_registry, que es la fuente canonica)
# ---------------------------------------------------------------------------

class TestCorrelatorTypeInStage01Metadata:
    def test_ads_thermal_correlator_type(self):
        """
        Para ads termico, get_correlator_type_for_geometry devuelve
        GEODESIC_APPROXIMATION (el camino real del observable en Stage 01).
        """
        ct = get_correlator_type_for_geometry("ads", use_geodesic=True)
        assert ct == "GEODESIC_APPROXIMATION"

    def test_ads_thermal_classification_from_registry(self):
        """
        classify_ads_geometry con z_h=1.0 devuelve ads_thermal.
        Esto es lo que Stage 01 escribe en HDF5 attrs y manifest.
        """
        cls = classify_ads_geometry("ads", z_h=1.0, deformation=0.0)
        assert cls == "ads_thermal"

    def test_non_ads_classification_is_none(self):
        """Para familias no-ads, classify_ads_geometry retorna None."""
        for family in ["lifshitz", "hyperscaling", "rn_ads", "kerr", "unknown"]:
            cls = classify_ads_geometry(family, z_h=1.0)
            assert cls is None, f"family={family}: expected None, got {cls}"

    def test_non_ads_correlator_type_is_canonical(self):
        """
        get_correlator_type_for_geometry retorna un valor canonico para
        cualquier familia (Stage 01 llama correlator_2pt_geodesic para todas).
        """
        for family in ["ads", "lifshitz", "hyperscaling", "rn_ads", "kerr"]:
            ct = get_correlator_type_for_geometry(family, use_geodesic=True)
            assert ct in CORRELATOR_TYPES, (
                f"family={family}: '{ct}' no esta en CORRELATOR_TYPES"
            )

    def test_non_geodesic_gives_toy_phenomenological(self):
        """use_geodesic=False devuelve TOY_PHENOMENOLOGICAL."""
        ct = get_correlator_type_for_geometry("ads", use_geodesic=False)
        assert ct == "TOY_PHENOMENOLOGICAL"

    def test_family_status_contract(self):
        assert "canonical_strong" in FAMILY_STATUS_STATES
        assert "toy_sandbox" in FAMILY_STATUS_STATES
        assert "realdata_surrogate" in FAMILY_STATUS_STATES
        assert "non_holographic_surrogate" in FAMILY_STATUS_STATES
        assert get_family_status("ads", ads_boundary_mode="gkpw") == "canonical_strong"
        assert get_family_status("ads", ads_boundary_mode="toy") == "toy_sandbox"
        assert get_family_status("lifshitz") == "toy_sandbox"
        assert get_family_status("kerr") == "non_holographic_surrogate"
        assert get_family_status("unknown", source="realdata") == "realdata_surrogate"



# ---------------------------------------------------------------------------
# 6. ads_thermal con GEODESIC_APPROXIMATION (estado actual del repo)
# ---------------------------------------------------------------------------

class TestRepoCurrentState:
    def test_all_ads_prototypes_are_template_only(self):
        """
        REGRESION: los prototipos ads actuales del repo (ads_d3_Tfinite, etc.)
        sin Gate 6 deben resultar en ADS_TEMPLATE_ONLY.

        Clasificacion geometrica: ads_thermal (correcto).
        Veredicto holografico: ADS_TEMPLATE_ONLY (Gate 6 ausente bloquea).
        """
        ads_prototypes = [
            {"name": "ads_d3_Tfinite",      "z_h": 1.0, "d": 3, "deformation": 0.0},
            {"name": "ads_d3_Tfinite_test",  "z_h": 1.0, "d": 3, "deformation": 0.0},
        ]
        for proto in ads_prototypes:
            meta = {
                "family": "ads",
                "d": proto["d"],
                "z_h": proto["z_h"],
                "deformation": proto["deformation"],
                "correlator_type": "GEODESIC_APPROXIMATION",
            }
            result = validate_ads_geometry(meta)
            assert result["classification"] == "ads_thermal", (
                f"{proto['name']}: expected ads_thermal, got {result['classification']}"
            )
            assert result["overall_verdict"] == "ADS_TEMPLATE_ONLY", (
                f"{proto['name']}: Gate 6 ausente debe dar ADS_TEMPLATE_ONLY, "
                f"got {result['overall_verdict']}"
            )


# ---------------------------------------------------------------------------
# 8. Todos los gates completos  ADS_HOLOGRAPHIC_STRONG_PASS
# ---------------------------------------------------------------------------

class TestAdsHolographicStrongPass:
    def test_all_gates_pass(self):
        meta = _meta_ads_all_gates()
        result = validate_ads_geometry(meta)
        assert result["overall_verdict"] == "ADS_HOLOGRAPHIC_STRONG_PASS", (
            f"Expected ADS_HOLOGRAPHIC_STRONG_PASS, got {result['overall_verdict']}"
        )

    def test_all_gates_pass_geometry_and_holo_ok(self):
        meta = _meta_ads_all_gates()
        result = validate_ads_geometry(meta)
        assert result["geometry_gate_status"] == "PASS"
        assert result["holographic_gate_status"] == "PASS"
        assert result["uv_ir_gate_status"] == "PASS"
        assert result["missing_fields"] == []


# ---------------------------------------------------------------------------
# 8b. Politica canonical/experimental
# ---------------------------------------------------------------------------

class TestAdsCanonicalExperimentalPolicy:
    def test_canonical_missing_gate6_is_contract_fail(self):
        meta = {
            "family": "ads",
            "d": 3,
            "z_h": 1.0,
            "deformation": 0.0,
            "ads_pipeline_tier": "canonical",
            "correlator_type": "GKPW_SOURCE_RESPONSE_NUMERICAL",
        }
        result = validate_ads_geometry(meta)
        assert result["ads_pipeline_tier"] == "canonical"
        assert result["overall_verdict"] == "ADS_CONTRACT_FAIL"

    def test_canonical_toy_correlator_is_contract_fail(self):
        meta = {
            "family": "ads",
            "d": 3,
            "z_h": 1.0,
            "deformation": 0.0,
            "ads_pipeline_tier": "canonical",
            "correlator_type": "TOY_PHENOMENOLOGICAL",
            "bulk_field_name": "TOY_NO_BULK_FIELD",
            "operator_name": "O1",
            "m2L2": 0.0,
            "Delta": 3.0,
            "bf_bound_pass": True,
            "uv_source_declared": False,
            "ir_bc_declared": False,
        }
        result = validate_ads_geometry(meta)
        assert result["ads_pipeline_tier"] == "canonical"
        assert result["strong_correlator"] is False
        assert result["overall_verdict"] == "ADS_CONTRACT_FAIL"

    def test_canonical_witten_over_toy_provenance_is_contract_fail(self):
        meta = {
            "family": "ads",
            "d": 3,
            "z_h": 1.0,
            "deformation": 0.0,
            "ads_pipeline_tier": "canonical",
            "ads_boundary_mode": "toy",
            "correlator_type": "HOLOGRAPHIC_WITTEN_DIAGRAM",
            "g2_correlator_type": "GEODESIC_APPROXIMATION",
            "gr_correlator_type": "TOY_PHENOMENOLOGICAL",
            "bulk_field_name": "TOY_NO_BULK_FIELD",
            "operator_name": "O1",
            "m2L2": 0.0,
            "Delta": 3.0,
            "bf_bound_pass": True,
            "uv_source_declared": True,
            "ir_bc_declared": True,
        }
        result = validate_ads_geometry(meta)
        assert result["strong_correlator"] is True
        assert result["toy_provenance"] is True
        assert result["overall_verdict"] == "ADS_CONTRACT_FAIL"

    def test_experimental_witten_over_toy_provenance_is_not_strong(self):
        meta = {
            "family": "ads",
            "d": 3,
            "z_h": 1.0,
            "deformation": 0.0,
            "ads_pipeline_tier": "experimental",
            "ads_boundary_mode": "toy",
            "correlator_type": "HOLOGRAPHIC_WITTEN_DIAGRAM",
            "g2_correlator_type": "GEODESIC_APPROXIMATION",
            "gr_correlator_type": "TOY_PHENOMENOLOGICAL",
            "bulk_field_name": "TOY_NO_BULK_FIELD",
            "operator_name": "O1",
            "m2L2": 0.0,
            "Delta": 3.0,
            "bf_bound_pass": True,
            "uv_source_declared": True,
            "ir_bc_declared": True,
        }
        result = validate_ads_geometry(meta)
        assert result["toy_provenance"] is True
        assert result["overall_verdict"] == "ADS_EXPERIMENTAL_TOY_ONLY"

    def test_experimental_toy_is_permitted_but_not_strong(self):
        meta = {
            "family": "ads",
            "d": 3,
            "z_h": 1.0,
            "deformation": 0.0,
            "ads_pipeline_tier": "experimental",
            "correlator_type": "TOY_PHENOMENOLOGICAL",
            "bulk_field_name": "TOY_NO_BULK_FIELD",
            "operator_name": "O1",
            "m2L2": 0.0,
            "Delta": 3.0,
            "bf_bound_pass": True,
            "uv_source_declared": False,
            "ir_bc_declared": False,
        }
        result = validate_ads_geometry(meta)
        assert result["ads_pipeline_tier"] == "experimental"
        assert result["strong_correlator"] is False
        assert result["overall_verdict"] == "ADS_EXPERIMENTAL_TOY_ONLY"

    def test_canonical_gkpw_gate6_complete_strong_pass(self):
        meta = {
            "family": "ads",
            "d": 3,
            "z_h": 1.0,
            "deformation": 0.0,
            "ads_pipeline_tier": "canonical",
            "correlator_type": "GKPW_SOURCE_RESPONSE_NUMERICAL",
            "bulk_field_name": "phi_O1",
            "operator_name": "O1",
            "m2L2": 0.0,
            "Delta": 3.0,
            "bf_bound_pass": True,
            "uv_source_declared": True,
            "ir_bc_declared": True,
        }
        result = validate_ads_geometry(meta)
        assert result["ads_pipeline_tier"] == "canonical"
        assert result["strong_correlator"] is True
        assert result["overall_verdict"] == "ADS_HOLOGRAPHIC_STRONG_PASS"


# ---------------------------------------------------------------------------
# 9. classify_ads_geometry
# ---------------------------------------------------------------------------

class TestClassifyAdsGeometry:
    def test_thermal(self):
        assert classify_ads_geometry("ads", z_h=1.0, deformation=0.0) == "ads_thermal"

    def test_thermal_any_positive_zh(self):
        assert classify_ads_geometry("ads", z_h=0.01, deformation=0.0) == "ads_thermal"
        assert classify_ads_geometry("ads", z_h=10.0, deformation=0.0) == "ads_thermal"

    def test_toy_boundary_no_horizon(self):
        assert classify_ads_geometry("ads", z_h=None, deformation=0.0) == "ads_toy_boundary"

    def test_toy_boundary_zero_horizon(self):
        assert classify_ads_geometry("ads", z_h=0.0, deformation=0.0) == "ads_toy_boundary"

    def test_deformed(self):
        assert classify_ads_geometry("ads", z_h=None, deformation=0.5) == "ads_deformed"

    def test_deformed_with_horizon(self):
        # deformation toma precedencia sobre horizon
        assert classify_ads_geometry("ads", z_h=1.0, deformation=0.3) == "ads_deformed"

    def test_non_ads_returns_none(self):
        assert classify_ads_geometry("lifshitz", z_h=1.0) is None
        assert classify_ads_geometry("rn_ads", z_h=1.0) is None
        assert classify_ads_geometry("unknown", z_h=None) is None


# ---------------------------------------------------------------------------
# 10 & 11. Constantes canonicas
# ---------------------------------------------------------------------------

class TestCanonicalConstants:
    def test_ads_classifications_complete(self):
        expected = {"ads_pure", "ads_thermal", "ads_deformed", "ads_toy_boundary"}
        assert expected == set(ADS_CLASSIFICATIONS)

    def test_correlator_types_complete(self):
        expected = {
            "HOLOGRAPHIC_WITTEN_DIAGRAM",
            "GKPW_SOURCE_RESPONSE_NUMERICAL",
            "GEODESIC_APPROXIMATION",
            "QNM_SURROGATE",
            "TOY_PHENOMENOLOGICAL",
            "UNKNOWN",
        }
        assert expected == set(CORRELATOR_TYPES)

    def test_ads_verdict_states_complete(self):
        expected = {
            "ADS_HOLOGRAPHIC_STRONG_PASS",
            "ADS_HOLOGRAPHIC_PARTIAL_PASS",
            "ADS_TEMPLATE_ONLY",
            "ADS_THERMAL_TOY_ONLY",
            "ADS_EXPERIMENTAL_TOY_ONLY",
            "ADS_UV_IR_FRAGILE",
            "ADS_CONTRACT_FAIL",
        }
        assert expected == set(ADS_VERDICT_STATES)

    def test_get_correlator_type_default_geodesic(self):
        assert get_correlator_type_for_geometry("ads") == "GEODESIC_APPROXIMATION"
        assert get_correlator_type_for_geometry("lifshitz") == "GEODESIC_APPROXIMATION"

    def test_unknown_correlator_gives_template_only(self):
        """correlator_type=UNKNOWN fuerza ADS_TEMPLATE_ONLY."""
        meta = {
            "family": "ads",
            "d": 3,
            "z_h": 1.0,
            "deformation": 0.0,
            "correlator_type": "UNKNOWN",
        }
        result = validate_ads_geometry(meta)
        assert result["overall_verdict"] == "ADS_TEMPLATE_ONLY"

    def test_uv_ir_fragile_verdict(self):
        """Gate UV/IR fragmentado con el resto de gates completos  ADS_UV_IR_FRAGILE."""
        meta = dict(_meta_ads_all_gates())
        meta["uv_source_declared"] = False   # fragile
        result = validate_ads_geometry(meta)
        assert result["overall_verdict"] == "ADS_UV_IR_FRAGILE"
