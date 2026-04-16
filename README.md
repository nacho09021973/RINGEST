# RINGEST

Pipeline local para el análisis holográfico de señales de ringdown gravitacional.
Extrae polos QNM de eventos GWOSC, los mapea a geometrías AdS emergentes mediante
redes neuronales y regresión simbólica, y valida la estructura del espectro contra
las frecuencias Kerr tabuladas.

---

## Qué hace el pipeline

```
Señal de ringdown (LIGO/Virgo)
        │
        ▼
Extracción de polos QNM (ESPRIT)          ← 01_extract_ringdown_poles
        │
        ├─▶  Ruta A — Geometría emergente
        │    Geometría AdS sintética → motor neural → redescubrimiento de
        │    ecuaciones de Einstein y relación λ_SL = Δ(Δ−d)
        │
        ├─▶  Ruta B — Inferencia holográfica sobre eventos reales
        │    Embedding de ringdown real en el espacio de familias holográficas
        │
        └─▶  Ruta C — Cadena QNM simbólica
             Dataset QNM → regresión simbólica (PySR) → clasificador KAN
             → validación contra tabla Kerr (Berti 2009)
```

La única familia con `family_status = canonical_strong` es AdS con frontera
GKPW (`--ads-boundary-mode gkpw`). El resto son `toy_sandbox` o `realdata_surrogate`.

---

## Estructura del repo

```
RINGEST/
  # Scripts de pipeline (19 activos)
  00_download_gwosc_events.py          Ruta B — descarga NPZ de GWOSC
  00_load_ligo_data.py                 Ruta B — NPZ → HDF5 whitened
  01_generate_sandbox_geometries.py    Ruta A — geometrías ADS sintéticas
  01_extract_ringdown_poles.py         Rutas B, C — ESPRIT sobre la señal
  02_emergent_geometry_engine.py       Rutas A, B — motor neural (train/inference)
  02_poles_to_dataset.py               Ruta C — polos → qnm_dataset.csv
  03_discover_bulk_equations.py        Ruta A — PySR sobre geometría de bulk
  03_discover_qnm_equations.py         Ruta C — PySR sobre dataset QNM
  04_geometry_physics_contracts.py     Ruta A — contratos físicos (R<0, f≥0)
  04_kan_qnm_classifier.py             Ruta C — k-means + KAN + auto_symbolic
  05_analyze_bulk_equations.py         Ruta A — análisis de ecuaciones descubiertas
  05_validate_qnm_kerr.py              Ruta C — match vs tabla Kerr Berti 2009
  06_build_bulk_eigenmodes_dataset.py  Ruta A — Sturm-Liouville
  07_emergent_lambda_sl_dictionary.py  Ruta A — redescubrimiento λ_SL = Δ(Δ−d)
  08_build_holographic_dictionary.py   Ruta A — atlas holográfico completo
  09_real_data_and_dictionary_contracts.py  Ruta A — contratos finales
  realdata_ringdown_to_stage02_boundary_dataset.py  Ruta B — bridge polos→stage02
  # Librerías compartidas
  bulk_scalar_solver.py  family_registry.py  feature_support.py  stage_utils.py
  # Documentación
  PIPELINE_ROUTES.md          Mapa corto de las tres rutas
  instrucciones_pipeline.md   Comandos completos con flags
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
| PySR + Julia | A (`03_discover_bulk_equations`), C (`03_discover_qnm_equations`) | `pip install -e ".[pysr]"` |
| pykan + torch | C (`04_kan_qnm_classifier`) | `pip install kan torch` |
| scipy | C (clustering k-means) | `pip install scipy` |
| gwosc | B, C (fetch params automático) | `pip install gwosc` |

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

### Ruta B — datos reales GWOSC

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
python3 02_emergent_geometry_engine.py --mode inference \
  --data-dir data/gwosc_events/GW150914/boundary_dataset \
  --checkpoint runs/<run_ruta_a>/02_emergent_geometry_engine/emergent_geometry_model.pt
```

### Ruta C — cadena QNM (modo análisis, sin dependencias pesadas)

```bash
python3 02_poles_to_dataset.py      --runs-dir data/gwosc_events --params-csv catalog_params.csv
python3 03_discover_qnm_equations.py --dataset-csv runs/qnm_dataset/qnm_dataset.csv --analysis-only
python3 04_kan_qnm_classifier.py    --summary runs/qnm_symbolic/qnm_symbolic_summary.json --analysis-only
python3 05_validate_qnm_kerr.py     --summary runs/qnm_kan/qnm_kan_summary.json
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
