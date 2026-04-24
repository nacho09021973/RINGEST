# T6 - Auditoria input Ruta C outliers Kerr

Fecha: 2026-04-24

## Resumen corto

Los tres outliers de `runs_sync/active/kerr_audit_20260424_zfix/` no quedan como candidatos robustos de tension Kerr. La auditoria manual-dirigida encuentra que `f_hz` y `tau_ms` del YAML coinciden con Table IX / IMR del paper TGR GWTC-2 y estan en marco detector/redshifted, pero los `z` activos en `data/qnm_events_literature.yml` no coinciden con GWOSC/GWTC-2.1 ni con las masas finales redshifted de Table I del paper.

El fallo no esta en Stage 02/03/04 ni en thresholds. Es fallo de homogeneizacion del input fisico: el pipeline calcula `M_detector = M_source * (1 + z)` y para estos tres eventos usa `z` demasiado altos, inflando `M_detector`, bajando `f_kerr_hz` y creando `residual_f > 3`.

No se modifica el YAML en esta auditoria.

## Mapa de rutas

- YAML activo: `data/qnm_events_literature.yml`
- Builder Ruta C: `02b_literature_to_dataset.py`
- Auditor Kerr: `05_kerr_consistency_audit.py`
- Protocolo Ruta C: `docs/PROTOCOLO_RUTA_C.md`
- Run auditado: `runs_sync/active/kerr_audit_20260424_zfix/`
- Dataset auditado: `runs_sync/active/kerr_audit_20260424_zfix/qnm_dataset.csv`
- Tabla auditada: `runs_sync/active/kerr_audit_20260424_zfix/kerr_audit_table.csv`
- Resumen auditado: `runs_sync/active/kerr_audit_20260424_zfix/kerr_audit_summary.json`

## Fuentes verificadas

- QNM publicados: Abbott et al., "Tests of General Relativity with Binary Black Holes from the second LIGO-Virgo Gravitational-Wave Transient Catalog", Phys. Rev. D 103, 122002, DOI `10.1103/PhysRevD.103.122002`; DCC `LIGO-P2000438`.
- Locator QNM: Table IX, columnas IMR, "redshifted frequency [Hz]" y "redshifted damping time [ms]".
- Masa/spin/redshift de catalogo: GWOSC `GWTC-2.1-confident`, evento `v2`, PE update `C01:Mixed`.
- Cross-check masa detector: Table I del paper TGR GWTC-2 reporta `(1+z) M_f`, no `M_f_source`.

## Tabla comparativa

| event | YAML f/tau | YAML M_source, chi, z | M_detector usado | fuente QNM | fuente catalogo verificada | M_detector fuente | Kerr audit zfix | diagnostico |
|---|---:|---:|---:|---|---|---:|---|---|
| GW190519_153544 | `127.0 +- 9.0 Hz`, `9.5 +- 1.6 ms` | `100.0`, `0.79`, `0.822` | `182.200` | Table IX IMR: `127 +9/-9 Hz`, `9.5 +1.7/-1.5 ms` | GWOSC v2: `M_f=100.0`, `chi_f=0.79`, `z=0.45` | `145.0`; TGR Table I `(1+z)M_f=146.8` | `f_kerr=94.09`, `r_f=3.66`, `verdict=strong_tension` | input z incompatible |
| GW190521_074359 | `198.0 +- 7.0 Hz`, `5.4 +- 0.4 ms` | `72.6`, `0.71`, `0.352` | `98.155` | Table IX IMR: `198 +7/-7 Hz`, `5.4 +0.4/-0.4 ms` | GWOSC v2: `M_f=72.6`, `chi_f=0.71`, `z=0.21` | `87.846`; TGR Table I `(1+z)M_f=88.0` | `f_kerr=165.99`, `r_f=4.57`, `r_gamma=3.33`, `verdict=strong_tension` | input z incompatible |
| GW190910_112807 | `177.0 +- 8.0 Hz`, `5.9 +- 0.65 ms` | `74.4`, `0.69`, `0.438` | `106.987` | Table IX IMR: `177 +8/-8 Hz`, `5.9 +0.8/-0.5 ms` | GWOSC v2: `M_f=74.4`, `chi_f=0.69`, `z=0.29` | `95.976`; TGR Table I `(1+z)M_f=97.0` | `f_kerr=150.30`, `r_f=3.34`, `verdict=strong_tension` | input z incompatible |

Notas:

- Los campos `sigma_f_hz` y `sigma_tau_ms` del YAML no son 1 sigma verificado. Son semianchos/armonizaciones de intervalos creibles al 90% de Table IX.
- El YAML activo no conserva `source_doi`, `source_url`, `source_locator`, `analysis_method`, `credible_interval` ni `notes`; esos campos existen en `docs/Recopilación de Datos de Ringdown GW.md`, pero no en el YAML usado por `02b`.
- La coincidencia de `M_final_Msun` y `chi_final` con GWOSC v2 no prueba que sean el mismo posterior usado para Table IX; esto queda como `NO_VERIFICADO`.

## Diagnostico por evento

### GW190519_153544

- `YAML_VALUES`: `f_hz=127.0`, `sigma_f_hz=9.0`, `tau_ms=9.5`, `sigma_tau_ms=1.6`, `M_final_Msun=100.0`, `chi_final=0.79`, `z=0.822`, `source_paper=TGR GWTC-2`.
- `KERR_AUDIT_VALUES`: `f_kerr_hz=94.0896489760075`, `residual_f=3.6567056693325006`, `residual_gamma=2.0786963493778874`, `verdict_kerr=strong_tension`, `kerr_sigma_source=point_estimate`.
- `SOURCE_CHECK`: f/tau verificados en Table IX/IMR. `M_final_Msun` y `chi_final` coinciden con GWOSC v2 update. `z` no coincide: fuente verificada `z=0.45`, YAML `z=0.822`. Table I TGR da `(1+z)M_f=146.8`, pero el YAML produce `182.2`.
- `INCONSISTENCY_TYPE`: `NON_SIMULTANEOUS_POSTERIORS`
- `CONFIDENCE`: alta
- `PROPOSED_ACTION`: `correct_yaml_after_source_confirmation`
- `DECISION`: `INPUT_HOMOGENEIZATION_FAILURE`

### GW190521_074359

- `YAML_VALUES`: `f_hz=198.0`, `sigma_f_hz=7.0`, `tau_ms=5.4`, `sigma_tau_ms=0.4`, `M_final_Msun=72.6`, `chi_final=0.71`, `z=0.352`, `source_paper=TGR GWTC-2`.
- `KERR_AUDIT_VALUES`: `f_kerr_hz=165.99364034612444`, `residual_f=4.572337093410795`, `residual_gamma=3.3335108893951415`, `verdict_kerr=strong_tension`, `kerr_sigma_source=point_estimate`.
- `SOURCE_CHECK`: f/tau verificados en Table IX/IMR. `M_final_Msun` y `chi_final` coinciden con GWOSC v2 update. `z` no coincide: fuente verificada `z=0.21`, YAML `z=0.352`. Table I TGR da `(1+z)M_f=88.0`, pero el YAML produce `98.155`.
- `INCONSISTENCY_TYPE`: `NON_SIMULTANEOUS_POSTERIORS`
- `CONFIDENCE`: alta
- `PROPOSED_ACTION`: `correct_yaml_after_source_confirmation`
- `DECISION`: `INPUT_HOMOGENEIZATION_FAILURE`

### GW190910_112807

- `YAML_VALUES`: `f_hz=177.0`, `sigma_f_hz=8.0`, `tau_ms=5.9`, `sigma_tau_ms=0.65`, `M_final_Msun=74.4`, `chi_final=0.69`, `z=0.438`, `source_paper=TGR GWTC-2`.
- `KERR_AUDIT_VALUES`: `f_kerr_hz=150.30433732044813`, `residual_f=3.336957834943984`, `residual_gamma=2.071770621146408`, `verdict_kerr=strong_tension`, `kerr_sigma_source=point_estimate`.
- `SOURCE_CHECK`: f/tau verificados en Table IX/IMR. `M_final_Msun` y `chi_final` coinciden con GWOSC v2 update. `z` no coincide: fuente verificada `z=0.29`, YAML `z=0.438`. Table I TGR da `(1+z)M_f=97.0`, pero el YAML produce `106.9872`.
- `INCONSISTENCY_TYPE`: `NON_SIMULTANEOUS_POSTERIORS`
- `CONFIDENCE`: alta
- `PROPOSED_ACTION`: `correct_yaml_after_source_confirmation`
- `DECISION`: `INPUT_HOMOGENEIZATION_FAILURE`

## Decision provisional

`T6_OUTLIERS_ARE_INPUT_FAILURES = si`

Ninguno de los tres cumple el criterio para `ROBUST_KERR_TENSION_CANDIDATE` porque no esta verificado que frecuencia, damping, masa, spin y redshift provengan del mismo analisis/posterior, y de hecho `z` falla contra fuente externa primaria/curada.

La tension fuerte actual no debe interpretarse como fisica Kerr. Es un artefacto de `M_detector` inflado por `z` incompatible con el catalogo.

## Datos pendientes

- Confirmar si Ruta C debe usar como canonico GWTC-2 original, GWTC-2.1 `C01:Mixed`, o directamente Table I `(1+z)M_f` del paper TGR para la prediccion en detector-frame.
- Restaurar provenance en YAML o en sidecar: `source_doi`, `source_url`, `source_locator`, `analysis_method`, `credible_interval`, `notes`.
- Anadir `sigma_M_final_Msun`, `sigma_chi_final` y, si se mantiene `z`, incertidumbre de `z`.
- Decidir si `sigma_f_hz`/`sigma_tau_ms` se quedan como 90% half-width conservador o se renombran/transforman a 1 sigma.
- Recalcular Ruta C despues de corregir solo input/provenance; no tocar thresholds antes de eso.

## Recomendacion para T7

T7 no debe empezar como conclusion fisica. Antes: corregir/proponer correccion de `z` con fuente explicita, rerun `02b` + `05`, y archivar un nuevo run. T7 puede empezar solo como esqueleto documental, no como interpretacion.

## T6.5 - Correccion canonica de z

Decision de canon: usar GWOSC `GWTC-2.1-confident`, evento `v2`, PE update `C01:Mixed` como fuente canonica de `z`. Table I del paper TGR GWTC-2 se usa solo como cross-check detector-frame porque el pipeline ya calcula explicitamente `M_detector = M_source * (1 + z)`.

Correcciones aplicadas al YAML:

| event | z anterior | z canonico GWOSC v2 | fuente exacta | cross-check Table I |
|---|---:|---:|---|---:|
| GW190519_153544 | `0.822` | `0.45` | GWOSC `GWTC-2.1-confident`, `GW190519_153544-v2`, PE update `C01:Mixed`, campo `redshift` | `(1+z)M_f = 146.8` |
| GW190521_074359 | `0.352` | `0.21` | GWOSC `GWTC-2.1-confident`, `GW190521_074359-v2`, PE update `C01:Mixed`, campo `redshift` | `(1+z)M_f = 88.0` |
| GW190910_112807 | `0.438` | `0.29` | GWOSC `GWTC-2.1-confident`, `GW190910_112807-v2`, PE update `C01:Mixed`, campo `redshift` | `(1+z)M_f = 97.0` |

Reglas mantenidas:

- No se tocaron thresholds.
- No se tocaron Stage 02/03/04.
- No se cambio `f_hz`, `tau_ms`, `M_final_Msun` ni `chi_final`.
- No se reinterpreto fisica antes de rerun.

Run nuevo:

- Ejecutado: `runs_sync/active/kerr_audit_20260424_t65_zcanon/`.
- Artefactos: `qnm_dataset.csv`, `qnm_dataset_220.csv`, `kerr_audit_table.csv`, `kerr_audit_summary.json`, `outlier_zfix_comparison.csv`.

Comparacion viejo vs nuevo:

| event | old verdict | old r_f | old r_gamma | new verdict | new r_f | new r_gamma | decision |
|---|---|---:|---:|---|---:|---:|---|
| GW190519_153544 | `strong_tension` | `3.6567` | `2.0787` | `marginal` | `0.9746` | `1.0887` | `INPUT_HOMOGENEIZATION_FAILURE` |
| GW190521_074359 | `strong_tension` | `4.5723` | `3.3335` | `tension` | `1.7894` | `2.1404` | `INPUT_HOMOGENEIZATION_FAILURE` |
| GW190910_112807 | `strong_tension` | `3.3370` | `2.0718` | `marginal` | `1.1814` | `1.2681` | `INPUT_HOMOGENEIZATION_FAILURE` |

Resumen del run T6.5:

- `strong_tension`: 0 eventos.
- `tension`: 5 eventos.
- `marginal`: 7 eventos.
- `consistent`: 7 eventos.
- `residual_mean`: 1.1294.
- `residual_std`: 0.7723.
- KS vs N(0,1): `FAIL` (`p=0.0`).
- AD vs N(0,1): `OK` (`stat=0.149`, crit 5% `0.736`).

Cierre T6.5:

`T6_OUTLIERS_ARE_INPUT_FAILURES = si`

`ROBUST_KERR_TENSION_CANDIDATE = ninguno`

Los tres outliers originales dejan de ser `strong_tension` tras corregir solo `z`. Por tanto, no sobreviven como tension Kerr robusta. T7 puede avanzar como conclusion condicionada al estado actual: cohorte post-zfix auditada sin tensiones Kerr robustas, con limitaciones explicitas por falta de `sigma_M_final_Msun`, `sigma_chi_final` y convencion 90%/1 sigma no cerrada.
