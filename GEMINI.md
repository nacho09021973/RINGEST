# RINGEST — Instrucciones de proyecto

## Objetivo

Transformar datos reales de ringdown GW en observables, relaciones empiricas o familias fisicas utiles.

Pregunta rectora:
"esto transforma datos reales en observables, relaciones o familias fisicas?"
Si no, no lo priorices.

## Prioridades

- Datos GW reales antes que sandbox.
- Polos QNM antes que marcos teoricos abstractos.
- YAML literatura QNM -> `qnm_dataset.csv` -> bridge -> inferencia geometrica antes que arquitectura nueva.
- Consistencia fisica antes que metricas de ajuste.
- Cambios minimos antes que redisenos.

## Carril preferente del repo

Ruta C (ESPRIT + PySR/KAN + validacion Kerr) fue ELIMINADA el 2026-04-20. No
reintroduzcas `02_poles_to_dataset.py`, `03_discover_qnm_equations.py`,
`04_kan_qnm_classifier.py` ni `05_validate_qnm_kerr.py`.

Prioriza esta cadena (Ruta B activa):

- `data/qnm_events_literature.yml`
- `02b_literature_to_dataset.py`
- `realdata_ringdown_to_stage02_boundary_dataset.py --dataset-csv ...`
- `02_emergent_geometry_engine.py --mode inference`
- `03_discover_bulk_equations.py` / `04_geometry_physics_contracts.py`

Ruta A queda en modo checkpoint-only desde 2026-04-20: el generador
sandbox `01_generate_sandbox_geometries.py` fue eliminado; sigue operativa
solo sobre el run congelado `runs/ads_gkpw_20260416_091407/`. La ingesta
NPZ + ESPRIT alternativa de Ruta B tambien fue eliminada
(`00_download_gwosc_events.py`, `00_load_ligo_data.py`,
`01_extract_ringdown_poles.py`, `run_batch_load.sh`). No los reintroduzcas.
No confundas:
- `canonical_strong`
- `realdata_surrogate`
- `toy_sandbox`
- `non_holographic_surrogate`

## Metodo

1. sintoma real
2. archivo o logica responsable
3. fisica real vs andamiaje
4. cambio minimo
5. test solo si toca

## Reglas

- Lee antes de proponer.
- Reutiliza antes de crear.
- No inventes rutas, flags, funciones ni resultados.
- No expandas el scope sin permiso.
- No priorices manifiestos, contratos o reorganizacion del repo si no mejoran un observable real.
- No propongas tests por defecto.
- No sobrevendas resultados con pocos eventos o clusters pequenos.

## Formato de analisis

- archivo:
- inputs reales:
- outputs reales:
- funcion fisica:
- dependencia toy/teorica:
- veredicto: RESCATAR / REESCRIBIR / ARCHIVAR

## Estilo

- Espanol.
- Directo.
- Tecnico.
- Sin humo.
