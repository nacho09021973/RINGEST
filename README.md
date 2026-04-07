# RINGEST

RINGEST es un proyecto distinto de `ringhier`.

- `ringhier` / BASURIN conserva validación, trazabilidad, freezes y cierres contractuales.
- `RINGEST` nace para exploración de patrones y generación de hipótesis.
- Los claims no se validan en `RINGEST`.
- Cualquier hallazgo candidato detectado en `RINGEST` debe volver a un carril validado antes de convertirse en claim.

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
