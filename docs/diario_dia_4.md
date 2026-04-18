# Diario día 4

## Estado al cierre

Hoy quedó cerrada la auditoría ampliada de `y_ref` en cohorte de 7 eventos para decidir si `envsum` merecía promoción frente al baseline `sumabs`.

La pregunta ya no era si `envsum` podía mover `t0_rel`. Eso ya estaba claro. La pregunta real era mucho más dura:
- si mejoraba el `worst-of-best`
- si mejoraba el `relative_rms` agregado
- si reducía falsos `chi≈0`
- si limpiaba la física útil per-event
- y si los cambios de bin Kerr iban en la dirección correcta

La respuesta final es nítida: **`envsum` no merece promoción a baseline**.

## Qué se verificó primero

Antes de comparar, se confirmó que `GW170814` y `GW170818` ya tenían polos canónicos completos en la ruta esperada:
- `poles_H1.json/csv`
- `poles_L1.json/csv`
- `poles_joint.json/csv`
- `summary.json`

Con eso, la cohorte ampliada quedó cerrada en 7 eventos:
- `GW150914`
- `GW151012`
- `GW170104`
- `GW170814`
- `GW170818`
- `GW190521_030229`
- `GW191109_010717`

## Qué quedó rescatado

### 1. `envsum` sí es una palanca causal real en peak-picking
La variante no es cosmética. Cambia de verdad la selección temporal y, por tanto, mueve la física downstream.

Casos claros:
- `GW170814`: pasa de `t0_rel=-0.457764` con `sumabs` a `t0_rel=0.029785` con `envsum`
- `GW170818`: también cambia fuertemente de brazo temporal
- `GW170104`: la variante introduce un desplazamiento grande hacia un brazo distinto

Conclusión:
- `envsum` no es ruido de implementación
- pertenece a la familia causal correcta
- merece quedar **rescatado como candidato experimental**

**Veredicto:** RESCATAR como candidato, no como baseline.

### 2. La auditoría ampliada ya cerró la decisión de promoción
La cohorte de 5 eventos dejaba a `envsum` en zona gris. La cohorte de 7 eventos ya no.

La comparación ampliada resuelve la duda importante:
- `envsum` mejora algunos eventos concretos
- pero no sostiene mejora robusta a nivel de cohorte

**Veredicto:** RESCATAR la conclusión, cerrar la duda, no seguir posponiendo la decisión.

## Qué queda archivado como promoción

### 1. Promover `envsum` a baseline
La regla de promoción era estricta:
- `worst-of-best_envsum <= worst-of-best_sumabs`
- mejora en media o mediana de best `relative_rms`
- no aumentar falsos `chi≈0`
- no degradar de forma sistemática la cohorte

`envsum` falla en lo más importante:

```text
worst_of_best_sumabs = 0.9901968753
worst_of_best_envsum = 0.9927844848

mean_best_sumabs   = 0.9543418130
mean_best_envsum   = 0.9610410458
median_best_sumabs = 0.9668411046
median_best_envsum = 0.9668411046
```

Lectura:
- empeora el `worst-of-best`
- empeora la media de best `relative_rms`
- la mediana no mejora

Eso basta por sí solo para bloquear promoción.

**Veredicto:** ARCHIVAR la promoción.

## Comparación dura per-event

```text
delta_rms = envsum - sumabs

GW150914         +0.003174
GW151012         +0.000000
GW170104         -0.022634
GW170814         +0.015939
GW170818         -0.039476
GW190521_030229  +0.076704
GW191109_010717  +0.013188
```

Lectura:
- mejora en `GW170104`
- mejora en `GW170818`
- empate en `GW151012`
- empeora en `GW150914`
- empeora en `GW170814`
- empeora con fuerza en `GW190521_030229`
- empeora en `GW191109_010717`

La degradación de `GW190521_030229` pesa demasiado como para hablar de promoción.

## Falsos `chi≈0`

El conteo bruto de falsos `chi≈0` en los mejores por evento no sube, pero tampoco baja:

- `sumabs`: 2
- `envsum`: 2

Lo importante es que **cambian de sitio**, no que desaparezcan.

Con `sumabs`:
- `GW151012`
- `GW190521_030229`

Con `envsum`:
- `GW151012`
- `GW170104`

Lectura:
- `envsum` arregla un falso `chi≈0` en `GW190521_030229`
- pero introduce otro en `GW170104`
- el problema no se limpia; solo se redistribuye

**Veredicto:** no suma evidencia a favor de promoción.

## Cambios de bin Kerr

Aquí sí hubo cambios reales en los mejores por evento:
- `GW170104`
- `GW170818`
- `GW190521_030229`

Tabla resumida:

```text
GW170104:
  sumabs -> ref_chi=0.99, poor
  envsum -> ref_chi=0.00, poor

GW170818:
  sumabs -> ref_chi=0.99, poor
  envsum -> ref_chi=0.60, fair

GW190521_030229:
  sumabs -> ref_chi=0.00, fair
  envsum -> ref_chi=0.99, poor
```

Lectura:
- `GW170818` sí mejora de forma física razonable
- `GW190521_030229` empeora justo en la dirección contraria
- `GW170104` cambia de bin, pero hacia un falso `chi≈0`

El balance neto no es de limpieza física; es mixto y peor en el agregado.

## Calidad per-row / per-event

Todos los rows del dataset vienen de `poles_joint.json`, así que la comparación es homogénea.

Conteo de calidad Kerr per-row:

```text
sumabs:
  fair = 7
  poor = 17

envsum:
  fair = 4
  poor = 20
```

Esto es especialmente importante porque muestra que `envsum` no solo falla en los mejores por evento. También **empeora la calidad física agregada por fila**.

**Veredicto:** evidencia adicional contra promoción.

## Hallazgo causal más importante del día

La rama correcta sigue siendo `y_ref` / peak-picking.

Pero esta variante concreta:
- sí mueve `t_peak`
- sí cambia los polos elegidos
- sí cambia bins Kerr
- y aun así **no mejora lo que importa en cohorte ampliada**

Eso fija una conclusión útil:

1. el cuello sigue estando arriba, en la geometría de `y_ref`
2. `envsum` no era la geometría correcta para promoción
3. la hipótesis causal sigue viva, pero esta implementación concreta no la resuelve

## Decisión final del día

- `sumabs`: se mantiene como baseline
- `envsum`: se mantiene como candidato rescatado
- promoción de `envsum`: archivada

Veredicto corto:

**MANTENER CANDIDATO**

No es un experimento muerto. Pero tampoco hay base para subirlo a baseline.
