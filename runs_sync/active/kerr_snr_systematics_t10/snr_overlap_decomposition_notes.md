# T10.1 overlap decomposition T6.6 vs T8.2a

- archivo: `snr_overlap_decomposition.csv`
- inputs reales: T10 SNR audit, overlap comparison, QNM datasets y Kerr audit tables de T6.6/T8.2a.
- outputs reales: tabla pareada de seis eventos solapados, atribucion Shapley por grupo de cambio y notas.
- funcion fisica: separar si el cambio de cola alta viene de observable QNM, sigmas o prediccion Kerr.
- dependencia toy/teorica: ninguna nueva; no se ejecutan stages ni se modifica pipeline.
- veredicto: RESCATAR como auditoria descriptiva; no afirmar causalidad fuerte.

## Eventos solapados

GW150914, GW190521_074359, GW190828_063405, GW190519_153544, GW190910_112807, GW170104

## Tabla pareada ordenada por SNR

| event | SNR | max T6.6 | max T8.2a | delta | r_f T6.6 | r_f T8.2a | r_gamma T6.6 | r_gamma T8.2a | driver | marca |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| GW150914 | 26 | 1.68 | 0.731 | -0.951 | 0.863 | 0.731 | 1.68 | 0.184 | OBS_SIGMA_CHANGE | HIGH_SNR_LOST_TAIL |
| GW190521_074359 | 25.9 | 1.32 | 0.61 | -0.714 | 0.645 | 0.61 | 1.32 | 0.402 | OBS_SIGMA_CHANGE | HIGH_SNR_LOST_TAIL |
| GW190828_063405 | 16.5 | 0.799 | 0.821 | 0.022 | 0.429 | 0.821 | 0.799 | -0.276 | MIXED | T82A_NO_IMPROVEMENT |
| GW190519_153544 | 15.9 | 0.788 | 0.462 | -0.327 | 0.442 | 0.153 | 0.788 | 0.462 | OBS_SIGMA_CHANGE |  |
| GW190910_112807 | 14.5 | 0.855 | 0.929 | 0.0743 | 0.418 | 0.284 | 0.855 | -0.929 | OBS_SHIFT | T82A_NO_IMPROVEMENT |
| GW170104 | 13.8 | 1.02 | 0.279 | -0.736 | 0.521 | 0.228 | 1.02 | -0.279 | OBS_SIGMA_CHANGE | LOST_TAIL |

## Driver dominante por evento

- `GW150914`: `OBS_SIGMA_CHANGE`; Shapley OBS=-0.121, OBS_SIGMA=-0.664, KERR=-0.162, KERR_SIGMA=-0.00416. same_direction_share=0.698; opposing_abs=0.
- `GW190521_074359`: `OBS_SIGMA_CHANGE`; Shapley OBS=0.0119, OBS_SIGMA=-0.726, KERR=0, KERR_SIGMA=0. same_direction_share=1.000; opposing_abs=0.0119.
- `GW190828_063405`: `MIXED`; Shapley OBS=0.196, OBS_SIGMA=-0.254, KERR=0.0728, KERR_SIGMA=0.00669. largest_same=OBS_SHIFT; share=0.712; opposing_abs=0.254.
- `GW190519_153544`: `OBS_SIGMA_CHANGE`; Shapley OBS=0.277, OBS_SIGMA=-0.604, KERR=0, KERR_SIGMA=0. same_direction_share=1.000; opposing_abs=0.277.
- `GW190910_112807`: `OBS_SHIFT`; Shapley OBS=0.495, OBS_SIGMA=-0.421, KERR=0, KERR_SIGMA=0. same_direction_share=1.000; opposing_abs=0.421.
- `GW170104`: `OBS_SIGMA_CHANGE`; Shapley OBS=0.00595, OBS_SIGMA=-0.693, KERR=-0.0416, KERR_SIGMA=-0.00779. same_direction_share=0.933; opposing_abs=0.00595.

## Lectura de f/tau, sigmas y Kerr

- En `GW150914`, `GW170104` y `GW190521_074359`, la cola T6.6 estaba dominada por `residual_gamma`; en T8.2a cae por aumento fuerte de `sigma_gamma_obs` y cambios de tau/damping. El driver dominante sale `OBS_SIGMA_CHANGE`.
- `GW190519_153544` tambien mejora, pero no era cola alta fuerte; su reduccion es mixta entre cambio observacional y sigma observacional.
- `GW190828_063405` y `GW190910_112807` no mejoran: T8.2a mantiene o sube `max_abs_residual`. En `GW190828_063405` el maximo pasa a frecuencia; en `GW190910_112807` queda dominado por gamma. No hay desaparicion universal de residuo en pSEOBNRv5PHM.
- Los cambios de prediccion Kerr (`f_kerr`, `gamma_kerr`) son secundarios en la mayoria de eventos; no explican por si solos la desaparicion de la cola alta.

## Interpretacion limitada para paper

- Hecho verificado: en los seis eventos solapados, los high-SNR `GW150914` y `GW190521_074359` pierden la cola alta en T8.2a.
- Inferencia: la reduccion esta mas ligada a sigmas observacionales de damping/tau y a cambios del observable QNM que a un desplazamiento coherente de la prediccion Kerr.
- Propuesta de frase segura: "In the six-event overlap, the pSEOBNRv5PHM rows reduce the high-SNR residual tail mainly through broader or shifted ringdown-mode posterior summaries, especially in the damping-time channel; this should be read as a waveform/posterior-systematics diagnostic rather than evidence for a physical deviation."

## Guardrails

- No se modifico YAML, codigo principal ni thresholds.
- No se ejecuto Stage 02/03/04.
- No se afirma causalidad fuerte.
