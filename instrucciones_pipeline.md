# Instrucciones para correr RINGEST

Ejecutar siempre desde la raíz del repo:

```bash
cd /path/to/RINGEST
```

`runs/` y `data/` están en `.gitignore` y se consideran desechables.
Para empezar desde cero basta con `rm -rf runs/`.

---

## Índice de rutas

| Ruta | Descripción |
|---|---|
| [A — Sandbox ADS/GKPW](#ruta-a-sandbox-adsgkpw) | Geometría emergente sobre datos sintéticos |
| [B — Datos reales GWOSC](#ruta-b-datos-reales-gwosc) | Inferencia holográfica sobre ringdown real |
| [C — Cadena QNM](#ruta-c-cadena-qnm) | Descubrimiento simbólico + KAN + validación Kerr |

---

## Ruta A — Sandbox ADS/GKPW

Pipeline canónico para entrenar y validar el motor con geometrías ADS sintéticas.

```bash
RUN_DIR=runs/ads_gkpw_$(date +%Y%m%d_%H%M%S)

# 1. Generar geometrías sintéticas
python3 01_generate_sandbox_geometries.py \
  --run-dir "$RUN_DIR" \
  --ads-only \
  --ads-boundary-mode gkpw \
  --n-z 256

# 2. Entrenar motor de geometría emergente
python3 02_emergent_geometry_engine.py \
  --run-dir "$RUN_DIR" \
  --data-dir "$RUN_DIR/01_generate_sandbox_geometries" \
  --mode train

# 3. Descubrimiento simbólico de ecuaciones de bulk (requiere PySR/Julia)
python3 03_discover_bulk_equations.py \
  --run-dir "$RUN_DIR" \
  --geometry-dir "$RUN_DIR/02_emergent_geometry_engine/geometry_emergent"

# 4. Contratos físicos sobre la geometría
python3 04_geometry_physics_contracts.py --run-dir "$RUN_DIR"

# 5. Analizar estructura de las ecuaciones descubiertas
python3 05_analyze_bulk_equations.py --run-dir "$RUN_DIR"

# 6. Dataset de eigenmodos (Sturm-Liouville)
python3 06_build_bulk_eigenmodes_dataset.py --run-dir "$RUN_DIR"

# 7. Redescubrir λ_SL = Δ(Δ−d) emergentemente
python3 07_emergent_lambda_sl_dictionary.py --run-dir "$RUN_DIR"

# 8. Construir atlas holográfico completo
python3 08_build_holographic_dictionary.py --run-dir "$RUN_DIR"

# 9. Contratos finales sobre datos reales + diccionario
python3 09_real_data_and_dictionary_contracts.py --run-dir "$RUN_DIR"
```

Smoke test documentado con parámetros verificados:
[docs/manual_pipeline_ads_gkpw.md](docs/manual_pipeline_ads_gkpw.md)

---

## Ruta B — Datos reales GWOSC

Eventos canónicos (5 canarios recomendados):

```text
GW150914  GW151012  GW170104  GW190521_030229  GW191109_010717
```

### B-1 · Descargar eventos

Todos los canarios:

```bash
python3 00_download_gwosc_events.py \
  --out-dir data/gwosc_events \
  --event GW150914 GW151012 GW170104 GW190521_030229 GW191109_010717
```

### B-2 · Convertir NPZ → boundary HDF5

```bash
# Todos los eventos locales en paralelo:
bash run_batch_load.sh --jobs 4

# Un evento manual:
python3 00_load_ligo_data.py \
  --h1-npz data/gwosc_events/GW150914/raw/GW150914_H1_4096Hz_32s.npz \
  --l1-npz data/gwosc_events/GW150914/raw/GW150914_L1_4096Hz_32s.npz \
  --run-dir data/gwosc_events/GW150914/boundary \
  --whiten --fft
```

### B-3 · YAML literatura → qnm_dataset.csv (carril activo)

```bash
python3 02b_literature_to_dataset.py \
  --sources data/qnm_events_literature.yml \
  --out runs/qnm_dataset_literature
```

Salida: `runs/qnm_dataset_literature/qnm_dataset.csv`, `qnm_dataset_220.csv`.

#### Rama ESPRIT alternativa (conservada, no activa)

```bash
python3 01_extract_ringdown_poles.py \
  --run-dir data/gwosc_events/GW150914/boundary \
  --duration 0.25 \
  --require-decay \
  --max-modes 16
```

Salida: `data/gwosc_events/GW150914/boundary/ringdown/poles_joint.json`

### B-4 · Bridge a formato stage-02

Carril activo (CSV de literatura):

```bash
python3 realdata_ringdown_to_stage02_boundary_dataset.py \
  --dataset-csv runs/qnm_dataset_literature/qnm_dataset.csv \
  --out-dir data/gwosc_events/qnm_literature_boundary \
  --d 4
```

Rama ESPRIT (alternativa):

```bash
python3 realdata_ringdown_to_stage02_boundary_dataset.py \
  --run-dir data/gwosc_events/GW150914/boundary \
  --ringdown-dirs ringdown \
  --out-dir data/gwosc_events/GW150914/boundary_dataset \
  --d 4
```

### B-5 · Inferencia con el motor (checkpoint de Ruta A)

```bash
python3 02_emergent_geometry_engine.py \
  --mode inference \
  --data-dir data/gwosc_events/qnm_literature_boundary \
  --output-dir data/gwosc_events/qnm_literature_boundary/02_emergent_geometry_engine \
  --checkpoint runs/<run_ruta_a>/02_emergent_geometry_engine/emergent_geometry_model.pt
```

### B-6 · Auditoría downstream

```bash
python3 03_discover_bulk_equations.py    --run-dir <run_dir>
python3 04_geometry_physics_contracts.py --run-dir <run_dir> \
  --data-dir data/gwosc_events/qnm_literature_boundary
```

---

## Ruta C — ELIMINADA (2026-04-20)

El carril ESPRIT + PySR/KAN + validación Kerr fue cerrado. La extracción
propia no identificaba limpiamente el modo (2,2,0) del strain real. Scripts
borrados: `02_poles_to_dataset.py`, `03_discover_qnm_equations.py`,
`04_kan_qnm_classifier.py`, `05_validate_qnm_kerr.py`. El input canónico de
QNM ahora viene de posteriors Bayesianos publicados (ver Ruta B-3).

---

## Estado de familias

Leer `family_status` antes de interpretar una salida como física fuerte.

| `family_status` | Significado |
|---|---|
| `canonical_strong` | Carril fuerte; actualmente solo `ads` con `--ads-boundary-mode gkpw` |
| `toy_sandbox` | Familia sintética/sandbox o observable fenomenológico |
| `realdata_surrogate` | Embedding derivado de ringdown real; no dual fuerte por sí solo |
| `non_holographic_surrogate` | Carril especial no holográfico, p. ej. Kerr |

---

## Tests

Smoke obligatorio tras tocar rutas, familias, ADS/GKPW o bridge real-data:

```bash
python3 -m pytest \
  tests/test_agmoo_ads_contract.py \
  tests/test_stage01_ads_gkpw_mode.py \
  tests/test_gkpw_ads_scalar_correlator.py \
  tests/test_realdata_bridge_saturation_detection.py \
  tests/test_realdata_bridge_g2_time_contracts.py \
  tests/test_g2_representation_contract.py \
  -v
```

Suite completa reducida:

```bash
python3 -m pytest tests/ -q
```

Tests relevantes por ruta:

| Ruta | Tests clave |
|---|---|
| A | `test_stage01_ads_gkpw_mode`, `test_agmoo_ads_contract`, `test_stage04_contract_runtime`, `test_stage08_contract_runtime` |
| B | `test_realdata_bridge_saturation_detection`, `test_realdata_bridge_g2_time_contracts`, `test_g2_representation_contract` |
| Común | `test_stage_utils_contract`, `test_common_contract_models`, `test_feature_support` |

Los tests que necesitan `torch` se saltan automáticamente en entornos sin GPU/backend instalado.
