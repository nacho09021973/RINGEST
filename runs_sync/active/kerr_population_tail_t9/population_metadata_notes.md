# T9.1 GWOSC population metadata enrichment

- archivo: `population_metadata_table.csv`
- inputs reales: `t9_base_residual_table.csv` y GWOSC API v2 (`/events/{event}`, `/event-versions/{version}/parameters`).
- outputs reales: metadata poblacional por fila event x cohort, cobertura JSON y estas notas.
- funcion fisica: anotar masas fuente, razon de masas, spin efectivo, redshift, SNR y significancia de busqueda para auditoria poblacional posterior; no ejecuta correlaciones ni claims.
- dependencia toy/teorica: ninguna nueva; esto solo enriquece filas Kerr/Ruta C ya existentes con metadata catalogal.
- veredicto: RESCATAR como capa exploratoria T9.1; no confirma familia fisica.

## Regla de seleccion

- Poblacion: resultado PE preferido del catalogo oficial GWTC/confident de mayor prioridad disponible. IAS-O3a queda solo como fallback si no hay GWTC oficial.
- SNR: `network_matched_filter_snr`/`network_snr` desde el PE seleccionado si esta; si no, desde el resultado search seleccionado.
- Busqueda: `p_astro`/FAR solo desde resultados `pipeline_type=search`. Se usa el mismo catalogo que el PE si existe; si no, el mejor search catalogal disponible con prioridad gstlal, pycbc_bbh, pycbc, pycbc_broad, pycbc_allsky, pycbc_highmass, mbta, cwb.
- `metadata_status=SOURCE_OK` exige masas fuente, `chi_eff`, `redshift`, `M_total_source`, `q`, algun SNR de red y `p_astro` o FAR. `chi_p` se evalua aparte mediante `chi_p_available`.

## Eventos consultados

GW150914, GW170104, GW170814, GW170823, GW190408_181802, GW190421_213856, GW190503_185404, GW190512_180714, GW190513_205428, GW190519_153544, GW190521, GW190521_074359, GW190602_175927, GW190630_185205, GW190706_222641, GW190708_232457, GW190727_060333, GW190828_063405, GW190910_112807, GW190915_235702, GW200129_065458, GW200224_222234, GW200311_115853

## Cobertura por campo

- `mass_1_source`: 23/23 eventos (100.0%), 29/29 filas (100.0%)
- `mass_2_source`: 23/23 eventos (100.0%), 29/29 filas (100.0%)
- `M_total_source`: 23/23 eventos (100.0%), 29/29 filas (100.0%)
- `q`: 23/23 eventos (100.0%), 29/29 filas (100.0%)
- `chi_eff`: 23/23 eventos (100.0%), 29/29 filas (100.0%)
- `chi_p`: 0/23 eventos (0.0%), 0/29 filas (0.0%)
- `network_matched_filter_snr`: 23/23 eventos (100.0%), 29/29 filas (100.0%)
- `network_snr`: 0/23 eventos (0.0%), 0/29 filas (0.0%)
- `network_snr_any`: 23/23 eventos (100.0%), 29/29 filas (100.0%)
- `redshift`: 23/23 eventos (100.0%), 29/29 filas (100.0%)
- `p_astro`: 23/23 eventos (100.0%), 29/29 filas (100.0%)
- `FAR`: 23/23 eventos (100.0%), 29/29 filas (100.0%)
- `p_astro_or_FAR`: 23/23 eventos (100.0%), 29/29 filas (100.0%)

## Metadata incompleta

- Ningun evento queda incompleto segun la definicion T9.1 usada aqui.

## chi_p

- `chi_p_available=true`: 0/23 eventos (0.0%).
- Cubre >=80%: false.
- Recomendacion T9.2: aparcar chi_p; la API GWOSC v2 no expone `chi_p` para esta muestra con el nombre solicitado.

## Limitaciones

- No se modifico YAML canonico, codigo principal, thresholds ni stages 02/03/04.
- No se reextrajeron QNM.
- FAR y `p_astro` son dependientes del pipeline de busqueda seleccionado; las fuentes quedan en columnas `search_*_source`.
- En O1/O2, si el PE preferido viene de GWTC-2.1 pero no hay resultado search en ese catalogo, `p_astro`/FAR se rellenan desde el search GWTC-1 disponible.
- Este output es exploratorio: no hay correlaciones, regresiones ni claims fisicos.
