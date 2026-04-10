# Canary de 5 eventos en RINGEST

## 1. Alcance

- VERIFICADO_POR_INSPECCION: Esta canary cubre solo el carril materialmente verificable en `docs/instrucciones_pipeline.md`: `00_load_ligo_data.py -> 01_extract_ringdown_poles.py -> 02R_build_ringdown_boundary_dataset.py`.
- VERIFICADO_POR_INSPECCION: Si un evento ya tiene `boundary/`, la canary puede empezar en `01_extract_ringdown_poles.py`.
- VERIFICADO_POR_INSPECCION: Si un evento ya tiene `boundary/ringdown/`, la canary puede empezar en `02R_build_ringdown_boundary_dataset.py`.
- BLOQUEADO: `00_download_gwosc_events.py` queda fuera porque depende de red y de `gwosc`.
- BLOQUEADO: `02_emergent_geometry_engine.py` y `03_discover_bulk_equations.py` quedan fuera porque el documento previo los dejó fuera del carril canary operativo.
- BLOQUEADO: `run_pipeline.py` queda fuera porque no existe en el repo.

## 2. Selección de eventos

- VERIFICADO_POR_INSPECCION: Elegir 5 eventos ya presentes localmente bajo `runs/gwosc_all/` que tengan al menos `raw/`.
- VERIFICADO_POR_INSPECCION: Para una canary corta y homogénea, usar estos 5 eventos ya presentes localmente:
  - `GW150914`
  - `GW151012`
  - `GW170104`
  - `GW190521_030229`
  - `GW191109_010717`
- VERIFICADO_POR_INSPECCION: Criterio de exclusión: excluir cualquier evento que no tenga `raw/`, o que no tenga un `.npz` H1 y otro L1 si se quiere ejecutar stage 00 exactamente como en el documento previo.
- VERIFICADO_POR_INSPECCION: Rutas exactas a inspeccionar por evento:
  - `runs/gwosc_all/<EVENT>/raw`
  - `runs/gwosc_all/<EVENT>/boundary`
  - `runs/gwosc_all/<EVENT>/boundary/ringdown`
  - `runs/gwosc_all/<EVENT>/boundary_dataset`

## 3. Prechecks

- VERIFICADO_POR_INSPECCION: Antes de ejecutar stage 00 deben existir:
  - `runs/gwosc_all/<EVENT>/raw/<EVENT>_H1_4096Hz_32s.npz`
  - `runs/gwosc_all/<EVENT>/raw/<EVENT>_L1_4096Hz_32s.npz`
- VERIFICADO_POR_INSPECCION: Antes de ejecutar stage 01 debe existir:
  - `runs/gwosc_all/<EVENT>/boundary/run_manifest.json`
  - `runs/gwosc_all/<EVENT>/boundary/data_boundary/<EVENT>_boundary.h5`
- VERIFICADO_POR_INSPECCION: Antes de ejecutar stage 02R debe existir:
  - `runs/gwosc_all/<EVENT>/boundary/ringdown/poles_H1.json`
  - `runs/gwosc_all/<EVENT>/boundary/ringdown/summary.json`
- VERIFICADO_POR_INSPECCION: Contratos mínimos que deben pasar antes de seguir:
  - `boundary/run_manifest.json` debe referenciar `data_boundary/<EVENT>_boundary.h5`
  - `boundary/ringdown/summary.json` debe referenciar el `boundary_h5_rel`
  - `boundary_dataset/manifest.json`, si ya existe, debe enumerar al menos un `.h5`

## 4. Secuencia por evento

### Stage 00. `00_load_ligo_data.py`

- VERIFICADO_POR_SMOKE: Comando exacto:
```bash
python3 00_load_ligo_data.py \
  --h1-npz runs/gwosc_all/<EVENT>/raw/<EVENT>_H1_4096Hz_32s.npz \
  --l1-npz runs/gwosc_all/<EVENT>/raw/<EVENT>_L1_4096Hz_32s.npz \
  --run-dir runs/gwosc_all/<EVENT>/boundary \
  --whiten \
  --fft
```
- VERIFICADO_POR_INSPECCION: Inputs: los dos NPZ locales de `raw/`.
- VERIFICADO_POR_INSPECCION: Outputs esperados:
  - `runs/gwosc_all/<EVENT>/boundary/run_manifest.json`
  - `runs/gwosc_all/<EVENT>/boundary/summary.json`
  - `runs/gwosc_all/<EVENT>/boundary/data_boundary/<EVENT>_boundary.h5`
- VERIFICADO_POR_INSPECCION: PASS si existen esos tres artefactos y `summary.json` mantiene `closure_criterion = "adapter_completed"`.
- VERIFICADO_POR_INSPECCION: FAIL si falta el HDF5 boundary o si `run_manifest.json` no lo referencia.

### Stage 01. `01_extract_ringdown_poles.py`

- VERIFICADO_POR_SMOKE: Comando exacto:
```bash
python3 01_extract_ringdown_poles.py \
  --run-dir runs/gwosc_all/<EVENT>/boundary
```
- VERIFICADO_POR_INSPECCION: Inputs: `boundary/run_manifest.json` y `boundary/data_boundary/<EVENT>_boundary.h5`.
- VERIFICADO_POR_INSPECCION: Outputs esperados:
  - `runs/gwosc_all/<EVENT>/boundary/ringdown/ringdown_spec.json`
  - `runs/gwosc_all/<EVENT>/boundary/ringdown/poles_H1.json`
  - `runs/gwosc_all/<EVENT>/boundary/ringdown/summary.json`
- VERIFICADO_POR_INSPECCION: PASS si existe `poles_H1.json` y `ringdown/summary.json` mantiene `closure_criterion = "ringdown_poles_extracted"`.
- VERIFICADO_POR_INSPECCION: FAIL si no se crea `ringdown/` o si `summary.json` no referencia `boundary_h5_rel`.

### Stage 02R. `02R_build_ringdown_boundary_dataset.py`

- VERIFICADO_POR_SMOKE: Comando exacto:
```bash
python3 02R_build_ringdown_boundary_dataset.py \
  --run-dir runs/gwosc_all/<EVENT>/boundary \
  --ringdown-dirs ringdown \
  --out-dir runs/gwosc_all/<EVENT>/boundary_dataset
```
- VERIFICADO_POR_INSPECCION: Inputs: `boundary/ringdown/poles_joint.json` si existe, o fallback a `poles_*.json`.
- VERIFICADO_POR_INSPECCION: Outputs esperados:
  - `runs/gwosc_all/<EVENT>/boundary_dataset/manifest.json`
  - `runs/gwosc_all/<EVENT>/boundary_dataset/*.h5`
- VERIFICADO_POR_INSPECCION: PASS si existe `manifest.json` y lista al menos un `.h5`.
- VERIFICADO_POR_INSPECCION: FAIL si `manifest.json` no existe o si `geometries` queda vacío.

## 5. Criterio de PASS global

- VERIFICADO_POR_INSPECCION: PASS global si los 5 eventos completan todos los stages que se decida ejecutar para ellos, sin salir del carril `00/01/02R`.
- VERIFICADO_POR_INSPECCION: Artefactos mínimos por evento al final:
  - `boundary/data_boundary/<EVENT>_boundary.h5`
  - `boundary/ringdown/poles_H1.json`
  - `boundary/ringdown/summary.json`
  - `boundary_dataset/manifest.json`
- VERIFICADO_POR_INSPECCION: La canary debe abortarse globalmente si ocurre cualquiera de estos fallos:
  - falta un input contractual mínimo en cualquiera de los 5 eventos
  - un stage deja de producir su artefacto contractual principal
  - aparece un fallo sistemático repetido en más de un evento para el mismo stage

## 6. Qué NO interpretar

- VERIFICADO_POR_INSPECCION: Esta canary no valida física, solo integridad operativa del carril `00/01/02R`.
- VERIFICADO_POR_INSPECCION: Esta canary no valida `02_emergent_geometry_engine.py`.
- VERIFICADO_POR_INSPECCION: Esta canary no valida `03_discover_bulk_equations.py`.
- VERIFICADO_POR_INSPECCION: Esta canary no valida DINGO ni ningún entrenamiento.
- VERIFICADO_POR_INSPECCION: Un PASS aquí solo significa que los cambios no rompieron el carril local `00_load_ligo_data.py -> 01_extract_ringdown_poles.py -> 02R_build_ringdown_boundary_dataset.py`.

## 7. Comandos exactos

- VERIFICADO_POR_SMOKE: Ayuda de CLI permitida:
```bash
python3 00_load_ligo_data.py --help
python3 01_extract_ringdown_poles.py --help
python3 02R_build_ringdown_boundary_dataset.py --help
```

- VERIFICADO_POR_INSPECCION: Precheck de presencia local de los 5 eventos:
```bash
for EV in GW150914 GW151012 GW170104 GW190521_030229 GW191109_010717; do
  test -d "runs/gwosc_all/$EV/raw" &&
  test -d "runs/gwosc_all/$EV/boundary" &&
  test -d "runs/gwosc_all/$EV/boundary_dataset" &&
  echo "OK $EV" || echo "MISSING $EV"
done
```

- VERIFICADO_POR_INSPECCION: Ejecución stage 00 para un evento:
```bash
python3 00_load_ligo_data.py \
  --h1-npz runs/gwosc_all/GW150914/raw/GW150914_H1_4096Hz_32s.npz \
  --l1-npz runs/gwosc_all/GW150914/raw/GW150914_L1_4096Hz_32s.npz \
  --run-dir runs/gwosc_all/GW150914/boundary \
  --whiten \
  --fft
```

- VERIFICADO_POR_INSPECCION: Ejecución stage 01 para un evento:
```bash
python3 01_extract_ringdown_poles.py \
  --run-dir runs/gwosc_all/GW150914/boundary
```

- VERIFICADO_POR_INSPECCION: Ejecución stage 02R para un evento:
```bash
python3 02R_build_ringdown_boundary_dataset.py \
  --run-dir runs/gwosc_all/GW150914/boundary \
  --ringdown-dirs ringdown \
  --out-dir runs/gwosc_all/GW150914/boundary_dataset
```

- NO_VERIFICADO: Bucle operador para los 5 eventos; sustentado por la estructura validada, pero no ejecutado en esta tarea:
```bash
for EV in GW150914 GW151012 GW170104 GW190521_030229 GW191109_010717; do
  python3 00_load_ligo_data.py \
    --h1-npz "runs/gwosc_all/$EV/raw/${EV}_H1_4096Hz_32s.npz" \
    --l1-npz "runs/gwosc_all/$EV/raw/${EV}_L1_4096Hz_32s.npz" \
    --run-dir "runs/gwosc_all/$EV/boundary" \
    --whiten \
    --fft &&
  python3 01_extract_ringdown_poles.py \
    --run-dir "runs/gwosc_all/$EV/boundary" &&
  python3 02R_build_ringdown_boundary_dataset.py \
    --run-dir "runs/gwosc_all/$EV/boundary" \
    --ringdown-dirs ringdown \
    --out-dir "runs/gwosc_all/$EV/boundary_dataset"
done
```

