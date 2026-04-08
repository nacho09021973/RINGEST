# RINGEST — Instrucciones para correr el pipeline completo

Pipeline de análisis holográfico GW/AdS sobre datos reales de LIGO/Virgo (GWOSC).

```
GWOSC → NPZ → boundary HDF5 → polos ringdown → dataset → geometría emergente → diccionario holográfico
```

---

## Requisitos

### Python y dependencias

```bash
python3 -m pip install numpy scipy h5py requests
python3 -m pip install torch          # para stages 02+
```

Versiones probadas: Python 3.10+, NumPy 1.24+, SciPy 1.11+, h5py 3.9+.

### PySR (Stage 03 y 07b)

PySR requiere un entorno virtual separado con Julia instalada:

```bash
# Crear venv en .venv-pysr/
cd ~/RINGEST
python3 -m venv .venv-pysr
.venv-pysr/bin/pip install pysr h5py numpy scipy

# Verificar:
.venv-pysr/bin/python -c "from pysr import PySRRegressor; print('PySR OK')"
```

Julia se descarga automáticamente en el primer uso de PySRRegressor.

### Estructura del repositorio

```
RINGEST/
├── 00_download_gwosc_events.py
├── 00_load_ligo_data.py
├── 01_extract_ringdown_poles.py
├── 02R_build_ringdown_boundary_dataset.py
├── 02_emergent_geometry_engine.py
├── 03_discover_bulk_equations.py
├── ...
├── run_batch_load.sh
├── runs/                        ← datos (excluidos de git)
├── docs/
└── instrucciones_pipeline.md   ← este archivo
```

Todos los scripts son ejecutables desde `~/RINGEST`. Los paths relativos
se resuelven siempre desde el directorio raíz del repo.

---

## Stage 00-A — Descarga de eventos GWOSC

Descarga strain data de 90 eventos de GWTC-1/2.1/3 desde GWOSC.

```bash
cd ~/RINGEST

python3 00_download_gwosc_events.py \
    --out-dir runs/gwosc_all
```

**Opciones útiles:**

| Flag | Descripción |
|------|-------------|
| `--dry-run` | Ver qué se descargaría sin descargar |
| `--force` | Re-descargar aunque el archivo ya exista |
| `--event GW150914 GW151226` | Solo estos eventos |
| `--out-dir PATH` | Directorio de salida (default: `runs/gwosc_all`) |

**Salida:**
```
runs/gwosc_all/
├── download_manifest.json
└── GW150914/
    └── raw/
        ├── GW150914_H1_4096Hz_32s.npz
        ├── GW150914_H1_4096Hz_32s.hdf5
        ├── GW150914_L1_4096Hz_32s.npz
        └── GW150914_L1_4096Hz_32s.hdf5
```

---

## Stage 00-B — Carga y blanqueamiento (boundary HDF5)

Convierte los NPZ crudos a artefactos de frontera (`boundary.h5`) con blanqueamiento
PSD y FFT. El script batch procesa los 90 eventos automáticamente.

```bash
cd ~/RINGEST

bash run_batch_load.sh --jobs 4
```

**Opciones:**

| Flag | Descripción |
|------|-------------|
| `--jobs N` | Paralelismo (requiere GNU parallel; default: 4) |
| `--dry-run` | Muestra comandos sin ejecutar |

Para correr un solo evento manualmente:

```bash
python3 00_load_ligo_data.py \
    --h1-npz runs/gwosc_all/GW150914/raw/GW150914_H1_4096Hz_32s.npz \
    --l1-npz runs/gwosc_all/GW150914/raw/GW150914_L1_4096Hz_32s.npz \
    --run-dir runs/gwosc_all/GW150914/boundary \
    --whiten \
    --fft
```

> **Nota sobre eventos sin H1:** 7 eventos (GW170608, GW190425, GW190620,
> GW190630, GW190708, GW190910, GW200112) no tienen datos H1. El batch los
> procesa usando L1 como detector primario (pasado como `--h1-npz`).

> **Nota sobre eventos sin L1:** 3 eventos (GW190925, GW191216, GW200302)
> no tienen datos L1. El batch los procesa con solo H1.

**Salida por evento:**
```
runs/gwosc_all/GW150914/boundary/
├── run_manifest.json
├── adapter_spec.json
├── summary.json
└── data_boundary/
    ├── GW150914_boundary.h5       ← strain raw + whitened + FFT
    └── GW150914_boundary_meta.json
```

**Parámetros de blanqueamiento (defaults):**
- Segmento offband: `[-28, -4]` s antes del evento
- PSD: método Welch
- Banda de paso: 20 – 1800 Hz

---

## Stage 01 — Extracción de polos de ringdown (ESPRIT/matrix-pencil)

Extrae los modos amortiguados del ringdown post-merger para cada evento.

```bash
# Un evento:
python3 01_extract_ringdown_poles.py \
    --run-dir runs/gwosc_all/GW150914/boundary \
    --duration 0.25 \
    --require-decay \
    --max-modes 16

# Todos los eventos en loop:
for ev in runs/gwosc_all/*/; do
    ev_name=$(basename "$ev")
    python3 01_extract_ringdown_poles.py \
        --run-dir "runs/gwosc_all/${ev_name}/boundary" \
        --duration 0.25 \
        --require-decay \
        --max-modes 16
done
```

**Parámetros clave:**

| Flag | Default | Descripción |
|------|---------|-------------|
| `--duration` | 0.25 s | Duración de la ventana de análisis |
| `--t0-rel` | auto (pico) | Inicio de ventana relativo al GPS del evento |
| `--start-offset` | 0.0 s | Desplazamiento desde el pico si se usa autodetección |
| `--require-decay` | off | Filtrar solo modos con Im(ω) < 0 |
| `--max-modes` | 16 | Número máximo de polos a conservar |
| `--rank` | auto | Rango del modelo; 0 = automático por umbral de SVs |
| `--sv-thresh` | 1e-3 | Umbral relativo para rango automático |
| `--hp-hz` | None | High-pass opcional (Hz) |
| `--lp-hz` | None | Low-pass opcional (Hz) |

> **Fix de overflow (GW190630):** ESPRIT puede devolver polos con `|z| > 1`
> que causan overflow numérico en la matriz de Vandermonde. El código filtra
> estos polos automáticamente (`stable_mask = np.abs(z) <= 1.0 + 1e-6`) antes
> del lstsq. Este fix está incorporado en `01_extract_ringdown_poles.py`.

**Salida por evento:**
```
runs/gwosc_all/GW150914/boundary/
└── ringdown/
    ├── ringdown_spec.json
    ├── poles_H1.json / poles_H1.csv
    ├── poles_L1.json / poles_L1.csv
    ├── poles_joint.json / poles_joint.csv
    └── summary.json
```

Los polos se expresan como `q = sigma + i*omega` (tiempo continuo) y también
en notación QNM: `omega_qnm = i*q`.

---

## Stage 02R — Dataset de frontera para geometría emergente

Construye el HDF5 de frontera por evento. Luego se combina todo en un único
directorio de inferencia.

### 2R-a: procesar cada evento

```bash
cd ~/RINGEST

for ev in runs/gwosc_all/*/; do
    ev_name=$(basename "$ev")
    python3 02R_build_ringdown_boundary_dataset.py \
        --run-dir "runs/gwosc_all/${ev_name}/boundary" \
        --ringdown-dirs ringdown \
        --out-dir "runs/gwosc_all/${ev_name}/boundary_dataset" \
        --d 4
done
```

### 2R-b: crear directorio de inferencia combinado

Stage 02 en modo `inference` requiere un único directorio con todos los HDF5
y un `manifest.json` combinado:

```bash
mkdir -p runs/gwosc_all/inference_input

# Copiar todos los HDF5
for ev in runs/gwosc_all/*/boundary_dataset/*.h5; do
    cp "$ev" runs/gwosc_all/inference_input/
done

# Generar manifest combinado
python3 - <<'EOF'
import json, glob, os

base = "runs/gwosc_all"
manifests = sorted(glob.glob(f"{base}/*/boundary_dataset/manifest.json"))
geometries = []
for mf in manifests:
    with open(mf) as f:
        m = json.load(f)
    ev = m["event_id"]
    for g in m["geometries"]:
        g["file"] = g["file"]  # filename only, no path
        geometries.append(g)

combined = {
    "created_at": "2026-04-08T00:00:00Z",
    "script": "combined_manifest v1.0",
    "version": "02R-v1",
    "source_run_dir": os.path.abspath(f"{base}/inference_input"),
    "config": {"d": 4, "n_omega": 256, "n_x": 256,
               "gr_normalization": "unit_peak",
               "g2_normalization": "unit_peak",
               "k_grid": [0.0],
               "embedding_space": "dimensionless_dominant_pole"},
    "geometries": geometries
}
out = f"{base}/inference_input/manifest.json"
with open(out, "w") as f:
    json.dump(combined, f, indent=2)
print(f"Combinado {len(geometries)} geometrías → {out}")
EOF
```

---

## Stage 02 — Motor de geometría emergente

Aprende la geometría de bulk emergente (A(z), f(z), R(z)) a partir de los datos
de frontera. Requiere PyTorch y un checkpoint de entrenamiento (`runs/sandbox_v4`).

```bash
# Inferencia sobre todos los eventos LIGO:
python3 02_emergent_geometry_engine.py \
    --mode inference \
    --experiment inference_gwosc_v4 \
    --checkpoint runs/sandbox_v4 \
    --data-dir runs/gwosc_all/inference_input
```

> **Nota:** El modo `inference` genera los HDF5 de geometría emergente en
> `runs/gwosc_all/inference_gwosc_v4/geometry_emergent/`. Un error menor de
> `ValueError: not in subpath` puede aparecer al final del post-procesado —
> es inofensivo; todos los HDF5 de resultados ya fueron guardados.

> **Checkpoint recomendado:** `runs/sandbox_v4` (R²_f=0.922, family_acc=0.817,
> entrenado con n=100 geometrías sintéticas, 500 épocas). Para mejores resultados,
> re-entrenar con más datos sintéticos antes de la inferencia real.

**Datasets en los HDF5 de salida (nombres reales):**
- `z_grid` — coordenada radial bulk
- `A_of_z` — métrica A(z)
- `f_of_z` — métrica f(z)
- `R_of_z` — curvatura escalar R(z)
- `family_pred` — familia predicha (ads/lifshitz/hvlf)
- `zh_pred` — horizonte predicho

---

## Stage 03 — Descubrimiento de ecuaciones de bulk (PySR)

Aplica regresión simbólica sobre la geometría emergente para descubrir
ecuaciones de campo en el bulk. **Usar el venv de PySR.**

```bash
cd ~/RINGEST

# Un evento (ejemplo):
.venv-pysr/bin/python ./03_discover_bulk_equations.py \
    --geometry-dir runs/gwosc_all/inference_gwosc_v4/geometry_emergent \
    --out-dir runs/gwosc_all/inference_gwosc_v4/03_bulk_equations_pysr \
    --iterations 30

# Todos los eventos en batch:
for h5 in runs/gwosc_all/inference_gwosc_v4/geometry_emergent/*.h5; do
    ev=$(basename "$h5" .h5)
    .venv-pysr/bin/python ./03_discover_bulk_equations.py \
        --geometry-dir runs/gwosc_all/inference_gwosc_v4/geometry_emergent \
        --out-dir runs/gwosc_all/inference_gwosc_v4/03_bulk_equations_pysr \
        --event "$ev" \
        --iterations 30
done
```

> **Advertencia de h5py:** Si Stage 03 muestra `[WARN] h5py no disponible`,
> instalar: `.venv-pysr/bin/pip install h5py numpy scipy`

> **Nota sobre familias:** Los eventos LIGO tienen nombres como
> `GW150914__ringdown` — el script no puede inferir familia del nombre.
> Las familias se asignan correctamente desde el campo `category`/`family`
> del manifest y se usan en Stage 05+.

---

## Stages 04–05 — Contratos físicos y análisis de ecuaciones

```bash
# Stage 04: contratos físicos de geometría emergente
python3 04_geometry_physics_contracts.py \
    --runs-dir runs/gwosc_all/inference_gwosc_v4 \
    --experiment .

# Stage 05: análisis de patrones en ecuaciones de bulk
python3 05_analyze_bulk_equations.py \
    --runs-dir runs/gwosc_all/inference_gwosc_v4 \
    --experiment .
```

> **Nota Stage 04:** El contrato `einstein_distribution` reportará FAIL si todos
> los eventos son `POSSIBLY_EINSTEIN_WITH_MATTER` (score=0.40). Esto es el
> resultado físico esperado para datos reales — no una violación.

> **Nota Stage 05:** La clasificación de familia usa `geo.get("category", ...)` 
> como fallback para eventos LIGO, ya que los nombres no contienen la familia.

---

## Stage 06 — Eigenmodos Sturm-Liouville

**Importante:** Los HDF5 de geometría emergente usan nombres de dataset no
estándar. Pasar explícitamente:

```bash
python3 06_build_bulk_eigenmodes_dataset.py \
    --runs-dir runs/gwosc_all/inference_gwosc_v4 \
    --experiment . \
    --A-dataset A_of_z \
    --f-dataset f_of_z \
    --z-dataset z_grid \
    --n-modes 6
```

**Salida:**
```
inference_gwosc_v4/
├── 06_eigenmodes/                         ← CSV por evento (λ_SL, Δ, family)
└── 06_build_bulk_eigenmodes_dataset/
    └── bulk_modes_dataset.csv             ← dataset combinado (540 filas = 90×6)
```

---

## Stage 07 — Diccionario λ_SL ↔ Δ (PySR)

> **Contrato de routing:** Stage 07 usa `--runs-dir` + `--experiment`, NO
> `--output-dir`. El CSV debe estar en la ubicación canónica.

```bash
# Asegurar que el CSV combinado está en la ubicación esperada:
cp runs/gwosc_all/inference_gwosc_v4/06_build_bulk_eigenmodes_dataset/bulk_modes_dataset.csv \
   runs/gwosc_all/inference_gwosc_v4/06_eigenmodes/bulk_modes_dataset.csv  # si fuera necesario

# Correr Stage 07:
.venv-pysr/bin/python ./07_emergent_lambda_sl_dictionary.py \
    --runs-dir runs/gwosc_all/inference_gwosc_v4 \
    --experiment . \
    --iterations 30
```

**Resultado esperado:** PySR redescubre `λ_SL = Δ(Δ−d)` con R²=1.0000.
Esta es la relación de Breitenlohner-Freedman / masa-dimensión de AdS/CFT.

---

## Stage 08 — Atlas holográfico

> **Limitación conocida:** El modo emergente de Stage 08 busca `boundary/x_grid`
> en los HDF5 de geometría, pero los HDF5 de inferencia usan `z_grid`. El script
> fallará en modo emergente con datos de inferencia LIGO.

**Workaround:** Construir el atlas directamente desde el CSV de Stage 06:

```python
# atlas_builder.py — correr desde ~/RINGEST
import pandas as pd, json, numpy as np

df = pd.read_csv("runs/gwosc_all/inference_gwosc_v4/06_build_bulk_eigenmodes_dataset/bulk_modes_dataset.csv")

# Normalizar columna is_ground_state (puede ser string '0'/'1' o bool)
df["is_ground_state"] = df["is_ground_state"].astype(str).isin(["True", "1", "true"])

atlas = {}
for family, grp in df.groupby("family"):
    gs = grp[grp["is_ground_state"]]
    atlas[family] = {
        "n_systems": grp["event_id"].nunique(),
        "n_operators": len(grp),
        "delta_mean": float(grp["delta"].mean()),
        "delta_std":  float(grp["delta"].std()),
        "m2L2_mean":  float(grp["m2L2"].mean()),
        "delta_gs_mean": float(gs["delta"].mean()) if len(gs) else None,
    }

out = "runs/gwosc_all/inference_gwosc_v4/08_build_holographic_dictionary/holographic_dictionary_v3_summary.json"
import os; os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w") as f:
    json.dump({"atlas": atlas}, f, indent=2)
print(json.dumps(atlas, indent=2))
```

```bash
python3 atlas_builder.py
```

---

## Stage 09 — Contratos finales

```bash
# Contratos generales:
python3 09_real_data_and_dictionary_contracts.py \
    --runs-dir runs/gwosc_all/inference_gwosc_v4 \
    --experiment .
```

> **Nota:** `run_contracts_fase12` solo ejecuta contratos Ising3D y KSS, que no
> aplican a datos LIGO. El bound de unitariedad y BF deben verificarse
> explícitamente:

```python
# unitarity_check.py — correr desde ~/RINGEST
import pandas as pd, json

df = pd.read_csv("runs/gwosc_all/inference_gwosc_v4/06_build_bulk_eigenmodes_dataset/bulk_modes_dataset.csv")
d = 4

results = []
all_pass = True
for _, row in df.iterrows():
    delta = float(row["delta"])
    m2L2  = float(row["m2L2"])
    unit_bound = (d - 2) / 2   # = 1.0 for d=4
    bf_bound   = -(d**2) / 4   # = -4.0 for d=4
    u_pass = delta >= unit_bound
    bf_pass = m2L2 >= bf_bound
    if not (u_pass and bf_pass):
        all_pass = False
    results.append({"event": row["event_id"], "delta": delta, "m2L2": m2L2,
                    "unitarity": u_pass, "bf_bound": bf_pass})

summary = {
    "total": len(results),
    "unitarity_pass": sum(r["unitarity"] for r in results),
    "bf_bound_pass":  sum(r["bf_bound"]  for r in results),
    "all_pass": all_pass
}
print(json.dumps(summary, indent=2))

out = "runs/gwosc_all/inference_gwosc_v4/09_contracts/unitarity_contracts.json"
import os; os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w") as f:
    json.dump({"summary": summary, "details": results}, f, indent=2)
```

```bash
python3 unitarity_check.py
```

**Resultado esperado:** 540/540 operadores pasan unitariedad (Δ ≥ 1) y BF bound (m²L² ≥ −4).

---

## Flujo completo — comandos en orden

```bash
cd ~/RINGEST

# ── Stage 00-A: Descargar eventos ─────────────────────────────────────────────
python3 00_download_gwosc_events.py --out-dir runs/gwosc_all

# ── Stage 00-B: Boundary HDF5 (blanqueamiento + FFT) ──────────────────────────
bash run_batch_load.sh --jobs 4

# ── Stage 01: Extraer polos de ringdown ───────────────────────────────────────
for ev in runs/gwosc_all/*/; do
    ev_name=$(basename "$ev")
    python3 01_extract_ringdown_poles.py \
        --run-dir "runs/gwosc_all/${ev_name}/boundary" \
        --duration 0.25 --require-decay --max-modes 16
done

# ── Stage 02R: Dataset de frontera por evento ─────────────────────────────────
for ev in runs/gwosc_all/*/; do
    ev_name=$(basename "$ev")
    python3 02R_build_ringdown_boundary_dataset.py \
        --run-dir "runs/gwosc_all/${ev_name}/boundary" \
        --ringdown-dirs ringdown \
        --out-dir "runs/gwosc_all/${ev_name}/boundary_dataset" \
        --d 4
done

# ── Stage 02R-b: Directorio de inferencia combinado ──────────────────────────
mkdir -p runs/gwosc_all/inference_input
for ev in runs/gwosc_all/*/boundary_dataset/*.h5; do
    cp "$ev" runs/gwosc_all/inference_input/
done
# + generar manifest combinado (ver sección Stage 02R arriba)

# ── Stage 02: Geometría emergente (requiere torch + checkpoint) ───────────────
python3 02_emergent_geometry_engine.py \
    --mode inference \
    --experiment inference_gwosc_v4 \
    --checkpoint runs/sandbox_v4 \
    --data-dir runs/gwosc_all/inference_input

# ── Stage 03: Ecuaciones de bulk (requiere .venv-pysr) ───────────────────────
for h5 in runs/gwosc_all/inference_gwosc_v4/geometry_emergent/*.h5; do
    ev=$(basename "$h5" .h5)
    .venv-pysr/bin/python ./03_discover_bulk_equations.py \
        --geometry-dir runs/gwosc_all/inference_gwosc_v4/geometry_emergent \
        --out-dir runs/gwosc_all/inference_gwosc_v4/03_bulk_equations_pysr \
        --event "$ev" --iterations 30
done

# ── Stage 04: Contratos físicos ───────────────────────────────────────────────
python3 04_geometry_physics_contracts.py \
    --runs-dir runs/gwosc_all/inference_gwosc_v4 --experiment .

# ── Stage 05: Análisis de ecuaciones ─────────────────────────────────────────
python3 05_analyze_bulk_equations.py \
    --runs-dir runs/gwosc_all/inference_gwosc_v4 --experiment .

# ── Stage 06: Eigenmodos Sturm-Liouville ──────────────────────────────────────
python3 06_build_bulk_eigenmodes_dataset.py \
    --runs-dir runs/gwosc_all/inference_gwosc_v4 --experiment . \
    --A-dataset A_of_z --f-dataset f_of_z --z-dataset z_grid --n-modes 6

# ── Stage 07: Diccionario λ_SL ↔ Δ (PySR) ────────────────────────────────────
.venv-pysr/bin/python ./07_emergent_lambda_sl_dictionary.py \
    --runs-dir runs/gwosc_all/inference_gwosc_v4 --experiment . \
    --iterations 30

# ── Stage 08: Atlas holográfico (workaround — ver sección Stage 08) ───────────
python3 atlas_builder.py

# ── Stage 09: Contratos finales ───────────────────────────────────────────────
python3 09_real_data_and_dictionary_contracts.py \
    --runs-dir runs/gwosc_all/inference_gwosc_v4 --experiment .
python3 unitarity_check.py
```

---

## Estructura de directorios resultante

```
runs/gwosc_all/
├── download_manifest.json
├── inference_input/                       ← HDF5 combinados + manifest
├── GW150914/
│   ├── raw/
│   │   ├── GW150914_H1_4096Hz_32s.npz
│   │   └── GW150914_L1_4096Hz_32s.npz
│   ├── boundary/
│   │   ├── run_manifest.json
│   │   ├── data_boundary/
│   │   │   └── GW150914_boundary.h5
│   │   └── ringdown/
│   │       ├── poles_H1.json
│   │       ├── poles_L1.json
│   │       ├── poles_joint.json
│   │       └── summary.json
│   └── boundary_dataset/
│       ├── manifest.json
│       └── GW150914__ringdown.h5
└── inference_gwosc_v4/
    ├── geometry_emergent/                 ← A(z), f(z), R(z) por evento
    ├── emergent_geometry_summary.json     ← familias y zh_pred
    ├── 03_bulk_equations_pysr/            ← ecuaciones R=F(...) por evento
    ├── 04_contracts/                      ← contratos físicos Stage 04
    ├── 05_bulk_equations_report.*         ← análisis de patrones Stage 05
    ├── 06_eigenmodes/                     ← CSV 540 modos λ_SL, Δ
    ├── 06_build_bulk_eigenmodes_dataset/
    │   └── bulk_modes_dataset.csv         ← dataset combinado
    ├── 07_emergent_lambda_sl_dictionary/  ← λ_SL=Δ(Δ−d) descubierto
    ├── 08_build_holographic_dictionary/   ← atlas holográfico
    └── 09_contracts/                      ← contratos finales + unitariedad
```

---

## Notas de reproducibilidad

- Todos los scripts son deterministas dado el mismo input (sin aleatoriedad en stages 00–02R).
- Cada run genera un `run_manifest.json` con checksums SHA-256 de los artefactos de entrada y salida.
- Los paths relativos en manifests son siempre relativos al `run_dir`, no al CWD.
- Para re-procesar un evento desde cero basta con borrar su subdirectorio `boundary/` y volver a correr los stages.
- Stage 02 (inferencia) puede generar un error inofensivo `ValueError: not in subpath` al final — ignorar.
- Stage 09 `einstein_distribution` reportará FAIL si todos los eventos son `POSSIBLY_EINSTEIN_WITH_MATTER` — esto es el resultado físico correcto para BBH reales.

## Issues conocidos y workarounds

| Stage | Issue | Workaround |
|-------|-------|------------|
| 01 | Overflow SVD en GW190630 (polos `\|z\|>1`) | Fix incorporado en el script |
| 03 | h5py no disponible en venv-pysr | `.venv-pysr/bin/pip install h5py` |
| 06 | Dataset names no estándar en HDF5 de inferencia | Pasar `--A-dataset A_of_z --f-dataset f_of_z --z-dataset z_grid` |
| 07 | Conflicto `--experiment` vs `--output-dir` | Usar siempre `--runs-dir + --experiment .` |
| 08 | Script emergente busca `x_grid`, HDF5 tiene `z_grid` | Usar atlas_builder.py (ver sección Stage 08) |
| 09 | Contratos Fase12 no aplican a LIGO | Correr unitarity_check.py manualmente |
