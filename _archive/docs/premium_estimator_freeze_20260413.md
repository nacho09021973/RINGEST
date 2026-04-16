# Premium Estimator Freeze 2026-04-13

## Estado congelado
- El premium estimator queda fijado como backend operativo con `backend_enabled = true`.
- El premium estimator ya no se considera placeholder: `is_placeholder = false`.
- El existence audit cerrado para esta fase es `SURVIVES`, anclado en `runs/estimator_existence_audit_sensitivity_iter1_20260413/experiment/estimator_existence_audit/outputs/existence_audit_report.json`.
- La comparación full-cohort cerrada para esta fase es `LIMITED_ADVANTAGE`, anclada en `runs/reopen_v1_33event_baseline_vs_premium_final_iter1_20260413/experiment/baseline_vs_premium_multievent/outputs/aggregate_comparison.json`.

## Resultado comparativo fijado
- Cohorte completa evaluada: 33 eventos.
- Ventaja clara del premium: 8 eventos.
- Ventaja limitada del premium: 25 eventos.
- `NO_ADVANTAGE`: 0 eventos.
- `premium_control_separation_count`: 33.
- `premium_signal_class_taxonomy_count`: 33.
- `premium_null_reject_count`: 33.
- No hubo degradación en rechazo de `null` respecto al cierre aprobado de esta línea.
- El veredicto agregado queda fijado en `LIMITED_ADVANTAGE`.

## Alcance del cierre
- El cambio funcional aprobado que sostiene este cierre fue la introducción de una única clase nueva, `moderate_decay`.
- No se añadieron features nuevas.
- No se añadieron dependencias nuevas.
- No cambiaron las reglas de veredicto.
- La línea comparativa baseline vs premium queda cerrada en esta fase y no se abre más tuning dentro del framework actual.

## Cautela de interpretación
- La taxonomía `sharp_decay / moderate_decay / attenuated_decay / broad_signal / null_like` es operativa.
- No debe usarse como taxonomía física fuerte.
- No debe usarse para claims físicos fuertes.
