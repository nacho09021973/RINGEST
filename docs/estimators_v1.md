# Estimators v1

## Objetivo
Fijar una suite mínima y profesional de estimación para RINGEST en capas explícitas: contrato, gate de información, baseline, premium, calibración, null/OOD y ablación.

La decisión de diseño central es esta:

- El vector canónico de 20 features queda relegado a baseline reproducible y auditable.
- El estimador premium trabaja sobre señal ringdown, ASD/PSD y metadatos instrumentales, no sobre un resumen comprimido.

## Qué NO hace este documento
- No integra todavía estos estimadores en el pipeline canónico.
- No define entrenamiento, inferencia ni datasets definitivos.
- No legitima interpretación física antes de pasar los gates.
- No convierte DINGO en baseline.

## Principio de gobernanza
Contract-first.

Si falla una precondición contractual o un gate material, el run no existe y se aborta downstream.

## Suite v1

### E00 `input_contract_guard_v1`
Rol:
Validar que el input existe contractualmente y que la representación es admisible.

Entrada:
- HDF5 boundary con vista cruda y canónica.
- `attrs` de contrato.
- hashes y rutas de procedencia.

Salida:
- `contract_ok: bool`
- `failure_reason`
- `representation_fingerprint`
- `RUN_VALID`

Reglas mínimas:
- `x_grid` canónico debe ser `float64`, estrictamente positivo y de longitud 100.
- attrs de QNM obligatorios presentes.
- vista cruda preservada.

Artefactos:
- `runs/<run_id>/experiment/estimators_v1/input_contract_guard/manifest.json`
- `runs/<run_id>/experiment/estimators_v1/input_contract_guard/stage_summary.json`
- `runs/<run_id>/experiment/estimators_v1/input_contract_guard/outputs/contract_report.json`

### E10 `information_gate_v1`
Rol:
Estimar si el evento contiene información útil para ringdown o si es indistinguible de ruido.

Entrada recomendada:
- strain whitened o ventana ringdown real
- ASD/PSD
- metadatos de IFO, `fs`, duración
- features simples de soporte opcionales: SNR local, energía, coherencia H1/L1

Salida:
- `p_information`
- `decision` en `{INSUFFICIENT_INFO, WEAK_INFO, USABLE_INFO}`
- `uncertainty`
- `calibrated_score`

Modelo recomendado:
- `LogisticRegression`
- `HistGradientBoosting`
- capa de calibración explícita

Métricas mínimas:
- AUROC
- AUPRC
- Brier score
- ECE
- tasa de falsos positivos en nulls

Aceptación mínima:
- `ECE <= 0.05`
- FPR en nulls bajo umbral fijado
- estabilidad ante perturbaciones no semánticas

### E20 `baseline_features_v1`
Rol:
Baseline serio, reproducible y difícil de humillar.

Entrada:
- vector canónico de 20 features
- bloques:
  - `G2 [0:9]`
  - `thermal [9:13]`
  - `QNM [13:16]`
  - `response [16:18]`
  - `global [18:20]`

Salida:
- score o posterior simple según tarea
- importancia por bloque
- calibración
- sensibilidad a representación

Modelos recomendados:
- `LogisticRegression`
- `Ridge`
- `ElasticNet`
- `HistGradientBoosting`
- ensemble pequeño de los anteriores

Regla:
- E20 debe existir siempre.
- Ningún premium entra en producción si no mejora de forma clara y reproducible a E20.

### E30 `premium_posterior_estimator_v1`
Rol:
Estimador premium de verdad.

Posicionamiento:
- DINGO pertenece aquí, no en E20.

Entrada:
- strain o ventana ringdown whitened
- ASD/PSD
- metadatos instrumentales
- máscara temporal o ventana de análisis opcional

Salida:
- `posterior_samples`
- medias o medianas posteriores
- intervalos creíbles
- diagnósticos de cobertura
- log de configuración

Objetivo:
Estimar parámetros latentes de ringdown y solo después mapearlos a decisiones downstream.

Latentes candidatos:
- `f0`
- `tau0`
- amplitud efectiva
- razones de overtones
- nuisance instrumentales

Aceptación mínima:
- cobertura razonable
- estabilidad entre reruns
- no colapso en nulls
- mejora clara sobre E20
- sensibilidad controlada a cambios no semánticos

### E40 `calibration_layer_v1`
Rol:
Medir y corregir honestidad probabilística de E10 y E30.

Entrada:
- scores o posteriors sin calibrar
- golden set validado

Salida:
- modelo calibrado
- curvas de fiabilidad
- `ece.json`
- cobertura empírica

Métodos válidos:
- isotonic
- temperature scaling
- conformal si aplica

Regla:
- un score sin calibración no se interpreta.
- un posterior sin cobertura auditada no se interpreta.

### E50 `null_ood_guard_v1`
Rol:
Bloquear falsos positivos y detectar fuera de distribución.

Entrada:
- outputs de E10, E20 y E30
- null datasets
- perturbaciones contractualmente equivalentes
- negativos sintéticos

Salida:
- `null_pass: bool`
- `ood_score`
- `false_positive_report`

Métodos recomendados:
- Mahalanobis sobre embeddings
- energy distance
- conformal p-values
- batería de null runs

Regla:
- si el premium ve estructura sistemática en nulls, el veredicto científico queda bloqueado.

### E60 `ablation_audit_v1`
Rol:
Localizar causalmente qué bloque sostiene la decisión.

Entrada:
- estimador E20 o E30
- bloques `G2`, `thermal`, `QNM`, `response`, `global`

Salida:
- delta por bloque
- ranking de dependencia
- sensibilidad al quitar `G2`
- sensibilidad al quitar `QNM`

Regla:
- si no se sabe qué bloque manda, no se entiende el estimador.

## Orden de ejecución
1. `E00 input_contract_guard_v1`
2. `E10 information_gate_v1`
3. `E20 baseline_features_v1`
4. `E30 premium_posterior_estimator_v1`
5. `E40 calibration_layer_v1`
6. `E50 null_ood_guard_v1`
7. `E60 ablation_audit_v1`

## Reglas de bloqueo
- Si `E00` falla: no hay run.
- Si `E10` devuelve `INSUFFICIENT_INFO`: no se interpreta nada.
- Si `E40` falla calibración: no se interpreta nada.
- Si `E50` falla en nulls u OOD: no se interpreta nada.
- `E30` solo es elegible si mejora a `E20`.

## Artefactos esperados
```text
runs/<run_id>/experiment/estimators_v1/
  input_contract_guard/
    manifest.json
    stage_summary.json
    outputs/contract_report.json
  information_gate/
    manifest.json
    stage_summary.json
    outputs/p_information.json
  baseline_features/
    manifest.json
    stage_summary.json
    outputs/baseline_scores.json
    outputs/block_importance.json
  premium_posterior/
    manifest.json
    stage_summary.json
    outputs/posterior_samples.h5
    outputs/posterior_summary.json
  calibration/
    manifest.json
    stage_summary.json
    outputs/ece.json
    outputs/reliability.json
  null_ood_guard/
    manifest.json
    stage_summary.json
    outputs/null_report.json
    outputs/ood_report.json
  ablation_audit/
    manifest.json
    stage_summary.json
    outputs/ablation_report.json
```

## Criterio global de aceptación
- `E00` estable y sin ambigüedad contractual.
- `E10` calibrado.
- `E20` reproducible y competitivo.
- `E30` mejora claramente a `E20`.
- `E40` con cobertura razonable.
- `E50` sin falsos positivos inaceptables.
- `E60` mostrando qué bloque manda.
- Ninguna interpretación física antes de pasar todos los gates.

## Rutas exactas
- Documento: `/home/ignac/RINGEST/docs/estimators_v1.md`
- Registry declarativo: `/home/ignac/RINGEST/estimators_registry.json`
