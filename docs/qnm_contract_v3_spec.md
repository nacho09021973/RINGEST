# Contrato QNM v3 — Camino C

**Estado:** borrador v1.0 — 2026-04-11  
**Precondición:** `qnm_v1` (FEATURE_NAMES_V2_5) congelado como evidencia de bloqueo.
`qnm_v2/B` (log1p) bloqueado por evidencia insuficiente: con corpus local de 1 evento real,
la separación en log-escala sigue siendo estructural (~6 unidades, ningún solapamiento).

---

## 0. Cadena de diagnóstico v1→v2→v3

### v1 bloqueado (diagnóstico de 02_reopen_dataset_spec.md)

`qnm_Q0` raw: Kerr sandbox ∈ [2.14, 7.02], GW150914 = 1124.9. z-score proyectado ≈ 795σ.  
Misma fórmula `Q0 = π·f/γ`, observable operacional distinto.

### v2/B bloqueado (diagnóstico de qnm_contract_v2_spec.md)

`log1p(qnm_Q0)`: Kerr ∈ [0.76, 1.95], GW150914 = 7.03. Gap en log-escala ≈ 6 unidades.  
Un solo evento real materializado localmente: no hay evidencia de régimen intermedio.  
B no tiene base suficiente para reapertura con corpus local actual.

### v3 — diagnóstico ampliado

Más allá del gap de escala, el audit de la estructura de datos revela incompatibilidades
adicionales que hacen que v2 no sea una reparametrización suficiente:

---

## 1. Diagnóstico estructural completo

### 1.1 Causa raíz: selección de polo ESPRIT

En `02R_build_ringdown_boundary_dataset.py`, el polo dominante se selecciona por amplitud:

```python
dom = max(poles, key=lambda p: p.amp_abs)
```

Para GW150914 (ventana de análisis larga, 16 polos ESPRIT):

| Polo | f (Hz) | τ (s) | Q0 | Fuente probable |
|---|---|---|---|---|
| **dominante en amplitud** | ~134 Hz | ~2.7 s | **1124** | Modo de larga vida (ruido/envolvente) |
| esperado físico (Kerr BBH) | ~251 Hz | ~0.004 s | ~3 | Ringdown real |

El ringdown físico (τ≈4ms) tiene baja amplitud en ventanas largas y **nunca es el polo de máxima
amplitud**. ESPRIT extrae correctamente los polos presentes en la señal, pero el criterio de
selección elige el modo incorrecto.

Consecuencia: `omega_dom_rads = 842 rad/s` (f=134 Hz) en lugar del esperado ~1577 rad/s (f=251 Hz).
Todo lo que se normaliza por `omega_dom_rads` —incluyendo la grilla ω̃ de G_R— está en la escala
incorrecta.

### 1.2 Incompatibilidad estructural de G_R

| Fuente | Forma de G_R | Normalización |
|---|---|---|
| `01b` Kerr sandbox | (n_k, n_omega) — 2D | `omega_dom_rads=1, gamma_dom_inv_s=0` (sin normalización física) |
| `02R` bridge real | (n_omega,) — 1D | `omega_dom_rads=842 rad/s` (polo ESPRIT dominante en amplitud) |

`build_feature_vector` extrae `GR_peak_height` y `GR_peak_width` de ambas fuentes
sin corregir esta diferencia de dimensionalidad ni de normalización.  
Para GW150914, el pico de `|G_R|` está en ω̃=8.4, no en ω̃≈1 —porque el polo de normalización
(f=134 Hz) no es el polo físicamente dominante del ringdown (f=251 Hz).

### 1.3 Lo que esto implica para features downstream

Cualquier feature derivada de attrs `qnm_*` o de la función G_R heredará estas incompatibilidades:
- `qnm_Q0` y sus variantes log miden el polo incorrecto en el carril real
- `GR_peak_height` / `GR_peak_width` están en escalas incoherentes entre fuentes
- No existe reparametrización de los attrs actuales que resuelva el problema sin cambiar upstream

---

## 2. Definición de Camino C

Camino C no es solo cambiar features en `build_feature_vector`. Requiere que **al menos una**
de las siguientes dos condiciones sea verdadera:

> **C1** — 02R extrae correctamente el polo del ringdown físico (selección guiada por frecuencia o
> por ventana temporal)
>
> **C2** — Las features de 02 se definen puramente sobre observables de G2 (correlador), sin
> depender de attrs QNM derivados de ESPRIT, eliminando la dependencia de la selección de polo

Ambos caminos son legítimos. C1 mantiene features QNM con semántica física. C2 los reemplaza
con observables estructuralmente más robustos pero con menor poder discriminante QNM.

---

## 3. Camino C1 — Selección de polo físico en 02R

### Descripción

Cambiar el criterio de selección del polo dominante en `02R` de **máxima amplitud** a
**máxima frecuencia dentro de una banda BBH plausible** (o polo más cercano al pico del G2).

### Criterio de selección propuesto

```python
# En lugar de: dom = max(poles, key=lambda p: p.amp_abs)
# Usar selección por banda física:

RINGDOWN_FREQ_MIN_HZ: float = 50.0
RINGDOWN_FREQ_MAX_HZ: float = 2000.0  # cubre M∈[10, 500] M☉
RINGDOWN_MIN_Q: float = 0.5            # excluye modos sub-oscilatorios

candidates = [
    p for p in poles
    if RINGDOWN_FREQ_MIN_HZ <= p.freq_hz <= RINGDOWN_FREQ_MAX_HZ
    and (math.pi * p.freq_hz / p.damping_1_over_s >= RINGDOWN_MIN_Q
         if p.damping_1_over_s > 0 else False)
]
dom = max(candidates, key=lambda p: p.amp_abs) if candidates else max(poles, key=lambda p: p.amp_abs)
```

Esto selecciona el polo de máxima amplitud DENTRO del régimen BBH plausible, excluyendo modos
DC, de larga vida (τ≫1 ms), y fuera del rango físico.

### Features resultantes

Con polo correcto seleccionado, `qnm_Q0`, `qnm_f1f0`, `qnm_g1g0` tendrían semántica consistente:
- Real (GW150914, polo físico): Q0≈3 (comparable a Kerr sandbox)
- El contrato v1 (nombres raw lineales) podría funcionar sin log-transform

Nuevos nombres versionados para el contrato C1:

```python
# Attrs escritos por 02R y 01b bajo contrato v3 (C1)
"qnm_Q0"       → "qnm_Q0_v3"        # mismo cálculo, polo seleccionado correctamente
"qnm_f1f0"     → "qnm_f1f0_v3"      # idem
"qnm_g1g0"     → "qnm_g1g0_v3"      # idem
"qnm_contract" → "v3c1"
```

### Riesgo C1

Si el polo del ringdown físico no es el más energético dentro de la banda [50, 2000 Hz]
(e.g., evento de bajo SNR), la selección sigue siendo incorrecta. Se necesita un criterio de
confianza o un fallback.

Señal de fallo: `qnm_Q0_v3 > 100` después de aplicar C1 indica que el polo seleccionado
sigue siendo un modo espurio. Gate debe marcar esta condición como WARN.

### Archivos a modificar (C1)

| Archivo | Qué cambia |
|---|---|
| `02R_build_ringdown_boundary_dataset.py` | Criterio de selección de polo dominante; escribir attrs `_v3` |
| `01b_generate_kerr_sandbox.py` | Solo añadir `qnm_contract="v3c1"` y attrs `_v3` (valores iguales a v1) |
| `feature_support.py` | `FEATURE_NAMES_V2_7_C1`, `CRITICAL_FEATURES_V2_7_C1` |
| `02_emergent_geometry_engine.py` | `build_feature_vector` lee `qnm_*_v3`; importa V2_7_C1 |

---

## 4. Camino C2 — Reemplazo de QNM por features de G2

### Descripción

Eliminar `qnm_Q0`, `qnm_f1f0`, `qnm_g1g0` del vector de features. Reemplazar con observables
extraídos directamente del correlador G2, que es el mismo observable en ambas fuentes y está
calculado con la misma normalización.

### Nuevas features propuestas (en lugar de QNM)

Tres observables de G2 que capturan información de desvanecimiento/estructura:

```python
# En build_feature_vector, bloque QNM → bloque G2_osc:

# Feature 1: pendiente de caída en x grande
# G2(x) ∝ exp(-γ̃·x) para un modo oscilatorio → pendiente de log(G2) en x∈[3,8]
# Comparable entre fuentes sin normalización de polo
g2 = boundary_data.get("G2_O1", boundary_data.get("G2_ringdown", None))
x  = boundary_data.get("x_grid", None)
if g2 is not None and x is not None:
    mask = (x >= 3) & (x <= 8) & (g2 > 1e-12)
    if mask.sum() >= 4:
        log_slope_decay = np.polyfit(x[mask], np.log(g2[mask]), 1)[0]  # < 0 para decaimiento
    else:
        log_slope_decay = 0.0
    # Feature 2: ratio G2(x=2)/G2(x=0.5) — estructura oscilatorio vs alisado
    idx_lo = np.argmin(np.abs(x - 0.5)); idx_hi = np.argmin(np.abs(x - 2.0))
    g2_ratio_osc = float(g2[idx_hi] / max(g2[idx_lo], 1e-12))
    # Feature 3: x del pico de G2 (proxy de frecuencia dominante)
    g2_peak_x = float(x[np.argmax(g2)])
else:
    log_slope_decay, g2_ratio_osc, g2_peak_x = 0.0, 0.0, 0.0

all_features.append(log_slope_decay)  # "G2_decay_slope"
all_features.append(g2_ratio_osc)     # "G2_osc_ratio"
all_features.append(g2_peak_x)        # "G2_peak_x"
```

Nuevos nombres en FEATURE_NAMES_V2_7_C2:

```python
# Bloque QNM (3 features) → bloque G2_osc (3 features)
"qnm_Q0"   → "G2_decay_slope"   # pendiente log-lineal de decaimiento en x∈[3,8]
"qnm_f1f0" → "G2_osc_ratio"     # ratio de amplitud en x corto vs largo
"qnm_g1g0" → "G2_peak_x"        # posición del máximo en G2(x)
```

Críticas para C2:

```python
CRITICAL_FEATURES_V2_7_C2 = (
    "has_horizon",
    "G2_large_x",
    "G2_decay_slope",   # reemplaza qnm_Q0 como discriminador de desvanecimiento
    "G2_osc_ratio",
    "G2_peak_x",
)
```

### Ventaja C2

Sin dependencia de attrs ESPRIT. Puramente computable desde los datasets G2/x_grid
que ya escriben ambas fuentes. Robusto a cambios en la extracción de polos upstream.

### Riesgo C2

Pérdida de poder discriminante QNM explícito: el modelo no ve directamente Q0 ni f1/f0.
La información QNM está codificada implícitamente en G2, pero de forma menos directa.

### Archivos a modificar (C2)

| Archivo | Qué cambia |
|---|---|
| `02_emergent_geometry_engine.py` | `build_feature_vector` bloque QNM → G2_osc features |
| `feature_support.py` | `FEATURE_NAMES_V2_7_C2`, `CRITICAL_FEATURES_V2_7_C2` |
| `01b_generate_kerr_sandbox.py` | Sin cambios (G2/x_grid ya escritos) |
| `02R_build_ringdown_boundary_dataset.py` | Sin cambios (G2_ringdown/x_grid ya escritos) |

C2 es el único camino que no requiere modificar `01b` ni `02R`.

---

## 5. Comparación de caminos

| Criterio | C1 (polo físico) | C2 (G2 features) |
|---|---|---|
| Cambios en 02R | Sí (criterio selección polo) | No |
| Cambios en 01b | Mínimos (attrs _v3) | No |
| Cambios en build_feature_vector | Mínimos (lee attrs _v3) | Sí (nueva extracción G2) |
| Poder discriminante QNM | Alto (Q0, f1/f0, g1/g0 físicos) | Medio (G2 codifica QNM implícitamente) |
| Riesgo de fallo en bajo SNR | Posible (polo incorrecto si SNR<umbral) | Bajo (G2 siempre tiene señal) |
| Tests de paridad B vs C | Verificables directamente | Requieren nuevas referencias |

---

## 6. Tests de aceptación (comunes a C1 y C2)

### 6.1 Test de paridad B vs C

Para cada feature QNM-equivalente `f` en el contrato v3 elegido:

```
|mean_B(f) - mean_C(f)| < 3 * (std_B(f) + std_C(f))
```

Este test fue el bloqueante para v2/B. Si C1 funciona correctamente, Q0_v3 en real debe ser
≈2-10 (como Kerr sandbox), y el test pasaría. Si sigue fallando tras C1, escalar a C2.

### 6.2 Train support test (mismo que v2)

```python
audit = audit_train_feature_support(
    feature_names=FEATURE_NAMES_V2_7_CX,
    X_mean=X_all.mean(axis=0),
    X_std=X_all.std(axis=0),
    critical_features=CRITICAL_FEATURES_V2_7_CX,
)
assert audit["verdict"] == "PASS"
assert not audit["critical_tiny_std_features"]
```

### 6.3 GW150914 probe

```bash
python 02_emergent_geometry_engine.py \
  --mode inference \
  --checkpoint runs/<reopen_run_id>/02_emergent_geometry_engine/emergent_geometry_model.pt \
  --data-dir runs/gwosc_all/inference_input \
  --output-dir runs/<reopen_run_id>/reopen_probe_gw150914 \
  --experiment reopen_probe_gw150914
echo "Exit code: $?"
```

Criterio: exit 0, `n_gate_fail = 0`, sin `UNSUPPORTED_FEATURE_REGIME`.

### 6.4 Cohorte ancla

GW151226 y GW170814: `n_gate_fail = 0` en ambos. Si falla cualquier evento ancla, el
checkpoint no reabre 02 aunque GW150914 pase.

---

## 7. Tabla de versiones de contrato

| Versión | Feature list | QNM contract | Estado |
|---|---|---|---|
| V2_5 | `FEATURE_NAMES_V2_5` | raw linear (01b+02R) | **CONGELADO** — bloqueo v1 |
| V2_6 | `FEATURE_NAMES_V2_6` | log1p (B) | **CONGELADO** — insuficiente con corpus local |
| V2_7_C1 | `FEATURE_NAMES_V2_7_C1` | polo físico seleccionado (C1) | **CANDIDATO** |
| V2_7_C2 | `FEATURE_NAMES_V2_7_C2` | G2 features, sin QNM (C2) | **ALTERNATIVA** |

---

## 8. Secuencia de implementación recomendada

### Paso 0 — Decisión de sub-camino

Elegir entre C1 y C2. La elección determina qué archivos se modifican.

**Señal para elegir C1:** si los eventos reales procesados por 02R producen Q0≈3 cuando se
selecciona el polo correcto (verificable inspeccionando el `poles_joint.json` de GW150914).  
**Señal para elegir C2:** si el polo físico no es identificable sin información externa
(masa del remanente, frecuencia ISCO), indicando que ESPRIT no es la herramienta correcta
para este carril.

### Paso 1 — Verificar si el polo físico existe en GW150914

Inspeccionar `runs/gwosc_all/GW150914/boundary/ringdown/poles_joint.json` (fuente original
de `02R`). Verificar si entre los 16 polos hay alguno con f∈[200,300] Hz y τ∈[1,20] ms.
Si existe → C1 es viable. Si no → C2 es el camino.

### Paso 2 — Implementar el sub-camino elegido

Ver §3 (C1) o §4 (C2).

### Paso 3 — Regenerar Slice B y Slice C bajo contrato v3

- Slice B: regenerar Kerr sandbox con nuevo contrato (o reutilizar si solo añaden attrs)
- Slice C: regenerar bridge real sobre corpus local con criterio de polo corregido (C1) o sin cambios (C2)

### Paso 4 — Ensamblar dataset A+B+C y entrenar

### Paso 5 — Probe real + cohorte ancla

Solo reabre 02 si §6.3 y §6.4 pasan.

---

## 9. Checklist de reapertura bajo v3

- [ ] Sub-camino elegido: C1 o C2 (documentar aquí: ______)
- [ ] Paso 1 completado: poles_joint.json inspeccionado, polo físico verificado/descartado
- [ ] feature_support.py: `FEATURE_NAMES_V2_7_CX` y `CRITICAL_FEATURES_V2_7_CX` añadidos
- [ ] build_feature_vector actualizado bajo contrato v3 elegido
- [ ] Si C1: 02R criterio de selección de polo corregido + attrs `_v3` escritos
- [ ] Si C1: 01b attrs `_v3` añadidos (valores iguales a v1)
- [ ] Test paridad B vs C (§6.1): PASS
- [ ] Dataset A+B+C ensamblado en `runs/<reopen_run_id>/02_reopen_dataset/`
- [ ] Audit pre-train: `verdict == "PASS"` con V2_7_CX / CRITICAL_FEATURES_V2_7_CX
- [ ] Reentrenamiento desde cero bajo V2_7_CX
- [ ] Train audit en summary: `feature_support_audit.verdict == "PASS"`
- [ ] GW150914 probe: exit 0, `n_gate_fail = 0`
- [ ] Cohorte ancla (GW151226, GW170814): `n_gate_fail = 0`
- [ ] hoja_de_ruta.md actualizado: 02 reabierto bajo `qnm_v3_cX`
