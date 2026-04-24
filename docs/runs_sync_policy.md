# Politica minima de `runs_sync/`

## Objetivo

`runs_sync/` es una carpeta ligera y versionable para mover entre maquinas solo los runs activos o congelados que siguen siendo utiles para continuar trabajo. No sustituye a `runs/` como historico local completo.

## Estado verificado en esta maquina

- `runs/` ocupa aproximadamente `145M`.
- `git lfs` no esta operativo aqui: `git lfs version` y `git lfs ls-files` fallan con `Maybe git-lfs is broken?`.
- El repo ya ignora `runs/` completo en [`.gitignore`](/home/ignac/RINGEST/.gitignore:1).
- El repo ya ignora binarios pesados en Git normal por extension global: `*.h5`, `*.hdf5`, `*.npz`.

## Criterio de inclusion

Entra en `runs_sync/`:

- resúmenes de stage (`stage_summary.json`)
- manifests (`manifest.json`)
- salidas textuales o tabulares ligeras (`.md`, `.json`, `.csv`, `.txt`, `.yml`, `.yaml`)
- tablas de referencia necesarias para continuar analisis en otra maquina

No entra en Git normal dentro de `runs_sync/`:

- `*.h5`
- `*.hdf5`
- `*.npz`
- `*.nc`
- `*.pt`

Esos binarios se dejan fuera hasta activar Git LFS de forma verificada.

## Subconjunto inicial elegido

Se ha preparado este espejo ligero:

- `runs_sync/active/routeB_all18_20260422`
  - origen: `runs/routeB_all18_20260422`
  - incluido: `qnm_dataset.csv`, `analysis/*.csv`, `analysis/*.md`, manifests y summaries de stages 02-04, `einstein_discovery.json` por evento, `boundary/manifest.json`
  - excluido: `boundary/*.h5`, `geometry_emergent/*.h5`, `predictions/*.npz`

- `runs_sync/active/community_ringdown_cohort`
  - origen: `runs/community_ringdown_cohort`
  - incluido: tablas de referencia comunitaria, manifests y summaries de stages 02-04, `einstein_discovery.json` por evento, `qnm_reference_boundary_smoke/manifest.json`
  - excluido: `qnm_reference_boundary_smoke/*.h5`, `geometry_emergent/*.h5`, `predictions/*.npz`

- `runs_sync/frozen/ads_gkpw_20260416_091407_fixAprior`
  - origen: `runs/ads_gkpw_20260416_091407_fixAprior`
  - incluido: manifests y summaries, `einstein_discovery.json` por caso
  - excluido: `02_emergent_geometry_engine/emergent_geometry_model.pt`, `geometry_emergent/*.h5`, `predictions/*.npz`
  - motivo: el checkpoint binario es util, pero no debe entrar en Git normal sin LFS

## Caso `docs/calibration/`

`docs/calibration/` existe y es ligero. No se ha duplicado dentro de `runs_sync/` porque ya encaja mejor en `docs/` como documentacion versionable del repo.

Rutas verificadas:

- [docs/calibration/phase1_ads_sanity.md](/home/ignac/RINGEST/docs/calibration/phase1_ads_sanity.md)
- [docs/calibration/stage02_reference_lock.md](/home/ignac/RINGEST/docs/calibration/stage02_reference_lock.md)

## Propuesta LFS exacta

Cuando `git lfs` este realmente instalado y funcional, la propuesta minima es:

```bash
git lfs track "runs_sync/**/*.h5"
git lfs track "runs_sync/**/*.hdf5"
git lfs track "runs_sync/**/*.npz"
git lfs track "runs_sync/**/*.nc"
git lfs track "runs_sync/**/*.pt"
```

Y el `.gitattributes` esperado seria:

```gitattributes
runs_sync/**/*.h5 filter=lfs diff=lfs merge=lfs -text
runs_sync/**/*.hdf5 filter=lfs diff=lfs merge=lfs -text
runs_sync/**/*.npz filter=lfs diff=lfs merge=lfs -text
runs_sync/**/*.nc filter=lfs diff=lfs merge=lfs -text
runs_sync/**/*.pt filter=lfs diff=lfs merge=lfs -text
```

No se ha creado aun ese `.gitattributes` porque en esta maquina `git lfs` no funciona y no conviene dejar el repo en un estado ambiguo.

## Como anadir un run nuevo

1. Crear destino bajo `runs_sync/active/` o `runs_sync/frozen/`.
2. Copiar solo artefactos ligeros y trazables:
   - manifests
   - summaries
   - tablas `.csv`
   - notas `.md`
   - `json` de resultados utiles
3. Si hace falta algun binario `*.h5`, `*.npz`, `*.nc` o `*.pt`, no meterlo en Git normal:
   - o bien esperar a LFS
   - o bien dejarlo solo en `runs/` local y documentar la dependencia exacta
4. Registrar el origen exacto del run en `runs_sync/README.md`.

## Como purgar un run viejo

1. Confirmar que ya no es run activo ni congelado de referencia.
2. Borrar solo su espejo en `runs_sync/`.
3. No tocar el historico original en `runs/` sin una decision separada.

## Regla operativa

`runs_sync/` no es un archivo historico total. Es un espejo de continuidad de trabajo entre maquinas.
