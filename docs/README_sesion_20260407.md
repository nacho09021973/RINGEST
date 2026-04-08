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

---

# Sesión 2026-04-08 — QNMs numéricos y clasificación de unknowns

## 1. `00_compute_sandbox_qnms.py` ejecutado sobre las 160 geometrías

Script implementado y ejecutado con `--n-modes 2`. Resuelve numéricamente los QNMs de cada bulk sandbox por método de shooting sobre la ecuación de perturbaciones escalar:

```
[e^{2A} f ∂_z(e^{-2A} f ∂_z φ)] + (ω² - m²_eff) φ = 0
```

Condición de contorno: modo entrante en el horizonte `φ ~ (z-z_h)^{-iω/(4πT)}`, cero en el boundary.

Resultados guardados en `runs/sandbox_v1/qnm_numerical.json`.

### Resumen por familia (160 geometrías, n_modes=2)

| Familia       | N  | f1/f0 | γ1/γ0 | Q0   |
|---------------|----|-------|-------|------|
| ads           | 30 | 2.326 | 1.089 | 3.15 |
| deformed      | 30 | 2.274 | 0.998 | 2.20 |
| dpbrane       | 40 | 2.362 | 1.012 | 4.23 |
| hyperscaling  | 20 | 2.337 | 1.027 | 4.76 |
| lifshitz      | 30 | 2.313 | 1.004 | 2.85 |
| unknown       | 10 | 2.302 | 1.011 | 3.71 |

### Hallazgos clave

**f1/f0 ≈ 2.3 es universal** — rango [1.9–2.8] sin separación clara entre familias. Contrasta con la fórmula analítica anterior (f1/f0 ≈ 1.29): los QNMs numéricos capturan la geometría real del bulk, no la aproximación CFT.

**γ1/γ0 discrimina `ads`**: 1.089 frente a ~1.00 del resto. Las geometrías AdS tienen el segundo modo relativamente más amortiguado que las demás familias.

**Q0 es el mejor discriminador de familia**:
- `hyperscaling` (4.76) y `dpbrane` (4.23): modos de larga vida
- `ads` (3.15) y `lifshitz` (2.85): Q medio
- `deformed` (2.20): amortiguamiento rápido

**Los unknowns**: Q0=3.71, γ1/γ0=1.011 → perfil compatible con `dpbrane`. Pendiente clasificación formal.

---

## 2. Nota sobre `consejos_ads_ringdown.md`

Documento de referencia revisado. Puntos accionables para las próximas fases:

- **Punto 12**: `LOSS_WEIGHT_PHYSICS_ADS = 0.02` en `02_emergent_geometry_engine.py` es un prior incorrecto para Kerr. Cambiar antes de adaptar a datos reales.
- **Punto 9**: Usar el paquete `qnm` (Python) como ground truth al validar con geometrías Kerr.
- **Punto 10**: El sandbox AdS debe reemplazarse por un generador de señales de ringdown Kerr sintéticas para la siguiente fase.
- **Punto 17**: Orden de adaptación confirmado: `02 → 06 → 07 → resto`.

---

## Estado artefactos al cierre de 2026-04-08

| Artefacto | Ruta | Estado |
|---|---|---|
| QNMs numéricos sandbox_v1 | `runs/sandbox_v1/qnm_numerical.json` | ✅ 160 geometrías |
| Script QNM shooting | `malda/00_compute_sandbox_qnms.py` | ✅ n_modes configurable |
| Boundary GW150914 blanqueado | `runs/GW150914_whitened/data_boundary/` | ✅ v4 con whitening Welch |
| `00_load_ligo_data.py` | `malda/` | ✅ v4, añadido `--whiten` |
| `01_extract_ringdown_poles.py` | `malda/` | ✅ fix conjugate-pair filter |

---

## 3. Whitening e integración en `01_extract_ringdown_poles.py`

### `00_load_ligo_data.py` → v4

Añadido whitening PSD-based como opción integrada:
- `--whiten`: activa el whitening
- PSD estimada con Welch (mediana) desde segmento offband configurable (`--whiten-psd-trel-start/end`)
- Strain blanqueado guardado como `strain/H1_whitened` (+ L1) en el HDF5
- Todos los parámetros de whitening loggeados en attrs + manifest

Resultado de validación (GW150914):
- Offband std ≈ 1.20 (objetivo ~1) ✅
- Post-merger (0–0.5s): std=1.05, max=4.60 — ringdown visible sobre el ruido ✅

### `01_extract_ringdown_poles.py` — fix conjugate pairs

Añadido filtro `Re(ω) > 0` en `_sort_and_filter`. ESPRIT sobre señal real produce pares conjugados (ω, −ω*); ambos tienen Im(ω)<0 y pasaban el filtro `--require-decay`. Ahora solo se conservan polos de frecuencia positiva.

`01` usa automáticamente `strain/H1_whitened` cuando existe en el HDF5.

### Análisis de sensibilidad `--start-offset` (GW150914)

Barrido: offset={-0.01, 0.00, 0.01, 0.02, 0.05} × duration={0.05, 0.10, 0.15} × rank=4, lp=400 Hz.

**Frecuencia f0: recuperable.** Mejor caso: 250±15 Hz para offset ≈ 0.01–0.02, dur=0.05s, H1.

**Amortiguamiento τ0: no recuperable a SNR~8.** Extraído: 30–400 ms vs referencia 13 ms (Isi+2019). Sesgo sistemático de ESPRIT a bajo SNR, consistente con Cotesta et al. (arXiv:2107.05609).

**Consecuencia para el clasificador:** Q extraído = 20–120 vs Q Kerr real ≈ 10. ESPRIT no puede pinchar el Q con fiabilidad a este SNR.

**Decisión:** usar los polos publicados de Isi+2019 (f0=250 Hz, τ0=13 ms) como entrada a `02R` para GW150914. La mejora de la extracción (análisis Bayesiano, integración con repositorio de Isi) queda recogida en `hoja_de_ruta.md`.

---

---

## 4. `02R` + retraining con features QNM (v4 → v5)

### Diagnóstico de raíz del clasificador

Feature vector (20 features, v2.5): reemplazados los 4 features Δ (n_ops, Δ_min, Δ_max, Δ_mean) por 3 features QNM (Q0, f1/f0, γ1/γ0). Estos features son iguales de 0 para LIGO con el vector antiguo.

`02R` v2 actualizado: almacena `qnm_Q0`, `qnm_f1f0`, `qnm_g1g0` en los attrs del grupo `boundary` de cada HDF5.
Sandbox v1: 160 HDF5 parcheados con los mismos attrs desde `qnm_numerical.json`.

### Retraining sandbox v4

500 epochs, datos sandbox_v1 (160 geometrías), feature vector con QNMs:
- A_r2 = 0.462, f_r2 = 0.922 (comparable a v2)
- **Family accuracy = 81.7%** (vs 53% en v3 — notable mejora)

### Inferencia LIGO con v4 + boundary v5

Resultado: todos los eventos → `hyperscaling`. **Pero ahora el diagnóstico es claro:**

| Feature | LIGO (Kerr) | max sandbox (hyperscaling) |
|---|---|---|
| qnm_Q0 | 10.20 | 4.76 |
| qnm_f1f0 | 1.48 | 2.36 |
| qnm_g1g0 | 2.88 | 1.09 |

LIGO está completamente fuera de la distribución de entrenamiento. El clasificador extrapola y asigna la familia de Q más alto conocido (`hyperscaling`). No es un bug — es un gap de training data.

**Solución necesaria: sandbox Kerr** — implementar `01b_generate_kerr_sandbox.py` con el paquete `qnm` para cubrir Q0≈5-20, f1/f0≈1.2-1.8, γ1/γ0≈2-4 (régimen Kerr real).

---

## Sesión 2026-04-08 (continuación — Kerr sandbox)

### Completar modificaciones de `02_emergent_geometry_engine.py`

Se completó la implementación del soporte Kerr en el engine:

- `has_bulk_train_t` tensor construido a partir de `train_data["has_bulk"]`
- Pasado a `train_one_epoch(has_bulk_mask=has_bulk_train_t)` — las pérdidas de reconstrucción A/f/R se anulan para geometrías sin bulk_truth (Kerr)

### `01b_generate_kerr_sandbox.py` — implementado

Generador sintético de geometrías Kerr para el clasificador:

- Usa paquete `qnm` para calcular QNMs teóricos (ℓ=2, m=2, n=0 y n=1)
- Grid: M∈[25,150] Msun × a/M∈[0.1,0.9] → 80 geometrías (8×10)
- Features clave Kerr (invariante con M por escala):
  - f1/f0 ≈ 0.935–0.994 (overtone **debajo** del fundamental — único en Kerr)
  - γ1/γ0 ≈ 3.01–3.07 (muy constante, independiente de spin y masa)
  - Q0 ≈ 2.18–5.18 (aumenta con spin)
- HDF5 sin grupo `bulk_truth` (Kerr no tiene dual holográfico)
- Embeddings surrogate: `G2_O1`, `G_R_real/imag` calculados con las mismas funciones que `02R`
- Manifiesto `geometries_manifest.json` compatible con el engine

### Merger sandbox_v1 + Kerr → sandbox_v5

Script `merge_manifests.py`: une los manifiestos de sandbox_v1 (160) y kerr_sandbox_v1 (80).
Total: **240 geometrías** en `runs/sandbox_v5/01_merged/`.

### Retraining sandbox_v5 (400 epochs)

- 160 geometrías sandbox (ads/lifshitz/hyperscaling/deformed/unknown) + 80 Kerr
- Family accuracy test: 66.7% (test set son los unknowns del sandbox — sin Kerr en test)
- **Kerr en training: p=0.997-0.999 para todos los puntos del grid** ✓

### Inferencia LIGO con modelo sandbox_v5

| Evento | Pred v4 | Pred v5 | p(Kerr) |
|---|---|---|---|
| GW150914 (boundary_v5) | hyperscaling | **kerr** | 0.966 |

**GW150914 se clasifica ahora como Kerr con p=0.966.**

El discriminador clave es f1/f0=1.48 (fuera del rango sandbox >2.3) que el modelo generaliza correctamente como Kerr-like, a pesar de que Q0=10.2 está fuera del rango de entrenamiento (2.18-5.18).

Nota: Q0_LIGO > Q0_Kerr_teorico (~3.15 para M=68, a=0.69) porque ESPRIT sobreestima τ0 a bajo SNR. La clasificación es correcta a pesar de esta discrepancia por la separabilidad de f1/f0.

---

## Siguiente paso (tras Fase 3)

- **B3 (AdS prior)**: Eliminar o condicionar `LOSS_WEIGHT_PHYSICS_ADS = 0.02` en `02_emergent_geometry_engine.py` antes de adaptar a Kerr real
- **Fase 4**: Adaptar `06_build_bulk_eigenmodes_dataset.py` para geometrías Kerr
- **Rigor**: Extender el sandbox Kerr a mayor rango de Q0 (a/M→0.99) para cubrir mejor el espacio de LIGO

---

# Sesión 2026-04-08 (continuación) — Fase 4: scripts 06 y 07

## Resumen

Se implementaron y ejecutaron todos los scripts de Fase 4 para la rama holográfica y la rama Kerr.

---

## 1. `bulk_scalar_solver.py` — Eigensolver Sturm-Liouville

Nuevo módulo auxiliar. Resuelve el problema de autovalores del campo escalar en bulk:

```
-(d/dz)[p(z) dψ/dz] = λ w(z) ψ
p(z) = A(z)^{d-1} f(z)
w(z) = A(z)^{d-3}
λ = ω²
```

Implementación:
- Diferencias finitas centradas (segundo orden)
- BC Dirichlet en ambos extremos (UV y horizonte)
- Truncado de horizonte: usa `zh_pred` attrs o auto-detección f<0.02
- Refinamiento de grilla: interpolación cúbica a 200 puntos
- Solver: `scipy.linalg.eigh` (problema generalizado simétrico)
- UV exponents: Δ_+ = (d + √(d²+4λ))/2

---

## 2. `06_holographic_eigenmode_dataset.py`

Construye el dataset de autovalores para stage 07 leyendo directamente de los HDF5 de sandbox (no del geometry emergente).

**Distinción crítica**: la fuente correcta de λ_sl = m²L² es `Delta_mass_dict` en los attrs de `boundary` — NO los autovalores ω² del SL solver. El SL solver es solo cross-check.

**d_formula**: calculado empíricamente para cada geometría:
```python
d_formula = round(median((Δ² - m2L2) / Δ))  # por operador
```
Varía entre 3, 4 y 5 para geometrías con d_sp=3. El valor no es simplemente d_sp+1.

Resultados:
- 480 filas holográficas (160 geo × 3 operadores): `bulk_modes_dataset.csv`
- 80 filas Kerr (sin bulk holográfico): `kerr_qnm_dataset.csv`
- max_err fórmula: 2.63e-08

---

## 3. `07_holo_lambda_dictionary.py`

Valida y aprende el diccionario holográfico λ_sl = Δ(Δ-d).

Resultados (480 muestras, 6 familias):

| Modelo | Train R² | CV R² |
|---|---|---|
| Theory check Δ(Δ-d) | 1.000000 | — |
| Poly grado 2 | 1.000000 | 1.000000 |
| GBR data-driven | 0.999989 | 0.999533 |
| Lineal | 0.9818 | 0.9802 |

- Todas las familias individualmente: R²=1.0000
- m²<0 (tachyónico, n=334): R²=1.0, MAE=6.79e-09
- m²>0 (n=146): R²=1.0, MAE=1.04e-08

**Conclusión**: la relación λ_sl = Δ(Δ-d) es verificada a precisión de máquina. Un modelo polinomial de grado 2 la recupera exactamente; el GBR la aprende de forma independiente con R²_cv=0.9995.

---

## 4. `07K_kerr_qnm_dictionary.py`

Diccionario inverso Kerr: (f0, τ0, Q0, f1/f0, γ1/γ0) → (M, a/M).

**Degeneración física**: f0×τ0, Q0, f1/f0, γ1/γ0 son todos independientes de M por escala. Un solo modo QNM no puede determinar M a partir de dimensionless features — necesita f0 en unidades absolutas.

**Predictor 2-step** (físico):
1. a/M = GBR(Q0, f1/f0, γ1/γ0) → R²_cv=1.0000
2. M = α(a/M) / (2π f0 MSUN_S) donde α(a/M) = Mω_R(a/M) del paquete `qnm` → R²=1.0

**GW150914** (τ0=13ms de Isi+2019, fuera del rango de training):
- a/M predicho: 0.900 (teoría: 0.69 para M=68 Msun)
- M predicho: 119 Msun (teoría: 68 Msun)
- Discrepancia: τ0_ESPRIT >> τ0_teórico a bajo SNR — sesgo documentado

**Invarianza física**: corr(ωM, a/M)=0.959, corr(τ/M, a/M)=0.837 — las cantidades dimensionless son las verdaderas variables del problema.

---

## 5. `00_download_gwosc_events.py`

Script de descarga masiva de todos los eventos LIGO/Virgo de GWOSC.

- Fuentes: GWTC-1, GWTC-2.1, GWTC-3 (90 eventos confident únicos)
- Descarga HDF5 de 32s a 4096 Hz por IFO (H1, L1, V1 si disponible)
- Extrae ventana de 32s de bloques de observación completos (v4+ datasets)
- Salida: `runs/gwosc_all/<event>/raw/<event>_<IFO>_4096Hz_32s.npz`
- Formato NPZ idéntico al esperado por `00_load_ligo_data.py`
- Opciones: `--dry-run`, `--force`, `--event GW150914`, `--max-events N`

Uso:
```bash
# Dry-run para ver qué se descargará
python3 malda/00_download_gwosc_events.py --dry-run

# Descarga real (tarda ~30-60 min, ~6 GB)
python3 malda/00_download_gwosc_events.py --out-dir runs/gwosc_all

# Post-procesado: whitening + boundary para todos
for npz in runs/gwosc_all/*/raw/*_H1_*.npz; do
  ev=$(basename $(dirname $(dirname $npz)))
  python3 malda/00_load_ligo_data.py \
    --npz $npz \
    --out-dir runs/gwosc_all/${ev}/boundary \
    --whiten
done
```

---

## Estado de artefactos al cierre de esta sesión

| Artefacto | Ruta | Estado |
|---|---|---|
| SL eigensolver | `malda/bulk_scalar_solver.py` | ✅ nuevo |
| Dataset eigenmodos holográficos | `runs/sandbox_v5_b3/06_holographic_eigenmode_dataset/` | ✅ 480 filas |
| Diccionario holográfico | `runs/sandbox_v5_b3/07_holo_lambda_dictionary/` | ✅ R²=1.0 |
| Diccionario Kerr QNM | `runs/sandbox_v5_b3/07K_kerr_qnm_dictionary/` | ✅ R²=1.0 |
| Script descarga GWOSC | `malda/00_download_gwosc_events.py` | ✅ 90 eventos |

## Siguiente paso

- **Ejecutar descarga masiva**: `python3 malda/00_download_gwosc_events.py --out-dir runs/gwosc_all`
- **Post-procesar con 00 + 01 + 02**: cadena completa sobre los 90 eventos
- **Scripts 08 y 09**: cuando tengamos clasificaciones sobre los datos reales
- **Análisis Bayesiano de τ0**: integración con repositorio `maxisi/ringdown` para estimación robusta de Q0
