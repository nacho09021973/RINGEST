# Diario día 3

## Estado al cierre

Hoy quedó cerrada una cadena causal bastante limpia en Carril B. La pregunta ya no es si el cuello estaba en Route C, en el clustering o en el ranking modal. La evidencia acumulada apunta a que el cuello real se fue desplazando hacia arriba hasta quedarse en la rama de anclaje temporal del extractor.

## Qué queda rescatado

### 1. `02_poles_to_dataset.py`: fix de signo
Se confirmó y corrigió un bug real de convención en la parte imaginaria de los polos. El dataset estaba construyendo `omega_im` con signo incompatible con la validación Kerr. Tras el fix, la física downstream dejó de estar artificialmente rota por convenio de signo.

**Veredicto:** RESCATAR.

### 2. `01_extract_ringdown_poles.py`: política v1.2 real
Se verificó que los supuestos defaults “v1.2” no estaban realmente activos en código y se asentó la política real:
- `rank=4`
- `require_decay=true`
- `max_modes=8`
- trazabilidad de versión actualizada

Esto cerró un falso diagnóstico: parte de los primeros canary no estaban midiendo v1.2 real, sino una mezcla de comportamiento heredado.

**Veredicto:** RESCATAR.

### 3. B4 (ventana temporal) como cuello real intermedio
La auditoría de ventana mostró causalidad fuerte:
- `start_offset=0.003`
- `duration=0.05`

condujeron en cohorte corta a una mejora física real respecto al baseline histórico. En esa fase, B4 sí explicó mejoría de física útil.

**Veredicto:** RESCATAR, pero no congelar todavía.

### 4. `--t0-rel` manual como herramienta diagnóstica
Se comprobó que fijar `t0_rel` a mano en microrejilla alrededor del brazo sano no añade física nueva: solo reproduce lo que el peak-picker automático ya hacía bien cuando estaba en un régimen sano.

**Veredicto:** RESCATAR como diagnóstico, ARCHIVAR como política.

## Qué queda archivado

### 1. `fmin30`
La comparación `--whiten-fmin-hz 20` vs `30` dejó un resultado robusto:
- `fmin30` mejora un poco métricas subespaciales (`lambda_4`, `lambda_4/lambda_5`)
- pero empeora la física útil downstream
- y en GW170104 desplaza patológicamente `t0_rel`

Conclusión: no rescata el pipeline; distorsiona el anclaje temporal.

**Veredicto:** ARCHIVAR.

### 2. Congelar B4 como política v1.3
La cohorte ampliada tumbó la ilusión inicial. `duration=0.05` y `start_offset=0.003` mejoran algunas métricas, pero no de forma robusta suficiente como para fijarlo como baseline provisional. En cohorte ampliada reaparecieron falsos matches a `chi=0` y no se sostuvo la mejora del mejor cluster.

**Veredicto:** ARCHIVAR como freeze global por ahora.

### 3. Seguir apretando solo `peak_search_start`
Se probó:
- `peak_search_start = -0.5, -0.1, 0.0`
- y luego `0.00, 0.02, 0.05`

Resultado:
- en el brazo sano, `0.00` queda como baseline útil
- al apretar de verdad (`0.02`, `0.05`) el efecto existe, pero es degradación, no estabilización

**Veredicto:** ARCHIVAR como única palanca.

### 4. `--peak-ref-smooth-samples 9`
Se introdujo una palanca experimental mínima sobre `y_ref`: suavizado por media móvil solo para peak-picking. La variante sí movió `t0_rel`, pero en la dirección equivocada; el caso más claro fue GW170104, con desplazamiento tardío importante sin mejora útil downstream.

**Veredicto:** ARCHIVAR la variante concreta. RESCATAR la conclusión causal: la siguiente familia de tiros sí vive en `y_ref` / rama de peak-picking.

## Hallazgo causal más importante del día

El cuello actual ya no está en:
- B3 (`_sort_and_filter`)
- downstream
- más tuning de `duration`
- más tuning de `whiten-fmin-hz`

El cuello está en **cómo se construye y se usa la referencia temporal para fijar `t_peak`**.

En código real:
- `y_ref` se construye actualmente como `|H1| + |L1|`
- `t_peak` se obtiene por `argmax(abs(y_ref[idxs]))`
- luego `t0_used = t_peak + start_offset`

La evidencia del día muestra que:
1. tocar `y_ref` sí mueve la física real,
2. pero el suavizado local no fue la implementación correcta,
3. y la siguiente familia de tiros mínimos ya está claramente en la **rama de peak-picking**, no en otra capa.

## Qué no tocar todavía

- `_sort_and_filter(...)`
- B3
- KAN / PySR / clustering
- core de ESPRIT
- más barridos grandes de `duration`
- más barridos de `fmin`
- fixes downstream cosméticos

## Siguiente tiro recomendado para mañana

La siguiente intervención mínima y causal ya no es suavizar `y_ref`, sino **cambiar la geometría de `y_ref`**.

El siguiente experimento recomendado es:
- baseline actual: `y_ref = |H1| + |L1|`
- comparar contra una variante: `y_ref = max(|H1|, |L1|)` punto a punto

Razonamiento:
- sigue en la misma capa causal correcta,
- no mete filtros nuevos,
- no toca la señal que entra a ESPRIT,
- no toca whitening,
- no toca B3,
- y ataca directamente la hipótesis de que la suma de módulos ensancha o desplaza el máximo temporal de forma no física.

## Qué subir a GitHub hoy

### Código
Subir sí o sí:
- `01_extract_ringdown_poles.py`
- `02_poles_to_dataset.py`
- `docs/diario_dia_3.md`

### Datos mínimos para poder seguir desde otro ordenador
Subir solo lo que evita recomputar lo ya costoso o frágil:
- datos canary base necesarios para continuar
- salidas de boundary/ringdown que vayas a reutilizar mañana
- CSV ad hoc de parámetros por evento usado en la auditoría upstream

Recomendación mínima:
- boundary inputs ya preparados para los eventos de control:
  - `GW150914`
  - `GW170104`
  - `GW190521_030229`
- cualquier directorio de salida que quieras conservar como referencia estable del audit de hoy, especialmente:
  - baseline sano usado en fmin20 / duration0.05 / peak_search_start=0.00
  - resultados del audit `peaksm9` solo si quieres preservar la falsación ya hecha

### Qué no hace falta subir si quieres mantener el repo limpio
- barridos completos redundantes que puedas rerun fácilmente desde boundary
- experimentos ya archivados y fácilmente recomputables, salvo que quieras trazabilidad estricta

## Checklist operativo para cerrar el día

1. Confirmar en `git status --short` qué cambios son código y qué cambios son runs/datos.
2. Añadir el resumen del día:
   - `docs/diario_dia_3.md`
3. Añadir solo los archivos de código y datos mínimos de continuidad.
4. Commit con mensaje claro.
5. Push a `main`.
6. Verificar desde GitHub web que están:
   - scripts modificados
   - resumen del día
   - datos mínimos para rerun/control

## Mensaje de commit sugerido

```bash
chore: close day 3 peak-picking audit and sync minimal canary assets
```

## Secuencia de push sugerida

```bash
# 1) mover el resumen al repo
cp /ruta/donde/lo/guardes/diario_dia_3.md docs/diario_dia_3.md

# 2) revisar cambios
 git status --short

# 3) añadir código y documentación
 git add 01_extract_ringdown_poles.py 02_poles_to_dataset.py docs/diario_dia_3.md

# 4) añadir solo los datos/runs mínimos que quieras preservar para continuar mañana
# Sustituye por las rutas exactas que decidas conservar:
# git add data/gwosc_events/GW150914/boundary/... \
#         data/gwosc_events/GW170104/boundary/... \
#         data/gwosc_events/GW190521_030229/boundary/... \
#         runs/upstream_whiten_timing_audit_params.csv

# 5) commit
 git commit -m "chore: close day 3 peak-picking audit and sync minimal canary assets"

# 6) push
 git push origin main
```

## Decisión final del día

- `fmin30`: archivado
- B4 freeze: archivado
- `t0_rel` manual como política: archivado
- `peak_search_start` como única palanca: archivado
- familia causal correcta: **`y_ref` / rama de peak-picking**
- siguiente tiro: **comparar `sumabs` vs `maxabs` en `y_ref`**, sin tocar ESPRIT ni downstream
