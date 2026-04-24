# Plan maestro para avanzar en Ruta C / Kerr en RINGEST

## 0. Propósito del documento

Este documento fija una hoja de ruta completa para reorientar el proyecto hacia **Ruta C / Kerr** como carril principal de valor físico, aprovechando lo aprendido en los carriles A y B sin heredar sus sobreinterpretaciones. El objetivo no es abandonar A y B, sino subordinarlos a una pregunta observacional mejor planteada y coherente con el estado actual del repo.

La decisión estratégica de este documento es explícita:

> **Ruta C se redefine usando QNM publicados/literatura como input canónico, no un extractor propio desde strain como carril principal.**

Esto no prohíbe reabrir en el futuro un carril de extracción propia. Simplemente evita que el resultado físico principal dependa hoy de la parte más débil y menos estable del proyecto.

---

## 1. Lo que este plan asume y lo que no promete

### Asume

- Estamos en **fase de exploración**, no de confirmación. Ningún número producido por este plan se bloquea ni se publica hasta pasar por la Fase 5.
- Los carriles A (sandbox AdS/GKPW) y B (puente embedding / geometría efectiva) existen, se conservan y **no son el resultado principal**. Sirven como infraestructura, baseline metodológico y anexo exploratorio.
- El repo actual ya no debe tratar la antigua Ruta C basada en extracción propia tipo ESPRIT como carril canónico.
- El objetivo de Ruta C es una frase precisa (ver §2). Cualquier pregunta que no encaje en esa frase queda fuera del scope de este documento.

### No promete

- Detectar física más allá de GR.
- Establecer “familias efectivas” en datos LIGO como resultado físico principal.
- Probar holografía o AdS en datos de LIGO.
- Usar más de ~20 eventos con ringdown de calidad decente sin marcar explícitamente que el conjunto útil es pequeño.

---

## 2. Objetivo físico único de Ruta C

> **Cuantificar, evento a evento y globalmente, hasta qué punto los observables QNM reportados en la literatura para eventos GWTC son consistentes con el espectro de cuasi-modos de Kerr(M_f, a_f) dentro de los errores del propio ringdown publicado y de la incertidumbre del catálogo sobre (M_f, a_f).**

Esto se parece a lo que la LVK ya hace en sus papers de tests de GR, y eso es intencional: el objetivo es que RINGEST sepa reproducir, de forma independiente y auditable, un resultado que tiene tradición. Reproducir bien lo conocido es condición necesaria para poder después hablar de desviaciones.

### Input canónico

- QNM publicados / literatura: tablas, YAML, CSV o artefactos canónicos del repo derivados de literatura.
- `(M_f, a_f)` del posterior público del evento en GWTC, **no reconstruidos aquí** como parte principal de Ruta C.

### Observables principales

- `(f_220, γ_220)` por evento, con barras de error honestas ya publicadas o derivadas de la literatura usada.
- Opcional si la literatura lo soporta de forma trazable: `(f_221, γ_221)` o `(f_330, γ_330)`.

### Referencia a la que comparar

Espectro Kerr(M_f, a_f) con `(M_f, a_f)` tomados del posterior público del evento en GWTC.

### Criterio operacional de consistencia con Kerr

Residuo estandarizado por evento:

- `r_f = (f_obs - f_Kerr) / sqrt(σ_f_obs² + σ_f_Kerr²)`
- `r_γ = (γ_obs - γ_Kerr) / sqrt(σ_γ_obs² + σ_γ_Kerr²)`

Criterio mínimo:

- por evento, `|r| ≲ 2` como consistencia razonable;
- globalmente, la distribución conjunta de residuos debe ser compatible con `N(0,1)` usando KS y/o Anderson–Darling.

Eso es el núcleo. Si lo cumple, el pipeline es defendible. Si no, hay que buscar el sistemático antes de hablar de física.

---

## 3. Lo que los carriles A y B ya enseñaron y cómo se reaprovecha

## 3.1. Lección de Ruta A

Ruta A sirvió para construir infraestructura, bancos sintéticos, learners, checks de coherencia interna y métricas de regularidad. También mostró sus límites:

- el puente sandbox ↔ real es frágil;
- el learner puede fallar por razones de protocolo y entrenamiento antes de tocar física;
- la compatibilidad con familias del banco no equivale a pertenencia física;
- los outputs “geométricos” pueden reflejar más el sesgo del entrenamiento que una señal del dato.

### Qué sí se conserva para Ruta C

- disciplina de manifests, summaries y outputs trazables;
- tests de contrato;
- control de splits y checkpoints;
- auditorías de training/inference;
- detección de cuándo un carril colapsa por razones numéricas y no físicas.

### Qué no se arrastra

- la idea de que cercanía en embedding sea evidencia física fuerte;
- la prioridad interpretativa de una familia sintética sobre Kerr.

## 3.2. Lección de Ruta B

Ruta B fue útil como máquina de auditoría epistemológica. Enseñó varias cosas:

- el `einstein_score` era heurístico y no calibrado;
- cambiar de carril/Stage 02 podía alterar cualitativamente el resultado;
- el pipeline podía mezclar fallo de protocolo, fallo de entrenamiento y lectura física;
- hubo que distinguir entre estructura simbólica estable y significado físico estable;
- problemas aparentemente “físicos” acababan viviendo en detalles concretos: UV de `A(z)`, materialización de `best_epoch`, observables mal planteados en cierto gauge.

### Qué sí se conserva para Ruta C

- no vender scores sin calibración;
- no interpretar demasiado con N pequeño;
- no confundir una estructura reproducible con una lectura física correcta;
- auditar protocolo antes de auditar física;
- separar exploración de validación;
- congelar referencias y comparar por hashes / manifests / summaries.

### Regla de oro heredada

Si un resultado de A/B contradice la lectura principal de Ruta C pero no sobrevive la auditoría de Ruta C, se trata como **hipótesis interna o artefacto**, no como hallazgo.

---

## 4. Tesis central

Ruta C no intenta “probar holografía”, “probar AdS” ni “descubrir geometría emergente” en sentido fuerte. Intenta construir un pipeline que permita, con trazabilidad y controles:

1. reunir observables QNM publicados de forma reproducible;
2. estimar su compatibilidad con Kerr con uncertainties honestas;
3. contrastarlos contra predicciones Kerr;
4. separar con claridad:
   - consistencia con Kerr,
   - tensiones reales con Kerr,
   - y artefactos del pipeline o de la cadena de inputs.

### Qué sería un éxito realista

- un **catálogo reproducible** de observables de ringdown por evento;
- una **métrica de consistencia Kerr** bien definida y auditada;
- una **subcohorte robusta** de eventos con consistencia Kerr fuerte;
- una **subcohorte gris** donde la inconsistencia aparente esté dominada por sistemáticos del input/literatura o del propio pipeline downstream;
- una **cartografía clara de failure modes** del pipeline;
- y, solo después, una lectura secundaria de A y B como herramientas auxiliares o de sanity-check.

### Qué no cuenta como éxito

- “parece AdS-like”;
- “el embedding cae cerca de una familia”;
- “hay una ecuación simbólica compacta”;
- “un score sale alto”;
- “un run da una narrativa bonita”.

Todo eso puede ser útil como *diagnóstico interno*, pero no como núcleo de conclusión física.

---

## 5. Arquitectura de trabajo propuesta

## 5.1. Separación por capas

### Capa 1 — Literatura y cohortes

Responsable de:

- qué eventos entran;
- qué observables publicados se usan;
- qué metadata física se usa;
- qué tablas de referencia quedan congeladas.

### Capa 2 — Construcción del dataset canónico

Responsable de:

- unificar outputs de literatura en un formato común;
- homogeneizar convenciones y unidades;
- documentar provenance y calidad.

### Capa 3 — Contraste Kerr

Responsable de:

- tomar observables y compararlos con Kerr;
- producir residuales y verdicts continuos.

### Capa 4 — Auditoría y robustez

Responsable de:

- sensibilidad a elecciones del catálogo, modos, errores y convenciones;
- detección de failure modes;
- clasificación de eventos por confiabilidad.

### Capa 5 — Exploración auxiliar (A/B)

Responsable de:

- embeddings;
- learners geométricos;
- symbolic discovery;
- checks internos.

Siempre subordinada a las capas 2–4.

---

## 6. Plan por fases

## Fase 0 — Auditoría de lo existente

### Pregunta

¿Qué hay ya en disco y en el repo que pueda responder antes de correr nada nuevo?

### Meta

Dejar una base estable para no perder tiempo reabriendo lo ya resuelto.

### Tareas

1. Identificar qué scripts y artefactos de Ruta C existen realmente en el repo actual.
2. Identificar qué inputs canónicos de literatura existen ya:
   - YAML/CSV/tablas;
   - tablas de referencia;
   - artefactos derivados.
3. Identificar qué resultados de validación Kerr existen ya en disco.
4. Registrar explícitamente:
   - qué parches de Stage 02 están activos;
   - qué bug de materialización save-best ya quedó resuelto;
   - qué runs anteriores quedan obsoletos por protocolo.
5. Dejar en `runs_sync/` los artefactos ligeros esenciales.

### Criterio de salida

Se puede decir exactamente desde qué commit, qué tabla y qué run empieza la Ruta C canónica basada en literatura.

---

## Fase 1 — Fijar protocolo (decisiones humanas, cero código)

### Pregunta

¿Con qué criterios cerrados hacemos la comparación con Kerr?

### Tareas

1. **Catálogo y lista de eventos congelados**
   - versión exacta y fecha de snapshot;
   - lista de `event_id` que entran al análisis.

2. **Fuente canónica de QNM publicados**
   - paper / tabla / fichero exacto;
   - convenciones de unidades;
   - qué modos se aceptan.

3. **Observables a contrastar**
   - obligatorio: `220`;
   - opcional: `221` o `330` solo si la fuente es clara y trazable.

4. **Referencia Kerr**
   - una sola biblioteca/documentación para evaluar `(f_Kerr, γ_Kerr)`;
   - `(M_f, a_f)` del posterior público.

5. **Criterio de consistencia**
   - por evento: residuos estandarizados;
   - global: compatibilidad de la distribución de residuos con `N(0,1)`.

6. **Política de calidad**
   - qué fuentes/eventos pasan al análisis principal;
   - cuáles quedan como exploratorios.

### Criterio de salida

Existe un `PROTOCOLO_RUTA_C.md` o documento equivalente con reglas cerradas y fechadas.

---

## Fase 2 — Diagnóstico del input canónico de literatura

### Pregunta

¿El input canónico de literatura es internamente consistente y usable como base física estable?

### Meta

Sustituir la antigua “validación del extractor” por una validación del **input** que ahora será el cimiento de Ruta C.

### Tareas

1. Verificar cobertura del catálogo:
   - qué eventos tienen `220`;
   - cuáles tienen además `221`/`330`.
2. Verificar consistencia de unidades y convenciones:
   - frecuencia vs angular frequency;
   - damping rate vs decay time;
   - Hz vs geometrized units.
3. Verificar provenance y definición de errores:
   - qué significa cada `σ`;
   - si es simétrico o no;
   - si viene de posterior o de ajuste local.
4. Verificar que los valores reportados caen en órdenes físicos plausibles para Kerr.
5. Construir una tabla de anomalías de input:
   - missing fields;
   - errores inconsistentes;
   - modos ambiguos;
   - unidades sospechosas.

### Criterio de salida

Existe una tabla canónica limpia y una tabla de exclusiones/anomalías. Si el input no es homogéneo, se documenta explícitamente antes de pasar a Kerr.

### Qué se anota

- tabla de cobertura;
- tabla de anomalías;
- criterios de exclusión.

---

## Fase 3 — Construcción del dataset canónico Kerr-ready

### Pregunta

¿Podemos convertir la literatura en un dataset único, reproducible y listo para contraste Kerr?

### Meta

Tener una tabla maestra por evento y modo, con todo lo necesario y nada narrativo.

### Tareas

1. Unificar por evento:
   - `event_id`
   - `mode`
   - `f_obs`, `σ_f_obs`
   - `γ_obs`, `σ_γ_obs`
   - fuente exacta
   - flags de calidad
2. Adjuntar metadata Kerr:
   - `M_f`, `σ_M_f`
   - `a_f`, `σ_a_f`
   - referencia del posterior.
3. Congelar el formato del artefacto maestro.
4. Versionar esa tabla con provenance completo.

### Criterio de salida

Existe una tabla maestra reproducible con la que se puede correr el contraste Kerr sin intervención manual.

---

## Fase 4 — Test de consistencia Kerr por evento

### Pregunta

¿Son los observables QNM publicados consistentes con los valores de Kerr predichos por `(M_f, a_f)` del catálogo?

### Meta

Pasar de “parece razonable” a una métrica explícita por evento y global.

### Tareas

1. Para cada evento:
   - evaluar distribución de `(f_Kerr, γ_Kerr)` dada la incertidumbre en `(M_f, a_f)`;
   - calcular residuos estandarizados `r_f`, `r_γ`.
2. Producir dos plots mínimos:
   - `f_obs` vs `f_Kerr` con barras de error;
   - histograma de residuos frente a `N(0,1)`.
3. Aplicar tests globales (KS/AD).
4. Clasificar eventos en:
   - consistentes;
   - tensionados;
   - no concluyentes;
   - dominados por input dudoso.

### Criterio de salida

Cada evento queda mapeado a una fila con cantidades continuas de consistencia Kerr, no solo etiquetas narrativas.

---

## Fase 5 — Interpretación y criterios globales

### Pregunta

¿Qué puede y qué no puede decir RINGEST al final de todo esto?

### Meta

Responder la pregunta científica con el máximo rigor posible.

### Qué se puede decir

1. “Con el protocolo P y usando el input canónico de literatura L, hemos contrastado `(f_220, γ_220)` de `N` eventos contra Kerr.”
2. “La distribución de residuos estandarizados frente al espectro Kerr(M_f, a_f) es / no es compatible con `N(0,1)`.”
3. “Los eventos A, B, C presentan tensión aparente y requieren revisión de input / calidad / convenciones antes de interpretarse físicamente.”

### Qué no se puede decir

- “Hemos detectado estructura geométrica efectiva” como resultado principal.
- “Los eventos prefieren una familia holográfica frente a otra.”
- “N eventos confirman X” con `N ≲ 20`.

### Criterio de salida

Existe un documento corto de conclusión principal con afirmaciones defendibles una por una, cada una con su `N`, su `p`-valor, su set de eventos y el commit/hash del pipeline que las produjo.

---

## Fase 6 — (Opcional, diferido) Anexo exploratorio A+B

### Pregunta

¿Los eventos que pasan o tensan el test Kerr ocupan regiones particulares del embedding o de los outputs exploratorios de A/B?

### Carácter

Puramente descriptivo. No entra en el resultado principal.

### Tareas

1. Tomar los eventos con residuales ya calculados.
2. Proyectar sus features/embeddings existentes.
3. Colorear por `|r|` o por clase de consistencia Kerr.
4. Registrar si hay correlación diagnóstica.

### Regla

Si la hay, es una señal diagnóstica del embedding. No es evidencia holográfica.

---

## 7. Objetivos concretos de Ruta C

## 7.1. Objetivo 1 — Congelar un baseline canónico Kerr

Definir y congelar un baseline con:

- conjunto de eventos elegibles;
- fuente canónica de QNM;
- biblioteca Kerr;
- formato estándar de outputs;
- métrica estándar de consistencia Kerr.

## 7.2. Objetivo 2 — Construir un catálogo reproducible por evento

Para cada evento, generar un registro mínimo estable con:

- evento;
- modo;
- observables publicados;
- incertidumbres;
- masa/spin finales usados;
- predicción Kerr correspondiente;
- residuales;
- flags de calidad;
- provenance exacto.

## 7.3. Objetivo 3 — Definir la métrica de consistencia Kerr

Necesitamos una métrica que sea:

- interpretable;
- auditable;
- estable;
- separable por componentes.

## 7.4. Objetivo 4 — Auditoría de sistemáticos del input y del downstream

No basta con un número final. Hay que medir sensibilidad a:

- elección de fuente de literatura;
- convenciones;
- modo reportado;
- propagación de incertidumbres;
- filtro de calidad.

## 7.5. Objetivo 5 — Publicabilidad interna

Ruta C debe producir resultados que sobrevivan una lectura crítica severa dentro del propio proyecto antes de pensar en fuera.

---

## 8. Dónde está la novedad real si sale bien

La novedad no debe venderse como “hemos redescubierto Kerr”.

La novedad, si sale, vive en algo más sobrio y más fuerte:

- una **auditoría independiente y reproducible** del contraste Kerr;
- una separación clara entre:
  - consistencia robusta,
  - tensión aparente por sistemáticos,
  - y artefactos de cadena de análisis;
- una cartografía explícita de qué parte del resultado depende del input y cuál del downstream.

Eso es menos vistoso que A, pero mucho más publicable si queda limpio.

---

## 9. Preguntas concretas que sí merece atacar primero

### Pregunta 1

> Para la subcohorte fuerte, ¿qué fracción de eventos es consistentemente compatible con Kerr usando input canónico de literatura y propagación honesta de errores?

### Pregunta 2

> En los eventos que parecen tensar Kerr, ¿la tensión sobrevive al cambio razonable de input/fuente/convenios o se evapora?

### Pregunta 3

> ¿Qué failure modes recurrentes del pipeline o del input imitan inconsistencia con Kerr?

### Pregunta 4

> ¿Qué subcohorte mínima tiene calidad suficiente para una afirmación robusta?

---

## 10. Entregables concretos que debería producir Ruta C

## 10.1. Tabla maestra por evento y modo

Con columnas mínimas como:

- event
- mode
- source_reference
- f_obs
- sigma_f_obs
- gamma_obs
- sigma_gamma_obs
- M_f
- sigma_M_f
- a_f
- sigma_a_f
- f_kerr
- gamma_kerr
- residual_f
- residual_gamma
- quality_tier
- robustness_flag
- verdict_kerr
- provenance

## 10.2. Documento de definición de métrica

Un markdown único donde quede fijado:

- fórmula de la métrica;
- inputs;
- thresholds si existen;
- qué significa cada rango;
- y qué no significa.

## 10.3. Documento de auditoría de input/sistemáticos

Tabla o md con sensibilidad por evento a fuente, convenciones y propagación de errores.

## 10.4. Documento de conclusión principal

Corto y sin humo:

- qué es consistente con Kerr;
- qué no;
- qué sigue abierto;
- qué está dominado por sistemáticos.

---

## 11. Riesgos principales

## 11.1. Riesgo 1 — Sobreajuste narrativo

Que el proyecto quiera seguir sacando jugo geométrico donde lo único defendible es Kerr + sistemáticos.

## 11.2. Riesgo 2 — Cohortes demasiado pequeñas

Que se venda demasiado con N pequeño.

## 11.3. Riesgo 3 — Métricas heurísticas

Que se cuele otro “score bonito” sin calibración.

## 11.4. Riesgo 4 — Mezcla de carriles

Que A/B sigan infiltrando la conclusión física final.

## 11.5. Riesgo 5 — Confundir input canónico con verdad absoluta

La literatura también tiene convenciones, sesgos y decisiones metodológicas. El input canónico mejora la base, pero no sustituye la auditoría.

---

## 12. Reglas prácticas para no perder el norte

1. Un rerun debe responder una pregunta concreta.
2. Cada cambio de código debe ir en commit separado por tema.
3. Las métricas continuas van antes que las etiquetas binarias.
4. Kerr es la referencia primaria.
5. A/B solo como auxiliares.
6. No interpretar nada fuerte con subcohortes débiles.
7. No mover umbrales para “arreglar” un resultado.
8. Si un resultado cambia al tocar protocolo, primero se arregla protocolo.
9. No presentar como hallazgo físico una divergencia que pueda venir del input canónico mal homogeneizado.

---

## 13. Orden de trabajo recomendado desde hoy

## Paso 1

Consolidar el estado del repo y fijar la fuente canónica de QNM de literatura.

## Paso 2

Construir o congelar la tabla maestra Kerr-ready.

## Paso 3

Definir formalmente la métrica Kerr y los thresholds interpretativos.

## Paso 4

Ejecutar el contraste Kerr por evento y global.

## Paso 5

Hacer la primera auditoría corta de sensibilidad a fuente/convenios/errores.

## Paso 6

Solo después volver a mirar A/B para ver si aportan algo diagnóstico adicional.

---

## 14. Mi juicio estratégico

Si el proyecto quiere maximizar probabilidad de producir algo serio, Ruta C debe convertirse en el carril principal. Ruta A y Ruta B no se tiran: se reutilizan como instrumentación interna y como generadores de hipótesis. Pero el peso físico y narrativo debe pasar a Kerr.

Dicho de forma simple:

- **Ruta A** aporta infraestructura y bancos.
- **Ruta B** aporta auditoría epistemológica y disciplina contra autoengaños.
- **Ruta C** es donde puede vivir el resultado físico defendible.

En la nueva definición de Ruta C, el valor no está en extraer desde strain con método propio, sino en razonar bien sobre observables confiables y producir una auditoría downstream mejor que la habitual.

---

## 15. Checklist de honestidad

Antes de marcar una fase como cerrada:

- [ ] ¿La decisión o el resultado está escrito, con fecha, en un `.md` de notas o docs?
- [ ] ¿Alguna afirmación depende de `N < 10` eventos? Si sí, ¿está marcada como preliminar?
- [ ] ¿Se están comparando números con sus errores, o solo medianas?
- [ ] ¿El criterio de salida era fijo antes de ver los resultados?
- [ ] ¿Alguna métrica bonita está actuando como prueba física sin un test físico detrás?
- [ ] ¿Se está hablando de “dualidad”, “geometría emergente” o “familias” en un sentido que Ruta C no ha demostrado?
- [ ] ¿Se ha auditado el input canónico antes de interpretar una tensión con Kerr?

Si cualquier respuesta es “no sé”, la fase no se cierra todavía.

---

## 16. Conclusión final

El mejor futuro del proyecto no pasa por intentar forzar que los datos de LIGO “sean AdS”, sino por construir un pipeline de ringdown lo bastante serio como para responder, con honestidad y reproducibilidad, cuándo los observables QNM publicados son compatibles con Kerr, cuándo no, y cuándo el propio pipeline todavía no merece decidir. Si Ruta C se hace bien, A y B seguirán siendo valiosos; pero dejarán de ser el centro de gravedad y pasarán a ser lo que hoy más necesitan ser: herramientas al servicio de una pregunta física correcta.

