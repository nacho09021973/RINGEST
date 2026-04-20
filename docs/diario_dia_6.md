# Diario día 6

## Estado al cierre

Hoy quedó cerrada la caracterización honesta de **Ruta C** sobre el carril real:

- `02_poles_to_dataset.py`
- `03_discover_qnm_equations.py`
- `04_kan_qnm_classifier.py`
- validación manual contra Kerr `l=m=2, n=0`

La pregunta del día fue concreta:

- si el dataset `220` filtrado ya permite recuperar relaciones físicas robustas,
- si el clustering sobre el plano adimensional descubre familias físicas,
- o si lo que aparece son regímenes operacionales del extractor.

La respuesta corta es:

- **sí** aparece una relación robusta en `freq_hz ~ 1 / M_final`
- **no** aparece todavía una ley Kerr usable en `omega_re_norm(chi)` ni `omega_im_norm(chi)`
- el clustering encuentra **tres bandas de desviación respecto a Kerr**
- pero esas bandas **no** se anclan limpiamente a `chi_final` ni a `M_final_Msun`

## Qué quedó fijado en disco

### Dataset principal y carril 220

- `runs/qnm_dataset/qnm_dataset.csv`
- `runs/qnm_dataset/qnm_dataset_220.csv`
- `runs/qnm_dataset/qnm_dataset_220.README`
- `runs/qnm_dataset/qnm_dataset_220_lt010.csv`

Resumen:

- `qnm_dataset.csv`: `848` filas
- `qnm_dataset_220.csv`: `60` filas (`kerr_220_distance < 0.15`)
- `qnm_dataset_220_lt010.csv`: `34` filas (`kerr_220_distance < 0.10`)

### Salidas simbólicas y KAN

- `runs/qnm_symbolic_220/`
- `runs/qnm_symbolic_220_lt010/`
- `runs/qnm_kan_220/`
- `runs/qnm_kan_220_steps3000/`

## Hallazgo positivo robusto

### PySR sobre `qnm_dataset_220.csv`

En `runs/qnm_symbolic_220/qnm_symbolic_summary.json`:

- `freq_hz = 17747.293 / (M_final_Msun + mode_rank)`
- `R² = 0.9252`

En el subconjunto estricto `qnm_dataset_220_lt010.csv`:

- `freq_hz = 17689.434 / (M_final_Msun + 1.8026965)`
- `R² = 0.9849`

Lectura física:

- la única estructura empírica fuerte que sobrevive de forma estable es la escala dimensional
  `freq_hz ~ 1 / M_final`
- esto es consistente con la escala QNM esperada
- estrechar el filtro Kerr mejora esta relación, no la destruye

**Veredicto:** RESCATAR esta relación como resultado empírico real del pipeline actual.

## Resultado negativo consistente

### Targets Kerr-normalizados

En `runs/qnm_symbolic_220/qnm_symbolic_summary.json`:

- `damping_hz`: `R² = 0.2344`
- `omega_re_norm`: `R² = 0.1537`
- `omega_im_norm`: `R² = 0.2588`

En `runs/qnm_symbolic_220_lt010/qnm_symbolic_summary.json`:

- `damping_hz`: `R² = 0.1997`
- `omega_re_norm`: `R² = 0.3528`
- `omega_im_norm`: `R² = -0.0528`

Lectura:

- apretar el filtro de `0.15` a `0.10` mejora algo `omega_re_norm`
- pero no rescata la dependencia Kerr completa
- `omega_im_norm` sigue sin señal física usable
- `damping_hz` tampoco se estabiliza

Conclusión:

- el pipeline actual **no** está recuperando de forma fiable la dependencia no trivial en `chi_final`
- la parte robusta es la escala `1 / M`
- la parte débil sigue siendo la estructura Kerr adimensional

**Veredicto:** no vender `omega_re_norm(chi)` ni `omega_im_norm(chi)` como resultado físico.

## Clustering y bandas de desviación respecto a Kerr

El clustering se hizo sobre:

- `omega_re_norm`
- `omega_im_norm`

con `3` clusters en `runs/qnm_kan_220/cluster_labels.csv`.

Centroides:

- cluster `0`: `omega_re_norm = 0.42537`, `omega_im_norm = -0.001430`
- cluster `1`: `omega_re_norm = 0.51351`, `omega_im_norm = -0.000046`
- cluster `2`: `omega_re_norm = 0.59909`, `omega_im_norm = -0.000044`

La inspección contra la tabla Kerr `220` da tres bandas de desviación en `omega_re_norm`:

- cluster `0`: media `-0.0643`, mediana `-0.0618`, `stdev = 0.0394`
- cluster `1`: media `+0.0165`, mediana `+0.0146`, `stdev = 0.0250`
- cluster `2`: media `+0.0912`, mediana `+0.0968`, `stdev = 0.0300`

Esto sí es una señal descriptiva real:

- los polos extraídos no caen aleatoriamente
- tampoco caen en el Kerr esperado para cada remanente
- se agrupan en **tres bandas sistemáticas de desviación**

Pero esas bandas no son, por sí mismas, familias físicas fuertes.

## Qué no explican los clusters

Cruce por `event` con el dataset `220`:

- cluster `0`: `chi_final` mediana `0.690`, `M_final_Msun` mediana `33.0`
- cluster `1`: `chi_final` mediana `0.690`, `M_final_Msun` mediana `54.5`
- cluster `2`: `chi_final` mediana `0.714`, `M_final_Msun` mediana `54.2`

Conclusión:

- los clusters **no** son bandas limpias de `chi_final`
- tampoco son bandas limpias de `M_final_Msun`

Además, al cruzar con variables internas del dataset:

- cluster `0`: `mode_rank` mediana `2`, `kerr_220_distance` mediana `0.0927`
- cluster `1`: `mode_rank` mediana `2`, `kerr_220_distance` mediana `0.0717`
- cluster `2`: `mode_rank` mediana `1`, `kerr_220_distance` mediana `0.1178`

Esto sugiere que el clustering está más cerca de:

- regímenes operacionales del extractor,
- o bolsas geométricas del filtro en el plano QNM,

que de una taxonomía física directa del remanente.

**Inferencia prudente:** correlacionan mejor con variables internas del pipeline que con metadatos físicos externos.

## KAN: qué aprendió y qué no

Comparación directa:

### `runs/qnm_kan_220/` (`100` pasos)

- `accuracy = 0.3667`
- `train_loss_final = 0.4686`
- `test_loss_final = 0.4906`

### `runs/qnm_kan_220_steps3000/` (`3000` pasos)

- `accuracy = 0.6667`
- `train_loss_final = 0.3331`
- `test_loss_final = 0.4278`

Lectura:

- `100` pasos era warm-up, no convergencia
- `3000` pasos aprenden estructura real
- no aparece overfitting fuerte: train y test bajan juntos

Pero el techo sigue siendo modesto:

- `0.67` de accuracy sobre `3` clases y `12` casos de test no es una separación física fuerte
- el KAN aprende parte de la estructura de las bandas
- no aprende una frontera casi perfecta porque el dataset mismo no es casi perfectamente separable

**Veredicto:** el KAN confirma la estructura descriptiva del clustering, no una familia física robusta.

## Diagnóstico final de Ruta C

Hoy Ruta C queda cerrada con el pipeline actual.

### Lo que sí recupera

- una ley empírica robusta `freq_hz ~ 1 / M_final`
- tres bandas de desviación sistemática respecto a Kerr en `omega_re_norm`

### Lo que no recupera

- una ley Kerr limpia `omega_re_norm(chi_final)`
- una ley usable `omega_im_norm(chi_final)`
- una clasificación fuerte de familias físicas en el plano adimensional

### Interpretación más prudente

El dataset `220` filtrado todavía mezcla:

- señal física real en frecuencia,
- desacoplo residual respecto a Kerr,
- y estructura inducida por el extractor / selección del candidato.

Por tanto:

- **no** conviene usar `omega_re_norm` y `omega_im_norm` como observables Kerr fiables aguas abajo
- sí se puede usar `freq_hz` y la escala con `M_final` como suelo firme

## Decisión operativa al cierre

Ruta C queda **caracterizada** y **cerrada** en su estado actual.

No hace falta seguir empujando:

- más pasos de KAN no van a convertir este dataset en una familia física fuerte
- más filtrado downstream en `02_poles_to_dataset.py` tampoco parece resolver el desacoplo Kerr

Si se quiere avanzar de verdad, el siguiente trabajo no está en `03` ni en `04`.
Está aguas arriba:

- preprocesado real
- whitening
- extracción de polos
- identificación física del candidato `220`

## Resumen ejecutivo

Resultado del día:

- **positivo**: el pipeline real recupera bien la escala `freq_hz ~ 1 / M_final`
- **negativo pero útil**: no recupera todavía la estructura Kerr adimensional
- **hallazgo descriptivo**: aparecen tres bandas de desviación respecto a Kerr
- **cierre honesto**: Ruta C no da aún familias físicas fuertes; da un diagnóstico cuantitativo del límite actual del pipeline
