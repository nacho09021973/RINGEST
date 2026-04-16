# RINGEST — Pipeline Routes

Este archivo define el orden operativo canónico.
Para comandos completos con flags consultar [instrucciones_pipeline.md](instrucciones_pipeline.md).

---

## Ruta A — Sandbox ADS/GKPW

Geometría emergente sobre datos sintéticos. Única ruta con `family_status = canonical_strong`.

```text
01_generate_sandbox_geometries.py   (--ads-boundary-mode gkpw)
 └→ 02_emergent_geometry_engine.py  (--mode train)
     └→ 03_discover_bulk_equations.py
         └→ 04_geometry_physics_contracts.py
             └→ 05_analyze_bulk_equations.py
                 └→ 06_build_bulk_eigenmodes_dataset.py
                     └→ 07_emergent_lambda_sl_dictionary.py
                         └→ 08_build_holographic_dictionary.py
                             └→ 09_real_data_and_dictionary_contracts.py
```

---

## Ruta B — Datos reales GWOSC

Inferencia holográfica sobre ringdown real.

```text
00_download_gwosc_events.py
 └→ 00_load_ligo_data.py            (NPZ → boundary HDF5)
     └→ 01_extract_ringdown_poles.py (ESPRIT, poles_joint.json)
         └→ realdata_ringdown_to_stage02_boundary_dataset.py
             └→ 02_emergent_geometry_engine.py  (--mode inference, checkpoint de Ruta A)
```

---

## Ruta C — Cadena QNM

Descubrimiento simbólico + KAN + validación Kerr sobre polos de ringdown.
Prerequisito: completar B-1 a B-3 para todos los eventos deseados.

```text
02_poles_to_dataset.py              (rings → qnm_dataset.csv)
 └→ 03_discover_qnm_equations.py    (PySR / --analysis-only; escribe kan_contract)
     └→ 04_kan_qnm_classifier.py    (k-means + KAN; escribe downstream_contract)
         └→ 05_validate_qnm_kerr.py (Berti 2009, l=m=2 n=0,1,2)
             └─> (injects into 08_build_holographic_dictionary.py)

`05_validate_qnm_kerr.py` ahora escribe `cluster_audit.csv` y `cluster_audit_summary.json`
para auditar la composición física de cada clúster.
```

---

## Estado de familias

| `family_status` | Significado |
|---|---|
| `canonical_strong` | Ruta A con `--ads-boundary-mode gkpw` |
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
