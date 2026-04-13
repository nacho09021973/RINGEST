from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_stage08():
    key = "stage08_for_test"
    sys.modules.pop(key, None)
    spec = importlib.util.spec_from_file_location(
        key, REPO_ROOT / "08_theory_dictionary_contrast.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    spec.loader.exec_module(mod)
    return mod


def _base_observables():
    return {
        "curvature": {
            "stage03": {
                "fraction_R_negative": 1.0,
                "fraction_einstein_vacuum_compatible": 0.0,
                "mean_einstein_score": 0.55,
                "dominant_verdict": "POSSIBLY_EINSTEIN_WITH_MATTER",
            },
            "stage04": {
                "fraction_category_ringdown": 1.0,
                "fraction_mode_inference": 1.0,
                "fraction_relaxed_correlator_contract": 1.0,
                "fraction_ads_asymptotic_A_logarithmic_uv": 0.0,
                "fraction_holographic_mass_dimension_ok": 0.0,
            },
        },
        "symbolic": {
            "has_universal_d2A": True,
            "fraction_has_cross_terms": 0.33,
            "avg_complexity": 6.0,
        },
        "spectral": {
            "lambda_delta": {
                "degenerate_input": True,
                "insufficient_variation": True,
                "delta_range": [4.0, 4.0],
            }
        },
    }


class TestTheoryDictionaryStage08(unittest.TestCase):
    def setUp(self):
        self.s08 = _load_stage08()
        self.theories = self.s08.load_theory_dictionary_config(
            REPO_ROOT / "configs" / "theory_dictionary" / "theory_dictionary_v1.json"
        )

    def test_theory_dictionary_schema(self):
        for theory in self.theories:
            for field in self.s08.REQUIRED_THEORY_FIELDS:
                self.assertIn(field, theory, f"{theory.get('theory_id')} missing {field}")

    def test_context_only_theory_is_not_scored_as_evaluable(self):
        theory = next(t for t in self.theories if t["theory_id"] == "qnm_shift_effective")
        result = self.s08.evaluate_theory(theory, _base_observables())
        self.assertFalse(result["evaluable"])
        self.assertIsNone(result["final_score"])
        self.assertEqual(result["verdict"], "not_evaluable")

    def test_degenerate_lambda_delta_is_marked_inconclusive(self):
        theory = {
            "theory_id": "spectral_probe",
            "family": "test_family",
            "version": "v1",
            "status": "evaluable",
            "assumptions": [],
            "domain_of_validity": [],
            "required_observables": ["spectral.lambda_delta.degenerate_input"],
            "predicted_relations": [],
            "predicted_signatures": [],
            "free_parameters": [],
            "comparison_protocol": [
                {
                    "rule_id": "spectral_non_degenerate",
                    "observable": "spectral.lambda_delta.degenerate_input",
                    "operator": "eq",
                    "value": False,
                    "weight": 1.0,
                    "evidence_if_pass": "non-degenerate",
                    "evidence_if_fail": "degenerate_input",
                }
            ],
            "pass_fail_policy": {
                "base_complexity_penalty": 0.0,
                "free_parameter_penalty": 0.0,
                "supported_if_score_gte": 2.5,
                "weakly_supported_if_score_gte": 0.75,
                "tension_if_score_lte": -10.0,
                "contradicted_if_score_lte": -10.0,
            },
            "notes": [],
        }
        result = self.s08.evaluate_theory(theory, _base_observables())
        self.assertEqual(result["verdict"], "inconclusive")
        self.assertEqual(result["supporting_evidence"], [])
        self.assertEqual(len(result["contradicting_evidence"]), 1)
        self.assertEqual(result["contradicting_evidence"][0]["message"], "degenerate_input")

    def test_theory_contrast_summary_is_reproducible(self):
        observables = _base_observables()
        summary_a = self.s08.build_theory_contrast_summary(self.theories, observables)
        summary_b = self.s08.build_theory_contrast_summary(self.theories, observables)
        self.assertEqual(summary_a, summary_b)

    def test_missing_observables_do_not_count_as_support(self):
        theory = {
            "theory_id": "missing_probe",
            "family": "test_family",
            "version": "v1",
            "status": "evaluable",
            "assumptions": [],
            "domain_of_validity": [],
            "required_observables": ["spectral.lambda_delta.nonexistent_metric"],
            "predicted_relations": [],
            "predicted_signatures": [],
            "free_parameters": [],
            "comparison_protocol": [
                {
                    "rule_id": "missing_rule",
                    "observable": "spectral.lambda_delta.nonexistent_metric",
                    "operator": "eq",
                    "value": True,
                    "weight": 1.0,
                    "evidence_if_pass": "should never happen",
                    "evidence_if_fail": "missing observable must not count as support",
                }
            ],
            "pass_fail_policy": {
                "base_complexity_penalty": 0.0,
                "free_parameter_penalty": 0.0,
                "supported_if_score_gte": 2.5,
                "weakly_supported_if_score_gte": 0.75,
                "tension_if_score_lte": -0.5,
                "contradicted_if_score_lte": -2.0,
            },
            "notes": [],
        }
        result = self.s08.evaluate_theory(theory, _base_observables())
        self.assertFalse(result["evaluable"])
        self.assertEqual(result["supporting_evidence"], [])
        self.assertIsNone(result["final_score"])


if __name__ == "__main__":
    unittest.main()
