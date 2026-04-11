#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from contracts.common_models import (
    ContractValidationError,
    ManifestArtifactModel,
    ManifestModel,
    StageSummaryModel,
    write_manifest,
    write_stage_summary,
)


SCRIPT_VERSION = "08_theory_dictionary_contrast.py v1.0"
REQUIRED_THEORY_FIELDS = [
    "theory_id",
    "family",
    "version",
    "status",
    "assumptions",
    "domain_of_validity",
    "required_observables",
    "predicted_relations",
    "predicted_signatures",
    "free_parameters",
    "comparison_protocol",
    "pass_fail_policy",
    "notes",
]
REQUIRED_INPUTS = {
    "stage03": "03_discover_bulk_equations/einstein_discovery_summary.json",
    "stage04": "04_geometry_physics_contracts/geometry_contracts_summary.json",
    "stage05": "05_analyze_bulk_equations/bulk_equations_analysis.json",
    "stage06": "06_build_bulk_eigenmodes_dataset/bulk_modes_dataset.json",
    "stage07b": "07b_discover_lambda_delta_relation/lambda_delta_discovery_report.json",
}
CONTEXT_ONLY_STATUS = "context_only"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _mean(values: List[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _variance(values: List[float]) -> float | None:
    if not values:
        return None
    mu = _mean(values)
    if mu is None:
        return None
    return sum((x - mu) ** 2 for x in values) / len(values)


def _fraction_true(items: List[bool]) -> float | None:
    if not items:
        return None
    return sum(1 for x in items if x) / len(items)


def _dominant(items: List[str]) -> str | None:
    if not items:
        return None
    counter = Counter(items)
    return sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def _get_path(payload: Dict[str, Any], dotted: str) -> Tuple[bool, Any]:
    current: Any = payload
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def load_required_inputs(input_root: Path) -> Dict[str, Dict[str, Any]]:
    bundle: Dict[str, Dict[str, Any]] = {}
    for key, relative in REQUIRED_INPUTS.items():
        path = input_root / relative
        if not path.exists():
            raise FileNotFoundError(f"Missing contractual input for {key}: {path}")
        bundle[key] = {
            "path": path,
            "data": json.loads(path.read_text(encoding="utf-8")),
            "sha256": sha256_file(path),
        }
    return bundle


def summarize_stage03(stage03: Dict[str, Any]) -> Dict[str, Any]:
    geometries = stage03.get("geometries", [])
    validations = [g.get("validation", {}) for g in geometries]
    verdicts = [v.get("verdict") for v in validations if v.get("verdict") is not None]
    scores = [float(v["einstein_score"]) for v in validations if v.get("einstein_score") is not None]
    return {
        "n_geometries": len(geometries),
        "fraction_R_constant": _fraction_true([bool(v.get("R_constant")) for v in validations]),
        "fraction_R_negative": _fraction_true([bool(v.get("R_negative")) for v in validations]),
        "fraction_einstein_vacuum_compatible": _fraction_true(
            [bool(v.get("einstein_vacuum_compatible")) for v in validations]
        ),
        "mean_einstein_score": _mean(scores),
        "dominant_verdict": _dominant(verdicts),
    }


def summarize_stage04(stage04: Dict[str, Any]) -> Dict[str, Any]:
    contracts = stage04.get("contracts", [])
    categories = [c.get("category") for c in contracts]
    modes = [c.get("mode") for c in contracts]
    relaxed_modes = [
        c.get("correlator_structure", {}).get("contract_mode")
        == "ringdown_inference_relaxed_v1"
        for c in contracts
    ]
    return {
        "n_contracts": len(contracts),
        "fraction_category_ringdown": _fraction_true([category == "ringdown" for category in categories]),
        "fraction_mode_inference": _fraction_true([mode == "inference" for mode in modes]),
        "fraction_relaxed_correlator_contract": _fraction_true(relaxed_modes),
        "fraction_ads_einstein_R_is_constant": _fraction_true(
            [bool(c.get("ads_einstein", {}).get("R_is_constant")) for c in contracts]
        ),
        "fraction_ads_asymptotic_A_logarithmic_uv": _fraction_true(
            [bool(c.get("ads_asymptotic", {}).get("A_logarithmic_uv")) for c in contracts]
        ),
        "fraction_holographic_mass_dimension_ok": _fraction_true(
            [bool(c.get("holographic", {}).get("mass_dimension_ok")) for c in contracts]
        ),
        "fraction_holographic_conformal_symmetry_ok": _fraction_true(
            [bool(c.get("holographic", {}).get("conformal_symmetry_ok")) for c in contracts]
        ),
    }


def summarize_stage05(stage05: Dict[str, Any]) -> Dict[str, Any]:
    by_family = stage05.get("by_family", {})
    entries = []
    for family_entries in by_family.values():
        entries.extend(family_entries)
    structures = [entry.get("structure", {}) for entry in entries]
    complexities = [float(s["complexity"]) for s in structures if s.get("complexity") is not None]
    universal_terms = sorted(stage05.get("patterns", {}).get("universal_terms", []))
    return {
        "n_entries": len(entries),
        "universal_terms": universal_terms,
        "has_universal_d2A": "has_d2A" in universal_terms,
        "fraction_has_d2A": _fraction_true([bool(s.get("has_d2A")) for s in structures]),
        "fraction_has_cross_terms": _fraction_true([bool(s.get("has_cross_terms")) for s in structures]),
        "avg_complexity": _mean(complexities),
        "family_specific_terms": stage05.get("patterns", {}).get("family_specific_terms", {}),
    }


def summarize_stage06(stage06: Dict[str, Any]) -> Dict[str, Any]:
    systems = stage06.get("systems", [])
    mode_counts = [int(system.get("n_modes", 0)) for system in systems]
    families = sorted({system.get("family", "unknown") for system in systems})
    lambda_sources = Counter(system.get("lambda_source", "unknown") for system in systems)
    return {
        "n_systems": len(systems),
        "n_modes_total": sum(mode_counts),
        "families": families,
        "lambda_source_counts": dict(sorted(lambda_sources.items())),
    }


def summarize_stage07b(stage07b: Dict[str, Any]) -> Dict[str, Any]:
    analysis = stage07b.get("preliminary_analysis", {})
    pairs = stage07b.get("pairs", [])
    delta_values = [float(pair["Delta"]) for pair in pairs if pair.get("Delta") is not None]
    lambda_values = [float(pair["lambda_sl"]) for pair in pairs if pair.get("lambda_sl") is not None]
    delta_variance = _variance(delta_values)
    delta_min = min(delta_values) if delta_values else None
    delta_max = max(delta_values) if delta_values else None
    delta_range = [delta_min, delta_max] if delta_values else None
    lambda_range = analysis.get("lambda_sl_range")
    if lambda_range is None and lambda_values:
        lambda_range = [min(lambda_values), max(lambda_values)]
    delta_range_from_analysis = analysis.get("Delta_range")
    if delta_range_from_analysis is None:
        delta_range_from_analysis = delta_range
    degenerate_input = False
    if delta_range_from_analysis is not None:
        degenerate_input = delta_range_from_analysis[0] == delta_range_from_analysis[1]
    if delta_variance is not None and delta_variance == 0.0:
        degenerate_input = True
    best_equation = stage07b.get("pysr_results", {}).get("best_equation")
    return {
        "n_pairs": len(pairs),
        "d_values": analysis.get("d_values", []),
        "lambda_range": lambda_range,
        "delta_range": delta_range_from_analysis,
        "delta_variance": delta_variance,
        "lambda_variance": _variance(lambda_values),
        "best_equation": best_equation,
        "degenerate_input": degenerate_input,
        "insufficient_variation": degenerate_input,
        "nonconstant_discovery": best_equation is not None and str(best_equation).strip() != "4.00000000000000",
    }


def normalize_observables(bundle: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "curvature": {
            "stage03": summarize_stage03(bundle["stage03"]["data"]),
            "stage04": summarize_stage04(bundle["stage04"]["data"]),
        },
        "symbolic": summarize_stage05(bundle["stage05"]["data"]),
        "spectral": {
            "stage06": summarize_stage06(bundle["stage06"]["data"]),
            "lambda_delta": summarize_stage07b(bundle["stage07b"]["data"]),
        },
    }


def load_theory_dictionary_config(config_path: Path) -> List[Dict[str, Any]]:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    theories = payload.get("theories")
    if not isinstance(theories, list):
        raise RuntimeError("Theory dictionary config must contain top-level 'theories' list")
    validate_theory_dictionary(theories)
    return sorted(theories, key=lambda theory: theory["theory_id"])


def validate_theory_dictionary(theories: List[Dict[str, Any]]) -> None:
    for theory in theories:
        missing = [field for field in REQUIRED_THEORY_FIELDS if field not in theory]
        if missing:
            raise RuntimeError(
                f"THEORY_DICTIONARY_SCHEMA_ERROR: {theory.get('theory_id', '<missing_id>')} "
                f"missing fields {missing}"
            )


def build_observable_matrix(
    theories: List[Dict[str, Any]], observables: Dict[str, Any]
) -> List[Dict[str, Any]]:
    matrix = []
    for theory in theories:
        available = []
        missing = []
        for observable in theory["required_observables"]:
            present, _ = _get_path(observables, observable)
            if present:
                available.append(observable)
            else:
                missing.append(observable)
        evaluable = theory["status"] != CONTEXT_ONLY_STATUS and len(available) > 0
        matrix.append(
            {
                "theory_id": theory["theory_id"],
                "status": theory["status"],
                "required_observables": theory["required_observables"],
                "available_observables": available,
                "missing_observables": missing,
                "evaluable": evaluable,
            }
        )
    return matrix


def _rule_matches(observed: Any, operator: str, expected: Any) -> bool:
    if operator == "eq":
        return observed == expected
    if operator == "min":
        return observed is not None and observed >= expected
    if operator == "max":
        return observed is not None and observed <= expected
    if operator == "in":
        return observed in expected
    if operator == "contains":
        return isinstance(observed, list) and expected in observed
    raise RuntimeError(f"Unsupported comparison operator: {operator}")


def evaluate_theory(theory: Dict[str, Any], observables: Dict[str, Any]) -> Dict[str, Any]:
    required = list(theory["required_observables"])
    available_required = []
    missing_required = []
    for observable in required:
        present, _ = _get_path(observables, observable)
        if present:
            available_required.append(observable)
        else:
            missing_required.append(observable)

    if theory["status"] == CONTEXT_ONLY_STATUS:
        return {
            "theory_id": theory["theory_id"],
            "evaluable": False,
            "n_required_observables": len(required),
            "n_available_observables": len(available_required),
            "supporting_evidence": [],
            "contradicting_evidence": [],
            "missing_evidence": [
                {
                    "reason": "theory status is context_only; excluded from competitive scoring",
                }
            ],
            "fit_score": None,
            "complexity_penalty": None,
            "final_score": None,
            "verdict": "not_evaluable",
        }

    supporting = []
    contradicting = []
    missing = []
    support_total = 0.0
    contradiction_total = 0.0

    for rule in theory["comparison_protocol"]:
        observable = rule["observable"]
        present, observed = _get_path(observables, observable)
        if not present:
            missing.append(
                {
                    "rule_id": rule["rule_id"],
                    "observable": observable,
                    "reason": "observable missing in this run",
                    "weight": rule["weight"],
                }
            )
            continue

        matched = _rule_matches(observed, rule["operator"], rule["value"])
        evidence = {
            "rule_id": rule["rule_id"],
            "observable": observable,
            "observed": observed,
            "expected": rule["value"],
            "operator": rule["operator"],
            "weight": rule["weight"],
        }
        if matched:
            evidence["message"] = rule["evidence_if_pass"]
            supporting.append(evidence)
            support_total += float(rule["weight"])
        else:
            evidence["message"] = rule["evidence_if_fail"]
            contradicting.append(evidence)
            contradiction_total += float(rule["weight"])

    if not available_required:
        return {
            "theory_id": theory["theory_id"],
            "evaluable": False,
            "n_required_observables": len(required),
            "n_available_observables": 0,
            "supporting_evidence": supporting,
            "contradicting_evidence": contradicting,
            "missing_evidence": missing + [
                {
                    "reason": "no required observables available; no competitive score assigned",
                }
            ],
            "fit_score": None,
            "complexity_penalty": None,
            "final_score": None,
            "verdict": "not_evaluable",
        }

    fit_score = support_total - contradiction_total
    complexity_penalty = float(theory["pass_fail_policy"].get("base_complexity_penalty", 0.0))
    complexity_penalty += float(
        theory["pass_fail_policy"].get("free_parameter_penalty", 0.0)
    ) * len(theory.get("free_parameters", []))
    final_score = fit_score - complexity_penalty

    if not supporting and missing and not contradicting:
        verdict = "inconclusive"
    elif final_score >= float(theory["pass_fail_policy"]["supported_if_score_gte"]):
        verdict = "supported"
    elif final_score >= float(theory["pass_fail_policy"]["weakly_supported_if_score_gte"]):
        verdict = "weakly_supported"
    elif final_score <= float(theory["pass_fail_policy"]["contradicted_if_score_lte"]):
        verdict = "contradicted"
    elif final_score <= float(theory["pass_fail_policy"]["tension_if_score_lte"]):
        verdict = "tension"
    else:
        verdict = "inconclusive"

    return {
        "theory_id": theory["theory_id"],
        "evaluable": True,
        "n_required_observables": len(required),
        "n_available_observables": len(available_required),
        "supporting_evidence": supporting,
        "contradicting_evidence": contradicting,
        "missing_evidence": missing,
        "fit_score": fit_score,
        "complexity_penalty": complexity_penalty,
        "final_score": final_score,
        "verdict": verdict,
    }


def build_theory_contrast_summary(
    theories: List[Dict[str, Any]], observables: Dict[str, Any]
) -> Dict[str, Any]:
    results = [
        evaluate_theory(theory, observables)
        for theory in sorted(theories, key=lambda item: item["theory_id"])
    ]
    results = sorted(results, key=lambda item: item["theory_id"])
    verdict_counts = Counter(result["verdict"] for result in results)
    return {
        "contract": "theory_contrast_summary_v1",
        "theory_results": results,
        "verdict_counts": dict(sorted(verdict_counts.items())),
        "observables_snapshot": observables,
        "scoring_policy": {
            "fit_score": "sum(support weights) - sum(contradiction weights)",
            "complexity_penalty": "base_complexity_penalty + free_parameter_penalty * n_free_parameters",
            "final_score": "fit_score - complexity_penalty",
            "notes": [
                "missing observables never add support",
                "context_only theories are excluded from competitive scoring",
                "degenerate lambda-Delta inputs can only generate contradiction or missing evidence, never support by absence of variation",
            ],
        },
    }


def write_scores_csv(path: Path, summary: Dict[str, Any]) -> None:
    rows = summary["theory_results"]
    fieldnames = [
        "theory_id",
        "evaluable",
        "n_required_observables",
        "n_available_observables",
        "fit_score",
        "complexity_penalty",
        "final_score",
        "verdict",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field) for field in fieldnames})


def build_stage_summary(
    input_root: Path,
    output_dir: Path,
    theories: List[Dict[str, Any]],
    summary: Dict[str, Any],
) -> StageSummaryModel:
    return StageSummaryModel(
        stage_name="08_theory_dictionary_contrast",
        script=SCRIPT_VERSION,
        status="OK",
        exit_code=0,
        input_root=str(input_root.resolve()),
        output_dir=str(output_dir.resolve()),
        n_theories=len(theories),
        n_evaluable=sum(1 for item in summary["theory_results"] if item["evaluable"]),
        n_not_evaluable=sum(1 for item in summary["theory_results"] if not item["evaluable"]),
        verdict_counts=summary["verdict_counts"],
        post_hoc_only=True,
        upstream_training_contamination="forbidden_by_design",
        created_at=utc_now(),
    )


def build_manifest(
    input_root: Path,
    output_dir: Path,
    input_bundle: Dict[str, Dict[str, Any]],
    outputs: Dict[str, Path],
) -> ManifestModel:
    return ManifestModel(
        created_at=utc_now(),
        script=SCRIPT_VERSION,
        stage="08_theory_dictionary_contrast",
        input_root=str(input_root.resolve()),
        inputs={
            key: ManifestArtifactModel(
                path=str(item["path"].resolve()),
                sha256=item["sha256"],
            )
            for key, item in sorted(input_bundle.items())
        },
        outputs={
            key: ManifestArtifactModel(
                path=str(path.resolve()),
                sha256=sha256_file(path),
            )
            for key, path in sorted(outputs.items())
        },
        notes=[
            "Stage 08 is strictly post-hoc.",
            "No theory is used as label, prior, or regularizer upstream.",
        ],
    )


def default_config_path() -> Path:
    return Path(__file__).resolve().parent / "configs" / "theory_dictionary" / "theory_dictionary_v1.json"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Stage 08: explicit post-hoc contrast between empirical artifacts and theory families."
    )
    parser.add_argument(
        "--input-root",
        required=True,
        help="Run root containing stages 03/04/05/06/07b, e.g. runs/reopen_v1",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where stage 08 artifacts will be written",
    )
    parser.add_argument(
        "--dictionary-config",
        default=str(default_config_path()),
        help="Path to the explicit theory dictionary config JSON",
    )
    args = parser.parse_args()

    input_root = Path(args.input_root).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    input_bundle = load_required_inputs(input_root)
    observables = normalize_observables(input_bundle)
    theories = load_theory_dictionary_config(Path(args.dictionary_config).resolve())
    observable_matrix = build_observable_matrix(theories, observables)
    contrast_summary = build_theory_contrast_summary(theories, observables)

    theory_dictionary_path = output_dir / "theory_dictionary.json"
    observable_matrix_path = output_dir / "theory_observable_matrix.json"
    contrast_summary_path = output_dir / "theory_contrast_summary.json"
    scores_csv_path = output_dir / "theory_scores.csv"
    stage_summary_path = output_dir / "stage_summary.json"

    write_json(theory_dictionary_path, theories)
    write_json(observable_matrix_path, observable_matrix)
    write_json(contrast_summary_path, contrast_summary)
    write_scores_csv(scores_csv_path, contrast_summary)

    stage_summary = build_stage_summary(input_root, output_dir, theories, contrast_summary)
    write_stage_summary(stage_summary, stage_summary_path)

    outputs = {
        "theory_dictionary_json": theory_dictionary_path,
        "theory_observable_matrix_json": observable_matrix_path,
        "theory_contrast_summary_json": contrast_summary_path,
        "theory_scores_csv": scores_csv_path,
        "stage_summary_json": stage_summary_path,
    }
    manifest_path = output_dir / "manifest.json"
    manifest = build_manifest(input_root, output_dir, input_bundle, outputs)
    write_manifest(manifest, manifest_path)

    print("=" * 70)
    print("THEORY DICTIONARY CONTRAST  —  Stage 08")
    print(f"Script: {SCRIPT_VERSION}")
    print(f"Input root: {input_root}")
    print(f"Output dir: {output_dir}")
    print(f"Theories: {len(theories)}")
    print(f"Evaluable: {stage_summary.n_evaluable}")
    print(f"Not evaluable: {stage_summary.n_not_evaluable}")
    print(f"Verdicts: {stage_summary.verdict_counts}")
    print(f"Spectral degenerate input: {observables['spectral']['lambda_delta']['degenerate_input']}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ContractValidationError as exc:
        print(f"[CONTRACT_ERROR] {exc}", file=sys.stderr)
        raise SystemExit(2)
