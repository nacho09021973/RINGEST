# Instrucciones para correr RINGEST

Ejecutar siempre desde la raiz del repo:

```bash
cd /home/ignac/RINGEST
```

## Datos

Los eventos reales viven en:

```text
data/gwosc_events/
```

`data/` esta en `.gitignore` por tamano. `runs/` tambien esta en `.gitignore` y
se considera desechable: se puede borrar para empezar de cero.

Eventos canarios canonicos:

```text
GW150914
GW151012
GW170104
GW190521_030229
GW191109_010717
```

Layout por evento:

```text
data/gwosc_events/<EVENT>/
  raw/
  boundary/
  boundary/ringdown/
  boundary_dataset/
```

## Ruta A: sandbox ADS/GKPW

Usar esta ruta para entrenar o probar el motor con datos sinteticos ADS. El modo
canonico es GKPW, no toy.

```bash
RUN_DIR=runs/ads_gkpw_$(date +%Y%m%d_%H%M%S)

python 01_generate_sandbox_geometries.py \
  --run-dir "$RUN_DIR" \
  --ads-only \
  --ads-boundary-mode gkpw \
  --n-z 256

python 02_emergent_geometry_engine.py \
  --run-dir "$RUN_DIR" \
  --data-dir "$RUN_DIR/01_generate_sandbox_geometries" \
  --mode train

python 03_discover_bulk_equations.py \
  --run-dir "$RUN_DIR" \
  --geometry-dir "$RUN_DIR/02_emergent_geometry_engine/geometry_emergent"

python 04_geometry_physics_contracts.py --run-dir "$RUN_DIR"
python 05_analyze_bulk_equations.py --run-dir "$RUN_DIR"
python 06_build_bulk_eigenmodes_dataset.py --run-dir "$RUN_DIR"
```

Smoke verificado y notas de parametros:
[docs/manual_pipeline_ads_gkpw.md](/home/ignac/RINGEST/docs/manual_pipeline_ads_gkpw.md).

## Estado de familias

Leer `family_status` antes de interpretar una salida como fisica fuerte.

| `family_status` | significado |
|---|---|
| `canonical_strong` | carril fuerte; actualmente solo `ads` con `--ads-boundary-mode gkpw` |
| `toy_sandbox` | familia sintetica/sandbox o observable fenomenologico |
| `realdata_surrogate` | embedding derivado de ringdown real; no dual fuerte por si solo |
| `non_holographic_surrogate` | carril especial no holografico, por ejemplo Kerr |

Regla actual:

```text
ads + gkpw         -> canonical_strong
ads toy           -> toy_sandbox
lifshitz, etc.    -> toy_sandbox
ringdown real     -> realdata_surrogate
kerr              -> non_holographic_surrogate
```

Stage 01 y el bridge real-data escriben este campo en manifests/HDF5.

## Ruta B: eventos reales GWOSC

### 1. Descargar

```bash
python 00_download_gwosc_events.py --out-dir data/gwosc_events
```

Para descargar solo canarios:

```bash
python 00_download_gwosc_events.py \
  --out-dir data/gwosc_events \
  --event GW150914 GW151012 GW170104 GW190521_030229 GW191109_010717
```

### 2. Convertir NPZ a boundary HDF5

Todos los eventos locales:

```bash
bash run_batch_load.sh --jobs 4
```

Solo inspeccion de comandos:

```bash
bash run_batch_load.sh --dry-run
```

Un evento manual:

```bash
python 00_load_ligo_data.py \
  --h1-npz data/gwosc_events/GW150914/raw/GW150914_H1_4096Hz_32s.npz \
  --l1-npz data/gwosc_events/GW150914/raw/GW150914_L1_4096Hz_32s.npz \
  --run-dir data/gwosc_events/GW150914/boundary \
  --whiten \
  --fft
```

### 3. Extraer ringdown

```bash
python 01_extract_ringdown_poles.py \
  --run-dir data/gwosc_events/GW150914/boundary \
  --duration 0.25 \
  --require-decay \
  --max-modes 16
```

### 4. Construir dataset para stage 02

```bash
python realdata_ringdown_to_stage02_boundary_dataset.py \
  --run-dir data/gwosc_events/GW150914/boundary \
  --ringdown-dirs ringdown \
  --out-dir data/gwosc_events/GW150914/boundary_dataset \
  --d 4
```

Este script no es un segundo stage 02: solo convierte polos de ringdown real al
formato que consume el motor.

### 5. Inferencia con el motor

Necesitas un checkpoint entrenado, normalmente generado por la Ruta A:

```bash
python 02_emergent_geometry_engine.py \
  --mode inference \
  --data-dir data/gwosc_events/GW150914/boundary_dataset \
  --output-dir data/gwosc_events/GW150914/02_emergent_geometry_engine \
  --checkpoint runs/<trained_run>/02_emergent_geometry_engine/emergent_geometry_model.pt
```

## Orden completo

El mapa corto esta en [PIPELINE_ROUTES.md](/home/ignac/RINGEST/PIPELINE_ROUTES.md).
Si un script no aparece ahi, no es obligatorio para correr el pipeline principal.

Config minimo que si pertenece al pipeline:

- `configs/theory_dictionary/theory_dictionary_v1.json`: diccionario explicito
  que consume `08_theory_dictionary_contrast.py`.

## Tests utiles

Smoke obligatorio despues de tocar rutas, familias, ADS/GKPW o bridge real-data:

```bash
python3 -m pytest \
  tests/test_agmoo_ads_contract.py \
  tests/test_stage01_ads_gkpw_mode.py \
  tests/test_gkpw_ads_scalar_correlator.py \
  tests/test_realdata_bridge_saturation_detection.py \
  tests/test_realdata_bridge_g2_time_contracts.py \
  tests/test_g2_representation_contract.py
```

Smoke rapido solo para bridge real-data:

```bash
python3 -m unittest \
  tests/test_realdata_bridge_saturation_detection.py \
  tests/test_realdata_bridge_g2_time_contracts.py
```

Suite reducida completa:

```bash
python3 -m pytest -q
```

Reduccion del ruido:

- `pytest` queda limitado al directorio `tests/`; no debe entrar en `data/` ni
  `runs/`.
- Los carriles laterales `repo_agent_*`, `estimator_*`,
  `baseline_vs_premium_*`, experimentos laterales de sensibilidad
  `softwall/gubser_rocha`, `decay_type_*`, `unified82_*` y `experiment_*`
  fueron eliminados para mantener el repo gobernable.
- Los tests imprescindibles para el pipeline actual son los de ADS/GKPW,
  `family_status`, bridge real-data, G2 representation, contratos runtime de
  stages y `stage_utils`.
- Los tests que necesitan `torch` se saltan en entornos sin backend de
  entrenamiento instalado; el pipeline stage 02 real sigue necesitando `torch`.
