# Stage 04 Correlator Semantics Freeze After `tail_strict`

This note freezes the current interpretation of Stage 04 `correlator_structure`
after the `tail_strict` rerun of `tools/decay_type_discrimination.py`:

```bash
source .venv/bin/activate && python tools/decay_type_discrimination.py --x-min 4.0 --suffix tail_strict
```

The relevant aggregate result for the canonical 33-event cohort is:

- `n_events = 33`
- `n_exponential_preferred = 16`
- `n_powerlaw_preferred = 10`
- `n_ambiguous = 0`
- `n_neither_good = 7`
- `powerlaw_majority_observed = false`
- `exponential_tilt_observed = true`
- `mean ΔBIC = 115.838`
- `median ΔBIC = 3.782`

## Freeze

`correlator_structure` in Stage 04 should not be interpreted as a physical test
for power-law decay. In particular:

- `has_power_law` should not be read as evidence for physical power-law decay.
- `log_slope` should not be read as a proxy for conformal dimension.
- Stage 04 should be read as a relaxed, non-discriminating contract about decay
  structure within a finite analysis window.

## Reading Of `tail_strict`

The `tail_strict` cohort result does not show a canonical cohort dominated by
power-law classifications. It shows an aggregate tilt toward exponential fits,
but the cohort remains heterogeneous and includes a relevant subset of
`NEITHER_GOOD` events.

This is a semantic governance update, not a claim that the underlying physical
decay law has been established. No canonical Stage 04 production fields are
renamed by this note.
