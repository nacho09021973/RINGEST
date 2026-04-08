# Malda En RINGEST

`malda/` fue copiado desde `/home/ignac/ringhier/malda` a `/home/ignac/RINGEST/malda`.

Decisión tomada:
- copia local en `RINGEST/malda/`

Motivo:
- dejar `RINGEST` autónomo
- evitar dependencia operativa a paths frágiles que apunten a `ringhier`
- preservar a `ringhier` como base histórica/validada sin acoplarle la exploración futura

Alcance analítico actual:
- `RINGEST` no opera actualmente sobre el corpus bruto de eventos de `ringhier/data`.
- `RINGEST` opera sobre un snapshot curado e inmutable de artefactos derivados importados desde `ringhier`; el manifiesto de referencia es `data/manifests/import_from_ringhier.json`.
- La fuente analítica actual incluye `data/raw/ringhier_snapshot/runs/phase8_ds46_estimator_input_unblock_20260407T000000Z/experiment/malda_residual_pattern_mining/outputs/residual_feature_table.json` como tabla derivada a nivel de evento.
- `exp002_pattern_scan_global_simple` selecciona una fuente derivada y `candidate_feature_fields`, y `exp003_exploratory_clustering` explora estructura en tablas derivadas a nivel de evento. `exp002` y `exp003` exploran estructura en tablas derivadas, no en datos crudos de eventos.

Regla:
- si más adelante se formaliza una dependencia externa o un submódulo, esa migración debe documentarse explícitamente
- en esta fase, `RINGEST` arranca con copia local y trazable
