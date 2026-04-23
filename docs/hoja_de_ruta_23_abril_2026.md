# Hoja de ruta — 23 de abril de 2026

## Estado actual

### Hecho verificado

En el carril activo del repo (Ruta B: literatura QNM → bridge stage02 → inferencia geométrica → auditoría downstream) ha aparecido una estructura reproducible en datos reales procesados por el pipeline.

En particular, la lectura de trabajo hoy es:

- existe una familia compacta reproducible tipo A/B/outlier;
- `03` produce una organización algebraica no amorfa;
- `04` acepta los 18/18 eventos inspeccionados sin fallos de contrato;
- `03` clasifica los 18/18 como `POSSIBLY_EINSTEIN_WITH_MATTER`.

### Inferencia legítima

Esto ya no encaja bien con la hipótesis “todo era ruido sin estructura”.

### Lo que todavía no está demostrado

No está demostrado que esa estructura sea una regularidad física externa del sistema astrofísico. Puede seguir siendo principalmente una regularidad robusta del surrogate geométrico / embedding del pipeline.

---

## Pregunta rectora

La pregunta que manda desde hoy es:

**¿La estructura A/B/outlier observada en Ruta B describe solo una regularidad interna del surrogate, o captura una regularidad física útil del ringdown real y del remanente?**

Todo lo que no ayude a responder esa pregunta baja de prioridad.

---

## Nivel de evidencia hoy

Punto de partida operativo:

- nivel metodológico: **alto**;
- nivel físico externo: **abierto**;
- valoración global: **escenario 2–3**.

Interpretación:

- ya hay una estructura fenomenológica reproducible;
- todavía no hay base para venderla como familia física fuerte;
- el lenguaje correcto, por ahora, es **familia fenomenológica / efectiva del carril real-data**.

---

## Reclamaciones permitidas y prohibidas

### Permitido decir

- hay evidencia de una estructura fenomenológica no trivial en el carril real-data;
- la estructura merece investigación seria;
- el pipeline no está devolviendo solo caos amorfo;
- el outlier `GW190503_185404` merece análisis específico.

### Prohibido decir por ahora

- que se ha encontrado nueva física;
- que se ha encontrado una familia física fundamental del ringdown;
- que el bulk inferido en Ruta B tenga interpretación fuerte por sí solo;
- que `POSSIBLY_EINSTEIN_WITH_MATTER` equivalga a validación física externa.

---

## Criterio de decisión

Esta hoja de ruta sube de nivel solo si pasan simultáneamente tres filtros:

1. **estabilidad metodológica**;
2. **interpretación física razonable**;
3. **anclaje externo mínimo**.

Si falla claramente cualquiera de los tres, la lectura física baja de nivel.

---

## Ejes de trabajo

### Eje 1 — Separar estructura del pipeline vs estructura física

### Objetivo

Medir cuánto de la familia A/B/outlier depende del dispositivo metodológico y cuánto parece sobrevivir como regularidad más robusta.

### Preguntas concretas

- ¿La familia compacta sobrevive a variantes razonables del checkpoint / inputs / bridge?
- ¿El outlier sigue siendo el mismo evento?
- ¿La rama B es estable o es una rotura frágil del ajuste?

### Criterio de éxito

La familia sigue viva sin colapso cualitativo bajo perturbaciones metodológicas razonables.

### Señal de fracaso

La estructura cambia de forma arbitraria o desaparece al tocar un elemento técnico moderado.

---

### Eje 2 — Dar lectura física al núcleo compacto

### Objetivo

Intentar interpretar el núcleo observado en variables con sentido físico y límites razonables.

### Preguntas concretas

- ¿La combinación compacta correlaciona con masa final, spin final, modo, calidad de fila o fuente?
- ¿El núcleo tiene monotonicidades razonables?
- ¿Tiene límites patológicos o dimensionalmente absurdos?

### Criterio de éxito

Existe una lectura física sobria, no ornamental, del núcleo y de la separación A/B.

### Señal de fracaso

La ecuación es compacta pero físicamente opaca o arbitraria.

---

### Eje 3 — Entender el outlier `GW190503_185404`

### Objetivo

Decidir si es un régimen físico especial o solo una rareza metodológica / de calidad.

### Preguntas concretas

- ¿sale como outlier de forma reproducible?
- ¿está asociado a masa alta, spin bajo u otro régimen identificable?
- ¿su calidad interna es claramente peor que la del resto?

### Criterio de éxito

El outlier queda explicado por régimen físico o por causa metodológica concreta.

### Señal de fracaso

Permanece “especial” sin explicación y sin estabilidad suficiente.

---

### Eje 4 — Medir valor predictivo fenomenológico

### Objetivo

Ver si la familia sirve para organizar o anticipar estructura fuera del subconjunto ya visto.

### Preguntas concretas

- ¿el patrón se mantiene al ampliar cohorte?
- ¿subcohortes distintas caen en la misma organización?
- ¿la separación A/B/outlier ayuda a resumir eventos nuevos de forma compacta?

### Criterio de éxito

La familia organiza nuevos casos sin reescribirse por completo.

### Señal de fracaso

La familia solo describe bien el conjunto ya inspeccionado y colapsa fuera de él.

---

## Orden de ejecución

### Fase 1 — Congelar lo que ya existe

### Objetivo

Fijar el estado actual como referencia para no mover la portería.

### Entregables mínimos

- copia en `docs/` del resumen del estado actual;
- referencia explícita al run base que sustenta la lectura 18/18;
- tabla mínima con eventos, rama A/B/outlier y observables principales.

### Veredicto esperado

A partir de aquí, todo cambio se compara contra esta referencia.

---

### Fase 2 — Releer outputs ya escritos en disco antes de correr nada nuevo

### Objetivo

Evitar trabajo duplicado y distinguir entre lo que ya está demostrado y lo que falta mirar.

### Acciones

- releer salidas de `03` y `04` del run base;
- localizar archivos donde ya esté la clasificación A/B/outlier;
- localizar archivo donde ya esté el núcleo compacto candidato;
- extraer citas internas verificables para futuras notas.

### Veredicto esperado

Inventario mínimo de outputs físicos ya disponibles.

---

### Fase 3 — Auditoría metodológica mínima

### Objetivo

Intentar romper la familia con cambios pequeños y razonables, no con reinvención del pipeline.

### Acciones

- comparar el run base con cualquier run cercano ya existente;
- comprobar si la familia A/B/outlier reaparece;
- comprobar si `GW190503_185404` sigue siendo especial;
- comprobar si el núcleo compacto cambia poco o mucho.

### Veredicto esperado

Primera estimación de robustez metodológica.

---

### Fase 4 — Lectura física del núcleo

### Objetivo

Traducir la estructura compacta a lenguaje de masa, spin, modo y calidad de dato.

### Acciones

- cruzar ramas A/B/outlier con `M_final`, `chi_final`, `freq_hz`, `damping_hz`, `mode_rank`;
- buscar monotonicidades, separaciones y degeneraciones;
- identificar si la rama B tiene firma física reconocible.

### Veredicto esperado

Nota técnica corta: “qué lectura física mínima soporta el núcleo”.

---

### Fase 5 — Decisión de estatus

### Objetivo

Asignar una etiqueta honesta al resultado.

### Posibles salidas

- **A. regularidad interna del surrogate**;
- **B. ley fenomenológica efectiva útil**;
- **C. pista física seria que merece validación externa más dura**.

### Regla

En caso de duda, quedarse en la categoría inferior.

---

## Primera ejecución práctica

La primera ejecución de esta hoja de ruta no es correr nada nuevo. Es esto:

1. identificar el **run base exacto** sobre el que descansa la lectura actual;
2. leer sus outputs de `03` y `04`;
3. extraer de ahí:
   - clasificación A/B/outlier,
   - núcleo compacto candidato,
   - lista de eventos,
   - posición de `GW190503_185404`.

Solo después decidimos si hace falta correr algo adicional.

---

## Plantilla de trabajo para cada paso

Para cada auditoría o microtarea derivada de esta hoja de ruta usar:

- **archivo / run**:
- **input real**:
- **output observado**:
- **hecho verificado**:
- **inferencia**:
- **riesgo de artefacto**:
- **siguiente cambio mínimo**:

---

## Criterio de estilo

- no vender física fuerte con `N` pequeño;
- no confundir `realdata_surrogate` con dualidad fuerte;
- no abrir rutas eliminadas;
- no crear scripts nuevos sin necesidad local clara;
- leer antes de correr;
- reutilizar antes de crear.

---

## Decisión operativa

A fecha **23 de abril de 2026**, esta estructura se trata como:

**una regularidad fenomenológica real y reproducible del carril activo de datos reales, todavía pendiente de discriminación entre artefacto metodológico robusto y regularidad física útil.**

Esa es la posición de trabajo oficial hasta que la evidencia obligue a subir o bajar de nivel.
