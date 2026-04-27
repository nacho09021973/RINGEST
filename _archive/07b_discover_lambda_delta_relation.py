#!/usr/bin/env python3
# 07b_discover_lambda_delta_relation.py
# CUERDAS  Descubrimiento emergente de la relacion _SL  
#
# FILOSOFIA:
#   - Los _SL vienen del solver emergente (bulk geometry  Sturm-Liouville)
#   - Los  vienen de datos EXTERNOS (bootstrap, lattice, exact CFT)
#   - PySR descubre la relacion sin que nosotros impongamos AdS/CFT
#
# ENTRADA:
#   - ground_truth_deltas.json (contiene pares _SL, , d por sistema)
#
# SALIDA:
#   - Ecuacion descubierta por PySR
#   - Comparacion post-hoc con  = d/2 + (d2/4 + _SL)
#
# USO:
#   python 07b_discover_lambda_delta_relation.py \
#       --input ground_truth_deltas.json \
#       --output-dir runs/emergent_dictionary \
#       --iterations 200

import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple

import numpy as np

try:
    from pysr import PySRRegressor
    HAS_PYSR = True
except Exception as exc:
    HAS_PYSR = False
    print(
        "[WARN] PySR no disponible. Solo se hara analisis preliminar. "
        f"Import error: {exc}"
    )


def load_ground_truth(json_path: Path) -> List[Dict[str, Any]]:
    """
    Carga el archivo ground_truth_deltas.json y extrae pares (d, _SL, ).
    Filtra entradas donde lambda_sl es null.
    """
    data = json.loads(json_path.read_text())

    systems = data.get("systems")
    if not isinstance(systems, list):
        raise RuntimeError(
            "INPUT_SCHEMA_MISMATCH: expected top-level 'systems' list"
        )

    pairs = []
    for idx, system in enumerate(systems):
        if not isinstance(system, dict):
            raise RuntimeError(
                f"INPUT_SCHEMA_MISMATCH: systems[{idx}] must be an object"
            )

        is_legacy = "system" in system and "operators" in system
        is_stage06 = (
            "geometry_name" in system
            and "lambda_sl_bulk" in system
            and "Delta_bulk_uv" in system
        )

        if is_legacy:
            if "d" not in system:
                raise RuntimeError(
                    f"INPUT_SCHEMA_MISMATCH: systems[{idx}] missing required key 'd'"
                )

            d = system["d"]
            system_name = system["system"]
            operators = system.get("operators", [])
            if not isinstance(operators, list):
                raise RuntimeError(
                    f"INPUT_SCHEMA_MISMATCH: systems[{idx}].operators must be a list"
                )

            for op in operators:
                lambda_sl = op.get("lambda_sl")
                delta = op.get("Delta")

                # Filtrar si lambda_sl o Delta es null o None
                if lambda_sl is None:
                    continue
                if delta is None:
                    continue

                pairs.append({
                    "system": system_name,
                    "d": d,
                    "lambda_sl": float(lambda_sl),
                    "Delta": float(delta),
                    "name": op.get("name", "unknown"),
                })
            continue

        if is_stage06:
            if "d" not in system:
                raise RuntimeError(
                    f"INPUT_SCHEMA_MISMATCH: systems[{idx}] missing required key 'd'"
                )

            lambda_vals = system["lambda_sl_bulk"]
            delta_vals = system["Delta_bulk_uv"]

            if not isinstance(lambda_vals, list):
                raise RuntimeError(
                    f"INPUT_SCHEMA_MISMATCH: systems[{idx}].lambda_sl_bulk must be a list"
                )
            if not isinstance(delta_vals, list):
                raise RuntimeError(
                    f"INPUT_SCHEMA_MISMATCH: systems[{idx}].Delta_bulk_uv must be a list"
                )
            if len(lambda_vals) != len(delta_vals):
                raise RuntimeError(
                    "INPUT_SCHEMA_MISMATCH: "
                    f"systems[{idx}] has {len(lambda_vals)} lambda_sl_bulk values "
                    f"but {len(delta_vals)} Delta_bulk_uv values"
                )

            d = system["d"]
            system_name = system["geometry_name"]
            for mode_idx, (lambda_sl, delta) in enumerate(zip(lambda_vals, delta_vals)):
                # Mantener el mismo criterio que legacy: ignorar pares incompletos.
                if lambda_sl is None:
                    continue
                if delta is None:
                    continue

                pairs.append({
                    "system": system_name,
                    "d": d,
                    "lambda_sl": float(lambda_sl),
                    "Delta": float(delta),
                    "name": f"mode_{mode_idx}",
                })
            continue

        raise RuntimeError(
            "INPUT_SCHEMA_MISMATCH: "
            f"systems[{idx}] does not match legacy "
            "('system' + 'operators') or stage06 canonical "
            "('geometry_name' + 'lambda_sl_bulk' + 'Delta_bulk_uv') schema"
        )
    
    return pairs


def theoretical_delta(d: float, lambda_sl: float) -> float:
    """
    Formula teorica AdS/CFT (solo para comparacion POST-HOC):
    
         = d/2 + (d2/4 + m2L2)
    
    donde interpretamos _SL  m2L2 (hipotesis a validar).
    
    NOTA: Esta funcion NUNCA se usa en el entrenamiento,
    solo para evaluar si PySR redescubrio algo similar.
    """
    return d/2 + np.sqrt(d**2/4 + lambda_sl)


def analyze_data(pairs: List[Dict]) -> Dict[str, Any]:
    """
    Analisis preliminar de los datos antes de PySR.
    """
    if not pairs:
        return {
            "error": "No hay datos validos",
            "n_points": 0,
            "point_by_point": [],
        }
    
    d_vals = np.array([p["d"] for p in pairs])
    lambda_vals = np.array([p["lambda_sl"] for p in pairs])
    delta_vals = np.array([p["Delta"] for p in pairs])
    
    # Calcular  teorico para comparacion
    delta_theory = np.array([theoretical_delta(d, l) for d, l in zip(d_vals, lambda_vals)])
    
    # Residuos respecto a teoria
    residuals = delta_vals - delta_theory
    
    analysis = {
        "n_points": len(pairs),
        "d_values": sorted(set(d_vals.tolist())),
        "lambda_sl_range": [float(lambda_vals.min()), float(lambda_vals.max())],
        "Delta_range": [float(delta_vals.min()), float(delta_vals.max())],
        "Delta_theoretical_comparison": {
            "formula": "d/2 + sqrt(d^2/4 + lambda_sl)",
            "mean_residual": float(np.mean(residuals)),
            "std_residual": float(np.std(residuals)),
            "max_abs_residual": float(np.max(np.abs(residuals))),
        },
        "point_by_point": []
    }
    
    for i, p in enumerate(pairs):
        analysis["point_by_point"].append({
            "system": p["system"],
            "operator": p["name"],
            "d": p["d"],
            "lambda_sl": p["lambda_sl"],
            "Delta_observed": p["Delta"],
            "Delta_theory": float(delta_theory[i]),
            "residual": float(residuals[i]),
        })
    
    return analysis


def run_pysr_discovery(
    pairs: List[Dict],
    niterations: int = 200,
    maxsize: int = 25,
    seed: int = 42,
) -> Tuple[Any, Dict]:
    """
    Ejecuta PySR para descubrir la relacion _SL, d  
    """
    if not HAS_PYSR:
        return None, {"error": "PySR no disponible"}
    
    # Preparar datos
    d_vals = np.array([p["d"] for p in pairs]).reshape(-1, 1)
    lambda_vals = np.array([p["lambda_sl"] for p in pairs]).reshape(-1, 1)
    X = np.hstack([d_vals, lambda_vals])
    y = np.array([p["Delta"] for p in pairs])
    
    print(f"\n>> Entrenando PySR con {len(pairs)} puntos...")
    print(f"   Features: d, lambda_sl")
    print(f"   Target: Delta")
    print(f"   Iterations: {niterations}")
    
    model = PySRRegressor(
        niterations=niterations,
        populations=20,
        population_size=50,
        ncycles_per_iteration=500,
        binary_operators=["+", "-", "*", "/"],
        unary_operators=["sqrt", "square", "exp", "log"],
        maxsize=maxsize,
        parsimony=0.003,
        complexity_of_constants=1,
        complexity_of_variables=1,
        random_state=seed,
        deterministic=True,
        parallelism="serial",  # Corregido: usar string en lugar de procs/multithreading
        warm_start=False,
        verbosity=1,
        progress=True,
    )
    
    model.fit(X, y, variable_names=["d", "lambda_sl"])
    
    # Extraer resultados
    results = {
        "best_equation": str(model.sympy()),
        "best_loss": float(model.equations_.iloc[-1]["loss"]) if hasattr(model, "equations_") else None,
        "pareto_front": [],
    }
    
    if hasattr(model, "equations_") and model.equations_ is not None:
        for _, row in model.equations_.iterrows():
            results["pareto_front"].append({
                "complexity": int(row["complexity"]),
                "loss": float(row["loss"]),
                "equation": str(row["equation"]),
            })
    
    # Predicciones del mejor modelo
    y_pred = model.predict(X)
    from sklearn.metrics import r2_score, mean_absolute_error
    
    results["metrics"] = {
        "r2": float(r2_score(y, y_pred)),
        "mae": float(mean_absolute_error(y, y_pred)),
    }
    
    return model, results


def main():
    parser = argparse.ArgumentParser(
        description="Descubrir relacion emergente _SL   usando PySR"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="ground_truth_deltas.json",
        help="Archivo JSON con ground truth (d, _SL, )",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="runs/emergent_dictionary",
        help="Directorio de salida",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=200,
        help="Numero de iteraciones de PySR",
    )
    parser.add_argument(
        "--maxsize",
        type=int,
        default=25,
        help="Tamano maximo de expresiones",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Semilla para reproducibilidad",
    )
    parser.add_argument(
        "--analysis-only",
        action="store_true",
        help="Solo analisis preliminar, sin PySR",
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("CUERDAS  DESCUBRIMIENTO EMERGENTE _SL  ")
    print("=" * 70)
    print(f"Input:      {input_path}")
    print(f"Output:     {output_dir}")
    print(f"Iterations: {args.iterations}")
    print("=" * 70)
    print("\nFILOSOFIA:")
    print("  - _SL viene del solver EMERGENTE (sin asumir AdS/CFT)")
    print("  -  viene de datos EXTERNOS (bootstrap/lattice/exact)")
    print("  - PySR descubre la relacion sin imposiciones teoricas")
    print("=" * 70)
    
    # Cargar datos
    if not input_path.exists():
        raise FileNotFoundError(f"No existe: {input_path}")
    
    pairs = load_ground_truth(input_path)
    print(f"\n>> Cargados {len(pairs)} pares (d, _SL, ) validos")
    
    for p in pairs:
        print(f"   {p['system']:15} {p['name']:15} d={p['d']} _SL={p['lambda_sl']:.6f} ={p['Delta']:.6f}")
    
    # Analisis preliminar
    print("\n>> Analisis preliminar...")
    analysis = analyze_data(pairs)
    
    print(f"\n   Comparacion con formula teorica  = d/2 + (d2/4 + _SL):")
    print(f"   (NOTA: esta comparacion es POST-HOC, no se usa en entrenamiento)")
    
    if "error" in analysis:
        print(f"\n   [ERROR] {analysis['error']}")
        print("   Verifica que ground_truth_deltas.json tiene operadores con lambda_sl != null")
        return
    
    for pp in analysis.get("point_by_point", []):
        print(f"   {pp['system']:15} {pp['operator']:15} "
              f"_obs={pp['Delta_observed']:.4f} _theory={pp['Delta_theory']:.4f} "
              f"residual={pp['residual']:+.4f}")
    
    tc = analysis["Delta_theoretical_comparison"]
    print(f"\n   Residuo medio: {tc['mean_residual']:.4f}  {tc['std_residual']:.4f}")
    print(f"   Residuo maximo: {tc['max_abs_residual']:.4f}")
    
    # Guardar analisis
    analysis_path = output_dir / "preliminary_analysis.json"
    analysis_path.write_text(json.dumps(analysis, indent=2))
    print(f"\n   Analisis guardado en: {analysis_path}")
    
    if args.analysis_only:
        print("\n>> Modo analysis-only. No se ejecuta PySR.")
        return
    
    if not HAS_PYSR:
        print("\n>> PySR no disponible. Instala con: pip install pysr")
        return
    
    if len(pairs) < 3:
        print(f"\n>> Solo {len(pairs)} puntos. Se recomienda al menos 3 para PySR.")
        print("   Ejecuta el solver en mas sistemas (Ising 2D, etc.) para mas datos.")
    
    # Ejecutar PySR
    model, results = run_pysr_discovery(
        pairs,
        niterations=args.iterations,
        maxsize=args.maxsize,
        seed=args.seed,
    )
    
    print("\n" + "=" * 70)
    print("RESULTADOS DE PySR")
    print("=" * 70)
    print(f"\n>> Mejor ecuacion descubierta:")
    print(f"    = {results['best_equation']}")
    print(f"\n>> Metricas:")
    print(f"   R2 = {results['metrics']['r2']:.6f}")
    print(f"   MAE = {results['metrics']['mae']:.6f}")
    
    print(f"\n>> Frente de Pareto (complejidad vs error):")
    for eq in results.get("pareto_front", [])[-10:]:  # Ultimas 10
        print(f"   complexity={eq['complexity']:2d}  loss={eq['loss']:.6f}  {eq['equation']}")
    
    # Guardar resultados
    final_report = {
        "timestamp": datetime.now().isoformat(),
        "input_file": str(input_path),
        "n_points": len(pairs),
        "pairs": pairs,
        "preliminary_analysis": analysis,
        "pysr_results": results,
        "philosophy_note": (
            "La relacion fue DESCUBIERTA por PySR, no impuesta. "
            "Los _SL vienen del solver emergente, los  de datos externos (bootstrap/exact). "
            "Si la ecuacion se parece a d/2 + sqrt(d2/4 + _SL), hemos redescubierto AdS/CFT."
        ),
    }
    
    report_path = output_dir / "lambda_delta_discovery_report.json"
    report_path.write_text(json.dumps(final_report, indent=2))
    print(f"\n>> Reporte completo guardado en: {report_path}")
    
    # Guardar modelo PySR si es posible
    if model is not None:
        try:
            import pickle
            model_path = output_dir / "pysr_model.pkl"
            with open(model_path, "wb") as f:
                pickle.dump(model, f)
            print(f">> Modelo PySR guardado en: {model_path}")
        except Exception as e:
            print(f">> No se pudo guardar modelo PySR: {e}")
    
    print("\n" + "=" * 70)
    print("[OK] DESCUBRIMIENTO COMPLETADO")
    print("=" * 70)


if __name__ == "__main__":
    main()
