# RINGEST

RINGEST es un proyecto distinto de `ringhier`.

- `ringhier` / BASURIN conserva validación, trazabilidad, freezes y cierres contractuales.
- `RINGEST` nace para exploración de patrones y generación de hipótesis.
- Los claims no se validan en `RINGEST`.
- Cualquier hallazgo candidato detectado en `RINGEST` debe volver a un carril validado antes de convertirse en claim.

## Regla operativa

Ningún cambio entra si no reduce complejidad o aumenta verificabilidad.
Nada derivado debe escribirse dentro de `data/raw/`.

---

## Índice canónico

### Pipeline principal (etapas numeradas)

| Script | Rol |
|---|---|
| `00_download_gwosc_events.py` | Descarga eventos GWOSC |
| `00_load_ligo_data.py` | Carga datos LIGO |
| `00_validate_io_contracts.py` | Valida contratos de entrada |
| `00b_physics_sanity_checks.py` | Gate de física en datos de entrada |
| `01_extract_ringdown_poles.py` | Extracción de polos de ringdown |
| `02_emergent_geometry_engine.py` | Motor de geometría emergente |
| `02R_build_ringdown_boundary_dataset.py` | Dataset de frontera sobre datos reales |
| `03_discover_bulk_equations.py` | Descubrimiento simbólico de ecuaciones bulk |
| `04_geometry_physics_contracts.py` | Contratos geometría-física (gate stage 04) |
| `04b_negative_control_contracts.py` | Controles negativos contractuales |
| `04d_negative_hawking.py` | Control negativo Hawking |
| `05_analyze_bulk_equations.py` | Análisis de ecuaciones bulk |
| `06_build_bulk_eigenmodes_dataset.py` | Dataset de eigenmodos bulk |
| `07_emergent_lambda_sl_dictionary.py` | Diccionario lambda emergente |
| `07K_kerr_qnm_dictionary.py` | Diccionario QNM Kerr |
| `07b_discover_lambda_delta_relation.py` | Relación lambda-delta |
| `08_build_holographic_dictionary.py` | Construcción del diccionario holográfico |
| `08_theory_dictionary_contrast.py` | Contraste teoría vs datos |
| `09_real_data_and_dictionary_contracts.py` | Contratos sobre datos reales y diccionario |
| `10_build_gwosc_enriched_event_table.py` | Tabla de eventos enriquecida GWOSC |

### Módulos de soporte

| Módulo | Rol |
|---|---|
| `stage_utils.py` | Utilidades comunes del pipeline (único py-module instalado) |
| `bulk_scalar_solver.py` | Solver escalar bulk |
| `family_registry.py` | Registro de familias holográficas |
| `feature_support.py` | Soporte de features |
| `premium_estimator.py` | Estimador premium canónico |
| `premium_backend_adapter_claude_code.py` | Adaptador de backend premium |
| `estimators_registry.json` | Registro de estimadores (datos) |
| `estimator_tools_registry.json` | Registro de herramientas de estimación (datos) |
| `run_batch_load.sh` | Entrada shell para carga por lotes |

### Contratos

| Módulo | Rol |
|---|---|
| `contracts/common_models.py` | Modelos Pydantic compartidos por el pipeline |

### Tests gate (21 activos)

| Test | Gate sobre |
|---|---|
| `test_common_contract_models.py` | `contracts/common_models.py` |
| `test_stage_utils_contract.py` | `stage_utils.py` |
| `test_feature_support.py` | `feature_support.py` |
| `test_focused_sandbox_and_engine.py` | Motor de geometría emergente |
| `test_02R_g2_time_contracts.py` | Stage 02R — contratos temporales g2 |
| `test_02R_saturation_detection.py` | Stage 02R — detección de saturación |
| `test_03_symbolic_discovery.py` | Stage 03 |
| `test_04_correlator_contract.py` | Stage 04 — contrato de correlador |
| `test_stage04_contract_runtime.py` | Stage 04 — runtime |
| `test_06_delta_uv_contract.py` | Stage 06 — contrato delta UV |
| `test_07b_discover_lambda_delta_relation.py` | Stage 07b |
| `test_08_theory_dictionary_contrast.py` | Stage 08 |
| `test_stage08_contract_runtime.py` | Stage 08 — runtime |
| `test_agmoo_ads_contract.py` | Contrato AGMOO/ADS |
| `test_g2_representation_contract.py` | Contrato representación g2 |
| `test_g2_representation_xmax6.py` | Contrato g2 con xmax=6 |
| `test_softwall_gubserrocha_baseline.py` | Baseline softwall / Gubser-Rocha |
| `test_decay_type_discrimination.py` | Discriminación de tipo de decaimiento |
| `test_estimator_tools_registry.py` | Registro de herramientas |
| `test_estimators_registry.py` | Registro de estimadores |
| `test_stage02_full_cohort_materialization.py` | Materialización cohorte completa |
| `test_repo_agent_v03.py` | Agente de repo v03 |

### Herramientas (`tools/`)

| Herramienta | Rol |
|---|---|
| `estimator_tools_registry.py` | Registro de herramientas de estimación |
| `estimators_registry.py` | Registro de estimadores |
| `repo_contracts.py` | Contratos del repo |
| `repo_registry.py` | Registro del repo |
| `repo_router.py` | Router del repo |
| `repo_agent_v03_module_help.py` | Agente de ayuda de módulos (v03) |
| `g2_representation_contract.py` | Contrato de representación g2 |
| `decay_type_discrimination.py` | Discriminador de tipo de decaimiento |
| `compare_softwall_gubserrocha_sensitivity.py` | Sensibilidad softwall vs Gubser-Rocha |
| `materialize_unified82_cohort.py` | Materialización cohorte unificada 82 |
| `validate_agmoo_ads.py` | Validación AGMOO/ADS |
| `validate_g2_representation_contract.py` | Validación contrato g2 |

### Documentación activa (`docs/`)

| Doc | Contenido |
|---|---|
| `instrucciones_pipeline.md` | Cómo correr el pipeline completo |
| `hoja_de_ruta.md` | Mapa de trabajo del proyecto |
| `qnm_contract_v3_spec.md` | Especificación contrato QNM (vigente) |
| `stage04_correlator_semantics_tail_strict.md` | Semántica de contratos stage 04 |
| `g2_representation_xmax6_contract.md` | Contrato representación g2 xmax=6 |
| `preregister_softwall_vs_gubserrocha.md` | Pre-registro comparación softwall/GR |
| `phase_b_premium_comparison_contract.md` | Contrato comparación fase B |
| `phase_b_premium_estimator_contract.md` | Contrato estimador premium fase B |
| `soft_wall vs gubser_rocha.pdf` | Referencia de física |

### Archivo (`_archive/`)

Archivos no canónicos pero preservados en historial.
No deben importarse ni ejecutarse sin auditoría previa.

## Instalación

Base:
```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -e . --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple
```

GPU / NVIDIA:
```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[gpu]" --index-url https://download.pytorch.org/whl/cu121 --extra-index-url https://pypi.org/simple
```

PySR opcional:
```bash
. .venv/bin/activate
pip install -e ".[pysr]" --extra-index-url https://pypi.org/simple
```

Verificación CUDA:
```bash
python - <<'PY'
import torch
print("torch_version=", torch.__version__)
print("cuda_available=", torch.cuda.is_available())
print("cuda_device_count=", torch.cuda.device_count())
PY
```

Nota:
- `PySR` es opcional y no bloquea el carril base.
- `PySR` necesita Julia disponible en el primer import/uso efectivo.
