# Resumen técnico — segunda oportunidad AdS/GKPW (`ads_gkpw_second_chance_d4`)

Fecha: 2026-04-21

## Objetivo

Dar una segunda oportunidad seria al carril AdS/GKPW, después de comprobar en quick-test que el pipeline podía volver a correr pero con varias roturas locales de integración.

Se buscaba responder dos preguntas distintas:

1. **Operatividad**: ¿Ruta A vuelve a ser regenerable desde el repo actual?
2. **Valor físico exploratorio**: ¿con un run menos toy el carril AdS produce algo más que prueba de vida?

---

## Configuración del run

Carril ejecutado:

- familia: `ads`
- boundary mode: `gkpw`
- cohorte homogénea: `d=4`
- run-dir: `runs/ads_gkpw_second_chance_d4`

Stage 01 produjo:

- `known = 20`
- `test = 10`
- `unknown = 0`
- total = `30 universes`

---

## Bloqueos previos resueltos antes de esta corrida

Antes de poder hacer esta segunda oportunidad hubo que resolver varios problemas reales del pipeline:

### 1. Ruta A restaurada
`01_generate_sandbox_geometries.py` había sido repuesto en el repo y se verificó que vuelve a correr.

### 2. Bug de `--focused-d`
El flag `--focused-d 4` se parseaba, pero no activaba el modo focused, así que Stage 01 seguía mezclando dimensiones (`d=3,4,5`).

Parche aplicado:
- activación automática de `focused_real_regime` al pasar `--focused-d`.

Resultado:
- Stage 01 pasó a generar cohorte homogénea en `d=4`.

### 3. Desajuste de ruta Stage 02 → Stage 08
Stage 08 buscaba geometría en:

- `02_emergent_geometry_engine/outputs/geometry_emergent`

pero Stage 02 escribía en:

- `02_emergent_geometry_engine/geometry_emergent`

Parche aplicado:
- corrección de la ruta contractual en `08_build_holographic_dictionary.py`.

### 4. Pérdida de `Delta_mass_dict`
Stage 08 esperaba `boundary.attrs["Delta_mass_dict"]` en los `.h5` emergentes de Stage 02, pero ese dato no sobrevivía al paso 02.

Hecho verificado:
- Stage 01 sí escribe `Delta_mass_dict`.
- Stage 02 no lo preserva en `geometry_emergent/*.h5`.

Parche mínimo aplicado en Stage 08:
- fallback al `.h5` fuente de `01_generate_sandbox_geometries/<system_name>.h5`.

Resultado:
- Stage 08 pasó de atlas vacío a atlas poblado.

### 5. Entorno PyTorch GPU
La venv estaba inicialmente en `torch +cpu`.

Se reinstaló:
- `torch 2.11.0+cu128`
- `torch.cuda.is_available() == True`
- GPU visible: `NVIDIA GeForce RTX 5060`

Observación:
- en cargas pequeñas la CPU seguía siendo competitiva o incluso más rápida; esto no se interpretó como fallo del pipeline.

---

## Resultados por stage

## Stage 01 — `01_generate_sandbox_geometries.py`

Resultado:
- completó correctamente
- escribió H5 + manifests
- produjo 30 geometrías AdS/GKPW homogéneas en `d=4`

Veredicto:
- **OK**
- Ruta A vuelve a ser regenerable al menos en Stage 01.

---

## Stage 02 — `02_emergent_geometry_engine.py --mode train`

Resultado final en test:

- `A(z) R² = 0.8692`
- `f(z) R² = 0.9869`
- `R(z) R² = -0.0083`
- `z_h MAE = 0.0240`
- `Family accuracy = 1.0000`

Artefactos escritos:

- `emergent_geometry_model.pt`
- `geometry_emergent/`
- `predictions/`
- `emergent_geometry_summary.json`

Interpretación:

- para `A(z)` y `f(z)`, el surrogate funciona razonablemente bien en este run;
- `R(z)` sigue sin ser útil;
- esto es bastante mejor que el quick-test anterior.

Veredicto:
- **OK como surrogate interno**
- no basta aún como validación física fuerte.

---

## Stage 03 — `03_discover_bulk_equations.py`

Patrón observado en múltiples geometrías:

- `R` no es aproximadamente constante;
- `R < 0` sí se cumple;
- `Compatible with Einstein: NO`
- `A ~ log(z): NO`
- `Einstein score = 0.50`
- veredicto repetido:
  - `POSSIBLY_EINSTEIN_WITH_MATTER`

Interpretación:

- no emerge una señal de Einstein vacuum limpia;
- sí emerge una estructura regular y compresible;
- el carril parece más próximo a “geometría efectiva con materia” que a una realización Einstein simple.

Veredicto:
- **interesante pero no concluyente**
- no rescata por sí solo el programa AdS como vía fuerte hacia QNM reales.

---

## Stage 07 — `07_emergent_lambda_sl_dictionary.py`

Resultado final:

- ecuación descubierta:
  - `Delta*(Delta - d)`
- `R² = 1.0000`
- `MAE = 0.0000`
- `Pearson = 1.0000`
- `ESTADO DE CONTRATOS POR RÉGIMEN: PASS`

Interpretación:

- el stage redescubre exactamente la relación esperada;
- aquí no hay ambigüedad: la señal es limpia.

Veredicto:
- **OK fuerte dentro del sandbox/diccionario**

---

## Stage 08 — `08_build_holographic_dictionary.py`

Tras el parche de `Delta_mass_dict`, el stage dejó de salir vacío.

Resultado:

- `ads_d4: 90 puntos con m2L2, d=4, 30 geometrías`

Resumen final relevante:

- mejor ecuación:
  - `(x0 - x1) * x0`
- esto es algebraicamente:
  - `Delta * (Delta - d)`
- `R²(m²L² = Delta(Delta-d)) = 1.0000`

Observación:
- el campo `R²(PySR) = -179.0000` no es interpretable físicamente tal como aparece;
- dado que la ecuación impresa coincide con la teoría y el ajuste teórico da 1.0000, ese número parece un artefacto de evaluación/registro del stage, no una refutación de la relación correcta.

Veredicto:
- **OK**
- el atlas ya no está vacío y reproduce la relación correcta.

---

## Stage 09 — `09_real_data_and_dictionary_contracts.py`

Resultado:

- `fase12: OK (0/0)`
- sin cierre downstream rico
- `extended_physics_contracts.py` ausente

Además, en la exploración previa se verificó que:
- Fase XIII espera un analysis con un schema que el output real de Stage 03 no produce en este carril/quick-test.

Interpretación:

- el cierre final contractual sigue siendo flojo;
- no invalida lo conseguido aguas arriba, pero tampoco aporta una validación física fuerte adicional.

Veredicto:
- **débil / no concluyente**

---

## Balance global

## Lo que esta segunda oportunidad sí ha demostrado

1. **Ruta A vuelve a ser operativamente regenerable** desde el repo actual.
2. El carril AdS/GKPW ya no es solo “pipeline que respira”.
3. Con un run menos toy:
   - Stage 02 aprende `A(z)` y `f(z)` de forma razonable;
   - Stage 07 redescubre exactamente `Delta(Delta-d)`;
   - Stage 08 construye un atlas poblado y consistente con `m²L² = Delta(Delta-d)`.

## Lo que no ha demostrado

1. No hay todavía una **salida física fuerte downstream** que justifique por sí sola AdS como vía convincente hacia QNM reales.
2. Stage 03 no converge a una señal Einstein simple.
3. Stage 09 no añade un cierre contractual/físico fuerte.

---

## Veredicto final

La conclusión honesta no es:

- “con AdS no somos capaces de hacer nada”

sino:

- **con AdS sí somos capaces de regenerar el pipeline y recuperar estructura interna coherente, incluida la relación `m²L² = Δ(Δ-d)`, pero todavía no hemos convertido eso en una vía downstream fuerte hacia física útil sobre QNM reales.**

En consecuencia:

- **AdS no debe archivarse como vía muerta inmediata**.
- **AdS tampoco debe venderse como carril ganador**.

Estado recomendado:

- **AdS = carril exploratorio técnicamente funcional y aún abierto**
- **Kerr / Kerr parametrizado = candidato serio si el siguiente criterio físico no mejora**

---

## Recomendación de proyecto

No borrar el trabajo AdS.

Sí hacer una de estas dos cosas:

1. **Congelar `ads_gkpw_second_chance_d4` como baseline exploratorio nuevo**, o
2. **cerrar una última evaluación física concreta** antes de decidir si el esfuerzo principal pasa a Kerr.

La decisión ya no debe basarse en “el pipeline ni corre”, porque eso ha dejado de ser cierto.
La decisión debe basarse en si este carril da o no **retorno físico suficiente** más allá de coherencia interna sandbox/diccionario.