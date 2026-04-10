# Estimator Tools Registry v1

## Objetivo
Fijar una capa declarativa y consumible de herramientas locales congeladas para `estimators_v1`, separada del pipeline canónico y separada de cualquier ejecución real de terceros.

La función de este registry es solo esta:

- declarar qué herramienta respalda cada estimador `E00..E60`
- declarar si el repo local ya existe bajo `/home/ignac/RINGEST/repo/`
- imponer una política de congelación y lectura antes de cualquier integración

## Qué NO hace
- No instala dependencias.
- No ejecuta herramientas de terceros.
- No clona repos automáticamente.
- No integra DINGO, sklearn, Captum, Evidently, ART o Alibi Detect en el pipeline.
- No modifica stages canónicos.

## Archivo principal
- `/home/ignac/RINGEST/estimator_tools_registry.json`

## Lector validado
- `/home/ignac/RINGEST/tools/estimator_tools_registry.py`

## Mapeo declarativo v1
- `E00 -> pydantic`
- `E10 -> scikit_learn`
- `E20 -> scikit_learn`
- `E30 -> dingo`
- `E40 -> scikit_learn, evidently`
- `E50 -> alibi_detect, art`
- `E60 -> captum`

## Campos por herramienta
- `tool_id`
- `repo_name`
- `local_repo_path`
- `required_for_estimators`
- `role`
- `repo_expected`
- `status`
- `freeze_policy`
- `integration_mode`
- `notes`

## Política por defecto
- `freeze_policy = pinned_commit_required`
- `integration_mode = read_only_until_validated`

## Estados esperados
- `dingo`: `present_local` si existe `/home/ignac/RINGEST/repo/dingo`
- resto: `missing_local` hasta que se materialicen bajo `/home/ignac/RINGEST/repo/`

La ausencia local de una herramienta no es error si:
- la ruta es válida bajo `/home/ignac/RINGEST/repo/`
- el `status` es coherente con la ausencia

## Criterios de aborto del lector
El lector debe fallar de forma explícita si:
- falta un campo requerido
- `tool_id` está duplicado
- `local_repo_path` no es absoluta
- `local_repo_path` no cuelga de `/home/ignac/RINGEST/repo/`
- `local_repo_path` no es coherente con `repo_name`
- `status` no coincide con la presencia o ausencia real del repo local

## Consultas mínimas expuestas
- herramientas por `estimator_id`
- `present_local_tools`
- `missing_local_tools`

## Smoke auditable
Ruta de salida:
- `/home/ignac/RINGEST/runs/estimator_tools_registry_smoke/estimator_tools_registry_v1/`

Artefactos:
- `manifest.json`
- `stage_summary.json`
- `registry_summary.json`

## Gobernanza
Este registry no autoriza ejecución.

La regla operativa es:
- repo local congelado
- commit pinneado requerido
- integración en modo solo lectura hasta validación explícita
