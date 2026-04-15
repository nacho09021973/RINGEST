# Smoke ADS/GKPW

Manual minimo para correr el carril ADS completo. ADS canonico usa
`--ads-boundary-mode gkpw`; no usar toy para esta ruta.

## Entorno

```bash
cd /home/ignac/RINGEST
. .venv/bin/activate
```

Si `.venv` no existe:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -e . --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple
```

## Smoke rapido

```bash
RUN_DIR=runs/ads_gkpw_smoke_$(date +%Y%m%d_%H%M%S)

python 01_generate_sandbox_geometries.py \
  --run-dir "$RUN_DIR" \
  --ads-only \
  --ads-boundary-mode gkpw \
  --quick-test \
  --seed 42 \
  --n-z 256 \
  --n-operators 2

python 02_emergent_geometry_engine.py \
  --run-dir "$RUN_DIR" \
  --data-dir "$RUN_DIR/01_generate_sandbox_geometries" \
  --mode train \
  --n-epochs 5 \
  --batch-size 2 \
  --device cpu \
  --seed 42

python 03_discover_bulk_equations.py \
  --run-dir "$RUN_DIR" \
  --geometry-dir "$RUN_DIR/02_emergent_geometry_engine/geometry_emergent" \
  --niterations 5 \
  --maxsize 10 \
  --d 3

python 04_geometry_physics_contracts.py --run-dir "$RUN_DIR"
python 05_analyze_bulk_equations.py --run-dir "$RUN_DIR"
python 06_build_bulk_eigenmodes_dataset.py --run-dir "$RUN_DIR" --n-eigs 3 --delta-uv-source solver
```

## Verificacion esperada

- Stage 01 escribe datos con `ads_boundary_mode = gkpw`.
- Stage 02 entrena y genera `02_emergent_geometry_engine/geometry_emergent/`.
- Stage 03 produce resumen de ecuaciones.
- Stage 04-06 terminan sin error en el smoke.

El smoke pequeno no pretende validar fisica final; solo prueba que el pipeline
arranca de punta a punta.
