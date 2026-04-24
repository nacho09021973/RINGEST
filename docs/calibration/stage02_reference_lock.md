# Stage 02 reference lock

## 1. Checkpoint de referencia

- ruta: `runs/ads_gkpw_20260416_091407/02_emergent_geometry_engine/emergent_geometry_model.pt`
- SHA256: `cf40bd1f6fad1bc1f39b1a065568ebdc23bf7215ea33de0ae604459f4c62a845`
- tamaño: `5 704 319` bytes
- fecha del fichero en disco: `2026-04-16 09:23` (mtime, hora local)

## 2. Metadatos observados

Fuente: `runs/ads_gkpw_20260416_091407/02_emergent_geometry_engine/emergent_geometry_summary.json`
y confirmación cruzada con `runs/community_ringdown_cohort/02_emergent_geometry_engine/emergent_geometry_summary.json` (carril que ya consume este checkpoint).

- `version`: `V2.2`
- `mode`: `train`
- `feature_contract`: `v3`
- `n_features`: `17`
- `n_z`: `256`
- `z_grid`: `{min: 0.01, max: 5.0, n_points: 256}`
- `n_train`: `20` (todos `family = ads`, generados por `01_generate_sandbox_geometries` del mismo run)
- `n_test`: `10`
- `n_epochs`: `2000`
- `best_epoch`: `2000`
- `created_at` (del summary): `2026-04-16T07:23:45Z`
- `loss_weights` declarados: `{A: 2.0, f: 2.0, R: 0.001, zh: 0.1, family: 0.05, physics: 0.05, physics_ads: 0.02}`

## 3. Métricas observadas

Todas leídas de `emergent_geometry_summary.json` (`test_metrics`):

- `A_r2`: `-0.0642`
- `f_r2`: `0.2705`
- `R_r2`: `-0.00289`
- `zh_mae`: `0.0470`
- `family_accuracy`: `1.0`

Caveat de métricas (verificado hoy):

- Sobre su propio split de test AdS, el checkpoint tiene `A_r2 < 0` y `R_r2 ≈ 0`; no reproduce A(z) ni R(z) del ground truth.
- `family_accuracy = 1.0` no implica calidad geométrica; solo implica que el cabezal de clasificación de familia separa correctamente dentro de un split de únicamente AdS.
- El peso de la loss para R es tres órdenes de magnitud menor que el de A y f (`R=0.001` vs `A=f=2.0`), consistente con un modelo que no está forzado a aprender R.

## 4. Decisión operativa

Este checkpoint queda **fijado como referencia operativa única** para todo trabajo de calibración del `einstein_score` a partir de hoy, con caveat de calidad explícito. Ningún carril de calibración debe usar un Stage 02 distinto, salvo que antes se levante este lock.

## 5. Caveat explícito

- Este lock **no certifica** que el checkpoint sea físicamente bueno.
- Fija un único carril para que no se mezclen Stage 02 incompatibles en el mismo análisis.
- El checkpoint `sandbox_serio_v1` citado por `runs/routeB_all18_20260422/02_emergent_geometry_engine/emergent_geometry_summary.json` (`feature_contract = v2_5`, `n_features = 20`) **no existe en este ordenador** y queda fuera del perímetro de calibración.
- El checkpoint `runs/ads_gkpw_smoke_20260415_184946/02_emergent_geometry_engine/emergent_geometry_model.pt` (SHA256 `a9553a27…`, 5 epochs, humo) **no** es candidato a referencia y no debe confundirse con este.
- La Fase 1 (ver `docs/calibration/phase1_ads_sanity.md`) documenta dos bloqueos previos a cualquier calibración del score; uno de ellos (`B2`) afecta directamente a este checkpoint.

## 6. Rutas exactas relacionadas

- Checkpoint: `runs/ads_gkpw_20260416_091407/02_emergent_geometry_engine/emergent_geometry_model.pt`
- Manifest: `runs/ads_gkpw_20260416_091407/02_emergent_geometry_engine/manifest.json`
- Summary técnico: `runs/ads_gkpw_20260416_091407/02_emergent_geometry_engine/emergent_geometry_summary.json`
- Geometrías sandbox fuente: `runs/ads_gkpw_20260416_091407/01_generate_sandbox_geometries/*.h5`
- Geometrías emergidas por este checkpoint: `runs/ads_gkpw_20260416_091407/02_emergent_geometry_engine/geometry_emergent/*.h5`
- Carril que ya consume este checkpoint: `runs/community_ringdown_cohort/02_emergent_geometry_engine/`
- Checkpoint humo a no usar: `runs/ads_gkpw_smoke_20260415_184946/02_emergent_geometry_engine/emergent_geometry_model.pt`
- Doc hermano: `docs/calibration/phase1_ads_sanity.md`
