# T9.2 population tail rank vs Kerr residual

- archivo: `population_tail_stats_table.csv`
- inputs reales: `population_metadata_table.csv`, `population_metadata_coverage.json`, `population_metadata_notes.md`.
- outputs reales: score poblacional, ranks por cohorte/combinado, tests H1 y secundarios exploratorios.
- funcion fisica: auditar si los residuos Kerr grandes se concentran en eventos poblacionalmente raros o en proxies de cobertura/seleccion de waveform.
- dependencia toy/teorica: ninguna nueva; no usa `chi_p`, no usa SNR/FAR/`p_astro` en el score primario.
- veredicto: NULL; recomendacion: KILL.

## Score primario

- Tipo: `MAHALANOBIS_SHRINKAGE`.
- Vector: `log(M_total_source)`, `logit(q)`, `chi_eff`, `redshift`.
- Estimacion: 23 eventos unicos; duplicados entre cohortes no reponderan la covarianza.
- Covarianza regularizada: shrinkage diagonal alpha=0.1; condicion=31.04.

## H1 primaria

| grupo | N filas | N eventos | rho Spearman | p_perm H1+ | Theil-Sen | LOO signo estable |
|---|---:|---:|---:|---:|---:|---|
| T6.6_O3_literature | 19 | 19 | -0.0877 | 0.644 | -0.0774 | true |
| T8.2a_GWTC4_pSEOBNR | 10 | 10 | 0.0303 | 0.466 | 0.0303 | false |
| COMBINED | 29 | 23 | -0.0508 | 0.608 | -0.0419 | false |

## Enrichment marginal / tercil alto

| grupo | marginales en top tercil | marginales totales | fraccion marginal top | top tercil base | ratio |
|---|---:|---:|---:|---:|---:|
| T6.6_O3_literature | 2 | 6 | 0.333 | 0.368 | 0.905 |
| T8.2a_GWTC4_pSEOBNR | 0 | 0 | NA | 0.4 | NA |
| COMBINED | 2 | 6 | 0.333 | 0.345 | 0.967 |

## Leave-one-out e influencia

- `T6.6_O3_literature`: rho_LOO min=-0.214, max=-0.00929; flips=ninguno; influyentes=GW190708_232457 (d_rho=0.126), GW190915_235702 (d_rho=0.0888), GW190521 (d_rho=-0.0784).
- `T8.2a_GWTC4_pSEOBNR`: rho_LOO min=-0.133, max=0.417; flips=GW150914, GW170104, GW190521_074359, GW190630_185205, GW190828_063405, GW200129_065458, GW200224_222234; influyentes=GW190910_112807 (d_rho=-0.386), GW190519_153544 (d_rho=-0.203), GW170104 (d_rho=0.164).
- `COMBINED`: rho_LOO min=-0.133, max=0.0495; flips=GW190910_112807; influyentes=GW190910_112807 (d_rho=-0.1), GW190708_232457 (d_rho=0.0821), GW150914 (d_rho=0.0671).

## Tests secundarios exploratorios

| grupo | predictor | rho | p_perm H1+ | Theil-Sen |
|---|---|---:|---:|---:|
| T6.6_O3_literature | q | 0.23 | 0.168 | 0.951 |
| T6.6_O3_literature | M_total_source | -0.0754 | 0.622 | -0.00083 |
| T6.6_O3_literature | chi_eff | 0.157 | 0.258 | 0.418 |
| T6.6_O3_literature | redshift | -0.571 | 0.994 | -2.27 |
| T6.6_O3_literature | network_matched_filter_snr | 0.729 | 0.00045 | 0.0929 |
| T6.6_O3_literature | p_astro | 0.228 | 0.173 | 4.68 |
| T6.6_O3_literature | FAR | -0.314 | 0.904 | -72 |
| T8.2a_GWTC4_pSEOBNR | q | 0.612 | 0.0317 | 1.25 |
| T8.2a_GWTC4_pSEOBNR | M_total_source | 0.285 | 0.213 | 0.00421 |
| T8.2a_GWTC4_pSEOBNR | chi_eff | 0.0985 | 0.395 | 0.276 |
| T8.2a_GWTC4_pSEOBNR | redshift | 0.0729 | 0.423 | 0.0189 |
| T8.2a_GWTC4_pSEOBNR | network_matched_filter_snr | 0.345 | 0.162 | 0.0156 |
| T8.2a_GWTC4_pSEOBNR | p_astro | -0.177 | 0.697 | -13.6 |
| T8.2a_GWTC4_pSEOBNR | FAR | 0.405 | 0.142 | 121 |
| COMBINED | q | 0.176 | 0.184 | 0.448 |
| COMBINED | M_total_source | 0.0458 | 0.407 | 0.000776 |
| COMBINED | chi_eff | 0.0877 | 0.328 | 0.25 |
| COMBINED | redshift | -0.272 | 0.918 | -0.962 |
| COMBINED | network_matched_filter_snr | 0.327 | 0.044 | 0.0261 |
| COMBINED | p_astro | 0.155 | 0.214 | 2.95 |
| COMBINED | FAR | -0.0934 | 0.682 | -1.4 |

## Diagnostico combinado unico

- Combinado por evento unico, promediando residuos de eventos duplicados: rho=-0.0553, p_perm=0.595, slope=-0.027.
- Este diagnostico no sustituye los tests por cohorte; sirve para detectar dependencia de duplicados entre cohortes.

## Interpretacion

- No hay asociacion positiva que cumpla simultaneamente p_perm<0.1, estabilidad leave-one-out, enriquecimiento de marginales y senal cualitativa por cohorte.
- Resultado estadistico: NULL para T9.2. Esto no es una refutacion fisica global; solo dice que esta muestra no soporta la hipotesis population-tail.
- Recomendacion: `KILL`.

## Guardrails

- No se modifico YAML canonico, codigo principal, thresholds ni stages 02/03/04.
- No se consultaron nuevas fuentes.
- `chi_p` queda aparcado por cobertura 0/23.
- SNR/FAR/`p_astro` aparecen solo como tests secundarios exploratorios, no en el score primario.
