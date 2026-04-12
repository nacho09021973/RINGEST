# G2 Representation Contract: xmax_6_v1

**Status:** Canonical upstream contract for the real-data carril (C2).  
**Supersedes:** Local non-canonical probe adapters in `runs/reopen_v1/`.  
**Decision ref:** `runs/reopen_v1/02_reopen_decision_summary.json`

---

## What this contract specifies

The `xmax_6_v1` contract is a versioned variant of the `logx_logg2_interp_unit_peak_v1`
G2 canonicalization, with `x_max = 6.0` instead of the default `x_max = 10.0`.

Canonical grid: `np.linspace(1e-3, 6.0, 100)` in linear space, interpolated in log-log.  
Peak normalisation: unit peak (`G2 / max(G2)`).

Defined constants in `tools/g2_representation_contract.py`:

| Constant | Value |
|---|---|
| `XMAX6_V1_X_MAX` | `6.0` |
| `XMAX6_V1_CONTRACT_NAME` | `"xmax_6_v1"` |
| `XMAX6_V1_N_X` | `100` |

---

## Why x_max = 6, not 10

The default `x_max = 10` was calibrated for holographic sandbox data, where AdS/Lifshitz
solutions are defined analytically on an unrestricted domain.

For real GWOSC events processed through `02R_build_ringdown_boundary_dataset.py`, the
G2 correlator is computed via ESPRIT on 250 ms ringdown windows. The physical signal
covers roughly `x ∈ [0.001, ~5]`. Beyond `x ≈ 5–6`, ESPRIT finds no reliable signal and
the interpolation holds the last observed value constant (edge-hold extrapolation).

With `x_max = 10`, the edge-hold region `x ∈ [5, 10]` inflates `G2_large_x` (the
large-x slope feature) far outside the training distribution. On GW150914, this produced
a z-score of `~795σ` for `G2_large_x` — a guaranteed FAIL on the V3 feature gate
(`CRITICAL_FEATURES_V3` contains `G2_large_x`, threshold `|z| > 5`).

With `x_max = 6.0`, the canonical grid stops before the edge-hold region. All three
anchor events (GW150914, GW151226, GW170814) passed the V3 gate with representative
holographic train statistics.

---

## Connection to feature contract V3 (C2)

The xmax_6_v1 G2 contract was developed alongside the V3 feature contract (Camino C2),
which drops the QNM block from the feature vector. The two are co-dependent:

- **C2 / V3**: removes `qnm_Q0`, `qnm_f1f0`, `qnm_g1g0` (ESPRIT modes are noise,
  not physical ringdown — see `docs/qnm_contract_v3_spec.md`)
- **xmax_6_v1**: fixes `G2_large_x` extrapolation so the remaining critical features
  stay within support

Together they form the canonical real-data configuration for stage 02.

---

## Anchor cohort

Three GWOSC events validated under xmax_6_v1 + V3:

| Event | Source H5 | Canonical H5 | Prior probe status |
|---|---|---|---|
| GW150914 | `runs/gwosc_all/GW150914/boundary_dataset/GW150914__ringdown.h5` | `runs/anchor_cohort_xmax6_v1/GW150914/GW150914__ringdown.h5` | PASS |
| GW151226 | `runs/gwosc_all/GW151226/boundary_dataset/GW151226__ringdown.h5` | `runs/anchor_cohort_xmax6_v1/GW151226/GW151226__ringdown.h5` | PASS |
| GW170814 | `runs/gwosc_all/GW170814/boundary_dataset/GW170814__ringdown.h5` | `runs/anchor_cohort_xmax6_v1/GW170814/GW170814__ringdown.h5` | PASS |

Manifest: `runs/anchor_cohort_xmax6_v1/anchor_manifest.json`

---

## How to regenerate the anchor cohort

```bash
for ev in GW150914 GW151226 GW170814; do
  python tools/g2_representation_contract.py \
    --source-h5 runs/gwosc_all/${ev}/boundary_dataset/${ev}__ringdown.h5 \
    --output-h5 runs/anchor_cohort_xmax6_v1/${ev}/${ev}__ringdown.h5 \
    --g2-repr-contract xmax_6_v1 \
    --x-max 6.0 \
    --summary-json runs/anchor_cohort_xmax6_v1/${ev}/contract_summary.json
done
```

---

## How to use in 02 inference

Pass the canonical H5 directly as the data source with a manifest that lists the events.
Stage 02 uses `build_feature_vector_v3` (17 features, no QNM block) and the V3 feature
gate. The checkpoint must have been trained on a dataset where `x_max=6.0` was used
during G2 canonicalization.

The upstream contract is enforced by the `g2_repr_contract` attribute written into
`boundary/` of each output H5. Any downstream consumer can verify:

```python
import h5py
with h5py.File("GW150914__ringdown.h5", "r") as f:
    assert f["boundary"].attrs["g2_repr_contract"] == "xmax_6_v1"
```

---

## Tests

`tests/test_g2_representation_xmax6.py` covers:
- Roundtrip: canonical grid ends at 6.0, unit-peak normalised, length 100
- Contract constants stable
- `write_contracted_boundary_h5` stores correct metadata
- Anchor manifest consumability (all H5 readable, contract attrs present)
- V3 feature gate passes on canonical H5 with representative train statistics
