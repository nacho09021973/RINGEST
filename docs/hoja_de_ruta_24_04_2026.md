# Hoja de ruta — 24/04/2026

## 1. Estado ejecutivo

Al cierre del trabajo del 23/04/2026, el carril Ruta B real-data queda operativo y trazado en tres cohortes: `all18`, `core7` y `community18`.
El run `runs/routeB_all18_20260422` existe con `02`, `03` y `04` reconstruidos en disco.
El run `runs/routeB_core7_20260423` existe con `02` y `03` reconstruidos en disco.
La cohorte comunitaria portable `runs/community_ringdown_cohort` queda conectada al bridge actual mediante `tools/community_reference_to_qnm_dataset.py`.
El Stage 03 crudo actual no reproduce `18/18 POSSIBLY_EINSTEIN_WITH_MATTER`.
El Stage 03 crudo actual tampoco reproduce `average_einstein_score = 0.5`.
El Stage 04 actual si reproduce `18/18` contratos pasados sin fallos reales en `all18` y `community18`.
La familia simbolica compacta reaparece parcialmente entre cohortes, pero la lectura A/B/outlier anterior queda como capa analitica derivada, no como salida bruta validada del Stage 03 actual.
El nucleo dominante `BASE_X3_PLUS_X2_X2X4` es estable en forma y tiene factor global aproximadamente `-8`.
El coeficiente de acoplo a `x4` muestra una rama principal `a ~ 0.73` y una subrama baja `a < 0.72` reproducida en `core7` y `all18`, pero no en `community18`.
La lectura fisica fuerte del nucleo queda abierta y por ahora debil.
La foto real del proyecto es: carril operativo reproducible, Stage 04 robusto, Stage 03 simbolicamente estructurado, pero sin validacion Einstein-like cruda reproducida.

## 2. Artefactos clave generados o verificados hoy

### `routeB_all18_20260422`

- `runs/routeB_all18_20260422/qnm_events_literature_all18.yml`
- `runs/routeB_all18_20260422/qnm_dataset_all18/qnm_dataset.csv`
- `runs/routeB_all18_20260422/qnm_dataset_all18/qnm_dataset_220.csv`
- `runs/routeB_all18_20260422/qnm_literature_boundary_all18/manifest.json`
- `runs/routeB_all18_20260422/qnm_literature_boundary_all18/*.h5`
- `runs/routeB_all18_20260422/02_emergent_geometry_engine/emergent_geometry_summary.json`
- `runs/routeB_all18_20260422/02_emergent_geometry_engine/geometry_emergent/*.h5`
- `runs/routeB_all18_20260422/03_discover_bulk_equations/outputs/einstein_discovery_summary.json`
- `runs/routeB_all18_20260422/03_discover_bulk_equations/outputs/*/einstein_discovery.json`
- `runs/routeB_all18_20260422/04_geometry_physics_contracts/outputs/geometry_contracts_summary.json`
- `runs/routeB_all18_20260422/04_geometry_physics_contracts/stage_summary.json`

### `routeB_core7_20260423`

- `runs/routeB_core7_20260423/qnm_events_literature_core7.yml`
- `runs/routeB_core7_20260423/qnm_dataset_core7/qnm_dataset.csv`
- `runs/routeB_core7_20260423/qnm_dataset_core7/qnm_dataset_220.csv`
- `runs/routeB_core7_20260423/qnm_literature_boundary_core7/manifest.json`
- `runs/routeB_core7_20260423/qnm_literature_boundary_core7/*.h5`
- `runs/routeB_core7_20260423/02_emergent_geometry_engine/emergent_geometry_summary.json`
- `runs/routeB_core7_20260423/02_emergent_geometry_engine/geometry_emergent/*.h5`
- `runs/routeB_core7_20260423/03_discover_bulk_equations/outputs/einstein_discovery_summary.json`
- `runs/routeB_core7_20260423/03_discover_bulk_equations/outputs/*/einstein_discovery.json`

### `community_ringdown_cohort`

- `runs/community_ringdown_cohort/community_ringdown_reference_table.csv`
- `tools/community_reference_to_qnm_dataset.py`
- `runs/community_ringdown_cohort/README_reference_table.md`
- `runs/community_ringdown_cohort/qnm_dataset_community_reference.csv`
- `runs/community_ringdown_cohort/qnm_reference_boundary_smoke/manifest.json`
- `runs/community_ringdown_cohort/qnm_reference_boundary_smoke/*.h5`
- `runs/community_ringdown_cohort/02_emergent_geometry_engine/emergent_geometry_summary.json`
- `runs/community_ringdown_cohort/02_emergent_geometry_engine/geometry_emergent/*.h5`
- `runs/community_ringdown_cohort/03_discover_bulk_equations/outputs/einstein_discovery_summary.json`
- `runs/community_ringdown_cohort/03_discover_bulk_equations/outputs/*/einstein_discovery.json`
- `runs/community_ringdown_cohort/04_geometry_physics_contracts/outputs/geometry_contracts_summary.json`
- `runs/community_ringdown_cohort/04_geometry_physics_contracts/stage_summary.json`

### Docs relevantes

- `docs/Route B all18.md`
- `docs/hoja_de_ruta_23_abril_2026.md`
- `docs/hoja_de_ruta_24_04_2026.md`

### Analysis relevantes

- `runs/routeB_all18_20260422/analysis/master_ansatz_formalization.md`
- `runs/routeB_all18_20260422/analysis/master_ansatz_validation.md`
- `runs/routeB_all18_20260422/analysis/master_ansatz_assignment.csv`
- `runs/routeB_all18_20260422/analysis/master_ansatz_audit.csv`
- `runs/routeB_all18_20260422/analysis/master_ansatz_universality.csv`
- `runs/routeB_all18_20260422/analysis/einstein_radial_candidate.md`
- `runs/routeB_all18_20260422/analysis/einstein_vs_schrodinger.md`
- `runs/routeB_all18_20260422/analysis/einstein_radial_best_combination.md`
- `runs/routeB_all18_20260422/analysis/einstein_radial_physical_interpretation.md`
- `runs/routeB_all18_20260422/analysis/stage03_symbolic_stability_across_cohorts.md`
- `runs/routeB_all18_20260422/analysis/stage03_core_physical_reading.md`
- `runs/routeB_all18_20260422/analysis/stage03_quality_vs_symbolic_classes.md`
- `runs/routeB_all18_20260422/analysis/stage03_core_coefficient_audit.md`
- `runs/routeB_all18_20260422/analysis/stage03_core_a_subbranches.md`
- `runs/routeB_all18_20260422/analysis/stage03_core_a_subbranch_reproducibility.md`

## 3. Mapa de rutas imprescindible

- `RUTA_CANONICA_ALL18_RUN = runs/routeB_all18_20260422`
- `RUTA_CANONICA_ALL18_YAML = runs/routeB_all18_20260422/qnm_events_literature_all18.yml`
- `RUTA_CANONICA_ALL18_QNM_DATASET = runs/routeB_all18_20260422/qnm_dataset_all18/qnm_dataset.csv`
- `RUTA_CANONICA_ALL18_BOUNDARY = runs/routeB_all18_20260422/qnm_literature_boundary_all18`
- `RUTA_CANONICA_ALL18_STAGE02 = runs/routeB_all18_20260422/02_emergent_geometry_engine`
- `RUTA_CANONICA_ALL18_STAGE03 = runs/routeB_all18_20260422/03_discover_bulk_equations`
- `RUTA_CANONICA_ALL18_STAGE04 = runs/routeB_all18_20260422/04_geometry_physics_contracts`
- `RUTA_CANONICA_ALL18_STAGE03_SUMMARY = runs/routeB_all18_20260422/03_discover_bulk_equations/outputs/einstein_discovery_summary.json`
- `RUTA_CANONICA_ALL18_STAGE04_SUMMARY = runs/routeB_all18_20260422/04_geometry_physics_contracts/outputs/geometry_contracts_summary.json`
- `RUTA_CANONICA_CORE7_RUN = runs/routeB_core7_20260423`
- `RUTA_CANONICA_CORE7_YAML = runs/routeB_core7_20260423/qnm_events_literature_core7.yml`
- `RUTA_CANONICA_CORE7_QNM_DATASET = runs/routeB_core7_20260423/qnm_dataset_core7/qnm_dataset.csv`
- `RUTA_CANONICA_CORE7_BOUNDARY = runs/routeB_core7_20260423/qnm_literature_boundary_core7`
- `RUTA_CANONICA_CORE7_STAGE02 = runs/routeB_core7_20260423/02_emergent_geometry_engine`
- `RUTA_CANONICA_CORE7_STAGE03 = runs/routeB_core7_20260423/03_discover_bulk_equations`
- `RUTA_CANONICA_CORE7_STAGE03_SUMMARY = runs/routeB_core7_20260423/03_discover_bulk_equations/outputs/einstein_discovery_summary.json`
- `RUTA_CANONICA_COMMUNITY_RUN = runs/community_ringdown_cohort`
- `RUTA_CANONICA_COMMUNITY_REFERENCE = runs/community_ringdown_cohort/community_ringdown_reference_table.csv`
- `RUTA_CANONICA_COMMUNITY_ADAPTER = tools/community_reference_to_qnm_dataset.py`
- `RUTA_CANONICA_COMMUNITY_QNM_DATASET = runs/community_ringdown_cohort/qnm_dataset_community_reference.csv`
- `RUTA_CANONICA_COMMUNITY_BOUNDARY = runs/community_ringdown_cohort/qnm_reference_boundary_smoke`
- `RUTA_CANONICA_COMMUNITY_STAGE02 = runs/community_ringdown_cohort/02_emergent_geometry_engine`
- `RUTA_CANONICA_COMMUNITY_STAGE03 = runs/community_ringdown_cohort/03_discover_bulk_equations`
- `RUTA_CANONICA_COMMUNITY_STAGE04 = runs/community_ringdown_cohort/04_geometry_physics_contracts`
- `RUTA_CANONICA_COMMUNITY_STAGE03_SUMMARY = runs/community_ringdown_cohort/03_discover_bulk_equations/outputs/einstein_discovery_summary.json`
- `RUTA_CANONICA_COMMUNITY_STAGE04_SUMMARY = runs/community_ringdown_cohort/04_geometry_physics_contracts/outputs/geometry_contracts_summary.json`
- `RUTA_DOC_ANTIGUA_ALL18 = docs/Route B all18.md`
- `RUTA_DOC_HOJA_23 = docs/hoja_de_ruta_23_abril_2026.md`
- `RUTA_DOC_HOJA_24 = docs/hoja_de_ruta_24_04_2026.md`
- `RUTA_ANALISIS_ESTABILIDAD = runs/routeB_all18_20260422/analysis/stage03_symbolic_stability_across_cohorts.md`
- `RUTA_ANALISIS_LECTURA_FISICA = runs/routeB_all18_20260422/analysis/stage03_core_physical_reading.md`
- `RUTA_ANALISIS_CALIDAD = runs/routeB_all18_20260422/analysis/stage03_quality_vs_symbolic_classes.md`
- `RUTA_ANALISIS_COEFICIENTES = runs/routeB_all18_20260422/analysis/stage03_core_coefficient_audit.md`
- `RUTA_ANALISIS_SUBRAMAS = runs/routeB_all18_20260422/analysis/stage03_core_a_subbranches.md`
- `RUTA_ANALISIS_REPRO_SUBRAMA = runs/routeB_all18_20260422/analysis/stage03_core_a_subbranch_reproducibility.md`

Rutas leidas hoy:

- `runs/routeB_all18_20260422/03_discover_bulk_equations/outputs/*/einstein_discovery.json`
- `runs/routeB_core7_20260423/03_discover_bulk_equations/outputs/*/einstein_discovery.json`
- `runs/community_ringdown_cohort/03_discover_bulk_equations/outputs/*/einstein_discovery.json`
- `runs/community_ringdown_cohort/community_ringdown_reference_table.csv`
- `runs/routeB_all18_20260422/analysis/*.md`
- `runs/routeB_all18_20260422/analysis/*.csv`
- `docs/Route B all18.md`
- `docs/hoja_de_ruta_23_abril_2026.md`

Rutas creadas hoy o dejadas como nuevos artefactos de trabajo:

- `tools/community_reference_to_qnm_dataset.py`
- `runs/community_ringdown_cohort/qnm_dataset_community_reference.csv`
- `runs/community_ringdown_cohort/qnm_reference_boundary_smoke/manifest.json`
- `runs/routeB_all18_20260422/analysis/stage03_symbolic_stability_across_cohorts.md`
- `runs/routeB_all18_20260422/analysis/stage03_core_physical_reading.md`
- `runs/routeB_all18_20260422/analysis/stage03_quality_vs_symbolic_classes.md`
- `runs/routeB_all18_20260422/analysis/stage03_core_coefficient_audit.md`
- `runs/routeB_all18_20260422/analysis/stage03_core_a_subbranches.md`
- `runs/routeB_all18_20260422/analysis/stage03_core_a_subbranch_reproducibility.md`
- `docs/hoja_de_ruta_24_04_2026.md`

Rutas que existen pero NO deben confundirse:

- `docs/Route B all18.md`: documento previo que afirma `n_possibly_einstein = 18` y `average_einstein_score = 0.5`; no coincide con el Stage 03 crudo actual.
- `runs/routeB_all18_20260422/analysis/master_ansatz_*.csv`: capa analitica derivada A/B/outlier; no es salida cruda actual del Stage 03.
- `runs/routeB_all18_20260422/analysis/einstein_radial_*.md`: interpretacion posterior; no es veredicto crudo actual.
- `runs/community_ringdown_cohort/community_ringdown_reference_table.csv`: tabla portable congelada; no implica que el pipeline original de `ringdown_fit` deba reejecutarse.
- `runs/community_ringdown_cohort/qnm_reference_boundary_smoke`: boundary generado desde la tabla comunitaria; no es `data/gwosc_events/qnm_literature_boundary/`.
- `data/gwosc_events/qnm_literature_boundary/`: no usar como all18 canonico; se verifico previamente que no era la cohorte documental all18.

Rutas canonicas para reanudar mañana:

- Para all18: `runs/routeB_all18_20260422/03_discover_bulk_equations/outputs/einstein_discovery_summary.json`
- Para core7: `runs/routeB_core7_20260423/03_discover_bulk_equations/outputs/einstein_discovery_summary.json`
- Para community18: `runs/community_ringdown_cohort/03_discover_bulk_equations/outputs/einstein_discovery_summary.json`
- Para contratos: `runs/routeB_all18_20260422/04_geometry_physics_contracts/outputs/geometry_contracts_summary.json` y `runs/community_ringdown_cohort/04_geometry_physics_contracts/outputs/geometry_contracts_summary.json`
- Para lectura simbolica: `runs/routeB_all18_20260422/analysis/stage03_symbolic_stability_across_cohorts.md`
- Para coeficientes: `runs/routeB_all18_20260422/analysis/stage03_core_coefficient_audit.md`
- Para subrama baja: `runs/routeB_all18_20260422/analysis/stage03_core_a_subbranch_reproducibility.md`

## 4. Qué se reprodujo hoy realmente

### 4.1 all18

Hechos verificados:

- Boundary all18 existe en `runs/routeB_all18_20260422/qnm_literature_boundary_all18`.
- El manifest del boundary all18 existe en `runs/routeB_all18_20260422/qnm_literature_boundary_all18/manifest.json`.
- Stage 02 all18 existe en `runs/routeB_all18_20260422/02_emergent_geometry_engine`.
- `runs/routeB_all18_20260422/02_emergent_geometry_engine/emergent_geometry_summary.json` contiene `n_systems = 18`.
- Stage 03 all18 existe en `runs/routeB_all18_20260422/03_discover_bulk_equations`.
- `runs/routeB_all18_20260422/03_discover_bulk_equations/outputs/einstein_discovery_summary.json` contiene:
  - `n_geometries = 18`
  - `n_with_equations = 18`
  - `n_likely_einstein = 0`
  - `n_possibly_einstein = 0`
  - `n_non_einstein = 18`
  - `average_einstein_score = 0.005555555555555556`
  - `pysr_available = true`
- Stage 04 all18 existe en `runs/routeB_all18_20260422/04_geometry_physics_contracts`.
- `runs/routeB_all18_20260422/04_geometry_physics_contracts/outputs/geometry_contracts_summary.json` contiene:
  - `n_total = 18`
  - `n_generic_passed_strict = 18`
  - `n_generic_passed_relaxed = 18`
  - `n_overall_passed_strict = 18`
  - `n_overall_passed_relaxed = 18`
  - `n_real_failures = 0`
  - `n_with_errors = 0`
  - `n_inference_mode = 18`
  - `avg_score = 0.8000000000000002`

### 4.2 core7

Hechos verificados:

- YAML core7 existe en `runs/routeB_core7_20260423/qnm_events_literature_core7.yml`.
- CSV core7 existe en `runs/routeB_core7_20260423/qnm_dataset_core7/qnm_dataset.csv`.
- Boundary core7 existe en `runs/routeB_core7_20260423/qnm_literature_boundary_core7`.
- El manifest core7 existe en `runs/routeB_core7_20260423/qnm_literature_boundary_core7/manifest.json`.
- Stage 02 core7 existe en `runs/routeB_core7_20260423/02_emergent_geometry_engine`.
- `runs/routeB_core7_20260423/02_emergent_geometry_engine/emergent_geometry_summary.json` contiene `n_systems = 7`.
- Stage 03 core7 existe en `runs/routeB_core7_20260423/03_discover_bulk_equations`.
- `runs/routeB_core7_20260423/03_discover_bulk_equations/outputs/einstein_discovery_summary.json` contiene:
  - `n_geometries = 7`
  - `n_with_equations = 7`
  - `n_likely_einstein = 0`
  - `n_possibly_einstein = 0`
  - `n_non_einstein = 7`
  - `average_einstein_score = 0.014285714285714287`
  - `pysr_available = true`
- No se usa aqui ningun Stage 04 core7 como hecho reproducido.

### 4.3 community18

Hechos verificados:

- Tabla comunitaria portable existe en `runs/community_ringdown_cohort/community_ringdown_reference_table.csv`.
- Adaptador minimo existe en `tools/community_reference_to_qnm_dataset.py`.
- CSV adaptado existe en `runs/community_ringdown_cohort/qnm_dataset_community_reference.csv`.
- Boundary generado desde tabla comunitaria existe en `runs/community_ringdown_cohort/qnm_reference_boundary_smoke`.
- Manifest del boundary comunitario existe en `runs/community_ringdown_cohort/qnm_reference_boundary_smoke/manifest.json`.
- Stage 02 community18 existe en `runs/community_ringdown_cohort/02_emergent_geometry_engine`.
- `runs/community_ringdown_cohort/02_emergent_geometry_engine/emergent_geometry_summary.json` contiene `n_systems = 18`.
- Stage 03 community18 existe en `runs/community_ringdown_cohort/03_discover_bulk_equations`.
- `runs/community_ringdown_cohort/03_discover_bulk_equations/outputs/einstein_discovery_summary.json` contiene:
  - `n_geometries = 18`
  - `n_with_equations = 18`
  - `n_likely_einstein = 0`
  - `n_possibly_einstein = 0`
  - `n_non_einstein = 18`
  - `average_einstein_score = 0.0`
  - `pysr_available = true`
- Stage 04 community18 existe en `runs/community_ringdown_cohort/04_geometry_physics_contracts`.
- `runs/community_ringdown_cohort/04_geometry_physics_contracts/outputs/geometry_contracts_summary.json` contiene:
  - `n_total = 18`
  - `n_generic_passed_strict = 18`
  - `n_generic_passed_relaxed = 18`
  - `n_overall_passed_strict = 18`
  - `n_overall_passed_relaxed = 18`
  - `n_real_failures = 0`
  - `n_with_errors = 0`
  - `n_inference_mode = 18`
  - `avg_score = 0.8000000000000002`

## 5. Qué NO se reprodujo

- No se reprodujo que Stage 03 clasifique `18/18` como `POSSIBLY_EINSTEIN_WITH_MATTER`.
- No se reprodujo `average_einstein_score = 0.5`.
- En `all18`, el Stage 03 actual da `n_possibly_einstein = 0` y `average_einstein_score = 0.005555555555555556` en `runs/routeB_all18_20260422/03_discover_bulk_equations/outputs/einstein_discovery_summary.json`.
- En `community18`, el Stage 03 actual da `n_possibly_einstein = 0` y `average_einstein_score = 0.0` en `runs/community_ringdown_cohort/03_discover_bulk_equations/outputs/einstein_discovery_summary.json`.
- En `core7`, el Stage 03 actual da `n_possibly_einstein = 0` y `average_einstein_score = 0.014285714285714287` en `runs/routeB_core7_20260423/03_discover_bulk_equations/outputs/einstein_discovery_summary.json`.
- La lectura documental vieja de `docs/Route B all18.md` no coincide con el crudo actual de Stage 03.
- El outlier fuerte `GW190503_185404` no queda validado hoy como outlier universal.
- En `core7` y `all18`, `GW190503_185404` cae en la clase dominante `BASE_X3_PLUS_X2_X2X4` segun `runs/routeB_all18_20260422/analysis/stage03_symbolic_stability_across_cohorts.md`.
- En `community18`, `GW190503_185404` no reproduce la subrama baja dentro del nucleo dominante segun `runs/routeB_all18_20260422/analysis/stage03_core_a_subbranch_reproducibility.md`.

## 6. Capa cruda vs capa analítica vs capa documental

### CAPA_CRUDA_PIPELINE

Rutas exactas:

- `runs/routeB_all18_20260422/02_emergent_geometry_engine/emergent_geometry_summary.json`
- `runs/routeB_all18_20260422/03_discover_bulk_equations/outputs/einstein_discovery_summary.json`
- `runs/routeB_all18_20260422/04_geometry_physics_contracts/outputs/geometry_contracts_summary.json`
- `runs/routeB_core7_20260423/02_emergent_geometry_engine/emergent_geometry_summary.json`
- `runs/routeB_core7_20260423/03_discover_bulk_equations/outputs/einstein_discovery_summary.json`
- `runs/community_ringdown_cohort/02_emergent_geometry_engine/emergent_geometry_summary.json`
- `runs/community_ringdown_cohort/03_discover_bulk_equations/outputs/einstein_discovery_summary.json`
- `runs/community_ringdown_cohort/04_geometry_physics_contracts/outputs/geometry_contracts_summary.json`

Qué dice hoy:

- `02` produce 18 sistemas en `all18`, 7 en `core7` y 18 en `community18`.
- `03` produce ecuaciones para todos los sistemas inspeccionados, pero clasifica todos como `NON_EINSTEIN_OR_DEFORMED`.
- `04` pasa 18/18 en `all18` y 18/18 en `community18`.

### CAPA_ANALISIS_DERIVADO

Rutas exactas:

- `runs/routeB_all18_20260422/analysis/master_ansatz_formalization.md`
- `runs/routeB_all18_20260422/analysis/master_ansatz_validation.md`
- `runs/routeB_all18_20260422/analysis/master_ansatz_assignment.csv`
- `runs/routeB_all18_20260422/analysis/master_ansatz_audit.csv`
- `runs/routeB_all18_20260422/analysis/master_ansatz_universality.csv`
- `runs/routeB_all18_20260422/analysis/einstein_radial_candidate.md`
- `runs/routeB_all18_20260422/analysis/einstein_vs_schrodinger.md`
- `runs/routeB_all18_20260422/analysis/einstein_radial_best_combination.md`
- `runs/routeB_all18_20260422/analysis/einstein_radial_physical_interpretation.md`
- `runs/routeB_all18_20260422/analysis/stage03_symbolic_stability_across_cohorts.md`
- `runs/routeB_all18_20260422/analysis/stage03_core_physical_reading.md`
- `runs/routeB_all18_20260422/analysis/stage03_quality_vs_symbolic_classes.md`
- `runs/routeB_all18_20260422/analysis/stage03_core_coefficient_audit.md`
- `runs/routeB_all18_20260422/analysis/stage03_core_a_subbranches.md`
- `runs/routeB_all18_20260422/analysis/stage03_core_a_subbranch_reproducibility.md`

Qué contiene:

- Una capa previa A/B/outlier y Einstein-radial.
- Una capa nueva de auditoria Stage 03 crudo actual: estabilidad simbolica entre cohortes, lectura fisica minima, control por calidad/procedencia, coeficientes del nucleo y subramas del coeficiente `a`.

Estatus hoy:

- La capa A/B/outlier y Einstein-radial existe en disco, pero queda como interpretacion derivada no validada por el Stage 03 crudo actual.
- La capa nueva de estabilidad simbolica si esta anclada a JSON crudos actuales.
- Inferencia: el resultado util hoy es fenomenologico/simbolico, no Einstein-like.

### CAPA_DOCUMENTAL

Rutas exactas:

- `docs/Route B all18.md`
- `docs/hoja_de_ruta_23_abril_2026.md`
- `docs/hoja_de_ruta_24_04_2026.md`

Qué afirmaba:

- `docs/Route B all18.md` afirmaba `n_possibly_einstein = 18`, `average_einstein_score = 0.5` y `POSSIBLY_EINSTEIN_WITH_MATTER`.
- `docs/Route B all18.md` tambien afirmaba Stage 04 18/18 contratos pasados.
- `docs/hoja_de_ruta_23_abril_2026.md` fue corregida para separar capa analitica de Stage 03 crudo.

Qué parte sigue viva:

- Sigue viva la validacion contractual downstream `04` 18/18.
- Sigue viva la existencia de estructura simbolica compacta en Stage 03.
- Sigue viva como documento la capa A/B/outlier, pero no como salida cruda reproducida.

Qué parte no sigue viva como hecho reproducido:

- `18/18 POSSIBLY_EINSTEIN_WITH_MATTER`.
- `average_einstein_score = 0.5`.
- `GW190503_185404` como outlier universal.

## 7. Hallazgos firmes del día

- Stage 02 all18 reconstruido: `runs/routeB_all18_20260422/02_emergent_geometry_engine/emergent_geometry_summary.json` contiene `n_systems = 18`.
- Stage 03 all18 reconstruido: `runs/routeB_all18_20260422/03_discover_bulk_equations/outputs/einstein_discovery_summary.json` contiene `n_geometries = 18` y `n_with_equations = 18`.
- Stage 03 actual no respalda `POSSIBLY_EINSTEIN_WITH_MATTER`.
- Stage 04 all18 es robusto: `runs/routeB_all18_20260422/04_geometry_physics_contracts/outputs/geometry_contracts_summary.json` contiene `n_overall_passed_strict = 18` y `n_real_failures = 0`.
- Stage 04 community18 es robusto: `runs/community_ringdown_cohort/04_geometry_physics_contracts/outputs/geometry_contracts_summary.json` contiene `n_overall_passed_strict = 18` y `n_real_failures = 0`.
- La tabla comunitaria portable se conecto operativamente al bridge mediante `tools/community_reference_to_qnm_dataset.py`.
- El output adaptado existe en `runs/community_ringdown_cohort/qnm_dataset_community_reference.csv`.
- El boundary derivado de la tabla comunitaria existe en `runs/community_ringdown_cohort/qnm_reference_boundary_smoke`.
- La familia simbolica compacta reaparece parcialmente entre `core7`, `all18` y `community18`, documentado en `runs/routeB_all18_20260422/analysis/stage03_symbolic_stability_across_cohorts.md`.
- El nucleo dominante `BASE_X3_PLUS_X2_X2X4` reaparece entre cohortes.
- El factor global del nucleo dominante es muy estable, aproximadamente `-8`, documentado en `runs/routeB_all18_20260422/analysis/stage03_core_coefficient_audit.md`.
- La subrama baja `a < 0.72` aparece en `core7` y `all18` con `GW170104` y `GW190503_185404`.
- La subrama baja `a < 0.72` no aparece en `community18`.

## 8. Hallazgos debilitados o caídos

- La hipotesis `18/18 POSSIBLY_EINSTEIN_WITH_MATTER` perdio apoyo como hecho reproducible.
- `average_einstein_score = 0.5` no quedo reproducido.
- La lectura documental vieja de Stage 03 en `docs/Route B all18.md` queda contradicha por los JSON actuales de `03`.
- El outlier universal `GW190503_185404` perdio apoyo: en `core7` y `all18` cae dentro del nucleo dominante, no fuera de familia.
- La lectura fisica fuerte del nucleo queda debil: `runs/routeB_all18_20260422/analysis/stage03_core_physical_reading.md` concluye `LECTURA_FISICA_DEL_NUCLEO: debil`.
- La separacion por masa/spin/tier/source_kind queda dudosa, no firme.
- La lectura Einstein-radial queda como capa interpretativa previa, no como conclusion cruda actual.

## 9. Estado actual de la hoja de ruta

El Eje 1 avanzo: se separo robustez simbolica de contaminacion por calidad/procedencia usando `core7`, `all18` y `community18`.
El Eje 2 avanzo parcialmente: se intento leer fisicamente el nucleo dominante, pero la lectura quedo debil.
La comparacion por coeficientes avanzo: el nucleo tiene factor global estable `~ -8` y una subestructura en `a`.
La busqueda de outlier fuerte baja de prioridad: `GW190503_185404` no es outlier universal bajo los JSON crudos actuales.
La lectura Einstein-like baja de prioridad hasta que exista una reproduccion cruda que la sostenga.
La pregunta rectora viva es: si la regularidad simbolica compacta del Stage 03 es una regularidad interna estable del surrogate real-data o si puede anclarse a observables fisicos de ringdown/remanente.

## 10. Próximos pasos recomendados

1. Objetivo: auditar estabilidad del coeficiente `a` frente a procedencia comunitaria.
   Input exacto: `runs/community_ringdown_cohort/03_discover_bulk_equations/outputs/*/einstein_discovery.json`.
   Rutas exactas: comparar contra `runs/routeB_all18_20260422/analysis/stage03_core_a_subbranch_reproducibility.md`.
   Sentido: la subrama baja desaparece en `community18`; hay que saber si eso depende de inputs o de que los eventos dejan de caer en el nucleo dominante.

2. Objetivo: revisar solo eventos comunes que cambian de clase entre `all18` y `community18`.
   Input exacto: `runs/routeB_all18_20260422/03_discover_bulk_equations/outputs/*/einstein_discovery.json` y `runs/community_ringdown_cohort/03_discover_bulk_equations/outputs/*/einstein_discovery.json`.
   Rutas exactas: usar `runs/routeB_all18_20260422/analysis/stage03_symbolic_stability_across_cohorts.md`.
   Sentido: separar sensibilidad a inputs de senal fisica.

3. Objetivo: documentar una tabla compacta evento-a-evento de clase all18 vs community18.
   Input exacto: los dos summaries Stage 03 y JSON por evento.
   Rutas exactas: `runs/routeB_all18_20260422/03_discover_bulk_equations/outputs` y `runs/community_ringdown_cohort/03_discover_bulk_equations/outputs`.
   Sentido: dejar listo el analisis de sensibilidad sin reejecutar nada.

4. Objetivo: revisar si las clases deformadas tienen peor soporte operacional.
   Input exacto: `runs/community_ringdown_cohort/community_ringdown_reference_table.csv` y `runs/routeB_all18_20260422/analysis/stage03_quality_vs_symbolic_classes.md`.
   Rutas exactas: no crear pipeline nuevo; solo analysis si hace falta.
   Sentido: atacar la posible mezcla entre fisica y calidad/procedencia.

5. Objetivo: actualizar la documentacion vieja para marcarla como historica.
   Input exacto: `docs/Route B all18.md` y `docs/hoja_de_ruta_23_abril_2026.md`.
   Rutas exactas: crear nota o encabezado, sin borrar contenido.
   Sentido: evitar que mañana se vuelva a tomar `POSSIBLY_EINSTEIN_WITH_MATTER` como reproducido.

## 11. Comandos mínimos para reanudar mañana

Inspeccionar all18:

```bash
cd /home/ignac/RINGEST
python3 - <<'PY'
import json
from pathlib import Path
p = Path("runs/routeB_all18_20260422/03_discover_bulk_equations/outputs/einstein_discovery_summary.json")
print(json.dumps(json.loads(p.read_text())["summary"], indent=2))
PY
```

Inspeccionar Stage 04 all18:

```bash
cd /home/ignac/RINGEST
python3 - <<'PY'
import json
from pathlib import Path
p = Path("runs/routeB_all18_20260422/04_geometry_physics_contracts/outputs/geometry_contracts_summary.json")
data = json.loads(p.read_text())
print(json.dumps({k: data[k] for k in ["n_total","n_generic_passed_strict","n_overall_passed_strict","n_real_failures","n_with_errors","avg_score"]}, indent=2))
PY
```

Inspeccionar core7:

```bash
cd /home/ignac/RINGEST
python3 - <<'PY'
import json
from pathlib import Path
p = Path("runs/routeB_core7_20260423/03_discover_bulk_equations/outputs/einstein_discovery_summary.json")
print(json.dumps(json.loads(p.read_text())["summary"], indent=2))
PY
```

Inspeccionar community18:

```bash
cd /home/ignac/RINGEST
python3 - <<'PY'
import json
from pathlib import Path
p = Path("runs/community_ringdown_cohort/03_discover_bulk_equations/outputs/einstein_discovery_summary.json")
print(json.dumps(json.loads(p.read_text())["summary"], indent=2))
PY
```

Inspeccionar contratos community18:

```bash
cd /home/ignac/RINGEST
python3 - <<'PY'
import json
from pathlib import Path
p = Path("runs/community_ringdown_cohort/04_geometry_physics_contracts/outputs/geometry_contracts_summary.json")
data = json.loads(p.read_text())
print(json.dumps({k: data[k] for k in ["n_total","n_generic_passed_strict","n_overall_passed_strict","n_real_failures","n_with_errors","avg_score"]}, indent=2))
PY
```

Releer analisis clave:

```bash
cd /home/ignac/RINGEST
sed -n '1,220p' runs/routeB_all18_20260422/analysis/stage03_symbolic_stability_across_cohorts.md
sed -n '1,220p' runs/routeB_all18_20260422/analysis/stage03_core_coefficient_audit.md
sed -n '1,220p' runs/routeB_all18_20260422/analysis/stage03_core_a_subbranch_reproducibility.md
```

Localizar todas las rutas canonicas actuales:

```bash
cd /home/ignac/RINGEST
find runs/routeB_all18_20260422 runs/routeB_core7_20260423 runs/community_ringdown_cohort -maxdepth 3 -type f | sort
```

## 12. Riesgos de confusión para mañana

- Confundir `all18` con `core7`: `all18` tiene 18 eventos; `core7` tiene 7.
- Confundir `community18` con el pipeline original de `ringdown_fit`: la tabla `runs/community_ringdown_cohort/community_ringdown_reference_table.csv` es entrada portable congelada; no exige reejecutar `ringdown_fit`.
- Confundir capa analitica A/B/outlier con Stage 03 crudo actual.
- Volver a perseguir `POSSIBLY_EINSTEIN_WITH_MATTER` como si estuviera reproducido.
- Tomar `docs/Route B all18.md` como verdad cruda actual: contiene afirmaciones viejas no reproducidas por Stage 03 actual.
- Usar `data/gwosc_events/qnm_literature_boundary/` como boundary all18: no es la ruta canonica all18 reconstruida.
- Interpretar `family_pred = ads` de Stage 02 como dualidad fuerte: los summaries Stage 02 incluyen notas de `realdata_surrogate` y compatibilidad, no pertenencia fisica fuerte.
- Llamar regimen fisico a la subrama baja `a < 0.72`: se reproduce en `core7` y `all18`, pero no en `community18`.
- Tratar `GW190503_185404` como outlier universal: hoy no queda validado asi.
- Olvidar que muchos analysis en `runs/` estan ignorados por git aunque existen en disco.

## 13. Frase final de estatus

Ruta B queda operativamente reconstruida y simbolicamente estructurada, pero la lectura Einstein-like/documental vieja no esta reproducida y la interpretacion fisica del nucleo sigue abierta.

## 14. Índice de rutas exactas

- `docs/Route B all18.md`
- `docs/hoja_de_ruta_23_abril_2026.md`
- `docs/hoja_de_ruta_24_04_2026.md`
- `tools/community_reference_to_qnm_dataset.py`
- `runs/routeB_all18_20260422`
- `runs/routeB_all18_20260422/qnm_events_literature_all18.yml`
- `runs/routeB_all18_20260422/qnm_dataset_all18/qnm_dataset.csv`
- `runs/routeB_all18_20260422/qnm_dataset_all18/qnm_dataset_220.csv`
- `runs/routeB_all18_20260422/qnm_literature_boundary_all18`
- `runs/routeB_all18_20260422/qnm_literature_boundary_all18/manifest.json`
- `runs/routeB_all18_20260422/02_emergent_geometry_engine`
- `runs/routeB_all18_20260422/02_emergent_geometry_engine/emergent_geometry_summary.json`
- `runs/routeB_all18_20260422/02_emergent_geometry_engine/geometry_emergent`
- `runs/routeB_all18_20260422/03_discover_bulk_equations`
- `runs/routeB_all18_20260422/03_discover_bulk_equations/outputs/einstein_discovery_summary.json`
- `runs/routeB_all18_20260422/03_discover_bulk_equations/outputs/*/einstein_discovery.json`
- `runs/routeB_all18_20260422/04_geometry_physics_contracts`
- `runs/routeB_all18_20260422/04_geometry_physics_contracts/outputs/geometry_contracts_summary.json`
- `runs/routeB_all18_20260422/04_geometry_physics_contracts/stage_summary.json`
- `runs/routeB_all18_20260422/analysis/master_ansatz_formalization.md`
- `runs/routeB_all18_20260422/analysis/master_ansatz_validation.md`
- `runs/routeB_all18_20260422/analysis/master_ansatz_assignment.csv`
- `runs/routeB_all18_20260422/analysis/master_ansatz_audit.csv`
- `runs/routeB_all18_20260422/analysis/master_ansatz_universality.csv`
- `runs/routeB_all18_20260422/analysis/einstein_radial_candidate.md`
- `runs/routeB_all18_20260422/analysis/einstein_vs_schrodinger.md`
- `runs/routeB_all18_20260422/analysis/einstein_radial_best_combination.md`
- `runs/routeB_all18_20260422/analysis/einstein_radial_physical_interpretation.md`
- `runs/routeB_all18_20260422/analysis/stage03_symbolic_stability_across_cohorts.md`
- `runs/routeB_all18_20260422/analysis/stage03_core_physical_reading.md`
- `runs/routeB_all18_20260422/analysis/stage03_quality_vs_symbolic_classes.md`
- `runs/routeB_all18_20260422/analysis/stage03_core_coefficient_audit.md`
- `runs/routeB_all18_20260422/analysis/stage03_core_a_subbranches.md`
- `runs/routeB_all18_20260422/analysis/stage03_core_a_subbranch_reproducibility.md`
- `runs/routeB_core7_20260423`
- `runs/routeB_core7_20260423/qnm_events_literature_core7.yml`
- `runs/routeB_core7_20260423/qnm_dataset_core7/qnm_dataset.csv`
- `runs/routeB_core7_20260423/qnm_dataset_core7/qnm_dataset_220.csv`
- `runs/routeB_core7_20260423/qnm_literature_boundary_core7`
- `runs/routeB_core7_20260423/qnm_literature_boundary_core7/manifest.json`
- `runs/routeB_core7_20260423/02_emergent_geometry_engine`
- `runs/routeB_core7_20260423/02_emergent_geometry_engine/emergent_geometry_summary.json`
- `runs/routeB_core7_20260423/02_emergent_geometry_engine/geometry_emergent`
- `runs/routeB_core7_20260423/03_discover_bulk_equations`
- `runs/routeB_core7_20260423/03_discover_bulk_equations/outputs/einstein_discovery_summary.json`
- `runs/routeB_core7_20260423/03_discover_bulk_equations/outputs/*/einstein_discovery.json`
- `runs/community_ringdown_cohort`
- `runs/community_ringdown_cohort/community_ringdown_reference_table.csv`
- `runs/community_ringdown_cohort/community_ringdown_tiers.csv`
- `runs/community_ringdown_cohort/community_ringdown_tiers.json`
- `runs/community_ringdown_cohort/README_reference_table.md`
- `runs/community_ringdown_cohort/qnm_dataset_community_reference.csv`
- `runs/community_ringdown_cohort/qnm_reference_boundary_smoke`
- `runs/community_ringdown_cohort/qnm_reference_boundary_smoke/manifest.json`
- `runs/community_ringdown_cohort/02_emergent_geometry_engine`
- `runs/community_ringdown_cohort/02_emergent_geometry_engine/emergent_geometry_summary.json`
- `runs/community_ringdown_cohort/02_emergent_geometry_engine/geometry_emergent`
- `runs/community_ringdown_cohort/03_discover_bulk_equations`
- `runs/community_ringdown_cohort/03_discover_bulk_equations/outputs/einstein_discovery_summary.json`
- `runs/community_ringdown_cohort/03_discover_bulk_equations/outputs/*/einstein_discovery.json`
- `runs/community_ringdown_cohort/04_geometry_physics_contracts`
- `runs/community_ringdown_cohort/04_geometry_physics_contracts/outputs/geometry_contracts_summary.json`
- `runs/community_ringdown_cohort/04_geometry_physics_contracts/stage_summary.json`
