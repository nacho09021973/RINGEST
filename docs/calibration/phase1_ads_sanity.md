# Phase 1 — AdS sanity check

## 1. Objetivo

Comprobar si Stage 03 produce una señal razonable de "esto es Einstein/AdS" sobre
entradas AdS sintéticas conocidas. Es el paso previo a cualquier intento de
calibrar el `einstein_score`: si el score no separa AdS sintético de no-AdS, no
tiene sentido mover pesos ni umbrales.

## 2. Artefactos inspeccionados

- Inputs sandbox AdS (fuente primaria): `runs/ads_gkpw_20260416_091407/01_generate_sandbox_geometries/ads_d*_Tfinite_known_*.h5`
  (contienen `z_grid`, `A_of_z`, `f_of_z`, y grupo `bulk_truth` con `R_truth`, `A_truth`, `f_truth`, `G_trace_truth`)
- Outputs emergidos del checkpoint canónico sobre esos mismos inputs:
  `runs/ads_gkpw_20260416_091407/02_emergent_geometry_engine/geometry_emergent/ads_d*_known_*_emergent.h5`
- Stage 03 smoke ya existente en disco (no utilizable como evidencia):
  `runs/ads_gkpw_smoke_20260415_184946/03_discover_bulk_equations/outputs/einstein_discovery_summary.json`
  (su Stage 02 upstream es el modelo humo de 5 epochs, no el canónico)
- Script auditado: `03_discover_bulk_equations.py`
  - `compute_geometric_tensors` (fórmula de Ricci numérica)
  - `validate_einstein_posterior` (banderas y score)

## 3. Hallazgo B1 — problema del observable `R_constant`

La métrica del pipeline usa el gauge declarado en `03_discover_bulk_equations.py`:

```
ds^2 = e^{2A(z)} [-f(z) dt^2 + dx^2] + dz^2/f(z)
R(z) = -2 D A''(z) - D(D-1) A'(z)^2 - (f'(z)/f(z)) A'(z)
```

Para AdS puro con `A(z) = -log(z/L)` y `f(z) = 1`, al sustituir se obtiene:

```
R(z) = -D(D+1) / z^2
```

Es decir, en este gauge la curvatura AdS es **explícitamente dependiente de `z`**,
no constante. Esto lo indica el propio comentario del código
(`03_discover_bulk_equations.py`, bloque de documentación de la fórmula).

Consecuencia directa:

- `validate_einstein_posterior` define `R_constant = (cv(R) < 0.15)`.
- Sobre AdS puro el `cv(R)` es grande por el factor `1/z^2`, no por ruido.
- Medido hoy sobre `bulk_truth/R_truth` del sandbox (5 eventos, d = 3, 4, 5):
  `cv ≈ 15.97` en todos los casos.
- Medido hoy sobre `compute_geometric_tensors` aplicado a `A_of_z`, `f_of_z`
  del mismo sandbox: `cv ≈ 5.5–5.9`.
- Por tanto `R_constant` **no puede dispararse** en AdS con este gauge, ni
  siquiera sobre ground truth.

Lectura útil para mañana: `cv(R) < 0.15` está mal planteado como criterio de
"AdS constante". Para este gauge, el observable natural sería algo como
`cv(R · z^2)` o un residuo `|R · z^2 + D(D+1)| / D(D+1)`. No se decide aquí
cuál usar; solo se deja registrado que la bandera actual es mathématicamente
incompatible con el gauge del pipeline.

## 4. Hallazgo B2 — fallo del checkpoint canónico sobre AdS conocido

Aplicando `compute_geometric_tensors` + `validate_einstein_posterior` (tal cual
están en `03_discover_bulk_equations.py`, sin PySR) sobre
`runs/ads_gkpw_20260416_091407/02_emergent_geometry_engine/geometry_emergent/ads_d3_Tfinite_known_*_emergent.h5`
(5 muestras, AdS conocido emergido por el propio checkpoint canónico):

| evento | `R_mean` | `cv` | `R_constant` | `R_negative` | `R_significant` | score | verdict |
|---|---|---|---|---|---|---|---|
| ads_d3_Tfinite_known_002 | −0.057 | 10.50 | False | False | False | 0.00 | NON_EINSTEIN_OR_DEFORMED |
| ads_d3_Tfinite_known_004 | −0.055 | 10.69 | False | False | False | 0.00 | NON_EINSTEIN_OR_DEFORMED |
| ads_d3_Tfinite_known_005 | −0.061 | 10.50 | False | False | False | 0.00 | NON_EINSTEIN_OR_DEFORMED |
| ads_d3_Tfinite_known_008 | −0.055 | 10.64 | False | False | False | 0.00 | NON_EINSTEIN_OR_DEFORMED |
| ads_d3_Tfinite_known_009 | −0.053 | 10.86 | False | False | False | 0.00 | NON_EINSTEIN_OR_DEFORMED |

Interpretación operativa:

- `|R_mean|` colapsa a ~`0.05`, muy por debajo del umbral duro `|R| > 0.5`.
- Se pierden simultáneamente `R_negative` (mean > −0.1), `R_significant` y cualquier
  bonus de R².
- El score canónico da `0.00` en el carril positivo canónico. No hay cohorte
  positiva utilizable sobre la que calibrar.

Este hallazgo es coherente con las métricas de test declaradas por el propio
checkpoint (`A_r2 = -0.064`, `R_r2 ≈ 0`); ver `docs/calibration/stage02_reference_lock.md`.

## 5. Consecuencia metodológica

Hoy **no se puede** pasar a calibrar el `einstein_score`.

Antes hay que resolver al menos uno de los dos bloqueos:

- `B1` (gauge): sustituir o reformular la bandera `R_constant` por un observable
  que tenga sentido en el gauge 1/z^2 del pipeline.
- `B2` (checkpoint): obtener un Stage 02 cuya salida emergida sobre AdS conocido
  no colapse `|R|` por debajo de los umbrales duros; sin eso, ninguna calibración
  tiene un positivo canónico.

Resolver solo uno de los dos no es suficiente: `B1` sin `B2` mantiene el carril
sin positivos usables; `B2` sin `B1` mantiene `R_constant` inalcanzable sobre AdS.

## 6. Estado de Fase 1

- `FASE_1_COMPLETADA_CON_ARTEFACTOS_EXISTENTES: parcial`
  - Razón: los artefactos Stage 03 ya en disco
    (`runs/ads_gkpw_smoke_20260415_184946/03_discover_bulk_equations/`) no son
    utilizables porque su Stage 02 upstream es humo. La evidencia concluyente
    requirió una comprobación mínima no destructiva hoy: lectura de `.h5` +
    `compute_geometric_tensors` + `validate_einstein_posterior` en memoria, sin
    PySR y sin re-ejecutar stages. No se persistió ningún artefacto nuevo más
    allá de este documento.
- `BLOQUEO_CRITICO_ANTES_DE_CALIBRAR: sí`
  - Bloqueos: B1 (gauge) y B2 (checkpoint), ambos descritos arriba.

## 7. Próximo paso mínimo

Decidir si se ataca primero B1 (rediseño mínimo del observable: pasar de
`cv(R)` a `cv(R · z^2)` o residuo `|R · z^2 + D(D+1)|`) o B2 (diagnóstico de por
qué el checkpoint canónico degrada `|R|` en AdS, empezando por los pesos
`loss_weights.R = 0.001`). No abrir ambos a la vez.

## 8. Rutas exactas relacionadas

- Inputs sandbox AdS: `runs/ads_gkpw_20260416_091407/01_generate_sandbox_geometries/*.h5`
- Outputs emergidos canónicos: `runs/ads_gkpw_20260416_091407/02_emergent_geometry_engine/geometry_emergent/*.h5`
- Checkpoint de referencia: `runs/ads_gkpw_20260416_091407/02_emergent_geometry_engine/emergent_geometry_model.pt`
- Summary del entrenamiento: `runs/ads_gkpw_20260416_091407/02_emergent_geometry_engine/emergent_geometry_summary.json`
- Smoke Stage 03 (no utilizable): `runs/ads_gkpw_smoke_20260415_184946/03_discover_bulk_equations/outputs/einstein_discovery_summary.json`
- Script auditado: `03_discover_bulk_equations.py`
- Lock hermano: `docs/calibration/stage02_reference_lock.md`
