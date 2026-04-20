@AGENTS.md

# RINGEST — Instrucciones para Claude

Estas instrucciones complementan `AGENTS.md`. Si hay conflicto, manda `AGENTS.md`.

## Que es este repo

RINGEST es un pipeline de fisica computacional para:

- extraer polos QNM de datos reales GWOSC,
- convertirlos en observables y datasets fisicos,
- buscar relaciones empiricas con PySR/KAN,
- y, solo despues, conectarlos con el carril holografico.

La pregunta rectora en este repo es:

> "esto transforma datos reales en observables, relaciones o familias fisicas?"

Si no, no lo priorices.

## Prioridad de rutas

### Ruta C — ELIMINADA (2026-04-20)
El carril de extraccion ESPRIT + PySR/KAN + validacion Kerr fue cerrado:
la extraccion propia no identificaba limpiamente el modo (2,2,0) de strain
real. Scripts borrados: `02_poles_to_dataset.py`, `03_discover_qnm_equations.py`,
`04_kan_qnm_classifier.py`, `05_validate_qnm_kerr.py`. No intentes
reintroducirlos. Si el usuario pregunta por QNM empiricos, apunta a
`02b_literature_to_dataset.py`.

### Ruta B — carril activo
Puente desde datos reales (literatura QNM) a embedding/inferencia:

- `data/qnm_events_literature.yml` — YAML canonico de eventos + modos
- `02b_literature_to_dataset.py` — YAML -> qnm_dataset.csv
- `realdata_ringdown_to_stage02_boundary_dataset.py --dataset-csv ...` — bridge a stage02
- `02_emergent_geometry_engine.py --mode inference` — geometria emergente
- `03_discover_bulk_equations.py`, `04_geometry_physics_contracts.py` — auditoria downstream

La rama ESPRIT alternativa fue eliminada el 2026-04-20 junto con la ingesta
NPZ. Scripts borrados: `00_download_gwosc_events.py`, `00_load_ligo_data.py`,
`01_extract_ringdown_poles.py`, `run_batch_load.sh`. No los reintroduzcas.

### Ruta A — checkpoint-only (2026-04-20)
`01_generate_sandbox_geometries.py` fue eliminado. Ruta A sigue operativa
solo sobre el run congelado `runs/ads_gkpw_20260416_091407/`, que conserva
los H5 sandbox y el checkpoint entrenado. Ese checkpoint es el que alimenta
`--mode inference` en Ruta B. No intentes reintroducir el generador sandbox.

## Estado conceptual que Claude debe respetar

- `canonical_strong`: solo el carril ADS/GKPW fuerte
- `realdata_surrogate`: embedding derivado de ringdown real; no es dual fuerte
- `toy_sandbox`: familia sintetica o fenomenologica
- `non_holographic_surrogate`: carril Kerr u otros no holograficos

No confundas embedding, surrogate o clustering con evidencia de dualidad fuerte.

## Forma correcta de trabajar aqui

- Antes de proponer una edicion, inspecciona el archivo real.
- Si vas a modificar codigo, manten el cambio lo mas pequeno posible.
- Reutiliza scripts existentes antes de crear otros nuevos.
- Si existe ya un output fisico en disco, leelo antes de rerunear el analisis.
- No generes documentacion nueva salvo que el usuario lo pida o que el cambio fisico la haga imprescindible.

## Sesgos a evitar

- No derivar rapido hacia AdS, Lifshitz, hyperscaling u otros sandbox si la pregunta actual es sobre datos reales.
- No sustituir fisica por manifiestos, contratos o reorganizacion del repo.
- No vender `R²`, clustering o symbolic regression como resultado fisico si no estan amarrados a validacion Kerr o a una relacion interpretable.
- No sobrevender resultados con pocos eventos o subconjuntos pequenos.

## Como responder

- Responde en espanol.
- Se directo, tecnico y sin humo.
- Diferencia con claridad:
  - hecho verificado
  - inferencia
  - propuesta

## Plantilla preferida de analisis

- archivo:
- inputs reales:
- outputs reales:
- funcion fisica:
- dependencia toy/teorica:
- veredicto: RESCATAR / REESCRIBIR / ARCHIVAR
