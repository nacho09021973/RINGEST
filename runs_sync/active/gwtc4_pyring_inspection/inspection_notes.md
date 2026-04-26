# T8.3 pyRing inspection

## Source
- DCC P2600130 `pyRing.tar.gz` downloaded under this directory.
- Extracted package root: `runs_sync/active/gwtc4_pyring_inspection/extract/pyring/`.

## Event coverage
- pyRing O4a catalog events: 22
- Overlap with T6.6 qnm_dataset: 0
- Overlap with T8.2a verified qnm_dataset: 0
- Overlap with GWTC-4.0 pSEOBNR event map: 7: GW230628_231200, GW230914_111401, GW230927_153832, GW231028_153006, GW231102_071736, GW231206_233901, GW231226_101520

## Fields and units
- `event_summary_samples/events_summary_file.h5` exposes per-event samples for templates `DS`, `Kerr`, `KerrPostmerger`, and `IMR`.
- Plot script labels `Mf` as `(1+z)M_f [M_sun]`, `af` as `chi_f`, `f_22` as Hz, and `tau_22` as ms.
- `DS` has direct `f_22` and `tau_22` but no `Mf`/`af`.
- `Kerr` and `KerrPostmerger` have `Mf`, `af`, `f_22`, `tau_22`.
- `evidence.h5` gives log-evidence arrays vs start time plus base/higher-mode attrs; log-BF requires subtraction. Log base is not explicitly stated in README; variable names use `lnb`.
- Raw `.dat` files require custom parsing. Kerr `.dat` has `Mf`/`af` but not direct `f_22`/`tau_22`; DS `.dat` has `f_t_0` and `tau_t_0`, with `tau_t_0` appearing in seconds. The summary HDF5 converts to `tau_22` ms.

## Pilot status
- Requested literal pilot overlapping T6.6/T8.2a is `NOT_AVAILABLE`: pyRing release is O4a only and has no events in those verified datasets.
- Reduced O4a proxy pilots: `GW230628_231200` and `GW231028_153006`; see `pilot_reduction.csv`.

## Verdict
- Status: `NEEDS_CUSTOM_REDUCTION`.
- A ringdown-only separated YAML is plausible from `DS` or `Kerr/KerrPostmerger` summary posteriors, but not YAML-ready without choosing template policy, source-frame mass/redshift policy, and uncertainty convention.
- Do not merge into canonical YAML yet. Keep pyRing separate from pSEOBNR.

## NO_VERIFICADO
- Source-frame conversion for `Mf`: summary gives detector-frame `(1+z)M_f`; source-frame mass needs GWOSC redshift/PE policy or explicit conversion.
- Exact log base of `lnb_22_noise`/evidence differences is not explicitly stated in README.
- Literal T6.6/T8.2a overlap pilot is absent.
- Whether to prefer `DS`, `Kerr`, or `KerrPostmerger` for RINGEST YAML is a physics decision, not an extraction issue.
