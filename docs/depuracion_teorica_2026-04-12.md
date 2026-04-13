# Depuración epistemológica del material teórico RINGEST/BASURIN

**Fecha:** 2026-04-12  
**Propósito:** Base operativa para orquestación, no ensayo especulativo  
**Criterio de éxito:** Dejar al orquestador con base conceptual depurada para decidir el siguiente experimento

---

## 1. Resumen ejecutivo

El pipeline ha procesado 90 eventos y producido dos cohortes que pasan Stages 03/04 con resultados operativamente indistinguibles. La diferencia entre ellas es de soporte en Stage 02 (`G2_large_x`), no de estructura física downstream.

**Hallazgo central:** El contrato actual de `correlator_structure` usa un test log-log diseñado para power-law, pero el observable G2 de ringdown real tiene decaimiento que puede ser exponencial. Este mismatch es el cuello conceptual más urgente: invalida cualquier interpretación fuerte basada en `has_power_law` o `log_slope`.

**Recomendación operativa:** El siguiente experimento debe ser un test robusto que discrimine entre decaimiento exponencial genuino y ajuste espurio tipo power-law en ventana finita. Todo lo demás (hyperscaling, zh_pred, POSSIBLY_EINSTEIN_WITH_MATTER) debe quedar en espera hasta resolver este problema.

---

## 2. Hechos del pipeline que deben preservarse

Estos son hechos operativos verificables en artefactos congelados. No requieren interpretación.

| Hecho | Fuente | Tipo |
|-------|--------|------|
| Cohorte total candidata: 90 eventos | `200_event_candidate_cohort.json` | **Hecho del pipeline** |
| Pass Stage 02 original (xmax=6): 27 eventos | `90_event_gate_split_summary.json` | **Hecho del pipeline** |
| Rescatados por corrección V3/V4: 8 eventos | `8_event_gamma_dom_v2_stage02_input/` | **Hecho del pipeline** |
| Cohorte canónica efectiva: 33 eventos | `33_event_effective_contract_pass_summary.json` | **Hecho del pipeline** |
| Cohorte OOD explícita: 55 eventos | `55_event_effective_ood_inference/` | **Hecho del pipeline** |
| Ambas cohortes pasan Stage 03 y 04 | `ood_vs_canonical_comparison_summary.json` | **Hecho del pipeline** |
| 100% de geometrías clasificadas como `POSSIBLY_EINSTEIN_WITH_MATTER` | Stage 03 summaries | **Hecho del pipeline** |
| Ratio `has_power_law=true`: 17/33 (canónico), 37/55 (OOD) | Stage 04 summaries | **Hecho del pipeline** |
| `family_pred=hyperscaling` en 8/33 eventos canónicos | `emergent_geometry_summary.json` | **Hecho del pipeline** |
| `zh_pred ≈ 1.712` para los 8 eventos hyperscaling | `emergent_geometry_summary.json` | **Hecho del pipeline** |
| `G2_large_x` demoted de CRITICAL a OOD_SIGNAL (V4) | `g2_demotion_governance_decision_2026-04-12.json` | **Hecho del pipeline** |

---

## 3. Afirmaciones a conservar

### A1. G2 captura estructura espacial real en el correlador

**Clasificación:** Hecho del pipeline  
**Evidencia:** `has_spatial_structure=true` para 33/33 canónicos y 55/55 OOD  
**Utilidad:** Confirma que el observable no es ruido constante

### A2. La diferencia entre cohorte canónica y OOD es de soporte representacional, no de física downstream

**Clasificación:** Hecho del pipeline  
**Evidencia:** Stage 03/04 scores son estadísticamente indistinguibles (delta < 0.01)  
**Utilidad:** Justifica la demotación de `G2_large_x` a señal OOD no excluyente

### A3. El contrato de correlador relaja `has_power_law` para ringdown inference

**Clasificación:** Hecho del pipeline  
**Evidencia:** `contract_mode=ringdown_inference_relaxed_v1` en todos los contratos Stage 04  
**Utilidad:** Documenta que la relajación es intencional, no un bug

### A4. Las ecuaciones simbólicas R(z) tienen estructura no trivial

**Clasificación:** Hecho del pipeline  
**Evidencia:** PySR produce ecuaciones con R² > 0.95, complejidad 5-13  
**Utilidad:** El bulk reconstruido no es constante; hay información codificada

---

## 4. Afirmaciones a rebajar

### B1. "El modelo predice familia hyperscaling para ciertos eventos"

**Formulación original:** El modelo identifica eventos cuya geometría bulk es tipo hyperscaling  
**Formulación rebajada:** El modelo produce `family_pred=hyperscaling` para 8/33 eventos; esto es una etiqueta de clasificación del modelo, no una identificación física de régimen hyperscaling  
**Clasificación rebajada:** Hipótesis abierta / no demostrada  
**Razón del rebajado:** No hay validación independiente de que esos eventos sean físicamente hyperscaling

### B2. "zh_pred ≈ 1.7 indica posición del horizonte"

**Formulación original:** El modelo infiere la posición del horizonte en z ≈ 1.7 para eventos hyperscaling  
**Formulación rebajada:** El modelo produce `zh_pred ≈ 1.712` para los 8 eventos hyperscaling; este valor es un atractor del modelo entrenado, no necesariamente una posición física de horizonte  
**Clasificación rebajada:** Hipótesis abierta / no demostrada  
**Razón del rebajado:** La convergencia a un valor fijo sugiere bias del entrenamiento, no señal física

### B3. "Las geometrías reconstruidas son Einstein con materia"

**Formulación original:** Stage 03 demuestra que las geometrías satisfacen ecuaciones de Einstein con tensor de stress-energy no nulo  
**Formulación rebajada:** Stage 03 clasifica las geometrías como `POSSIBLY_EINSTEIN_WITH_MATTER` porque no satisfacen R=constante (vacío) pero sí tienen R<0 y estructura simbólica compatible  
**Clasificación rebajada:** Interpretación teórica compatible  
**Razón del rebajado:** "Posiblemente" no es "demostrado"; la etiqueta indica compatibilidad, no confirmación

### B4. "La curvatura negativa es una señal física robusta"

**Formulación original:** R<0 en todas las geometrías indica curvatura negativa genuina  
**Formulación rebajada:** El modelo produce R<0 para 100% de las geometrías; esto es consistente con el prior de entrenamiento (sandbox holográfico tiene R<0) y puede reflejar bias más que señal  
**Clasificación rebajada:** Interpretación teórica compatible  
**Razón del rebajado:** Sin control positivo (eventos con R>0 esperado), no se puede distinguir bias de señal

---

## 5. Afirmaciones a eliminar

### C1. "El pipeline detecta geometría de agujero negro de Kerr"

**Por qué eliminar:** El modelo no tiene Kerr QNMs en el dataset de entrenamiento actual; `family_pred=kerr` es una etiqueta heredada de la arquitectura, no una detección calibrada

### C2. "El pass de Stage 03/04 confirma que la física holográfica aplica"

**Por qué eliminar:** Los contratos Stage 03/04 están relajados (`ringdown_inference_relaxed_v1`); el pass es operativo, no físico. Pasar el gate solo significa que no hay violaciones graves de regularidad/causalidad.

### C3. "La coherencia entre cohorte canónica y OOD valida el modelo"

**Por qué eliminar:** Ambas cohortes producen resultados similares porque el modelo trata todo como ringdown inference con contratos relajados. La similitud no es validación; puede ser señal de que el modelo no distingue entre datos in-distribution y OOD.

### C4. "El log_slope del correlador mide la dimensión conforme Δ"

**Por qué eliminar:** El test log-log asume decaimiento power-law. Si el decaimiento real es exponencial, el `log_slope` no tiene interpretación como dimensión conforme.

### C5. "hyperscaling es una familia física detectada en datos LIGO"

**Por qué eliminar:** hyperscaling es una categoría del sandbox de entrenamiento. El modelo la predice, pero no hay evidencia de que datos de ringdown LIGO contengan física hyperscaling.

---

## 6. Lectura mínima útil de G2_ringdown

### Qué sí es defendible

1. **G2 tiene estructura espacial no trivial.** El observable no es ruido constante; hay variación sistemática en `x` que sobrevive al filtrado y normalización.

2. **G2_large_x captura una diferencia de morfología de cola.** Los eventos con G2 alto en x_max=6 tienen comportamiento de decaimiento cualitativamente diferente. Esta diferencia es real y reproducible.

3. **G2_large_x no predice daño contractual downstream.** Eventos con G2_large_x fuera de soporte pasan Stage 03/04 igual que eventos in-support. La exclusión original era conservadora, no necesaria.

### Qué no puede afirmarse todavía

1. **No se puede afirmar que G2 sea un correlador CFT.** El observable viene de ESPRIT sobre datos de ringdown; su conexión con correladores de teoría conforme es una analogía operativa, no una correspondencia establecida.

2. **No se puede afirmar que el decaimiento de G2 sea power-law.** Solo 17/33 eventos canónicos pasan el test `has_power_law=true` con los umbrales actuales. La mayoría no.

3. **No se puede afirmar que log_slope mida una cantidad física.** Sin saber si el decaimiento es exponencial o power-law, el valor numérico de `log_slope` es interpretacionalmente ambiguo.

---

## 7. Riesgo central: exponencial vs power-law

### Por qué este riesgo es central

El contrato `correlator_structure` hace un ajuste lineal en log-log:
```
log(G2) = m * log(x) + b
```

Si G2 tiene decaimiento power-law genuino: `G2(x) ~ x^{-2Δ}`, entonces `m = -2Δ` y el ajuste es físicamente significativo.

Si G2 tiene decaimiento exponencial: `G2(x) ~ exp(-αx)`, entonces:
```
log(G2) = -αx + const  (NO lineal en log(x))
```

En una ventana finita [x_min, x_max], un exponencial puede ajustarse razonablemente bien con una recta en log-log, produciendo un `log_slope` y `correlation_quality` espurios.

### Qué invalida interpretar demasiado fuerte el contrato actual

1. **El test no distingue entre los dos tipos de decaimiento.** Un R² de 0.4-0.5 es compatible tanto con power-law ruidoso como con exponencial en ventana finita.

2. **El ringdown físico tiene decaimiento exponencial.** Las señales QNM decaen como `exp(-t/τ)`, no como power-law. Si G2 hereda esta estructura, esperar power-law es físicamente incorrecto.

3. **La relajación del contrato oculta el problema.** Al no requerir `has_power_law=true` para pasar, el pipeline evita el fail pero no resuelve la ambigüedad interpretativa.

### Qué debería cambiar en el siguiente experimento

1. **Ajustar ambos modelos explícitamente.** Calcular `fit_exponential(G2, x)` además de `fit_power_law(G2, x)`.

2. **Comparar con criterio de selección de modelo.** Usar BIC o AIC para determinar cuál modelo describe mejor los datos.

3. **Reportar el resultado de la comparación.** Un nuevo campo `decay_type: "exponential" | "power_law" | "inconclusive"` con el score de selección.

4. **Evaluar implicaciones downstream.** Si la mayoría de eventos son exponenciales, la analogía con correladores CFT pierde fuerza.

---

## 8. Cómo interpretar OOD sin sobrerreaccionar

### Qué significa que 55 sea OOD en soporte pero sobreviva 03/04

1. **Significado operativo:** Los 55 eventos tienen `G2_large_x` fuera del rango de entrenamiento del modelo Stage 02. El modelo los procesa igual, pero con menor confianza teórica en las predicciones.

2. **Significado para la validación:** Los contratos Stage 03/04 no son lo suficientemente discriminativos para separar OOD de canónico. Esto puede indicar que:
   - Los contratos están demasiado relajados
   - La diferencia de soporte no afecta las métricas downstream
   - El modelo generaliza bien (interpretación optimista)
   - El modelo no es sensible a la diferencia (interpretación pesimista)

### Interpretación prudente para el orquestador

1. **No fusionar las cohortes retroactivamente.** Mantener la distinción canónico/OOD en metadata aunque pasen los mismos gates.

2. **No afirmar que OOD "valida" el modelo.** El pass de OOD no es evidencia de robustez; es evidencia de que los contratos no discriminan.

3. **Usar OOD para exploración, no para claims.** Cualquier hallazgo en la cohorte OOD debe replicarse en la canónica antes de considerarse robusto.

4. **El next step correcto no es expandir la cohorte, sino fortalecer los contratos.** Antes de incluir más eventos, asegurar que los contratos detecten diferencias reales.

---

## 9. Cómo interpretar hyperscaling sin vender humo

### Qué valor conceptual puede tener esta salida

1. **Como señal de agrupamiento.** Los 8 eventos con `family_pred=hyperscaling` forman un cluster en el espacio latente del modelo. Esto puede indicar similitud morfológica en el input.

2. **Como indicador de comportamiento fuera de lo común.** Si kerr es el caso "default" y hyperscaling es el caso "alternativo", la predicción hyperscaling señala eventos que el modelo trata diferente.

3. **Como pista para investigación dirigida.** Los 8 eventos pueden compartir características astrofísicas (masa, spin, SNR) que merecen auditoría separada.

### Qué sería humo si se afirmara ahora

1. **"Estos eventos muestran física hyperscaling."** Hyperscaling es una propiedad de métricas holográficas; no hay ninguna razón para esperar que datos de LIGO contengan esta estructura.

2. **"zh_pred = 1.7 es la posición del horizonte."** El valor convergente sugiere un atractor del modelo, no una medición física. Sin calibración independiente, el número no tiene significado.

3. **"La familia predicha discrimina regímenes físicos."** La etiqueta viene del entrenamiento en sandbox; su aplicabilidad a datos reales no está demostrada.

### Recomendación operativa

Registrar `family_pred` y `zh_pred` en metadata para trazabilidad, pero no usar estos campos para decisiones de gobernanza ni para claims en documentos externos hasta tener validación cruzada.

---

## 10. Cómo interpretar POSSIBLY_EINSTEIN_WITH_MATTER

### Qué lectura operativa es aceptable

1. **"Stage 03 no encuentra R=constante."** Las ecuaciones simbólicas producen R(z) variable, no el caso especial de vacío Einstein donde R=-2Λ/d.

2. **"Stage 03 encuentra R<0 consistentemente."** El escalar de curvatura es negativo en la grilla bulk, compatible con geometría tipo anti-de Sitter deformada.

3. **"El veredicto es una clasificación operativa."** POSSIBLY_EINSTEIN_WITH_MATTER es una etiqueta de triage, no un teorema. Indica "no es vacío, no es claramente non-Einstein, queda en bucket intermedio."

### Qué lectura física fuerte no es aceptable

1. **"Las geometrías reconstruidas satisfacen ecuaciones de Einstein."** No se verifican las ecuaciones de campo; se verifica una ecuación simbólica ajustada a R(z).

2. **"Hay materia en el bulk."** La etiqueta "with_matter" significa "R no es constante", no que se haya identificado un tensor de stress-energy.

3. **"Esto confirma la correspondencia holográfica."** El pipeline usa herramientas inspiradas en holografía; el pass de contratos no establece correspondencia matemática.

### Lectura recomendada para el orquestador

`POSSIBLY_EINSTEIN_WITH_MATTER` significa: "no violamos regularidad ni causalidad, R varía pero es negativo, no somos vacío puro." Usarlo como bucket de clasificación, no como claim físico.

---

## 11. Siguiente experimento correcto

### Propuesta: Test de discriminación exponencial vs power-law

**Justificación:** Este es el siguiente cuello conceptual real porque:

1. **Invalida interpretaciones downstream.** Si G2 es exponencial, toda la analogía con correladores CFT (que son power-law) pierde base.

2. **Es testeable con los observables actuales.** No requiere nuevo pipeline ni nuevo modelo; solo análisis adicional sobre G2 existente.

3. **Tiene implicación de gobernanza clara.** Si la mayoría de eventos son exponenciales, hay que revisar la semántica de `log_slope` y posiblemente cambiar el contrato de correlador.

4. **Es el prerequisito para cualquier claim holográfico.** Sin saber la forma funcional del decaimiento, afirmaciones sobre dimensión conforme o estructura CFT son prematuras.

### Stage o contrato donde debe absorberse

**Opción A (recomendada):** Nuevo sub-contrato en Stage 04, `decay_type_discrimination`, que corre después de `correlator_structure` y agrega:
- `decay_type: "exponential" | "power_law" | "inconclusive"`
- `bic_exponential`, `bic_power_law`
- `bic_delta` (diferencia)

**Opción B:** Reemplazar el contrato `correlator_structure` por uno que haga ambos ajustes y reporte el ganador.

### Observable(s) a usar

- `G2` (correlador existente)
- `x_grid` (grilla espacial existente)

### Comparación mínima

Para cada evento:
1. Ajustar `G2(x) = A * x^{-m}` (power-law)
2. Ajustar `G2(x) = B * exp(-α * x)` (exponencial)
3. Calcular BIC para cada ajuste: `BIC = n * log(RSS/n) + k * log(n)`
4. Reportar `decay_type` según `min(BIC_exp, BIC_pow)`
5. Si `|BIC_exp - BIC_pow| < 2`, reportar `inconclusive`

### Hipótesis nula a testear

H0: "La mayoría de eventos canónicos (33) tienen decaimiento mejor descrito por power-law que por exponencial."

Si H0 se rechaza (mayoría exponencial o inconcluso), la interpretación de `log_slope` como dimensión conforme debe abandonarse.

---

## 12. Artefacto nuevo recomendado

### Nombre
`runs/reopen_v1/decay_type_discrimination_33_event_canonical.json`

### Estructura
```json
{
  "version": "1.0",
  "scope": "33_event_effective_contract_pass",
  "test_date": "2026-04-XX",
  "summary": {
    "n_exponential": <int>,
    "n_power_law": <int>,
    "n_inconclusive": <int>,
    "h0_rejected": <bool>,
    "dominant_decay_type": "exponential" | "power_law" | "mixed"
  },
  "events": [
    {
      "name": "GW150914__ringdown",
      "decay_type": "exponential" | "power_law" | "inconclusive",
      "bic_exponential": <float>,
      "bic_power_law": <float>,
      "bic_delta": <float>,
      "fit_params_exp": {"B": <float>, "alpha": <float>},
      "fit_params_pow": {"A": <float>, "m": <float>},
      "r2_exp": <float>,
      "r2_pow": <float>
    },
    ...
  ],
  "governance": {
    "if_majority_exponential": "Revisar semántica de log_slope; considerar deprecar interpretación como dimensión conforme",
    "if_majority_power_law": "Mantener contrato actual; log_slope puede interpretarse como proxy de Δ",
    "if_mixed": "Estratificar cohorte por decay_type; analizar correlación con parámetros astrofísicos"
  }
}
```

### Criterio de congelación

El artefacto se congela cuando:
1. Los 33 eventos canónicos han sido procesados
2. El resumen incluye decisión de H0
3. Se documenta la implicación para `correlator_structure`

---

## Anexo: Checklist de validación para el orquestador

Antes de aprobar cualquier claim teórico nuevo, verificar:

- [ ] ¿Es un hecho del pipeline verificable en artefactos?
- [ ] ¿Es una interpretación teórica compatible que no sobrepasa la evidencia?
- [ ] ¿Es una hipótesis abierta claramente etiquetada como tal?
- [ ] ¿Se ha verificado que el decaimiento exponencial vs power-law está resuelto?
- [ ] ¿Las afirmaciones sobre family_pred/zh_pred tienen validación independiente?
- [ ] ¿El pass de Stage 03/04 se usa como clasificación operativa, no como demostración física?
- [ ] ¿Los artefactos citados existen y son consistentes con las afirmaciones?

Si alguna respuesta es "no", el claim debe rebajarse o eliminarse antes de documentación externa.
