# Route B all18 — estreno de la tabla canónica
Run: `runs/routeB_all18_20260422`

## Entrada
- Cohorte real completa de 18 eventos de `community_ringdown_cohort`
- Tabla canónica congelada:
  - `runs/community_ringdown_cohort/community_ringdown_reference_table.csv`
- Bridge real:
  - `realdata_ringdown_to_stage02_boundary_dataset.py`

## Resultado Stage 02
- 18/18 sistemas inferidos correctamente
- Sin errores de contrato de features ni de routing

## Resultado Stage 03
- `n_geometries = 18`
- `n_with_equations = 18`
- `n_likely_einstein = 0`
- `n_possibly_einstein = 18`
- `average_einstein_score = 0.5`

Interpretación:
- Ninguna geometría cae en Einstein vacuum puro
- Toda la cohorte cae en el régimen `POSSIBLY_EINSTEIN_WITH_MATTER`

## Resultado Stage 04
- `n_total = 18`
- `n_generic_passed_strict = 18`
- `n_generic_passed_relaxed = 18`
- `n_overall_passed_strict = 18`
- `n_overall_passed_relaxed = 18`
- `n_real_failures = 0`
- `n_with_errors = 0`

Interpretación:
- Las 18 geometrías pasan contratos genéricos y globales
- No hay fallos reales de validación en la cohorte

## Conclusión técnica
La tabla canónica Ruta B funciona operativamente y escala a la cohorte completa de 18 eventos sin romper el pipeline.

Fenomenológicamente, la cohorte real completa reproduce de forma uniforme el veredicto:
- geometrías válidas bajo contratos del pipeline,
- pero no compatibles con Einstein vacuum puro.

Este resultado no demuestra física nueva ni refuta Kerr, pero sí establece una observación robusta:
la señal “no Einstein vacuum / effective matter-like geometry” sobrevive al paso desde sandbox y submuestras pequeñas a la cohorte real completa de 18 eventos.