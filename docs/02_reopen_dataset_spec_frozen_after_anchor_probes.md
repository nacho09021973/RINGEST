# Spec de reapertura de stage 02 — Dataset canónico y criterios de aceptación

**Estado:** borrador v1.0 — 2026-04-11  
**Contexto:** stage 02 está contractualmente bloqueado desde que el gate de feature support
(`feature_support.py`) confirmó que el checkpoint `sandbox_serio_v1` tiene 5 critical features
congeladas en train. Este documento define el dataset mínimo y el checkpoint candidato que deben
existir para desbloquear el stage.

---

## 0. Por qué está bloqueado: diagnóstico auditado

El checkpoint `runs/sandbox_serio_v1/02_emergent_geometry_engine/emergent_geometry_model.pt`
fue entrenado **solo con geometrías holográficas** (sin Kerr).

Consecuencia directa, verificada por inspección del checkpoint:

| Feature | mean | std_raw | Causa del congelamiento |
|---|---|---|---|
| `has_horizon` | 1.0 | ≈0 | Holográfico siempre tiene `T>0` → `float(T>1e-10)=1` constante |
| `qnm_Q0` | 0.0 | ≈0 | Holográfico no escribe `qnm_*` attrs → `build_feature_vector` lee 0 |
| `qnm_f1f0` | 0.0 | ≈0 | Ídem |
| `qnm_g1g0` | 0.0 | ≈0 | Ídem |
| `G2_large_x` | 0.0006 | 0.0044 | Holográfico G2 decae rápido; GW150914 real produce x=0.19 → z≈44 |

En inference sobre GW150914:
- `has_horizon=0` (02R escribe `temperature=0`) vs mean_train=1 → **TINY_STD**
- `qnm_Q0=1124.9` vs mean_train=0 → **TINY_STD**
- `qnm_f1f0=8.41` vs mean_train=0 → **TINY_STD**
- `qnm_g1g0=1.58` vs mean_train=0 → **TINY_STD**
- `G2_large_x=0.19` → z=43.8 → **OFF_SUPPORT + CLIP_RISK**

Más epochs sobre el mismo dataset no arreglan nada: la varianza sigue siendo cero.

---

## 1. Definición del dataset de reapertura

### 1.1 Estructura canónica de salida

```
runs/<reopen_run_id>/02_reopen_dataset/
  geometries_manifest.json          ← manifest consumible por 02 train
  <name_holo_N>.h5                  ← Slice A
  <name_kerr_N>.h5                  ← Slice B
  <name_bridge_N>.h5                ← Slice C (opcional para v1, mandatorio para v2)
  dataset_audit.json                ← estadísticas por feature, criterios PASS/FAIL
```

El manifest debe seguir el esquema que ya consume `run_train_mode`:

```json
{
  "geometries": [
    {"name": "<name>", "category": "known"},
    {"name": "<name>", "category": "test"}
  ]
}
```

### 1.2 Tres slices requeridos

#### Slice A — Holográfico (base, ya existe)

**Fuente:** `01_generate_sandbox_geometries.py`  
**Propósito:** cubre `G2_*`, `GR_*`, `thermal_scale`, `central_charge_eff`, `d`  
**Requisito mínimo:** ≥80 geometrías, mix de families `ads`, `lifshitz`, `hyperscaling`, `deformed`

Campos H5 requeridos en `boundary/`:
```
datasets: G2_<O>, x_grid, G_R_real, G_R_imag, omega_grid, k_grid,
          temperature, central_charge_eff, d
attrs:    family, d, temperature
bulk_truth/ group: A_truth, f_truth, R_truth, z_grid, z_h, family, d
```

Restricción crítica: **el slice A por sí solo deja `has_horizon=1` constante**.
Esta restricción se resuelve con Slice B.

#### Slice B — Kerr / QNM (requerido para descongelar QNMs)

**Fuente:** `01b_generate_kerr_sandbox.py` (ya existente, `runs/kerr_sandbox_v1/`)  
**Propósito:** aportar varianza en `qnm_Q0`, `qnm_f1f0`, `qnm_g1g0`; y también en
`has_horizon` (Kerr escribe `temperature=0` → `has_horizon=0`)  
**Requisito mínimo:** ≥40 geometrías, rango M∈[25,150] M☉, a/M∈[0.1,0.9]

Campos H5 requeridos en `boundary/`:
```
datasets: G2_O1, x_grid, G_R_real, G_R_imag, omega_grid, k_grid,
          temperature (=0.0), central_charge_eff (=0.0), d
attrs:    family="kerr", d, qnm_Q0, qnm_f1f0, qnm_g1g0, qnm_n_modes
```

**Nota:** Kerr no tiene `bulk_truth` — el entrenamiento ya lo maneja vía `has_bulk_mask=False`.

**Restricción semántica `qnm_f1f0`:**  
`01b` computa `f1f0 = by_amp[1].freq_hz / by_amp[0].freq_hz` (ratio por amplitud).
`02R` computa exactamente igual (mismo código `_compute_qnm_features`).
Esto es consistente. Sin embargo, si `by_amp[1]` es una resonancia espuria, el ratio puede
ser absurdo. El gate ya detecta valores fuera de `[0.5, 20]` con `semantic_warning`.
No cambiar la semántica sin versionar el contrato.

#### Slice C — Bridge real-like (recomendado para v1, mandatorio para v2)

**Fuente:** `02R_build_ringdown_boundary_dataset.py` sobre eventos GWOSC con buena SNR  
**Propósito:** llevar el soporte de train al régimen real; sin Slice C, el modelo aprende
la distribución Kerr sintético pero puede seguir fuera de soporte para ringdown real  
**Requisito mínimo para v1:** al menos GW150914 + 2-3 eventos ancla (GW151226, GW170814)  
**Campos H5:** misma semántica que 02R produce — ver campos escritos por `02R` en boundary/ attrs

Diferencia importante respecto a Slice A/B: **no tiene `bulk_truth`**.
Estos ejemplos aportan cobertura de soporte en inferencia, no supervisión de reconstrucción.

---

## 2. Condiciones estadísticas mínimas del dataset ensamblado

Estas condiciones deben verificarse en `dataset_audit.json` **antes de entrenar**.
La función `audit_train_feature_support` de `feature_support.py` las verifica
automáticamente post-train; este audit pre-train es adicional.

| Condición | Mínimo requerido |
|---|---|
| `std(has_horizon) > 1e-4` | Mix A+B cubre esto (A→1, B→0) |
| `std(qnm_Q0) > 0.1` | Slice B con ≥40 geometrías Kerr |
| `std(qnm_f1f0) > 0.05` | Slice B con variación de a/M |
| `std(qnm_g1g0) > 0.05` | Ídem |
| `max(G2_large_x) > 0.05` | Slice B o C (Kerr G2 real tiene largo x) |
| Sin critical feature con `std < 1e-6` tras ensamblado | Verificado por audit |
| `has_horizon` tiene al menos 2 valores distintos (0 y 1) | Mix A+B |

Script de verificación pre-train (añadir como paso explícito antes de `run_train_mode`):

```python
from feature_support import audit_train_feature_support, FEATURE_NAMES_V2_5
import numpy as np

X_all = np.stack([build_feature_vector(bd, ops) for bd, ops in dataset])
audit = audit_train_feature_support(
    feature_names=FEATURE_NAMES_V2_5,
    X_mean=X_all.mean(axis=0),
    X_std=X_all.std(axis=0),   # raw, without floor
)
assert audit["verdict"] == "PASS", audit["verdict_reason"]
```

---

## 3. Criterios de aceptación del checkpoint candidato

Un checkpoint candidato `runs/<reopen_run_id>/02_emergent_geometry_engine/emergent_geometry_model.pt`
**reabre stage 02** si y solo si cumple **todas** las condiciones siguientes:

### 3.1 Audit de train (persistido en `emergent_geometry_summary.json`)

```json
"feature_support_audit": {
  "verdict": "PASS",
  "tiny_std_features": [],
  "critical_tiny_std_features": []
}
```

Ninguna de estas features puede tener `std_raw < 1e-6`:
`has_horizon`, `qnm_Q0`, `qnm_f1f0`, `qnm_g1g0`, `G2_large_x`

### 3.2 Probe real sobre GW150914

```bash
python 02_emergent_geometry_engine.py \
  --mode inference \
  --checkpoint runs/<reopen_run_id>/02_emergent_geometry_engine/emergent_geometry_model.pt \
  --data-dir runs/gwosc_all/GW150914/g2_contract_validation/contracted_boundary \
  --output-dir runs/<reopen_run_id>/reopen_probe_gw150914 \
  --experiment reopen_probe_gw150914
echo "Exit code: $?"
```

Resultado esperado:
- **exit code: 0**
- `feature_support_report.json` → `n_gate_fail: 0`
- ningún sistema con `gate_status: "UNSUPPORTED_FEATURE_REGIME"`
- ningún `critical_features_triggered`
- cero `clip_risk` (ningún `|z| > 10`)

### 3.3 Probe sobre cohorte ancla (recomendado)

Misma verificación repetida sobre GW151226 y GW170814.
Si alguno de los eventos ancla dispara gate fail, el checkpoint **no reabre 02** aunque GW150914 pase.

### 3.4 Artefactos canónicos esperados

```
runs/<reopen_run_id>/02_emergent_geometry_engine/
  emergent_geometry_model.pt
  emergent_geometry_summary.json    ← feature_support_audit.verdict == "PASS"
  stage_summary.json                ← status == "OK"
runs/<reopen_run_id>/reopen_probe_gw150914/
  feature_support_report.json       ← n_gate_fail == 0
  emergent_geometry_summary.json    ← n_gate_fail == 0
  stage_summary.json                ← status == "OK"
```

---

## 4. Dos caminos de reapertura (y cuál no está admitido)

### Camino 1 — Mantener contrato de features actual (recomendado para v1)

Ensamblar dataset A+B+C, verificar condiciones estadísticas, reentrenar.
No tocar `build_feature_vector` ni `FEATURE_NAMES_V2_5`.

**Riesgo residual:** si los rangos de `qnm_f1f0` en Kerr sintético siguen sin cubrir el régimen
real (GW150914: f1f0≈8.4), el checkpoint puede pasar el audit de train pero fallar el probe real.
En ese caso, revisar la distribución de M y a/M en Slice B para ampliar el rango.

### Camino 2 — Cambiar contrato de features

Si tras Camino 1 alguna critical feature sigue fuera de régimen en probe real, revisar la semántica
**upstream**: orden de polos en `_compute_qnm_features`, escala de `qnm_Q0`, definición de
`has_horizon` en el bridge real.

Cualquier cambio de semántica requiere:
1. Nueva versión de `FEATURE_NAMES_V2_5` o nueva feature list nombrada
2. Actualización del gate en `feature_support.py`
3. Nuevo checkpoint desde cero (no fine-tune del candidato)
4. Versionar el contrato en este documento

**No admitido:** reabrir 02 con un checkpoint cuyo probe real produce gate fail,
aunque el audit de train sea PASS. Ambas condiciones son conjuntamente necesarias.

---

## 5. Acción inmediata recomendada

1. **Verificar si `runs/kerr_sandbox_v1/` ya tiene el formato correcto** para ser
   consumido directamente por `run_train_mode` (manifest + H5 con bulk_truth/Kerr placeholder).
2. **Ensamblar manifest mixto** A+B (holográfico + Kerr) con `merge_manifests.py` o equivalente.
3. **Ejecutar audit pre-train** para confirmar condiciones estadísticas antes de entrenar.
4. **Reentrenar 02** con el dataset mixto.
5. **Ejecutar probe real** sobre GW150914 y cohorte ancla.
6. Si probe pasa → reapertura de 02, actualizar `hoja_de_ruta.md`.
7. Si probe falla en `G2_large_x` o `qnm_f1f0` → añadir Slice C y/o revisar rangos de Slice B.
