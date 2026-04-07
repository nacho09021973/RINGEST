# Malda En RINGEST

`malda/` fue copiado desde `/home/ignac/ringhier/malda` a `/home/ignac/RINGEST/malda`.

Decisión tomada:
- copia local en `RINGEST/malda/`

Motivo:
- dejar `RINGEST` autónomo
- evitar dependencia operativa a paths frágiles que apunten a `ringhier`
- preservar a `ringhier` como base histórica/validada sin acoplarle la exploración futura

Regla:
- si más adelante se formaliza una dependencia externa o un submódulo, esa migración debe documentarse explícitamente
- en esta fase, `RINGEST` arranca con copia local y trazable
