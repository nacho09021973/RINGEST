# Física del ringdown — precauciones fundamentales

**1. El problema del tiempo de inicio es el más peligroso del proyecto.**
* No existe consenso sobre cuándo empieza el ringdown lineal. Isi et al. vs Cotesta/Buonanno llevan años debatiéndolo. 
* El Bayes factor cambia órdenes de magnitud variando `t_inicio` en ventanas de solo ~5M (masas del agujero negro). 
* Tu parámetro `--start-offset` en `01_extract_ringdown_poles.py` es el más crítico del pipeline. 
* Nunca lo fijes sin justificación; trátalo como variable y estudia la sensibilidad.

**2. Con LIGO actual, solo tienes un polo confiable, máximo dos.**
* El SNR de ringdown en GW150914 es ~8-10 (el SNR total de 24 incluye la fase de inspiral). 
* Para resolver el overtone (2,2,1) necesitas un SNR de ringdown >20. 
* Si tu método ESPRIT extrae 3, 4 o 5 polos de datos reales, los extras son ruido disfrazado de física. 
* El parámetro `rank` en `esprit_poles()` debe estar en 1-2 para datos LIGO actuales, no más.

**3. La degeneración M·ω = f(a/M) es un problema serio.**
* Con un solo modo QNM fundamental, el mapa (ω_R, ω_I) → (M, a/M) está degenerado: no puedes separar masa y spin sin información adicional. 
* Necesitas al menos dos modos independientes para romper esa degeneración, y con el SNR actual eso es marginal. 
* Tu script `07` necesita tener esto en cuenta explícitamente.

**4. No mezcles "recuperar M y a" con "testear no-hair".**
* Recuperar parámetros de Kerr asumiendo que el agujero es Kerr es una cosa. Testear si el agujero es Kerr es otra. 
* Si entrenas un mapa aprendido con datos Kerr y luego validas con datos Kerr, no has testeado nada.

---

## El método ESPRIT/matrix-pencil — limitaciones prácticas

**5. Prony/ESPRIT genera polos espurios en presencia de ruido.**
* Cotesta et al. (arXiv:2107.05609) y su parte II (arXiv:2410.02704) documentan cómo un preprocesamiento descuidado (downsampling, filtrado) genera detecciones falsas. 
* Tu pipeline tiene un bandpass en `01`, revisa que el filtro no introduzca artefactos en el rango de ringdown (150-300 Hz para GW150914).

**6. El whitening del detector es obligatorio, no opcional.**
* El ruido de LIGO no es blanco. ESPRIT asume ruido blanco implícitamente. 
* Sin whitening adecuado, los "polos" que extrae pueden ser resonancias del espectro de ruido del interferómetro, no del agujero negro. 
* Verifica si `00_load_ligo_data.py` hace whitening o si delega eso.

**7. La ventana de análisis afecta los polos tanto como el método.**
* Ventanas cortas (<0.1s) tienen resolución espectral insuficiente para separar el fundamental del overtone. 
* Ventanas largas capturan ruido post-ringdown. 
* El rango razonable es 0.05s - 0.3s post-merger. 
* Tu default de `--duration 0.25` está en el límite largo; prueba con 0.05, 0.1 y 0.15 también.

---

## Datos y entrenamiento — evitar sobreajuste

**8. No entrenes el mapa holográfico solo con datos LIGO reales.**
* El catálogo GWTC-3 tiene ~90 eventos BBH pero solo 10-15 con SNR suficiente para ringdown confiable. 
* Con ese volumen memorizarás el ruido del detector, no la física. 
* La estrategia correcta: entrenar con waveforms sintéticos de NR/IMR (miles de puntos con parámetros conocidos), y usar LIGO solo para validación final.

**9. Usa el paquete `qnm` (Python) como ground truth.**
* Las tablas de Berti (arXiv:0905.2975) y el paquete `qnm` (arXiv:1908.10377) dan frecuencias QNM para cualquier (l, m, n, a/M) sin interpolación. 
* Deberían ser tu prior y tu oracle de validación en `06` y `07`. No construyas el diccionario desde cero cuando ya existe.

**10. El "sandbox" existente en `malda/` asume geometrías AdS — reemplázalo.**
* Los scripts `01_generate_sandbox_geometries.py` y `02_emergent_geometry_engine.py` generan datos sintéticos con física AdS. 
* Antes de tocar datos reales, necesitas un sandbox nuevo que genere señales de ringdown Kerr sintéticas con parámetros conocidos (M, a/M, SNR). 
* Sin eso no puedes verificar que el pipeline funciona.

---

## La correspondencia holográfica — honestidad epistémica

**11. El "bulk" que reconstruye `02` ya no es AdS — define qué es.**
* En AdS/CFT el bulk es una geometría hiperbólica extra-dimensional. 
* Para GW, la analogía natural es: boundary = strain en el detector, bulk = región del espacio-tiempo cerca del agujero negro. Pero esto es una metáfora, no una correspondencia matemática rigurosa. 
* Decide desde el principio si el objetivo es (a) usar las herramientas computacionales de AdS/CFT sin reclamar correspondencia formal, o (b) establecer una correspondencia. Son proyectos muy distintos.

**12. `LOSS_WEIGHT_PHYSICS_ADS = 0.02` en `02` es un prior físico incorrecto.**
* Esa regularización asume que la geometría bulk se parece a AdS. 
* Para Kerr, el prior correcto sería que A(z) y f(z) se parezcan a las funciones métricas de Kerr en Boyer-Lindquist. 
* Si no cambias ese prior, la red neuronal aprenderá geometría AdS aunque los datos sean de Kerr.

**13. La "dimensión conforme Δ" no existe en espacio plano.**
* Los scripts `07` y `08` usan Δ como variable central. Δ es una cantidad CFT que requiere invarianza conforme, que el vacío de Minkowski no tiene. 
* Para GW, la variable análoga es simplemente el índice armónico esferoidal (l, m, n). 
* Documentar esto explícitamente en el código evitará confusión futura.

---

## Infraestructura y reproducibilidad

**14. El debate Isi/Cotesta muestra que los resultados son muy sensibles a elecciones de preprocesamiento.**
* Tu pipeline debe loggear todos los parámetros de preprocesamiento (whitening, filtro, ventana, rank, start_offset) en el `run_manifest.json` por cada evento. 
* `00` ya hace algo así, pero verifica que `01` también lo capture todo. Sin reproducibilidad exacta, no puedes comparar resultados entre eventos.

**15. Compara siempre contra el repositorio ringdown de Isi.**
* Maximiliano Isi tiene un repositorio público (`github.com/maxisi/ringdown`) con análisis Bayesiano robusto de ringdown en datos LIGO reales. Es la implementación de referencia del campo. 
* Antes de publicar cualquier resultado, verifica que tus polos extraídos sean consistentes con los suyos en los mismos eventos.

**16. Los scripts `04b_negative_control_contracts.py`, `04c`, `04d` ya existen — mantenlos.**
* El proyecto ya tiene controles negativos para el pipeline AdS. 
* La equivalencia para GW sería: inyectar señales no-ringdown (ruido puro, sinusoides, chirps) y verificar que el pipeline no los clasifica como Kerr. 
* Sin controles negativos el pipeline no es científicamente defendible.

---

## Estrategia de adaptación — por dónde empezar

**17. El orden correcto de adaptación es: 02 → 06 → 07 → resto.**
* `02` es la columna vertebral (geometry engine). Si fallas ahí, todo lo demás es inútil. 
* `06` es el que genera el dataset de modos que alimenta el diccionario. 
* `07` aprende el mapa. Los scripts `03`, `04`, `05`, `08`, `09` son análisis y contratos que se adaptan sobre esa base.

**18. No adaptes 08 y 09 hasta que 07 funcione.**
* El diccionario holográfico de `08` y los contratos de `09` son downstream de todo. 
* Adaptarlos antes de tener un mapa (ω_R, ω_I) → (M, a/M) robusto es trabajo que puede quedar obsoleto.

**19. Los scripts `05_exp03_c3_metric_sensitivity_v3.py` y `07b_discover_lambda_delta_relation.py` son variantes iterativas — no los pierdas de vista.**
* Indican que el proyecto ya pasó por rondas de refinamiento en AdS. 
* Cuando adaptes `05` y `07`, usa esas variantes como referencia de qué no funcionó en iteraciones anteriores.

> **Para mañana concretamente:** empieza por crear el sandbox GW (punto 10) — un generador de señales de ringdown Kerr sintéticas con `qnm` + ruido gaussiano blanco, sin tocar datos reales todavía. Con eso puedes validar `01` y `02` en un entorno controlado antes de entrar en la complejidad del ruido real de LIGO.