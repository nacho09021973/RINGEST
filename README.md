# RINGEST

RINGEST es un proyecto distinto de `ringhier`.

- `ringhier` / BASURIN conserva validación, trazabilidad, freezes y cierres contractuales.
- `RINGEST` nace para exploración de patrones y generación de hipótesis.
- Los claims no se validan en `RINGEST`.
- Cualquier hallazgo candidato detectado en `RINGEST` debe volver a un carril validado antes de convertirse en claim.

Estado analítico actual:
- `RINGEST` no opera actualmente sobre el corpus bruto de eventos de `ringhier/data`.
- `RINGEST` opera sobre un snapshot curado e inmutable de artefactos derivados importados desde `ringhier`, descrito en `data/manifests/import_from_ringhier.json`.
- La fuente analítica actual incluye `data/raw/ringhier_snapshot/runs/phase8_ds46_estimator_input_unblock_20260407T000000Z/experiment/malda_residual_pattern_mining/outputs/residual_feature_table.json` como tabla derivada a nivel de evento.
- `exp002_pattern_scan_global_simple` (`schema_version = exp002-pattern-scan-0.1`) selecciona una fuente derivada y `candidate_feature_fields`; `exp003_exploratory_clustering` explora estructura y clustering sobre tablas derivadas a nivel de evento. Ninguno de los dos debe describirse como minería sobre datos brutos de eventos ni sobre el corpus completo de `ringhier/data`.

## Estructura inicial

- `data/raw/`: snapshots inmutables importados desde proyectos validados. Solo lectura por convención.
- `data/manifests/`: manifiestos de importación y procedencia.
- `malda/`: copia local para evitar dependencia frágil de paths hacia `ringhier`.
- `experiments/`: exploración controlada futura.
- `notebooks/`: notebooks futuros, no ejecutados en este arranque.
- `outputs/`: salidas derivadas de RINGEST.
- `docs/`: notas operativas y convenciones.
- `scripts/`: utilidades del proyecto.

## Regla operativa

Nada derivado debe escribirse dentro de `data/raw/`.
