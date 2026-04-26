# T8.4 pyRing DS reduction

## Scope
- Reduced only `DS/f_22` and `DS/tau_22` from pyRing O4a `events_summary_file.h5`.
- Did not use pyRing Kerr/KerrPostmerger `Mf/af` in the DS baseline.
- External PE was queried from GWOSC API v2 for `final_mass_source`, `final_spin`, and `redshift`.

## Counts
- Total pyRing DS events: 22
- SOURCE_OK: 0
- PE_INCOMPLETE: 22
- QNM_INCOMPLETE: 0

## SOURCE_OK events
- None.

## Blocked events
- GW230601_224134: PE_INCOMPLETE; missing `final_spin`; PE runs=12, runs with final_spin=0; selected=GWTC-4.0_GW230601_224134_C00:Mixed+XO4a_RW4_PE
- GW230609_064958: PE_INCOMPLETE; missing `final_spin`; PE runs=8, runs with final_spin=0; selected=GWTC-4.0_GW230609_064958_C00:Mixed_RW2_PE
- GW230628_231200: PE_INCOMPLETE; missing `final_spin`; PE runs=8, runs with final_spin=0; selected=GWTC-4.0_GW230628_231200_C00:Mixed_RW2_PE
- GW230811_032116: PE_INCOMPLETE; missing `final_spin`; PE runs=6, runs with final_spin=0; selected=GWTC-4.0_GW230811_032116_C00:Mixed_RW2_PE
- GW230814_061920: PE_INCOMPLETE; missing `final_spin`; PE runs=12, runs with final_spin=0; selected=GWTC-4.0_GW230814_061920_C00:Mixed+XO4a_RW4_PE
- GW230824_033047: PE_INCOMPLETE; missing `final_spin`; PE runs=8, runs with final_spin=0; selected=GWTC-4.0_GW230824_033047_C00:Mixed_RW2_PE
- GW230914_111401: PE_INCOMPLETE; missing `final_spin`; PE runs=12, runs with final_spin=0; selected=GWTC-4.0_GW230914_111401_C00:Mixed+XO4a_RW4_PE
- GW230922_020344: PE_INCOMPLETE; missing `final_spin`; PE runs=8, runs with final_spin=0; selected=GWTC-4.0_GW230922_020344_C00:Mixed_RW2_PE
- GW230922_040658: PE_INCOMPLETE; missing `final_spin`; PE runs=8, runs with final_spin=0; selected=GWTC-4.0_GW230922_040658_C00:Mixed_RW2_PE
- GW230924_124453: PE_INCOMPLETE; missing `final_spin`; PE runs=8, runs with final_spin=0; selected=GWTC-4.0_GW230924_124453_C00:Mixed_RW2_PE
- GW230927_043729: PE_INCOMPLETE; missing `final_spin`; PE runs=8, runs with final_spin=0; selected=GWTC-4.0_GW230927_043729_C00:Mixed_RW2_PE
- GW230927_153832: PE_INCOMPLETE; missing `final_spin`; PE runs=10, runs with final_spin=0; selected=GWTC-4.0_GW230927_153832_C00:Mixed+XO4a_RW4_PE
- GW230928_215827: PE_INCOMPLETE; missing `final_spin`; PE runs=8, runs with final_spin=0; selected=GWTC-4.0_GW230928_215827_C00:Mixed_RW2_PE
- GW231001_140220: PE_INCOMPLETE; missing `final_spin`; PE runs=10, runs with final_spin=0; selected=GWTC-4.0_GW231001_140220_C00:Mixed+XO4a_RW4_PE
- GW231028_153006: PE_INCOMPLETE; missing `final_spin`; PE runs=12, runs with final_spin=0; selected=GWTC-4.0_GW231028_153006_C00:Mixed+XO4a_RW4_PE
- GW231102_071736: PE_INCOMPLETE; missing `final_spin`; PE runs=12, runs with final_spin=0; selected=GWTC-4.0_GW231102_071736_C00:Mixed+XO4a_RW4_PE
- GW231108_125142: PE_INCOMPLETE; missing `final_spin`; PE runs=6, runs with final_spin=0; selected=GWTC-4.0_GW231108_125142_C00:Mixed_RW2_PE
- GW231206_233134: PE_INCOMPLETE; missing `final_spin`; PE runs=8, runs with final_spin=0; selected=GWTC-4.0_GW231206_233134_C00:Mixed_RW2_PE
- GW231206_233901: PE_INCOMPLETE; missing `final_spin`; PE runs=8, runs with final_spin=0; selected=GWTC-4.0_GW231206_233901_C00:Mixed_RW2_PE
- GW231213_111417: PE_INCOMPLETE; missing `final_spin`; PE runs=8, runs with final_spin=0; selected=GWTC-4.0_GW231213_111417_C00:Mixed_RW2_PE
- GW231223_032836: PE_INCOMPLETE; missing `final_spin`; PE runs=8, runs with final_spin=0; selected=GWTC-4.0_GW231223_032836_C00:Mixed_RW2_PE
- GW231226_101520: PE_INCOMPLETE; missing `final_spin`; PE runs=12, runs with final_spin=0; selected=GWTC-4.0_GW231226_101520_C00:Mixed+XO4a_RW4_PE

## 02b/05 recommendation
- Do not run `02b/05` yet: the YAML has zero `SOURCE_OK` events because GWOSC PE did not expose `final_spin` for the O4a events inspected.
- Do not merge into `data/qnm_events_literature.yml`.

## NO_VERIFICADO
- `final_spin` is absent from the selected GWOSC PE runs, and no queried PE run exposed it for these O4a events.
- DS gives only `f_22/tau_22`; using pyRing Kerr/KerrPostmerger `Mf/af` would be a separate self-contained pyRing-Kerr decision and is not used here.
- If source-frame PE spin is later exposed by GWOSC or an official PE table, this reduction can be promoted without touching QNM extraction.
