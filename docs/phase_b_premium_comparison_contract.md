# Fase B — Baseline vs Premium Comparison Contract (beta)

## Objetivo
Comparar, para un mismo evento y mismos artefactos canónicos de entrada, el carril baseline frente al carril premium, sin habilitar downstream por defecto.

## Pregunta falsable
¿El carril premium produce una representación más estable e informativa que el baseline para el mismo evento?

## Inputs requeridos
- runs/<run_id>/premium_estimator/outputs/premium_estimate.json
- runs/<run_id>/premium_estimator/outputs/premium_features.npz
- artefacto baseline canónico del mismo evento
- configuración explícita versionada en repo

## Artefacto canónico requerido
runs/<run_id>/baseline_vs_premium_comparison/
  manifest.json
  stage_summary.json
  outputs/
    comparison_report.json
    comparison_metrics.json
    provenance.json

## Requisitos mínimos de comparison_metrics.json
- schema_version
- event_id
- baseline_artifacts
- premium_artifacts
- metrics
- verdict
- provenance_hash

## Requisitos mínimos de stage_summary.json
- stage_name = "baseline_vs_premium_comparison"
- status = PASS | FAIL | DEGRADED
- event_id
- n_inputs
- n_outputs
- warnings[]
- blocking_reason (si FAIL o DEGRADED)

## Métricas iniciales
- n_features_baseline
- n_features_premium
- compute_ran_premium
- placeholder_flag_premium
- estabilidad / completitud de artefactos
- disponibilidad de señales auditables para downstream

## Reglas de gobernanza
- Prohibido escribir fuera de runs/<run_id>/
- No habilitar downstream automáticamente
- PASS en este stage no implica PASS científico global
- Si falta cualquier input contractual, el run no existe

## Estado inicial
Este comparador nace bloqueado hasta que exista implementación canónica del stage.
