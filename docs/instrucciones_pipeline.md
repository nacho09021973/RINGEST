# Instrucciones del pipeline RINGEST

## 1. Estado de descubrimiento

- VERIFICADO_POR_INSPECCION: El repo no contiene un entrypoint único tipo `run_pipeline.py`. `02R_build_ringdown_boundary_dataset.py` lo menciona como siguiente paso, pero el archivo no existe en este repo.
- VERIFICADO_POR_INSPECCION: La ruta mínima demostrable sobre datos GWOSC/reales está repartida en scripts del root y se puede reconstruir como secuencia manual: `00_download_gwosc_events.py` -> `00_load_ligo_data.py` -> `01_extract_ringdown_poles.py` -> `02R_build_ringdown_boundary_dataset.py`.
- VERIFICADO_POR_INSPECCION: Existe evidencia material de esa secuencia manual en `runs/gwosc_all/<EVENT>/raw`, `runs/gwosc_all/<EVENT>/boundary`, `runs/gwosc_all/<EVENT>/boundary/ringdown` y `runs/gwosc_all/<EVENT>/boundary_dataset`.
- VERIFICADO_POR_INSPECCION: Hay evidencia adicional de continuidad posterior para al menos un evento ya procesado: `runs/gwosc_all/GW150914/02_emergent_geometry_engine/` y `runs/gwosc_all/GW150914/03_discover_bulk_equations/`.
- VERIFICADO_POR_SMOKE: `00_load_ligo_data.py --help`, `01_extract_ringdown_poles.py --help` y `02R_build_ringdown_boundary_dataset.py --help` responden correctamente en este entorno.
- BLOQUEADO: `00_download_gwosc_events.py --help` no llega al parser porque aborta antes al no encontrar `gwosc`.
- BLOQUEADO: `02_emergent_geometry_engine.py --help` no llega al parser porque aborta al importar `torch`.
- VERIFICADO_POR_SMOKE: `run_batch_load.sh --dry-run` existe y ejecuta, pero apunta a `/home/ignac/malda/runs/gwosc_all`, no a este repo; por tanto no es un entrypoint operativo fiable aquí.
- NO_VERIFICADO: La ejecución completa de `02_emergent_geometry_engine.py` sobre nuevos datos reales no se ha verificado en este entorno.
- NO_VERIFICADO: La continuidad más allá de `03_discover_bulk_equations.py` existe por inspección de scripts, pero no forma parte de la secuencia mínima demostrable sobre GWOSC si no se resuelven dependencias pesadas.

## 2. Scripts canónicos del root

### 2.1 Scripts canónicos directamente relacionados con GWOSC/datos reales

| script | rol | inputs | outputs | observaciones |
|---|---|---|---|---|
| `00_download_gwosc_events.py` | Descarga HDF5 de GWOSC y los convierte a NPZ por IFO/evento | catálogos GWOSC; flags `--out-dir`, `--catalogs`, `--event`, `--max-events` | `<out-dir>/<event>/raw/*.npz`, HDF5 crudos, `download_manifest.json` | BLOQUEADO en este entorno por dependencia `gwosc`; además usa red |
| `00_load_ligo_data.py` | Adapta NPZ locales a artefacto boundary auditable | `--h1-npz`, opcional `--l1-npz`, opcional metas, `--run-dir` o `--runs-root` | `run_manifest.json`, `adapter_spec.json`, `summary.json`, `data_boundary/<event>_boundary.h5`, `data_boundary/<event>_boundary_meta.json` | CLI verificada por smoke |
| `01_extract_ringdown_poles.py` | Extrae polos operacionales desde el HDF5 boundary | `--run-dir`, opcional `--boundary-h5` | `ringdown/ringdown_spec.json`, `poles_*.json`, `poles_*.csv`, `ringdown/summary.json`, actualización de `run_manifest.json` | CLI verificada por smoke; prefiere strain blanqueado si existe |
| `02R_build_ringdown_boundary_dataset.py` | Convierte artefactos de ringdown a dataset boundary consumible por stage 02 | `--run-dir`, `--ringdown-dirs`, `--out-dir` | `<out-dir>/*.h5`, `<out-dir>/manifest.json` | CLI verificada por smoke; puente explícito hacia stage 02 |
| `02_emergent_geometry_engine.py` | Motor de geometría emergente; tiene modo `train` y `inference` | `--data-dir`, `--output-dir`, `--mode`, `--checkpoint` | `geometry_emergent/*.h5`, `predictions/*.npz`, `emergent_geometry_summary.json`, `stage_summary.json` | BLOQUEADO aquí por `torch` ausente; no hay entrypoint único externo |
| `03_discover_bulk_equations.py` | Descubre ecuaciones sobre geometrías emergentes | `--geometry-dir` o run dir/experiment | `03_discover_bulk_equations/einstein_discovery_summary.json` y subdirectorios por geometría | Existe un ejemplo material en `runs/gwosc_all/GW150914/03_discover_bulk_equations/` |
| `05_analyze_bulk_equations.py` | Analiza el resumen de stage 03 | `--input` o inferencia desde `03_discover_bulk_equations` | `bulk_equations_report.txt`, `.json`, `stage_summary.json` | No es parte mínima del camino GWOSC |
| `06_build_bulk_eigenmodes_dataset.py` | Construye dataset de autovalores SL desde geometrías emergentes | `02_emergent_geometry_engine/geometry_emergent/*.h5` | `bulk_modes_dataset.csv`, `bulk_modes_meta.json`, `stage_summary.json` | Requiere solver bulk; no verificado por smoke |
| `07_emergent_lambda_sl_dictionary.py` | Aprende relación emergente `lambda_sl` <-> `Delta` | `06_build_bulk_eigenmodes_dataset/bulk_modes_dataset.csv` | `lambda_sl_dictionary_report.json`, `lambda_sl_dictionary_pareto.csv`, `stage_summary.json` | Tiene interacción potencial con el usuario si detecta métodos sospechosos |
| `08_build_holographic_dictionary.py` | Construye atlas/diccionario desde geometrías emergentes | `02_emergent_geometry_engine/geometry_emergent/*.h5` | `holographic_dictionary_v3_summary.json`, `stage_summary.json` | Usa geometrías emergentes, no datos GWOSC crudos |
| `09_real_data_and_dictionary_contracts.py` | Contratos entre diccionario emergente y datos/controles reales | `07.../lambda_sl_dictionary_report.json` y opcionales de fase 13 | `contracts_12_13.json`, `stage_summary.json` | Aguas abajo; no parte mínima para producir boundary/ringdown |
| `10_build_gwosc_enriched_event_table.py` | Tabla enriquecida de eventos en `runs/gwosc_all` | `--runs-dir` local más HTTP a GWOSC | `gwosc_enriched_event_table.csv`, `gwosc_enriched_event_table_summary.json` | No es stage del pipeline principal; usa red |

### 2.2 Scripts del root que son canónicos, pero sandbox/auxiliares/experimentales

- VERIFICADO_POR_INSPECCION: `01_generate_sandbox_geometries.py`, `01b_generate_kerr_sandbox.py`, `00_compute_sandbox_qnms.py`, `00_sandbox_to_poles_bridge.py`, `04_geometry_physics_contracts.py`, `04b_negative_control_contracts.py`, `04c_negative_controls.py`, `04d_negative_hawking.py`, `06_holographic_eigenmode_dataset.py`, `07_holo_lambda_dictionary.py`, `07K_kerr_qnm_dictionary.py`, `07b_discover_lambda_delta_relation.py`, `merge_manifests.py` forman parte del carril sandbox/auxiliar y no son necesarios para la secuencia mínima GWOSC->boundary->ringdown->02R.
- VERIFICADO_POR_INSPECCION: `stage_utils.py` es infraestructura de stages; no es entrypoint.

### 2.3 Archivos del root no canónicos para operar el pipeline

- VERIFICADO_POR_INSPECCION: `gemini-code.py`, `import_google.py`, `test_gemini.py` no forman parte del pipeline RINGEST sobre GWOSC.
- VERIFICADO_POR_SMOKE: `run_batch_load.sh` no es canónico para este repo tal como está, porque resuelve rutas bajo `/home/ignac/malda/` y en este checkout produce `Eventos: 0`.

## 3. Entry point real del pipeline

- VERIFICADO_POR_INSPECCION: No existe en el repo un entrypoint único verificable para el pipeline real sobre GWOSC.
- VERIFICADO_POR_INSPECCION: La secuencia mínima manual demostrable es:
  1. `00_download_gwosc_events.py` para materializar `raw/*.npz` por evento.
  2. `00_load_ligo_data.py` para crear un `run_dir` boundary auditable por evento.
  3. `01_extract_ringdown_poles.py` para producir `ringdown/`.
  4. `02R_build_ringdown_boundary_dataset.py` para producir `boundary_dataset/`.
- VERIFICADO_POR_INSPECCION: A partir de `boundary_dataset/`, el siguiente stage lógico es `02_emergent_geometry_engine.py --mode inference`, pero el script que 02R cita (`run_pipeline.py`) no está presente y por tanto no puede documentarse como entrypoint real.
- BLOQUEADO: Documentar un comando único de orquestación posterior a 02R sería inventar un entrypoint no presente.

## 4. Secuencia mínima sobre datos reales

### Stage 00A. Descarga GWOSC

- VERIFICADO_POR_INSPECCION: Script `00_download_gwosc_events.py`.
- VERIFICADO_POR_INSPECCION: Comando base inferido del propio script:
```bash
python3 00_download_gwosc_events.py --out-dir runs/gwosc_all
```
- VERIFICADO_POR_INSPECCION: Inputs requeridos: acceso de red a GWOSC, paquete `gwosc`, `requests`, `numpy`, `h5py`.
- VERIFICADO_POR_INSPECCION: Outputs esperados: `runs/gwosc_all/<EVENT>/raw/<EVENT>_<IFO>_4096Hz_32s.npz`, HDF5 crudos y `runs/gwosc_all/download_manifest.json`.
- VERIFICADO_POR_INSPECCION: Contrato de salida explícito: los NPZ contienen `t_gps`, `strain`, `fs`, `ifo`, `event`, `gps`, `start`, `end`, `source_url`, exactamente el esquema que `00_load_ligo_data.py` espera.
- BLOQUEADO: No es operable ahora mismo en este entorno por ausencia de `gwosc` y por restricción de no usar red.

### Stage 00B. Adaptación a boundary auditable

- VERIFICADO_POR_SMOKE: Script `00_load_ligo_data.py`.
- VERIFICADO_POR_SMOKE: Comando base mínimo con rutas reales existentes:
```bash
python3 00_load_ligo_data.py \
  --h1-npz runs/gwosc_all/GW150914/raw/GW150914_H1_4096Hz_32s.npz \
  --l1-npz runs/gwosc_all/GW150914/raw/GW150914_L1_4096Hz_32s.npz \
  --run-dir runs/gwosc_all/GW150914/boundary \
  --whiten \
  --fft
```
- VERIFICADO_POR_INSPECCION: Inputs requeridos: `--h1-npz`; `--l1-npz` opcional; esquema NPZ descrito arriba; opcionales metas.
- VERIFICADO_POR_INSPECCION: Outputs esperados dentro de `run_dir`: `run_manifest.json`, `adapter_spec.json`, `summary.json`, `data_boundary/<EVENT>_boundary.h5`, `data_boundary/<EVENT>_boundary_meta.json`.
- VERIFICADO_POR_INSPECCION: Contrato de salida: `run_manifest.json` publica `artifacts.ligo_boundary_h5` y `artifacts.ligo_boundary_meta_json`; `summary.json` fija `closure_criterion = "adapter_completed"`.

### Stage 01. Extracción de polos de ringdown

- VERIFICADO_POR_SMOKE: Script `01_extract_ringdown_poles.py`.
- VERIFICADO_POR_SMOKE: Comando base mínimo sobre un run existente:
```bash
python3 01_extract_ringdown_poles.py \
  --run-dir runs/gwosc_all/GW150914/boundary
```
- VERIFICADO_POR_INSPECCION: Inputs requeridos: `--run-dir`; opcional `--boundary-h5`. Si no se pasa `--boundary-h5`, el script lo resuelve desde `run_manifest.json`.
- VERIFICADO_POR_INSPECCION: Outputs esperados: `ringdown/ringdown_spec.json`, `ringdown/poles_H1.json`, `ringdown/poles_H1.csv`, opcionales `poles_L1.*`, opcionales `poles_joint.*`, `ringdown/summary.json`.
- VERIFICADO_POR_INSPECCION: Contrato de salida: `summary.json` fija `closure_criterion = "ringdown_poles_extracted"` y `run_manifest.json` se actualiza con `ringdown_dir`, `ringdown_spec`, `ringdown_summary` y los artefactos `poles_*`.

### Stage 02R. Bridge ringdown -> boundary dataset

- VERIFICADO_POR_SMOKE: Script `02R_build_ringdown_boundary_dataset.py`.
- VERIFICADO_POR_SMOKE: Comando base mínimo sobre un run existente:
```bash
python3 02R_build_ringdown_boundary_dataset.py \
  --run-dir runs/gwosc_all/GW150914/boundary \
  --ringdown-dirs ringdown \
  --out-dir runs/gwosc_all/GW150914/boundary_dataset
```
- VERIFICADO_POR_INSPECCION: Inputs requeridos: `--run-dir`, uno o más `--ringdown-dirs` dentro de ese run, `--out-dir`.
- VERIFICADO_POR_INSPECCION: Inputs consumidos dentro de cada `ringdown-dir`: `poles_joint.json` si existe; fallback a `poles_*.json`; opcionales `coincident_pairs.json` y `null_test.json`.
- VERIFICADO_POR_INSPECCION: Outputs esperados: `boundary_dataset/*.h5` y `boundary_dataset/manifest.json`.
- VERIFICADO_POR_INSPECCION: Contrato de salida: el HDF5 resultante expone grupo `boundary/` con `omega_grid`, `k_grid`, `G_R_real`, `G_R_imag`, `x_grid`, `G2_ringdown` y attrs de procedencia; `manifest.json` publica `geometries[*].file` y `source_ringdown_dir`.

### Stage 02. Geometría emergente sobre datos reales

- VERIFICADO_POR_INSPECCION: `02_emergent_geometry_engine.py` tiene modo `inference` y acepta `--data-dir`, `--output-dir`, `--mode inference`, `--checkpoint`.
- VERIFICADO_POR_INSPECCION: El stage 02 consume un directorio con `manifest.json` o `geometries_manifest.json`; `02R` produce precisamente `manifest.json`.
- VERIFICADO_POR_INSPECCION: Existe evidencia material de una corrida previa en `runs/gwosc_all/GW150914/02_emergent_geometry_engine/emergent_geometry_summary.json`, donde el input fue `runs/gwosc_all/GW150914/boundary_dataset/GW150914__ringdown.h5`.
- BLOQUEADO: En este entorno no puede verificarse la CLI por `--help` porque falta `torch`.
- NO_VERIFICADO: Comando manual plausible por inspección, pero no validado aquí:
```bash
python3 02_emergent_geometry_engine.py \
  --mode inference \
  --data-dir runs/gwosc_all/GW150914/boundary_dataset \
  --output-dir runs/gwosc_all/GW150914/02_emergent_geometry_engine \
  --checkpoint runs/sandbox_v5_b3/02_emergent_geometry_engine/emergent_geometry_model.pt
```

## 5. Contratos entre stages

### 00_download_gwosc_events.py -> 00_load_ligo_data.py

- VERIFICADO_POR_INSPECCION: `00_download_gwosc_events.py` documenta que escribe NPZ con claves `t_gps`, `strain`, `fs`, `ifo`, `event`, `gps`, `start`, `end`, `source_url`.
- VERIFICADO_POR_INSPECCION: `00_load_ligo_data.py` documenta ese mismo esquema como input esperado.

### 00_load_ligo_data.py -> 01_extract_ringdown_poles.py

- VERIFICADO_POR_INSPECCION: `01_extract_ringdown_poles.py` busca `<RUN_DIR>/data_boundary/<EVENT>_boundary.h5`.
- VERIFICADO_POR_INSPECCION: Si no se pasa `--boundary-h5`, resuelve ese HDF5 desde `run_manifest.json`.
- VERIFICADO_POR_INSPECCION: `00_load_ligo_data.py` produce exactamente ambos artefactos: `data_boundary/<EVENT>_boundary.h5` y `run_manifest.json`.
- VERIFICADO_POR_INSPECCION: El stage 01 prefiere `strain/H1_whitened` y `strain/L1_whitened` cuando existen; esos datasets son producidos por stage 00 solo si se usa `--whiten`.

### 01_extract_ringdown_poles.py -> 02R_build_ringdown_boundary_dataset.py

- VERIFICADO_POR_INSPECCION: `02R_build_ringdown_boundary_dataset.py` consume `poles_joint.json` o fallback a `poles_*.json` dentro de cada `ringdown-dir`.
- VERIFICADO_POR_INSPECCION: `01_extract_ringdown_poles.py` produce exactamente `poles_H1.json`, `poles_L1.json` y `poles_joint.json` cuando procede.
- VERIFICADO_POR_INSPECCION: El handoff mínimo real no requiere `coincident_pairs.json` ni `null_test.json`; 02R los trata como opcionales.

### 02R_build_ringdown_boundary_dataset.py -> 02_emergent_geometry_engine.py

- VERIFICADO_POR_INSPECCION: `02R_build_ringdown_boundary_dataset.py` declara explícitamente que su salida es “consumable by” stage 02.
- VERIFICADO_POR_INSPECCION: `02_emergent_geometry_engine.py` en modo inference busca `manifest.json` o `geometries_manifest.json` en `--data-dir`.
- VERIFICADO_POR_INSPECCION: `02R` escribe `manifest.json` y HDF5 con grupo `boundary/`, que es el formato que stage 02 carga.
- BLOQUEADO: La orquestación vía `run_pipeline.py` no puede documentarse porque el archivo no existe.

### 02_emergent_geometry_engine.py -> 03_discover_bulk_equations.py

- VERIFICADO_POR_INSPECCION: `03_discover_bulk_equations.py` prioriza `runs/<exp>/02_emergent_geometry_engine/geometry_emergent/*.h5`.
- VERIFICADO_POR_INSPECCION: `02_emergent_geometry_engine.py` produce `geometry_emergent/*.h5`.
- VERIFICADO_POR_INSPECCION: Hay evidencia material de este handoff en `runs/gwosc_all/GW150914/02_emergent_geometry_engine/geometry_emergent/` y `runs/gwosc_all/GW150914/03_discover_bulk_equations/einstein_discovery_summary.json`.

### 03_discover_bulk_equations.py -> 05_analyze_bulk_equations.py

- VERIFICADO_POR_INSPECCION: `05_analyze_bulk_equations.py` busca por defecto `03_discover_bulk_equations/einstein_discovery_summary.json`.
- VERIFICADO_POR_INSPECCION: `03_discover_bulk_equations.py` escribe exactamente `einstein_discovery_summary.json`.

### 02_emergent_geometry_engine.py -> 06_build_bulk_eigenmodes_dataset.py

- VERIFICADO_POR_INSPECCION: `06_build_bulk_eigenmodes_dataset.py` declara como input `runs/<experiment>/02_emergent_geometry_engine/geometry_emergent/*.h5`.

### 06_build_bulk_eigenmodes_dataset.py -> 07_emergent_lambda_sl_dictionary.py

- VERIFICADO_POR_INSPECCION: `07_emergent_lambda_sl_dictionary.py` declara como entrada `runs/<experiment>/06_build_bulk_eigenmodes_dataset/bulk_modes_dataset.csv`.
- VERIFICADO_POR_INSPECCION: `06_build_bulk_eigenmodes_dataset.py` declara como salida `bulk_modes_dataset.csv`.

### 02_emergent_geometry_engine.py -> 08_build_holographic_dictionary.py

- VERIFICADO_POR_INSPECCION: `08_build_holographic_dictionary.py` declara como input `runs/<experiment>/02_emergent_geometry_engine/geometry_emergent/*.h5`.

### 07_emergent_lambda_sl_dictionary.py / fase 13 -> 09_real_data_and_dictionary_contracts.py

- VERIFICADO_POR_INSPECCION: `09_real_data_and_dictionary_contracts.py` resuelve por defecto `07_emergent_lambda_sl_dictionary/lambda_sl_dictionary_report.json`.
- VERIFICADO_POR_INSPECCION: `09_real_data_and_dictionary_contracts.py` también acepta reportes/análisis de fase 13 por flags explícitos.

### Contratos que no deben afirmarse

- NO_VERIFICADO: No he encontrado evidencia de un handoff directo `02 -> 03 -> 04 -> 05 -> 06 -> 07 -> 08 -> 09` como pipeline único obligatorio.
- NO_VERIFICADO: No he encontrado un manifiesto maestro que encadene automáticamente todos los stages reales.

## 6. Prueba canary recomendada

- VERIFICADO_POR_INSPECCION: La canary debe seleccionarse desde eventos ya materializados localmente en `runs/gwosc_all/*/raw` para evitar red y para no mezclar descubrimiento con descarga.
- VERIFICADO_POR_INSPECCION: La gobernanza más segura es procesar solo 5 eventos en directorios aislados por evento y auditar `run_manifest.json`, `ringdown/summary.json` y `boundary_dataset/manifest.json` después de cada uno.
- NO_VERIFICADO: Selección sugerida de 5 eventos con artefactos locales ya presentes y cronología diversa: `GW150914`, `GW151012`, `GW170104`, `GW190521_030229`, `GW191109_010717`.
- VERIFICADO_POR_INSPECCION: Qué no ejecutar todavía: descarga masiva nueva, `02_emergent_geometry_engine.py` si sigue faltando `torch`, entrenamiento sandbox, stages PySR largos (`03`, `07`) y cualquier batch grande.
- VERIFICADO_POR_INSPECCION: Artefactos a auditar por evento:
  - `boundary/run_manifest.json`
  - `boundary/summary.json`
  - `boundary/ringdown/summary.json`
  - `boundary_dataset/manifest.json`
- VERIFICADO_POR_INSPECCION: Criterios PASS por evento:
  - existe `data_boundary/<EVENT>_boundary.h5`
  - existe `ringdown/poles_H1.json`
  - existe `boundary_dataset/manifest.json`
  - los manifests referencian rutas que existen
- VERIFICADO_POR_INSPECCION: Criterios FAIL por evento:
  - falta cualquier artefacto contractual mínimo anterior
  - `run_manifest.json` no referencia el HDF5 boundary
  - `ringdown/summary.json` no referencia el input boundary
  - `boundary_dataset/manifest.json` no enumera ningún `.h5`
- NO_VERIFICADO: Ejecutar la canary completa no se ha hecho en esta tarea; esto es una recomendación operativa basada en inspección.

## 7. Riesgos y bloqueos

- BLOQUEADO: `00_download_gwosc_events.py` depende de `gwosc` y de acceso a red; ambas cosas están fuera de lo permitido en esta tarea.
- BLOQUEADO: `02_emergent_geometry_engine.py` depende de `torch`, ausente en este entorno.
- BLOQUEADO: `run_pipeline.py` es citado por 02R pero no existe en el repo.
- VERIFICADO_POR_SMOKE: `run_batch_load.sh` usa rutas `malda/` y por eso no sirve como entrypoint canónico en este checkout.
- VERIFICADO_POR_INSPECCION: Varios stages aguas abajo (`03`, `07`) dependen de PySR u otros componentes pesados; no deben tratarse como smoke.
- VERIFICADO_POR_INSPECCION: `10_build_gwosc_enriched_event_table.py` usa HTTP a GWOSC; no entra en la ruta mínima offline.
- VERIFICADO_POR_INSPECCION: La cadena posterior a 02R no está gobernada por un manifiesto maestro único; hay acoplamiento por convenciones de rutas/stage dirs.
- VERIFICADO_POR_INSPECCION: `07_emergent_lambda_sl_dictionary.py` puede pedir confirmación interactiva si detecta métodos sospechosos; eso complica automatización ciega.

## 8. Comandos exactos recomendados

### 8.1 Comandos seguros y verificados en este entorno

- VERIFICADO_POR_SMOKE:
```bash
python3 00_load_ligo_data.py --help
```

- VERIFICADO_POR_SMOKE:
```bash
python3 01_extract_ringdown_poles.py --help
```

- VERIFICADO_POR_SMOKE:
```bash
python3 02R_build_ringdown_boundary_dataset.py --help
```

- VERIFICADO_POR_SMOKE:
```bash
bash run_batch_load.sh --dry-run
```

### 8.2 Comandos operativos mínimos sostenidos por inspección del repo

- VERIFICADO_POR_SMOKE:
```bash
python3 00_load_ligo_data.py \
  --h1-npz runs/gwosc_all/GW150914/raw/GW150914_H1_4096Hz_32s.npz \
  --l1-npz runs/gwosc_all/GW150914/raw/GW150914_L1_4096Hz_32s.npz \
  --run-dir runs/gwosc_all/GW150914/boundary \
  --whiten \
  --fft
```

- VERIFICADO_POR_SMOKE:
```bash
python3 01_extract_ringdown_poles.py \
  --run-dir runs/gwosc_all/GW150914/boundary
```

- VERIFICADO_POR_SMOKE:
```bash
python3 02R_build_ringdown_boundary_dataset.py \
  --run-dir runs/gwosc_all/GW150914/boundary \
  --ringdown-dirs ringdown \
  --out-dir runs/gwosc_all/GW150914/boundary_dataset
```

### 8.3 Comandos que no recomiendo como operativos ahora

- BLOQUEADO:
```bash
python3 00_download_gwosc_events.py --out-dir runs/gwosc_all
```

- BLOQUEADO:
```bash
python3 02_emergent_geometry_engine.py --help
```

- BLOQUEADO:
```bash
python3 02_emergent_geometry_engine.py \
  --mode inference \
  --data-dir runs/gwosc_all/GW150914/boundary_dataset \
  --output-dir runs/gwosc_all/GW150914/02_emergent_geometry_engine \
  --checkpoint runs/sandbox_v5_b3/02_emergent_geometry_engine/emergent_geometry_model.pt
```

