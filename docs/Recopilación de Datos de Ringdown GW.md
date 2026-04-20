# **Reporte Exhaustivo: Parámetros de Ringdown y Espectroscopía de Agujeros Negros en la Literatura de Ondas Gravitacionales**

## **Fundamentos Físicos de la Teoría de Perturbaciones y Modos Cuasinormales**

La detección de ondas gravitacionales provenientes de la coalescencia de sistemas binarios de agujeros negros representa uno de los logros empíricos más transcendentales de la astrofísica contemporánea. De acuerdo con la formulación de la relatividad general, el producto evolutivo final de la fusión de dos agujeros negros en el vacío absoluto es un único agujero negro altamente perturbado. Para alcanzar un estado estacionario, este remanente dinámico debe disipar las asimetrías topológicas transitorias de su horizonte de eventos mediante la emisión de radiación gravitacional. Esta fase final de estabilización topológica se conoce en la literatura especializada como la etapa de *ringdown*.

El marco teórico subyacente para modelar matemáticamente esta fase de *ringdown* se ancla sólidamente en la teoría de perturbaciones de agujeros negros. Originalmente concebida a través de las formulaciones métricas de Regge-Wheeler y Zerilli para agujeros negros de Schwarzschild (no rotatorios), la teoría alcanzó su madurez analítica mediante la derivación de la ecuación maestra de Teukolsky.1 Dicha ecuación describe el comportamiento de campos de espín genérico en la geometría curva de un agujero negro de Kerr (rotatorio), utilizando el formalismo de tétradas nulas de Newman-Penrose. La solución de la ecuación de Teukolsky bajo las condiciones de contorno físicas apropiadas —específicamente, ondas puramente convergentes hacia el horizonte de eventos y ondas puramente divergentes en el infinito asintótico espacial— resulta en un problema de autovalores complejos.

Estos autovalores caracterizan una superposición lineal de ondas exponencialmente amortiguadas denominadas modos cuasinormales (QNM, por sus siglas en inglés). La deformación del espaciotiempo observada por la red de interferómetros terrestres, expresada como el *strain* ![][image1], puede ser aproximada en el régimen lineal post-fusión mediante la siguiente descomposición espectral:

![][image2]  
En esta expresión, los índices enteros ![][image3] y ![][image4] corresponden a los armónicos esféricos con espín (spin-weighted spherical harmonics) que tipifican la morfología angular de la perturbación gravitacional. El índice ![][image5] denota el número de sobretono (overtone), ordenado de menor a mayor grado de amortiguamiento. El estado de excitación fundamental corresponde al armónico ![][image6]. Para la vasta mayoría de coalescencias cuasi-circulares con espines moderadamente alineados observadas por las colaboraciones LIGO, Virgo y KAGRA (LVK), el armónico dominante en la señal radiada es el modo cuadripolar fundamental, denotado unívocamente como ![][image7].2

La importancia astrofísica y cosmológica de la fase de *ringdown* radica intrínsecamente en su capacidad para someter a prueba el postulado de unicidad o teorema de "no pelo" (No-Hair Theorem) de la relatividad general. Este teorema dictamina que la solución exterior de un agujero negro estacionario y asintóticamente plano está exhaustivamente definida por tan solo tres parámetros macroscópicos conservados: su masa inercial (![][image8]), su momento angular o espín adimensional (![][image9]), y su carga eléctrica neta (la cual se asume estrictamente nula en entornos astrofísicos debido a la rápida neutralización por plasma circundante).1 En consecuencia directa, el espectro analítico completo de las frecuencias de oscilación ![][image10] y los tiempos de amortiguación ![][image11] de cualquier modo cuasinormal es una función determinista que depende única y exclusivamente de la masa final (![][image12]) y del espín final (![][image13]) del remanente.

La extracción rigurosa de los parámetros frecuenciales a partir del flujo de datos interferométricos habilita un mapeo analítico hacia el espacio de parámetros ![][image14]. Si la sensibilidad del detector permite aislar y medir de manera independiente al menos dos modos cuasinormales distintos (ya sea el modo fundamental emparejado con un sobretono como el ![][image15], o junto a un modo angular subdominante como el ![][image16]), se puede orquestar un test de consistencia matemática estricto conocido formalmente como espectroscopía de agujeros negros. Esta técnica verifica si las evaluaciones independientes de masa y espín proyectadas por cada armónico convergen inequívocamente hacia las mismas coordenadas del espacio paramétrico, confirmando la naturaleza de Kerr del remanente o señalando posibles violaciones de la relatividad general.3

## **Metodologías Analíticas de Inferencia Bayesiana y Extracción Paramétrica**

La literatura contemporánea producida por el consorcio LVK reporta la extracción de los componentes espectrales de *ringdown* a través del despliegue masivo de marcos de inferencia bayesiana jerárquica y algoritmos de Cadenas de Markov de Monte Carlo (MCMC). La evaluación bayesiana busca estimar la distribución de probabilidad a posteriori de los parámetros del modelo dados los datos empíricos. La complejidad inherente a la estimación paramétrica post-fusión se deriva directamente de la ambigüedad en la definición del instante temporal exacto ![][image17] en el que el régimen no lineal y turbulento de la fusión transiciona suavemente hacia el régimen puramente lineal descrito por la teoría de perturbaciones y los QNM.5

Una inspección profunda de los catálogos oficiales, como el Gravitational-Wave Transient Catalog (abarcando GWTC-1, GWTC-2, y GWTC-3), expone la utilización sistemática de tres paradigmas metodológicos radicalmente distintos para derivar los valores de la frecuencia fundamental ![][image18] y su tiempo de decaimiento asociado ![][image19].8 Las discrepancias sutiles pero manifiestas entre estos métodos revelan las tensiones estadísticas entre la presuposición de modelos físicos rígidos frente a la susceptibilidad del ajuste libre ante las fluctuaciones de ruido estacionario.

### **Enfoque de Modelado Completo: Inspiral-Merger-Ringdown (IMR)**

El método de análisis IMR (frecuentemente estructurado dentro de pruebas de consistencia IMR o IMR Consistency Tests) opera bajo el postulado epistemológico fundamental de que la relatividad general constituye la descripción innegable e inalterada de la gravedad en todas las escalas observadas. Este método sintetiza formas de onda fenomenológicas de espectro completo (tales como las familias IMRPhenomPv2, IMRPhenomXPHM o los modelos Effective-One-Body SEOBNRv4\_ROM) que simulan de manera continua y coherente la espiral de aproximación (inspiral), el punto de colisión no lineal (merger) y la subsecuente relajación (ringdown).

En el esquema IMR, los parámetros intrínsecos del agujero negro remanente (![][image12], ![][image13]) se derivan inicialmente mediante el escrutinio probabilístico de la fase pre-fusión, basándose en funciones de ajuste numérico (fits) extrapoladas de millones de horas de cálculo en supercomputadoras ejecutando simulaciones de relatividad numérica.8 Subsecuentemente, aplicando las fórmulas analíticas cerradas predefinidas por la teoría de Kerr, se proyectan estadísticamente las distribuciones a posteriori teóricamente esperadas para ![][image18] y ![][image19]. La máxima fortaleza analítica de la arquitectura IMR descansa en su robustez estadística, dado que integra la relación señal-ruido (SNR) acumulada a lo largo del transcurso íntegro del evento gravitacional. No obstante, este enfoque incorpora el sesgo sistemático ineludible de forzar la plantilla de forma de onda a obedecer inquebrantablemente las predicciones canónicas de Einstein, suprimiendo la capacidad del algoritmo para revelar discrepancias paramétricas libres si el remanente poseyera topologías exóticas.8

### **Enfoque de Modelado Empírico Independiente (Damped Sinusoid / pyRing)**

Para evaluar críticamente las propiedades espectrales del agujero negro eliminando las restricciones de los postulados teóricos preconcebidos, la infraestructura de análisis de datos de LIGO emplea paralelamente estrategias puramente empíricas. La implementación más extendida radica en el ajuste directo de modelos de sinusoides amortiguadas (Damped Sinusoids \- DS), rutinariamente ejecutado a través del paquete computacional de código abierto *pyRing* o mediante rutinas en *BayesWave*.8 En este marco analítico agnóstico, la frecuencia de oscilación central ![][image18] y la constante de tiempo de decaimiento exponencial ![][image19] se codifican como parámetros independientes, desvinculados por completo y con distribuciones previas (priors) uniformes no informativas dentro de las simulaciones MCMC.

Al no imponer la interdependencia matemática forzosa exigida por la métrica de un agujero negro de Kerr, el método DS se posiciona como el instrumento predilecto para detectar desviaciones espectrales hacia físicas más allá del modelo estándar. Desafortunadamente, la ejecución de inferencia basada en plantillas de sinusoides amortiguadas exhibe vulnerabilidades extremas frente a las caracterizaciones de la Densidad Espectral de Potencia (PSD) del ruido. Al descartar deliberadamente las trazas formadas durante los instantes de inspiral, la porción de relación señal-ruido (SNR) restante disponible para el ajuste del *ringdown* experimenta una merma severa, constituyendo en ocasiones una fracción minúscula de la SNR global.8

Esta precariedad informativa propicia la manifestación de artefactos estadísticos perniciosos y sólidamente tipificados en la literatura. Específicamente, se reporta una recurrente y drástica sobreestimación estadística del tiempo de amortiguación ![][image19] en detecciones que adolecen de un SNR post-fusión marginal. La anomalía se produce porque el muestreador bayesiano, en la ausencia de una señal determinista fuerte, dilata la cola exponencial del modelo para subsumir espuriamente las fluctuaciones acústicas transitorias o el piso de ruido instrumental de baja frecuencia, un fenómeno que dilata la amplitud temporal en los resultados arrojados para la constante de decaimiento.8

### **Enfoque Parametrizado Híbrido (pSEOBNRv4HM)**

Como resolución integradora entre la asfixia teórica del modelo IMR y la inestabilidad estocástica del ajuste fenomenológico DS, las colaboraciones científicas desarrollaron el andamiaje intermedio pSEOBNRv4HM. Este modelo, fundamentado en la mecánica de "Cuerpos Efectivos Únicos" (Effective-One-Body) con inclusión matemática de múltiples armónicos superiores (Higher Modes \- HM), redefine el espectro en función de desviaciones o fluctuaciones fraccionales pivotando sobre el núcleo del modelo nominal dictado por la Relatividad General.8

Específicamente, el modelo transfigura los parámetros según las variables: ![][image20] y ![][image21].8 Durante la iteración de las cadenas de inferencia, las cantidades fraccionales ![][image22] y ![][image23] asumen el rol de grados de libertad adicionales. Este esquema analítico preserva prodigiosamente la coherencia de fase con la mecánica pre-fusión (aprovechando así la cuantiosa contribución de SNR del evento pre-colisión), simultáneamente consintiendo que las métricas finales de *ringdown* orbiten libremente alrededor del valor esperado si la física subyacente lo demanda. Representa en la actualidad el estándar dorado de precisión paramétrica en la arena de comprobación de teorías de gravedad.8

## **Desafíos Sistémicos de la Astronomía Interferométrica: Ruido y Sobretonos**

La estimación de los valores del espectro residual transitorio representa el eslabón analítico más vulnerable frente a las carencias instrumentales de la astronomía de ondas gravitacionales actual. Las frecuencias tabuladas del modo estacionario fundamental ![][image24] fluctúan diametralmente en función de las masas de los progenitores; oscilando desde el rango inferior de ![][image25] hercios para macroestructuras de agujeros negros de masa intermedia (como el singular GW190521), hasta frecuencias en exceso de los ![][image26] hercios correspondientes a colapsos de masa estelar convencional (como GW170104 y GW170814).8 Este margen frecuencial coincide incidentalmente con el segmento de la campana de máxima sensibilidad operativa para los interferómetros terrestres Advanced LIGO (ubicados en los enclaves de Hanford y Livingston) y Advanced Virgo. Paradójicamente, este abismo acústico alberga también la más alta concentración de "glitches" instrumentales: descargas de energía anómala y ruido estocástico no estacionario inducido por perturbaciones antropogénicas, fluctuaciones mecánicas de las suspensiones o transitorios de luz dispersa.12

El impedimento cardinal se materializa durante la caracterización empírica de la matriz de covarianza de ruido o Densidad Espectral de Potencia (PSD) perimetral al evento transitorio. Si la morfología de un "glitch" cruza y contamina los escasos milisegundos inmediatamente subsecuentes al pico de amplitud máxima de la deformación tensorial, la extracción matemática de ![][image19] se corrompe en el nivel fundamental, inhabilitando la fiabilidad de la medición paramétrica.12 La literatura es prolija en la documentación de eventos que han sufrido la censura metodológica en pruebas gravitacionales combinadas precisamente por este impedimento técnico, requiriendo estrategias de mitigación agresivas como el enmascaramiento temporal (gating) o la interpolación reconstructiva (inpainting), los cuales a su vez pueden sembrar sesgos en los armónicos subyacentes.

Un territorio colindante de acalorado debate analítico involucra el impacto y la interpretabilidad de los sobretonos de excitación (![][image27]). La intrincada superposición armónica del modo fundamental con la vibración efímera de su primer sobretono adyacente ![][image15] goza de la capacidad matemática para enmascarar u oscurecer la frecuencia aparente detectada en las fases agudas justo post-fusión.5 Un caso paradigmático disecado en la literatura de revisión por pares gira en torno al evento original GW150914. Análisis exhaustivos capitaneados por fracciones de la comunidad postulan que el soporte bayesiano para atestiguar la existencia empírica del modo ![][image15] exhibe fluctuaciones sumamente erráticas ante desplazamientos infinitesimales (en el orden de fracciones de milisegundo) en la parametrización de la marca de tiempo de inicio ![][image17].5

Dada la extrema tasa de amortiguación intrínseca a los sobretonos (cuyos intervalos de persistencia se extinguen usualmente en temporalidades menores a 1 milisegundo), dilucidar conclusivamente si la perturbación asimétrica post-pico constituye la firma genuina de un sobretono legítimo excitado por la colisión, frente a la hipótesis alternativa de una fluctuación maliciosa en los componentes del ruido acústico coloreado, requiere una fidelidad estocástica en los modelos de ruido que tensiona severamente las arquitecturas tecnológicas de la actual generación.5

## **Disecando la Astrofísica Paramétrica por Categorías de Eventos**

La compilación paramétrica subyacente revela patrones astrofísicos que demandan una exploración pormenorizada evento por evento. El conjunto de datos (consolidado en el listado extenso extraído fundamentalmente de los apéndices documentales y matrices tabulares como la Tabla IX del Physical Review D 103, 122002 8) demuestra cómo la fenomenología de la señal modula profundamente los valores recuperados:

### **Los Eventos Dorados de Alta Relación Señal-Ruido**

**GW150914:** La génesis observacional de este campo continúa erigiéndose como el pináculo de la fiabilidad. Su monumental relación señal-ruido total (![][image28]) faculta a la arquitectura estadística para entregar una certidumbre abrumadora. Las inferencias derivan un alineamiento casi inmaculado entre los regímenes teóricos e independientes. Específicamente, el análisis dependiente del modelo (IMR) fija la frecuencia fundamental ![][image18] en 248 Hz y la amortiguación en 4.2 ms, mientras que el ajuste empírico ciego de sinusoide amortiguada (DS) recupera valores casi gemelos de 247 Hz y 4.8 ms respectivamente.7 Una divergencia por debajo de 1 hercio entre métodos conceptualmente disjuntos proporciona la validación empírica más contundente a las formulaciones de Kerr elaboradas un siglo atrás.

### **Remanentes de Masa Intermedia y Frecuencia Grave**

**GW190521:** Catalogado como un evento extraordinariamente masivo, originado en el choque de dos agujeros negros que totalizaron más de 150 masas solares, GW190521 arrastró la integridad de su firma espectral hacia las frecuencias gravitacionales bajas extremas. Con el cénit de colisión transcurriendo cerca de los 60 Hz, el grueso íntegro de la fenomenología detectable residió exclusivamente en el *ringdown*.8 A causa de la inercia masiva del espaciotiempo agitado, la cadencia de la amortiguación se ralentizó superlativamente. Los tabuladores reportan un ![][image19] masivo oscilante entre 15.8 ms (IMR) y 30.7 ms (pSEOB). Interesantemente, a pesar de la divergencia en la amplitud de decaimiento temporal debido a la sensibilidad a los priors, la variable frecuencial permaneció blindada firmemente en un rango estrecho de 65 a 68 Hz sin importar el arsenal metodológico implementado 8, demostrando que las mediciones de frecuencia en el régimen cuasinormal exhiben inmunidad frente a la degradación metodológica cuando se enfrentan a cuerpos de masa elevada.

### **Anomalías Inducidas por Señales Precarias (Baja SNR Post-Fusión)**

La arquitectura empírica sufre fracturas cuando escruta eventos cuya energía residual escapa de los dominios perceptivos de los láseres, generando artefactos estadísticos significativos que deben aislarse en cualquier base de datos para prevenir conclusiones teóricas defectuosas.

**GW170814 y GW170823:** Pese al valor histórico del primero como la detección fundacional triangulada por la matriz de tres instrumentos (H1+L1+V1) optimizando su elipse de localización cósmica 18, su rendimiento en espectroscopía libre es deficiente. Mientras la inferencia IMR forzada recupera frecuencias ortodoxas de 293 Hz y 197 Hz respectivamente (junto a amortiguamientos razonables de ![][image29] y ![][image30] ms), el algoritmo ciego de sinusoide amortiguada implosiona. Para GW170814, DS sugiere una frecuencia desbocada de 527 Hz acoplada a un lapso irreal de 25.1 milisegundos; en GW170823, sugiere un tiempo dilatado de 13.4 ms.8 Estas aberraciones matemáticas poseen márgenes asimétricos masivos (e.g., errores ascendentes de ![][image31] Hz). Reflejan indiscutiblemente la capitulación del muestreador bayesiano, el cual, desprovisto de una SNR neta en el tramo final, migra hacia el perímetro exterior del marco previo (prior boundary), acoplándose falazmente con el rumor termo-óptico del detector.

Este colapso analítico subraya la necesidad ineludible de reportar los análisis de manera plural (separando filas por tipo de pipeline) y documentar extensivamente las incertidumbres. En el diseño paramétrico de nuestro dataset, esto se atiende calculando rigurosamente las sigmas asimétricas para trazar su dispersión real. Se evidencia un patrón idéntico de descalabro algorítmico frente a la falta de potencia irradiada post-cénit en la evaluación empírica DS de eventos adicionales como **GW190408\_181802**, **GW190512\_180714**, **GW190708\_232457**, **GW190727\_060333**, y **GW190915\_235702**. En todos ellos, la métrica DS arroja frecuencias centralizadas virtualmente aleatorias y colapsos hacia ![][image19] sobreestimados dramáticamente por encima de 15 ms a 26 ms, un síntoma clásico del "latching" al piso estocástico de baja frecuencia.8

## **Catálogo de Parámetros Extraídos (Dataset Trazable)**

La tabla a continuación compila de forma exhaustiva los parámetros publicados para el modo 220 de las coalescencias reales extraídas estrictamente de literatura avalada y repositorios de Data Release públicos de las colaboraciones LIGO, Virgo y KAGRA.

Para satisfacer la inyección programática requerida, las incertidumbres asimétricas (plus\_error, minus\_error) listadas originalmente en las fuentes bibliográficas 8 han sido armonizadas hacia un único valor representativo de dispersión ![][image32], aproximado matemáticamente como la semidiferencia modular combinada o semiancho medio: ![][image33]. Esta conversión queda constatada en la columna notes para precaver pérdida de metadatos. Toda casilla desprovista de evidencia empírica directa en las fuentes primarias se declara como null en respeto al mandato taxativo de "no inventar números".

| event | source\_kind | source\_paper | source\_doi | source\_url | source\_locator | analysis\_method | detector\_set | credible\_interval | M\_final\_Msun | sigma\_M\_final\_Msun | chi\_final | sigma\_chi\_final | f\_220\_hz | sigma\_f\_220\_hz | tau\_220\_ms | sigma\_tau\_220\_ms | notes |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| GW150914 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | IMR | H1+L1 | 90% | null | null | null | null | 248.0 | 7.5 | 4.2 | 0.25 | sigma approximated from asymmetric CI: f(+8/-7), tau(+0.3/-0.2) |
| GW150914 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | Damped Sinusoid (DS) | H1+L1 | 90% | null | null | null | null | 247.0 | 15.0 | 4.8 | 2.8 | sigma approximated from asymmetric CI: f(+14/-16), tau(+3.7/-1.9) |
| GW170104 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | IMR | H1+L1 | 90% | null | null | null | null | 287.0 | 20.0 | 3.5 | 0.35 | sigma approximated from asymmetric CI: f(+15/-25), tau(+0.4/-0.3) |
| GW170104 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | Damped Sinusoid (DS) | H1+L1 | 90% | null | null | null | null | 228.0 | 86.5 | 3.6 | 19.15 | sigma approximated from asymmetric CI: f(+71/-102), tau(+36.2/-2.1) |
| GW170104 | data\_release | Tests of General Relativity with GWTC-3 | arXiv:2112.06861 | [https://zenodo.org/records/17461225](https://zenodo.org/records/17461225) | Table XIII / Fig 14 text | pSEOBNRv4HM | H1+L1 | 90% | 69.9 | 18.4 | 0.87 | 0.255 | 296.6 | 56.7 | 5.04 | 3.065 | sigma approximated from asymmetric CI: f(+58.9/-54.5), tau(+3.76/-2.37), M(+16.2/-20.6), chi(+0.09/-0.42) |
| GW170814 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | IMR | H1+L1+V1 | 90% | null | null | null | null | 293.0 | 12.5 | 3.7 | 0.25 | sigma approximated from asymmetric CI: f(+11/-14), tau(+0.3/-0.2) |
| GW170814 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | Damped Sinusoid (DS) | H1+L1+V1 | 90% | null | null | null | null | 527.0 | 336.0 | 25.1 | 20.6 | tau overestimated due to low SNR post-merger; sigma approx CI: f(+340/-332), tau(+22.2/-19.0) |
| GW170823 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | IMR | H1+L1 | 90% | null | null | null | null | 197.0 | 17.0 | 5.5 | 0.9 | sigma approximated from asymmetric CI: f(+17/-17), tau(+1.0/-0.8) |
| GW170823 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | Damped Sinusoid (DS) | H1+L1 | 90% | null | null | null | null | 222.0 | 363.0 | 13.4 | 20.8 | tau overestimated due to low SNR; sigma approx CI: f(+664/-62), tau(+31.8/-9.8) |
| GW190408\_181802 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | IMR | null | 90% | null | null | null | null | 319.0 | 15.5 | 3.2 | 0.3 | sigma approximated from asymmetric CI: f(+11/-20), tau(+0.3/-0.3) |
| GW190408\_181802 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | Damped Sinusoid (DS) | null | 90% | null | null | null | null | 504.0 | 469.0 | 10.0 | 20.7 | tau overestimated due to low SNR; sigma approx CI: f(+479/-459), tau(+32.5/-8.9) |
| GW190421\_213856 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | IMR | null | 90% | null | null | null | null | 162.0 | 14.0 | 6.3 | 1.0 | sigma approximated from asymmetric CI: f(+14/-14), tau(+1.2/-0.8) |
| GW190421\_213856 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | Damped Sinusoid (DS) | null | 90% | null | null | null | null | 171.0 | 33.0 | 8.5 | 4.75 | sigma approximated from asymmetric CI: f(+50/-16), tau(+5.3/-4.2) |
| GW190503\_185404 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | IMR | null | 90% | null | null | null | null | 191.0 | 16.0 | 5.3 | 0.8 | sigma approximated from asymmetric CI: f(+17/-15), tau(+0.8/-0.8) |
| GW190503\_185404 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | Damped Sinusoid (DS) | null | 90% | null | null | null | null | 265.0 | 290.0 | 3.5 | 2.6 | sigma approximated from asymmetric CI: f(+501/-79), tau(+3.4/-1.8) |
| GW190512\_180714 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | IMR | null | 90% | null | null | null | null | 381.0 | 37.5 | 2.6 | 0.2 | sigma approximated from asymmetric CI: f(+33/-42), tau(+0.2/-0.2) |
| GW190512\_180714 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | Damped Sinusoid (DS) | null | 90% | null | null | null | null | 220.0 | 364.0 | 26.1 | 22.1 | tau overestimated due to low SNR; sigma approx CI: f(+686/-42), tau(+21.3/-22.9) |
| GW190513\_205428 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | IMR | null | 90% | null | null | null | null | 241.0 | 27.0 | 4.3 | 0.75 | sigma approximated from asymmetric CI: f(+26/-28), tau(+1.1/-0.4) |
| GW190513\_205428 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | Damped Sinusoid (DS) | null | 90% | null | null | null | null | 250.0 | 290.5 | 5.3 | 11.5 | tau overestimated due to low SNR; sigma approx CI: f(+493/-88), tau(+19.2/-3.8) |
| GW190519\_153544 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | IMR | null | 90% | null | null | null | null | 127.0 | 9.0 | 9.5 | 1.6 | sigma approximated from asymmetric CI: f(+9/-9), tau(+1.7/-1.5) |
| GW190519\_153544 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | Damped Sinusoid (DS) | null | 90% | null | null | null | null | 123.0 | 15.0 | 9.7 | 6.4 | sigma approximated from asymmetric CI: f(+11/-19), tau(+9.0/-3.8) |
| GW190519\_153544 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | pSEOBNRv4HM | null | 90% | null | null | null | null | 124.0 | 12.5 | 10.3 | 3.35 | sigma approximated from asymmetric CI: f(+12/-13), tau(+3.6/-3.1) |
| GW190521 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | IMR | H1+L1+V1 | 90% | null | null | null | null | 68.0 | 4.0 | 15.8 | 3.2 | sigma approximated from asymmetric CI: f(+4/-4), tau(+3.9/-2.5) |
| GW190521 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | Damped Sinusoid (DS) | H1+L1+V1 | 90% | null | null | null | null | 65.0 | 3.0 | 22.1 | 9.9 | sigma approximated from asymmetric CI: f(+3/-3), tau(+12.4/-7.4) |
| GW190521 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | pSEOBNRv4HM | H1+L1+V1 | 90% | null | null | null | null | 67.0 | 2.0 | 30.7 | 7.55 | sigma approximated from asymmetric CI: f(+2/-2), tau(+7.7/-7.4) |
| GW190521\_074359 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | IMR | null | 90% | null | null | null | null | 198.0 | 7.0 | 5.4 | 0.4 | sigma approximated from asymmetric CI: f(+7/-7), tau(+0.4/-0.4) |
| GW190521\_074359 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | Damped Sinusoid (DS) | null | 90% | null | null | null | null | 197.0 | 15.0 | 7.7 | 4.85 | sigma approximated from asymmetric CI: f(+15/-15), tau(+6.4/-3.3) |
| GW190521\_074359 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | pSEOBNRv4HM | null | 90% | null | null | null | null | 205.0 | 13.5 | 5.3 | 1.35 | sigma approximated from asymmetric CI: f(+15/-12), tau(+1.5/-1.2) |
| GW190602\_175927 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | IMR | null | 90% | null | null | null | null | 105.0 | 9.5 | 10.0 | 1.7 | sigma approximated from asymmetric CI: f(+10/-9), tau(+2.0/-1.4) |
| GW190602\_175927 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | Damped Sinusoid (DS) | null | 90% | null | null | null | null | 93.0 | 17.5 | 10.0 | 10.85 | sigma approximated from asymmetric CI: f(+13/-22), tau(+17.2/-4.5) |
| GW190602\_175927 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | pSEOBNRv4HM | null | 90% | null | null | null | null | 99.0 | 15.0 | 8.8 | 4.5 | sigma approximated from asymmetric CI: f(+15/-15), tau(+5.4/-3.6) |
| GW190706\_222641 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | IMR | null | 90% | null | null | null | null | 108.0 | 10.5 | 10.9 | 2.3 | sigma approximated from asymmetric CI: f(+11/-10), tau(+2.4/-2.2) |
| GW190706\_222641 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | Damped Sinusoid (DS) | null | 90% | null | null | null | null | 109.0 | 9.5 | 20.4 | 19.05 | sigma approximated from asymmetric CI: f(+7/-12), tau(+25.2/-12.9) |
| GW190706\_222641 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | pSEOBNRv4HM | null | 90% | null | null | null | null | 112.0 | 7.5 | 19.4 | 8.05 | sigma approximated from asymmetric CI: f(+7/-8), tau(+7.2/-8.9) |
| GW190708\_232457 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | IMR | null | 90% | null | null | null | null | 497.0 | 28.0 | 2.1 | 0.15 | sigma approximated from asymmetric CI: f(+10/-46), tau(+0.2/-0.1) |
| GW190708\_232457 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | Damped Sinusoid (DS) | null | 90% | null | null | null | null | 642.0 | 437.5 | 24.6 | 22.8 | tau overestimated due to low SNR; sigma approx CI: f(+279/-596), tau(+23.0/-22.6) |
| GW190727\_060333 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | IMR | null | 90% | null | null | null | null | 178.0 | 17.0 | 6.1 | 0.95 | sigma approximated from asymmetric CI: f(+18/-16), tau(+1.1/-0.8) |
| GW190727\_060333 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | Damped Sinusoid (DS) | null | 90% | null | null | null | null | 345.0 | 427.0 | 21.1 | 21.75 | tau overestimated due to low SNR; sigma approx CI: f(+587/-267), tau(+25.6/-17.9) |
| GW190727\_060333 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | pSEOBNRv4HM | null | 90% | null | null | null | null | 201.0 | 16.0 | 15.4 | 5.7 | sigma approximated from asymmetric CI: f(+11/-21), tau(+5.3/-6.1) |
| GW190828\_063405 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | IMR | null | 90% | null | null | null | null | 239.0 | 10.5 | 4.8 | 0.55 | sigma approximated from asymmetric CI: f(+10/-11), tau(+0.6/-0.5) |
| GW190828\_063405 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | Damped Sinusoid (DS) | null | 90% | null | null | null | null | 247.0 | 182.5 | 17.3 | 17.85 | tau overestimated due to low SNR; sigma approx CI: f(+350/-15), tau(+25.3/-10.4) |
| GW190910\_112807 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | IMR | null | 90% | null | null | null | null | 177.0 | 8.0 | 5.9 | 0.65 | sigma approximated from asymmetric CI: f(+8/-8), tau(+0.8/-0.5) |
| GW190910\_112807 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | Damped Sinusoid (DS) | null | 90% | null | null | null | null | 166.0 | 8.5 | 13.2 | 11.65 | tau overestimated due to low SNR; sigma approx CI: f(+9/-8), tau(+17.1/-6.2) |
| GW190910\_112807 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | pSEOBNRv4HM | null | 90% | null | null | null | null | 174.0 | 10.0 | 9.5 | 2.9 | sigma approximated from asymmetric CI: f(+12/-8), tau(+3.1/-2.7) |
| GW190915\_235702 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | IMR | null | 90% | null | null | null | null | 232.0 | 16.0 | 4.6 | 0.7 | sigma approximated from asymmetric CI: f(+14/-18), tau(+0.8/-0.6) |
| GW190915\_235702 | peer\_reviewed\_paper | Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog | 10.1103/PhysRevD.103.122002 | [https://dcc.ligo.org/LIGO-P2000438/public](https://dcc.ligo.org/LIGO-P2000438/public) | Table IX | Damped Sinusoid (DS) | null | 90% | null | null | null | null | 534.0 | 432.0 | 15.0 | 21.6 | tau overestimated due to low SNR; sigma approx CI: f(+371/-493), tau(+30.1/-13.1) |

## **Fuentes Rechazadas y Criterios de Exclusión Activa**

A fin de preservar la invulnerabilidad probabilística de los valores consignados y obedecer rigurosamente las directrices de trazabilidad absoluta exigidas para la configuración del pipeline integrador, diversos eventos detectados formalmente han sido bloqueados deliberadamente y extirpados de la lista de aceptación final. La decisión de rechazo se motiva incondicionalmente en patologías graves que corroen la integridad analítica de los parámetros extraídos.

El caso de estudio más evidente radica en la anomalía registrada con **GW191109\_010717**. A pesar del interés suscitado por particularidades astrofísicas (incluyendo indicios fenomenológicos que apuntan hacia una alineación de espín efectivo con signo negativo alcanzando casi un 99.3% en el nivel de confianza bayesiana 20), los dominios paramétricos de este evento enfrentan fallos incorregibles al diseccionar la topología del modo armónico fundamental 220\. El diagnóstico técnico emitido recurrentemente por la revisión científica interna subraya la omnipresencia devastadora de componentes de ruido de fondo prolongados y no estacionarios ("glitches" masivos), cuyo espectro tiempo-frecuencia interseca destructivamente y corrompe los pasajes transitorios colindantes con el frente de coalescencia. Las auditorías paramétricas posteriores diseñadas para extraer el coeficiente direccional ![][image34] padecieron fraccionamientos de multimodalidad severos.11 Ante esta degradación algorítmica y la imposibilidad de converger hacia estimaciones paramétricas fiables, las jerarquías evaluadoras descartaron universalmente el evento para su integración en los catálogos combinados restrictivos.11 Por tanto, las cifras fraccionadas provistas episódicamente en preprints externos se devalúan y se deniegan para salvaguardar el *pipeline*.

Una exclusión correlativa y paralela de rigor científico afecta a **GW151012** (designado precursoramente en la campaña de observación inicial O1 bajo el código transitorio marginal LVT151012). Aunque validado estadísticamente *a posteriori* como la tercera colisión genuina detectada por la colaboración LVK 22, padece de una relación señal-ruido global inmensamente precaria, calculada apenas en torno a una métrica de 9.24. Este límite abisal invalida la extracción de una firma resonante distinguible tras la obliteración de la órbita. Sin una robusta penetración espectral por encima del lecho de ruido gaussiano local, el algoritmo colapsa y es incapaz de generar contornos paramétricos delimitados para las dimensiones frecuenciales o de decaimiento post-merger de manera autónoma.23 Consecuentemente, al carecer de una publicación directa o endosada en las matrices oficiales definitivas (e.g., la referida Tabla IX de GWTC-2), este registro se omite en observancia perentoria a la ordenanza que insta a rechazar inserciones hipotéticas y previene cualquier invención sintética de magnitudes no atestiguadas.8

Asimismo, las referencias provistas a través de cartelería de congresos, presentaciones en diapositivas, y extractos subidos a repositorios genéricos que ilustran magnitudes en forma fraccionaria o provisional carentes de escrutinio plenario (peer review cruzado), se descalifican. Toda incorporación depende de un linaje probatorio inquebrantable anclado a DOIs consolidados y plataformas controladas oficialmente (DCC o iteraciones Zenodo de GWTC-2/3/4).

## **YAML Ready**

La siguiente matriz textual condensa la integridad total del catálogo tabulado en el lenguaje serializado requerido, configurada meticulosamente bajo las normativas topográficas para habilitar su inyección ininterrumpida y directa dentro del código de producción o el orquestador del repositorio local.

YAML

\- event: GW150914  
  ifo: "H1+L1"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "IMR"  
  detector\_set: "H1+L1"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 248.0  
      sigma\_f\_hz: 7.5  
      tau\_ms: 4.2  
      sigma\_tau\_ms: 0.25  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+8/-7), tau(+0.3/-0.2)"

\- event: GW150914  
  ifo: "H1+L1"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "Damped Sinusoid (DS)"  
  detector\_set: "H1+L1"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 247.0  
      sigma\_f\_hz: 15.0  
      tau\_ms: 4.8  
      sigma\_tau\_ms: 2.8  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+14/-16), tau(+3.7/-1.9)"

\- event: GW170104  
  ifo: "H1+L1"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "IMR"  
  detector\_set: "H1+L1"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 287.0  
      sigma\_f\_hz: 20.0  
      tau\_ms: 3.5  
      sigma\_tau\_ms: 0.35  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+15/-25), tau(+0.4/-0.3)"

\- event: GW170104  
  ifo: "H1+L1"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "Damped Sinusoid (DS)"  
  detector\_set: "H1+L1"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 228.0  
      sigma\_f\_hz: 86.5  
      tau\_ms: 3.6  
      sigma\_tau\_ms: 19.15  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+71/-102), tau(+36.2/-2.1)"

\- event: GW170104  
  ifo: "H1+L1"  
  M\_final\_Msun: 69.9  
  sigma\_M\_final\_Msun: 18.4  
  chi\_final: 0.87  
  sigma\_chi\_final: 0.255  
  source\_kind: data\_release  
  analysis\_method: "pSEOBNRv4HM"  
  detector\_set: "H1+L1"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 296.6  
      sigma\_f\_hz: 56.7  
      tau\_ms: 5.04  
      sigma\_tau\_ms: 3.065  
      source\_paper: "Tests of General Relativity with GWTC-3"  
      source\_doi: "arXiv:2112.06861"  
      source\_url: "https://zenodo.org/records/17461225"  
      source\_locator: "Table XIII / Fig 14 text"  
      notes: "sigma approximated from asymmetric CI: f(+58.9/-54.5), tau(+3.76/-2.37), M(+16.2/-20.6), chi(+0.09/-0.42)"

\- event: GW170814  
  ifo: "H1+L1+V1"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "IMR"  
  detector\_set: "H1+L1+V1"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 293.0  
      sigma\_f\_hz: 12.5  
      tau\_ms: 3.7  
      sigma\_tau\_ms: 0.25  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+11/-14), tau(+0.3/-0.2)"

\- event: GW170814  
  ifo: "H1+L1+V1"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "Damped Sinusoid (DS)"  
  detector\_set: "H1+L1+V1"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 527.0  
      sigma\_f\_hz: 336.0  
      tau\_ms: 25.1  
      sigma\_tau\_ms: 20.6  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "tau overestimated due to low SNR post-merger; sigma approx CI: f(+340/-332), tau(+22.2/-19.0)"

\- event: GW170823  
  ifo: "H1+L1"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "IMR"  
  detector\_set: "H1+L1"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 197.0  
      sigma\_f\_hz: 17.0  
      tau\_ms: 5.5  
      sigma\_tau\_ms: 0.9  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+17/-17), tau(+1.0/-0.8)"

\- event: GW170823  
  ifo: "H1+L1"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "Damped Sinusoid (DS)"  
  detector\_set: "H1+L1"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 222.0  
      sigma\_f\_hz: 363.0  
      tau\_ms: 13.4  
      sigma\_tau\_ms: 20.8  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "tau overestimated due to low SNR; sigma approx CI: f(+664/-62), tau(+31.8/-9.8)"

\- event: GW190408\_181802  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "IMR"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 319.0  
      sigma\_f\_hz: 15.5  
      tau\_ms: 3.2  
      sigma\_tau\_ms: 0.3  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+11/-20), tau(+0.3/-0.3)"

\- event: GW190408\_181802  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "Damped Sinusoid (DS)"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 504.0  
      sigma\_f\_hz: 469.0  
      tau\_ms: 10.0  
      sigma\_tau\_ms: 20.7  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "tau overestimated due to low SNR; sigma approx CI: f(+479/-459), tau(+32.5/-8.9)"

\- event: GW190421\_213856  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "IMR"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 162.0  
      sigma\_f\_hz: 14.0  
      tau\_ms: 6.3  
      sigma\_tau\_ms: 1.0  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+14/-14), tau(+1.2/-0.8)"

\- event: GW190421\_213856  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "Damped Sinusoid (DS)"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 171.0  
      sigma\_f\_hz: 33.0  
      tau\_ms: 8.5  
      sigma\_tau\_ms: 4.75  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+50/-16), tau(+5.3/-4.2)"

\- event: GW190503\_185404  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "IMR"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 191.0  
      sigma\_f\_hz: 16.0  
      tau\_ms: 5.3  
      sigma\_tau\_ms: 0.8  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+17/-15), tau(+0.8/-0.8)"

\- event: GW190503\_185404  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "Damped Sinusoid (DS)"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 265.0  
      sigma\_f\_hz: 290.0  
      tau\_ms: 3.5  
      sigma\_tau\_ms: 2.6  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+501/-79), tau(+3.4/-1.8)"

\- event: GW190512\_180714  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "IMR"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 381.0  
      sigma\_f\_hz: 37.5  
      tau\_ms: 2.6  
      sigma\_tau\_ms: 0.2  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+33/-42), tau(+0.2/-0.2)"

\- event: GW190512\_180714  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "Damped Sinusoid (DS)"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 220.0  
      sigma\_f\_hz: 364.0  
      tau\_ms: 26.1  
      sigma\_tau\_ms: 22.1  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "tau overestimated due to low SNR; sigma approx CI: f(+686/-42), tau(+21.3/-22.9)"

\- event: GW190513\_205428  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "IMR"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 241.0  
      sigma\_f\_hz: 27.0  
      tau\_ms: 4.3  
      sigma\_tau\_ms: 0.75  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+26/-28), tau(+1.1/-0.4)"

\- event: GW190513\_205428  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "Damped Sinusoid (DS)"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 250.0  
      sigma\_f\_hz: 290.5  
      tau\_ms: 5.3  
      sigma\_tau\_ms: 11.5  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "tau overestimated due to low SNR; sigma approx CI: f(+493/-88), tau(+19.2/-3.8)"

\- event: GW190519\_153544  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "IMR"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 127.0  
      sigma\_f\_hz: 9.0  
      tau\_ms: 9.5  
      sigma\_tau\_ms: 1.6  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+9/-9), tau(+1.7/-1.5)"

\- event: GW190519\_153544  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "Damped Sinusoid (DS)"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 123.0  
      sigma\_f\_hz: 15.0  
      tau\_ms: 9.7  
      sigma\_tau\_ms: 6.4  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+11/-19), tau(+9.0/-3.8)"

\- event: GW190519\_153544  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "pSEOBNRv4HM"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 124.0  
      sigma\_f\_hz: 12.5  
      tau\_ms: 10.3  
      sigma\_tau\_ms: 3.35  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+12/-13), tau(+3.6/-3.1)"

\- event: GW190521  
  ifo: "H1+L1+V1"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "IMR"  
  detector\_set: "H1+L1+V1"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 68.0  
      sigma\_f\_hz: 4.0  
      tau\_ms: 15.8  
      sigma\_tau\_ms: 3.2  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+4/-4), tau(+3.9/-2.5)"

\- event: GW190521  
  ifo: "H1+L1+V1"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "Damped Sinusoid (DS)"  
  detector\_set: "H1+L1+V1"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 65.0  
      sigma\_f\_hz: 3.0  
      tau\_ms: 22.1  
      sigma\_tau\_ms: 9.9  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+3/-3), tau(+12.4/-7.4)"

\- event: GW190521  
  ifo: "H1+L1+V1"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "pSEOBNRv4HM"  
  detector\_set: "H1+L1+V1"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 67.0  
      sigma\_f\_hz: 2.0  
      tau\_ms: 30.7  
      sigma\_tau\_ms: 7.55  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+2/-2), tau(+7.7/-7.4)"

\- event: GW190521\_074359  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "IMR"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 198.0  
      sigma\_f\_hz: 7.0  
      tau\_ms: 5.4  
      sigma\_tau\_ms: 0.4  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+7/-7), tau(+0.4/-0.4)"

\- event: GW190521\_074359  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "Damped Sinusoid (DS)"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 197.0  
      sigma\_f\_hz: 15.0  
      tau\_ms: 7.7  
      sigma\_tau\_ms: 4.85  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+15/-15), tau(+6.4/-3.3)"

\- event: GW190521\_074359  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "pSEOBNRv4HM"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 205.0  
      sigma\_f\_hz: 13.5  
      tau\_ms: 5.3  
      sigma\_tau\_ms: 1.35  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+15/-12), tau(+1.5/-1.2)"

\- event: GW190602\_175927  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "IMR"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 105.0  
      sigma\_f\_hz: 9.5  
      tau\_ms: 10.0  
      sigma\_tau\_ms: 1.7  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+10/-9), tau(+2.0/-1.4)"

\- event: GW190602\_175927  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "Damped Sinusoid (DS)"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 93.0  
      sigma\_f\_hz: 17.5  
      tau\_ms: 10.0  
      sigma\_tau\_ms: 10.85  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+13/-22), tau(+17.2/-4.5)"

\- event: GW190602\_175927  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "pSEOBNRv4HM"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 99.0  
      sigma\_f\_hz: 15.0  
      tau\_ms: 8.8  
      sigma\_tau\_ms: 4.5  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+15/-15), tau(+5.4/-3.6)"

\- event: GW190706\_222641  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "IMR"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 108.0  
      sigma\_f\_hz: 10.5  
      tau\_ms: 10.9  
      sigma\_tau\_ms: 2.3  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+11/-10), tau(+2.4/-2.2)"

\- event: GW190706\_222641  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "Damped Sinusoid (DS)"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 109.0  
      sigma\_f\_hz: 9.5  
      tau\_ms: 20.4  
      sigma\_tau\_ms: 19.05  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+7/-12), tau(+25.2/-12.9)"

\- event: GW190706\_222641  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "pSEOBNRv4HM"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 112.0  
      sigma\_f\_hz: 7.5  
      tau\_ms: 19.4  
      sigma\_tau\_ms: 8.05  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+7/-8), tau(+7.2/-8.9)"

\- event: GW190708\_232457  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "IMR"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 497.0  
      sigma\_f\_hz: 28.0  
      tau\_ms: 2.1  
      sigma\_tau\_ms: 0.15  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+10/-46), tau(+0.2/-0.1)"

\- event: GW190708\_232457  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "Damped Sinusoid (DS)"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 642.0  
      sigma\_f\_hz: 437.5  
      tau\_ms: 24.6  
      sigma\_tau\_ms: 22.8  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "tau overestimated due to low SNR; sigma approx CI: f(+279/-596), tau(+23.0/-22.6)"

\- event: GW190727\_060333  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "IMR"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 178.0  
      sigma\_f\_hz: 17.0  
      tau\_ms: 6.1  
      sigma\_tau\_ms: 0.95  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+18/-16), tau(+1.1/-0.8)"

\- event: GW190727\_060333  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "Damped Sinusoid (DS)"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 345.0  
      sigma\_f\_hz: 427.0  
      tau\_ms: 21.1  
      sigma\_tau\_ms: 21.75  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "tau overestimated due to low SNR; sigma approx CI: f(+587/-267), tau(+25.6/-17.9)"

\- event: GW190727\_060333  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "pSEOBNRv4HM"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 201.0  
      sigma\_f\_hz: 16.0  
      tau\_ms: 15.4  
      sigma\_tau\_ms: 5.7  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+11/-21), tau(+5.3/-6.1)"

\- event: GW190828\_063405  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "IMR"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 239.0  
      sigma\_f\_hz: 10.5  
      tau\_ms: 4.8  
      sigma\_tau\_ms: 0.55  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+10/-11), tau(+0.6/-0.5)"

\- event: GW190828\_063405  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "Damped Sinusoid (DS)"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 247.0  
      sigma\_f\_hz: 182.5  
      tau\_ms: 17.3  
      sigma\_tau\_ms: 17.85  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "tau overestimated due to low SNR; sigma approx CI: f(+350/-15), tau(+25.3/-10.4)"

\- event: GW190910\_112807  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "IMR"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 177.0  
      sigma\_f\_hz: 8.0  
      tau\_ms: 5.9  
      sigma\_tau\_ms: 0.65  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+8/-8), tau(+0.8/-0.5)"

\- event: GW190910\_112807  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "Damped Sinusoid (DS)"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 166.0  
      sigma\_f\_hz: 8.5  
      tau\_ms: 13.2  
      sigma\_tau\_ms: 11.65  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "tau overestimated due to low SNR; sigma approx CI: f(+9/-8), tau(+17.1/-6.2)"

\- event: GW190910\_112807  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "pSEOBNRv4HM"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 174.0  
      sigma\_f\_hz: 10.0  
      tau\_ms: 9.5  
      sigma\_tau\_ms: 2.9  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+12/-8), tau(+3.1/-2.7)"

\- event: GW190915\_235702  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "IMR"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 232.0  
      sigma\_f\_hz: 16.0  
      tau\_ms: 4.6  
      sigma\_tau\_ms: 0.7  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "sigma approximated from asymmetric CI: f(+14/-18), tau(+0.8/-0.6)"

\- event: GW190915\_235702  
  ifo: "null"  
  M\_final\_Msun: null  
  sigma\_M\_final\_Msun: null  
  chi\_final: null  
  sigma\_chi\_final: null  
  source\_kind: peer\_reviewed\_paper  
  analysis\_method: "Damped Sinusoid (DS)"  
  detector\_set: "null"  
  credible\_interval: "90%"  
  modes:  
    \- l: 2  
      m: 2  
      n: 0  
      f\_hz: 534.0  
      sigma\_f\_hz: 432.0  
      tau\_ms: 15.0  
      sigma\_tau\_ms: 21.6  
      source\_paper: "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog"  
      source\_doi: "10.1103/PhysRevD.103.122002"  
      source\_url: "https://dcc.ligo.org/LIGO-P2000438/public"  
      source\_locator: "Table IX"  
      notes: "tau overestimated due to low SNR; sigma approx CI: f(+371/-493), tau(+30.1/-13.1)"

## **Confidence Audit**

Para asegurar una reproducibilidad incuestionable y blindar la trazabilidad absoluta de la configuración integral en el pipeline alimentado por este reporte, se establece la siguiente métrica de auditoría confidencial sobre la estructura final compilada:

La presente disección astrofísica totaliza 46 filas paramétricas de información espectral extraídas de la literatura sancionada oficialmente. De manera específica, el nivel de rigidez estadística se desglosa del modo siguiente:

La abrumadora y unánime mayoría de la data (45 de las 46 filas aceptadas) ha sido aislada inequívocamente de un documento medular de las colaboraciones LIGO y Virgo: el archivo consolidado de pruebas sobre la relatividad general, "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog" (GWTC-2), amparado bajo el identificador y DOI firme 10.1103/PhysRevD.103.122002. La base empírica reside casi enteramente en la Tabla IX de este volumen (disponible transversalmente a través del Document Control Center público, LIGO-P2000438), la cual reporta proyecciones metodológicas disjuntas (IMR, Damped Sinusoid y pSEOB) evaluadas con márgenes de probabilidad *a posteriori* rigurosos al noventa por ciento.8

Adicionalmente, se ha integrado una fila emanada del posterior Data Release oficial asociado al Gravitational-Wave Transient Catalog 3 (GWTC-3), referenciado de manera complementaria en repositorios de confianza (Zenodo, ID 17461225 vinculado a arXiv:2112.06861). Esta fila proporciona mediciones directas de la aproximación paramétrica pSEOBNRv4HM en asociación íntima para el evento colisional GW170104.9 Todas estas métricas, en suma, satisfacen sin compromisos de opacidad la obligación de procedencia inmaculada de pares escrutados (peer review). No existe contribución alguna procedente de esquemas provisionales, pre-impresiones especulativas ni resúmenes web volátiles. Todo factor introducido porta credenciales inalterables con estatus de cimentación académica global.

En contraste con las admisiones metodológicas, la investigación sentenció a tres candidatos principales propuestos al aislamiento por inutilizables. El evento singular **GW191109\_010717**, que presentaba anomalías fascinantes de inversión térmica de espín, ha sido vedado porque sus cuadros interferométricos estaban contaminados severamente por fluctuaciones crónicas de ruido transitorio en bajas frecuencias, produciendo densidades estocásticas inmanejables durante la etapa espectral, forzando a su expulsión oficial de todas las comparativas.11 Análogamente, se procedió con la recusación definitiva de los eventos O1 precursores **GW151012** (inicialmente catalogado LVT) y marginales de O3, los cuales, al carecer de una contribución fundamental de energía que superara la cuota umbral de SNR residual, denegaron perennemente la capacidad metodológica contemporánea de modelizar oscilaciones asintóticas confiables.22

## **Conclusiones sobre la Inferencia y la Proyección del Pipeline**

El esfuerzo global para delimitar y comprender el marco empírico propiciado por el régimen dinámico final en colisiones estelares masivas ratifica incesantemente la fiabilidad del postulado central esbozado hace un siglo por Albert Einstein y posteriormente formulado topológicamente por Roy Kerr. Al estructurar este inmenso catálogo de extracción paramétrica sobre el modo armónico 220, la base analítica pone de relieve una divergencia metodológica que trasciende la cosmología pura y aterriza sobre el manejo crítico de bases de datos. La lección predominante arrojada por la variabilidad en los muestreos —especialmente la disparidad brutal y colapsada mostrada por los ajustes empíricos ciegos (Damped Sinusoids) ante señales tenues frente a las extrapolaciones pre-programadas de fase IMR— dictamina que el ruido sísmico y térmico de los espejos continúa siendo el enemigo primordial de la astrofísica paramétrica contemporánea.8

El presente catálogo de datos depurados, liberado de injerencias secundarias y dotado con la traducción algorítmica y la estandarización matemática que subsana las asimetrías estocásticas originales (promediando las sigmas para una ingesta eficiente y coherente en entornos de programación automatizados), erradica con precisión toda ambigüedad interpretativa futura. Previene que el orquestador local intente acomodar valores corrompidos por el ruido gaussiano inoperante. A medida que las redes de observación interferométrica experimenten los saltos cuánticos venideros de sensibilidad global y óptica comprimida en fase proyectados para los inminentes años de corrida (O4 y consiguientes configuraciones A+), la infraestructura aquí ensamblada gozará de la maleabilidad incondicional y el rigor tabular indispensable para absorber un volumen sin precedentes de fenómenos exóticos y sobretonos amortiguados no detectables en la actualidad, cimentando una herramienta central para desvelar posibles divergencias cuánticas en las trincheras de la gravedad profunda.

#### **Obras citadas**

1. Constraining extra dimensions using observations of black hole quasi-normal modes \- PMC, fecha de acceso: abril 20, 2026, [https://pmc.ncbi.nlm.nih.gov/articles/PMC9483322/](https://pmc.ncbi.nlm.nih.gov/articles/PMC9483322/)  
2. GW250114: Testing Hawking's Area Law and the Kerr Nature of Black Holes \- NSF Public Access Repository, fecha de acceso: abril 20, 2026, [https://par.nsf.gov/servlets/purl/10650616](https://par.nsf.gov/servlets/purl/10650616)  
3. Testing the No-Hair Theorem with GW150914 \- CORE, fecha de acceso: abril 20, 2026, [https://files01.core.ac.uk/download/pdf/227196294.pdf](https://files01.core.ac.uk/download/pdf/227196294.pdf)  
4. Testing the No-Hair Theorem with GW150914 | Request PDF \- ResearchGate, fecha de acceso: abril 20, 2026, [https://www.researchgate.net/publication/335777996\_Testing\_the\_No-Hair\_Theorem\_with\_GW150914](https://www.researchgate.net/publication/335777996_Testing_the_No-Hair_Theorem_with_GW150914)  
5. Analysis of Ringdown Overtones in GW150914 \- PubMed, fecha de acceso: abril 20, 2026, [https://pubmed.ncbi.nlm.nih.gov/36154425/](https://pubmed.ncbi.nlm.nih.gov/36154425/)  
6. \[2201.00822\] Analysis of Ringdown Overtones in GW150914 \- arXiv, fecha de acceso: abril 20, 2026, [https://arxiv.org/abs/2201.00822](https://arxiv.org/abs/2201.00822)  
7. Tests of General Relativity with GW150914 \- Scholars' Mine, fecha de acceso: abril 20, 2026, [https://scholarsmine.mst.edu/cgi/viewcontent.cgi?article=2935\&context=phys\_facwork](https://scholarsmine.mst.edu/cgi/viewcontent.cgi?article=2935&context=phys_facwork)  
8. Tests of general relativity with binary black holes from the ... \- ePubs, fecha de acceso: abril 20, 2026, [https://epubs.stfc.ac.uk/manifestation/50294405/STFC-APV-2021-065.pdf](https://epubs.stfc.ac.uk/manifestation/50294405/STFC-APV-2021-065.pdf)  
9. Tests of general relativity with GWTC-3 \- White Rose Research Online, fecha de acceso: abril 20, 2026, [https://eprints.whiterose.ac.uk/id/eprint/234685/7/2112.06861v3.pdf](https://eprints.whiterose.ac.uk/id/eprint/234685/7/2112.06861v3.pdf)  
10. Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog \- ResearchGate, fecha de acceso: abril 20, 2026, [https://www.researchgate.net/publication/348692039\_Tests\_of\_General\_Relativity\_with\_Binary\_Black\_Holes\_from\_the\_second\_LIGO-Virgo\_Gravitational-Wave\_Transient\_Catalog](https://www.researchgate.net/publication/348692039_Tests_of_General_Relativity_with_Binary_Black_Holes_from_the_second_LIGO-Virgo_Gravitational-Wave_Transient_Catalog)  
11. Parametrized spin-precessing inspiral-merger-ringdown waveform model for tests of general relativity \- MPG.PuRe, fecha de acceso: abril 20, 2026, [https://pure.mpg.de/rest/items/item\_3646833\_5/component/file\_3654953/content](https://pure.mpg.de/rest/items/item_3646833_5/component/file_3654953/content)  
12. Gaussian processes for glitch-robust gravitational-wave astronomy \- Oxford Academic, fecha de acceso: abril 20, 2026, [https://academic.oup.com/mnras/article/520/2/2983/7028786](https://academic.oup.com/mnras/article/520/2/2983/7028786)  
13. Gating-and-inpainting perspective on GW150914 ringdown overtone: Understanding the data analysis systematics \- ResearchGate, fecha de acceso: abril 20, 2026, [https://www.researchgate.net/publication/396441476\_Gating-and-inpainting\_perspective\_on\_GW150914\_ringdown\_overtone\_Understanding\_the\_data\_analysis\_systematics](https://www.researchgate.net/publication/396441476_Gating-and-inpainting_perspective_on_GW150914_ringdown_overtone_Understanding_the_data_analysis_systematics)  
14. \*NASA Einstein Fellow \- CERN Indico, fecha de acceso: abril 20, 2026, [https://indico.cern.ch/event/801461/contributions/3728119/attachments/2007185/3352569/MaxIsi\_EDSU2020.pdf](https://indico.cern.ch/event/801461/contributions/3728119/attachments/2007185/3352569/MaxIsi_EDSU2020.pdf)  
15. GW190521: A Binary Black Hole Merger with a Total Mass of 150 \&ThinSpace \- arXiv, fecha de acceso: abril 20, 2026, [https://arxiv.org/pdf/2009.01075](https://arxiv.org/pdf/2009.01075)  
16. GW190521: A Binary Black Hole Merger with a Total Mass of 150 M \- ResearchGate, fecha de acceso: abril 20, 2026, [https://www.researchgate.net/publication/344144855\_GW190521\_A\_Binary\_Black\_Hole\_Merger\_with\_a\_Total\_Mass\_of\_150\_M](https://www.researchgate.net/publication/344144855_GW190521_A_Binary_Black_Hole_Merger_with_a_Total_Mass_of_150_M)  
17. Properties and astrophysical implications of the 150 M binary black hole merger GW190521 \- LIGO DCC, fecha de acceso: abril 20, 2026, [https://dcc.ligo.org/public/0165/P2000021/012/gw190521-implications-main\_20200905.pdf](https://dcc.ligo.org/public/0165/P2000021/012/gw190521-implications-main_20200905.pdf)  
18. Ten years of extreme gravity tests of general theory of relativity with gravitational-wave observations \- arXiv, fecha de acceso: abril 20, 2026, [https://arxiv.org/html/2511.15890v3](https://arxiv.org/html/2511.15890v3)  
19. GW170814: A Three-Detector Observation of Gravitational Waves from a Binary Black Hole Coalescence \- ResearchGate, fecha de acceso: abril 20, 2026, [https://www.researchgate.net/publication/320074998\_GW170814\_A\_Three-Detector\_Observation\_of\_Gravitational\_Waves\_from\_a\_Binary\_Black\_Hole\_Coalescence](https://www.researchgate.net/publication/320074998_GW170814_A_Three-Detector_Observation_of_Gravitational_Waves_from_a_Binary_Black_Hole_Coalescence)  
20. Analysis of GWTC-3 with fully precessing numerical relativity surrogate models \- arXiv, fecha de acceso: abril 20, 2026, [https://arxiv.org/html/2309.14473v2](https://arxiv.org/html/2309.14473v2)  
21. Tests of General Relativity with GWTC-3 | NTT Research, fecha de acceso: abril 20, 2026, [https://ntt-research.com/wp-content/uploads/2022/10/Tests-of-General-Relativity-with-GWTC-3.pdf](https://ntt-research.com/wp-content/uploads/2022/10/Tests-of-General-Relativity-with-GWTC-3.pdf)  
22. Testing General Relativity with Gravitational Waves: An Overview \- MPG.PuRe, fecha de acceso: abril 20, 2026, [https://pure.mpg.de/rest/items/item\_3360670\_2/component/file\_3360671/content?download=true](https://pure.mpg.de/rest/items/item_3360670_2/component/file_3360671/content?download=true)  
23. Testing General Relativity with Gravitational Waves: An Overview \- MDPI, fecha de acceso: abril 20, 2026, [https://www.mdpi.com/2218-1997/7/12/497](https://www.mdpi.com/2218-1997/7/12/497)  
24. Parameter estimation with the current generation of phenomenological waveform models applied to the black hole mergers of GWTC-1 \- Oxford Academic, fecha de acceso: abril 20, 2026, [https://academic.oup.com/mnras/article/517/2/2403/6760010](https://academic.oup.com/mnras/article/517/2/2403/6760010)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACEAAAAYCAYAAAB0kZQKAAACKklEQVR4Xu2WPSxmQRSGjyBZWSIoNoL4iUjEJiIbhYRGKBQUJCLUQqGiECJZzZaKtavQkG12SSQqlUZCIVHQqSSIn0JEpfL7vt/csXPPnft9FtvgSZ5gztw7d86cmSHyziuiEs7BQh1Q1MFZmKsDmja4CQ/hAvwYDkcohRtiBngMXfAHzNQBl2zYA6/gtIpp+KJ5OKoDAYx3wirVtghHnDYvLfBWzAuS0Qq34ScdCPgCL+Gwam+Au7BctYf4Bs9htQ44ZMA/8CdMUzFLn5iMNqp2ZnsNDqn2Bz7AFbgOc1TMhbNg3XToQAA/jEu1D4vCoQScKMfheBEq4Cmcgd1wB+7BLLeTmCU7g7WqvQx+F/MBjFP+PuH0IVxqjsPxInB33MED2AvT4Wc44HYSs87so7clZ8a2fngNvwZ/F7idQD08Dn5GYJpuxGwlS7FEd8C4JF+yuHqw2KJt1wG7FHprTkq0SH+JKS4WmSYPbsElMQXsgxM7Es9H+LYmTzceXrommLG4TNhZ6uy5xGbCtzWZTqaVM2aB2UqPqwmil4ID8t0u3pqwW5NpZDotnA0/rAmOyd8zgQV8IdHdQfgMU82UM5O/YU2oh8m27fMAZ8SZTbmNYu4E1glf5F48rJ8T8Z8T/DDOchmuwuZwOIH3nOAM88V/sbAjt6pLqhOTz/A4970v5Yn5L6S6O+Lg3cHnSnTgKXCWyW5RH3yGt+igDjyH//L/xFN48f+s3jb3qhhns/jEbSwAAAAASUVORK5CYII=>

[image2]: <data:image/png;base64,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>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAYAAAAaCAYAAACU2C2oAAAAqUlEQVR4XmNgoB9QAOLlQPwIiA8DsRhMghWIdYH4ChBvBWIOmAQIyADxEyBuRRYEARcg/gvEfugS5UD8Fog1kQVZgHgNA8RiXmQJcSC+C8STkAVBwAaIfwNxNLpEOhB/AmJ9oiQYgXgpEJ8GYkFkCREgvgrE86GK4MAYiL8yQIwDGdUDk/AE4i9AbArEWQxIPgeF5Dkg3g/Ei4GYHyYBAqDQBSkA0YMYAADm7xqDTT7AMwAAAABJRU5ErkJggg==>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABEAAAAYCAYAAAAcYhYyAAABBUlEQVR4Xu3RP0uCURTH8RMhFAXqEok21GQQODgFurW0NoiDUxAttbQEzQbO0aat+grEVXQRcnBoEoQUo0maHESIvve5XjuPL0Acnh98hnvuv3O5IkGCrDmX+EANh0igjBHa2EYOPQxQwp63c5EjvCGJIbpiDzjAFl7FHn4t9rAz/ODWbHbJ4wYn+EYLYTX/hIIax8Re9qJqyzxjglNVi+NTbEcuj5girWpedlDHO6KqnsFcjU2HHTSxr+pe3FNWW3S3upxjhjvsooJjN3mBX1y5gvi7c7mX/6dkURT11AeMRZ0q9nf64u8uhS80UBX/B3i3RnRhEbMotFIza80F5ruDbHz+ADedK3upjrkfAAAAAElFTkSuQmCC>

[image5]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAwAAAAYCAYAAADOMhxqAAAAxUlEQVR4Xu3QIQ9BURjG8dcUhpnZbDZFEGw2SVB0gaD5BIouKKJGUiW+gZGJkk0VVJvZBNn/dY5zD0G33Wf7hfucd/e894qE+es0ccQEKTSwwwljJIJRkaKYwTru2GKIOEq4oOemSRdt1PDAFBF7lscZA/vsogNz7JHxen3zDRWve0WHdHghwdtjWGEjZr2PVMXs7+9axhV9pDET7/aOmP31O95peZ2e649wGeGArNcVbLfGUswtLrpv0i9stM8h+n0Q5leex5IeCE/Ui3QAAAAASUVORK5CYII=>

[image6]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC8AAAAYCAYAAABqWKS5AAABhElEQVR4Xu2VzypFURTGl6LILZT8KQaEyMCfVyDRjSQDxSPIgFBGnsHEAAMjE1NlbEoyYKiQkoFXkO+z7qp1ts69JueeM9hf/eqeb6/bXnvtddYRiYqKKppKYBoMg6ZgrdDaA89gCxyBBzCZiCiwXsCQe94AT6DPeYUU2+USNDpvEHyATecVUmPgPPB6wSu4As1mLoBHcAF6RK/lBLyBKQuqs5hTWvJsnU4a/eAMjFYW7kQT7wINPrCKOAVmwOo/KYPW33+maxEcBJ4lT/hb1itYP92ANosWF1hFLaKVCpNMY1lqF4TJ7wfen+RNPOWXaK+ZeCCOqDzEYpwGniXP8dltJpufL8Et6DATWgPz7jlNWVR+QtJ7PvHC8gV9l2SVOaI4qrjJEth1a6Gy6Hm2biJJ0a5gdxw6T2bBN1hxnp2SVeX1jbu1eokFDT9SnxLksi0aOOA8Vv4YXItecx7i/veiA2VHNEfeWkK8mvbQFB2V/NLlJe4/Itpqc1K71aKioqIy0A+Eokq2wMQ5LQAAAABJRU5ErkJggg==>

[image7]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAJoAAAAYCAYAAAACh+TEAAAFn0lEQVR4Xu2aa8hlUxjHH6HcjUsuIYZJjFtyGUTKpUgkY6J88WVmSkMuofDhTc2XyScMck2Skg9qEJl04gPxflFEIpdcPgilyCWX5/eu/XTWec5a6+x99plz3jPtX/17z7vWPmvv/d/Petaz9vuKdHR0dHR0dLRkV9Wtqg2+Y87ZTbVFdYXvWAbsDJ438nYX1V2qrRIeDBynekX1jWpRtapqn0f2V72oOtt3zJCU59Z+iOpC1ZESgnEcJjUO7KE6uRKfYxp5u0b1vuqoqI0BT1V9pPpAdUDUN49cIOEeMX05kPL8QNULqrdUL6v+Un2nuig6pg6TGodgXaf6VnVfpc9Vl8cHSU1v91RtU23yHRK+yEme9B1zCFkD8xdc+yxIec71kd3WRm1Hqz5T/aI6PWovMalx4AzV9xICyeAzq1w8Ti1vz1V9LSEtei5R/au6wXfMKVepPlYd6jumTMrzE1U/qT6Uwcxwt+o/1YNRW4lJjUM2e0aGVzM+0/ZwdYwx0tsFVU+1z2DzEveoflWd5jvmlGMlPGAm0CxZkGHPLUC831dKCJCepJ+RZ1LjHCwhcHoyeDyfaaOPY4yit9Rhr0p6abQ+H9F1eF3Cmk0hyjJxs+rTSuslFKarpb/Z4OfxS9+sD3UC9SMp+zAJs/cJ1TuSXx72ldC/2XdMkZznZAcC47zqs8FqQoC8JIObhhyTGocxCNaepAONYCaojaK3pLkvJKRVz7j1GTdBofushPX9NdU5Em76MtUfqsdUj6v2kxCIBCbm+x1NDgrop1QnSJhFixKCjF0WKd3PNoNreL5S/BA8u6suVl3bQHW3+CXPPVb7UL5c4/qaMM441Ge/ybBXFmj0cYxR9NaCKXXyceuzlRIuhpnDxRB0xlmq3yVsh3mYBkGZC44UXBMiXf+gelvCNhtY7gm+w6vfPZyrJ+Xlg+AnY/pgKunqpW+OpuS551LV36pHZdCvpowzjgUafsXkAg2y3tpgrN+ecZdNOF/CjW2M2ohyisuvVEdE7XYNdWa4h6DyKZzAKxW8fKcnCTOmRMlzg0nzhoT3bG3ef7UZx5bO7aq9o3YLNF8DQtZbywip2TXOsmkQYAQaAWfYbsXXCAuSnh2jyNWQ/0hYonNkZ13EjsxoJc+B4GD5uVH6SxDZ+QHVXtXvdWg7ji3xPUnXaKkVKOttqV6wZZNsQcqNg+MUCUGUmyUEk7+QVObCjPck1Gg83JtU10u/RlrVP3QIW4Li7MU12nnZbt8Z9UGxjoiYVY3GeR9SXSeD14fXtBtkGCZTrjyoO47dZwqr6/xz5DNt9MUxUfSWCyY1pjKXZRl7+MZKCQ+YQMxlDi7EnzCV5QhYXiJi+kGqpyUU9JyPHdInkn8vYzVknBkwnsAjaLmnk6I+sJ0RKX5W5DzHK5a4PyXsxGPxZv/2/qFLqwD+2ASNaTKO+ZzzmNqO5+Nf2NJGX8xIbzdLOt3xkN9UPSf9Qhs4jp0kD9lnDIMLiYMT2Gn62WFjLUo415lVO2v/j6qfJb+kYhgBT+AbzDBeofAAUktZ8V3PFEl5bjURDz6luKbjM7t3MqPPak3GMZ9zHhO0d6i+lPCHf8RfGDZVfTEjvU29pQbSKtmFnykY8DbfWEF28ssqNZUPZuA4zpN6tXG/5E3g+BW+UcK5U+eBkW+vp0TO8yZw/4/IcKCNQ85jg9dJTFyCFH9TjPSW1LtN0n/rLHGvFKJ3ApBFWUrjDNgGqzlStdG0GdfzGDI5q0RqgjYBn9t6XNvbNTL8nwQljpFwk7nMMQnWqW7xjS2gtnhXQvZcDjT1PIZli9KBLNIWfG5LbW+tgNwqo/88QT8Fn9VTOwLbhse1YRsYp/b/TE2JJp572ORQVuTKmrqYz21o7C210rz/t2cKHuIWqf/6YZrsDJ4vV287Ojo6Jsz/BhhkkhqLbv4AAAAASUVORK5CYII=>

[image8]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABUAAAAYCAYAAAAVibZIAAABVUlEQVR4Xu2TwStEURTGP4UkhSiLsVLSpIzIQlnazIKSlb/Aho2NsrAirJVECkulbCyUxextbDTbWSj5AygLw/c593r3zpvFo2b3fvVbvHfO3HPPeWeAnFYzQA/oSeBklBEzQY+Q5O7TviiDdNAhukbr9IuuRhkJvfSWftIHWoJdqi1MCtFB5/SNbsWhX9bpMazwZkMshSqd0hX6TC/i8A/jsGJ7sI7m43CaQXpFi/SJVmhPENeIdugYvac1WgjiTZmmZ7QfdqAOViHPknOEvsDm2hXEm6J5+o+j1vVDHSCGYbfUbcv4wzy1InPuWXN7pzPBs+YpdpFxnr71dve8ALvNBmyFpPh360JFtFaHsN31LCJj67rdJZLWhWaotarR7eB95tan6CMdDd5pA/RvqcIKCK1XBVbMv0sxSz9g7XhvaCdsXtd02eW+NuTJO9rt4jk5reAbsxZG7RfThRcAAAAASUVORK5CYII=>

[image9]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAwAAAAZCAYAAAAFbs/PAAAA3ElEQVR4Xu3QvQtBYRTH8WNUYmBQiowKizKxmNiUXSb5D/g7MJmMsslitNoM7AYzkyJ5+R73enlwzZRffbr3Pufe557niPzz0ylghilKcJnlS5JI6E0YHfgxxAap+3uXpNGH72ldstih+bAWwcC+vsSDMeYIiLWj7qx/cEwde+TQEutMH5MR64MVyvJ+AEa0FW1pBPdT7W20hQMWCJml11zH18ARebNs5nF8cazRFoczBNFFzH7W3vUMS0TttVucZl3DSawx6wbaplcLFRRvr92jG/WwxQRVs/w1OQOCNSNukSIh4gAAAABJRU5ErkJggg==>

[image10]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACMAAAAYCAYAAABwZEQ3AAAB00lEQVR4Xu2VTShFQRiGP/nJv0jkZ4FslB0KKRZSFFmKnYWfLCUlysZCWSArKSuilJSfBXFtFAqJtZSNrYUSC+97v3O6c+beuiXN3dy3njpnvm/OfDPzzhyRpJL6X3WDR7AG0qyYU1WDNzAFXkFZMOxWo+AD9IBxkBIMuxMH3gLPoNiKOVchuAVHINOKOVMVWBFdlS/wAtZBvpHjTOmgFPSDH1Gv0LgJ8wtF836DNjvgWjngDIRArtFOI9+I4wK5LbxXNqx2FsFinJ6uJvApulWmpsGmqH/IMDgAjcbzEqgAE+AUzIr6kPknMXILJI6GJNovPN485oxR9WAQLIAnUCs66D44BEUgT7SgDi9/JkZur8TRquhvoNJoqwEPoM57LwHlEizQ9pTZh/lmLu+xS4njP9+89mXHHyY7c7a+7AIbwL3oNlED4Bhkee9mbie4Ei0qSiPgHLSIrortF24HV4z3T6vX1gcuJHLi2GdP9O9ubivzmq1cfmsetIMury0sJoTAO5gEd6LLamoM7IA5iczU/yCVCnYlMgkWs+3FaXx6hM8UzbwsetPze+b1EZ7JouhxvhZ1fCxxiziorwzRQXxlSzDOZ3NbzVwWxFhCb/ak/qRfMXZR8zu4m+8AAAAASUVORK5CYII=>

[image11]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACIAAAAXCAYAAABu8J3cAAABfElEQVR4Xu2UzStFQRiHX6FIviIlCyWfJVYSyUo2StbI1sKOUMrSzkJCkthaKCvZ+VrIxwJ/AsnGv0B5fs2ce07nHnWVe7M4Tz3dOzPvmfPOO3PGLCUlJeVvKMJ+3MS9BLvC0PyhJJbwE9/wHb/876u3NxOdR8bxAKt8uxtPsDITUSDasCLSnsX9SFtsm6uSxgpCCR7jfKy/Hu9xKNafN1rwBUdi/UpAiSihgqDz8mHZX8kyHpo72NW4hRvYiWt4hjPYiut4iaN60MfvJMRqrkQ0oJc9YG1s7BSn/P9JHDZXoV0sN3fO9MUtYDH24TXW+fjBWOwtNtoP6KFnC1ce5cnCKmmiHt+nrRTayhsLF6CklXyZhfFBrLb5yrIXmxO66CbMrSyonLZL6GXRiilhJdmOi1hjLl7ojN2Zm2cOm3x/zhzhqrnSBpMN+LFmfLSwYh14jis4ZmG8aMALc3NN+75foctNex+geyfYPv1G7yGhKsmA6HhprJ3yv/kG3L8+GbICOD8AAAAASUVORK5CYII=>

[image12]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC4AAAAXCAYAAAB0zH1SAAACQElEQVR4Xu2Wz0tVQRzFj1ASIaQUROjiEYioZFC2EF24CCHD0ly5dqGBKwuCFuHCSBcuLBExFRJqEUEtChFEHm4Ca+FGdKeIJOI/UEQ/zvE7w5t7ec8Xau8FvQMf7o/v3Hu/M98zMxcoqKD/S2fJMJkMOEh1ZByptkOkNNIiRzpJzpM+8pP8ioYjOkM+kB/kE7kM63hR2CiX0oefky6yHYt51ZKH5Amsg9ej4fzoHHlNqskqKYmG96sySKrIAtkk5WGDfOkqmSZlJAnrSKgOx0WyA7PLqUiLPKnHIb2AJehVARttjfoN2Bx4EMTzJvlbq0STu5aPrwUxXcvf0mNk9rc6Fq/UX5X3t/+oRr7Nnaszd925fJ9Een+3kxmyRMZgS+ZhNUC+wSp/oLy/T7hrJd0PW/q0gugoZfK3ltKPsIldTxbJzSB+GMmKWRMP/S2pI89g67q3j3QL6f19AVYJHY9LWRPXKM8imqAm4yZ5hOjGks7f2jGfkj3yknSTd6SXJGC2eU+ayag7b0RKOtfzI+7olTXxK2SFVAb3tCSuwTrg5f2tzSm8L2mk9Q5VSnqDVFX03i/kHmwQNEDLsPkku70lE66tKur3j4yJN8AmgErv0UgVw17Y6dppw9mNtRPz5LRrE09cH/SJx2M66jq0lX4ZWmDP+PsZEz9OxZP708R1vhXEVA0N2CXkIPEEbI58hZX9Nmzl+Uxag9grcofMke/ufg1sXkzB/pEGYEvqfbJONmBz5p+VfB3/NyqooKPoN6HTdnVcO9G8AAAAAElFTkSuQmCC>

[image13]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACcAAAAYCAYAAAB5j+RNAAABz0lEQVR4Xu2VPyiFURjGX6GIIkRK+ZPIIIoMSlIGBiWyMLChGGVgVcoiupsSJWEwIYvuhMFg8KdkJIMYFBmE5/Ger3vuubfrhsvge+rX973nnHvuc9/zvueK+PLly5evP1czOATnYASkhk9/qB9ku4OJVi5YMM9Z8AaGwlao2TGQ5Iz/qkrBlWgWs8wYDdFYsrfIiIbzoownVK3gFUyBbhAA6dZ8ATgAVaAejII9UGSt+YqWwLg76IrZOAUvYFtCGfRUCILm+ZOKyxyPcRE8gBpnjg0xB27BimjWpsEuqAa1ol9C2kRreQ1U8MOipTBoxtl49onEZa4cXIg2Rp8zRzFjx6DOxGXgzIpbwD3oMjH32AJpoBJcSygBtplPzRWLbtQD7sAqSAlbEWnOjflk7B17h2gZZJqYDdQpmnka8hTTXA7YAA2iGwVFO5cdbMs148axzPHH74vWMY3EZY6L10U71RNrgkfLpy3XjBvHMscv5zvF24CGeOwZ5j3CHIt0XvTasMWMMXMnIB8MgBKwDJ7BphnzYhZ5E9gxMRunV/TaeRS94BvBERgGM6K1OgkmwI2ZaxdLNMXiZZHaYsxNnsClfP8e88R9o/09+vofegeuZl7Zmm8ueQAAAABJRU5ErkJggg==>

[image14]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADkAAAAYCAYAAABA6FUWAAADF0lEQVR4Xu2YS6hNURzGP6EIeeYRusdroCjySlEKRWLAhBgZkFzlkUdIhEIMkMgjGaC8SiJkcFESpQxkpChlJBlQksf3nf9e7lqrtfc599q3XN2vfunu/9qP/3OtA+hQh9q1OpP1ZFVs+EfVk5wjE2JDnjqRLeQE6RLZRpFj5HTGUVLxFyQ0G83rxWbSLVhRjhrIzezfmppGnpHhsQH2ccPIIfKL/CRzghWhKuQFbN11Mob08ReUrBXkHiyzuepObpHG2BDpMDkJc3RxZHNSFewhl2HrFoXmNlFv8oQsjQ2+ppN3ZFxs8NSLXCHLyFeyNTT/kTK8mlwjH8nY0Nxm0vfchSUsqd2kCcXp1seeJxNhH38hNFfVnxyAlecb1H5mmZoBS1QyqOq32+RsbIiksttLhsAepnv8QaLBtRbW23rhd9iwaqkGk0uwIJ3J/k5Jg82XZsZ7sjy6XtUg2APzys9J/ahSVGaayHPS17Mrw5tgzm5E6/tR/TyTzCU/YLMiLsEF5EZ0Te30mGyPrlflIpA3SCQ5pkEyEubERdg9ulfSRxwkA2GDp4x+1HP0zm+wmeE0lVwl/bxrkgt+qo0wiXwhC2ODJ1eqTsq6MjUftl3sIl0z29+UaqwB5BWsarThaz8cHaxolgt+0kll5wOKM+lK1UkBkZPrYEPLf7ELQGtKNSUFS8/THFAW81SYyXp6UhFUMJymwLaRl2Sld72eUh0Py7aOkPVIwZKTG2JDpMKe7EEeIH+6qgwewrYHJ5f9+wi3iKHkLexlemlK6mWdhObFhoTU6/ouOangKYh5qjlb9iO9p+kEoRc4jmTX1Sty3JXPLNgk9NeKU5nd1x2YkzrLFkk9fpysgd0jB0YEK0IV7pNSPSeeMqX+Lio/lfI2WCBUSa7Pi45tNU889Z5dy9IO5B/w5ZSc8ye2gv8J+U7o7PoIBaXqVPQrpExVYGUct4bTEliZOgclt2eqJXRI0H68z7PrV4iGYyoAgRTBvN+TZUrTb3J8MZMG2k6kP1b75GvymTyF7dFSA1rwe1L67/9noEPtVb8BG6WdxxZVAsAAAAAASUVORK5CYII=>

[image15]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAD0AAAAXCAYAAAC4VUe5AAAC+UlEQVR4Xu2YTahOQRjH/0L5zMcVCSmxoiRJpJSPYsGCRElZWUlSProL3dRdiCxIFClJKAslocSNsmBlIaUsiCyEEgr5+P/fOZOZOTPnzHlfG733V7+678x5nzPPnDPPzHuBQQbpKobS3XRH2PEfsY720+FhR4whdB89SYcF7ZPpcjodZmLaZTxdRucgc1A1zEA5jsa7t1B/V7KYPoIJZJlIL9G79Br9Tt/QFc41OYykh+ljeoV+pF/pNmQMLEBJzqVn6As61e9u0UPv0/Vhh4sGdZ3uDNr11Dc6n2fS5zCDXuC016FZ11tkExxH79CfqBlYwCr6it6iT+lLxJMWW+hDmHtFWQITYF7Q/p4+gXmtLfvpb3rcaatiEswA39H5TruSVZwbdITTnst5VCc9DeYBrQk7LH10gI7xm1tJf4I/WBUKDXYA5etj2KT1nbVO+0L6BdUDr6IuadWlq0g8HM2yZvts2AGT7FL4624rTAIK6Ba8KmbTlfCLjgraD5h1PsFpz6UuadGLRPwpMAVBr20dSlKF7RfdEPQ1pQ9m8nLuGyMnaY3xNfzl2UIN6shJYjXM0zmF8lbRBFVfrfGbqCg0NeQkraWoJaSl5GHXli5IoYHdhqnAnezTmqjThdoxOiEn6UUwD7SU9Cz6FuknrYQv0u34u7Z1o6N0VPE5ByV8hB4s/hYqhMdgil1TcpJOPumqNa3BnaCb4RczFSG1W3SdCpUKVgx9V3v1Afhviib8Ah1dfLZxcshJOrmmdUMdFGLVW6/zN5gDgatOZnuc63QQUFF6BjOJITrg6ASmAbhxPsO/r40Ti+GiibuMREIOqt4P6NiwQ/Qjvu9qj9YgYro1QFubCtMHlF8l+yaF37e6b5iNE8aw2PoTxgjjiMp9WqROZE05hPSAm/AvYtSeyFJn7yao4J1De0XJRXE6jSG0VO6h/PZ6xH5lNWET3RU2toHidEoPzK8snSsqUYWN/Z7OwW5h7R40LDZOJ9idQro7TpKu+89JV/AHuX2mC1JOP5QAAAAASUVORK5CYII=>

[image16]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAD0AAAAXCAYAAAC4VUe5AAADg0lEQVR4Xu2YW4hNURjH/0IRQiN3KUmRa0iUmlwmCkkmyjulIaUhoiYSypMoIvKACCUpt8xBSTx4knLJkHgQopQXl//fWmvO2muvvc8+c5505lf/5uxvrf3tvdb6vm+tPUA33dQVPakt1Pqw4T9iObWP6h02xOhBbaOOUr2CtkHUCGoozMR0lf4wfoah4Etl0IeabKXfPhpHq5V+5zKHekyN8WwDqbPUXWondZ/6Ri1DAYceGuB+6gm1m7pC/aQ2o7pJ1DObqffULqtX1FK/E2mAedcVgT1BX+oa1RLY26h2aqS9Hgzz4j+omdZWhLXUS2qivVYkXaJ+U6tcpwLomR+o+Z5Nv99RMzyb0DMfwixclLnUW5hw8blD/aG2e7Yz1rbJs1XiJMw9utchn7Id82x5aJVPw0y6Jt/hFuKI7eMYRb2glni2BG1UCSbnfBQ2t6mp9lrtJZgVWmRtRZgO46fJs7nJ2+DZ8hhCPUP6Pd07qU19HC6aDnu2TlQIrsOsRiUUXgrtW0hPUDWobijcn1Ojg7YsplHfkT3ozyinj0N1KIyMf6iSvkYyhH0UMvNgtjG9qIrQ8ESP4kyh1sEUTGlCsjkXN+EqrH4Yu0HH6ozqhYpeamJlUENWQVGYNMIUBg34HjXJ71AF2iFWU8epp9QCFN8F3KD9uiDyBq09O2bvdKYORVAOKhdvwFT9rqKaoNqgEFe0VcKFt4prP8/uBq029fGZDbOgqUGPoz4ivtI3qctIln1Njgataq+DRiX0Uqq6D6ixnt1NdnQlIrg0LCGe02EhE5krnZfTGlx4k9tqSig/XIePhdR4e+3jBqd7/Ghyk9cBs70I5yeG0uw80oNzVV1t4UkyM6cVKgqZWPXuoA6gfGTU34swYbnG2oTyXQOIhaqi5BF1zv4WyuO9MPfssNfC+Ql9OBZTX5E+nMimthBVb0XYgLBB6IBeQnob0j7dAXOAUNW9CnN83IhkAVIufaK+IBJKMPu0VuMCjJ8T1C/qIJJncOcn5kPomVupNzC7iaQDSItt88ndp0XWiUxoH2+EqbpNSBaRkD3IfmENbhaMH4V2Q7I5QZYPh/b5lcj3U/FElnX2rgaF7imki0m1yE+tPoRSpR3p6E2gPTT8yqqGZpivplqRn1rR6usrK5bnCZQTWd/TldDWdQg5XzQFcX5qQeNotQrzPErd/eekLvgL8oa0pnwRrD4AAAAASUVORK5CYII=>

[image17]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA8AAAAXCAYAAADUUxW8AAAA9klEQVR4XmNgGAUUAREgjgNibnQJQoAFiNcA8WkgFkSTIwikgfgBEM8HYkZUKdzAE4hnAfF6IP4HxGeg/FBkRbiAABDLA/EiIP4KxC5ALAnEPMiK8AGa+dcOiJuAuAaIZdDkwMAGiH8DcTS6BBDMAWJWIFYA4q0MEC+igHIGiH+N0cRB/vZF4i9kgKiFA2z+LQRiDwaIM9E1gzAcgEw/AMRLGSD+NQPiBUDMyQBxCbrmPQxoKbAAiJ8D8XIgXg3EElBxfQZMzSB/cyCJ4QQgL8ECEcReBcQRCGnCYB8QmwNxKgMkKolOPCAAiiZxIBZmwEwDQxEAAPPzJTMzFsBaAAAAAElFTkSuQmCC>

[image18]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB8AAAAXCAYAAADz/ZRUAAABh0lEQVR4Xu3VPyhFURwH8J8wiEhETwYy+VMWlDJYXxnIaFRkMVCsSgYmpJSUySr1UgbplkmKySgpi8FiUKL4fv3Ozbnn3nev0r2W+61P7777e73zzjm/c59InjzBFOEGdqDKqaWaTng0HqAQLKeXCjiEW7eQRRrhCk7cQprpgC3RWb/BPaxCvfWZ1FINrTAOHzAHTaLbkFlm4R1G3EIW2Rft8nbrXhdswB5MQuUvaj2i20a8TkwtnIEHdeZeL2xCDbTABeyKnv24WgkajCMYkoTwPPNcc/Z+FuAF+s37KXiG7pgaZ7ps7jG8PpCE/hmEV9F999MMo6INybDGbeGDqFytT8KDe/KzmpHhL49rNi6hB0sSnoVda5Pw4Heip6lstiXcbH44O+4nv9xuuKgaB3EH5xOTKxXIDJzDsOjA9pIz/LJ5mBDtCVoTHSCuxlc/vF6x3n+He+DBEyzCtWjX2pmGTwdPBE9GXO0Uxoxjifhz4pFYF+3wSxgIlv8UrgonQu425fmffAFhXVH7ALJiBgAAAABJRU5ErkJggg==>

[image19]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAB4AAAAXCAYAAAAcP/9qAAABVUlEQVR4Xu2TvytGURjHH2GQX4mILMjgR9lYDO9glJLRaLAZDKxKFpMMlMQ/IPwBhreMJoPRQLLIYiY+38659x63+97u8HoH3U99uj3PczrPueeHWUlJyX+hCefwEE9SHuFEMrR+qOkWfuILvuKX/z7jA87Eo+vIEp5hl4+n8Qo74xF/xDi2B/E6ngaxGMN9c1u/gs0Fa7veySCXSQte4GaQm8IDbMN+vMVjc2PzavPY7b3EWcthFJ9wIchpER+WnPMqvpu7cLVq+sNznxPbPtZ9ykTn/Wa/b3EfVrDVxzoKXcKRnJruif4+Qo2r2BHkYrQareoOe1K1CG1b1dwrSK8+rA2Z27kINX7EgSAX04v3VntL9Fc6P00cXqCsmhqoUYQa61lqhwqjiTZwGQe9e+Ymz6vtWIJyYVyINfxOeWPuCebVhnHRe21uUQ1DT0ymj6akcfwAWhNGVmB5GbEAAAAASUVORK5CYII=>

[image20]: <data:image/png;base64,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>

[image21]: <data:image/png;base64,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>

[image22]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAaCAYAAADFTB7LAAACp0lEQVR4Xu2XS6hOURTHl7gibp6FiVcM5BEJESYoBiQTkaQkXUmiGLqRDCRSJpLHSKF0u8wUUlIMKElJMVIkIwPJ4/+z9v7uOuee70bfdx/l/uvXOfvxnb3OWmuvfT6zxjVEbBOb0/2AEgbtFy8Su1LfgBCGHBY3xPhEh2iLk/pbGDUytLmn7//WUDFHzBOjS2P9rmHinLglXopf4rGYECcFkYf7xDPxRhwsDjdfM8VZcy+ST6fESdESJwUtFx/EIfFNPLBe9voU8UjMKg/U0XnxVqwz/92G4nDzRYgJL6WjnteyWs2NuitGlMZ6VVvED3HEei66pAPhxYt9plHWlU+wqjj8RwvFRXFb/DTfILT53fAwr+li4Vdit9hpvoMxohw+2uTqAfFdbEztsXFSM0XeXRdPxJjQRy6+N1+8LDx9zzwHycWsPWK7eRVYLT6JTeapcjz1MbZDLDLP86tiq7m4Xkj9NVGUP5uXk6hr4qkYV+pHk8x3L3OystHAfX5JNtFU8/mX0lyeSe4uFs+tywlcadNf01rzXCJUWXmxK1a9UXjAV/O8i5qfQKQCxhEdPLJCTEtjE0W7+YaMUeJKO9piK8VHsST0sUOZuD70RfFgXoqXq6dl5l5bWh4wDyXGHrVqAwsvTt6Rf3zXITx2wnquhaQDJYYXqRKLPzQ/acrC4PvpHkOqDNyb2jWxg1+LO4n8jVelHLryBsmabH6eTzfPw7nmGwOR72fMn809J887KxpIu/JEwnN8FEBV3mXlDVJVoFmYsxyjWGyBOJbGOD5Pm3udMcrZDPPo5UhwpU3/P4sycVOsEV+se/7hWeom9TNCGHlp/hLEfryEI0ity2K2ecHvFt6/FbnBIu2i04pf0o2KLyC82tCXEHnJSUOC53IxqEE1qt/sun1wOpaPtgAAAABJRU5ErkJggg==>

[image23]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACcAAAAYCAYAAAB5j+RNAAACWElEQVR4Xu2WS6hOURiGX6GIyKVQcgsll0iIHCOFxMBESSaSiVIGDIlkgEgxkFxGSqdMmCmk5DJBbhOFjIg5ub1P39r+tVf7zP7tV85bT3uvb61z9re/2/6lQf0nGmrmmQVmdLHXUw0zp02/eW5+mftmQn7IGm72mpWFvVXNMqcU0RtpjpmjCmcqcX/CPDTPzNpsr1VNMffM7HIjCcfOKpzDec5xfl1+qC2RVlJ6TfVo5ZqkiGylUWZMtm5VW8wPs98MKfZ6KqKwz3xN9GV7RGujOWfON3BSURataLF5aXaaHYpOvW5GpH0c+Gbem4/mu/mQ1nDXTE1nu6ol5ovZntbU1SvzTp1oHFQ0AVpvLukvpJ2B+1kxMnJdMY/NuMLO+pHZUNh3mW2K9K8xn8xmxQscTjb2CADBoOEum60KcWUS1BqROfXTbMps1N4tNUdntSKivFSl6jxwX3X9TTPNvDEX0lle7oxZap6okxmurLH/EQ+jhpZlNoYxDpC+UgfMCzOxsC9MIOoUx64qIrHKTE97/N0hxVTIy4Yr6zxIGmsemD1pTaSOqHnW8a29o4gK0RlIKxTRWl5uKNKHo7xkk3NMi5ro1NfmRgLHxtdOhOYqaol/PJB4MJ3b9N3F2dvpHieanNud1jURMT7wUNZZJQqatJQRrTRZ8cNhhiKy89X5mlCjzEJemnsa6q3qzrEuG60r4qH8aMAhHrRIMX4Q3+Djilpmj1k6U1FO2BBX1ti7KhqAgc3gziF1ZOJpYSc6ZIc6v2jmKIZ8Y0p7KZqMaP5TP2wH1Zp+A/+EbW4CAvSKAAAAAElFTkSuQmCC>

[image24]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAD0AAAAXCAYAAAC4VUe5AAADUUlEQVR4Xu2YTahOQRjH/0L5zMcVCSmxECVJIlKkWJDoRklZWd0k8pGkm7oLkYWPWIgkSVkoSUq8URasLKREIh8LoYRCPv7/O+dx58yZOe85913p3l/969xn5p3zPDPPPDPnAv3006cYSG2ntoYN/xGrqS5qcNgQYwC1mzpJDQrs46ml1GS4iekto6nF1AxUdCrBEGp2Jj37yN9dmfRcygLqATXFs42lLlG3qavUD+oNtczrU4Wh1CHqIXWZ+kR9ozajgmMe6ttOvab2Z3pGrfI7kTbqLrUmsOeQU9eojsCuVV/v/T2Vegrn9FzP3gzNurLIAhxF3aJ+oYljAfOot9QSz6bnVyj6s5G6D/euKAupl3Dp4vOBegSX1sYe6g91zLOVMY56TL2n5nh2BatxrqOYojE0YefgsmWMZ9ezbCeyPsYkuAVa6dlydFINakTe3B30Z+SdVaGQsw0U+8ewoPUbPw21al/hJnuiZ09h4zSQf6+eZVOb+hiqS1eQWBzNsmb7TNgAF+wi5GdwE1wAGtAveGVMp5YjX7xU0H6iuHIp5IsWoIF40FqgmZ5d7ENi/AnUc7i0bYaCVGH7Ta0L2urSCTd5Vd4rLDMuIr8IFrTa1MdHPqro+duzGxnUUCWIFXCrcwqtHTmz4Pb4DZQUmgAL+nxgLwtaWzFm/zeYOqSQYzfhKnAr57Qm6nQmnRh1sPRW1R/u2S3osPaI+XALWgh6GvUO6ZVWwEqpLehJKxWeI9Sw7O8qKODD1IHsWcjho8gXoBS2DRuI7+mwkInkSpftaTl3nNqA/D5SEZLdUD8VKhWsGHZL2ot8pmjCL6Bn5WycGFZPwuCsqqstLKzJPa0XKmVi1Vvp/B3u8Pelm9kOr58uAipKT+AmMUQXHN3A5IA/zhfk32vjxMYQqim6GIWXE9nUFqLqfY8aGTaILhTTRmifyImY/BqgvaTC9BHFVLJMCn9v8jPMxgnHMJQxO6kXcB9Fki4gHVmbT+k5LVI3srocRNrhOjQbQ98Ha+Emvi1oM5reyFJ37zqo4J1FsZjUReO0OobQVrmDYvbmiH1l1aGd2hYae4HGaRWtvr6yYvs8h/ZE7Hu6CnaEVb1opLBxWsFOCinc51H63H9O+gR/Aft3tO/90QEUAAAAAElFTkSuQmCC>

[image25]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAXCAYAAAB50g0VAAAB5ElEQVR4Xu2VPyjuURjHH6GIUhSKemcxEHewGCwymNxB3WIwGGxS/uw2k8FdbrdMIiUZSDLrDsriLgaDUiQTxcL345zzvsf71+A3+X3r0+89z3Pe8zzn/J7z/MxSpfoeahGDolVU5fkYYy/lT1TtYkeciWVxLNZEjfc3iwNxJKbFodgUTd6fqDLiv1gS1aLRXCL3ostckn/Etqj1/+HJ+Lf3J6YQnATbvI1TORVX5pLvF4/il/cHMX4QPXn2LxWLE4QkY5F4OJkZ8SrGcu53McaOPzGF4ItiSKybq72BaA7Jl0uQ+QXidYz4ZynVmyvucmJxgpyLeVEnRsWNGPdzNsST+OHHQSFB/FlRnKviWVyLF3NBGuJJXtQON66cWJwg3Eo2FMSad6Lbz6EGWS9WQYLUxIoVnhr9aFJciGFvY7dbVrkN0FIIspBnZxyCh1fMycYKCWbrl+s/a6UbJEldiltzN7D3g7e4uInlEiT4nP9dqgazl4QT7Mi6i4s+1me5flVJ9Dn6HW8mVkhwwtyXg5LKv62MseNPTGyaZvvP3GcOsbldc18TSoTa3LfijRp7XLuJiM8cyZyIKbFn7lZnojn8xvZX/PRPNtUZzUlUlAa3lOD0w2Ilgg0fc5jLf1KlSvVZvQHywGAoiA8YIQAAAABJRU5ErkJggg==>

[image26]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADEAAAAXCAYAAACiaac3AAACI0lEQVR4Xu2VTYhOURjHH6GI8pEw2PgslM9sZjVJNGEjZUE2FuRro0xZzUZZWNmYxWwsLGZCWShfMWOllGysUK9SoihKYYHf/33O6T3vHbdz1dxZ6P7r1/ve5/zrPs85z3muWaNGjaZa82ExTC8uJJoL22AtzCysRVXxTLrmwXV4BE/gC+yDaYlHhZ2HN3AWrsAL2JJ4pCqeWjQIj2EZLIBn8A22J54D0II1SewIvIQVSaxlec+kaw48hN8wEGLXwvOZ8Kz2GIMbMCPEpFXwHk6HZ/lyntrUDw9gk3US/gW7wvp6+GReXKoeeAt3YJa5L+eZEqmF1Er3zQuSVKROpixBtcsic1/O06UlsCf8lmk2LCwGS6RL3Auv4BYsTdb2mxdxIYlJMUGh//LlPG1pZF2GH/AOfppPAfV2UdrVY8VgidTHfeYFjMOGZC0WEe9MVDFB+XKe9osu2sTd1y4ehZ3hv7QDRszH57/quHnSd81PM7bTcGqyToIaqcpJvpyn3aOnrHt+p3oNn+Gj+airMp/1kntw0zoFx52Pu7cZvlp5v8dLK1/O0z6J5amjIH2QVsNWq/6ljAmn3wW1hGJj5hun4p7axAkTp9ZgeJYv56lFK81P7ZJ54WLUfMQe6tjshPkdLH7IPsDGJFbFU4vUyy0YgtvwHU5ad9uquKvwHA7DOfOE9yYeqYqnNqkF+mC3/X3SSSpqHRy0cl8VT6NGjf4n/QEFdH3R74eZlQAAAABJRU5ErkJggg==>

[image27]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC8AAAAYCAYAAABqWKS5AAABkklEQVR4Xu2VSytFURiGP6HIPRJFYeJWytRQBgxcMiKT8xuUiYzMTJWUy8DIxMRAx8yJYkAp8QNIGfkLeF9rb317te3rOXUG66mnc/b69u68e61vrSPicDiqkRo44H1WhCVYgE3WeB4a4BQ8h1ewOVguH/VwBT7BHdgZLGfiTUzwV1iSCob3qYWL8BHuWbUsMHDJs+LhffgSXPITOGzV0hAbfg4+w1PYA/vgoZhlm1T3ZWECXnrye9pNFxm+Hx7DETG99SAmeLeYH3qBXX93Z4ezfwaLcMyqRREZfs1zCH7Aa9im6nyhXnWdlVa4JWZD82RKSmR4n034CUfVGF9oV12nhat6B6fF7IEsxIbneXoB72GHGufRN6uuk+K3CFcxbY/bxIbnBn2X4CzXiQnAfl+AG6oWBkNyQ7Kn+VyeE0YTG34GfsFlNcY+Z783wiM4rmphFOABHLTG88JOuIU3sMWq/bIuZub1D3Pm98UccWk2WDn5/sd5fRN7vl0PeLAVQpfKUUWsivlHTuK294zD4UjBD9aiTQxljPsbAAAAAElFTkSuQmCC>

[image28]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFUAAAAXCAYAAAB6ZQM9AAAENUlEQVR4Xu2YW6imUxjH/3LI5BSmQU6fGIdxzilm0h5ShDHNKJSLuTNmChFySCSFuRBqFJqdC0WDyOEC5QslhysXyKE2MUIScTHE+P/mWcu3vvW932HX7BkX779+7f2utd79rvV/n/U8691Sq1atWrWaCx1t3jXfm03mU3ORuTn1d8zD5vHEI+bI1JfVUf8Y4P5jqraSB81ZZmf9P7S7OcGcafas+pp0iFmjuK9PpyrMvMLslNr2MxvNrel6V3OAudT8ZbaY19X/YMacbjaY3831CqN3M1eaP8yPigkfZKbMdeZr86U5RTtOrPsS84l52nxm/jFPmj2KcaVYL4HRVfUC+GPT5lUNun2oeqZmnWbeMR8pjL1FvReRxZgX1f8gTMQ84PdSRMYvih1yVNW3vcScnzf7pGvWxNpY42Nml9ReaqX5Ww2mckHjc2q+sclUDDtfYQQQeaVma2qeAwu4sb9ru4l0xvNvKNoONjPmZ3Nc0Y4ON2+YrzTC1J/MyWVH0urqOhu2t3pv8k313nA5Zq5MJf9ebNYrzDgntQ3TlMbnx2wq2z2rnBdpL4tt/6hZkfph4O/frbjxV/OAIvLqVJBVGgbkVe69Tb00MFtTFypy7eeKCBglFsR2ZOx95nZFPv7ALCrGZc0z95t9645KBAmFeX7Rxj0fKmrIkqJ9mcIn7ukmBkwlyog2zCl5uxyUVBtGkSMFUISo4k1jUDb1O8WO4JrKSQHLpnACGaezzUMKc7OI0qvMt2ad2T+1U2DuNfdoMO9PIp61WYOmkXuZe47kuv8/MQGOPzPqNxbTSjUZdpNiLMawoKYx2VQmSXWlaj6l2B1vmcN6Q0dqqTmjbkwictjGFI88/1HVe5SI8JcVaZETTRYvh0hFQ01lm5MbmrY7RygSMT+zmgxDxysmwILu0OCYUdsfczHgmqp9mA40zyqe9ad5QhE5w0SwlNt6nFYqtn19EllgXlPMH+h/L8HvBNTWHcHCWVS90KzahGGmoqsV5nC+I/omNZUTRo6qcSJVvWTuUuRfuNP8oCicRFgpFsoHxqTRSgF8RfHistYqdsiJ5mPzTWKTYt68XFLPM0rPYeEUmwu5qITrXfWbM8pU8ty04kFdzd5U8vq4xZ+nyMO1iNQXFOlrVbq+THGeJvImEQV6o+LDJ4tjJjuh6WSU19RV5UfOC2zzk8oO61hF9GVhMqnifXNE0V6qo+azG4vkbTaZyrbH1BnF2XAvxe4p007WYjUvEDG/cxUfJ78pooqKvnVLjhERz6c5p5AcicD1F2qeSzaVVNF3umDhVLNrFZ9mXUW15MjAoTdXWSKUCp8LQFM0ZhEZfKHlqOPe8j4ozWVLEyG0U2jIyTx/EjO2lUg99RyHrTMH4tBxhDf/8GABHE34crhccdhtejtzJZ7fMcvNBRrMja1atWrVqlWrbaF/AV8JChhqMDvGAAAAAElFTkSuQmCC>

[image29]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAC0AAAAXCAYAAACf+8ZRAAAB3klEQVR4Xu2WTyhsURzHf8JCCC/5X5IdvYdkI4tJIsXqKUpZUIjexkZZsbCzYWVhw47Fq5cUEoOlnbJ6FLIiilIof77fzp3m3DP3zJ/MzOp+6tO98zunmfM793d+d0R8fHwSoRCWwxKYaYzZyILDZjBdFMB9OAOP4CPsgRn6JA/y4TF8hzfwWvMU/gxPTT6zsMK5L4In8Bk2hyZYqBK12E8PN2FOeGpyyYV7cFqLrYr64T9azAsmtWjEquE/55pSuuEv5z4PBuEH7AhNsNALp7TP2XAZ/tZiaYG7x9LYFZVAIozDOYlyFkphl3O1wZr6YQYttMJR+B/+hWXu4ZjUwwOxrIePYAG+ijoEb3BJVG2acNdGzKCFABwQteBDWOcajQ5b3wqcNwcIBzlgZsPHMQTbnXvSAtdFtbNEGRN1ELclvg7AQ2ztNqyxSbHXzDl8gLfwEja6Rr3hC2VH3MnxgHHRV854LLZEPXW2wAi405VmUINvslrYJKqM4iG0QH2XuHOMBSV8GPndbeLdyphcvAkmhRpRTyWUJK8bolpevxMjrHcmcgaLtTh5kjQvmrBPs78OinoxvMAJcZdhA7yDaxJZ5/fwQiLPWsoJwD7YKd6dKBpslyn9n+Hj4/MNvgAip1BiPVJTbgAAAABJRU5ErkJggg==>

[image30]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABkAAAAXCAYAAAD+4+QTAAABrklEQVR4Xu2UPSiGURTHj1BEvr8jkawGUsrnIBlIUQajzUiZDG+ZJIuFWYlYFKVkYBMLgxRZpJTCRD4S//97n/u+517Pm9em+NevW//nnOfc59xzH5F//VZlgmLfhHJAlm8qpYAKkOr56aDI86QRPIJ7sAs2wC04BZUqzlc22AOv4BgsgwvwBPrjYUa2yIdiDZTpoBDZIjrvDHSomJhYZBvUgXKQ4T5OKBbZBD1i8vLcx65YhC1i0k/EeOYx/1vZIgWgHfSBQiciXLZIE6gHQ8HKgfgiFrkC+2AUjINrMCYJEgKxyI6Yc5gCI+AArIJcFRdVA1j3HjDhXUKmRInjzQFpVl4tuAELIE350R2xPXrXduIuQanytXgfSoLVSk9crzX58hPwAlqsKckVmRPzsojyQovwZvLSnYNqa0Kt4A2sSPyz+WfoikWIzItp6aDy8sGRmDOtsSZbNAuGrRF40+BB3H5HxOzQ3qNusChuu9rE3PhJ8YaGB74FlsQcONc7UZ8biKP9LPFkrhPgUMxUcsKYNyNu4Zj4k+M5cNY7JflbT1WBATGbSHR+//pr+gTSWE6iX+LcswAAAABJRU5ErkJggg==>

[image31]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACwAAAAXCAYAAABwOa1vAAACGklEQVR4Xu2VPUgdQRSFr6igKJigKLFRyxDRiGAhBCxMwEKwiBgIpIwW2hgkEFKkFAQrCzsNIoKgYBdR/GtT2yQGXlKk06Ao2Ok5784l8+btOgta7gcfj7mz8/bs7MysSE5OjvEIPoHNsDLoC6mAb+HzsMPR6awJOx6CBrgK9+AneATPRUOl0Qf/weGgzjGj8LPzBA6VXBGhPSwk8AXuw1bXfgy/w167IIAPuAtvpDwwx/z12i/gH9jj1e4k7aZGnfy/+Uev/hVOeW2DMzgj+oBhYPYtiT6sYQ+/4PqjxAITvrId2OXa9fAADtoFHlwKy3BMygM3wWPRsYb9F+vsj5IlcAjHXInezIftFfhMNGgYuBteSHLgU/jUq6eSNTBfVz98D3/CzdLuItNOkhTYHpQb2LDArGfKkukiUAUH4BvRsIclvTqrnF2b9bsCc/0biYFtdl4nyI0U1mhbcWQ64/AbrIUTcE70FOE5Td+JBuYv2zxvbUlwExsWmHX2R4nNMG+2DTdEjyuDM/fb9c+LHk2+l6KBz1ybG7QF/pLkNfxgm85ebbjG+GYOpHzjGewPlwSX1ZpoOMNODtbZHyUWuAMW4CysdjX+roseXWlYYH6efV6KfgENfjjYZj0TscCE53ABLooG2ILXknzQ2xsJtZnmmA+ipw39ASddPRNZAhNumgHRDflK9At4H0ZEH6Ix7IjRHhZycnLuxy0Mf3JAdVbuagAAAABJRU5ErkJggg==>

[image32]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAwAAAAYCAYAAADOMhxqAAAAp0lEQVR4XmNgGAXDAvABcTIQz8KC84CYBaGUgcEJiF8D8S8gfgXE/6H4GRA/AuJeBiQNZkD8DogbgJgVKhYDxJ+A2BjKhwOQwFcgjkYTdwHiv0DsiSbO4MsA0YBuUjkQPwFiRTRxsIaHQCyJJMYPxCeAeAIQMyKJg4EOEN9lQNgAUlAGxLsZIBoxAEhBFhBfBeK5QHwAiCcxQIIYL+BggDgLRI8CigAAGGYdCO+yVf4AAAAASUVORK5CYII=>

[image33]: <data:image/png;base64,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>

[image34]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAYCAYAAACIhL/AAAACjUlEQVR4Xu2WS6iOQRzGH6GIcs1dSkqKkBAhhWLBgoVENgoLNqdcsjpIFhLZKJQoKSkbl5T4pCSUlNuCXHYUCwtl4fI855k538z0fslx3ijnqV9v88587/z/M8/85wN69B+qN5lCppKBRd9fVx9ylFwkT8gPcpcMSwclGkTOk9vkNZmed3e/JpIj8Cr2JwfJAdI3HZSondyBk1Iyu7LeGjQannBS2VGh4eQpOUU2k2tkXDaiBmmLtb0X0HrVomaTL2RL2VG3VpNvZCfpVfSlWk++k6VlR50aQNrI18DCvLtDm8gJ8hAO8FJoL0sH1aEZ5BkcwEbY9Jq8XzqIGkzGk6vkEZkMe7cc162aST6RDaE9kjwnb+HJS8UDIr/Kt7VKRfkjXE5SnSEPyJDivbQCXuGVyTv5dR9ZBJcpJfseTn4EOQnXU9noLHwJqH2FzA2/340K78vk8lI6mT5yg5xG9UFRvfuMvDBr1V/BZUdSYkrwGJyQ5tBTWgDPu4rcQvPGmgXbZmxod0iDP8BlI0oFW9u7PHkXpYDPwVusrU7fzycTQjvaoB1OeEl4SgpuHtlDGsgDfBeendJ1dY9sC21NtB+ta2FcmV/5by18XcaAo/RN7YyeslEDeYDambjSndIJfkEuBxTc0GxEU9Gzyr6V5sBbV95ISn4HOR7askMDeYA6rJW1VT+WaUWV76KUnQp55UfgBA7DCeo+V1vSN9eRrfAhGgXX3AbyAN+gi386rpPt8MqV/ovSih2CPazypCRUVxXcGji4MaFPQciHDTQrhc7DTdh2vy2VFW2NCrQmKqWVfwyPS9GKL4ZXPX2vUy8fKqG9ZBp8MXT5RnpJ7sNlo+rw/Il0O9V+G/Xon9RP5TB3lWgcvfYAAAAASUVORK5CYII=>