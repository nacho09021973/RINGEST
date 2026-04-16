# Pipeline State Freeze 2026-04-13

Este documento deja una foto maestra, prudente y ejecutiva, del estado global
actual del pipeline BASURIN tras los cierres recientes. No reabre tuning ni
modifica la lógica científica o contractual ya congelada en los artefactos
referidos.

## Stage 04 semantic freeze

- `correlator_structure` ya no debe leerse como test físico de power-law.
- `has_power_law` y `log_slope` no deben leerse como evidencia física fuerte.
- El contrato operativo de Stage 04 queda reinterpretado como
  `RELAXED_NON_DISCRIMINANT` dentro de la ventana finita de análisis.
- Referencia principal:
  `docs/stage04_correlator_semantics_tail_strict.md`

## Decay type discrimination

- La línea `decay_type_discrimination` queda cerrada como experimento trazable
  BASURIN-ready bajo:
  `runs/basurin_decay_type_tail_strict_20260413/experiment/decay_type_discrimination/`
- Resultado agregado de la cohorte canónica de 33 eventos:
  `n_exponential_preferred = 16`,
  `n_powerlaw_preferred = 10`,
  `n_neither_good = 7`,
  `powerlaw_majority_observed = false`,
  `exponential_tilt_observed = true`.
- Lectura de programa: el experimento sirve como evidencia de gobernanza
  semántica para relajar la lectura de Stage 04, no como claim físico fuerte.
- Referencias útiles:
  `docs/stage04_correlator_semantics_tail_strict.md`
  `runs/basurin_decay_type_tail_strict_20260413/experiment/decay_type_discrimination/outputs/decay_type_discrimination_33_event_canonical_tail_strict.json`

## Estimator existence audit

- La secuencia histórica relevante quedó cerrada como `FAILS -> BOUNDED -> SURVIVES`.
- El estado vigente es `SURVIVES`, lo que fija que el premium existe
  operativamente dentro del marco actual.
- Referencia trazable:
  `runs/estimator_existence_audit_sensitivity_iter1_20260413/experiment/estimator_existence_audit/outputs/existence_audit_report.json`

## Premium estimator freeze

- El premium queda congelado como backend operativo:
  `backend_enabled = true`.
- El premium ya no es placeholder:
  `is_placeholder = false`.
- El freeze documental está fijado en:
  `docs/premium_estimator_freeze_20260413.md`
- La comparación full-cohort cerrada para 33 eventos queda en
  `LIMITED_ADVANTAGE`, con:
  `NO_ADVANTAGE = 0`,
  `LIMITED_ADVANTAGE = 25`,
  `CLEAR_ADVANTAGE = 8`.
- Lectura de programa: el premium aporta valor limitado pero estable; no se
  recomienda más tuning local dentro del framework actual.
- Referencias útiles:
  `runs/reopen_v1_33event_baseline_vs_premium_final_iter1_20260413/experiment/baseline_vs_premium_multievent/outputs/aggregate_comparison.json`
  `estimators_registry.json`

## Current program decisions

- Las líneas cerradas en esta fase son:
  reinterpretación semántica de Stage 04,
  `decay_type_discrimination`,
  `estimator_existence_audit`,
  freeze del `premium_estimator`,
  y comparación full-cohort `baseline vs premium`.
- No se reabre tuning local.
- No se cambian reglas de veredicto.
- No se elevan claims físicos a partir de Stage 04 ni de la taxonomía operativa
  del premium.
- La recomendación vigente es retorno al roadmap principal (`RETURN_TO_MAIN_ROADMAP`).
