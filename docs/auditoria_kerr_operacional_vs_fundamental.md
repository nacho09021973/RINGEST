# Auditoría Kerr: polos operacionales vs fundamental esperado

## Objetivo

Dejar por escrito el hallazgo metodológico cerrado en la revisión del carril:

`01_extract_ringdown_poles.py` -> `02_poles_to_dataset.py` -> `05_validate_qnm_kerr.py`

Sin abrir más análisis río arriba y sin convertir esto en una reescritura del extractor.

## Hechos verificados

### 1. `chi_final` es metadato externo

- En `02_poles_to_dataset.py`, `chi_final` se carga desde una tabla externa `event,M_final_Msun,chi_final`.
- Se propaga al dataset sin modificación.
- En `05_validate_qnm_kerr.py`, `chi_final` no participa en decisiones del pipeline ni en el veredicto global.
- Solo se usa para auditoría y agregados (`chi_final_mean`, `chi_final_median`).

### 2. `ref_chi` en `05_validate_qnm_kerr.py` no es spin inferido

- `nearest_kerr_mode()` asigna el punto de la tabla Kerr más cercano por distancia euclídea en el plano `(omega_re_norm, omega_im_norm)`.
- `ref_chi` es el `chi` de esa fila de referencia.
- No hay interpolación, ajuste, inversión de parámetros ni propagación de incertidumbres.
- El veredicto `PARTIAL_KERR_CONSISTENCY` es una contabilidad geométrica de centroides, no una validación física de `chi_final`.

### 3. Los clusters no caen donde Kerr esperaría para el `chi_final` externo

- En el run auditado, los `chi_final_mean` por cluster están alrededor de `0.68-0.72`.
- Los `ref_chi` geométricos de los centroides caen en valores discretos que no siguen ese patrón (`0.00`, `0.99`, etc.).
- La nueva métrica `delta_chi_vs_external` hace explícita esta tensión dentro del `cluster_audit_summary.json`.

### 4. `mode_rank` no significa "fundamental Kerr" ni "máxima amplitud pura"

- El orden lo fija `_sort_and_filter()` en `01_extract_ringdown_poles.py`.
- La regla real es:

```python
order = np.lexsort((-amp, -np.imag(w)))
```

- Esto significa:
  - primero, polos menos amortiguados (`Im(w)` más cerca de `0` desde abajo)
  - después, amplitud mayor como criterio secundario
- Por tanto:
  - `mode_rank = 0` = primer polo retenido tras ese ordenado
  - no = QNM fundamental identificado
  - no = dominante por amplitud en sentido estricto

### 5. El filtro `omega_re_norm <= 1.02` no es el que elimina el fundamental esperado

- Para `GW150914`, en el dataset no podado de la cohorte auditada solo aparecen dos polos.
- Esos dos mismos polos ya están en `poles_joint.csv` y en `qnm_dataset.csv`.
- No hay un tercer o cuarto polo de `GW150914` oculto que haya sido descartado por el corte `omega_re_norm <= 1.02`.
- En este run, el extractor conjunto simplemente no produjo un polo más cercano al fundamental Kerr esperado para ese evento.

## Verificación concreta con GW150914

### Aritmética

Fila auditada:

- `freq_hz = 207.4476`
- `M_final_Msun = 68.0`
- `chi_final = 0.69`
- `omega_re_norm = 0.43656`
- `omega_im_norm = -0.02058`

La normalización cierra:

`omega_re_norm = 2 pi freq_hz M_final G/c^3`

Resultado:

- la normalización es correcta
- el problema no está en unidades

### Física

Para ese mismo evento:

- el polo `rank 0` sale cerca de `207 Hz`
- eso queda por debajo del fundamental Kerr `l=m=2, n=0` esperado para un remanente con `chi ~ 0.69`
- por eso el match Kerr sale `fair` y no `good`

Conclusión:

- el problema no es `05_validate_qnm_kerr.py`
- el problema no es la normalización
- el problema está río arriba, en qué polos produce y retiene el extractor operacional

## Sobre la tabla de parámetros externos

Hecho importante:

- el run auditado no usa el `catalog_params.csv` actual del repo
- usa `runs/audit_envsum_v3/cohort_params_7.csv`

Para `GW150914`:

- `cohort_params_7.csv` usa `M_final_Msun = 68.0`
- `catalog_params.csv` actual usa `M_final_Msun = 63.1`

Esto no invalida la auditoría principal, pero sí obliga a no mezclar cohortes de parámetros al interpretar resultados físicos.

## Qué significa este hallazgo

Resumen honesto:

- el pipeline actual extrae polos operacionales poco amortiguados
- luego los agrupa
- luego los compara geométricamente contra una tabla Kerr

Pero:

- los polos operacionales menos amortiguados no son, en general, el QNM fundamental Kerr esperado

Por tanto:

- el análisis Kerr actual no puede sostener una afirmación fuerte del tipo
  "el pipeline está identificando el fundamental Kerr de los remanentes"

Sí puede sostener, en cambio, una afirmación más modesta:

- "el pipeline caracteriza polos operacionales del post-pico y mide su cercanía geométrica a una tabla Kerr discreta"

## Estado de la hipótesis

Hipótesis descartadas en esta auditoría:

- bug trivial de normalización
- `ref_chi` como inferencia física de spin
- `mode_rank = 0` como proxy fiable de fundamental Kerr
- filtro `omega_re_norm <= 1.02` como causa de desaparición del fundamental esperado

Hipótesis que quedan abiertas, pero no se atacan en este documento:

- ventana temporal del ringdown
- preprocesado
- merge H1/L1
- política de rango y filtrado del extractor
- procedencia física exacta de algunas cohortes de masa/espín

## Decisión de parada

Se para aquí de forma deliberada.

Razón:

- ya hay un hallazgo metodológico suficiente
- seguir río arriba implica una investigación real del extractor ESPRIT, no una verificación rápida
- no conviene encadenar más "un paso río arriba" sin redefinir explícitamente la pregunta física

## Veredicto

- `01_extract_ringdown_poles.py`: `RESCATAR`
- `02_poles_to_dataset.py`: `RESCATAR`
- `05_validate_qnm_kerr.py`: `RESCATAR`

Pero la interpretación correcta del carril auditado es:

- `pipeline operacional de polos`
- no `identificador limpio del fundamental Kerr`
