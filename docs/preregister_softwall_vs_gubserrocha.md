# 1. Título

Prerregistro científico-técnico para evaluar si la separación `soft_wall` vs `gubser_rocha` sobrevive a control estadístico, sensibilidad de resolución, hiperparámetros y cohorte

## 2. Objetivo

Congelar, antes de nuevos análisis, un protocolo auditable para responder la pregunta de si existe una separación reproducible entre las familias `soft_wall` y `gubser_rocha` en el framework holográfico del repo, distinguiendo explícitamente entre:

- efecto de familia;
- artefacto UV;
- artefacto IR;
- sensibilidad a resolución;
- sensibilidad a hiperparámetros;
- sensibilidad a cohorte;
- mezcla inducida por discretización o normalización.

El documento está pensado para ejecución posterior sin rehacer la lógica metodológica.

## 3. Pregunta bloqueante

¿La separación `soft_wall` vs `gubser_rocha` sobrevive a un tratamiento estadístico preregistrado y a sensibilidad de hiperparámetros, resolución y cohorte, una vez separadas las contribuciones UV, bulk/familia e IR y controlada la mezcla por discretización y normalización?

## 4. Hipótesis

### H0

No existe evidencia robusta de separación entre `soft_wall` y `gubser_rocha` bajo el protocolo preregistrado. Cualquier diferencia observada puede explicarse por una o más de las siguientes causas:

- artefacto de región UV;
- artefacto de región IR;
- sensibilidad a discretización o resolución;
- sensibilidad a normalización;
- sensibilidad a hiperparámetros del learner;
- sensibilidad a la composición de cohorte;
- o por selección post-hoc del observable.

### H1

Existe evidencia robusta de separación entre `soft_wall` y `gubser_rocha` bajo el protocolo preregistrado, y dicha separación:

- aparece en la cohorte canónica preregistrada;
- no depende de escoger a posteriori el mejor observable;
- sobrevive a los checks de resolución, hiperparámetros y cohorte;
- y no puede atribuirse principalmente a una sola ventana UV o IR ni a un cambio de normalización.

## 5. Alcance y no-alcance

Alcance:

- comparación entre `soft_wall` y `gubser_rocha` usando artefactos ya definidos en `01_generate_sandbox_geometries.py`, `02_emergent_geometry_engine.py`, `06_build_bulk_eigenmodes_dataset.py`, `07_emergent_lambda_sl_dictionary.py` y `08_build_holographic_dictionary.py`;
- uso de cohortes sandbox con trazabilidad contractual vía `runs/<run_id>/...`;
- uso de los HDF5 de `01_generate_sandbox_geometries` como fuente primaria de `boundary/`, `bulk_truth/`, `z_grid`, `x_grid`, `G2_O1..O3`, `Delta_mass_dict` y metadatos de familia;
- uso de `02_emergent_geometry_engine/emergent_geometry_summary.json` y `predictions/*.npz` para la evaluación de separación operativa del learner.

No-alcance:

- no demostrar física fuerte, holografía real ni un mecanismo microscópico;
- no elevar una etiqueta `family_pred` a claim físico;
- no reutilizar `Stage 04` como soporte de física de power-law, de acuerdo con `docs/stage04_correlator_semantics_tail_strict.md`;
- no reinterpretar `log_slope` o `has_power_law` como dimensión conforme ni como evidencia de separación física;
- no usar cohortes reales GWOSC para resolver esta pregunta;
- no hacer tuning abierto hasta “encontrar” separación.

## 6. Cohorte canónica

La cohorte canónica preregistrada será la subcohorte emparejada `d=4`, categoría `test`, del run:

- `runs/tier_a_ext_discrim_20260414_codex_run1/01_generate_sandbox_geometries/`

Definición exacta:

- `10` sistemas `gubser_rocha`: `gubser_rocha_d4_mu08_test_000` a `gubser_rocha_d4_mu08_test_009`
- `10` sistemas `soft_wall`: `soft_wall_d4_k05_test_000` a `soft_wall_d4_k05_test_009`

Justificación:

- misma corrida de generación;
- mismo comando base persistido en `runs/tier_a_ext_discrim_20260414_codex_run1/01_generate_sandbox_geometries/manifest.json`;
- misma resolución generativa visible hoy: `--z-max 5.0 --n-z 100 --n-operators 3`;
- mismos tamaños observados en HDF5: `z_grid=100`, `x_grid=100`, `omega_grid=50`, `k_grid=30`;
- emparejamiento por `d=4` y por categoría `test`, minimizando mezcla entre efecto de familia y diferencias triviales de soporte.

Queda explícitamente prohibido sustituir esta cohorte canónica por otra distinta después de ver resultados. Cualquier cohorte adicional entra solo como sensibilidad preregistrada y debe reportarse separada.

## 7. Observable primario

Observable primario provisional:

`BA_binaria_test_d4`, definido como la balanced accuracy binaria exacta sobre la cohorte canónica, usando exclusivamente el artefacto:

- `runs/tier_a_ext_discrim_20260414_codex_run1/02_emergent_geometry_engine/emergent_geometry_summary.json`

Regla exacta:

1. Se filtran únicamente los `20` sistemas de la cohorte canónica.
2. La verdad terreno es `family_truth ∈ {gubser_rocha, soft_wall}`.
3. La predicción válida es:
   - `gubser_rocha` si `family_pred == "gubser_rocha"`
   - `soft_wall` si `family_pred == "soft_wall"`
4. Cualquier otra salida (`gauss_bonnet`, `dpbrane`, `unknown`, etc.) se codifica como error, no como abstención favorable.
5. Se calcula:
   - sensibilidad para `gubser_rocha`;
   - sensibilidad para `soft_wall`;
   - `BA_binaria_test_d4 = 0.5 * (sensibilidad_GR + sensibilidad_SW)`.

Motivo de esta elección:

- es reproducible hoy con artefactos ya persistidos;
- no depende de escoger una feature local del correlador;
- no depende de inspección manual de casos favorables;
- responde directamente a la pregunta de separación operativa entre familias.

Congelación pendiente:

El observable primario definitivo preferible sería score-based, por ejemplo un `AUROC_binario_test_d4` construido con `family_scores["soft_wall"] - family_scores["gubser_rocha"]` o una versión equivalente a partir de `family_margin`. Ese score no está persistido en `run_train_mode()` aunque sí existe en código en `build_family_inference_report()` de `02_emergent_geometry_engine.py`. Por tanto:

- el observable primario queda congelado hoy como `BA_binaria_test_d4`;
- y se marca como artefacto faltante la persistencia por sistema de `family_scores`, `family_top1_score` y `family_margin` en outputs de entrenamiento para una futura versión score-based, sin cambiar la lógica del protocolo.

## 8. Observable(s) secundario(s)

Se preregistran dos familias de observables secundarios. Ninguno puede reemplazar al primario a posteriori.

Secundario A, integral de frontera:

`D_G2_region(op, region)`, definido para `op ∈ {O1,O2,O3}` y para cada región preregistrada `UV`, `MID`, `IR`, como el área absoluta entre las curvas promedio por familia:

- fuente: `runs/tier_a_ext_discrim_20260414_codex_run1/01_generate_sandbox_geometries/*.h5`
- datasets: `boundary/x_grid`, `boundary/G2_O1`, `boundary/G2_O2`, `boundary/G2_O3`

Definición:

1. Para cada sistema y operador se construye `log G2_norm(x)`.
2. La normalización canónica divide cada `G2_Ok(x)` por la media de `G2_Ok(x)` en la ventana UV canónica antes de pasar a logaritmo.
3. Para cada familia se promedia `log G2_norm(x)` punto a punto.
4. Se calcula el área absoluta entre promedios familiares en cada región:

`D_G2_region = ∫_region | mean_logG2_softwall(x) - mean_logG2_gubser(x) | dx`

5. Se reporta además el agregado integral:

`D_G2_total = media_op [ D_G2_UV + D_G2_MID + D_G2_IR ]`

Secundario B, integral radial de bulk:

`D_bulk_region(field, region)` con `field ∈ {A_truth, f_truth}` usando:

- fuente: `runs/tier_a_ext_discrim_20260414_codex_run1/01_generate_sandbox_geometries/*.h5`
- datasets: `z_grid`, `bulk_truth/A_truth`, `bulk_truth/f_truth`

Definición:

1. Se promedian por familia los perfiles `A_truth(z)` y `f_truth(z)` sobre la cohorte canónica.
2. Se calcula por región:

`D_bulk_region(field) = ∫_region | mean_field_softwall(z) - mean_field_gubser(z) | dz`

3. Se reporta también el agregado:

`D_bulk_total = D_A_UV + D_A_MID + D_A_IR + D_f_UV + D_f_MID + D_f_IR`

Función de estos secundarios:

- obligar a comprobar si la separación aparente proviene de todo el perfil o solo de un segmento local;
- separar contribución de frontera y contribución geométrica;
- impedir que una diferencia numérica localizada se promocione a claim de familia.

## 9. Variables de sensibilidad

### resolución

Bloque principal:

- variar una sola dimensión de resolución por vez respecto al baseline canónico `n-z=100`;
- no variar simultáneamente resolución y normalización;
- no mezclar cambios de resolución con cambios de cohorte.

Baseline preregistrado:

- `runs/tier_a_ext_discrim_20260414_codex_run1/01_generate_sandbox_geometries/manifest.json`
- comando observado: `--z-max 5.0 --n-z 100 --n-operators 3`

Sensibilidades mínimas preregistradas:

- resolución radial baja;
- resolución radial alta;
- cualquier regeneración debe conservar misma definición de familias, mismo `z-max`, mismo número de operadores y misma lógica de split.

Si el generador no permite separar todos los ejes de malla de forma independiente, se documentará explícitamente qué knob global se modificó y no se reinterpretará como cambio puro UV o puro IR.

### hiperparámetros

Bloque principal:

- variar un solo hiperparámetro del learner por vez;
- mantener fija la cohorte canónica;
- mantener fija la resolución;
- mantener fija la normalización.

Baseline operativo observado:

- `02_emergent_geometry_engine.py`
- defaults del parser: `hidden_dim=256`, `n_layers=4`, `batch_size=32`, `lr=1e-3`, `seed=42`
- run canónico de referencia: `runs/tier_a_ext_discrim_20260414_codex_run1/02_emergent_geometry_engine/manifest.json`
- comando observado: `--n-epochs 500`

Hipótesis de sensibilidad que deben probarse una a una:

- semilla;
- `n_epochs`;
- `hidden_dim`;
- `n_layers`;
- `batch_size`;
- `lr`.

No se permite un barrido simultáneo de múltiples knobs sin trazabilidad. Todo cambio debe producir un nuevo `run_id`.

### cohorte

Cohorte canónica:

- solo la subcohorte `d=4`, `test`, descrita en la sección 6.

Sensibilidades de cohorte permitidas:

- otra cohorte emparejada y preregistrada por adelantado;
- una cohorte generada con otro `seed` pero con misma definición de familias y mismo diseño;
- una cohorte ampliada únicamente si mantiene balance entre ambas familias y si se reporta por separado.

No se permite:

- cambiar de cohorte después de inspeccionar resultados;
- sustituir la cohorte `test` por la cohorte `known` porque “funciona mejor”;
- combinar subcohortes heterogéneas para rescatar separación.

### normalización / región UV-IR si aplica

Normalización canónica de frontera:

- para cada operador, dividir `G2_Ok(x)` por la media en la ventana UV canónica antes de tomar logaritmo.

Ventanas canónicas:

- `UV`: primer tercio de `x_grid` en coordenada física, no por índice tras reordenamientos manuales;
- `MID`: tercio central;
- `IR`: tercio final.

Análogo radial:

- `UV_bulk`: primer tercio de `z_grid`;
- `MID_bulk`: tercio central;
- `IR_bulk`: tercio final, cercano a horizonte.

Sensibilidades permitidas:

- una variante de normalización alternativa preregistrada;
- una variante de fronteras de ventana UV/MID/IR preregistrada.

No se permite:

- mover ventanas después de ver qué región separa mejor;
- elegir el mejor operador o la mejor región como claim principal.

## 10. Diseño estadístico preregistrado

Bloque A, evaluación primaria:

1. Usar la cohorte canónica fija de `20` sistemas.
2. Calcular `BA_binaria_test_d4`.
3. Estimar incertidumbre mediante bootstrap estratificado por familia sobre sistemas, con el mismo tamaño por familia en cada remuestreo.
4. Complementar con prueba de permutación sobre etiquetas de familia en la cohorte canónica.
5. Umbral numérico preregistrado para considerar separación útil en el baseline:
   - `BA_binaria_test_d4 >= 0.75`
   - y percentil 2.5% bootstrap `> 0.50`

Bloque B, descomposición por región:

1. Calcular `D_G2_UV`, `D_G2_MID`, `D_G2_IR`, `D_G2_total`.
2. Calcular `D_A_UV`, `D_A_MID`, `D_A_IR`, `D_f_UV`, `D_f_MID`, `D_f_IR`, `D_bulk_total`.
3. Reportar contribución relativa de cada región al total.

Bloque C, sensibilidades:

1. Ejecutar el bloque A y el bloque B en el baseline canónico.
2. Repetir variando una sola cosa por vez:
   - resolución;
   - hiperparámetro;
   - cohorte;
   - normalización o ventanas.
3. Prohibido interpretar un resultado de sensibilidad como nuevo baseline.

Bloque D, gobernanza contra p-hacking:

- el observable primario no se cambia tras mirar los secundarios;
- los secundarios no se convierten en primarios si “quedan mejor”;
- cualquier métrica adicional se etiqueta como exploratoria y no entra en el veredicto;
- toda corrida debe conservar manifiesto y comando exactos en `runs/<run_id>/manifest.json`.

## 11. Regla de decisión

El protocolo solo puede emitir uno de estos tres veredictos:

- `SEPARATION_CONFIRMED`
- `SEPARATION_FRAGILE`
- `NO_CONCLUSIVE_SEPARATION`

Regla para `SEPARATION_CONFIRMED`:

- `BA_binaria_test_d4 >= 0.75` en la cohorte canónica;
- y el límite inferior bootstrap al `95%` es `> 0.50`;
- la incertidumbre bootstrap no reduce el efecto a azar operacional;
- el signo del efecto se mantiene en todos los bloques principales de sensibilidad;
- y en cada sensibilidad principal la métrica no cae por debajo de `0.65`;
- ninguna sola región `UV` o `IR` explica casi todo el efecto;
- y los secundarios integrales no muestran que la separación dependa solo de una mezcla de normalización o discretización.

Regla para `SEPARATION_FRAGILE`:

- el baseline canónico sugiere separación, pero esta:
  - cae por debajo del umbral en al menos un bloque principal de sensibilidad;
  - o cambia de signo;
  - o queda concentrada casi por completo en UV o IR;
  - o desaparece bajo una normalización preregistrada alternativa;
  - o depende de un único ajuste de hiperparámetros.

Regla para `NO_CONCLUSIVE_SEPARATION`:

- el observable primario no muestra separación suficiente en el baseline;
- o la incertidumbre es demasiado amplia;
- o faltan artefactos mínimos para ejecutar el protocolo de forma completa;
- o los resultados son internamente inconsistentes sin patrón estable.

## 12. Criterios de fragilidad / no conclusión

Se considerará fragilidad o no conclusión cualquiera de los siguientes casos:

- el efecto aparece solo en una ventana `UV` o solo en una ventana `IR`;
- una sola región aporta `>= 80%` de `D_G2_total` o de `D_bulk_total`;
- el efecto desaparece al usar la cohorte canónica replicada;
- el efecto requiere escoger a posteriori el operador `O1`, `O2` u `O3`;
- el efecto requiere escoger a posteriori la mejor normalización;
- el efecto se sostiene solo para una combinación de varios knobs movidos a la vez;
- el efecto no sobrevive al cambio de semilla;
- el observable primario queda desacoplado de los observables integrales secundarios;
- la separación puede explicarse por discretización, clipping o soporte de entrenamiento;
- o el protocolo queda bloqueado por falta del score binario persistido y la versión label-only resulta insuficiente.

## 13. Interpretación física permitida

Solo si el veredicto final es `SEPARATION_CONFIRMED` se permite afirmar, y solo de forma limitada, que:

- dentro del sandbox y de este protocolo, `soft_wall` y `gubser_rocha` exhiben una separación operativa reproducible;
- dicha separación no parece reducirse de forma trivial a una sola cola UV o IR;
- y la señal sobrevive a los checks preregistrados de robustez.

Incluso en ese caso no se permite hablar de descubrimiento físico fuerte. La lectura permitida seguirá siendo de compatibilidad interna del sandbox y del pipeline.

## 14. Interpretación física no permitida

Queda explícitamente prohibido inferir, a partir de este protocolo:

- que existe ya una separación física real en naturaleza;
- que `family_pred` identifica la teoría correcta del bulk;
- que una diferencia numérica local en una cola implica una fase física distinta;
- que `Stage 04` aporta soporte de power-law físico o de dimensión conforme;
- que una mejora tras tuning local equivale a evidencia;
- que una diferencia robusta en el sandbox valida directamente datos reales o GWOSC.

## 15. Riesgos metodológicos

- el primario actual es label-based y no score-based porque `run_train_mode()` no persiste `family_scores` por sistema;
- la cohorte canónica es pequeña (`20` sistemas), por lo que la incertidumbre debe reportarse siempre;
- el learner de `02_emergent_geometry_engine.py` tiene múltiples hiperparámetros con capacidad de inducir sensibilidad artificial;
- el repo ya documenta que las lecturas de `Stage 04` pueden inflarse semánticamente si no se gobiernan;
- la región IR puede dominar por normalización deficiente;
- la región UV puede dominar por fijación indebida de escala;
- usar cohortes no emparejadas por `d` o categoría mezclaría familia con soporte o complejidad;
- y usar muchas variantes sin trazabilidad convertiría el experimento en tuning post-hoc.

## 16. Entregables esperados

- un reporte principal con el veredicto único entre `SEPARATION_CONFIRMED`, `SEPARATION_FRAGILE` y `NO_CONCLUSIVE_SEPARATION`;
- tabla con `BA_binaria_test_d4` y su incertidumbre;
- tabla con `D_G2_UV`, `D_G2_MID`, `D_G2_IR`, `D_G2_total`;
- tabla con `D_A_*`, `D_f_*` y `D_bulk_total`;
- matriz de sensibilidades, una fila por perturbación y una sola variable cambiada por vez;
- registro completo de comandos, `run_id`, manifests y rutas exactas.

## 17. Criterios de aceptación

El prerregistro se considerará ejecutado correctamente solo si:

- la cohorte canónica usada coincide exactamente con la sección 6;
- el observable primario reportado es `BA_binaria_test_d4` y no otro escogido post-hoc;
- los secundarios integrales se reportan completos, no solo la región “ganadora”;
- las sensibilidades se ejecutan una a una;
- cada sensibilidad tiene trazabilidad en `runs/<run_id>/...`;
- el reporte final emite un único veredicto de la sección 11;
- y cualquier limitación por falta de score persistido se declara explícitamente.

## 18. Próximos pasos

1. Persistir por sistema en `run_train_mode()` los campos `family_scores`, `family_top1_score` y `family_margin` ya definidos en `build_family_inference_report()` de `02_emergent_geometry_engine.py`.
2. Ejecutar el baseline canónico sobre `runs/tier_a_ext_discrim_20260414_codex_run1`.
3. Ejecutar réplicas one-at-a-time para resolución, hiperparámetros y cohorte.
4. Emitir veredicto único sin reabrir observable ni cohorte.
5. Solo si el veredicto es `SEPARATION_CONFIRMED`, pasar a una discusión física cuidadosamente limitada.
