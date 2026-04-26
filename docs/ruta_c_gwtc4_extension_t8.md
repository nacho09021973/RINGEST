# Ruta C / Kerr: estado de la extension GWTC-4 tras T8

Fecha: 2026-04-25

## Resumen corto

T8 amplio el mapa de RINGEST hacia GWTC-4 sin modificar el YAML canonico. El resultado fisico es asimetrico:

- `pSEOBNR` Table 3 aporta un carril verificado de 10 eventos con PE externo completo; sirve como cross-check separado, no como reemplazo del baseline O3.
- `pyRing DS` aporta 22 reducciones ringdown-only `f_22/tau_22`, pero queda bloqueado para auditoria Kerr porque GWOSC API v2 no expone `final_spin` externo para esos O4a.
- No hay base para fusionar `data/qnm_events_literature.yml` todavia.

## Tabla de carriles

| carril | fuente QNM | PE externo | N QNM | N auditado Kerr | estado | uso recomendado |
|---|---|---:|---:|---:|---|---|
| O3 literature baseline T6.6 | YAML canonico de literatura O3 | YAML/GWOSC ya integrado | 19 | 19 | baseline activo | resultado principal Ruta C/Kerr |
| GWTC-4 pSEOBNR T8.1/T8.2a | GWTC-4 Tests of GR III Table 3 pSEOBNR | GWOSC API v2 para `M_final`, `chi_final`, `z` | 17 usable main | 10 | cross-check verificado parcial | sensibilidad a metodo y 4 eventos nuevos completos |
| GWTC-4 pyRing DS T8.3/T8.4 | pyRing O4a DS posterior `f_22/tau_22` | GWOSC API v2 incompleto: falta `final_spin` | 22 | 0 | QNM-ready, PE-blocked | archivar como cohorte ringdown-only pendiente de PE |

## Resultados pSEOBNR

Artefactos:

- `runs_sync/active/gwtc4_pseobnr_ingest/gwtc4_pseobnr_event_map.csv`
- `runs_sync/active/kerr_audit_gwtc4_pseobnr_t82a_verified/kerr_audit_summary.json`
- `runs_sync/active/kerr_audit_gwtc4_pseobnr_t82a_verified/kerr_audit_table.csv`
- `runs_sync/active/kerr_audit_compare_t66_vs_t82a/comparison_summary.json`
- `runs_sync/active/kerr_audit_compare_t66_vs_t82a/comparison_notes.md`

Conteos Table 3:

- eventos Table 3 pSEOBNR: 19
- `usable_main`: 17
- excluidos por asterisco LVK: 2 (`GW191109_010717`, `GW200208_130117`)
- `usable_main` con PE completo GWOSC: 10
- `usable_main` bloqueados por PE incompleto: 7
- ya presentes en YAML canonico actual dentro de `usable_main`: 6
- nuevos potenciales para RINGEST dentro de `usable_main`: 11
- nuevos completos que entraron en T8.2a: 4

Eventos nuevos completos en T8.2a:

- `GW190630_185205`
- `GW200129_065458`
- `GW200224_222234`
- `GW200311_115853`

Eventos O4a pSEOBNR bloqueados por `final_spin = NO_VERIFICADO`:

- `GW230628_231200`
- `GW230914_111401`
- `GW230927_153832`
- `GW231028_153006`
- `GW231102_071736`
- `GW231206_233901`
- `GW231226_101520`

Auditoria T8.2a:

- `N_events = 10`
- `N_mode_rows = 10`
- verdicts por evento: `consistent = 10`
- verdicts por modo: `consistent = 10`
- `residual_mean = 0.2341`
- `residual_std = 0.4053`
- `KS stat = 0.3403`
- `KS p-value = 0.0143`
- `KS consistent_with_normal = false`
- `AD stat = 0.3981`
- `AD critical 5% = 0.721`
- `AD consistent_with_normal_5pct = true`

Comparacion T6.6 vs T8.2a:

- T6.6: 19 eventos, verdicts `consistent = 13`, `marginal = 6`
- T8.2a: 10 eventos, verdicts `consistent = 10`
- solapados: 6 eventos
- nuevos que entraron en T8.2a frente a T6.6: 4 eventos
- cambios de residual maximo en solapados: 4 mejoran, 2 empeoran levemente
- nota especial: `GW190519_153544` aparece en `qnm_dataset.csv` T8.2a pero no en `qnm_dataset_220.csv`; `kerr_220_distance = 0.153954`

Interpretacion limitada: T8.2a no muestra outliers Kerr en el subconjunto pSEOBNR verificado. Esto no es evidencia fuerte por N pequeno ni sustituye el baseline O3; mide sensibilidad a una fuente QNM/PE distinta.

## Resultados pyRing DS

Artefactos:

- `runs_sync/active/gwtc4_pyring_inspection/inspection_notes.md`
- `runs_sync/active/gwtc4_pyring_ds_reduction/pyring_ds_reduction_table.csv`
- `runs_sync/active/gwtc4_pyring_ds_reduction/pyring_ds_reduction_notes.md`

Inspeccion T8.3:

- pyRing O4a catalog events: 22
- overlap con T6.6: 0
- overlap con T8.2a verificado: 0
- overlap con mapa pSEOBNR GWTC-4: 7 eventos
- `DS` contiene `f_22` y `tau_22`, no contiene `Mf/af`
- `Kerr` y `KerrPostmerger` contienen `Mf/af`, pero no se usan en el baseline DS para evitar circularidad en auditoria Kerr

Reduccion T8.4:

- eventos O4a DS: 22
- QNM completos: 22
- `SOURCE_OK`: 0
- `PE_INCOMPLETE`: 22
- `QNM_INCOMPLETE`: 0
- causa unica de bloqueo: falta `final_spin` en GWOSC API v2 para todos los eventos inspeccionados
- runs PE consultados con `final_spin`: 0 para cada evento

No se corre auditoria Kerr sobre pyRing DS porque faltan `chi_final` externos. Reinterpretar DS como tension Kerr sin `M_f/chi_f` externo mezclaria un observable ringdown-only con una referencia Kerr no verificada. Usar `Mf/af` de pyRing Kerr/KerrPostmerger seria otro carril autocontenido, no el baseline DS.

## Decision provisional

- No fusionar `data/qnm_events_literature.yml`.
- Mantener T6.6 como baseline canonico O3/literatura.
- Usar T8.2a pSEOBNR como cross-check separado y parcial.
- No usar eventos pSEOBNR marcados con asterisco LVK en el main result.
- Archivar pyRing DS como cohorte QNM-ready pero PE-blocked.
- No mezclar `pSEOBNR`, `pyRing DS`, `pyRing Kerr` y `pyRing KerrPostmerger` en una misma afirmacion fisica.

## Datos pendientes

- `final_spin` externo para los eventos O4a en GWOSC API v2 o en una tabla PE oficial equivalente.
- Politica explicita para O4a pSEOBNR si se acepta `chi_f` de Table 3 en un carril autocontenido.
- Politica separada para un posible carril pyRing Kerr/KerrPostmerger autocontenido.
- Revision manual antes de promover los 4 nuevos pSEOBNR completos al YAML canonico.

## Recomendacion para paper/T7

Presentar T8 como extension y estudio de sensibilidad a metodo, no como resultado principal. La frase defensible es:

> RINGEST conserva un baseline O3/literatura auditado y anade una extension GWTC-4 separada: pSEOBNR produce un cross-check verificado de 10 eventos sin outliers Kerr, mientras que pyRing DS queda reducido en QNM pero bloqueado por PE externo incompleto.

No vender la desaparicion de marginales en T8.2a como evidencia fuerte: el cambio mezcla fuente QNM, errores y PE, y N=10 es pequeno.

## Dudas dejadas intactas

- Si la ausencia de `final_spin` O4a en GWOSC API v2 es temporal o estructural del release.
- Si conviene crear un carril autocontenido pSEOBNR Table 3 usando `chi_f` de la propia tabla.
- Si conviene crear un carril autocontenido pyRing Kerr/KerrPostmerger y declararlo explicitamente no comparable con el baseline DS.
- Base exacta de los `lnb`/evidences pyRing: no afecta la reduccion DS `f_22/tau_22`, pero queda no verificada.
