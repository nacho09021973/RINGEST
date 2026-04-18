# Diario día 5

## Estado al cierre

Hoy quedó cerrada la primera ejecución real de **Ruta C canónica** sobre el baseline ya congelado.

La pregunta del día ya no era si el extractor upstream seguía moviéndose. Eso quedó atrás. La pregunta útil pasó a ser:

- si el dataset canónico ya permite extraer relaciones empíricas reales,
- si aparecen familias observacionales no triviales,
- y si esas relaciones sobreviven al filtrado.

La respuesta corta es:

- **sí** aparecen relaciones empíricas, sobre todo en `damping_hz`
- **no** aparece todavía consistencia Kerr robusta
- y la poda extrema `best_per_event` **no** mejora el cuadro físico

## Qué quedó congelado

El artefacto canónico baseline quedó fijado en:

- `runs/qnm_dataset_canonical_7ev/qnm_dataset.csv`
- `runs/qnm_dataset_canonical_7ev/qnm_dataset_manifest.json`

Además quedaron dos carriles derivados:

### 1. `canonical_all`
Dataset observacional completo del baseline canónico.

Uso:
- cobertura fenomenológica
- clustering observacional
- búsqueda de relaciones empíricas sin podar demasiado pronto

### 2. `canonical_filtered`
Versión filtrada con criterio físico más estricto:
- `pole_source == poles_joint.json`
- exclusión de filas con `ref_chi == 0.0`

Uso:
- PySR más limpio
- prueba de robustez frente a filtrado físico mínimo

### 3. `canonical_best_per_event`
Solo la mejor fila por evento según `relative_rms`.

Uso:
- control diagnóstico
- no como carril principal

## Perfil físico de los tres carriles

### `canonical_all`
- 24 filas
- 7 eventos
- `fair = 7`
- `poor = 17`

### `canonical_filtered`
- 18 filas
- 7 eventos
- elimina todos los `ref_chi == 0.0`
- `fair = 3`
- `poor = 15`

### `canonical_best_per_event`
- 7 filas
- 7 eventos
- todos con `mode_rank = 0`
- mantiene dos `ref_chi == 0.0` espurios:
  - `GW151012`
  - `GW190521_030229`

Conclusión:
- `best_per_event` no limpia de verdad el problema físico
- solo reduce cobertura

## Hallazgo técnico importante

Hoy apareció y se corrigió un bug real en `03_discover_qnm_equations.py`.

El filtro de filas válidas estaba tratando valores `0` como falsy y los convertía en `NaN`.

Eso rompía justo el carril `best_per_event`, porque:
- todos sus rows tienen `mode_rank = 0`
- y el script los descartaba como si no fueran finitos

Tras el fix, `best_per_event` volvió a producir ecuaciones reales.

**Veredicto:** RESCATAR el fix.

## Saneamiento del entorno Ruta C

Hoy también quedó resuelto el bloqueo de entorno que impedía correr PySR y KAN de verdad.

### PySR / Julia
Se instanció correctamente el entorno Julia del proyecto con:
- `PythonCall`
- `SymbolicRegression`

### KAN
Se instaló `pykan` y dependencias faltantes:
- `PyYAML`
- `matplotlib`

Además se ajustó `04_kan_qnm_classifier.py` para compatibilidad con la API real de `pykan 0.2.8`, usando `fit(...)` en lugar de asumir `train(...)`.

**Veredicto:** RESCATAR el saneamiento de entorno y el parche de compatibilidad.

## PySR: relaciones empíricas encontradas

### `canonical_all`
PySR encontró 4/4 ecuaciones.

Resultados principales:
- `freq_hz`: `R² = 0.3482`
- `damping_hz`: `R² = 0.9854`
- `omega_re_norm`: `R² = 0.3781`
- `omega_im_norm`: `R² = 0.2186`

Lectura:
- la señal fuerte está en `damping_hz`
- la física en el plano normalizado sigue siendo débil

### `canonical_filtered`
PySR también encontró 4/4 ecuaciones.

Resultados principales:
- `freq_hz`: `R² = 0.3725`
- `damping_hz`: `R² = 0.9922`
- `omega_re_norm`: `R² = 0.4626`
- `omega_im_norm`: `R² = 0.2014`

Lectura:
- el filtrado mejora ligeramente `freq_hz`
- mejora algo `omega_re_norm`
- y da el mejor ajuste de todo el día en `damping_hz`

### `canonical_best_per_event`
Tras corregir el bug de `mode_rank=0`, también encontró 4/4 ecuaciones.

Resultados principales:
- `freq_hz`: `R² = 0.7638`
- `damping_hz`: `R² = 0.7018`
- `omega_re_norm`: `R² = 0.3148`
- `omega_im_norm`: `R² = 0.1676`

Lectura:
- `freq_hz` sube artificialmente por poda extrema y muestra mínima
- pero `damping_hz` cae mucho
- y la parte normalizada no mejora

Conclusión global de PySR:

1. la relación empírica más robusta del día vive en `damping_hz`
2. el carril útil para PySR no es `best_per_event`
3. `canonical_filtered` es el mejor carril estricto para ecuaciones

## KAN: familias observacionales

### `canonical_all`
- 3 clusters
- `accuracy = 1.000`

Centroides observacionales:
- `(2.3869, -0.2592)` con 11 filas
- `(1.0321, -0.0421)` con 6 filas
- `(0.2847, -0.0404)` con 7 filas

### `canonical_filtered`
- 3 clusters
- `accuracy = 0.944`

Centroides observacionales:
- `(2.2952, -0.0475)` con 10 filas
- `(0.9470, -0.0390)` con 7 filas
- `(3.3047, -2.3765)` con 1 fila

Lectura:
- aparece un singleton extremo
- eso daña la limpieza física del clustering

### `canonical_best_per_event`
- 3 clusters
- `accuracy = 1.000`

Centroides observacionales:
- `(2.5459, -0.0036)` con 3 filas
- `(0.2877, -0.0159)` con 3 filas
- `(1.2315, -0.0027)` con 1 fila

Lectura:
- otra vez aparece un singleton
- con solo 7 puntos la separación interna deja de ser una prueba fuerte

Conclusión global de KAN:

- `canonical_all` sigue siendo el carril más útil para clustering observacional
- `canonical_filtered` sirve como prueba de robustez, pero introduce degeneración
- `best_per_event` no es un carril principal fiable

## Validación Kerr

Los tres carriles terminan con el mismo veredicto:

**`NO_KERR_CONSISTENCY`**

### `canonical_all`
- `24 rows matched`
- `fair = 7`
- `poor = 17`
- mejor cluster `fair` asociado a `chi ≈ 0.00`

### `canonical_filtered`
- `18 rows matched`
- `fair = 3`
- `poor = 15`
- el filtrado elimina `chi≈0` a nivel de fila, pero no rescata consistencia Kerr global

### `canonical_best_per_event`
- `7 rows matched`
- `fair = 2`
- `poor = 5`
- vuelve a aparecer un cluster `fair` anclado en `chi ≈ 0.00`

Conclusión:
- filtrar más no está produciendo una familia Kerr más limpia
- la poda extrema tampoco rescata consistencia física

## Qué queda rescatado

### 1. Ruta C ya produce observables reales
Por primera vez quedó ejecutada de punta a punta sobre un dataset canónico estable:
- dataset congelado
- PySR real
- KAN real
- validación Kerr real

**Veredicto:** RESCATAR.

### 2. `canonical_all` como carril principal de familias observacionales
Es el carril con mejor equilibrio entre:
- cobertura
- clustering útil
- y estabilidad de estructura

**Veredicto:** RESCATAR como carril principal.

### 3. `canonical_filtered` como carril estricto para PySR
Da la mejor relación para `damping_hz` y sirve como control serio de robustez.

**Veredicto:** RESCATAR como carril secundario estricto.

### 4. Fix de `mode_rank=0` en `03_discover_qnm_equations.py`
Era un bug real que sesgaba cualquier dataset con ceros legítimos.

**Veredicto:** RESCATAR.

## Qué queda archivado

### 1. `canonical_best_per_event` como carril principal
No mejora la física.
No mejora Kerr.
No mejora el plano normalizado.
Solo reduce cobertura y mete estructura demasiado frágil.

**Veredicto:** ARCHIVAR como carril principal. Mantener solo como diagnóstico.

### 2. La idea de que “más filtrado” arregla automáticamente Kerr
La evidencia de hoy no sostiene eso.

`canonical_filtered` mejora algunas ecuaciones, pero no rescata consistencia Kerr.

**Veredicto:** ARCHIVAR como expectativa automática.

## Decisión final del día

- baseline upstream: congelado
- Ruta C: operativa y sana
- carril principal: `canonical_all`
- carril secundario estricto: `canonical_filtered`
- carril diagnóstico: `canonical_best_per_event`
- veredicto Kerr global: todavía **no consistente**

## Siguiente paso recomendado

La siguiente pregunta útil ya no es de peak-picking ni de entorno.

La siguiente pregunta útil es:

**¿por qué `damping_hz` sí muestra relaciones empíricas robustas, mientras el plano normalizado `omega_re_norm / omega_im_norm` sigue sin organizarse en familias Kerr limpias?**

Eso sugiere que el próximo tiro no debería ser:
- más poda trivial
- más tuning de extractor
- ni más cambalaches de entorno

Sino una auditoría física centrada en:
- outliers del plano normalizado
- posibles mezclas de familias no-Kerr
- y cómo se distribuyen los `mode_rank` altos dentro de los clusters observacionales

## Veredicto corto

**SEGUIR POR RUTA C CANÓNICA**

pero ya con una conclusión más fina:

- `canonical_all` para familias observacionales
- `canonical_filtered` para ecuaciones empíricas más estrictas
- `best_per_event` solo como control diagnóstico, no como carril principal
