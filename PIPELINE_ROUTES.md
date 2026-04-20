# RINGEST — Pipeline Routes

Este archivo define el orden operativo canónico.
Para comandos completos con flags consultar [instrucciones_pipeline.md](instrucciones_pipeline.md).

---

## Ruta A — Sandbox ADS/GKPW (checkpoint-only, 2026-04-20)

Geometría emergente sobre datos sintéticos. Única configuración con
`family_status = canonical_strong`. El generador sandbox
(`01_generate_sandbox_geometries.py`) fue eliminado el 2026-04-20; Ruta A
sigue operativa solo sobre el checkpoint ya entrenado
(`runs/ads_gkpw_20260416_091407/02_emergent_geometry_engine/emergent_geometry_model.pt`)
y sobre los H5 de bulk/boundary ya existentes en disco. No se puede
regenerar training data desde cero.

```text
runs/ads_gkpw_20260416_091407/01_generate_sandbox_geometries/   (congelado)
 └→ 02_emergent_geometry_engine.py      (--mode train | inference)
     └→ 03_discover_bulk_equations.py
         └→ 04_geometry_physics_contracts.py
             └→ 05_analyze_bulk_equations.py
                 └→ 06_build_bulk_eigenmodes_dataset.py
                     └→ 07_emergent_lambda_sl_dictionary.py
                         └→ 08_build_holographic_dictionary.py
                             └→ 09_real_data_and_dictionary_contracts.py
```

---

## Ruta B — Datos reales (literatura QNM)

Inferencia holográfica sobre ringdown real. El carril activo usa QNM
publicados (Bayesian posteriors de LVC / Isi / Giesler / Capano / pyRing),
no extracción ESPRIT propia.

```text
data/qnm_events_literature.yml
 └→ 02b_literature_to_dataset.py                (YAML → qnm_dataset.csv)
     └→ realdata_ringdown_to_stage02_boundary_dataset.py --dataset-csv …
         └→ 02_emergent_geometry_engine.py      (--mode inference, checkpoint de Ruta A)
             └→ 03_discover_bulk_equations.py
                 └→ 04_geometry_physics_contracts.py
```

Rama ESPRIT alternativa: eliminada el 2026-04-20. Scripts borrados:
`00_download_gwosc_events.py`, `00_load_ligo_data.py`,
`01_extract_ringdown_poles.py`, `run_batch_load.sh`. Ya no hay ingesta
NPZ→HDF5 propia ni extractor ESPRIT en el repo.

---

## Ruta C — ELIMINADA (2026-04-20)

El carril de extracción ESPRIT + PySR/KAN + validación Kerr fue cerrado:
la extracción propia no identificaba limpiamente el modo (2,2,0) del strain
real. Scripts borrados: `02_poles_to_dataset.py`, `03_discover_qnm_equations.py`,
`04_kan_qnm_classifier.py`, `05_validate_qnm_kerr.py`. El input canónico de
QNM ahora viene de literatura (ver Ruta B).

---

## Estado de familias

| `family_status` | Significado |
|---|---|
| `canonical_strong` | Ruta A con `--ads-boundary-mode gkpw` (checkpoint congelado) |
| `toy_sandbox` | Familia sintética/fenomenológica |
| `realdata_surrogate` | Embedding de ringdown real |
| `non_holographic_surrogate` | Carril Kerr (no holográfico) |

La clasificación vive en `family_registry.py`.

---

## Librerías compartidas

| Módulo | Usado por |
|---|---|
| `bulk_scalar_solver.py` | `06_build_bulk_eigenmodes_dataset.py` |
| `family_registry.py` | Rutas A, B |
| `feature_support.py` | Rutas A, B |
| `stage_utils.py` | Rutas A, B |

`tools/` contiene validadores de contrato compartidos; no se ejecuta como secuencia lineal.
