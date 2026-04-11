# Fase B — Premium Estimator Contract (beta)

## Objetivo
Construir un estimador upstream premium para eventos reales que mejore la calidad de la señal útil respecto al carril baseline actual, sin romper la gobernanza del pipeline.

## Pregunta falsable
¿El estimador premium produce una representación del evento real más estable e informativa que el baseline actual?

## Alcance
Esta fase NO sustituye todavía el downstream.
Primero produce artefactos canónicos comparables contra el baseline.

## Inputs permitidos
- Ventanas reales GWOSC ya descargadas
- Artefactos canónicos previos del carril baseline cuando se usen solo como referencia
- Configuración explícita versionada en repo

## Artefacto canónico requerido
El estimador premium deberá escribir exclusivamente bajo:

runs/<run_id>/premium_estimator/

con esta estructura mínima:

runs/<run_id>/premium_estimator/
  manifest.json
  stage_summary.json
  outputs/
    premium_estimate.json
    premium_features.npz
    provenance.json

## Requisitos mínimos de premium_estimate.json
- schema_version
- event_id
- estimator_name
- estimator_version
- input_artifacts
- status
- summary_metrics
- feature_paths
- provenance_hash

## Requisitos mínimos de stage_summary.json
- stage_name = "premium_estimator"
- status = PASS | FAIL | DEGRADED
- event_id
- estimator_name
- n_inputs
- n_outputs
- warnings[]
- blocking_reason (si FAIL)

## Reglas de gobernanza
- Prohibido escribir fuera de runs/<run_id>/
- Si falta cualquier input contractual, el run se considera inexistente
- No se habilita downstream si stage_summary.json no está en PASS
- No se inventan datasets intermedios ambiguos; si hacen falta, se formalizan como stage canónico

## Comparación obligatoria contra baseline
Toda evaluación de Fase B deberá comparar:
- mismo evento
- mismo tramo temporal
- baseline actual vs premium estimator
- mismas métricas de comparación
- misma política de persistencia

## Métricas iniciales de comparación
- estabilidad entre detectores
- estabilidad frente a ventana temporal
- consistencia de polos / features extraídas
- riqueza informativa para 02
- tasa de warnings / degradaciones

## Estado inicial
Fase B queda ABIERTA.
03 y downstream siguen bloqueados hasta que exista un premium_estimator con artefactos canónicos y comparación baseline-vs-premium.
