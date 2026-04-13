# Estado del pipeline BASURIN

## Resumen ejecutivo

BASURIN se encuentra en una fase metodológicamente más madura que narrativamente cerrada. El valor principal del pipeline, en su estado actual, no es sostener claims físicos fuertes, sino separar con trazabilidad qué resultados son contratos operativos robustos, qué resultados son evidencia física interpretable y qué lecturas previas deben ser relajadas o deprecadas.

La posición técnica actual puede resumirse así:

- La infraestructura de ejecución, trazabilidad y validación contractual es uno de los activos más sólidos del proyecto.
- La cohorte canónica y los carriles de análisis están hoy mejor separados que en fases previas, reduciendo mezcla entre cobertura, OOD y validez contractual.
- El experimento de discriminación `exponential vs power-law` sobre `G2_ringdown` ha resuelto un cuello conceptual importante: Stage 04 ya no debe leerse como test físico de power-law.
- El siguiente cuello crítico no es ampliar narrativa física, sino cerrar la auditoría del estimador y congelar semánticamente los contratos antes de cualquier claim externo.

---

## 1. Estado actual del pipeline

### 1.1. Gobernanza, reproducibilidad y disciplina de ejecución

La parte más fuerte del pipeline hoy es la infraestructura epistemológica y operativa:

- IO determinista por `runs/<run_id>/...`
- gating explícito por `RUN_VALID`
- separación entre artefacto canónico, experimento y análisis downstream
- contratos por stage con validación explícita
- comportamiento fail-fast cuando un contrato falla

Esto no es una propiedad cosmética. Es la base que permite auditar resultados sin mezclar estados parciales, outputs no validados o conclusiones derivadas de runs contractualmente inválidos.

### 1.2. Cohortes y bases de comparación mejor separadas

El pipeline ya no está operando con mezcla difusa entre cohortes. La situación actual está más limpia:

- cohorte canónica efectiva de `33`
- cohorte OOD / ampliada de `55`
- base diaria de `52` en carriles de agregación tipo E5F

Esta separación reduce riesgo de sobreinterpretación y mejora la trazabilidad de cualquier conclusión agregada.

### 1.3. Ancla operativa de agregación

La ejecución ancla de arranque válida para E5F ya está fijada:

- `mvp_GW190408_181802_real_20260312T115334Z`
- estado `PASS`
- `n_events_aggregated = 52`
- `schema_version = e5f-0.1`

Esto permite trabajar con una base estable de agregación sin reabrir cada vez la discusión sobre cuál run es la referencia válida.

### 1.4. Cierre parcial de un cuello conceptual en Stage 04

El experimento de discriminación entre decaimiento exponencial y power-law sobre `G2_ringdown` ha tenido un efecto metodológico importante.

Resultado operativo consolidado:

- la cohorte canónica de `33` no está dominada por power-law;
- en cola estricta, la cohorte muestra una inclinación agregada hacia exponencial, pero con heterogeneidad relevante;
- una fracción no menor de eventos no queda bien descrita por ninguna de las dos familias simples.

Implicación directa:

> `correlator_structure` en Stage 04 no debe seguir interpretándose como test físico de power-law.

Esto no cierra la física final del observable, pero sí obliga a relajar la semántica contractual de ese stage.

---

## 2. Problemas actuales del pipeline

### 2.1. Semántica inflada en algunos contratos

El principal problema actual no es de ejecución, sino de interpretación contractual. Existen campos y salidas que estaban siendo leídos con una fuerza física mayor de la que realmente soportan.

Caso paradigmático:

- `has_power_law`
- `log_slope`
- lecturas tipo CFT, hyperscaling o `POSSIBLY_EINSTEIN_WITH_MATTER`

El problema no es necesariamente que el cálculo esté mal, sino que el significado atribuido al resultado era excesivo para la evidencia disponible.

### 2.2. Desacople entre detector operativo y claim físico

Varias partes del pipeline producen señales útiles como:

- gate de calidad,
- descriptor de forma,
- filtro de estructura,
- criterio de compatibilidad,

pero no deben elevarse automáticamente a claim físico.

La lección central de Stage 04 es precisamente esta:

> un ajuste log-log útil como descriptor en ventana finita no equivale a evidencia de power-law físico.

### 2.3. Heterogeneidad de cohorte

La cohorte no se comporta como un bloque uniforme. Esto aparece en varios frentes:

- eventos que favorecen exponencial;
- eventos que favorecen power-law;
- eventos `NEITHER_GOOD`;
- diferencias en soporte efectivo y enriquecimiento en carriles tipo RD-weighted;
- sensibilidad a joins, selección de submuestras y definición de ventana.

Esto obliga a evitar narrativas demasiado globales sin una capa previa de estratificación o auditoría de sensibilidad.

### 2.4. Bloqueos geométricos aguas arriba

Los carriles geométricos E5A/E5B/E5E/E5H siguen parcialmente condicionados por la falta de formalización upstream de la cohorte geométrica canónica compatible de `48` sobre una base diaria de `52`.

Esto significa que parte del bloqueo actual no es de física, sino de canonización y gobernanza de cohortes.

### 2.5. Fragilidad operativa en experimentos de enriquecimiento

El trabajo en T6 / RD-weighted fue útil porque forzó a depurar:

- joins correctos por `geometry_id`
- ubicación real de `delta_lnL`
- enriquecimiento desde `ranked_all`
- recomputación local contra IMR
- manejo explícito de `AF_EMPTY` y `CONSERVATIVE_SKIP`

Eso fortaleció el pipeline, pero también mostró que estos carriles requieren una lectura especialmente disciplinada para no sobreprometer interpretación física.

---

## 3. Próximas fases

### 3.1. Fase inmediata: reinterpretación formal de Stage 04

La siguiente acción mínima correcta no es reescribir toda la física del pipeline, sino congelar la reinterpretación semántica de `correlator_structure`.

Cambio mínimo recomendado:

- deprecar la lectura física de `has_power_law`
- reinterpretar `correlator_structure` como contrato relajado sobre estructura de decaimiento
- cortar la inferencia automática hacia CFT / hyperscaling / materia efectiva
- documentar explícitamente que el stage es un gate de forma o calidad, no un test físico concluyente

### 3.2. Integración de Q3 en auditoría de mecanismo

Siguiente bloque de trabajo ya fijado en la hoja de ruta:

- integrar Q3 en `high_mass_mechanism_audit`
- congelar `interpretation_freeze_q3`

Esto debe consolidar una lectura más estable de los resultados antes de seguir ampliando narrativa.

### 3.3. Filtro existencial del estimador

Este es el gate científico más importante de la hoja de ruta actual.

La pregunta aquí no es qué teoría apoya el pipeline, sino:

> si el estimador sobrevive a una auditoría seria de null, sintético y sesgo.

Mientras este gate no esté cerrado favorablemente, toda lectura física debe seguir siendo provisional.

### 3.4. Sensibilidad y congelación de interpretación física

Solo si el estimador sobrevive, el orden correcto es:

1. comparar `delta_f` frente a `Mf`, `af` y modelo conjunto;
2. auditar sensibilidad a modelado y referencia;
3. congelar interpretación física;
4. congelar claims externos y narrativa de paper.

La secuencia es correcta porque prioriza viabilidad y robustez antes de narrativa.

---

## 4. Posicionamiento científico actual

### 4.1. Qué está construyendo realmente BASURIN

En su estado actual, BASURIN está mejor posicionado como:

- pipeline auditable de inferencia estructural sobre ringdown;
- framework de análisis por cohortes con contratos explícitos;
- programa de falsación y depuración de sobreclaims;
- infraestructura reproducible para separar descriptor operativo de interpretación física.

Esto es más sólido y defendible que presentarlo, a estas alturas, como una prueba cerrada de holografía o como un motor de claims fuertes sobre CFT efectiva.

### 4.2. Diferencial frente a la comunidad

La propuesta distintiva del pipeline no es solo el contenido físico, sino la forma de trabajo:

- análisis sistemático de cohorte, no cherry-picking de pocos eventos;
- trazabilidad run por run;
- contratos ejecutivos explícitos;
- separación fuerte entre canónico, experimento y downstream;
- corrección activa de sobreinterpretaciones cuando la evidencia no las sostiene.

Ese posicionamiento es valioso frente a una comunidad donde muchos resultados son técnicamente sugerentes, pero menos auditables o menos robustos contractualmente.

### 4.3. Qué posición conviene evitar por ahora

No conviene posicionar aún BASURIN como:

- evidencia de holografía;
- lectura directa de dimensión conforme desde `log_slope`;
- soporte fuerte para hyperscaling;
- evidencia de materia efectiva basada en Stage 04.

La razón no es que esas direcciones estén descartadas para siempre, sino que el pipeline aún está en una fase donde su mayor fortaleza es **limpiar semántica y controlar inferencia**, no cerrar teoría final.

---

## 5. Posicionamiento recomendado en la comunidad

Formulación recomendada:

> BASURIN es un pipeline contract-first y auditable para analizar estructura de ringdown y compatibilidad geométrica en cohortes de eventos GW, con énfasis en trazabilidad, falsabilidad y control de sobreinterpretación física.

Esta formulación:

- protege la credibilidad del proyecto;
- encaja con el estado real del pipeline;
- permite comunicar valor metodológico fuerte sin inflar claims físicos;
- posiciona BASURIN como infraestructura científica seria y no como narrativa especulativa.

---

## 6. Conclusión operativa

El estado actual del pipeline puede resumirse así:

1. **La infraestructura de ejecución y auditoría es fuerte.**
2. **La cohorte canónica y los carriles están mejor separados que antes.**
3. **Stage 04 ya no puede sostener semántica de power-law física.**
4. **El problema central actual es semántico-epistemológico, no solo técnico.**
5. **La siguiente prioridad no es ampliar claims, sino cerrar auditoría del estimador y congelar interpretación contractual.**
6. **El mejor posicionamiento en la comunidad es como framework riguroso, falsable y reproducible de análisis estructural de ringdown.**

---

## 7. Mensaje corto para documentación ejecutiva

> BASURIN avanza de forma sólida en infraestructura, trazabilidad y control contractual. El pipeline ya permite distinguir entre descriptores operativos y claims físicos, y ha mostrado que ciertos contratos, como `correlator_structure` en Stage 04, deben reinterpretarse para evitar sobrelecturas de power-law físico. La prioridad inmediata es consolidar esta semántica, cerrar la auditoría del estimador y reforzar la posición del proyecto como framework auditable y reproducible para análisis estructural de ringdown en cohortes GW.
