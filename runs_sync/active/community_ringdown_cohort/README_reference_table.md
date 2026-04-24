# Community Ringdown Reference Table

## Proposito

Esta tabla congela una referencia final, portable y versionable por evento para Ruta B.
Se puede reutilizar manana en otro ordenador sin reinstalar ni rerunear `ringdown`, `pyRingGW` ni otros ecosistemas externos.

Artefacto principal: `runs/community_ringdown_cohort/community_ringdown_reference_table.csv`.

## Politica A/B/C Reutilizada

- La clasificacion se toma tal cual de `runs/community_ringdown_cohort/community_ringdown_tiers.csv`.
- `A`: ancla multipolo local + remanente materializado.
- `B`: remanente materializado pero sin ancla multipolo suficiente en los artefactos inspeccionados.
- `C`: sin remanente suficiente. Hoy no aparece ningun caso en la cohorte congelada.

## Significado de `source_kind`

- `community_ringdown_pilot`: valor tomado del piloto `ringdown` ya parseado.
- `community_ringdown_t0_selected`: valor tomado del barrido de `t0` ya parseado y seleccionado hoy.
- `community_ringdown_single_pass`: valor tomado de una unica corrida H1 ejecutada hoy con el patron base del piloto.
- `literature_anchor`: valor tomado de la cohorte/literatura materializada y usado como ancla congelada.
- `provisional`: valor de literatura usado para eventos cuyo tier sigue siendo provisional.
- `no_frozen_value`: no hay valor congelado suficiente; los campos quedan vacios.

## Criterio De Seleccion

- Prioridad 1: decisiones operativas congeladas hoy.
- Prioridad 2: piloto `ringdown` ya materializado.
- Prioridad 3: ancla de literatura ya materializada en el repo.
- Si una fuente no trae cuantiles `q05/q95` o `selected_t0/duration`, esos campos quedan vacios y se explica en `notes`.

## Casos Con `ringdown` Piloto Directo

- GW150914

## Casos Con `ringdown` y `t0` Seleccionado

- GW170104 usa `delta_t = +0.004 s`.
- GW170814 usa `delta_t = -0.002 s`.

## Casos Con `ringdown` De Una Sola Pasada Hoy

- GW170823, GW190421_213856, GW190503_185404, GW190828_063405

## Eventos Realmente Congelados Con `ringdown`

- GW150914
- GW170104
- GW170814
- GW170823
- GW190421_213856
- GW190503_185404
- GW190828_063405

## Casos Solo Literatura Provisional

- GW190408_181802, GW190512_180714, GW190513_205428, GW190519_153544, GW190521_074359, GW190602_175927, GW190706_222641, GW190708_232457, GW190727_060333, GW190910_112807, GW190915_235702

## Casos Con Tier Todavia Provisional

- GW170823, GW190408_181802, GW190421_213856, GW190503_185404, GW190512_180714, GW190513_205428, GW190519_153544, GW190521_074359, GW190602_175927, GW190706_222641, GW190708_232457, GW190727_060333, GW190828_063405, GW190910_112807, GW190915_235702

## Reutilizacion Offline Manana

- Usar `community_ringdown_reference_table.csv` como tabla canonica de entrada por evento.
- No rerunear `ringdown` para recuperar estos valores; ya estan congelados en el CSV.
- Consultar `source_kind`, `source_artifacts` y `notes` antes de promover un evento a uso mas fuerte downstream.

## Adaptador A Ruta B Operativa

- Script: `tools/community_reference_to_qnm_dataset.py`.
- Input canonico: `runs/community_ringdown_cohort/community_ringdown_reference_table.csv`.
- Output canonico adaptado: `runs/community_ringdown_cohort/qnm_dataset_community_reference.csv`.
- Funcion: convertir la tabla comunitaria congelada al esquema `qnm_dataset.csv` que ya consume `realdata_ringdown_to_stage02_boundary_dataset.py`.
- No rerunea `ringdown`, no invoca `pyRingGW` y no estima valores nuevos: solo deriva campos algebraicos (`omega_re`, `omega_im`, normalizaciones y distancia Kerr-220) desde `f_ringdown_hz`, `damping_hz`, `M_final_Msun` y `chi_final` ya congelados.
- Campos sin soporte directo en la tabla (`amp_abs`, `relative_rms`) quedan vacios; el bridge ya trata `amp_abs` vacio como amplitud unitaria.

## Cobertura De Hoy

- Eventos con piloto directo congelado: 1.
- Eventos con `t0` seleccionado congelado: 2.
- Eventos con una sola pasada H1 hoy: 4.
- Eventos provisionales segun tiers: 15.
