# RINGEST

Pipeline local para el análisis holográfico de señales de ringdown gravitacional.
Toma QNM de eventos GWOSC (desde posteriors Bayesianos publicados en literatura)
y los mapea a geometrías AdS emergentes mediante redes neuronales y regresión
simbólica.

---

## Qué hace el pipeline

```
QNM de literatura (posteriors Bayesianos LVC/Isi/Giesler/Capano/pyRing)
        │
        ▼
data/qnm_events_literature.yml → 02b_literature_to_dataset.py → qnm_dataset.csv
        │
        ├─▶  Ruta A — Geometría emergente
        │    Geometría AdS sintética → motor neural → redescubrimiento de
        │    ecuaciones de Einstein y relación λ_SL = Δ(Δ−d)
        │
        └─▶  Ruta B — Inferencia holográfica sobre eventos reales
             Bridge a stage02 → 02_emergent_geometry_engine --mode inference
             → 03_discover_bulk_equations → 04_geometry_physics_contracts

Ruta C (ESPRIT + PySR/KAN + validación Kerr) fue eliminada el 2026-04-20:
la extracción propia no identificaba limpiamente el (2,2,0) de strain real.
```

La única familia con `family_status = canonical_strong` es AdS con frontera
GKPW (`--ads-boundary-mode gkpw`). El resto son `toy_sandbox` o `realdata_surrogate`.

---

## Estructura del repo

```
RINGEST/
  # Scripts de pipeline (15 activos; Ruta C eliminada 2026-04-20)
  00_download_gwosc_events.py          Ruta B — descarga NPZ de GWOSC
  00_load_ligo_data.py                 Ruta B — NPZ → HDF5 whitened
  01_generate_sandbox_geometries.py    Ruta A — geometrías ADS sintéticas
  01_extract_ringdown_poles.py         Ruta B — ESPRIT (rama alternativa, conservada)
  02_emergent_geometry_engine.py       Rutas A, B — motor neural (train/inference)
  02b_literature_to_dataset.py         Ruta B — YAML literatura → qnm_dataset.csv
  03_discover_bulk_equations.py        Ruta A — PySR sobre geometría de bulk
  04_geometry_physics_contracts.py     Ruta A — contratos físicos (R<0, f≥0)
  05_analyze_bulk_equations.py         Ruta A — análisis de ecuaciones descubiertas
  06_build_bulk_eigenmodes_dataset.py  Ruta A — Sturm-Liouville
  07_emergent_lambda_sl_dictionary.py  Ruta A — redescubrimiento λ_SL = Δ(Δ−d)
  08_build_holographic_dictionary.py   Ruta A — atlas holográfico completo
  09_real_data_and_dictionary_contracts.py  Ruta A — contratos finales
  realdata_ringdown_to_stage02_boundary_dataset.py  Ruta B — bridge a stage02
  # Librerías compartidas
  bulk_scalar_solver.py  family_registry.py  feature_support.py  stage_utils.py
  # Documentación
  PIPELINE_ROUTES.md          Mapa corto de las rutas
  instrucciones_pipeline.md   Comandos completos con flags
  data/qnm_events_literature.yml   Fuente canónica de QNM (literatura)
  docs/
  configs/
  contracts/
  tools/
  _archive/   Scripts retirados (no borrados del historial git)
```

---

## Instalación

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

Dependencias opcionales por ruta:

| Componente | Ruta | Instalar con |
|---|---|---|
| PyTorch | A (entrenamiento), B (inferencia) | `pip install -e ".[gpu]"` |
| PySR + Julia | A (`03_discover_bulk_equations`) | `pip install -e ".[pysr]"` |
| gwosc | B (descarga de eventos, rama ESPRIT) | `pip install gwosc` |
| pyyaml | B (lectura de YAML literatura) | `pip install pyyaml` |

Los scripts con dependencias opcionales aceptan `--analysis-only` para ejecutarse
sin ellas y escribir igualmente su contrato de salida JSON.

---

## Uso rápido

### Ruta A — sandbox ADS/GKPW

```bash
RUN=runs/ads_$(date +%Y%m%d)

python3 01_generate_sandbox_geometries.py --run-dir $RUN --ads-only --ads-boundary-mode gkpw
python3 02_emergent_geometry_engine.py    --run-dir $RUN --mode train
python3 03_discover_bulk_equations.py     --run-dir $RUN
python3 04_geometry_physics_contracts.py  --run-dir $RUN
python3 05_analyze_bulk_equations.py      --run-dir $RUN
python3 06_build_bulk_eigenmodes_dataset.py --run-dir $RUN
python3 07_emergent_lambda_sl_dictionary.py --run-dir $RUN
python3 08_build_holographic_dictionary.py  --run-dir $RUN
python3 09_real_data_and_dictionary_contracts.py --run-dir $RUN --phase both
```

### Ruta B — datos reales (carril literatura, activo)

```bash
python3 02b_literature_to_dataset.py \
  --sources data/qnm_events_literature.yml \
  --out runs/qnm_dataset_literature
python3 realdata_ringdown_to_stage02_boundary_dataset.py \
  --dataset-csv runs/qnm_dataset_literature/qnm_dataset.csv \
  --out-dir data/gwosc_events/qnm_literature_boundary \
  --d 4
python3 02_emergent_geometry_engine.py --mode inference \
  --data-dir data/gwosc_events/qnm_literature_boundary \
  --checkpoint runs/<run_ruta_a>/02_emergent_geometry_engine/emergent_geometry_model.pt
python3 03_discover_bulk_equations.py    --run-dir <run_dir>
python3 04_geometry_physics_contracts.py --run-dir <run_dir> --data-dir data/gwosc_events/qnm_literature_boundary
```

Rama ESPRIT alternativa (conservada, no activa):

```bash
python3 00_download_gwosc_events.py --out-dir data/gwosc_events \
  --event GW150914 GW151012 GW170104
bash run_batch_load.sh --jobs 4
python3 01_extract_ringdown_poles.py --run-dir data/gwosc_events/GW150914/boundary
python3 realdata_ringdown_to_stage02_boundary_dataset.py \
  --run-dir data/gwosc_events/GW150914/boundary \
  --ringdown-dirs ringdown \
  --out-dir data/gwosc_events/GW150914/boundary_dataset \
  --d 4
```

---

## Documentación

| Archivo | Contenido |
|---|---|
| [PIPELINE_ROUTES.md](PIPELINE_ROUTES.md) | Mapa de las tres rutas |
| [instrucciones_pipeline.md](instrucciones_pipeline.md) | Comandos completos con todos los flags |
| [docs/canonical_events.md](docs/canonical_events.md) | Eventos canónicos de prueba |
| [docs/manual_pipeline_ads_gkpw.md](docs/manual_pipeline_ads_gkpw.md) | Smoke test ADS/GKPW verificado |

---

## Tests

```bash
python3 -m pytest tests/ -q
```

Smoke obligatorio tras cambios en rutas, familias o bridge real-data:

```bash
python3 -m pytest \
  tests/test_agmoo_ads_contract.py \
  tests/test_stage01_ads_gkpw_mode.py \
  tests/test_gkpw_ads_scalar_correlator.py \
  tests/test_realdata_bridge_saturation_detection.py \
  tests/test_g2_representation_contract.py -v
```
