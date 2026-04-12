# Contrato QNM v2 — `FEATURE_NAMES_V2_6`

**Estado:** borrador v1.0 — 2026-04-11  
**Razón de existencia:** `qnm_v1` (contrato implícito de `FEATURE_NAMES_V2_5`) está contractualmente
roto para el carril real. Este documento define `qnm_v2` como sustituto explícito y versionado.

---

## 0. Por qué v1 está roto

`qnm_v1` usa la misma fórmula `Q0 = π·f_Hz / γ_s⁻¹` en dos fuentes cuya semántica es
incompatible:

| Fuente | Poles de entrada | f típica | γ típica | Q0 resultante |
|---|---|---|---|---|
| `01b_generate_kerr_sandbox.py` | Modos analíticos Kerr (`qnm` package) | ~100–250 Hz | ~100–250 s⁻¹ | **2–7** |
| `02R_build_ringdown_boundary_dataset.py` | Polo dominante ESPRIT en señal real | ~134 Hz | ~0.37 s⁻¹ | **~1125** |

El polo dominante que ESPRIT extrae de datos reales no es el modo de ringdown físico; es un modo
de larga vida (τ≈2.7 s) dominante en amplitud dentro de la ventana de análisis.

Mismo nombre de attr, observable operacional distinto.  
Resultado medido: z-score proyectado de `qnm_Q0` para GW150914 sobre modelo entrenado con Kerr
sandbox ≈ **795σ**. La gate siempre falla; no es una cuestión de cobertura.

El contrato v1 queda **congelado como evidencia del bloqueo** de stage 02.  
No modificar `FEATURE_NAMES_V2_5`, `CRITICAL_FEATURES`, ni el checkpoint `sandbox_serio_v1`.

---

## 1. Definición de `qnm_v2`

### 1.1 Transformaciones

Las tres features QNM pasan a escala logarítmica para comprimir el rango dinámico y hacer
comparable el régimen sintético con el real:

| Feature v1 | Feature v2 | Fórmula exacta | Rango esperado (ver §1.3) |
|---|---|---|---|
| `qnm_Q0` | `qnm_Q0_v2` | `log1p(qnm_Q0)` | [0.76, 9.0] aprox. |
| `qnm_f1f0` | `qnm_f1f0_v2` | `log(max(qnm_f1f0, 1e-4))` | [-9.2, ~2.5] aprox. |
| `qnm_g1g0` | `qnm_g1g0_v2` | `log(max(qnm_g1g0, 1e-4))` | [-9.2, ~1.5] aprox. |

**Invariante**: las tres features usan transformación logarítmica. No dejar ninguna en escala
lineal. Un bloque QNM internamente mixto (lineal/log) es tan incoherente como v1.

### 1.2 Manejo del valor cero / un solo modo

Cuando hay menos de 2 modos (`qnm_n_modes < 2`) o el campo está ausente:

- `qnm_f1f0` raw = 0.0 → `qnm_f1f0_v2 = log(1e-4) = -9.21` (sentinel, fuera de rango físico)
- `qnm_g1g0` raw = 0.0 → `qnm_g1g0_v2 = log(1e-4) = -9.21` (idem)
- `qnm_Q0` raw = 0.0 → `qnm_Q0_v2 = log1p(0) = 0.0`

El sentinel -9.21 es deliberadamente extremo: activa el gate en off-support para sistemas sin
segundo modo. Esto es correcto — un sistema sin estructura de overtone es cualitativamente
distinto y no debe inferir sin advertencia.

### 1.3 Rangos observados por fuente (pre-mezcla)

| Fuente | `qnm_Q0_v2` | `qnm_f1f0_v2` | `qnm_g1g0_v2` |
|---|---|---|---|
| Kerr sandbox (80 geos, M∈[20,150] M☉, a/M∈[0.05,0.95]) | [0.76, 1.95] | [-0.07, -0.002] | [1.09, 1.11] |
| GW150914 (ESPRIT) | 7.03 | 2.13 | 0.46 |
| GW151226 (ESPRIT) | 8.89 | -0.52 | ~tbd |

Los rangos de Slice B (Kerr) y Slice C (real) ya no son disjuntos en `qnm_Q0_v2` gracias a la
compresión logarítmica, pero el solapamiento no es completo. La mezcla A+B+C en training
amplía el rango de soporte.

---

## 2. `FEATURE_NAMES_V2_6`

20 features, misma estructura que v2.5, solo cambia el bloque QNM:

```python
FEATURE_NAMES_V2_6: Tuple[str, ...] = (
    # Correlator (9)
    "G2_log_slope", "G2_log_curvature", "G2_small_x", "G2_large_x",
    "slope_UV", "slope_IR", "slope_running", "G2_std", "G2_skew",
    # Thermal (4)
    "temperature", "has_horizon", "thermal_scale", "exponential_decay",
    # QNM v2 (3)  ← cambiado respecto a V2_5
    "qnm_Q0_v2", "qnm_f1f0_v2", "qnm_g1g0_v2",
    # Response G_R (2)
    "GR_peak_height", "GR_peak_width",
    # Global scalars (2)
    "central_charge_eff", "d",
)
```

Índices 13–15 son los únicos que cambian de nombre. Todos los demás índices son idénticos a V2_5.

### Features críticas v2.6

```python
CRITICAL_FEATURES_V2_6: Tuple[str, ...] = (
    "has_horizon",
    "qnm_Q0_v2",
    "qnm_f1f0_v2",
    "qnm_g1g0_v2",
    "G2_large_x",
)
```

Las tres QNM siguen siendo críticas. La condición de activación no cambia: si el modelo fue
entrenado bajo v2.6 y la cobertura de train es adecuada, un punto real debe estar dentro de
soporte. Si aún así falla, es señal de Camino C (redefinición de observable).

---

## 3. Archivos a modificar

### Cambio mínimo requerido (Opción B)

| Archivo | Qué cambia | Notas |
|---|---|---|
| `feature_support.py` | Añadir `FEATURE_NAMES_V2_6`, `CRITICAL_FEATURES_V2_6` | No eliminar V2_5 ni V1 |
| `02_emergent_geometry_engine.py` | `build_feature_vector`: aplicar transformaciones v2; importar V2_6 | Ver §3.1 |
| `01b_generate_kerr_sandbox.py` | Escribir `qnm_Q0_v2`, `qnm_f1f0_v2`, `qnm_g1g0_v2` en attrs de H5 | Además de los campos raw v1 como compatibilidad |
| `02R_build_ringdown_boundary_dataset.py` | Ídem — escribir attrs v2 además de v1 | Ver §3.2 |
| `tests/test_feature_support.py` | Tests de paridad B vs C (ver §4) | |

### 3.1 Cambio en `build_feature_vector` (engine)

```python
# 3. Features QNM v2 (3 features): qnm_v2 log-scaled
import math as _math

qnm_Q0_raw   = float(boundary_data.get("qnm_Q0",   0.0))
qnm_f1f0_raw = float(boundary_data.get("qnm_f1f0", 0.0))
qnm_g1g0_raw = float(boundary_data.get("qnm_g1g0", 0.0))

qnm_Q0_v2   = _math.log1p(qnm_Q0_raw)
qnm_f1f0_v2 = _math.log(max(qnm_f1f0_raw, 1e-4))
qnm_g1g0_v2 = _math.log(max(qnm_g1g0_raw, 1e-4))

all_features.append(qnm_Q0_v2)
all_features.append(qnm_f1f0_v2)
all_features.append(qnm_g1g0_v2)
```

El cambio lee los mismos attrs raw (`qnm_Q0`, `qnm_f1f0`, `qnm_g1g0`) que ya escriben ambas
fuentes — no requiere regenerar los H5 existentes si no se quieren añadir los attrs `_v2`
explícitos. La transformación ocurre solo en `build_feature_vector`.

### 3.2 Attrs `_v2` en H5 (opcional pero recomendado)

Para trazabilidad, `01b` y `02R` deben escribir también:

```python
b.attrs["qnm_Q0_v2"]   = math.log1p(float(Q0))
b.attrs["qnm_f1f0_v2"] = math.log(max(float(f1f0), 1e-4))
b.attrs["qnm_g1g0_v2"] = math.log(max(float(g1g0), 1e-4))
b.attrs["qnm_contract"] = "v2"
```

Esto permite auditar los H5 directamente sin pasar por `build_feature_vector`.

---

## 4. Tests de aceptación

### 4.1 Test de paridad B vs C (nuevo)

Bajo `qnm_v2`, los rangos de features QNM de Slice B (Kerr sintético) y Slice C (bridge real)
deben solaparse en al menos un orden de magnitud en escala log, es decir, la distancia entre
los centroides debe ser menor que la suma de sus desviaciones estándar multiplicada por un
factor razonable.

Criterio formal: para cada feature `f ∈ {qnm_Q0_v2, qnm_f1f0_v2, qnm_g1g0_v2}`,

```
|mean_B(f) - mean_C(f)| < 3 * (std_B(f) + std_C(f))
```

Si el criterio no se cumple para `qnm_Q0_v2`, B y C siguen siendo distribuciones disjuntas en
esa feature: training los dos juntos no construye un soporte coherente.

### 4.2 Train support test

Sobre el dataset ensamblado A+B+C con v2:

```python
audit = audit_train_feature_support(
    feature_names=FEATURE_NAMES_V2_6,
    X_mean=X_all.mean(axis=0),
    X_std=X_all.std(axis=0),
    critical_features=CRITICAL_FEATURES_V2_6,
)
assert audit["verdict"] == "PASS"
assert "qnm_Q0_v2"   not in audit["critical_tiny_std_features"]
assert "qnm_f1f0_v2" not in audit["critical_tiny_std_features"]
assert "qnm_g1g0_v2" not in audit["critical_tiny_std_features"]
assert "has_horizon"  not in audit["critical_tiny_std_features"]
assert "G2_large_x"   not in audit["critical_tiny_std_features"]
```

### 4.3 GW150914 probe

```bash
python 02_emergent_geometry_engine.py \
  --mode inference \
  --checkpoint runs/<reopen_run_id>/02_emergent_geometry_engine/emergent_geometry_model.pt \
  --data-dir runs/gwosc_all/inference_input \
  --output-dir runs/<reopen_run_id>/reopen_probe_gw150914 \
  --experiment reopen_probe_gw150914
echo "Exit code: $?"
```

Criterio: `exit code = 0`, `n_gate_fail = 0`, sin `UNSUPPORTED_FEATURE_REGIME`.

### 4.4 Cohorte ancla

Misma verificación sobre GW151226 y GW170814.
Si cualquier evento ancla dispara gate fail, el checkpoint **no reabre 02**.

---

## 5. Criterio de escalación a Camino C

Si tras reentrenamiento A+B+C con `v2` el probe real (§4.3 / §4.4) sigue produciendo
`n_gate_fail > 0` en features QNM:

→ El problema no es de escala sino de definición del observable.  
→ Escalar a Camino C: redefinir QNM features usando un observable que sea consistente entre
   fuentes (e.g., frecuencia reducida, damping normalizado por masa estimada, estructura
   espectral del G2 en lugar de poles ESPRIT).

No escalar a C antes de completar B. Camino C requiere cambiar `01b`, `02R`, y todo el contrato
de features desde la generación de datos.

---

## 6. Versioning

| Versión | Feature list | QNM contract | Estado |
|---|---|---|---|
| V2_5 | `FEATURE_NAMES_V2_5` | raw linear | **CONGELADO** — evidencia de bloqueo |
| V2_6 | `FEATURE_NAMES_V2_6` | log-scaled v2 | **ACTIVO** — contrato de reapertura |

Un checkpoint entrenado bajo V2_5 no es válido para inferencia bajo V2_6 y viceversa.  
El campo `qnm_contract` en los H5 (§3.2) permite auditar de qué versión provienen los datos.

---

## 7. Checklist de reapertura bajo v2

- [ ] `feature_support.py`: `FEATURE_NAMES_V2_6` y `CRITICAL_FEATURES_V2_6` añadidos
- [ ] `build_feature_vector` actualizado (usa log-transform, lee raw attrs)
- [ ] `01b_generate_kerr_sandbox.py`: escribe `qnm_*_v2` attrs y `qnm_contract="v2"`
- [ ] `02R_build_ringdown_boundary_dataset.py`: ídem
- [ ] Slice C regenerada (o verificada) con `qnm_contract="v2"`
- [ ] Dataset A+B+C ensamblado con manifest canónico en `runs/<reopen_run_id>/02_reopen_dataset/`
- [ ] Audit pre-train: `verdict == "PASS"` con V2_6 / CRITICAL_FEATURES_V2_6
- [ ] Reentrenamiento desde cero bajo V2_6
- [ ] Train audit en summary: `feature_support_audit.verdict == "PASS"`
- [ ] GW150914 probe: exit 0, `n_gate_fail = 0`
- [ ] Cohorte ancla: `n_gate_fail = 0`
- [ ] `hoja_de_ruta.md` actualizado: 02 reabierto bajo `qnm_v2`
