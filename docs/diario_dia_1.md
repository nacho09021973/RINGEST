
## Diario de Día 1

### 1. `02_poles_to_dataset.py`

* Confirmamos el bug real: el carril `--fetch-params` estaba roto por dependencia inestable de `gwosc`.
* Vimos que no era solo import/API: también fallaba el parseo de payload.
* Resultado práctico: **no conviene seguir apoyando Ruta C en `--fetch-params`**.

### 2. Dataset QNM real

* Construiste `runs/qnm_dataset/qnm_dataset.csv`.
* Resultado útil:

  * **859 filas** totales
  * **672 filas** con `M_final_Msun`, `chi_final`, `omega_re_norm`, `omega_im_norm`
* Veredicto: **datos reales → observables físicos en disco** conseguido.

### 3. `03_discover_qnm_equations.py --analysis-only`

* Perfilaste el dataset real.
* Confirmaste:

  * **215 eventos**
  * contrato KAN usable
  * features: `omega_re_norm`, `omega_im_norm`
* Aún **sin ecuaciones**, pero el stage sirve como preparación.

### 4. `04_kan_qnm_classifier.py`

* Hiciste clustering sobre el dataset real.
* Salieron **3 clusters** empíricos en el plano QNM complejo.

### 5. `05_validate_qnm_kerr.py`

* Validaste contra Kerr.
* Antes de limpiar:

  * `PARTIAL_KERR_CONSISTENCY`
  * un cluster razonable, dos claramente malos
* Después de limpiar:

  * sigue `PARTIAL_KERR_CONSISTENCY`
  * pero con bastante menos basura
  * **cluster 0** queda como familia claramente Kerr-compatible:

    * centroide ≈ `(0.6952, -5.57e-05)`
    * `dist=0.0263` → **good**

### 6. `03_clean_physical_dataset.py`

* Lo creaste y lo calibraste.
* Probaste varios cortes en `omega_im_norm`.
* El único razonable de hoy fue:

  * `--max-re-norm 1.5`
  * `--max-im-norm=-1e-5`
* Con eso:

  * **290 filas limpias**
  * **140 eventos**
  * mejora clara en proporción de matches Kerr pobres

### 7. Documentación

* Dejamos corregida la documentación de Ruta C para usar:

  * `catalog_params.csv`
  * `--params-csv`
* Y quitamos de la documentación el carril viejo de `--fetch-params`.

---

## Qué sabemos ya

### Respuesta a la pregunta central

Sí, ya has conseguido:

* **datos reales**
* **observables QNM físicos**
* **familias empíricas**
* **una familia Kerr-compatible clara**

Lo que **todavía no** has conseguido de forma sólida:

* ecuaciones empíricas descubiertas con PySR sobre el dataset limpio
* una separación física limpia de todas las familias, no solo del cluster 0

---

## Qué hacer mañana

### Prioridad 1

**Aislar y estudiar el cluster 0**, no seguir creciendo en ramas nuevas.

Objetivo:

* ver distribución de `chi_final`
* ver distribución de `mode_rank`
* ver distancia Kerr por fila
* comprobar si ese cluster ya puede tratarse como familia física rescatada

### Prioridad 2

Correr **PySR real** sobre el dataset limpio, no solo `analysis-only`.

Objetivo:

* buscar relaciones empíricas en:

  * `omega_re_norm`
  * `omega_im_norm`
* usando como inputs:

  * `chi_final`
  * `mode_rank`

### Prioridad 3

Decidir si `mode_rank` sirve o no como variable física.
Hoy la evidencia apunta a que:

* **no coincide bien con “fundamental Kerr”**
* y probablemente está contaminando clustering e interpretación

---

## Qué no hacer mañana

* no abrir más carriles tipo Cardiff/GWOSC/JSON nuevos si ya tienes `catalog_params.csv`
* no meter wrappers
* no conectar todavía a `08_build_holographic_dictionary.py`
* no añadir scripts nuevos si el mismo objetivo se puede cubrir con:

  * un filtro
  * una opción nueva en un script existente
  * o un notebook/CSV auxiliar fuera del pipeline principal

---

## Qué scripts deberíamos borrar o archivar

Aquí sí: hay que podar.

### ARCHIVAR / eliminar del carril principal

1. **cualquier variante rota o intermedia de `02_poles_to_dataset.py`**

   * especialmente las que siguen empujando `--fetch-params` como carril principal
   * el flujo robusto ya es `--params-csv`

2. **`03_clean_physical_dataset.py`**

   * **no lo borraría hoy**
   * pero tampoco lo dejaría crecer como stage permanente si solo sirve para calibrar un corte
   * mi recomendación:

     * **mantenerlo temporalmente**
     * y, si mañana fijamos el corte definitivo, **absorber ese filtro dentro de `03_discover_qnm_equations.py` o como prefilter opcional del dataset**
     * después **archivarlo**

3. **cualquier script auxiliar inventado para catálogos externos**

   * si existe algo tipo `crear_csv_cardiff.py` y no está integrado ni verificado, **archivar**
   * no metas otro origen de complejidad

4. **cualquier wrapper tipo `run_clean_pipeline.sh`**

   * directamente **no merece existir**
   * solo añade una capa más de fragilidad

### MANTENER

* `02_poles_to_dataset.py`
* `03_discover_qnm_equations.py`
* `04_kan_qnm_classifier.py`
* `05_validate_qnm_kerr.py`

Son el carril real de Ruta C.

---

## Mi recomendación de poda concreta

### Opción conservadora

* mantener `03_clean_physical_dataset.py` mañana
* usarlo una vez más
* si el corte `-1e-5` queda validado, entonces:

  * o lo integras en un script existente
  * o lo archivas a `_archive/`

### Opción más limpia

No crear más scripts y decidir que:

* la limpieza física del dataset se haga como opción dentro de:

  * `02_poles_to_dataset.py`
  * o `03_discover_qnm_equations.py`

Eso deja Ruta C así:

* `02_poles_to_dataset.py`
* `03_discover_qnm_equations.py`
* `04_kan_qnm_classifier.py`
* `05_validate_qnm_kerr.py`

Y ya.

---

## Resumen ejecutivo

### Hoy

* rescataste Ruta C sobre **datos reales**
* obtuviste dataset físico usable
* separaste un **cluster Kerr-compatible real**
* limpiaste bastante la basura

### Mañana

* no crecer
* estudiar el **cluster 0**
* correr **PySR real**
* decidir si `03_clean_physical_dataset.py` se integra o se archiva

### Poda recomendada

* **deprecate `--fetch-params`**
* **no crear scripts auxiliares nuevos**
* **archivar `03_clean_physical_dataset.py` cuando el corte quede fijado**
* **mantener solo el carril 02 → 03 → 04 → 05**

### TABLA DE MIERDA

| Ruta                       | Función física real                                               | Qué transforma                                                | Riesgo principal                                                       | Prioridad      | Veredicto                                                   |
| -------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------- | ---------------------------------------------------------------------- | -------------- | ----------------------------------------------------------- |
| **A — Sandbox ADS/GKPW**   | Calibrar motor, solver, PySR y contratos en un entorno controlado | geometrías sintéticas → bulk/eigenmodos/diccionario           | parecer física cuando en realidad es banco de pruebas                  | **media-baja** | **RESCATAR como infraestructura, no como evidencia física** |
| **B — Datos reales GWOSC** | Convertir strain real en objetos físicos explotables              | strain/NPZ reales → boundary HDF5 → polos/QNM                 | que el preprocesado y ESPRIT metan basura irreversible                 | **máxima**     | **CRÍTICA**                                                 |
| **C — Cadena QNM**         | Sacar observables, clustering y contraste Kerr desde polos reales | polos reales → `qnm_dataset.csv` → clusters → validación Kerr | interpretar artefactos como familias físicas; `mode_rank` mal alineado | **alta**       | **RESCATAR con poda**                                       |

## Ruta A

**Archivo / ruta:** sandbox ADS/GKPW en docs canónicas. 
**Inputs reales:** ninguno
**Outputs reales:** internos al sandbox
**Función física:** validar andamiaje matemático y numérico
**Dependencia toy/teórica:** total
**Veredicto:** **RESCATAR**, pero solo como carril de calibración. Si el objetivo es “datos reales → observables/familias físicas”, por sí sola **no responde**.

## Ruta B

**Archivo / ruta:** descarga GWOSC → boundary → polos. 
**Inputs reales:** strain GWOSC
**Outputs reales:** `poles_joint.json`, `poles_H1.json`, boundary HDF5
**Función física:** aquí nace la física real del pipeline
**Dependencia toy/teórica:** mínima; es el carril observacional
**Veredicto:** **CRÍTICA**. Si B mete basura, C solo la ordena y la decora. La calidad de B decide casi todo.

## Ruta C

**Archivo / ruta:** `02_poles_to_dataset.py` → `03_discover_qnm_equations.py` → `04_kan_qnm_classifier.py` → `05_validate_qnm_kerr.py` 
**Inputs reales:** polos de B
**Outputs reales:** `qnm_dataset.csv`, clusters, validación Kerr
**Función física:** transformar polos reales en observables y familias empíricas
**Dependencia toy/teórica:** baja, pero dependiente de que B esté limpio
**Veredicto:** **RESCATAR con poda**. Ya ha dado algo real: un cluster Kerr-compatible. Pero sigue mezclando ruido y familias mal interpretadas.

## Ranking brutal

1. **B** — la que importa de verdad
2. **C** — la que puede convertir B en física útil
3. **A** — la que ayuda a construir, pero no demuestra física real

## Riesgo de fracaso

* **A** fracasa si se convierte en religión del sandbox.
* **B** fracasa si el preprocesado/extracción modal está mal.
* **C** fracasa si sigues dejando crecer scripts y clusters sin poda física.

## Qué haría yo

* **Mantener A** estable y congelada.
* **Concentrar esfuerzo en B**: robustez de polos y orden modal.
* **Usar C solo en modo austero**: dataset limpio, validación Kerr, estudio del cluster 0.
* **No añadir más scripts** salvo que eliminen otro.

## Poda recomendada

* **Deprecar `--fetch-params`** en docs y flujo principal.
* **Mantener temporalmente** `03_clean_physical_dataset.py`.
* Si el corte final se consolida, **absorberlo** en `02_poles_to_dataset.py` o `03_discover_qnm_equations.py` y luego **archivar** `03_clean_physical_dataset.py`.
* No crecer más por la vía de wrappers.

Mi lectura final: **A construye, B observa, C decide si de verdad hay física o solo artefactos**.

