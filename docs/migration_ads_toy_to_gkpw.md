# Migration: ads Toy Boundary to GKPW Source/Response

## Current Canonical Policy

The canonical `ads` boundary rail is `ads_boundary_mode=gkpw`.

Canonical `ads` means:

- `ads_pipeline_tier=canonical`
- `ads_boundary_mode=gkpw`
- `correlator_type=GKPW_SOURCE_RESPONSE_NUMERICAL`
- Gate 6 metadata is complete:
  - `bulk_field_name`
  - `operator_name`
  - `m2L2`
  - `Delta`
  - `bf_bound_pass`
  - `uv_source_declared`
  - `ir_bc_declared`
  - `correlator_type`
- AGMOO validation may return a holographic pass state only when the correlator is strong and has no toy provenance.

Experimental `ads` means:

- `ads_pipeline_tier=experimental`
- `ads_boundary_mode=toy`
- toy/geodesic/QNM-style observables may exist for legacy compatibility
- the validator must not report the result as a strong holographic rail

## What Was Descanonized

The following boundary surfaces are no longer canonical for `ads`:

- `correlator_2pt_thermal` as a primary `ads` boundary generator
- `correlator_2pt_geodesic` as the final canonical `ads` boundary observable
- phenomenological pole embeddings written to `G_R_real` / `G_R_imag`
- silent promotion of toy/geodesic metadata into a strong holographic verdict

These paths may remain only behind explicit experimental/toy mode for compatibility and regression comparison.

## Canonical GKPW Rail

The canonical rail is implemented in `tools/gkpw_ads_scalar_correlator.py`.

It consumes an `ads` geometry with root datasets/attrs:

- `z_grid`
- `A_of_z`
- `f_of_z`
- `family=ads`
- `d`
- `z_h`

It then:

1. declares a probe bulk scalar field,
2. checks the BF bound,
3. derives `Delta`,
4. solves the linearized scalar equation over `(omega,k)`,
5. imposes ingoing IR boundary conditions for thermal `ads` and regularity for horizonless `ads`,
6. extracts UV source and response by a two-branch asymptotic fit,
7. writes `G_R_real` and `G_R_imag` from `response/source`,
8. emits Gate 6 metadata, `config_hash`, and `reproducibility_hash`.

The correlator type is deliberately `GKPW_SOURCE_RESPONSE_NUMERICAL`, not `HOLOGRAPHIC_WITTEN_DIAGRAM`, because contact-term subtraction and full holographic renormalization are not implemented yet.

## Contracts And Summaries

Per-correlator summaries are written by `generate_to_run(...)` under:

```text
runs/<run_id>/gkpw_ads_scalar_correlator/<geometry>__gkpw_scalar_correlator_summary.json
```

The summary records:

- `correlator_type`
- `classification`
- `gate6_complete`
- `bf_bound_pass`
- `agmoo_verdict`
- `config_hash`
- `reproducibility_hash`
- optional stability benchmarks

Stage 01 also writes a run-level contract summary:

```text
01_generate_sandbox_geometries/ads_gkpw_migration_summary.json
```

That file aggregates the `ads` entries from `geometries_manifest.json` and records whether canonical `ads` entries satisfy the Gate 6 and AGMOO contract.

## Benchmarks

The GKPW module can emit deterministic stability checks with:

```text
python tools/gkpw_ads_scalar_correlator.py --geometry-h5 <ads.h5> --run-dir runs/<run_id> --run-benchmarks
```

The checks compare the retarded correlator under:

- radial discretization changes,
- UV cutoff changes,
- frequency resolution changes.

These checks are numerical stability probes, not proof of continuum convergence. They are intended to catch discontinuous behavior, hidden toy fallbacks, and accidental non-reproducibility.

## Remaining Debt

The migration removes toy observables from canonical `ads`, but the following work remains:

- full holographic renormalization and contact-term subtraction,
- a stronger Euclidean `G2` construction beyond the current spectral Laplace projection from the GKPW retarded correlator,
- convergence thresholds calibrated on a physics benchmark suite rather than generic finite-difference sensitivity,
- extension of source/response extraction to more bulk fields and channels,
- downstream engine semantics that distinguish per-observable rigor rather than relying only on file-level metadata.
