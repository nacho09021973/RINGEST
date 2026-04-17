
## Diario de Dia 2.

### 1. Git, repo y daños colaterales

* Se restauró `catalog_params.csv` desde historial y quedó subido a `main`.
* Se limpiaron commits accidentales/metidos por herramienta en `05_validate_qnm_kerr.py`.
* Estado final del repo:
  * `main` limpio
  * cambios relevantes ya empujados a GitHub
  * Ruta C canónica otra vez reproducible

### 2. Ruta C canónica restaurada

Se volvió a correr el flujo canónico:

```bash
python3 02_poles_to_dataset.py --runs-dir data/gwosc_events --out-dir runs/qnm_dataset --params-csv ./catalog_params.csv --max-modes 4
python3 03_discover_qnm_equations.py --dataset-csv runs/qnm_dataset/qnm_dataset.csv --out-dir runs/qnm_symbolic --analysis-only
python3 04_kan_qnm_classifier.py --summary runs/qnm_symbolic/qnm_symbolic_summary.json --out-dir runs/qnm_kan --analysis-only --n-clusters 3
python3 05_validate_qnm_kerr.py --summary runs/qnm_kan/qnm_kan_summary.json --out-dir runs/qnm_kerr_validation

Resultado real:

215 eventos
859 filas
672 filas con columnas adimensionales
3. Validación Kerr de la Ruta C canónica

Resultado real otra vez:

PARTIAL_KERR_CONSISTENCY
cluster 0:
centroide ≈ (0.6654, -0.0001)
dist=0.0245
good a nivel de centroide
clusters 1 y 2:
claramente poor

Conteo global:

good = 32
fair = 134
poor = 506

Conclusión:

Ruta C canónica sigue siendo el mejor estado conocido
el experimento upstream de filtros/ranking en 02_poles_to_dataset.py queda desautorizado como carril canónico
4. Auditoría del cluster 0

Se confirmó con la auditoría nueva de 05_validate_qnm_kerr.py:

n_rows = 379
mode_rank distribution = {0: 94, 1: 95, 2: 97, 3: 93}
pole_source distribution = {'poles_H1.json': 110, 'poles_joint.json': 269}
chi_final mean = 0.683
chi_final median = 0.690
row quality = {'good': 32, 'fair': 134, 'poor': 213}

Lectura dura:

el centroide del cluster 0 sí parece Kerr-compatible
la población interna del cluster 0 está muy mezclada
mode_rank no separa ninguna subfamilia limpia
chi_final tampoco discrimina entre good/fair/poor
5. Cluster 0 por pole_source

Chequeo real dentro del cluster 0:

poles_H1.json: 9 good / 36 fair / 65 poor
poles_joint.json: 23 good / 98 fair / 148 poor

Proporciones:

H1: ~8.2% good
joint: ~8.6% good

Conclusión:

joint aporta más good en número absoluto porque pesa más
pero no limpia apenas nada
el problema no está principalmente en la fusión joint
el problema ya entra antes, en la extracción de polos de B
6. Primer bug real en Ruta B

Se encontró un bug concreto en 01_extract_ringdown_poles.py:

project_root = Path(__file__).resolve().parent.parent

Eso resolvía mal rutas relativas y mandaba --run-dir fuera del repo.

Cambio mínimo correcto:

project_root = Path(__file__).resolve().parent

Veredicto:

RESCATAR con parche mínimo
primer bug real confirmado en B
7. Autopsia de GW150914 con extractor actual (rank=auto)

Se corrió:

python3 01_extract_ringdown_poles.py \
  --run-dir data/gwosc_events/GW150914/boundary \
  --duration 0.25 \
  --require-decay \
  --max-modes 16

Resultado en poles_joint.json:

n_poles = 16
frecuencias muy dispersas
damping_1_over_s casi degenerado en una banda estrecha (~5–7)

Ejemplos:

722 Hz, damping 5.10
1537 Hz, damping 5.13
427 Hz, damping 5.21
295 Hz, damping 5.24
266 Hz, damping 5.29
603 Hz, damping 5.37

Lectura:

demasiadas frecuencias distintas con amortiguamiento casi clavado
eso huele más a nube numérica del extractor que a familia QNM física limpia
8. Confirmación en GW170104

Se repitió en otro canario:

mismo patrón
frecuencias muy abiertas
damping_1_over_s otra vez concentrado en una banda estrecha (~5–7)

Conclusión:

no era casualidad
no era un solo evento
no era solo joint
el problema ya nace en la extracción/subselección de polos
9. Hipótesis fuerte: el rango automático de ESPRIT mete mucha basura

Se probó --rank 4 --max-modes 8.

GW150914

Resultado:

H1: 1 polo
L1: 2 polos
joint: 3 polos

Ejemplo joint:

121.953 Hz, damping 9.298
432.060 Hz, damping 37.998
1038.788 Hz, damping 12.386
GW170104

Resultado:

H1: 1 polo
L1: 1 polo
joint: 2 polos

Ejemplo joint:

1067.408 Hz, damping 5.883
153.038 Hz, damping 74.113

Lectura:

desaparece la nube de 16 polos casi degenerados
el extractor deja de fabricar familias artificiales de damping casi constante
el rango automático queda bajo sospecha fuerte
rank=4 limpia radicalmente la salida de B
10. Qué queda descartado
que el problema principal esté en joint
que baste con tocar mode_order
que mode_rank rescate física útil
que el tuning upstream en 02_poles_to_dataset.py fuera la solución
11. Qué gana fuerza
el cuello de botella principal está en 01_extract_ringdown_poles.py
más concretamente, en:
la selección automática de rango en esprit_poles(...)
y después en la poda débil de _sort_and_filter(...)
la Ruta C solo hereda y organiza una población ya sucia
12. Veredicto del día
Ruta C
RESCATAR como baseline canónico
congelarla y no seguir tuneándola
Ruta B
CRÍTICA y rota a nivel de extracción modal
el siguiente trabajo serio va aquí
Extractor
no parece que haya que reescribir ESPRIT entero
sí parece que hay que reescribir la política de rango canónico
13. Qué hacer mañana
Prioridad 1

Revisar 01_extract_ringdown_poles.py con foco en:

esprit_poles(...)
selección automática de rango
_sort_and_filter(...)
Prioridad 2

Tratar --rank 4 como baseline provisional en canarios:

comparar salidas
ver si mejora la física final aguas abajo
Prioridad 3

No tocar Ruta C salvo para medir efectos de cambios en B

14. Qué no hacer mañana
no volver a afinar filtros upstream en 02_poles_to_dataset.py
no abrir más scripts
no meter más wrappers
no seguir con sweeps ciegos en Ruta C
no declarar “familia Kerr limpia” todavía
Resumen ejecutivo del Día 2
se restauró y estabilizó el repo
se confirmó otra vez el mejor baseline de Ruta C
se demostró que el cluster 0 bueno-centroide está internamente mezclado
se aisló que joint no es el culpable principal
se encontró un bug real de rutas en 01_extract_ringdown_poles.py
se encontró evidencia fuerte de que el rango automático de ESPRIT está metiendo mucha basura
rank=4 limpia drásticamente la salida de los canarios
el proyecto deja de mirar C y se mueve de lleno a B


Sí. Aquí va un **plan de trabajo completo** para los tres carriles, con prioridades, criterios de avance y poda.

---

# Plan maestro de trabajo

## Objetivo general

Pasar de:

* datos reales GW
* strain / boundary
* polos / QNM

a:

* observables robustos en disco
* relaciones empíricas
* familias físicas defendibles

Regla central:
**si algo no mejora señal, observables o familias físicas, no entra.**

---

# Carril A — Sandbox / calibración

## Función

Sirve para:

* probar motor matemático
* comprobar solver
* validar contratos físicos
* ensayar descubrimiento simbólico en entorno controlado

## Qué es

* carril de calibración
* no carril probatorio sobre datos reales

## Estado

* útil como infraestructura
* no prioritario frente a B y C

## Objetivo del carril

Mantener un banco de pruebas estable para:

* detectar regresiones numéricas
* validar que PySR/KAN/solver no están rotos
* comparar contra un entorno controlado

## Trabajo pendiente

### Prioridad baja

1. congelar configuración canónica ADS/GKPW
2. dejar outputs mínimos y trazables
3. no crecer en geometrías sandbox nuevas salvo necesidad clara

## Qué no hacer

* no convertir A en centro del proyecto
* no usar A para justificar física real
* no abrir nuevas familias teóricas solo por explorar

## Veredicto

**RESCATAR como infraestructura.**

---

# Carril B — Extracción desde datos reales

## Función

Es el carril clave:

* strain real
* boundary HDF5
* polos/QNM
* señal física mínima que alimenta C

## Estado actual

* es el cuello de botella principal
* ya se encontró:

  * bug real en rutas de `01_extract_ringdown_poles.py`
  * sospecha fuerte sobre `rank=auto`
  * patrón raro de muchos polos con damping casi degenerado
  * mejora clara en canarios con `--rank 4 --max-modes 8`

## Objetivo del carril

Obtener una representación modal:

* mínima
* estable
* físicamente defendible
* trazable

## Plan de trabajo B

### Fase B1 — saneamiento del extractor

#### Archivo principal

* `01_extract_ringdown_poles.py`

#### Tareas

1. **fijar baseline provisional**

   * usar `rank=4` como referencia de trabajo
   * no confiar en `rank=auto` como canónico

2. **comparar canarios**

   * `GW150914`
   * `GW170104`
   * y 1–2 eventos más si hace falta

3. **medir por detector**

   * `H1`
   * `L1`
   * `joint`

4. **comparar outputs**

   * `n_poles`
   * `freq_hz`
   * `damping_1_over_s`
   * `amp_abs`

#### Criterio de éxito

* menos polos espurios
* menos degeneración artificial en damping
* estabilidad entre detectores
* menos nube numérica

---

### Fase B2 — política canónica de rango

#### Decisión a tomar

Elegir una política:

* `rank=4` fijo por defecto
  o
* auto-rank capado con techo pequeño

#### Orden recomendado

1. primero probar **default CLI = 4**
2. si funciona en varios canarios, evaluar si luego merece capar auto-rank internamente

#### Criterio de éxito

* cambio mínimo
* reversible
* medible

---

### Fase B3 — revisar `_sort_and_filter(...)`

Solo después de B1/B2.

#### Qué mirar

* si el filtro actual deja pasar demasiados polos operacionales
* si el orden “least damped first” introduce sesgo malo
* si `max_modes` sigue teniendo sentido con rango bajo

#### Criterio

No tocarlo antes de estabilizar el rango.

---

### Fase B4 — revisar ventana de ringdown

Si tras fijar rango el extractor sigue raro.

#### Qué mirar

* `t0_rel`
* `duration`
* `peak_search`
* `start_offset`

#### Objetivo

Ver si el problema es mezcla de merger + ringdown temprano.

---

### Fase B5 — trazabilidad

Añadir solo si hace falta:

* `rank_used`
* `rank_policy`
* quizá métricas mínimas por canal

No abrir scripts nuevos.

## Qué no hacer en B

* no reescribir ESPRIT entero de entrada
* no abrir 5 heurísticas simultáneas
* no cambiar extractor, ventana y postfiltro a la vez
* no volver a downstream antes de entender el extractor

## Veredicto

**CRÍTICA.**
Aquí se juega el proyecto.

---

# Carril C — Dataset, clustering y validación

## Función

Transformar polos reales en:

* dataset QNM
* clustering
* validación Kerr
* observables y familias empíricas

## Estado actual

Carril canónico restaurado y funcional:

* `qnm_dataset.csv`
* 859 filas
* 672 filas con columnas adimensionales
* `PARTIAL_KERR_CONSISTENCY`
* cluster 0 con centroide Kerr-compatible
* pero población interna muy mezclada

## Objetivo del carril

No “fabricar familias”.
Sí:

* medir qué sale de B
* organizarlo
* contrastarlo con Kerr
* auditar mezcla y subestructura

## Plan de trabajo C

### Fase C1 — congelación canónica

Mantener como baseline:

* `02_poles_to_dataset.py`
* `03_discover_qnm_equations.py`
* `04_kan_qnm_classifier.py`
* `05_validate_qnm_kerr.py`

Con:

* `catalog_params.csv`
* sin `--fetch-params` como carril principal

---

### Fase C2 — usar C como termómetro de B

Cada vez que cambie B:

1. regenerar dataset
2. rerun de clustering
3. rerun de validación Kerr
4. comparar contra baseline

#### Métricas clave

* `Events`
* `Total rows`
* `With M/chi`
* centroides
* `good/fair/poor`
* composición del cluster 0

---

### Fase C3 — auditoría del cluster 0

Ya empezada.

#### Qué sabemos

* `mode_rank` no separa
* `chi_final` no separa
* `joint` domina en número, pero no mejora pureza
* cluster 0 es útil como centroide, no limpio como familia

#### Qué hacer

Seguir usándolo como:

* indicador de mejora o empeoramiento de B
* no como resultado físico final aún

---

### Fase C4 — adaptar C solo si B mejora

Solo si una política de B se estabiliza.

#### Posibles cambios mínimos futuros

1. `02_poles_to_dataset.py`

   * aclarar semántica de damping
   * añadir trazabilidad de extracción si llega desde B

2. `05_validate_qnm_kerr.py`

   * mantenerlo como termómetro
   * quizá mejorar criterios más adelante, pero no ahora

#### Qué no tocar de momento

* clustering en sí
* PySR
* interpretaciones fuertes de familias

## Qué no hacer en C

* no más sweeps ciegos de `mode_order`
* no más filtros upstream improvisados en `02`
* no reabrir `03_clean_physical_dataset.py` salvo auditoría puntual
* no rediseñar C antes de estabilizar B

## Veredicto

**RESCATAR como baseline y termómetro.**

---

# Orden global de prioridades

## Prioridad 1

**Carril B**

* estabilizar extractor
* fijar política de rango
* revisar canarios

## Prioridad 2

**Carril C como medida**

* rerun tras cambios de B
* comparar con baseline canónico

## Prioridad 3

**Carril A**

* solo mantenimiento
* no invertir aquí energía principal

---

# Hitos concretos

## Hito 1

B funciona mejor en canarios con una política fija de rango.

### Señales de éxito

* menos polos
* menos degeneración de damping
* salidas más defendibles

## Hito 2

Esa política se prueba en unos pocos eventos adicionales.

## Hito 3

Se pasa esa salida por C y se compara con baseline.

### Pregunta clave

¿mejora la física o solo cambia la forma de la basura?

## Hito 4

Si mejora:

* hacer canónica la nueva política de B
* adaptar mínimamente C

## Hito 5

Solo entonces volver a relaciones/familias con más ambición.

---

# Qué archivar o congelar

## Congelar

* Ruta C actual como baseline
* A como entorno de calibración

## Archivar o no tocar

* experimento fallido de filtros upstream en `02_poles_to_dataset.py`
* cualquier wrapper temporal
* cualquier barrido que no haya aportado mejora física

---

# Entregables físicos por carril

## A

* outputs estables de sandbox
* contratos físicos
* solver funcionando

## B

* `poles_H1.json`
* `poles_L1.json`
* `poles_joint.json`
* extracción trazable y menos espuria

## C

* `qnm_dataset.csv`
* `qnm_kerr_validation_summary.json`
* `cluster_audit.csv`
* `cluster_audit_summary.json`

---

# Regla de oro

## Si mañana solo haces una cosa

Haz esta:

**convertir `rank=4` en baseline provisional de B y medir su efecto en canarios antes de tocar nada más.**

---

# Resumen ejecutivo

## A

* mantener
* no priorizar

## B

* foco total
* extractor bajo sospecha
* `rank=auto` casi seguro mete basura
* probar/fijar política de rango canónica

## C

* congelar como baseline
* usar para medir efectos de B
* no seguir tuneándolo


