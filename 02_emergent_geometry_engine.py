#!/usr/bin/env python3
from __future__ import annotations

# 02_emergent_geometry_engine.py
# CUERDAS AfAE'A,AcAfAcAca,!A!A,A!AfAcAcaEURsA!A,A? Bloque A: GeometrAfAE'A+aEUR(TM)AfaEURsA,A-a emergente (motor de reconstrucciAfAE'A+aEUR(TM)AfaEURsA,A3n) V 2.3
#
#
# CAMBIOS EN V 2.3 (FIX CONSISTENCIA GEOMETRICA):
#   - ELIMINADO decoder_R independiente
#   - R(z) se calcula DETERMINISTICAMENTE desde A(z) y f(z) usando
#     la formula de geometria diferencial basica (NO ecuaciones de Einstein)
#   - Esto garantiza que la curvatura sea consistente con la metrica
#   - NO inyecta fisica: solo matematica de variedades Riemannianas
#   - Reduccion de parametros del modelo (menos sobreajuste)
#
# CAMBIOS EN V 2.2 (respecto a V 2.1):
#   - AAfAE'A+aEUR(TM)A+-adido modo --mode {train, inference}
#   - En mode='inference': carga checkpoint sandbox, procesa boundary-only, genera .h5
#   - No se accede a bulk_truth en inference (honestidad preservada)
#   - Salida inference: .h5 en geometry_emergent/ con contrato 3.3 del README
#
# CAMBIOS PRINCIPALES EN V 2.1:
#   - PriorizaciAfAE'A+aEUR(TM)AfaEURsA,A3n de A(z) y f(z) sobre R(z) y clasificaciAfAE'A+aEUR(TM)AfaEURsA,A3n de family
#   - Pesos de loss expuestos como constantes configurables al inicio del script
#   - NormalizaciAfAE'A+aEUR(TM)AfaEURsA,A3n robusta mejorada (z-score con clipping para R)
#   - Scheduler CosineAnnealing actualizado por EPOCH (no por batch)
#   - Bucle de entrenamiento refactorizado en funciones auxiliares
#   - MAfAE'A+aEUR(TM)AfaEURsA,A(C)tricas RAfAE'Aca,!A!A2(A), RAfAE'Aca,!A!A2(f) calculadas y mostradas periAfAE'A+aEUR(TM)AfaEURsA,A3dicamente en test
#   - Arquitectura refinada: factor residual adaptativo, mejor inicializaciAfAE'A+aEUR(TM)AfaEURsA,A3n
#   - Physics loss documentada con explicaciAfAE'A+aEUR(TM)AfaEURsA,A3n de cada tAfAE'A+aEUR(TM)AfaEURsA,A(C)rmino
#   - Summary JSON extendido con mAfAE'A+aEUR(TM)AfaEURsA,A(C)tricas por family y evoluciAfAE'A+aEUR(TM)AfaEURsA,A3n temporal
#
# Objective:
#   Aprender la geometrAfAE'A+aEUR(TM)AfaEURsA,A-a de bulk "emergente" a partir de datos de frontera (CFT),
#   sin acceso directo a la mAfAE'A+aEUR(TM)AfaEURsA,A(C)trica real ni al solver de campo.
#   Produce campos A(z), f(z), R(z), etc. para cada universo.
#
# Inputs:
#   - runs/sandbox_geometries/boundary/*.h5
#       * Datos CFT por universo: grids, correladores, espectros, etc.
#   - Opcional: configuraciAfAE'A+aEUR(TM)AfaEURsA,A3n de red y entrenamiento:
#       * n_epochs, device, seed, arquitectura, regularizaciAfAE'A+aEUR(TM)AfaEURsA,A3n, ...
#
# Outputs:
#   runs/emergent_geometry/
#     geometry_emergent/
#       <system_name>_emergent.h5
#         - z_grid, A_emergent, f_emergent, R_emergent, ...
#         - metadatos: family_pred, scores, etc.
#     emergent_geometry_summary.json
#       - MAfAE'A+aEUR(TM)AfaEURsA,A(C)tricas de ajuste (train/test), RAfAE'Aca,!A!A2, errores, family predicha, ...
#
# RELACIAfAE'A+aEUR(TM)AfAcAcaEURsA!A...aEURoeN CON OTROS SCRIPTS
#   - Usa como input: boundary/ generados por 01_generate_sandbox_geometries.py
#   - Proporciona geometrAfAE'A+aEUR(TM)AfaEURsA,A-a emergente a:
#       * 03_discover_bulk_equations.py
#       * 04_geometry_physics_contracts.py
#       * 06_build_bulk_eigenmodes_dataset.py
#       * 08_build_holographic_dictionary.py
#
# HONESTIDAD
#   - No se inyecta bulk_truth en la loss ni en las features de entrenamiento.
#   - Cualquier comparaciAfAE'A+aEUR(TM)AfaEURsA,A3n con bulk_truth sucede aguas abajo, en contratos y anAfAE'A+aEUR(TM)AfaEURsA,A!lisis.
#   - En inference mode, NO se accede a bulk_truth (CuerdasDataLoader lo bloquea).

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

# Registro canónico de familias — fuente de verdad para FAMILY_MAP
try:
    from family_registry import FAMILY_MAP as _REGISTRY_FAMILY_MAP
    _HAS_FAMILY_REGISTRY = True
except ImportError:
    _REGISTRY_FAMILY_MAP = {}
    _HAS_FAMILY_REGISTRY = False

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

# Import local IO module for run manifest support
try:
    from cuerdas_io import write_run_manifest
    HAS_CUERDAS_IO = True
except ImportError:
    HAS_CUERDAS_IO = False

# V3 contract: feature support audit (C2 — QNM block removed)
HAS_FEATURE_SUPPORT = False
FEATURE_NAMES_V3 = None
CRITICAL_FEATURES_V3 = None
audit_feature_support = None
audit_train_feature_support = None
SUPPORT_MODE_STRICT = "strict"
SUPPORT_MODE_PERMISSIVE_OOD = "permissive_ood"
try:
    from feature_support import (
        FEATURE_NAMES_V3,
        CRITICAL_FEATURES_V3,
        audit_feature_support,
        audit_train_feature_support,
        SUPPORT_MODE_STRICT,
        SUPPORT_MODE_PERMISSIVE_OOD,
    )
    HAS_FEATURE_SUPPORT = True
except ImportError:
    pass


def _resolve_train_audit_critical_features(
    feature_names,
    X_std_raw,
    critical_features,
    tiny_std_threshold: float = 1e-6,
):
    """Contextualize critical train-audit features for cohorts with uniform horizons."""
    critical_features_for_audit = list(critical_features)
    names = list(feature_names)
    sigma = np.asarray(X_std_raw, dtype=float).flatten()
    info_message = None

    if "has_horizon" in critical_features_for_audit and "has_horizon" in names:
        idx_has_horizon = names.index("has_horizon")
        if sigma[idx_has_horizon] < tiny_std_threshold:
            critical_features_for_audit.remove("has_horizon")
            info_message = (
                "[INFO] TRAIN_FEATURE_SUPPORT_CONTEXT: has_horizon is constant in this "
                "cohort; downgraded from critical to contextual warning"
            )

    return critical_features_for_audit, info_message


# ============================================================
# CONFIGURACIAfAE'A+aEUR(TM)AfAcAcaEURsA!A...aEURoeN DE PESOS DE LOSS (MODIFICAR AQUAfAE'A+aEUR(TM)AfaEURsA,A?)
# ============================================================
# Estos pesos controlan la importancia relativa de cada tAfAE'A+aEUR(TM)AfaEURsA,A(C)rmino.
# V2.1: Prioriza A y f sobre R y family para datasets pequeAfAE'A+aEUR(TM)A+-os.

LOSS_WEIGHT_A = 2.0          # Warp factor A(z) - PRIORITARIO
LOSS_WEIGHT_F = 2.0          # Blackening factor f(z) - PRIORITARIO
LOSS_WEIGHT_R = 0.001        # Escalar de Ricci R(z) - MUY BAJO (secundario)
LOSS_WEIGHT_ZH = 0.1         # PosiciAfAE'A+aEUR(TM)AfaEURsA,A3n del horizonte z_h - BAJO
LOSS_WEIGHT_FAMILY = 0.05    # ClasificaciAfAE'A+aEUR(TM)AfaEURsA,A3n de family - MUY BAJO
LOSS_WEIGHT_PHYSICS = 0.05   # Regularización física genérica (solo muestras con bulk_truth)
LOSS_WEIGHT_PHYSICS_ADS = 0.02  # Regularización AdS-específica (solo muestras ads, via ads_mask)

# Learning rate y scheduler
LEARNING_RATE = 1e-3
WEIGHT_DECAY = 1e-4
GRAD_CLIP_NORM = 1.0

# Frecuencia de evaluaciAfAE'A+aEUR(TM)AfaEURsA,A3n en test (cada N epochs)
EVAL_FREQUENCY = 50

# Semántica operativa de family en inference sobre cohortes OOD/unificadas:
# publicar compatibilidad y abstenerse salvo soporte suficiente.
FAMILY_OUTPUT_SEMANTICS = "compatibility_with_abstention"
FAMILY_CONFIDENCE_TOP1_THRESHOLD = 0.60
FAMILY_CONFIDENCE_MARGIN_THRESHOLD = 0.20


# ============================================================
# UTILIDADES VARIAS
# ============================================================

def set_torch_seed(seed: int = 42):
    """Fija semillas para reproducibilidad."""
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)


def resolve_runtime_device(requested_device: str) -> torch.device:
    """
    Resuelve el dispositivo de ejecución con fallback no intrusivo a CPU.

    Reglas:
    - Si se pide CUDA y no está disponible, avisa y cae a CPU.
    - Si el string de dispositivo es inválido, avisa y cae a CPU.
    - Siempre imprime el dispositivo realmente usado.
    """
    requested = (requested_device or "cpu").strip().lower()

    if requested.startswith("cuda") and not torch.cuda.is_available():
        print(
            f"[WARN] Se solicitó --device {requested_device!r}, pero CUDA no está disponible. "
            "Fallback a cpu."
        )
        resolved = torch.device("cpu")
        print(f"[INFO] Dispositivo real en uso: {resolved}")
        return resolved

    try:
        resolved = torch.device(requested)
    except Exception as exc:
        print(
            f"[WARN] Dispositivo inválido {requested_device!r}: {exc}. "
            "Fallback a cpu."
        )
        resolved = torch.device("cpu")
        print(f"[INFO] Dispositivo real en uso: {resolved}")
        return resolved

    if resolved.type == "cuda":
        device_count = torch.cuda.device_count()
        if resolved.index is not None and resolved.index >= device_count:
            print(
                f"[WARN] Se solicitó {requested_device!r}, pero solo hay {device_count} "
                "dispositivos CUDA visibles. Fallback a cpu."
            )
            resolved = torch.device("cpu")

    print(f"[INFO] Dispositivo real en uso: {resolved}")
    return resolved


def compute_r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """RAfAE'Aca,!A!A2 clAfAE'A+aEUR(TM)AfaEURsA,A!sico, con protecciAfAE'A+aEUR(TM)AfaEURsA,A3n para casos degenerados."""
    y_true = np.asarray(y_true).flatten()
    y_pred = np.asarray(y_pred).flatten()
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    if np.sum(mask) < 3:
        return float("nan")
    y_true = y_true[mask]
    y_pred = y_pred[mask]
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot <= 1e-10:
        return float("nan")
    return float(1.0 - ss_res / ss_tot)


def compute_mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Mean Absolute Error con protecciAfAE'A+aEUR(TM)AfaEURsA,A3n."""
    y_true = np.asarray(y_true).flatten()
    y_pred = np.asarray(y_pred).flatten()
    mask = np.isfinite(y_true) & np.isfinite(y_pred)
    if np.sum(mask) < 1:
        return float("nan")
    return float(np.mean(np.abs(y_true[mask] - y_pred[mask])))


def safe_relative_path(path: Path, *base_paths: Optional[Path]) -> str:
    """Serializa una ruta de forma estable sin fallar si no cae bajo la base principal."""
    resolved_path = path.resolve()
    for base_path in base_paths:
        if base_path is None:
            continue
        try:
            return str(resolved_path.relative_to(Path(base_path).resolve()))
        except ValueError:
            continue
    return str(resolved_path)


def build_family_inference_report(
    family_prob_row: np.ndarray,
    family_map_inv: Dict[int, str],
) -> Dict[str, Any]:
    """Convierte logits/probabilidades de family en compatibilidad + abstención explícita."""
    family_prob_row = np.asarray(family_prob_row, dtype=np.float64)
    family_order = np.argsort(family_prob_row)[::-1]
    top1_idx = int(family_order[0])
    top2_idx = int(family_order[1]) if len(family_order) > 1 else top1_idx
    family_raw_name = family_map_inv.get(top1_idx, "unknown")
    family_top2_name = family_map_inv.get(top2_idx, "unknown")
    family_top1_score = float(family_prob_row[top1_idx])
    family_top2_score = float(family_prob_row[top2_idx]) if len(family_order) > 1 else 0.0
    family_margin = family_top1_score - family_top2_score
    family_entropy = float(-np.sum(family_prob_row * np.log(np.clip(family_prob_row, 1e-12, 1.0))))
    family_pred_confident = bool(
        family_top1_score >= FAMILY_CONFIDENCE_TOP1_THRESHOLD
        and family_margin >= FAMILY_CONFIDENCE_MARGIN_THRESHOLD
    )
    family_pred_was_abstained = not family_pred_confident
    abstention_reasons: List[str] = []
    if family_top1_score < FAMILY_CONFIDENCE_TOP1_THRESHOLD:
        abstention_reasons.append("top1_below_threshold")
    if family_margin < FAMILY_CONFIDENCE_MARGIN_THRESHOLD:
        abstention_reasons.append("margin_below_threshold")
    family_abstention_reason = "none" if not abstention_reasons else "+".join(abstention_reasons)
    family_name = family_raw_name if family_pred_confident else "unknown"
    family_scores = {
        family_map_inv.get(int(idx), f"family_{int(idx)}"): float(family_prob_row[int(idx)])
        for idx in family_order
    }
    return {
        "family_pred": top1_idx,
        "family_raw_name": family_raw_name,
        "family_name": family_name,
        "family_top2_name": family_top2_name,
        "family_scores": family_scores,
        "family_top1_score": family_top1_score,
        "family_top2_score": family_top2_score,
        "family_margin": family_margin,
        "family_entropy": family_entropy,
        "family_pred_confident": family_pred_confident,
        "family_pred_was_abstained": family_pred_was_abstained,
        "family_abstention_reason": family_abstention_reason,
        "family_classification_mode": "confident" if family_pred_confident else "abstained",
        "family_output_semantics": FAMILY_OUTPUT_SEMANTICS,
        "family_confidence_thresholds": {
            "top1_min": FAMILY_CONFIDENCE_TOP1_THRESHOLD,
            "margin_min": FAMILY_CONFIDENCE_MARGIN_THRESHOLD,
        },
    }


# ============================================================
# EXTRACCIAfAE'A+aEUR(TM)AfAcAcaEURsA!A...aEURoeN DE FEATURES DEL BOUNDARY
# ============================================================

def extract_correlator_features(G2: np.ndarray, x: np.ndarray) -> Dict[str, float]:
    """
    Extrae features robustas de un correlador G2(x) sin producir NaN/Inf.
    
    Features V2.4 (2024-12-30):
    - Originales: slope, curvature, small_x, large_x
    - Running: slope_UV, slope_IR, slope_running (captura deformaciones)
    - Estadisticos: G2_std, G2_skew (forma de distribucion)
    
    Justificacion fisica (post-hoc, AGMOO ?3.1.3, ?4.3.2):
    - La posicion radial z actua como escala de energia
    - Comportamiento diferente en UV vs IR indica geometria no-trivial
    - NO inyecta teoria: son operaciones matematicas sobre G2(x)
    """
    features = {
        # Originales
        "G2_log_slope": 0.0,
        "G2_log_curvature": 0.0,
        "G2_small_x": 0.0,
        "G2_large_x": 0.0,
        # Running (UV vs IR)
        "slope_UV": 0.0,
        "slope_IR": 0.0,
        "slope_running": 0.0,
        # Estadisticos de distribucion
        "G2_std": 0.0,
        "G2_skew": 0.0,
    }

    if G2 is None or x is None:
        return features

    G2 = np.asarray(G2, dtype=float)
    x = np.asarray(x, dtype=float)

    if G2.size == 0 or x.size == 0:
        return features

    # UV/IR (robusto)
    g0 = np.nan_to_num(G2[0], nan=0.0, posinf=0.0, neginf=0.0)
    g1 = np.nan_to_num(G2[-1], nan=0.0, posinf=0.0, neginf=0.0)
    features["G2_small_x"] = float(np.clip(g0, 0.0, 1e6))
    features["G2_large_x"] = float(np.clip(g1, 0.0, 1e6))

    # Log-log fit (robusto): exige x>0, G2>0 y finitud
    mask = (G2 > 0) & np.isfinite(G2) & (x > 0) & np.isfinite(x)
    if int(np.sum(mask)) < 3:
        return features

    x_log = np.log(x[mask])
    G2_log = np.log(G2[mask] + 1e-8)

    m2 = np.isfinite(x_log) & np.isfinite(G2_log)
    if int(np.sum(m2)) < 3:
        return features

    # Pendiente
    try:
        coeffs = np.polyfit(x_log[m2], G2_log[m2], 1)
        slope = float(coeffs[0])
        if not np.isfinite(slope):
            slope = 0.0
        features["G2_log_slope"] = float(np.clip(slope, -20.0, 20.0))
    except Exception:
        features["G2_log_slope"] = 0.0

    # Curvatura (requiere mAfAE'A+aEUR(TM)AfaEURsA,A!s puntos)
    if int(np.sum(m2)) >= 4:
        try:
            coeffs2 = np.polyfit(x_log[m2], G2_log[m2], 2)
            curvature = float(coeffs2[0])
            if not np.isfinite(curvature):
                curvature = 0.0
            features["G2_log_curvature"] = float(np.clip(curvature, -10.0, 10.0))
        except Exception:
            features["G2_log_curvature"] = 0.0

    # =========================================================
    # NUEVAS FEATURES V2.4: Running y Estadisticos
    # =========================================================
    
    # RUNNING: Exponente local en UV vs IR
    # Justificacion: Si el correlador tiene power-law G2 ~ x^(-2?),
    # una deformacion hace que ?_eff cambie con la escala.
    # Dividimos el rango en dos mitades y calculamos pendiente local.
    n_valid = int(np.sum(m2))
    if n_valid >= 6:
        mid = n_valid // 2
        x_log_valid = x_log[m2]
        G2_log_valid = G2_log[m2]
        
        try:
            # Pendiente en UV (primera mitad, x pequeno)
            slope_uv = float(np.polyfit(x_log_valid[:mid], G2_log_valid[:mid], 1)[0])
            if np.isfinite(slope_uv):
                features["slope_UV"] = float(np.clip(slope_uv, -20.0, 20.0))
        except Exception:
            pass
        
        try:
            # Pendiente en IR (segunda mitad, x grande)
            slope_ir = float(np.polyfit(x_log_valid[mid:], G2_log_valid[mid:], 1)[0])
            if np.isfinite(slope_ir):
                features["slope_IR"] = float(np.clip(slope_ir, -20.0, 20.0))
        except Exception:
            pass
        
        # Running = diferencia entre IR y UV
        # AdS puro: running ? 0
        # AdS deformado: running != 0
        running = features["slope_IR"] - features["slope_UV"]
        features["slope_running"] = float(np.clip(running, -10.0, 10.0))
    else:
        # Si no hay suficientes puntos, usar slope global
        features["slope_UV"] = features["G2_log_slope"]
        features["slope_IR"] = features["G2_log_slope"]
        features["slope_running"] = 0.0
    
    # ESTADISTICOS DE DISTRIBUCION (matematica pura, sin scipy)
    # Capturan la "forma" del correlador mas alla de slope/curvature
    G2_valid = G2[np.isfinite(G2) & (G2 > 0)]
    if len(G2_valid) >= 3:
        # Trabajamos en log-space para estabilidad numerica
        log_G2 = np.log(G2_valid + 1e-8)
        
        # Desviacion estandar (dispersion)
        std_val = float(np.std(log_G2))
        features["G2_std"] = float(np.clip(std_val, 0.0, 20.0))
        
        # Skewness manual: E[(X-u)3] / ?3
        # Mide asimetria de la distribucion
        mean_val = np.mean(log_G2)
        if std_val > 1e-10:
            centered = (log_G2 - mean_val) / std_val
            skew_val = float(np.mean(centered ** 3))
            features["G2_skew"] = float(np.clip(skew_val, -10.0, 10.0))

    return features



def extract_thermal_features(G2: np.ndarray, x: np.ndarray, T: float) -> Dict[str, float]:
    """
    Features tAfAE'A+aEUR(TM)AfaEURsA,A(C)rmicos bAfAE'A+aEUR(TM)AfaEURsA,A!sicos: presencia de horizonte, escala tAfAE'A+aEUR(TM)AfaEURsA,A(C)rmica, etc.
    
    Features extraAfAE'A+aEUR(TM)AfaEURsA,A-dos:
    - temperature: temperatura normalizada
    - has_horizon: indicador binario de existencia de horizonte
    - thermal_scale: escala tAfAE'A+aEUR(TM)AfaEURsA,A(C)rmica AfAE'A...A 1/2 A2 = 1/T
    - exponential_decay: tasa de decaimiento exponencial a alta T
    """
    features = {}
    
    G2 = np.asarray(G2, dtype=float)
    x = np.asarray(x, dtype=float)
    
    T_arr = np.asarray(T, dtype=float)
    T_scalar = float(T_arr.ravel()[0]) if T_arr.size > 0 else 0.0

    features["temperature"] = float(np.clip(T_scalar, 0, 10))
    features["has_horizon"] = float(T_scalar > 1e-10)

    if T_scalar > 1e-10:
        beta = 1.0 / T_scalar
        features["thermal_scale"] = float(np.clip(beta, 0.1, 100))

        valid = (x > beta) & (G2 > 0) & np.isfinite(G2)
        if np.sum(valid) > 3:
            log_G2 = np.log(G2[valid] + 1e-20)
            try:
                slope_exp = np.polyfit(x[valid], log_G2, 1)[0]
                features["exponential_decay"] = float(np.clip(-slope_exp, -10, 10))
            except Exception:
                features["exponential_decay"] = 0.0
        else:
            features["exponential_decay"] = 0.0
    else:
        features["thermal_scale"] = 0.0
        features["exponential_decay"] = 0.0

    return features


def extract_spectral_features(operators: List[Dict]) -> Dict[str, float]:
    """
    Extrae features del espectro de operators.
    
    Features extraAfAE'A+aEUR(TM)AfaEURsA,A-dos:
    - n_ops: nAfAE'A+aEUR(TM)AfaEURsA,Aomero de operators
    - Delta_min, Delta_max, Delta_mean: estadAfAE'A+aEUR(TM)AfaEURsA,A-sticas de las dimensiones conformes
    """
    features = {}
    
    if not operators:
        features["n_ops"] = 0.0
        features["Delta_min"] = 0.0
        features["Delta_max"] = 0.0
        features["Delta_mean"] = 0.0
        return features
    
    deltas = [op.get("Delta", 0.0) for op in operators]
    deltas = np.asarray(deltas, dtype=float)
    deltas = deltas[np.isfinite(deltas)]
    if len(deltas) == 0:
        features["n_ops"] = 0.0
        features["Delta_min"] = 0.0
        features["Delta_max"] = 0.0
        features["Delta_mean"] = 0.0
        return features
    
    features["n_ops"] = float(len(deltas))
    features["Delta_min"] = float(np.min(deltas))
    features["Delta_max"] = float(np.max(deltas))
    features["Delta_mean"] = float(np.mean(deltas))
    
    return features


def extract_response_features(
    G_R_real: np.ndarray,
    G_R_imag: np.ndarray,
    omega: np.ndarray,
    k: np.ndarray,
) -> Dict[str, float]:
    """
    Features de la respuesta de Green retardada G_R(omega, k).
    
    Features extraAfAE'A+aEUR(TM)AfaEURsA,A-dos:
    - GR_peak_height: altura mAfAE'A+aEUR(TM)AfaEURsA,A!xima del pico (relacionado con QNMs)
    - GR_peak_width: ancho del pico (relacionado con lifetime)
    """
    features = {}
    
    G_R_real = np.asarray(G_R_real, dtype=float)
    G_R_imag = np.asarray(G_R_imag, dtype=float)
    
    if G_R_real.ndim != 2 or G_R_imag.ndim != 2:
        return {"GR_peak_height": 0.0, "GR_peak_width": 0.0}
    
    magnitude = np.sqrt(G_R_real**2 + G_R_imag**2)
    mag_flat = magnitude.reshape(-1)
    
    if mag_flat.size == 0:
        return {"GR_peak_height": 0.0, "GR_peak_width": 0.0}
    
    peak_height = float(np.max(mag_flat))
    if peak_height <= 0:
        return {"GR_peak_height": 0.0, "GR_peak_width": 0.0}
    
    thresh = 0.5 * peak_height
    mask = mag_flat >= thresh
    peak_width = float(np.sum(mask) / mag_flat.size)
    
    features["GR_peak_height"] = float(np.clip(peak_height, 0, 1e3))
    features["GR_peak_width"] = float(np.clip(peak_width, 0, 1.0))
    return features


def build_feature_vector(boundary_data: Dict[str, Any], operators: List[Dict]) -> np.ndarray:
    """
    Construye vector de features a partir de boundary_data + operators.
    
    El vector tiene estructura fija para garantizar consistencia entre geometrAfAE'A+aEUR(TM)AfaEURsA,A-as.
    """
    all_features: List[float] = []
    
    # 1. Features de correlador G2 vs x (4 features)
    x_grid = boundary_data.get("x_grid", np.linspace(0.1, 10, 100))
    
    # Buscar cualquier correlador G2_* disponible
    G2 = None
    for key in boundary_data:
        if key.startswith("G2_") and isinstance(boundary_data[key], np.ndarray):
            G2 = boundary_data[key]
            break
    
    if G2 is not None:
        corr_feats = extract_correlator_features(G2, x_grid)
        # Features V2.4: 4 originales + 3 running + 2 estadisticos = 9 features
        for k in ["G2_log_slope", "G2_log_curvature", "G2_small_x", "G2_large_x",
                  "slope_UV", "slope_IR", "slope_running",
                  "G2_std", "G2_skew"]:
            all_features.append(corr_feats.get(k, 0.0))
    else:
        all_features.extend([0.0] * 9)  # 9 features del correlador
    
    # 2. Features tAfAE'A+aEUR(TM)AfaEURsA,A(C)rmicos (4 features)
    T = boundary_data.get("temperature", boundary_data.get("T", 0.0))
    if isinstance(T, np.ndarray):
        T = float(T.ravel()[0]) if T.size > 0 else 0.0
    
    if G2 is not None:
        thermal_feats = extract_thermal_features(G2, x_grid, T)
        for k in ["temperature", "has_horizon", "thermal_scale", "exponential_decay"]:
            all_features.append(thermal_feats.get(k, 0.0))
    else:
        all_features.extend([float(T), float(T > 1e-10), 0.0, 0.0])
    
    # 3. Features QNM (3 features): Q0, f1/f0, γ1/γ0
    # Replaces the 4 Δ operator features, which are 0 for all LIGO data
    # (no CFT operator spectrum) but non-zero for sandbox — breaking generalization.
    # QNM features are stored as boundary attrs by both 00_compute_sandbox_qnms.py
    # (sandbox) and realdata_ringdown_to_stage02_boundary_dataset.py (LIGO).
    qnm_Q0   = float(boundary_data.get("qnm_Q0",   0.0))
    qnm_f1f0 = float(boundary_data.get("qnm_f1f0", 0.0))
    qnm_g1g0 = float(boundary_data.get("qnm_g1g0", 0.0))
    all_features.append(qnm_Q0)
    all_features.append(qnm_f1f0)
    all_features.append(qnm_g1g0)
    
    # 4. Features de respuesta G_R (2 features)
    if "G_R_real" in boundary_data and "G_R_imag" in boundary_data:
        G_R_real = boundary_data["G_R_real"]
        G_R_imag = boundary_data["G_R_imag"]
        omega = boundary_data.get("omega_grid", np.linspace(0.1, 10, 50))
        k = boundary_data.get("k_grid", np.linspace(0, 5, 30))
        resp_feats = extract_response_features(G_R_real, G_R_imag, omega, k)
        all_features.append(resp_feats.get("GR_peak_height", 0.0))
        all_features.append(resp_feats.get("GR_peak_width", 0.0))
    else:
        all_features.extend([0.0, 0.0])

    # 5. Observable escalar opcional: "central charge" toy (1 feature)
    c_eff = boundary_data.get("central_charge_eff", None)
    if c_eff is not None:
        c_eff_arr = np.asarray(c_eff, dtype=float)
        c_eff_val = float(c_eff_arr.ravel()[0]) if c_eff_arr.size > 0 else 0.0
    else:
        c_eff_val = 0.0
    all_features.append(c_eff_val)
    
    # 6. DimensiAfAE'A+aEUR(TM)AfaEURsA,A3n d como feature explAfAE'A+aEUR(TM)AfaEURsA,A-cita (1 feature)
    d = boundary_data.get("d", 4)
    if isinstance(d, np.ndarray):
        d = int(d.ravel()[0]) if d.size > 0 else 4
    all_features.append(float(d))
    
    # Total: 20 features (V2.5: reemplaza 4 features Δ por 3 features QNM)
    # Correlador: 9 (4 orig + 3 running + 2 stats)
    # Termicos: 4, QNM: 3 (Q0/f1f0/g1g0), Respuesta: 2, Globales: 2
    return np.array(all_features, dtype=np.float32)


def build_feature_vector_v3(boundary_data: Dict[str, Any], operators: List[Dict]) -> np.ndarray:
    """
    V3 feature vector — Camino C2 contract (17 features).

    Identical to build_feature_vector except the QNM block (qnm_Q0, qnm_f1f0,
    qnm_g1g0) is intentionally absent.  This makes the vector interoperable
    between the holographic sandbox (Kerr analytical, Q0≈2–7) and the real
    GWOSC bridge (ESPRIT 250 ms window, Q0≈100–10000) without the 795σ
    extrapolation that killed the V2.5 gate.

    Feature ordering (must stay in sync with FEATURE_NAMES_V3 in feature_support.py):
      0–8:   G2 correlator (9): log_slope, log_curvature, small_x, large_x,
             slope_UV, slope_IR, slope_running, G2_std, G2_skew
      9–12:  Thermal (4): temperature, has_horizon, thermal_scale, exponential_decay
      13–14: Response G_R (2): GR_peak_height, GR_peak_width
      15:    central_charge_eff (1)
      16:    d (1)
    """
    all_features: List[float] = []

    # 1. G2 correlator (9)
    x_grid = boundary_data.get("x_grid", np.linspace(0.1, 10, 100))
    G2 = None
    for key in boundary_data:
        if key.startswith("G2_") and isinstance(boundary_data[key], np.ndarray):
            G2 = boundary_data[key]
            break
    if G2 is not None:
        corr_feats = extract_correlator_features(G2, x_grid)
        for k in ["G2_log_slope", "G2_log_curvature", "G2_small_x", "G2_large_x",
                  "slope_UV", "slope_IR", "slope_running", "G2_std", "G2_skew"]:
            all_features.append(corr_feats.get(k, 0.0))
    else:
        all_features.extend([0.0] * 9)

    # 2. Thermal (4)
    T = boundary_data.get("temperature", boundary_data.get("T", 0.0))
    if isinstance(T, np.ndarray):
        T = float(T.ravel()[0]) if T.size > 0 else 0.0
    if G2 is not None:
        thermal_feats = extract_thermal_features(G2, x_grid, T)
        for k in ["temperature", "has_horizon", "thermal_scale", "exponential_decay"]:
            all_features.append(thermal_feats.get(k, 0.0))
    else:
        all_features.extend([float(T), float(T > 1e-10), 0.0, 0.0])

    # QNM block intentionally absent (V3 / Camino C2)

    # 3. Response G_R (2)
    if "G_R_real" in boundary_data and "G_R_imag" in boundary_data:
        resp_feats = extract_response_features(
            boundary_data["G_R_real"],
            boundary_data["G_R_imag"],
            boundary_data.get("omega_grid", np.linspace(0.1, 10, 50)),
            boundary_data.get("k_grid", np.linspace(0, 5, 30)),
        )
        all_features.append(resp_feats.get("GR_peak_height", 0.0))
        all_features.append(resp_feats.get("GR_peak_width", 0.0))
    else:
        all_features.extend([0.0, 0.0])

    # 4. central_charge_eff (1)
    c_eff = boundary_data.get("central_charge_eff", None)
    if c_eff is not None:
        c_eff_arr = np.asarray(c_eff, dtype=float)
        c_eff_val = float(c_eff_arr.ravel()[0]) if c_eff_arr.size > 0 else 0.0
    else:
        c_eff_val = 0.0
    all_features.append(c_eff_val)

    # 5. d (1)
    d = boundary_data.get("d", 4)
    if isinstance(d, np.ndarray):
        d = int(d.ravel()[0]) if d.size > 0 else 4
    all_features.append(float(d))

    # Total: 17 features
    return np.array(all_features, dtype=np.float32)


# ============================================================
# CARGA SEGURA DE DATOS (BULK vs BOUNDARY)
# ============================================================

class CuerdasDataLoader:
    """
    Encapsula el acceso a los datos de geometrAfAE'A+aEUR(TM)AfaEURsA,A-a.
    
    - En todos los modos se leen SIEMPRE los datos de *boundary* y la metainformaciAfAE'A+aEUR(TM)AfaEURsA,A3n.
    - El acceso a `bulk_truth` (A_truth, f_truth, R_truth, etc.) SOLO estAfAE'A+aEUR(TM)AfaEURsA,A! permitido
      cuando `mode == "train"`.
      
    Esto implementa a nivel de cAfAE'A+aEUR(TM)AfaEURsA,A3digo la separaciAfAE'A+aEUR(TM)AfaEURsA,A3n Sandbox vs. Discovery: cualquier
    script que quiera reutilizar este loader en modo `inference` podrAfAE'A+aEUR(TM)AfaEURsA,A! leer el
    boundary, pero recibirAfAE'A+aEUR(TM)AfaEURsA,A! un error claro si intenta acceder al bulk.
    """
    
    def __init__(self, mode: str = "train"):
        if mode not in ("train", "inference", "finetune_physics"):
            raise ValueError(f"Modo no reconocido para CuerdasDataLoader: {mode}")
        self.mode = mode
    
    def load_boundary_and_meta(self, f: h5py.File) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Carga datos de frontera y operators desde un file HDF5.
        
        Esta funciAfAE'A+aEUR(TM)AfaEURsA,A3n NO toca `bulk_truth` y es segura en cualquier modo.
        """
        boundary_group = f["boundary"]
        boundary_data: Dict[str, Any] = {}
        
        for key in boundary_group.keys():
            boundary_data[key] = boundary_group[key][:]
        for key in boundary_group.attrs.keys():
            boundary_data[key] = boundary_group.attrs[key]
        
        operators_raw = f.attrs.get("operators", "[]")
        if isinstance(operators_raw, bytes):
            operators_raw = operators_raw.decode("utf-8")
        operators = json.loads(operators_raw)
        return boundary_data, operators
    
    def load_bulk_truth(self, f: h5py.File) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, float, str, int, bool]:
        """
        Accede al grupo `bulk_truth` solo en modo entrenamiento.

        Para geometrías sin bulk_truth (e.g. Kerr sintético) devuelve arrays de ceros
        y has_bulk_truth=False. El loop de entrenamiento debe anular la loss de
        reconstrucción para esas geometrías.

        Returns: (A_truth, f_truth, R_truth, z_grid, z_h, family, d, has_bulk_truth)
        """
        if self.mode != "train":
            raise RuntimeError(
                "Acceso a bulk_truth bloqueado en inference mode/discovery. "
                "Use solo los datos de boundary en este modo."
            )

        if "bulk_truth" not in f:
            # Geometría sin dual holográfico conocido (e.g. Kerr).
            # Devolver placeholder de ceros; el training loop usará has_bulk_truth=False
            # para omitir la loss de reconstrucción A/f/R.
            family_attr = f.attrs.get("family", b"unknown")
            if isinstance(family_attr, bytes):
                family_attr = family_attr.decode("utf-8")
            d_attr = int(f.attrs.get("d", 4))
            N = 100  # longitud de grid por defecto
            zeros = np.zeros(N, dtype=np.float32)
            z_grid = np.linspace(0.01, 1.0, N, dtype=np.float32)
            return zeros, zeros, zeros, z_grid, 0.0, str(family_attr), d_attr, False
        
        bulk = f["bulk_truth"]
        A_truth = bulk["A_truth"][:]
        f_truth = bulk["f_truth"][:]
        R_truth = bulk["R_truth"][:]
        z_grid = bulk["z_grid"][:]
        z_h = bulk.attrs.get("z_h", 0.0)
        family = bulk.attrs.get("family", "unknown")
        if isinstance(family, bytes):
            family = family.decode("utf-8")
        d_value = int(bulk.attrs.get("d", 4))
        
        return A_truth, f_truth, R_truth, z_grid, float(z_h), str(family), d_value, True


SUPPORTED_ENGINE_MODES = ("train", "inference")
EXPERIMENTAL_ENGINE_MODES = ("finetune_physics",)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CUERDAS - Geometria emergente V2.2 (train, inference, experimental finetune hook)"
    )
    parser.add_argument("--data-dir", type=str, default=None,
                        help="directory con datos HDF5 de geometrías")
    parser.add_argument("--output-dir", type=str, default=None,
                        help="directory de salida para modelo y predicciones")
    parser.add_argument("--n-epochs", type=int, default=2000,
                        help="Número de épocas de entrenamiento (solo mode=train)")
    parser.add_argument("--device", type=str, default="cpu",
                        help="Dispositivo: 'cpu' o 'cuda'")
    parser.add_argument("--hidden-dim", type=int, default=256,
                        help="Dimensión oculta de la red")
    parser.add_argument("--n-layers", type=int, default=4,
                        help="Número de capas residuales")
    parser.add_argument("--batch-size", type=int, default=32,
                        help="Tamaño de batch")
    parser.add_argument("--seed", type=int, default=42,
                        help="Semilla aleatoria")
    parser.add_argument("--verbose", action="store_true", default=True,
                        help="Imprimir progreso detallado")
    parser.add_argument("--lr", type=float, default=LEARNING_RATE,
                        help="Learning rate inicial")
    parser.add_argument(
        "--mode",
        type=str,
        choices=[*SUPPORTED_ENGINE_MODES, *EXPERIMENTAL_ENGINE_MODES],
        default="train",
        help=(
            "Modo de uso: 'train' (sandbox con bulk_truth), 'inference' "
            "(boundary-only usando checkpoint) o 'finetune_physics' "
            "(gancho experimental, no implementado)."
        ),
    )
    parser.add_argument(
        "--checkpoint",
        type=str,
        default=None,
        help="Ruta al checkpoint del modelo entrenado en sandbox "
             "(solo obligatorio en mode='inference')"
    )
    parser.add_argument(
        "--support-mode",
        type=str,
        choices=["strict", "permissive_ood"],
        default="strict",
        help=(
            "Feature support gate mode. 'strict' (default) fails on OOD critical "
            "features (canonical behavior). 'permissive_ood' allows inference with "
            "explicit OOD flag for events outside training support."
        ),
    )
    add_standard_arguments(parser)
    return parser


def run_finetune_physics_mode(args):
    """
    Gancho explícito para un futuro ajuste físico autosupervisado.

    No debe inferirse de esta ruta que exista hoy validación boundary↔bulk
    ni una loss física operacional.
    """
    raise NotImplementedError(
        "finetune_physics not implemented yet; current engine supports only "
        "supervised train (sandbox with bulk_truth) and boundary-only inference. "
        "No validated physics fine-tuning or boundary↔bulk consistency loop is available yet."
    )


# ============================================================
# NORMALIZACIAfAE'A+aEUR(TM)AfAcAcaEURsA!A...aEURoeN ROBUSTA DE TARGETS (V2.1 MEJORADA)
# ============================================================

class TargetNormalizer:
    """
    Normaliza targets de forma robusta para entrenamiento.
    
    V2.1: Usa z-score robusto (mediana + MAD) para A, y percentiles
    con clipping para R que puede tener valores muy extremos.
    """
    
    def __init__(self):
        self.A_mean = None
        self.A_std = None
        self.R_mean = None
        self.R_std = None
        self.f_mean = None
        self.f_std = None
        
    def fit(self, A: np.ndarray, f: np.ndarray, R: np.ndarray):
        """Calcula estadAfAE'A+aEUR(TM)AfaEURsA,A-sticas de normalizaciAfAE'A+aEUR(TM)AfaEURsA,A3n."""
        # A: z-score robusto (mediana + MAD)
        A_flat = A.flatten()
        A_flat = A_flat[np.isfinite(A_flat)]
        self.A_mean = float(np.median(A_flat))
        mad = np.median(np.abs(A_flat - self.A_mean))
        self.A_std = float(max(mad * 1.4826, 0.1))  # 1.4826 para equivalencia con std normal
        
        # f: normalizaciAfAE'A+aEUR(TM)AfaEURsA,A3n simple (ya estAfAE'A+aEUR(TM)AfaEURsA,A! en [0,1] tAfAE'A+aEUR(TM)AfaEURsA,A-picamente)
        f_flat = f.flatten()
        f_flat = f_flat[np.isfinite(f_flat)]
        self.f_mean = float(np.mean(f_flat))
        self.f_std = float(max(np.std(f_flat), 0.1))
        
        # R: normalizaciAfAE'A+aEUR(TM)AfaEURsA,A3n con clipping agresivo (valores pueden ser muy grandes)
        R_flat = R.flatten()
        R_valid = R_flat[np.isfinite(R_flat) & (np.abs(R_flat) < 1e4)]
        if len(R_valid) > 0:
            # Usar percentiles para robustez ante outliers
            self.R_mean = float(np.percentile(R_valid, 50))
            iqr = np.percentile(R_valid, 75) - np.percentile(R_valid, 25)
            self.R_std = float(max(iqr / 1.35, 1.0))  # 1.35 para equivalencia con std normal
        else:
            self.R_mean = -20.0
            self.R_std = 10.0
    
    @classmethod
    def from_dict(cls, d: Dict[str, float]) -> "TargetNormalizer":
        """Reconstruye un TargetNormalizer desde un diccionario (checkpoint)."""
        norm = cls()
        norm.A_mean = d.get("A_mean", 0.0)
        norm.A_std = d.get("A_std", 1.0)
        norm.f_mean = d.get("f_mean", 0.5)
        norm.f_std = d.get("f_std", 0.3)
        norm.R_mean = d.get("R_mean", -20.0)
        norm.R_std = d.get("R_std", 10.0)
        return norm
    
    def normalize_A(self, A: np.ndarray) -> np.ndarray:
        return (A - self.A_mean) / self.A_std
    
    def denormalize_A(self, A_norm: np.ndarray) -> np.ndarray:
        return A_norm * self.A_std + self.A_mean
    
    def normalize_f(self, f: np.ndarray) -> np.ndarray:
        # f ya estAfAE'A+aEUR(TM)AfaEURsA,A! tAfAE'A+aEUR(TM)AfaEURsA,A-picamente en [0,1], normalizaciAfAE'A+aEUR(TM)AfaEURsA,A3n suave
        return (f - self.f_mean) / self.f_std
    
    def denormalize_f(self, f_norm: np.ndarray) -> np.ndarray:
        return f_norm * self.f_std + self.f_mean
    
    def normalize_R(self, R: np.ndarray) -> np.ndarray:
        # Clipping antes de normalizar para evitar explosiAfAE'A+aEUR(TM)AfaEURsA,A3n
        R_clipped = np.clip(R, self.R_mean - 10 * self.R_std, self.R_mean + 10 * self.R_std)
        return (R_clipped - self.R_mean) / self.R_std
    
    def denormalize_R(self, R_norm: np.ndarray) -> np.ndarray:
        return R_norm * self.R_std + self.R_mean


# ============================================================
# EMERGENT GEOMETRY NETWORK (V2.1 MEJORADA)
# ============================================================

class EmergentGeometryNet(nn.Module):
    """
    Red que mapea features del boundary -> geometrAfAE'A+aEUR(TM)AfaEURsA,A-a del bulk.
    
    V2.1: 
    - Factor residual adaptativo (0.3 en lugar de 0.1)
    - Mejor inicializaciAfAE'A+aEUR(TM)AfaEURsA,A3n de pesos
    - Dropout calibrado por capa
    - Decoder de f mejorado (sin Sigmoid, usa normalizaciAfAE'A+aEUR(TM)AfaEURsA,A3n)
    """
    
    def __init__(
        self,
        n_features: int,
        n_z: int,
        hidden_dim: int = 256,
        n_layers: int = 4,
        n_families: int = 5,
        dropout: float = 0.1,
        d: int = 3,  # Dimension del boundary para calculo de R
    ):
        super().__init__()
        
        self.n_z = n_z
        self.n_families = n_families
        self.d = d  # Almacenar para calculo de Ricci
        
        # Input projection con normalizaciAfAE'A+aEUR(TM)AfaEURsA,A3n
        self.input_norm = nn.LayerNorm(n_features)
        self.input_proj = nn.Linear(n_features, hidden_dim)
        
        # Bloques residuales tipo "Transformer-lite"
        self.layers = nn.ModuleList()
        self.layer_norms = nn.ModuleList()
        for i in range(n_layers):
            self.layers.append(
                nn.Sequential(
                    nn.Linear(hidden_dim, hidden_dim * 2),
                    nn.GELU(),
                    nn.Dropout(dropout * (1 + i * 0.1)),  # Dropout creciente por capa
                    nn.Linear(hidden_dim * 2, hidden_dim),
                )
            )
            self.layer_norms.append(nn.LayerNorm(hidden_dim))
        
        self.final_norm = nn.LayerNorm(hidden_dim)
        
        # Decoders separados para cada salida
        # A(z): warp factor
        self.decoder_A = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, n_z)
        )
        
        # f(z): blackening factor (sin Sigmoid - normalizado externamente)
        self.decoder_f = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, n_z)
        )
        
        # R(z): escalar de Ricci (secundario)
        # V2.3: decoder_R ELIMINADO - R se calcula desde A,f (consistencia geometrica)
        # self.decoder_R = nn.Sequential(...)  # REMOVED
        
        # z_h: posiciAfAE'A+aEUR(TM)AfaEURsA,A3n del horizonte
        self.decoder_zh = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Linear(hidden_dim // 2, 1)
        )
        
        # ClasificaciAfAE'A+aEUR(TM)AfaEURsA,A3n de family
        self.decoder_family = nn.Linear(hidden_dim, n_families)
        
        self._init_weights()
    
    def _init_weights(self):
        """InicializaciAfAE'A+aEUR(TM)AfaEURsA,A3n cuidadosa para evitar Outputs: absurdas."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                # Xavier con gain moderado
                nn.init.xavier_normal_(m.weight, gain=0.6)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
        
        # InicializaciAfAE'A+aEUR(TM)AfaEURsA,A3n especial para decoders: Outputs: cerca de 0
        for decoder in [self.decoder_A, self.decoder_f, self.decoder_zh]:
            if isinstance(decoder, nn.Sequential):
                last_layer = decoder[-1]
                if isinstance(last_layer, nn.Linear):
                    nn.init.xavier_normal_(last_layer.weight, gain=0.1)
                    nn.init.zeros_(last_layer.bias)
    
    def forward(self, x: torch.Tensor, z_grid: torch.Tensor = None) -> Dict[str, torch.Tensor]:
        # Normalizacion de entrada
        h = self.input_norm(x)
        h = self.input_proj(h)
        h = F.gelu(h)
        
        # Bloques residuales con factor adaptativo
        for layer, ln in zip(self.layers, self.layer_norms):
            residual = layer(h)
            h = ln(h + 0.3 * residual)  # Factor residual 0.3 (mas expresivo que 0.1)
        
        h = self.final_norm(h)
        
        # Decoders para campos primarios (A, f)
        A = self.decoder_A(h)
        f_raw = self.decoder_f(h)
        z_h = self.decoder_zh(h).squeeze(-1)
        family_logits = self.decoder_family(h)
        
        # V2.3: R se calcula DETERMINISTICAMENTE desde A,f
        # Esto garantiza consistencia geometrica: R es propiedad de la metrica
        if z_grid is not None:
            R = compute_ricci_from_metric(A, f_raw, z_grid, self.d)
        else:
            # Sin z_grid, no podemos calcular R
            R = torch.zeros_like(A)
        
        return {
            "A": A,
            "f": f_raw,  # Sin activacion, normalizado externamente
            "R": R,      # Calculado desde A,f (no predicho)
            "z_h": z_h,
            "family_logits": family_logits,
        }


# ============================================================
# PHYSICS-INFORMED LOSSES (V2.1 DOCUMENTADA)
# ============================================================

def compute_ricci_from_metric(
    A: torch.Tensor,
    f: torch.Tensor,
    z: torch.Tensor,
    d: int
) -> torch.Tensor:
    """
    Calcula el escalar de Ricci R(z) DETERMINAfAE'A,A?STICAMENTE desde A(z) y f(z).
    
    Esta funcion garantiza CONSISTENCIA GEOMAfAE'Aca,!A?TRICA: R es una propiedad
    derivada de la metrica, no un campo independiente.
    
    Para la metrica en gauge conformal:
        dsA2 = e^{2A(z)} [-f(z)dtA2 + dxA2] + dzA2/f(z)
    
    El escalar de Ricci es:
        R = -2(D)A'' - D(D-1)(A')A2 - (f'/f)A'
    
    donde D = d + 1 es la dimension del bulk.
    
    NOTA IMPORTANTE (HONESTIDAD EPISTEMOLOGICA):
    Esta formula es GEOMETRAfAE'A,A?A DIFERENCIAL BAfAE'A,A?SICA, no fisica.
    NO estamos asumiendo que R = -d(d+1)/LA2 (valor AdS).
    NO estamos imponiendo las ecuaciones de Einstein.
    Solo garantizamos que la curvatura sea consistente con la metrica.
    
    Args:
        A: Warp factor predicho, shape (batch, n_z)
        f: Blackening factor predicho, shape (batch, n_z)
        z: Grid radial, shape (n_z,)
        d: Dimension del boundary (CFT)
    
    Returns:
        R: Escalar de Ricci calculado, shape (batch, n_z)
    """
    D = d + 1  # Dimension del bulk
    
    if len(z) < 3:
        # No podemos calcular derivadas con menos de 3 puntos
        return torch.zeros_like(A)
    
    dz = z[1] - z[0]
    
    # Primera derivada de A: (A[i+1] - A[i-1]) / (2*dz)
    dA = torch.zeros_like(A)
    dA[:, 1:-1] = (A[:, 2:] - A[:, :-2]) / (2 * dz)
    dA[:, 0] = (A[:, 1] - A[:, 0]) / dz  # Forward difference at boundary
    dA[:, -1] = (A[:, -1] - A[:, -2]) / dz  # Backward difference at boundary
    
    # Segunda derivada de A: (A[i+1] - 2*A[i] + A[i-1]) / dzA2
    d2A = torch.zeros_like(A)
    d2A[:, 1:-1] = (A[:, 2:] - 2*A[:, 1:-1] + A[:, :-2]) / (dz ** 2)
    d2A[:, 0] = d2A[:, 1]  # Extrapolate at boundaries
    d2A[:, -1] = d2A[:, -2]
    
    # Primera derivada de f
    df = torch.zeros_like(f)
    df[:, 1:-1] = (f[:, 2:] - f[:, :-2]) / (2 * dz)
    df[:, 0] = (f[:, 1] - f[:, 0]) / dz
    df[:, -1] = (f[:, -1] - f[:, -2]) / dz
    
    # Escalar de Ricci: R = -2D*A'' - D(D-1)(A')A2 - (f'/f)*A'
    # Proteccion contra division por cero en f
    f_safe = f + 1e-10
    
    R = -2 * D * d2A - D * (D - 1) * (dA ** 2) - (df / f_safe) * dA
    
    return R


def physics_loss_generic(
    A: torch.Tensor, 
    f: torch.Tensor, 
    z: torch.Tensor, 
    d: int
) -> torch.Tensor:
    """
    RegularizaciAfAE'A+aEUR(TM)AfaEURsA,A3n fAfAE'A+aEUR(TM)AfaEURsA,A-sica genAfAE'A+aEUR(TM)AfaEURsA,A(C)rica aplicable a TODAS las geometrAfAE'A+aEUR(TM)AfaEURsA,A-as.
    
    TAfAE'A+aEUR(TM)AfaEURsA,A(C)rminos incluidos:
    1. loss_curvature: penaliza segundas derivadas grandes (suavidad)
    2. loss_smooth: penaliza cambios bruscos en la primera derivada
    3. loss_monotonic_A: A debe decrecer en la regiAfAE'A+aEUR(TM)AfaEURsA,A3n UV (cerca de z=0)
    4. loss_f_bounds: f debe estar aproximadamente en [0, 1]
    
    Estos son priors fAfAE'A+aEUR(TM)AfaEURsA,A-sicos muy genAfAE'A+aEUR(TM)AfaEURsA,A(C)ricos que NO asumen la forma exacta
    de la soluciAfAE'A+aEUR(TM)AfaEURsA,A3n (no inyectamos A = -log(z/L) ni nada similar).
    """
    n_z = A.shape[1]
    dz = z[1] - z[0]
    
    # Derivadas de A
    dA = (A[:, 2:] - A[:, :-2]) / (2 * dz)
    d2A = (A[:, 2:] - 2 * A[:, 1:-1] + A[:, :-2]) / (dz ** 2)
    
    # Derivadas de f
    d2f = (f[:, 2:] - 2 * f[:, 1:-1] + f[:, :-2]) / (dz ** 2)
    
    # 1. Penalizar curvatura excesiva (promueve suavidad)
    loss_curvature = torch.mean(d2A ** 2) + 0.1 * torch.mean(d2f ** 2)
    
    # 2. Penalizar cambios bruscos en pendiente (suavidad de orden superior)
    if dA.shape[1] > 1:
        loss_smooth = torch.mean((dA[:, 1:] - dA[:, :-1]) ** 2)
    else:
        loss_smooth = torch.tensor(0.0, device=A.device)
    
    # 3. A tAfAE'A+aEUR(TM)AfaEURsA,A-picamente decrece hacia el interior (dA < 0 en UV)
    # Solo en la primera fracciAfAE'A+aEUR(TM)AfaEURsA,A3n del grid (regiAfAE'A+aEUR(TM)AfaEURsA,A3n UV)
    n_uv = max(1, int(0.2 * dA.shape[1]))
    loss_monotonic_A = torch.mean(F.relu(dA[:, :n_uv]))  # Penaliza dA > 0 en UV
    
    # 4. f debe estar aproximadamente en [0, 1]
    loss_f_bounds = torch.mean(F.relu(-f) + F.relu(f - 1.0))
    
    # Pesos relativos dentro de esta loss
    total = (
        0.3 * loss_curvature + 
        0.3 * loss_smooth + 
        0.2 * loss_monotonic_A + 
        0.2 * loss_f_bounds
    )
    
    return total


def physics_loss_ads_specific(
    A: torch.Tensor,
    f: torch.Tensor,
    z: torch.Tensor,
    d: int,
    family_mask: torch.Tensor
) -> torch.Tensor:
    """
    RegularizaciAfAE'A+aEUR(TM)AfaEURsA,A3n adicional para geometrAfAE'A+aEUR(TM)AfaEURsA,A-as clasificadas como AdS-like.
    
    TAfAE'A+aEUR(TM)AfaEURsA,A(C)rminos incluidos (solo para muestras con family="ads"):
    1. loss_ads_monotonic: A debe ser monAfAE'A+aEUR(TM)AfaEURsA,A3tonamente decreciente en toda la regiAfAE'A+aEUR(TM)AfaEURsA,A3n UV
    2. loss_f_uv: f debe tender a 1 cerca del borde (z AfAE'A,AcAfAcAcaEURsA!A,A AfAcAcaEURsA!AcaEURzAc 0)
    
    Note: NO imponemos A = -log(z/L) explAfAE'A+aEUR(TM)AfaEURsA,A-citamente. Solo priors cualitativos.
    """
    if torch.sum(family_mask) == 0:
        return torch.tensor(0.0, device=A.device)
    
    A_ads = A[family_mask]
    f_ads = f[family_mask]
    
    n_z = A_ads.shape[1]
    dz = z[1] - z[0]
    
    # Derivada de A para muestras AdS
    dA = (A_ads[:, 2:] - A_ads[:, :-2]) / (2 * dz)
    
    # 1. A monAfAE'A+aEUR(TM)AfaEURsA,A3tono decreciente en la mitad UV del grid
    n_uv_half = max(1, int(0.5 * dA.shape[1]))
    loss_ads_monotonic = torch.mean(F.relu(dA[:, :n_uv_half]))
    
    # 2. f AfAE'A,AcAfAcAcaEURsA!A,A AfAcAcaEURsA!AcaEURzAc 1 en UV (primeros ~10% del grid)
    n_uv_small = max(1, int(0.1 * f_ads.shape[1]))
    f_uv = f_ads[:, :n_uv_small]
    loss_f_uv = torch.mean((f_uv - 1.0) ** 2)
    
    return 0.5 * loss_ads_monotonic + 0.5 * loss_f_uv


# ============================================================
# FUNCIONES DE ENTRENAMIENTO (V2.1 REFACTORIZADO)
# ============================================================

def train_one_epoch(
    model: nn.Module,
    X: torch.Tensor,
    Y_A: torch.Tensor,
    Y_f: torch.Tensor,
    Y_R: torch.Tensor,
    Y_zh: torch.Tensor,
    Y_family: torch.Tensor,
    z_t: torch.Tensor,
    d_value: int,
    family_map: Dict[str, int],
    optimizer: torch.optim.Optimizer,
    batch_size: int,
    device: torch.device,
    has_bulk_mask: Optional[torch.Tensor] = None,
) -> Dict[str, float]:
    """
    Entrena una AfAE'A+aEUR(TM)AfaEURsA,A(C)poca completa y devuelve las pAfAE'A+aEUR(TM)AfaEURsA,A(C)rdidas medias.
    """
    model.train()
    n_train = X.shape[0]
    
    # Shuffle
    idx = torch.randperm(n_train, device=device)
    X = X[idx]
    Y_A = Y_A[idx]
    Y_f = Y_f[idx]
    Y_R = Y_R[idx]
    Y_zh = Y_zh[idx]
    Y_family = Y_family[idx]
    if has_bulk_mask is not None:
        has_bulk_mask = has_bulk_mask[idx]
    
    n_batches = int(np.ceil(n_train / batch_size))
    
    # Acumuladores
    losses = {
        "total": 0.0, "A": 0.0, "f": 0.0, "R": 0.0, 
        "zh": 0.0, "family": 0.0, "physics": 0.0, "physics_ads": 0.0
    }
    
    huber = nn.SmoothL1Loss()
    mse = nn.MSELoss()
    ce = nn.CrossEntropyLoss()
    
    for b in range(n_batches):
        start = b * batch_size
        end = min((b + 1) * batch_size, n_train)
        
        xb = X[start:end]
        yA = Y_A[start:end]
        yf = Y_f[start:end]
        yR = Y_R[start:end]
        yzh = Y_zh[start:end]
        yfam = Y_family[start:end]
        bulk_w = has_bulk_mask[start:end].float() if has_bulk_mask is not None else torch.ones(end - start, device=device)

        optimizer.zero_grad()

        # V2.3: Pasar z_grid para calcular R desde A,f
        out = model(xb, z_grid=z_t)

        # Perdidas de datos — anular reconstrucción A/f/R para geometrías sin bulk_truth
        # (e.g. Kerr sintético). bulk_w=0 para esas, 1 para geometrías holográficas.
        huber_nr = nn.SmoothL1Loss(reduction='none')
        mse_nr   = nn.MSELoss(reduction='none')
        loss_A  = (huber_nr(out["A"], yA).mean(dim=-1)  * bulk_w).mean()
        loss_f  = (mse_nr(out["f"],   yf).mean(dim=-1)  * bulk_w).mean()
        loss_R  = (huber_nr(out["R"], yR).mean(dim=-1)  * bulk_w).mean()
        loss_zh = (huber_nr(out["z_h"].squeeze(-1), yzh) * bulk_w).mean() if out["z_h"].dim() > 1 else (huber(out["z_h"], yzh))
        loss_family = ce(out["family_logits"], yfam)
        
        # Pérdidas físicas.
        # physics_generic: solo muestras con bulk_truth (holográficas); Kerr no tiene
        # dual holográfico y sus A/f reconstruidas no están supervisadas (bulk_w=0),
        # por lo que regularizarlas con priors AdS sería un prior incorrecto.
        # physics_ads_specific: ya usa ads_mask=(yfam==ads) → Kerr excluido automáticamente.
        holo_mask = bulk_w.bool()
        if holo_mask.any():
            loss_physics = physics_loss_generic(
                out["A"][holo_mask], out["f"][holo_mask], z_t, d_value
            )
        else:
            loss_physics = torch.tensor(0.0, device=device)
        ads_mask = (yfam == family_map["ads"])
        loss_physics_ads = physics_loss_ads_specific(out["A"], out["f"], z_t, d_value, ads_mask)
        
        # PAfAE'A+aEUR(TM)AfaEURsA,A(C)rdida total ponderada
        total = (
            LOSS_WEIGHT_A * loss_A + 
            LOSS_WEIGHT_F * loss_f + 
            LOSS_WEIGHT_R * loss_R +
            LOSS_WEIGHT_ZH * loss_zh + 
            LOSS_WEIGHT_FAMILY * loss_family +
            LOSS_WEIGHT_PHYSICS * loss_physics +
            LOSS_WEIGHT_PHYSICS_ADS * loss_physics_ads
        )
        
        total.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), GRAD_CLIP_NORM)
        optimizer.step()
        
        # Acumular para promedio
        batch_weight = (end - start) / n_train
        losses["total"] += float(total.item()) * batch_weight
        losses["A"] += float(loss_A.item()) * batch_weight
        losses["f"] += float(loss_f.item()) * batch_weight
        losses["R"] += float(loss_R.item()) * batch_weight
        losses["zh"] += float(loss_zh.item()) * batch_weight
        losses["family"] += float(loss_family.item()) * batch_weight
        losses["physics"] += float(loss_physics.item()) * batch_weight
        losses["physics_ads"] += float(loss_physics_ads.item()) * batch_weight
    
    return losses


@torch.no_grad()
def evaluate_on_test(
    model: nn.Module,
    X_test: torch.Tensor,
    Y_A_test: np.ndarray,
    Y_f_test: np.ndarray,
    Y_R_test: np.ndarray,
    Y_zh_test: np.ndarray,
    Y_family_test: np.ndarray,
    normalizer: TargetNormalizer,
    device: torch.device,
    z_grid: torch.Tensor = None,  # V2.3: necesario para calcular R
) -> Dict[str, float]:
    """
    Evalua el modelo en el conjunto de test y devuelve metricas.
    """
    model.eval()
    
    # V2.3: Pasar z_grid para calcular R desde A,f
    out = model(X_test, z_grid=z_grid)
    
    # Desnormalizar predicciones
    A_pred_norm = out["A"].cpu().numpy()
    f_pred_norm = out["f"].cpu().numpy()
    R_pred_norm = out["R"].cpu().numpy()
    zh_pred_raw = out["z_h"].cpu().numpy()
    zh_pred = np.maximum(zh_pred_raw, 0.0)
    family_logits = out["family_logits"].cpu().numpy()
    family_probs = torch.softmax(out["family_logits"], dim=1).cpu().numpy()
    family_pred = np.argmax(family_logits, axis=1)
    
    A_pred = normalizer.denormalize_A(A_pred_norm)
    f_pred = normalizer.denormalize_f(f_pred_norm)
    # FAfAE'A+aEUR(TM)AfaEURsA,A-sica: f(z) AfAE'A,AcAfAcAcaEURsA!A,A?AfaEURsA,AJPY 0 por causalidad (signatura de la mAfAE'A+aEUR(TM)AfaEURsA,A(C)trica),
    # y f(z) AfAE'A,AcAfAcAcaEURsA!A,A?AfaEURsA,A? 1 en geometrAfAE'A+aEUR(TM)AfaEURsA,A-as tAfAE'A+aEUR(TM)AfaEURsA,A(C)rmicas con horizonte bien definido
    f_pred = np.clip(f_pred, 0.0, 1.0)
    R_pred = normalizer.denormalize_R(R_pred_norm)
    
    metrics = {
        "A_r2": compute_r2(Y_A_test, A_pred),
        "f_r2": compute_r2(Y_f_test, f_pred),
        "R_r2": compute_r2(Y_R_test, R_pred),
        "zh_mae": compute_mae(zh_pred, Y_zh_test),
        "family_accuracy": float(np.mean(family_pred == Y_family_test)),
    }
    
    return metrics, A_pred, f_pred, R_pred, zh_pred, family_pred


# ============================================================
# INFERENCE DE GEOMETRAfAE'A+aEUR(TM)AfaEURsA,A?A (BOUNDARY-ONLY) - V2.2 NUEVO
# ============================================================

@torch.no_grad()
def run_inference_single(
    model: nn.Module,
    X: np.ndarray,
    normalizer: TargetNormalizer,
    family_map_inv: Dict[int, str],
    device: torch.device,
    z_grid: torch.Tensor = None,  # V2.3: necesario para calcular R
) -> Dict[str, np.ndarray]:
    """
    Ejecuta inferencia sobre un unico sistema (un vector de features).
    
    Args:
        model: Modelo loaded from checkpoint
        X: Vector de features [n_features]
        normalizer: TargetNormalizer para desnormalizar Outputs:
        family_map_inv: Mapeo id -> nombre de family
        device: Dispositivo torch
        z_grid: Grid radial (necesario para calcular R desde A,f)
    
    Returns:
        Dict con A_pred, f_pred, R_pred, zh_pred, family_pred, family_name
    """
    model.eval()
    
    # Anadir dimension de batch si es necesario
    if X.ndim == 1:
        X = X[np.newaxis, :]
    
    X_t = torch.from_numpy(X.astype(np.float32)).to(device)
    # V2.3: Pasar z_grid para calcular R desde A,f
    out = model(X_t, z_grid=z_grid)
    
    # Desnormalizar
    A_pred_norm = out["A"].cpu().numpy()
    f_pred_norm = out["f"].cpu().numpy()
    R_pred_norm = out["R"].cpu().numpy()
    zh_pred_raw = out["z_h"].cpu().numpy()
    zh_pred = np.maximum(zh_pred_raw, 0.0)
    family_logits = out["family_logits"].cpu().numpy()
    family_probs = torch.softmax(out["family_logits"], dim=1).cpu().numpy()
    
    A_pred = normalizer.denormalize_A(A_pred_norm)
    f_pred = normalizer.denormalize_f(f_pred_norm)
    f_pred = np.clip(f_pred, 0.0, 1.0)
    R_pred = normalizer.denormalize_R(R_pred_norm)
    
    family_prob_row = family_probs[0]
    family_report = build_family_inference_report(family_prob_row, family_map_inv)

    return {
        "A_pred": A_pred[0],  # Quitar dimensiAfAE'A+aEUR(TM)AfaEURsA,A3n de batch
        "f_pred": f_pred[0],
        "R_pred": R_pred[0],
        "zh_pred_raw": float(zh_pred_raw[0]),
        "zh_pred": float(zh_pred[0]),
        "zh_pred_was_clipped": bool(zh_pred_raw[0] < 0.0),
        **family_report,
    }


def run_inference_mode(args):
    """
    inference mode: carga checkpoint sandbox, procesa boundary-only, genera .h5
    
    NO accede a bulk_truth en ningAfAE'A+aEUR(TM)AfaEURsA,Aon momento.
    """
    print("=" * 70)
    print("FASE XI V2.2 - inference mode (BOUNDARY-ONLY)")
    print("=" * 70)

    device = resolve_runtime_device(args.device)
    
    # Validar argumentos
    if args.checkpoint is None:
        raise ValueError(
            "En mode='inference' debes pasar --checkpoint con un modelo "
            "entrenado en sandbox"
        )
    
    checkpoint_path = Path(args.checkpoint)
    if not checkpoint_path.exists():
        raise FileNotFoundError(f"No se encontrAfAE'A+aEUR(TM)AfaEURsA,A3 el checkpoint: {checkpoint_path}")
    
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    
    print(f"  Checkpoint:   {checkpoint_path}")
    print(f"  Datos:        {data_dir}")
    print(f"  Salida:       {output_dir}")
    print(f"  Dispositivo:  {device}")
    print("=" * 70)
    
    # === CARGAR CHECKPOINT ===
    print("\n>> Cargando checkpoint sandbox...")
    ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)

    
    # Extraer configuraciAfAE'A+aEUR(TM)AfaEURsA,A3n del modelo
    n_features = ckpt["n_features"]
    n_z = ckpt["n_z"]
    hidden_dim = ckpt.get("hidden_dim", 256)
    n_layers = ckpt.get("n_layers", 4)
    # Fallback: si el checkpoint no tiene family_map, usar el registro canónico.
    # El registro extiende el mapa original (índices 0-4 idénticos) con Tier A.
    _default_fm = _REGISTRY_FAMILY_MAP if _HAS_FAMILY_REGISTRY else {
        "ads": 0, "lifshitz": 1, "hyperscaling": 2, "deformed": 3, "unknown": 4,
        "kerr": 6,
        "charged_hvlif": 7, "gauss_bonnet": 8, "linear_axion": 9,
        "massive_gravity": 10, "rn_ads": 11,
        "gubser_rocha": 12, "soft_wall": 13,
    }
    family_map = ckpt.get("family_map", _default_fm)
    family_map_inv = {v: k for k, v in family_map.items()}
    
    # NormalizaciAfAE'A+aEUR(TM)AfaEURsA,A3n de features (X)
    X_mean = ckpt.get("X_mean", np.zeros(n_features))
    X_std = ckpt.get("X_std", np.ones(n_features))
    if isinstance(X_mean, np.ndarray) and X_mean.ndim > 1:
        X_mean = X_mean.flatten()
    if isinstance(X_std, np.ndarray) and X_std.ndim > 1:
        X_std = X_std.flatten()
    
    # NormalizaciAfAE'A+aEUR(TM)AfaEURsA,A3n de targets
    normalizer = TargetNormalizer.from_dict(ckpt.get("normalizer", {}))
    
    # z_grid del checkpoint (CRAfAE'A+aEUR(TM)AfaEURsA,A?TICO: usar el mismo que en train)
    z_grid = ckpt.get("z_grid", np.linspace(0.01, 5.0, n_z))
    d_value = ckpt.get("d", 4)
    
    print(f"  Checkpoint:  {checkpoint_path}")
    print(f"   z_grid: [{z_grid[0]:.3f}, {z_grid[-1]:.3f}], {len(z_grid)} points")
    print(f"   d (checkpoint): {d_value}")
    
    # === CREAR MODELO Y CARGAR PESOS ===
    model = EmergentGeometryNet(
        n_features=n_features,
        n_z=n_z,
        hidden_dim=hidden_dim,
        n_layers=n_layers,
        n_families=len(family_map),
        d=d_value,  # V2.3: necesario para calcular R desde A,f
    ).to(device)
    
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()
    print("   Modelo cargado correctamente")
    
    # === PREPARAR directoryS DE SALIDA ===
    geom_dir = output_dir / "geometry_emergent"
    geom_dir.mkdir(parents=True, exist_ok=True)

    preds_dir = output_dir / "predictions"
    preds_dir.mkdir(parents=True, exist_ok=True)
    
    # === CARGAR MANIFEST ===
    manifest_path = data_dir / "geometries_manifest.json"
    if not manifest_path.exists():
        manifest_path = data_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"geometries_manifest.json / manifest.json not found en {data_dir}")

    manifest = json.loads(manifest_path.read_text())
    geometries = manifest.get("geometries", [])
    
    print(f"\n>> Procesando {len(geometries)} sistemas...")
    
    # === PROCESAR CADA SISTEMA ===
    loader = CuerdasDataLoader(mode="inference")  # BLOQUEA acceso a bulk_truth
    
    summary_entries = []
    _n_gate_fail = 0

    for geo_info in geometries:
        name = geo_info["name"]
        h5_path = data_dir / f"{name}.h5"
        
        if not h5_path.exists():
            print(f"   [WARN] Does not exist: {h5_path}")
            continue
        
        print(f"   Procesando: {name}")
        
        with h5py.File(h5_path, "r") as f:
            # Solo carga boundary (bulk_truth bloqueado)
            boundary_data, operators = loader.load_boundary_and_meta(f)
        
        # Extraer d del boundary o manifest
        d_boundary = geo_info.get("d", boundary_data.get("d", d_value))
        if isinstance(d_boundary, np.ndarray):
            d_boundary = int(d_boundary.ravel()[0])
        boundary_data["d"] = d_boundary
        
        # Construir features (V3 — 17 features, no QNM block)
        X = build_feature_vector_v3(boundary_data, operators)

        # Feature support audit (V3 gate)
        # Resolve support_mode from args (default: strict)
        _support_mode = getattr(args, 'support_mode', SUPPORT_MODE_STRICT)
        gate_report = None  # Will hold gate metadata for H5 output

        if HAS_FEATURE_SUPPORT and audit_feature_support is not None:
            _x_mean_flat = X_mean.flatten() if hasattr(X_mean, 'flatten') else np.asarray(X_mean).flatten()
            _x_std_flat = (X_std.flatten() if hasattr(X_std, 'flatten') else np.asarray(X_std).flatten())
            gate_report = audit_feature_support(
                feature_vector=X,
                X_mean=_x_mean_flat,
                X_std=_x_std_flat,
                feature_names=list(FEATURE_NAMES_V3),
                critical_features=list(CRITICAL_FEATURES_V3),
                support_mode=_support_mode,
            )
            if gate_report.verdict == "FAIL":
                _n_gate_fail += 1
                print(f"   [GATE FAIL] {name}: {gate_report.verdict_reason}")
                continue  # skip normalization + inference for this system
            elif gate_report.verdict == "OOD_PASS":
                # permissive_ood mode: allow inference with explicit OOD flag
                _n_ood_pass = getattr(args, '_n_ood_pass', 0) + 1
                setattr(args, '_n_ood_pass', _n_ood_pass)
                print(f"   [OOD PASS] {name}: {gate_report.verdict_reason}")
                # Continue with inference but gate_report carries OOD metadata
            elif gate_report.verdict == "WARN":
                print(f"   [GATE WARN] {name}: {gate_report.verdict_reason}")

        # NaN/Inf-safe features (inference): evita que el modelo propague NaNs
        if not np.all(np.isfinite(X)):
            if args.verbose:
                n_bad = int(np.sum(~np.isfinite(X)))
                print(f"   [WARN] Features no finitas en {name}: {n_bad}/{len(X)} (se reemplazan por 0.0)")
            X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

        
        # Normalizar features con estadAfAE'A+aEUR(TM)AfaEURsA,A-sticas del checkpoint
        # Si alguna feature fue casi constante en train (X_std tiny), proyectar a la media del checkpoint
        std_floor = 1e-6
        tiny_std = (X_std < std_floor)
        if np.any(tiny_std):
            if args.verbose:
                idxs = np.where(tiny_std)[0].tolist()
                print(f"   [WARN] X_std < {std_floor} en idx {idxs}; fijando X=X_mean en esas componentes")
            X = np.where(tiny_std, X_mean, X)

        X_norm = (X - X_mean) / X_std
        X_norm = np.clip(X_norm, -10.0, 10.0)
        
        # V2.3: Convertir z_grid a tensor para calcular R
        z_t = torch.from_numpy(z_grid.astype(np.float32)).to(device)
        
        # Inferencia
        preds = run_inference_single(model, X_norm, normalizer, family_map_inv, device, z_grid=z_t)
        
        # === GUARDAR COMO .h5 (IO_CONTRACTS_V1) ===
        out_h5_path = geom_dir / f"{name}_emergent.h5"
        
        with h5py.File(out_h5_path, "w") as f_out:
            # Atributos (IO_CONTRACTS_V1)
            family_pred = preds["family_name"]
            f_out.attrs["system_name"] = name
            # CanAfAE'A+aEUR(TM)AfaEURsA,A3nico: 'family' debe existir (family_pred es opcional)
            f_out.attrs["family"] = family_pred
            f_out.attrs["family_pred"] = family_pred
            f_out.attrs["family_raw_pred"] = preds["family_raw_name"]
            f_out.attrs["family_best_compatibility_label"] = preds["family_raw_name"]
            f_out.attrs["family_output_semantics"] = preds["family_output_semantics"]
            f_out.attrs["family_classification_mode"] = preds["family_classification_mode"]
            f_out.attrs["family_pred_confident"] = preds["family_pred_confident"]
            f_out.attrs["family_pred_was_abstained"] = preds["family_pred_was_abstained"]
            f_out.attrs["family_abstention_reason"] = preds["family_abstention_reason"]
            f_out.attrs["family_scores_json"] = json.dumps(preds["family_scores"], sort_keys=True)
            f_out.attrs["d"] = int(d_boundary)
            f_out.attrs["d_pred"] = int(d_boundary)
            # CanAfAE'A+aEUR(TM)AfaEURsA,A3nico: provenance AfAE'A,AcAfaEUR1Aca,!A AfaEUR1Aca,!A  {"train","inference"}
            f_out.attrs["provenance"] = "inference"
            # Detalle de trazabilidad (no contractual)
            f_out.attrs["provenance_detail"] = "inference_from_boundary_using_sandbox_model"
            f_out.attrs["zh_pred"] = preds["zh_pred"]
            f_out.attrs["zh_pred_raw"] = preds["zh_pred_raw"]
            f_out.attrs["zh_pred_was_clipped"] = preds["zh_pred_was_clipped"]
            f_out.attrs["family_top1_score"] = preds["family_top1_score"]
            f_out.attrs["family_top2_score"] = preds["family_top2_score"]
            f_out.attrs["family_margin"] = preds["family_margin"]
            f_out.attrs["family_entropy"] = preds["family_entropy"]
            f_out.attrs["checkpoint_source"] = str(checkpoint_path)

            # OOD-permissive mode metadata (support_mode gate contract)
            if gate_report is not None:
                f_out.attrs["support_mode"] = gate_report.support_mode
                f_out.attrs["ood_status"] = gate_report.ood_status
                f_out.attrs["g2_large_x_status"] = gate_report.g2_large_x_status
                f_out.attrs["run_policy"] = gate_report.run_policy
                if gate_report.ood_features:
                    f_out.attrs["ood_features"] = json.dumps(gate_report.ood_features)
            else:
                # Fallback when feature_support not available
                f_out.attrs["support_mode"] = _support_mode
                f_out.attrs["ood_status"] = "none"
                f_out.attrs["g2_large_x_status"] = "unknown"
                f_out.attrs["run_policy"] = "canonical_strict" if _support_mode == "strict" else "ood_permissive"

            # Datasets (IO_CONTRACTS_V1) AfAE'A,AcAfAcAca,!A!A,A!AfAcAcaEURsA!A,A? nombres canAfAE'A+aEUR(TM)AfaEURsA,A3nicos
            f_out.create_dataset("z_grid", data=z_grid)
            f_out.create_dataset("A_of_z", data=preds["A_pred"])
            f_out.create_dataset("f_of_z", data=preds["f_pred"])
            # Opcional pero AfAE'A+aEUR(TM)AfaEURsA,Aotil para contratos/diagnAfAE'A+aEUR(TM)AfaEURsA,A3stico
            f_out.create_dataset("R_of_z", data=preds["R_pred"])

            # Export NPZ (compatibilidad con 03/04)
            A_arr = preds.get('A_pred', preds.get('A_of_z'))
            f_arr = preds.get('f_pred', preds.get('f_of_z'))
            R_arr = preds.get('R_pred', preds.get('R_of_z'))
            if A_arr is None or f_arr is None or R_arr is None:
                raise ValueError(f"[inference] faltan A/f/R para {name}")
            np.savez(
                preds_dir / f"{name}_geometry.npz",
                z=np.asarray(z_grid, dtype=np.float64),
                z_grid=np.asarray(z_grid, dtype=np.float64),
                A_pred=np.asarray(A_arr, dtype=np.float32),
                f_pred=np.asarray(f_arr, dtype=np.float32),
                R_pred=np.asarray(R_arr, dtype=np.float32),
                A_of_z=np.asarray(A_arr, dtype=np.float32),
                f_of_z=np.asarray(f_arr, dtype=np.float32),
                R_of_z=np.asarray(R_arr, dtype=np.float32),
                family_pred=np.array(str(preds.get('family_name','unknown')), dtype=object),
                family_raw_pred=np.array(str(preds.get('family_raw_name','unknown')), dtype=object),
                family_best_compatibility_label=np.array(str(preds.get('family_raw_name','unknown')), dtype=object),
                family_output_semantics=np.array(str(preds.get('family_output_semantics', FAMILY_OUTPUT_SEMANTICS)), dtype=object),
                family_classification_mode=np.array(str(preds.get('family_classification_mode', 'abstained')), dtype=object),
                family_pred_confident=np.array(bool(preds.get('family_pred_confident', False)), dtype=np.bool_),
                family_pred_was_abstained=np.array(bool(preds.get('family_pred_was_abstained', True)), dtype=np.bool_),
                family_abstention_reason=np.array(str(preds.get('family_abstention_reason', 'unknown')), dtype=object),
                family_scores_json=np.array(json.dumps(preds.get('family_scores', {}), sort_keys=True), dtype=object),
                family_top1_score=np.array(float(preds.get('family_top1_score', float('nan'))), dtype=np.float32),
                family_top2_score=np.array(float(preds.get('family_top2_score', float('nan'))), dtype=np.float32),
                family_margin=np.array(float(preds.get('family_margin', float('nan'))), dtype=np.float32),
                family_entropy=np.array(float(preds.get('family_entropy', float('nan'))), dtype=np.float32),
                zh_pred=np.array(float(preds.get('zh_pred', float('nan'))), dtype=np.float32),
                zh_pred_raw=np.array(float(preds.get('zh_pred_raw', float('nan'))), dtype=np.float32),
                d=np.array(int(d_boundary), dtype=np.int32),
                provenance=np.array('inference', dtype=object),
            )

        summary_entries.append({
            "name": name,
            "h5_input": str(h5_path),
            "h5_output": str(out_h5_path),
            "family_pred": preds["family_name"],
            "family_raw_pred": preds["family_raw_name"],
            "family_best_compatibility_label": preds["family_raw_name"],
            "family_output_semantics": preds["family_output_semantics"],
            "family_classification_mode": preds["family_classification_mode"],
            "family_pred_confident": preds["family_pred_confident"],
            "family_pred_was_abstained": preds["family_pred_was_abstained"],
            "family_abstention_reason": preds["family_abstention_reason"],
            "family_scores": preds["family_scores"],
            "family_top1_score": preds["family_top1_score"],
            "family_top2_score": preds["family_top2_score"],
            "family_margin": preds["family_margin"],
            "family_entropy": preds["family_entropy"],
            "zh_pred_raw": preds["zh_pred_raw"],
            "zh_pred": preds["zh_pred"],
            "zh_pred_was_clipped": preds["zh_pred_was_clipped"],
            "d": d_boundary,
            "provenance": "inference",
            "provenance_detail": "inference_from_boundary_using_sandbox_model",
            "family": preds["family_name"],
        })
        
        print(
            "      -> "
            f"family_pred={preds['family_name']} "
            f"(raw={preds['family_raw_name']}, mode={preds['family_classification_mode']}), "
            f"zh_pred={preds['zh_pred']:.3f}"
        )

    # === GATE FAIL CHECK ===
    # Write summary before raising so the caller can inspect it (test contract)
    _summary_pre: Dict[str, Any] = {
        "version": "V2.2",
        "mode": "inference",
        "feature_contract": "v3",
        "n_features": 17,
        "description": (
            "Geometría emergente inferida desde datos boundary-only "
            "usando modelo entrenado en sandbox"
        ),
        "checkpoint": str(checkpoint_path),
        "n_systems": len(summary_entries),
        "z_grid_from_checkpoint": {
            "min": float(z_grid[0]),
            "max": float(z_grid[-1]),
            "n_points": len(z_grid),
        },
        "systems": summary_entries,
        "metrics": None,
    }
    _summary_path_pre = output_dir / "emergent_geometry_summary.json"
    _summary_path_pre.write_text(json.dumps(_summary_pre, indent=2, ensure_ascii=False, default=str))

    if _n_gate_fail > 0:
        raise RuntimeError(
            f"UNSUPPORTED_FEATURE_REGIME: {_n_gate_fail}/{len(summary_entries)} systems failed "
            "the V3 feature support gate. Inference aborted."
        )

    # === ESCRIBIR RUN_MANIFEST (IO v2) ===
    if HAS_CUERDAS_IO:
        manifest_artifacts = {
            "data_dir": str(data_dir.relative_to(output_dir) if data_dir.is_relative_to(output_dir) else data_dir),
            "checkpoint": str(checkpoint_path.relative_to(output_dir) if checkpoint_path.is_relative_to(output_dir) else checkpoint_path),
            "geometry_emergent_dir": "geometry_emergent",
            "predictions_dir": "predictions",
            "summary_json": "emergent_geometry_summary.json",
            "systems": [
                {
                    "name": e["name"],
                    "h5_output": f"geometry_emergent/{e['name']}_emergent.h5",
                    "npz_output": f"predictions/{e['name']}_geometry.npz",
                }
                for e in summary_entries
            ]
        }
        manifest_metadata = {
            "script": "02_emergent_geometry_engine.py",
            "mode": "inference",
            "version": "V2.2",
        }
        try:
            manifest_path = write_run_manifest(output_dir, manifest_artifacts, manifest_metadata)
            print(f"  Manifest:     {manifest_path}")
        except Exception as e:
            print(f"  [WARN] No se pudo escribir run_manifest.json: {e}")
    
    # === BANNER FINAL ===
    print("\n" + "=" * 70)
    print("[OK] FASE XI V2.2 - inference mode COMPLETADO")
    print(f"  GeometrAfAE'A+aEUR(TM)AfaEURsA,A-as:   {geom_dir}")
    print(f"  Summary:      {_summary_path_pre}")
    print(f"  Sistemas:     {len(summary_entries)}")
    print("=" * 70)
    print("Next step: 03_discover_bulk_equations.py")


# ============================================================
# MODO TRAIN (CAfAE'A+aEUR(TM)AfAcAcaEURsA!A...aEURoeDIGO ORIGINAL V2.1)
# ============================================================

def run_train_mode(args):
    """
    Modo train: comportamiento original (sandbox con bulk_truth).
    """
    # Set seed
    set_torch_seed(args.seed)
    
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    device = resolve_runtime_device(args.device)
    
    print("=" * 70)
    print("EMERGENT GEOMETRY ENGINE (MODO TRAIN)")
    print("Prioriza A(z) y f(z) sobre R(z) y clasificaciAfAE'A+aEUR(TM)AfaEURsA,A3n")
    print("=" * 70)
    print(f"  Pesos de loss: A={LOSS_WEIGHT_A}, f={LOSS_WEIGHT_F}, R={LOSS_WEIGHT_R}")
    print(f"                 zh={LOSS_WEIGHT_ZH}, family={LOSS_WEIGHT_FAMILY}")
    print(f"                 physics={LOSS_WEIGHT_PHYSICS}, ads={LOSS_WEIGHT_PHYSICS_ADS}")
    print("=" * 70)
    
    # Cargar manifest (geometries_manifest.json tiene precedencia sobre manifest.json)
    manifest_path = data_dir / "geometries_manifest.json"
    if not manifest_path.exists():
        manifest_path = data_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"geometries_manifest.json / manifest.json not found en {data_dir}")
    manifest = json.loads(manifest_path.read_text())
    
    # family_map: fuente canónica desde family_registry.
    # Si el módulo no está disponible, fallback inline (mismo orden de índices).
    if _HAS_FAMILY_REGISTRY:
        family_map = dict(_REGISTRY_FAMILY_MAP)
    else:
        family_map = {
            "ads": 0, "lifshitz": 1, "hyperscaling": 2, "deformed": 3,
            "dpbrane": 4, "unknown": 5, "kerr": 6,
            "charged_hvlif": 7, "gauss_bonnet": 8, "linear_axion": 9,
            "massive_gravity": 10, "rn_ads": 11,
            "gubser_rocha": 12, "soft_wall": 13,
        }
    family_map_inv = {v: k for k, v in family_map.items()}
    
    # Estructuras para datos
    train_data = {
        "X": [], "Y_A": [], "Y_f": [], "Y_R": [], "Y_zh": [], 
        "Y_family": [], "names": [], "families": []
    }
    test_data = {
        "X": [], "Y_A": [], "Y_f": [], "Y_R": [], "Y_zh": [], 
        "Y_family": [], "names": [], "categories": [], "families": []
    }
    
    z_grid = None
    d_value = 4
    
    loader = CuerdasDataLoader(mode="train")
    
    # Cargar datos
    print("\n>> Cargando geometrAfAE'A+aEUR(TM)AfaEURsA,A-as...")
    for geo_info in manifest["geometries"]:
        h5_path = data_dir / f"{geo_info['name']}.h5"
        if not h5_path.exists():
            print(f"   [WARN] Does not exist: {h5_path}")
            continue
            
        category = geo_info["category"]
        
        with h5py.File(h5_path, "r") as f:
            boundary_data, operators = loader.load_boundary_and_meta(f)
            (A_truth, f_truth, R_truth, z_grid_local, z_h, family, d_value_local, has_bulk
            ) = loader.load_bulk_truth(f)
            d_value = d_value_local

        if z_grid is None:
            z_grid = z_grid_local

        # AAfAE'A+aEUR(TM)A+-adir d a boundary_data para feature extraction
        boundary_data["d"] = d_value_local

        X = build_feature_vector_v3(boundary_data, operators)
        family_id = family_map.get(family, 4)

        if category == "known":
            train_data["X"].append(X)
            train_data["Y_A"].append(A_truth)
            train_data["Y_f"].append(f_truth)
            train_data["Y_R"].append(R_truth)
            train_data["Y_zh"].append(z_h if z_h else 0.0)
            train_data["Y_family"].append(family_id)
            train_data["names"].append(geo_info["name"])
            train_data["families"].append(family)
            train_data.setdefault("has_bulk", []).append(has_bulk)
        else:
            test_data["X"].append(X)
            test_data["Y_A"].append(A_truth)
            test_data["Y_f"].append(f_truth)
            test_data["Y_R"].append(R_truth)
            test_data["Y_zh"].append(z_h if z_h else 0.0)
            test_data["Y_family"].append(family_id)
            test_data["names"].append(geo_info["name"])
            test_data["categories"].append(category)
            test_data["families"].append(family)
    
    if len(train_data["X"]) == 0:
        raise ValueError("No hay datos de entrenamiento (category='known')")
    
    # Convertir a arrays
    X_train = np.stack(train_data["X"])
    Y_A_train = np.stack(train_data["Y_A"])
    Y_f_train = np.stack(train_data["Y_f"])
    Y_R_train = np.stack(train_data["Y_R"])
    Y_zh_train = np.array(train_data["Y_zh"])
    Y_family_train = np.array(train_data["Y_family"])
    
    print(f"\n   TRAIN (known):       {len(X_train)} geometrAfAE'A+aEUR(TM)AfaEURsA,A-as")
    print(f"   TEST (test/unknown): {len(test_data['X'])} geometrAfAE'A+aEUR(TM)AfaEURsA,A-as")
    print(f"   Features:            {X_train.shape[1]}")
    print(f"   n_z (puntos radial): {Y_A_train.shape[1]}")
    
    # Contar por family en train
    print("\n   DistribuciAfAE'A+aEUR(TM)AfaEURsA,A3n por family (train):")
    for fam_name, fam_id in family_map.items():
        count = np.sum(Y_family_train == fam_id)
        if count > 0:
            print(f"     {fam_name}: {count}")
    
    # === FEATURE SUPPORT AUDIT (V3 train gate) ===
    if HAS_FEATURE_SUPPORT and audit_train_feature_support is not None:
        _X_std_raw = X_train.std(axis=0)
        critical_features_for_audit, _train_audit_context_msg = (
            _resolve_train_audit_critical_features(
                feature_names=list(FEATURE_NAMES_V3),
                X_std_raw=_X_std_raw,
                critical_features=list(CRITICAL_FEATURES_V3),
            )
        )
        if _train_audit_context_msg:
            print(f"\n   {_train_audit_context_msg}")
        _train_audit = audit_train_feature_support(
            feature_names=list(FEATURE_NAMES_V3),
            X_mean=X_train.mean(axis=0),
            X_std=_X_std_raw,
            critical_features=critical_features_for_audit,
        )
        print(f"\n   Train feature audit: verdict={_train_audit['verdict']}")
        if _train_audit["verdict_reason"]:
            print(f"     {_train_audit['verdict_reason']}")
        if _train_audit["verdict"] == "FAIL":
            raise RuntimeError(
                f"TRAIN_FEATURE_SUPPORT_FAIL: {_train_audit['verdict_reason']}"
            )

    # === NORMALIZACIAfAE'A+aEUR(TM)AfAcAcaEURsA!A...aEURoeN ===

    # Features
    X_mean = X_train.mean(axis=0, keepdims=True)
    X_std = X_train.std(axis=0, keepdims=True) + 1e-8
    X_train_norm = (X_train - X_mean) / X_std

    # Targets
    normalizer = TargetNormalizer()
    normalizer.fit(Y_A_train, Y_f_train, Y_R_train)
    
    Y_A_train_norm = normalizer.normalize_A(Y_A_train)
    Y_f_train_norm = normalizer.normalize_f(Y_f_train)
    Y_R_train_norm = normalizer.normalize_R(Y_R_train)
    
    print(f"\n   NormalizaciAfAE'A+aEUR(TM)AfaEURsA,A3n:")
    print(f"     A: mean={normalizer.A_mean:.3f}, std={normalizer.A_std:.3f}")
    print(f"     f: mean={normalizer.f_mean:.3f}, std={normalizer.f_std:.3f}")
    print(f"     R: mean={normalizer.R_mean:.3f}, std={normalizer.R_std:.3f}")
    
    # Convertir a tensores
    X_train_t = torch.from_numpy(X_train_norm.astype(np.float32)).to(device)
    Y_A_train_t = torch.from_numpy(Y_A_train_norm.astype(np.float32)).to(device)
    Y_f_train_t = torch.from_numpy(Y_f_train_norm.astype(np.float32)).to(device)
    Y_R_train_t = torch.from_numpy(Y_R_train_norm.astype(np.float32)).to(device)
    Y_zh_train_t = torch.from_numpy(Y_zh_train.astype(np.float32)).to(device)
    Y_family_train_t = torch.from_numpy(Y_family_train.astype(np.int64)).to(device)
    z_t = torch.from_numpy(z_grid.astype(np.float32)).to(device)
    has_bulk_train = np.array(train_data.get("has_bulk", [True] * len(train_data["X"])), dtype=bool)
    has_bulk_train_t = torch.from_numpy(has_bulk_train).to(device)

    # Preparar test
    has_test = len(test_data["X"]) > 0
    if has_test:
        X_test = np.stack(test_data["X"])
        X_test_norm = (X_test - X_mean) / X_std
        X_test_t = torch.from_numpy(X_test_norm.astype(np.float32)).to(device)
        Y_A_test = np.stack(test_data["Y_A"])
        Y_f_test = np.stack(test_data["Y_f"])
        Y_R_test = np.stack(test_data["Y_R"])
        Y_zh_test = np.array(test_data["Y_zh"])
        Y_family_test = np.array(test_data["Y_family"])
    
    # === MODELO ===
    
    model = EmergentGeometryNet(
        n_features=X_train.shape[1],
        n_z=Y_A_train.shape[1],
        hidden_dim=args.hidden_dim,
        n_layers=args.n_layers,
        n_families=len(family_map),
        d=d_value,  # V2.3: necesario para calcular R desde A,f
    ).to(device)
    
    n_params = sum(p.numel() for p in model.parameters())
    print(f"  Parameters: {n_params:,}")
    
    # === ENTRENAMIENTO ===
    
    optimizer = torch.optim.AdamW(
        model.parameters(), 
        lr=args.lr, 
        weight_decay=WEIGHT_DECAY
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, 
        T_max=args.n_epochs,
        eta_min=args.lr * 0.01
    )
    
    # Historia de entrenamiento
    history = {
        "train_losses": [],
        "test_metrics": [],
        "epochs": []
    }
    
    best_test_A_r2 = -np.inf
    best_epoch = 0
    
    print("\n>> Iniciando entrenamiento...")
    print("-" * 70)
    
    for epoch in range(1, args.n_epochs + 1):
        # Entrenar una AfAE'A+aEUR(TM)AfaEURsA,A(C)poca
        train_losses = train_one_epoch(
            model, X_train_t, Y_A_train_t, Y_f_train_t, Y_R_train_t,
            Y_zh_train_t, Y_family_train_t, z_t, d_value, family_map,
            optimizer, args.batch_size, device,
            has_bulk_mask=has_bulk_train_t,
        )
        
        # Actualizar scheduler por AfAE'A+aEUR(TM)AfAcAcaEURsA!A,A?POCA (no por batch)
        scheduler.step()
        
        # Guardar historia
        history["train_losses"].append(train_losses)
        history["epochs"].append(epoch)
        
        # Evaluar en test periAfAE'A+aEUR(TM)AfaEURsA,A3dicamente
        should_eval = (epoch % EVAL_FREQUENCY == 0) or (epoch == 1) or (epoch == args.n_epochs)
        
        if has_test and should_eval:
            test_metrics, _, _, _, _, _ = evaluate_on_test(
                model, X_test_t, Y_A_test, Y_f_test, Y_R_test,
                Y_zh_test, Y_family_test, normalizer, device,
                z_grid=z_t  # V2.3: necesario para calcular R
            )
            history["test_metrics"].append({"epoch": epoch, **test_metrics})
            
            # Tracking del mejor modelo
            if test_metrics["A_r2"] > best_test_A_r2:
                best_test_A_r2 = test_metrics["A_r2"]
                best_epoch = epoch
        
        # Logging
        if args.verbose and (epoch % max(1, args.n_epochs // 20) == 0 or epoch == 1):
            lr_current = scheduler.get_last_lr()[0]
            log_msg = (
                f"[Epoch {epoch:4d}/{args.n_epochs}] "
                f"L_total={train_losses['total']:.4f} | "
                f"L_A={train_losses['A']:.4f} | "
                f"L_f={train_losses['f']:.4f} | "
                f"lr={lr_current:.2e}"
            )
            
            if has_test and should_eval:
                log_msg += f" || Test: A_r2={test_metrics['A_r2']:.3f}, f_r2={test_metrics['f_r2']:.3f}"
            
            print(log_msg)
    
    print("-" * 70)
    
    # === EVALUACIAfAE'A+aEUR(TM)AfAcAcaEURsA!A...aEURoeN FINAL EN TEST ===
    
    geom_dir = output_dir / "geometry_emergent"
    geom_dir.mkdir(parents=True, exist_ok=True)
    preds_dir = output_dir / "predictions"
    preds_dir.mkdir(parents=True, exist_ok=True)
    systems_summary = []
    
    if has_test:
        print("\n>> EvaluaciAfAE'A+aEUR(TM)AfaEURsA,A3n final en TEST...")
        
        test_metrics_final, A_pred, f_pred, R_pred, zh_pred, family_pred = evaluate_on_test(
            model, X_test_t, Y_A_test, Y_f_test, Y_R_test,
            Y_zh_test, Y_family_test, normalizer, device,
            z_grid=z_t  # V2.3: necesario para calcular R
        )
        
        print(f"\n   TEST Metrics (final):")
        print(f"   A(z) RAfAE'Aca,!A!A2:         {test_metrics_final['A_r2']:.4f}")
        print(f"   f(z) RAfAE'Aca,!A!A2:         {test_metrics_final['f_r2']:.4f}")
        print(f"   R(z) RAfAE'Aca,!A!A2:         {test_metrics_final['R_r2']:.4f}")
        print(f"   z_h MAE:         {test_metrics_final['zh_mae']:.4f}")
        print(f"   Family accuracy: {test_metrics_final['family_accuracy']:.4f}")
        print(f"\n   Mejor AfAE'A+aEUR(TM)AfaEURsA,A(C)poca (por A_r2): {best_epoch} con A_r2={best_test_A_r2:.4f}")
        
        # MAfAE'A+aEUR(TM)AfaEURsA,A(C)tricas por family
        metrics_by_family = {}
        for fam_name, fam_id in family_map.items():
            mask = Y_family_test == fam_id
            if np.sum(mask) > 0:
                metrics_by_family[fam_name] = {
                    "count": int(np.sum(mask)),
                    "A_r2": compute_r2(Y_A_test[mask], A_pred[mask]),
                    "f_r2": compute_r2(Y_f_test[mask], f_pred[mask]),
                }
        
        print("\n   MAfAE'A+aEUR(TM)AfaEURsA,A(C)tricas por family:")
        for fam_name, fam_metrics in metrics_by_family.items():
            if fam_metrics["count"] > 0:
                print(f"     {fam_name} (n={fam_metrics['count']}): "
                      f"A_r2={fam_metrics['A_r2']:.3f}, f_r2={fam_metrics['f_r2']:.3f}")
        
    else:
        test_metrics_final = {}
        metrics_by_family = {}

    # === INFERENCIA FINAL SOBRE LA COHORTE COMPLETA (train + test) ===
    # Stage 02 debe materializar geometry_emergent y predictions para TODA la cohorte
    # declarada en el manifest (N = n_train + n_test), no sólo para la subcohorte de test.
    # El split se mantiene intacto para las métricas de entrenamiento/validación.
    all_names = list(train_data["names"]) + list(test_data["names"])
    all_X_list = list(train_data["X"]) + list(test_data["X"])
    all_Y_A = np.stack(list(train_data["Y_A"]) + list(test_data["Y_A"]))
    all_Y_f = np.stack(list(train_data["Y_f"]) + list(test_data["Y_f"]))
    all_Y_R = np.stack(list(train_data["Y_R"]) + list(test_data["Y_R"]))
    all_Y_zh = np.array(list(train_data["Y_zh"]) + list(test_data["Y_zh"]))
    all_Y_family = np.array(list(train_data["Y_family"]) + list(test_data["Y_family"]))
    all_categories = (["known"] * len(train_data["names"])) + list(test_data["categories"])

    all_X = np.stack(all_X_list)
    all_X_norm = (all_X - X_mean) / X_std
    all_X_t = torch.from_numpy(all_X_norm.astype(np.float32)).to(device)

    (
        _,
        A_pred_all,
        f_pred_all,
        R_pred_all,
        zh_pred_all,
        family_pred_all,
    ) = evaluate_on_test(
        model, all_X_t, all_Y_A, all_Y_f, all_Y_R, all_Y_zh, all_Y_family,
        normalizer, device, z_grid=z_t
    )

    print(f"\n>> Materializando cohorte completa: {len(all_names)} geometrías")

    for i, name in enumerate(all_names):
        family_pred_idx = int(family_pred_all[i])
        family_pred_name = family_map_inv.get(family_pred_idx, f"family_{family_pred_idx}")
        family_truth_idx = int(all_Y_family[i])
        family_truth_name = family_map_inv.get(family_truth_idx, f"family_{family_truth_idx}")
        cat_i = all_categories[i]

        out_h5_path = geom_dir / f"{name}_emergent.h5"
        with h5py.File(out_h5_path, "w") as f_out:
            f_out.attrs["system_name"] = name
            # `family` es la semántica canónica (ground truth) preservada
            # desde stage 01. La predicción del modelo vive en `family_pred`.
            # No pisar la verdad con la predicción rompe la trazabilidad
            # semántica en el carril canónico (e.g. ADS/GKPW -> massive_gravity).
            f_out.attrs["family"] = family_truth_name
            f_out.attrs["family_pred"] = family_pred_name
            f_out.attrs["family_truth"] = family_truth_name
            f_out.attrs["family_pred_id"] = family_pred_idx
            f_out.attrs["family_truth_id"] = family_truth_idx
            f_out.attrs["category"] = cat_i
            f_out.attrs["d"] = int(d_value)
            f_out.attrs["d_pred"] = int(d_value)
            f_out.attrs["provenance"] = "train"
            f_out.attrs["provenance_detail"] = "train_mode_full_cohort_inference"
            f_out.attrs["zh_pred"] = float(zh_pred_all[i])
            f_out.attrs["zh_truth"] = float(all_Y_zh[i])
            f_out.create_dataset("z_grid", data=z_grid)
            f_out.create_dataset("A_of_z", data=A_pred_all[i])
            f_out.create_dataset("f_of_z", data=f_pred_all[i])
            f_out.create_dataset("R_of_z", data=R_pred_all[i])

        np.savez(
            preds_dir / f"{name}_geometry.npz",
            z=z_grid,
            A_pred=A_pred_all[i],
            f_pred=f_pred_all[i],
            R_pred=R_pred_all[i],
            A_truth=all_Y_A[i],
            f_truth=all_Y_f[i],
            R_truth=all_Y_R[i],
            zh_pred=zh_pred_all[i],
            zh_truth=all_Y_zh[i],
            family_pred=family_pred_all[i],
            family_truth=all_Y_family[i],
            category=cat_i,
        )
        systems_summary.append({
            "system_name": name,
            "name": name,
            "category": cat_i,
            "family_pred": family_pred_name,
            "family_truth": family_truth_name,
            "family_pred_id": family_pred_idx,
            "family_truth_id": family_truth_idx,
            "zh_pred": float(zh_pred_all[i]),
            "zh_truth": float(all_Y_zh[i]),
            "h5_output": str(out_h5_path),
            "npz_output": str(preds_dir / f"{name}_geometry.npz"),
        })
    
    # === GUARDAR MODELO ===
    
    model_path = output_dir / "emergent_geometry_model.pt"
    torch.save({
        "model_state_dict": model.state_dict(),
        "n_features": X_train.shape[1],
        "n_z": Y_A_train.shape[1],
        "hidden_dim": args.hidden_dim,
        "n_layers": args.n_layers,
        "family_map": family_map,
        "X_mean": X_mean,
        "X_std": X_std,
        "normalizer": {
            "A_mean": normalizer.A_mean,
            "A_std": normalizer.A_std,
            "f_mean": normalizer.f_mean,
            "f_std": normalizer.f_std,
            "R_mean": normalizer.R_mean,
            "R_std": normalizer.R_std,
        },
        "z_grid": z_grid,
        "d": d_value,
        "loss_weights": {
            "A": LOSS_WEIGHT_A,
            "f": LOSS_WEIGHT_F,
            "R": LOSS_WEIGHT_R,
            "zh": LOSS_WEIGHT_ZH,
            "family": LOSS_WEIGHT_FAMILY,
            "physics": LOSS_WEIGHT_PHYSICS,
            "physics_ads": LOSS_WEIGHT_PHYSICS_ADS,
        },
        "history": history,
        "best_epoch": best_epoch,
        "best_test_A_r2": best_test_A_r2,
    }, model_path)
    
    # === GUARDAR SUMMARY ===
    
    # Extraer AfAE'A+aEUR(TM)AfaEURsA,Aoltima loss de entrenamiento
    final_train_losses = history["train_losses"][-1] if history["train_losses"] else {}
    
    summary = {
        "version": "V2.2",
        "mode": "train",
        "n_train": int(len(X_train)),
        "n_test": int(len(test_data["X"])),
        "n_features": int(X_train.shape[1]),
        "n_z": int(Y_A_train.shape[1]),
        "n_epochs": args.n_epochs,
        "best_epoch": best_epoch,
        "loss_weights": {
            "A": LOSS_WEIGHT_A,
            "f": LOSS_WEIGHT_F,
            "R": LOSS_WEIGHT_R,
            "zh": LOSS_WEIGHT_ZH,
            "family": LOSS_WEIGHT_FAMILY,
            "physics": LOSS_WEIGHT_PHYSICS,
            "physics_ads": LOSS_WEIGHT_PHYSICS_ADS,
        },
        "train_metrics": {
            "final_total_loss": final_train_losses.get("total", 0.0),
            "final_A_loss": final_train_losses.get("A", 0.0),
            "final_f_loss": final_train_losses.get("f", 0.0),
            "final_R_loss": final_train_losses.get("R", 0.0),
            "final_zh_loss": final_train_losses.get("zh", 0.0),
            "final_family_loss": final_train_losses.get("family", 0.0),
            "final_physics_loss": final_train_losses.get("physics", 0.0),
        },
        "test_metrics": test_metrics_final,
        "metrics_by_family": metrics_by_family,
        "systems": systems_summary,
        "normalizer_stats": {
            "A_mean": normalizer.A_mean,
            "A_std": normalizer.A_std,
            "f_mean": normalizer.f_mean,
            "f_std": normalizer.f_std,
            "R_mean": normalizer.R_mean,
            "R_std": normalizer.R_std,
        },
    }
    
    summary_path = output_dir / "emergent_geometry_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str))
    
    # === ESCRIBIR RUN_MANIFEST (IO v2) ===
    if HAS_CUERDAS_IO:
        # Construir lista de sistemas desde summary
        systems_list = summary.get("systems", [])
        manifest_artifacts = {
            "data_dir": str(data_dir.relative_to(output_dir) if data_dir.is_relative_to(output_dir) else data_dir),
            "checkpoint": "emergent_geometry_model.pt",
            "geometry_emergent_dir": "geometry_emergent",
            "predictions_dir": "predictions",
            "summary_json": "emergent_geometry_summary.json",
            "systems": [
                {
                    "name": s.get("system_name", s.get("name", "unknown")),
                    "h5_output": f"geometry_emergent/{s.get('system_name', s.get('name', 'unknown'))}_emergent.h5",
                    "npz_output": f"predictions/{s.get('system_name', s.get('name', 'unknown'))}_geometry.npz",
                }
                for s in systems_list
            ]
        }
        manifest_metadata = {
            "script": "02_emergent_geometry_engine.py",
            "mode": "train",
            "version": "V2.2",
            "n_epochs": args.n_epochs,
            "seed": args.seed,
        }
        try:
            manifest_path = write_run_manifest(output_dir, manifest_artifacts, manifest_metadata)
            print(f"  Manifest:     {manifest_path}")
        except Exception as e:
            print(f"  [WARN] No se pudo escribir run_manifest.json: {e}")
    
    # === BANNER FINAL ===
    
    print("\n" + "=" * 70)
    print("[OK] EMERGENT GEOMETRY ENGINE COMPLETED (TRAIN MODE)")
    print(f"  Model:       {model_path}")
    print(f"  Geometry:    {geom_dir}")
    print(f"  Predictions: {preds_dir}")
    print(f"  Summary:      {summary_path}")
    print("=" * 70)
    print("Next step: 03_discover_bulk_equations.py")
    return {
        "model_path": model_path,
        "preds_dir": preds_dir,
        "summary_path": summary_path,
        "output_dir": output_dir,
        "geometry_dir": geom_dir,
    }


# ============================================================
# MAIN (V2.2)
# ============================================================

def main():
    parser = build_parser()

    args = parse_stage_args(parser)
    ctx = StageContext.from_args(args, stage_number="02", stage_slug="emergent_geometry_engine")
    project_root = Path(__file__).resolve().parent

    if args.data_dir is None:
        args.data_dir = str(ctx.run_root / "01_generate_sandbox_geometries")
    if args.output_dir is None:
        args.output_dir = str(ctx.stage_dir)

    status = STATUS_OK
    exit_code = EXIT_OK
    error_message: Optional[str] = None
    artifacts: List[Path] = []

    try:
        ctx.record_artifact(ctx.stage_dir)
    except Exception:
        pass

    try:
        global h5py  # type: ignore
        import h5py  # type: ignore

        # Despachar segAfAE'A+aEUR(TM)AfaEURsA,Aon modo
        if args.mode == "train":
            result = run_train_mode(args)
        elif args.mode == "inference":
            result = run_inference_mode(args)
        else:
            result = run_finetune_physics_mode(args)
        if isinstance(result, dict):
            for key in ["model_path", "preds_dir", "summary_path", "output_dir", "geometry_dir", "checkpoint"]:
                val = result.get(key)
                if val:
                    artifacts.append(Path(val))
        ctx.record_artifact(ctx.stage_dir)
        for art in artifacts:
            try:
                ctx.record_artifact(Path(art))
            except Exception:
                pass
        ctx.write_manifest(
            outputs={
                "geometry_engine_dir": safe_relative_path(Path(args.output_dir), ctx.run_root, project_root)
            },
            metadata={"command": " ".join(sys.argv), "mode": args.mode},
        )
    except Exception as exc:
        status = STATUS_ERROR
        exit_code = EXIT_ERROR
        error_message = str(exc)
        # Do NOT re-raise: allow finally to write summary and call sys.exit(EXIT_ERROR)
    finally:
        summary_path = ctx.stage_dir / "stage_summary.json"
        try:
            ctx.record_artifact(summary_path)
        except Exception:
            pass
        ctx.write_summary(status=status, exit_code=exit_code, error_message=error_message)
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
