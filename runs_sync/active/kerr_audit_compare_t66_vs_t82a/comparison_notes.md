# T8.2b comparison: T6.6 literature/O3 vs T8.2a GWTC-4.0 pSEOBNR verified

## Inputs
- `runs_sync/active/kerr_audit_20260424_t66_sigmas/qnm_dataset.csv`
- `runs_sync/active/kerr_audit_20260424_t66_sigmas/kerr_audit_table.csv`
- `runs_sync/active/kerr_audit_gwtc4_pseobnr_t82a_verified/qnm_dataset.csv`
- `runs_sync/active/kerr_audit_gwtc4_pseobnr_t82a_verified/kerr_audit_table.csv`
- `runs_sync/active/gwtc4_pseobnr_ingest/gwtc4_pseobnr_event_map.csv`

## Counts
- T6.6: 19 qnm rows, 19 unique events, verdicts {'marginal': 6, 'consistent': 13}
- T8.2a: 10 qnm rows, 10 unique events, verdicts {'consistent': 10}
- Overlap: 6 events
- T8.2a new vs T6.6 entered: 4 events: GW190630_185205, GW200129_065458, GW200224_222234, GW200311_115853
- Event-map new-for-RINGEST candidates: 11 total; 4 entered T8.2a; 7 blocked by verification/null fields

## Overlap residual changes
Improvement/worsening is defined only as delta in `max_abs_residual`: `T8.2a - T6.6`. Negative means smaller residual in T8.2a.

| event | verdict T6.6 | verdict T8.2a | delta_f_hz | delta_tau_ms | delta_max_abs_residual |
|---|---|---:|---:|---:|---:|
| GW150914 | marginal | consistent | 5.300 | 0.310 | -0.951 |
| GW170104 | marginal | consistent | -2.200 | 1.410 | -0.736 |
| GW190521_074359 | marginal | consistent | 6.000 | 0.090 | -0.714 |
| GW190519_153544 | consistent | consistent | -5.300 | -0.950 | -0.327 |
| GW190910_112807 | consistent | consistent | -2.500 | 3.590 | 0.074 |
| GW190828_063405 | consistent | consistent | 13.400 | 1.610 | 0.022 |

## Special notes
- GW190519_153544 in t82a: appears in qnm_dataset.csv but not qnm_dataset_220.csv; kerr_220_distance=0.153954.

## Interpretation
- This is a small-N comparison and should not be sold as strong evidence.
- T8.2a removes the marginal per-event verdicts seen in the overlapping T6.6 rows, mostly because the pSEOBNR Table 3 uncertainties and PE values differ from the older literature inputs.
- The physical result is conservative: no event-level Kerr outlier appears in the verified pSEOBNR subset; O4a remains blocked until `final_spin` is verified or a separate self-contained pSEOBNR carril is approved.

## Recommendation
- Keep T6.6 as baseline canonical literature/O3.
- Use T8.2a as a separate pSEOBNR verified cross-check and as a source for the four new complete events only after explicit merge review.
- Do not merge O4a into the main baseline until `final_spin` is resolved from GWOSC or a separate `table3_selfcontained` carril is created.
