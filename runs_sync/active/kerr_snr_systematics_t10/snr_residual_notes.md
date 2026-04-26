# T10.0 SNR residual robustness audit

- archivo: `snr_residual_audit_table.csv`
- inputs reales: `population_tail_stats_table.csv`, `population_tail_summary.json`.
- outputs reales: ranking por SNR/residuo, Spearman, permutation p-value, leave-one-out, top-SNR jackknife y controles parciales.
- funcion fisica: auditar si la senal secundaria SNR-residuo es robusta o un artefacto de pocos eventos/proxies poblacionales.
- dependencia toy/teorica: ninguna nueva; no se ejecutan stages ni se consultan fuentes externas.
- veredicto: ROBUST_DIAGNOSTIC; recomendacion: DO_CONTINUE.

## Asociacion primaria SNR-residuo

| grupo | N filas | N eventos | rho | p_perm H1+ | Theil-Sen |
|---|---:|---:|---:|---:|---:|
| T6.6_O3_literature | 19 | 19 | 0.729 | 0.00035 | 0.0929 |
| T8.2a_GWTC4_pSEOBNR | 10 | 10 | 0.345 | 0.165 | 0.0156 |
| COMBINED | 29 | 23 | 0.327 | 0.0432 | 0.0261 |

## Leave-one-out

| grupo | rho min | rho max | runs p<0.1 positivo | sign flips | eventos mas influyentes |
|---|---:|---:|---:|---|---|
| T6.6_O3_literature | 0.681 | 0.785 | 19/19 | ninguno | GW190708_232457 (d=-0.056), GW150914 (d=0.0479), GW190421_213856 (d=0.0479) |
| T8.2a_GWTC4_pSEOBNR | 0.1 | 0.7 | 2/10 | ninguno | GW190910_112807 (d=-0.355), GW170104 (d=0.245), GW190828_063405 (d=-0.138) |
| COMBINED | 0.252 | 0.377 | 22/23 | ninguno | GW190421_213856 (d=0.0749), GW190727_060333 (d=0.0697), GW150914 (d=0.0562) |

## Jackknife top-SNR

| grupo | quita | eventos quitados | rho | p_perm H1+ |
|---|---:|---|---:|---:|
| T6.6_O3_literature | top 1 | GW150914 | 0.681 | 0.0015 |
| T6.6_O3_literature | top 2 | GW150914, GW190521_074359 | 0.644 | 0.00355 |
| T6.6_O3_literature | top 3 | GW150914, GW190521_074359, GW170814 | 0.595 | 0.0078 |
| T8.2a_GWTC4_pSEOBNR | top 1 | GW200129_065458 | 0.333 | 0.19 |
| T8.2a_GWTC4_pSEOBNR | top 2 | GW200129_065458, GW150914 | 0.31 | 0.227 |
| T8.2a_GWTC4_pSEOBNR | top 3 | GW200129_065458, GW150914, GW190521_074359 | 0.321 | 0.247 |
| COMBINED | top 1 | GW200129_065458 | 0.368 | 0.0275 |
| COMBINED | top 2 | GW200129_065458, GW150914 | 0.307 | 0.0621 |
| COMBINED | top 3 | GW200129_065458, GW150914, GW190521_074359 | 0.277 | 0.096 |

## Control parcial

| grupo | control | partial rho | p_perm H1+ |
|---|---|---:|---:|
| T6.6_O3_literature | population_tail_rank | 0.736 | 0.0004 |
| T6.6_O3_literature | M_total_source | 0.733 | 0.0005 |
| T6.6_O3_literature | q | 0.713 | 0.00095 |
| T6.6_O3_literature | redshift | 0.644 | 0.0027 |
| T6.6_O3_literature | population_tail_rank+M_total_source+q+redshift | 0.572 | 0.0141 |
| T8.2a_GWTC4_pSEOBNR | population_tail_rank | 0.356 | 0.169 |
| T8.2a_GWTC4_pSEOBNR | M_total_source | 0.328 | 0.189 |
| T8.2a_GWTC4_pSEOBNR | q | -0.21 | 0.707 |
| T8.2a_GWTC4_pSEOBNR | redshift | 0.439 | 0.118 |
| T8.2a_GWTC4_pSEOBNR | population_tail_rank+M_total_source+q+redshift | -0.292 | 0.717 |
| COMBINED | population_tail_rank | 0.326 | 0.0449 |
| COMBINED | M_total_source | 0.325 | 0.0458 |
| COMBINED | q | 0.282 | 0.0724 |
| COMBINED | redshift | 0.217 | 0.128 |
| COMBINED | population_tail_rank+M_total_source+q+redshift | 0.146 | 0.239 |

## Eventos que impulsan la correlacion

- `T6.6_O3_literature`: GW190708_232457 (delta_rho=-0.056, rho_sin=0.785, p_sin=0.0002), GW150914 (delta_rho=0.0479, rho_sin=0.681, p_sin=0.0015), GW190421_213856 (delta_rho=0.0479, rho_sin=0.681, p_sin=0.0013), GW190727_060333 (delta_rho=0.0479, rho_sin=0.681, p_sin=0.0011), GW190521 (delta_rho=-0.0451, rho_sin=0.774, p_sin=0.00015)
- `T8.2a_GWTC4_pSEOBNR`: GW190910_112807 (delta_rho=-0.355, rho_sin=0.7, p_sin=0.0205), GW170104 (delta_rho=0.245, rho_sin=0.1, p_sin=0.404), GW190828_063405 (delta_rho=-0.138, rho_sin=0.483, p_sin=0.0967), GW190519_153544 (delta_rho=0.0955, rho_sin=0.25, p_sin=0.259), GW190630_185205 (delta_rho=0.0955, rho_sin=0.25, p_sin=0.259)
- `COMBINED`: GW190421_213856 (delta_rho=0.0749, rho_sin=0.252, p_sin=0.1), GW190727_060333 (delta_rho=0.0697, rho_sin=0.257, p_sin=0.0961), GW150914 (delta_rho=0.0562, rho_sin=0.27, p_sin=0.0878), GW190708_232457 (delta_rho=-0.0503, rho_sin=0.377, p_sin=0.0249), GW190512_180714 (delta_rho=0.0489, rho_sin=0.278, p_sin=0.079)

## Interpretacion

- `ROBUST_DIAGNOSTIC` aplica estrictamente a `T6.6_O3_literature`: sobrevive leave-one-out, top-SNR jackknife y controles parciales, incluido el control conjunto.
- `T8.2a_GWTC4_pSEOBNR` queda NULL: rho positivo pero p_perm no significativo y controles parciales no sostienen la senal.
- `COMBINED` es fragil a controles: top-SNR jackknife conserva p<0.1, pero el control conjunto `population_tail_rank+M_total_source+q+redshift` deja rho=0.146 y p=0.239.
- No leer esto como claim fisico global entre cohortes; es un diagnostico tecnico de SNR en T6.6.
- Recomendacion: `DO_CONTINUE` solo para auditoria de sistematicos/cobertura SNR, no para narrativa fisica.

## Guardrails

- No se modifico YAML, codigo principal ni thresholds.
- No se ejecuto Stage 02/03/04.
- No se consultaron nuevas fuentes.
- No se construye narrativa fisica; esto es auditoria tecnica/estadistica de una correlacion secundaria.
