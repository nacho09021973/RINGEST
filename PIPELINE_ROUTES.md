# RINGEST pipeline routes

Este archivo define el orden operativo. La numeracion historica de scripts no
define un unico pipeline global.

## Ruta A: sandbox ADS/GKPW

Para generar datos sinteticos ADS y entrenar/probar el motor:

```text
01_generate_sandbox_geometries.py
-> 02_emergent_geometry_engine.py
-> 03_discover_bulk_equations.py
-> 04_geometry_physics_contracts.py
-> 05_analyze_bulk_equations.py
-> 06_build_bulk_eigenmodes_dataset.py
-> 07_emergent_lambda_sl_dictionary.py
-> 08_build_holographic_dictionary.py
-> 09_real_data_and_dictionary_contracts.py
```

Comando base:

```bash
python 01_generate_sandbox_geometries.py \
  --run-dir runs/ads_gkpw_<fecha> \
  --ads-only \
  --ads-boundary-mode gkpw \
  --n-z 256
```

Luego:

```bash
python 02_emergent_geometry_engine.py \
  --run-dir runs/ads_gkpw_<fecha> \
  --data-dir runs/ads_gkpw_<fecha>/01_generate_sandbox_geometries \
  --mode train
```

## Ruta B: datos reales GWOSC

Para eventos reales:

```text
00_download_gwosc_events.py
-> 00_load_ligo_data.py
-> 01_extract_ringdown_poles.py
-> realdata_ringdown_to_stage02_boundary_dataset.py
-> 02_emergent_geometry_engine.py --mode inference
```

`realdata_ringdown_to_stage02_boundary_dataset.py` no es otro stage 02; es un
puente desde ringdown real hacia el formato que consume
`02_emergent_geometry_engine.py`.

## Estado de familias

El campo `family_status` debe leerse antes de interpretar una familia como
fisica fuerte:

| `family_status` | significado |
|---|---|
| `canonical_strong` | carril fuerte; actualmente solo `ads` con `--ads-boundary-mode gkpw` |
| `toy_sandbox` | familia sintetica/sandbox o observable fenomenologico |
| `realdata_surrogate` | embedding derivado de ringdown real; no dual fuerte por si solo |
| `non_holographic_surrogate` | carril especial no holografico, por ejemplo Kerr |

La clasificacion vive en `family_registry.py` y se escribe en manifests/HDF5
cuando el stage lo soporta.

Datos:

```text
data/gwosc_events/<EVENT>/
  raw/
  boundary/
  boundary/ringdown/
  boundary_dataset/
```

`data/` esta ignorado por git. No guardar eventos reales en `runs/`.

## Auxiliares

Estos scripts no son pasos obligatorios de las rutas principales:

| script | uso |
|---|---|
| `00_validate_io_contracts.py` | valida manifests y HDF5 |
| `00b_physics_sanity_checks.py` | sanity checks fisicos |
| `00_compute_sandbox_qnms.py` | QNMs sinteticos |
| `00_sandbox_to_poles_bridge.py` | adapta sandbox a embeddings tipo polos |
| `01b_generate_kerr_sandbox.py` | sandbox Kerr alternativo |
| `04b_negative_control_contracts.py` | contratos de controles negativos |
| `04c_negative_controls.py` | controles negativos |
| `04d_negative_hawking.py` | control negativo Hawking |
| `06_holographic_eigenmode_dataset.py` | legacy frente a `06_build_bulk_eigenmodes_dataset.py` |
| `07_holo_lambda_dictionary.py` | legacy frente a `07_emergent_lambda_sl_dictionary.py` |
| `07b_discover_lambda_delta_relation.py` | analisis lambda-Delta |
| `07K_kerr_qnm_dictionary.py` | diccionario Kerr/QNM |
| `08_theory_dictionary_contrast.py` | contraste teorico posterior |
| `10_build_gwosc_enriched_event_table.py` | tabla lateral de metadatos GWOSC |

`tools/` queda reservado para validadores/contratos compartidos del pipeline.
No se lee como una secuencia lineal.
