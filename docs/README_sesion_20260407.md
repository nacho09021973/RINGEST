# Sesión 2026-04-07 — Estado del proyecto RINGEST

## Qué se hizo hoy

### 1. Diagnóstico inicial
- `RINGEST` solo tenía JSON derivados de un run previo de `ringhier`, sin el sustrato real.
- Conclusión: los 52 GB de `ringhier/data/` son observacionales (GWTC). Los pipelines `01→02→03` de `malda/` son **completamente autónomos** — generan geometrías sintéticas sin leer esos datos.
- El bloqueo era solo para `01_extract_ringdown_poles.py` (que sí lee strain GWTC).

---

### 2. Cadena sandbox ejecutada de cero

```
01_generate_sandbox_geometries.py  →  sandbox_v1  (160 universos, seed=42)
02_emergent_geometry_engine.py     →  sandbox_v1  (100 epochs)  A_r2=0.025, f_r2=0.89
02_emergent_geometry_engine.py     →  sandbox_v2  (500 epochs)  A_r2=0.447, f_r2=0.928
03_discover_bulk_equations.py      →  sandbox_v1/v2
```

Familias sandbox: `ads`, `lifshitz`, `hyperscaling`, `deformed`, `dpbrane`, `unknown`  
160 geometrías con jitter de parámetros (z_h, d, θ, z_dyn).

**Fix aplicado**: `ctx.write_manifest()` sobreescribía el manifest de geometrías.  
Solución: `01` ahora escribe `geometries_manifest.json` (separado del `manifest.json` de stage_utils).  
`02` lee `geometries_manifest.json` primero.

**Fix numpy**: `numpy` y `h5py` añadidos a imports de módulo en `01_generate_sandbox_geometries.py`.

---

### 3. Primera prueba real: GW150914

Descargado strain 4096 Hz de GWOSC (32s, H1+L1).  
Instalado `gwpy` para blanqueo.

Pipeline completo:
```
00_load_ligo_data.py        →  boundary.h5
02R_build_...dataset.py     →  embeddings G_R, G2
02_emergent_geometry_engine →  inference  →  family=hyperscaling, z_h≈1.08
03_discover_bulk_equations  →  Einstein score=0.40 (POSSIBLY_EINSTEIN_WITH_MATTER)
```

Eventos procesados: GW150914, GW170814, GW170823, GW151226  
Resultado uniforme: **todos clasifican como `hyperscaling`**.

---

### 4. Diagnóstico del clasificador

**Test A** (sandbox holográfico completo → inference):  
→ 100% accuracy. El modelo discrimina perfectamente cuando tiene datos holográficos.

**Test B** (polos sintéticos de distintas familias → 02R → inference):  
→ Todo → `hyperscaling`. Saturación.

**Causa raíz identificada en dos capas**:

**Capa 1 — Features de operadores**  
`build_feature_vector` usa 4 features de operadores (n_ops, Δ_min, Δ_max, Δ_mean).  
Sandbox: Δ∈[2,5]. LIGO: operadores = [], todas las features = 0.  
El modelo, entrenado con Δ como discriminador primario, no sabe qué hacer con todo-ceros.

**Capa 2 — Escala del x_grid**  
`02R` normalizaba por `γ_dom` → `x_dimless = t × γ_dom` → G2 decae como `e^{-2x}` → `log_slope ≈ -10`.  
Sandbox: `log_slope ≈ -1.4` a `-1.8`. Gap de 6-7x.  
**Fix aplicado**: `02R` ahora normaliza por `ω_dom` → `x_dimless = t × ω_dom` → G2 decae a tasa `γ/ω = 1/Q`.  
Resultado: `log_slope(LIGO) ≈ -0.41` vs `log_slope(sandbox) ≈ -1.4` → gap reducido a ~3x.

---

### 5. Sandbox v3 — training en formato polo-derivado

Nuevo script: `malda/00_sandbox_to_poles_bridge.py`  
Para cada geometría sandbox, genera embeddings tipo polo usando QNMs analíticos:

| Familia | Fórmula QNM | Q medio |
|---|---|---|
| ads | ω_n = 2πT(2Δ+2n+1) | 7.8 |
| lifshitz | ω_n = 2πT(2Δ+2n+1)/z | 7.3 |
| hyperscaling | igual con z_eff = z/(1-θ/d) | 7.9 |
| deformed | ads + γ×1.5 | 4.9 |

Añadidas geometrías **high-Q sintéticas** (Q=8–22) para cubrir el rango Kerr.

**Entrenamiento sandbox_v3**: 500 epochs, 172 geometrías, family accuracy=53%.  
Clasificación sandbox_v3 (test interno): 100% accuracy.  
Clasificación LIGO con v3: **sigue siendo `hyperscaling`**.

---

### 6. Diagnóstico final — por qué sigue fallando

Con la fórmula analítica, el ratio de sobretonos es siempre:

```
f₁/f₀ = (2Δ+3)/(2Δ+1) ≈ 1.29   para TODAS las familias
γ₁/γ₀ = 3.0                       para TODAS las familias
```

Kerr real (GW150914): `f₁/f₀ = 1.48`, `γ₁/γ₀ = 2.88`

Las familias son **indistinguibles entre sí a Q igual** con embeddings de 2 polos y ratios idénticos. El clasificador elige `hyperscaling` porque `highQ_hyperscaling_hq02` tiene Q=21, el más cercano a LIGO Q=20.4.

---

## Estado actual de los artefactos

| Artefacto | Ruta | Estado |
|---|---|---|
| Sandbox datos | `runs/sandbox_v1/01_generate_sandbox_geometries/` | ✅ 160 HDF5 |
| Checkpoint v2 | `runs/sandbox_v2/02_emergent_geometry_engine/emergent_geometry_model.pt` | ✅ A_r2=0.45 |
| Checkpoint v3 | `runs/sandbox_v3/02_emergent_geometry_engine/emergent_geometry_model.pt` | ✅ polo-derivado |
| Sandbox v3 datos | `runs/sandbox_v3_poles/boundary/` | ✅ 172 HDF5 |
| GW150914 raw | `runs/GW150914/raw/` | ✅ GWOSC 4096Hz |
| GW150914 boundary | `runs/GW150914/boundary_ringdown_v3/` | ✅ omega-norm |
| GW170814/170823/151226 | `runs/GW17xxxx/` | ✅ misma estructura |

---

## Siguiente paso (mañana)

### Implementar `00_compute_sandbox_qnms.py`

Resolver numéricamente los QNMs de cada geometría bulk usando el **método de shooting**:

1. Cargar `bulk_truth/A_truth`, `f_truth`, `z_grid` de cada sandbox HDF5
2. Plantear la ecuación de perturbaciones escalar:
   ```
   [e^{2A} f ∂_z(e^{-2A} f ∂_z φ)] + (ω² - m²_eff) φ = 0
   ```
3. Imponer condición entrante en el horizonte (z=z_h): `φ ~ (z-z_h)^{-iω/(4πT)}`
4. Integrar hacia el boundary (z→0): buscar ω tal que `φ → 0` (QNM condition)
5. Usar `scipy.optimize.fsolve` sobre ω complejo para encontrar los polos

Esto produce `f₁/f₀` y `γ₁/γ₀` **específicos por familia**, que son las huellas digitales espectrales que distinguen AdS de Lifshitz de hyperscaling.

Con esos QNMs numéricos, el clasificador aprenderá la estructura espectral correcta y podrá decir si LIGO se parece más a AdS, Lifshitz, hyperscaling — o a ninguno de los anteriores.

---

## Fixes pendientes menores

- [ ] `02R`: el arg `--x-min-s` / `--x-max-s` fue renombrado a `--x-min-dimless` / `--x-max-dimless` — actualizar cualquier script que los llame
- [ ] El aviso `X_std < 1e-06` en inference indica features degeneradas (índices 10, 13 = operator Δ features). Considerar zeroing explícito en training también para esas posiciones.
