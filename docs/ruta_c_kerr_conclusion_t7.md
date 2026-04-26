# T7 - Conclusion provisional Ruta C / Kerr

Fecha: 2026-04-24

## Resumen

Con el input canonico corregido y auditado, la cohorte Ruta C actual no contiene candidatos robustos de tension Kerr. Los tres eventos que quedaban como `strong_tension` tras la correccion cosmologica detector-frame eran fallos de homogeneizacion de `z`, no evidencia fisica contra Kerr.

Resultado operativo:

```text
ROBUST_KERR_TENSION_CANDIDATE = ninguno
T6_OUTLIERS_ARE_INPUT_FAILURES = si
strong_tension_post_T6_5 = 0
```

Esta conclusion es provisional: depende del baseline actual con `kerr_sigma_source=point_estimate`, sin `sigma_M_final_Msun`, sin `sigma_chi_final`, y con errores QNM tratados como escala efectiva derivada de intervalos creibles al 90%.

## Protocolo usado

- Input QNM canonico: `data/qnm_events_literature.yml`
- Builder: `02b_literature_to_dataset.py`
- Auditor Kerr: `05_kerr_consistency_audit.py`
- Protocolo: `docs/PROTOCOLO_RUTA_C.md`
- Run base post cosmologia: `runs_sync/active/kerr_audit_20260424_zfix/`
- Run T6.5 canonico: `runs_sync/active/kerr_audit_20260424_t65_zcanon/`

Observable comparado:

```text
f_220_obs, gamma_220_obs
vs
Kerr(M_detector, chi_final)
```

con:

```text
M_detector = M_source * (1 + z)
```

Clasificacion por evento:

```text
consistent: max(|r_f|, |r_gamma|) < 1
marginal:   1 <= max < 2
tension:    2 <= max < 3
strong_tension: max >= 3
```

## Sintoma real

Antes de T6/T6.5, el run `kerr_audit_20260424_zfix` dejaba tres eventos en `strong_tension`:

| event | old r_f | old r_gamma | old verdict |
|---|---:|---:|---|
| GW190519_153544 | 3.6567 | 2.0787 | strong_tension |
| GW190521_074359 | 4.5723 | 3.3335 | strong_tension |
| GW190910_112807 | 3.3370 | 2.0718 | strong_tension |

La mini-auditoria indicaba que para cerrar Kerr habia que reducir artificialmente `M_source`, lo que apuntaba a un problema en la construccion de `M_detector`.

## Archivo o logica responsable

El calculo responsable esta en `02b_literature_to_dataset.py`: la prediccion Kerr se evalua en marco detector usando:

```text
M_detector = M_final_Msun * (1 + z)
```

El fallo estaba en `data/qnm_events_literature.yml`: los tres `z` activos eran demasiado altos para la fuente canonica GWOSC v2 / GWTC-2.1 `C01:Mixed`.

Correccion aplicada:

| event | z anterior | z canonico | fuente canonica |
|---|---:|---:|---|
| GW190519_153544 | 0.822 | 0.45 | GWOSC `GWTC-2.1-confident`, `GW190519_153544-v2`, PE update `C01:Mixed` |
| GW190521_074359 | 0.352 | 0.21 | GWOSC `GWTC-2.1-confident`, `GW190521_074359-v2`, PE update `C01:Mixed` |
| GW190910_112807 | 0.438 | 0.29 | GWOSC `GWTC-2.1-confident`, `GW190910_112807-v2`, PE update `C01:Mixed` |

Table I del paper TGR GWTC-2 se uso como cross-check de `(1+z)M_f`, no como fuente primaria de `z`.

## Fisica real vs andamiaje

Hecho verificado:

- `f_hz` y `tau_ms` de los tres outliers coinciden con Table IX / IMR del paper TGR GWTC-2.
- Esos observables estan reportados como frecuencia y damping time redshifted, por tanto deben compararse contra Kerr en marco detector.
- `M_final_Msun` y `chi_final` coinciden con GWOSC v2 para los tres eventos auditados.
- El cambio de solo `z` elimina los tres `strong_tension`.

Inferencia:

- La tension fuerte anterior era un artefacto de input: `z` inflado aumentaba `M_detector`, bajaba `f_kerr_hz`, y forzaba `r_f > 3`.
- No hay base para interpretar esos tres eventos como tension fisica Kerr robusta.

No afirmado:

- No se afirma confirmacion fuerte de Kerr con N=19.
- No se afirma calibracion completa de errores, porque faltan `sigma_M_final_Msun` y `sigma_chi_final`.
- No se afirma que las tensiones `tension` restantes sean fisica; son puntos a mantener bajo bandera de incertidumbre de input/modelo.

## Resultado antes/despues

Conteos por evento:

| run | consistent | marginal | tension | strong_tension |
|---|---:|---:|---:|---:|
| `kerr_audit_20260424_zfix` | 7 | 5 | 4 | 3 |
| `kerr_audit_20260424_t65_zcanon` | 7 | 7 | 5 | 0 |

Comparacion de outliers:

| event | old verdict | new verdict | new r_f | new r_gamma | decision |
|---|---|---|---:|---:|---|
| GW190519_153544 | strong_tension | marginal | 0.9746 | 1.0887 | INPUT_HOMOGENEIZATION_FAILURE |
| GW190521_074359 | strong_tension | tension | 1.7894 | 2.1404 | INPUT_HOMOGENEIZATION_FAILURE |
| GW190910_112807 | strong_tension | marginal | 1.1814 | 1.2681 | INPUT_HOMOGENEIZATION_FAILURE |

Estadistica global del run T6.5:

```text
n_unique_events = 19
n_mode_rows = 19
n_residuals = 38
kerr_sigma_source = point_estimate
residual_mean = 1.1294
residual_std = 0.7723
KS vs N(0,1) = FAIL, p = 0.0
AD vs N(0,1) = OK, stat = 0.149 < 0.736
```

Lectura: la auditoria elimina los candidatos robustos de tension Kerr, pero el test global no queda cerrado como confirmacion estadistica fuerte. El sesgo residual y la falta de propagacion de `sigma_M`/`sigma_chi` siguen siendo limitaciones del baseline.

## Veredicto por evento auditado

| event | veredicto T7 |
|---|---|
| GW190519_153544 | no robusto; fallo de homogeneizacion de input corregido |
| GW190521_074359 | no robusto; queda en `tension`, pero `max|r| < 3` y no cumple criterio de candidato robusto |
| GW190910_112807 | no robusto; fallo de homogeneizacion de input corregido |

## Decision T7

Conclusion defendible:

```text
Con el YAML corregido en z y el run T6.5 archivado, la cohorte Ruta C actual no muestra candidatos robustos de tension Kerr.
Las tres aparentes strong_tension tras la correccion cosmologica eran fallos de homogeneizacion del input.
```

Forma segura de citar el resultado:

```text
Exploracion Ruta C, N=19, modo (2,2,0), una fuente de literatura, errores de Kerr puntuales:
sin candidatos robustos de tension Kerr tras auditoria manual de outliers.
```

## Limitaciones abiertas

- Faltan `sigma_M_final_Msun` y `sigma_chi_final`; por tanto `sigma_f_kerr_hz=0` y `sigma_gamma_kerr_hz=0` en el baseline.
- Los errores QNM proceden de intervalos creibles al 90% armonizados; no esta cerrado si se interpretan como 1 sigma o como semiancho conservador.
- El YAML activo conserva provenance insuficiente: falta `source_doi`, `source_url`, `source_locator`, `analysis_method`, `credible_interval`, `notes`.
- N=19 y una sola fuente principal; no hay confirmacion estadistica fuerte.
- KS falla aunque AD pasa; no usar el test global como prueba cerrada de normalidad de residuos.

## Recomendacion

No tocar thresholds ni Stage 02/03/04 para forzar conclusiones.

Siguiente cambio minimo antes de una conclusion mas fuerte:

```text
T8: enriquecer provenance y sigmas de M_final/chi_final en YAML o sidecar,
rerun 02b + 05,
y comparar contra T6.5.
```

Mientras tanto, Ruta C puede reportar una conclusion provisional honesta:

```text
Kerr consistency baseline: no robust outliers after input audit.
```
