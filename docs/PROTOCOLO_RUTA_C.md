# Protocolo Ruta C — Contraste Kerr

**Versión**: 1.0  
**Fecha de cierre**: 2026-04-24  
**Rama activa**: `claude/ruta-c-kerr-strategy-yoMRj`

---

## Objetivo físico

Cuantificar, evento a evento y globalmente, hasta qué punto los observables QNM
reportados en la literatura para eventos GWTC son consistentes con el espectro
de cuasi-modos de Kerr(M_f, a_f) dentro de los errores publicados.

---

## Input canónico

- **Literatura QNM**: `data/qnm_events_literature.yml`
- **Fuente de referencia Kerr**: tabla Berti 2009 (arXiv:0905.2975, Table VIII),
  interpolación lineal, modo l=m=2, n=0 (fundamental) y n=1 (primera sobretono).
- **Parámetros finales (M_f, chi_f)**: valores medios tomados del mismo YAML,
  extraídos del paper LVK citado en `source_paper` de cada evento.

---

## Observables comparados

| Observable | YAML | Predicción Kerr |
|-----------|------|-----------------|
| f₂₂₀ (Hz) | `f_hz` ± `sigma_f_hz` | `f_kerr_hz` ± `sigma_f_kerr_hz` |
| γ₂₂₀ (Hz) | 1000/`tau_ms` ± propagación de `sigma_tau_ms` | `gamma_kerr_hz` ± `sigma_gamma_kerr_hz` |

---

## Métrica de consistencia

### Residuos estandarizados por evento y observable

```
r_f     = (f_obs - f_Kerr)   / sqrt(σ_f_obs²   + σ_f_Kerr²)
r_gamma = (γ_obs - γ_Kerr)   / sqrt(σ_γ_obs²   + σ_γ_Kerr²)
```

Donde `σ_f_Kerr` y `σ_γ_Kerr` se propagan desde `(σ_M, σ_chi)` por diferencias
finitas sobre la tabla Berti. **Cuando `sigma_M_final_Msun` y `sigma_chi_final`
no estén disponibles en el YAML, se usa `σ_f_Kerr = 0` (estimación puntual del
parámetro): el residuo es conservador en el sentido de que subestima el error
total.**

### Clasificación por evento

| Clase | Criterio en max(|r_f|, |r_γ|) |
|-------|-------------------------------|
| `consistent` | < 1 |
| `marginal` | 1 ≤ max < 2 |
| `tension` | 2 ≤ max < 3 |
| `strong_tension` | ≥ 3 |
| `no_data` | residuos no disponibles |

### Test global

Sobre la distribución conjunta de todos los residuos individuales (r_f y r_gamma):

- **Kolmogorov-Smirnov** vs N(0,1): p > 0.05 como criterio de no-rechazo.
- **Anderson-Darling** vs N(0,1): estadístico < valor crítico al 5%.

Consistencia con N(0,1) indica que los residuos son compatibles con ruido
blanco gaussiano calibrado correctamente.

---

## Limitaciones actuales (versión 1.0)

1. **Faltan `sigma_M_final_Msun` y `sigma_chi_final` en el YAML.** Sin estos,
   `σ_f_Kerr = 0`: el residuo usa únicamente el error observacional en el
   numerador. Los residuos son conservadores (sobrestiman la tensión real si
   la incertidumbre en M_f/chi_f no es despreciable).

2. **Solo modo (2,2,0).** El YAML no contiene modos adicionales. El protocolo
   admite (2,2,1) y (3,3,0) si se añaden con fuente trazable.

3. **N = 19 eventos.** Subcohorte pequeña. Ningún resultado se interpreta
   como confirmación estadística fuerte con este N.

4. **Una sola fuente de literatura.** Todos los eventos citan el mismo paper
   (GWTC-2 TGR). La sensibilidad a la fuente no está auditada todavía.

---

## Scripts del carril

| Script | Función |
|--------|---------|
| `02b_literature_to_dataset.py` | YAML → CSV con predicción Kerr en Hz y residuos |
| `05_kerr_consistency_audit.py` | CSV → tabla de veredictos + test KS/AD global |

---

## Tareas pendientes para completar el protocolo

- [ ] **T4**: Añadir `sigma_M_final_Msun` y `sigma_chi_final` al YAML desde el
  posterior del paper citado (GWTC-2 TGR, Abbott et al. 2021).
- [ ] **T5**: Re-correr `02b` + `05` con sigmas completos y archivar en `runs_sync/`.
- [ ] **T6**: Auditoría de sensibilidad: cambio de fuente, convenciones, modos.
- [ ] **T7**: Documento de conclusión física con afirmaciones defendibles una a una.

---

## Criterio de cierre de fase

Una fase no se cierra si:

- alguna afirmación depende de N < 10 sin marcarse como preliminar;
- los residuos se calculan sin sus errores correspondientes;
- el criterio de consistencia fue definido después de ver los resultados;
- la tensión aparente con Kerr no ha sido auditada contra sistemáticos del input.
