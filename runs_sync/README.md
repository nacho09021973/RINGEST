# `runs_sync/`

Espejo ligero para continuidad entre maquinas. El historico completo sigue en `runs/`.

## Estructura actual

- `active/routeB_all18_20260422`
  - origen: `runs/routeB_all18_20260422`
  - contenido: summaries, manifests, tablas y notas; sin `*.h5` ni `*.npz`

- `active/community_ringdown_cohort`
  - origen: `runs/community_ringdown_cohort`
  - contenido: referencia comunitaria, summaries, manifests y tablas; sin `*.h5` ni `*.npz`

- `frozen/ads_gkpw_20260416_091407_fixAprior`
  - origen: `runs/ads_gkpw_20260416_091407_fixAprior`
  - contenido: manifests, summaries y `einstein_discovery.json`; sin `*.pt`, `*.h5` ni `*.npz`

## Regla

Si un artefacto no es ligero o no aporta continuidad real de trabajo entre maquinas, no entra aqui por defecto.
