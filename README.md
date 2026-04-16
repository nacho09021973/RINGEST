# RINGEST

Pipeline local para generar datos ADS/GKPW, procesar eventos GWOSC y pasar ambos
carriles por el motor de geometria emergente.

## Lo primero

- Los datos pesados viven en `data/gwosc_events/`.
- `data/` y `runs/` estan en `.gitignore`.
- `runs/` es desechable: se usa solo para experimentos nuevos, checkpoints y
  resultados temporales.
- `configs/theory_dictionary/theory_dictionary_v1.json` es configuracion minima
  del stage 08; no es un carril lateral.
- El orden de scripts esta en [PIPELINE_ROUTES.md](/home/ignac/RINGEST/PIPELINE_ROUTES.md).
- El manual de ejecucion esta en [instrucciones_pipeline.md](/home/ignac/RINGEST/instrucciones_pipeline.md).

## Instalacion

```bash
cd /home/ignac/RINGEST
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -e . --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple
```

PySR es opcional para busqueda simbolica:

```bash
. .venv/bin/activate
pip install -e ".[pysr]" --extra-index-url https://pypi.org/simple
```

## Rutas principales

### Sandbox ADS/GKPW

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

ADS debe ejecutarse en modo `--ads-boundary-mode gkpw`. No usar el modo toy para
el carril canonico.

Los manifests/HDF5 escriben `family_status`. Actualmente solo `ads` con GKPW es
`canonical_strong`; el resto de familias sinteticas son `toy_sandbox`.

### Datos reales GWOSC

```text
00_download_gwosc_events.py
-> 00_load_ligo_data.py
-> 01_extract_ringdown_poles.py
-> realdata_ringdown_to_stage02_boundary_dataset.py
-> 02_emergent_geometry_engine.py --mode inference
```

Los eventos canonicos y el layout local estan en
[docs/canonical_events.md](/home/ignac/RINGEST/docs/canonical_events.md).

## Documentacion minima

- [PIPELINE_ROUTES.md](/home/ignac/RINGEST/PIPELINE_ROUTES.md): orden de scripts.
- [instrucciones_pipeline.md](/home/ignac/RINGEST/instrucciones_pipeline.md): comandos para correr.
- [docs/canonical_events.md](/home/ignac/RINGEST/docs/canonical_events.md): datos y eventos canonicos.
- [docs/manual_pipeline_ads_gkpw.md](/home/ignac/RINGEST/docs/manual_pipeline_ads_gkpw.md): smoke ADS/GKPW verificado.
