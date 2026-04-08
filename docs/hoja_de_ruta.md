# Hoja de ruta — RINGEST hacia pipeline operativo

Estado: 2026-04-08. Documento vivo; actualizar con cada sesión.

---

## Estado actual

| Componente | Estado | Notas |
|---|---|---|
| Sandbox 160 geometrías | ✅ | `runs/sandbox_v1/` |
| Geometry engine v2 | ✅ | A_r2=0.45, f_r2=0.928 |
| QNMs numéricos (shooting) | ✅ | 160 geometrías, `qnm_numerical.json` |
| Clasificación unknowns | ✅ | unknown_1 → deformed/lifshitz; unknown_2 → ads/dpbrane |
| Extracción polos LIGO | ⚠️ | Whitening ✅; ESPRIT sobreestima τ0 a bajo SNR (necesita Bayesiano) |
| Kerr sandbox (01b) | ✅ | 80 geometrías M∈[25,150] Msun, a/M∈[0.1,0.9] — `runs/kerr_sandbox_v1/` |
| Geometry engine v5_b3 (Kerr+B3) | ✅ | Kerr p=1.000; GW150914 → kerr p=0.994 |
| Scripts 06, 07 (holográfico) | ✅ | Fase 4 completada — λ_sl=Δ(Δ-d) verificado R²=1.0 |
| Script 07K (Kerr QNM dict.) | ✅ | M y a/M de (f0,τ0) — R²=1.0 con predictor 2-step |
| Scripts 08, 09 | ⏳ | Pendientes (tras validación datos reales) |
| Descarga masiva GWOSC | ✅ | `00_download_gwosc_events.py` — 90 eventos confident |

---

## Bloqueadores críticos (en orden de prioridad)

### B1. ~~Whitening ausente en la cadena de datos LIGO~~ ✅ RESUELTO (2026-04-08)
`00_load_ligo_data.py` v4 implementa whitening Welch integrado (`--whiten`). Strain blanqueado en `strain/H1_whitened`. `01` lo usa automáticamente. Offband std ≈ 1 verificado sobre GW150914.

### B2. ~~Feature vector roto para datos LIGO~~ ✅ RESUELTO (2026-04-08)
Features Δ reemplazados por features QNM (Q0, f1/f0, γ1/γ0) en `build_feature_vector`. Sandbox parcheado. Family accuracy sandbox: 81.7%. LIGO sigue → hyperscaling pero ahora por razón correcta: extrapolación fuera de distribución (Q0_LIGO=10.2 vs max sandbox=4.76). Fix: sandbox Kerr (Fase 3).

### B2b. ~~Gap de distribución: no hay ejemplos Kerr en el training set~~ ✅ RESUELTO (2026-04-08)
`01b_generate_kerr_sandbox.py` genera 80 geometrías Kerr sintéticas (M∈[25,150] Msun, a/M∈[0.1,0.9]). Retraining sandbox_v5 (240 geo = 160 sandbox + 80 Kerr): clasificación Kerr p=0.997-0.999 en training, GW150914 → kerr p=0.966.

Discriminador clave: f1/f0<1 para Kerr (overtone debajo del fundamental) vs f1/f0≈2.3 para todas las familias sandbox.

### B3. ~~Prior físico incorrecto para Kerr~~ ✅ RESUELTO (2026-04-08)

Diagnóstico real: `physics_loss_ads_specific` ya estaba correctamente condicionada via `ads_mask`. El problema era `physics_loss_generic` que aplicaba priors de suavidad AdS (f∈[0,1], A monótona) a geometrías Kerr, cuyos A/f no están supervisados (`bulk_w=0`).

**Fix aplicado**: `physics_loss_generic` ahora solo se evalúa sobre `holo_mask = bulk_w.bool()` (muestras con bulk_truth holográfico). Kerr excluido completamente de toda regularización de bulk.

Resultado: GW150914 → kerr p=0.966 (v5) → **p=0.994** (v5_b3, con B3 resuelto).

---

## Fase 1 — Arreglar extracción de polos LIGO (próximo paso inmediato)

- [ ] **Añadir whitening** a `00_load_ligo_data.py`: estimar PSD de segmento offband (≥4s antes del evento), dividir strain en frecuencia
- [x] **Re-ejecutar `01_extract_ringdown_poles.py`** con rank=4, duration=0.05–0.15, bandpass 20–400 Hz, barrido de start-offset — **realizado 2026-04-08**
- [x] **Verificar coherencia con Isi+2019**: f0 recuperable (250±15 Hz), τ0 NO recuperable a SNR~8 (extraído 30–400 ms vs 13 ms). ESPRIT tiene sesgo sistemático en amortiguamiento a bajo SNR.
- [x] **Loggear parámetros**: whitening + rank + duration loggeados en manifest via `00` v4 y `01`
- [ ] **Integrar análisis Bayesiano** (Isi `ringdown` repo) para estimación robusta de τ0 — bloqueador para clasificación confiable en régimen Kerr real
- [ ] Para avanzar en el pipeline: usar polos publicados Isi+2019 para GW150914 (f0=250 Hz, τ0=13 ms)

---

## Fase 2 — Reparar el clasificador (features y retraining)

- [ ] **Actualizar `build_feature_vector`**: usar (Q₀, f₁/f₀, γ₁/γ₀) de QNMs numéricos como features primarios. Eliminar o aislar los features de Δ para que no afecten a datos LIGO
- [ ] **Retrain `02_emergent_geometry_engine.py`** con el nuevo feature vector sobre `sandbox_v3` o `sandbox_v4` con QNMs numéricos
- [ ] **Validar** clasificación interna del sandbox (debe ≥95% accuracy), luego relanzar sobre GW150914
- [ ] **Estudiar sensibilidad** del clasificador a `--start-offset` (¿cambia la familia asignada?)

---

## Fase 3 — Sandbox Kerr sintético ✅ COMPLETADA (2026-04-08)

- [x] **`01b_generate_kerr_sandbox.py`**: generador de QNMs Kerr teóricos con paquete `qnm`
  - 80 geometrías (8 masas × 10 spins), embeddings G2/G_R surrogate, HDF5 sin bulk_truth
- [x] **Retraining sandbox_v5** (160 sandbox + 80 Kerr = 240 total): Kerr p=0.997-0.999, GW150914 → kerr p=0.966
- [ ] **Corregir `LOSS_WEIGHT_PHYSICS_ADS`** (B3 aún pendiente — para Fase 4)
- [ ] **Controles negativos Kerr**: inyectar ruido puro, sinusoides, chirps → verificar que NO se clasifican como Kerr

---

## Fase 4 — Scripts 06, 07, 08 (orden fijo) ✅ COMPLETADA PARCIALMENTE (2026-04-08)

Orden correcto: `02 → 06 → 07 → resto`.

- [x] **`06_holographic_eigenmode_dataset.py`** (nuevo): 480 filas (160 geo × 3 operadores) + 80 Kerr.
  Calcula d_formula = (Δ²−m2L2)/Δ por geometría (varía: 3, 4, 5 para d_sp=3).
  SL solver (`bulk_scalar_solver.py`) corre como cross-check independiente.
  CSV: `runs/sandbox_v5_b3/06_holographic_eigenmode_dataset/bulk_modes_dataset.csv`
- [x] **`07_holo_lambda_dictionary.py`** (nuevo): valida λ_sl=Δ(Δ-d) R²=1.0 (todas las familias).
  GBR data-driven R²_cv=0.9995; poly grado-2 R²_cv=1.0. PySR opcional (--use-pysr).
  JSON: `runs/sandbox_v5_b3/07_holo_lambda_dictionary/lambda_sl_dictionary_report.json`
- [x] **`07K_kerr_qnm_dictionary.py`** (nuevo): diccionario inverso Kerr (f0,τ0)→(M,a/M).
  a/M R²_cv=1.0; M con predictor 2-step R²=1.0. GW150914: M=119 Msun (ESPRIT bias τ0).
- [ ] **`08_build_holographic_dictionary.py`**: construir el diccionario holográfico completo. Solo cuando `07` sea robusto con datos reales
- [ ] **`09_real_data_and_dictionary_contracts.py`**: contratos finales con datos reales

---

## Fase 5 — Validación y rigor científico

- [ ] **Comparar contra repositorio de Isi** (`github.com/maxisi/ringdown`) antes de cualquier publicación. Los polos extraídos deben ser consistentes en los mismos eventos
- [ ] **No entrenar con datos LIGO reales** como conjunto de entrenamiento principal: solo 10-15 eventos con SNR de ringdown suficiente → riesgo de memorizar el ruido del detector. Usar NR/IMR sintéticos para entrenamiento; LIGO solo para validación final
- [ ] **No mezclar** "recuperar M y a" con "testear no-hair". Si el mapa se entrena asumiendo Kerr y se valida con Kerr, no se está testeando nada
- [ ] **Mantener y extender** los controles negativos existentes (`04b`, `04c`, `04d`) hacia régimen Kerr
- [ ] **Degeneración M·ω = f(a/M)**: con un solo modo QNM fundamental no se puede separar masa y spin. Necesario al menos dos modos; con SNR actual esto es marginal. Documentar esta limitación explícitamente en `07`

---

## Deuda técnica menor

- [ ] `02R`: renombrar args `--x-min-s` / `--x-max-s` → `--x-min-dimless` / `--x-max-dimless` en cualquier script que los llame
- [ ] Features degeneradas (índices 10, 13 = Δ operators): añadir zeroing explícito también en training para consistencia con inference
- [ ] `unknown_family_2_unknown_003`: QNM probablemente converge a rama espuria (Q0=11.63 vs ~3 en sus vecinos). Recomputar con semilla diferente
- [ ] Documentar en `07` y `08` que Δ (dimensión conformal) no existe en espacio plano; la variable análoga para GW es (l, m, n)
