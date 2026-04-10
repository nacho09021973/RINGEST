# Repo Agent v0

## Objetivo
Definir una capa mínima, auditable y contract-first para orquestar repos locales bajo `/home/ignac/RINGEST/repo/` sin ejecutar código de terceros ni tocar el pipeline canónico.

## Alcance v0
- Descubrir repos locales bajo `/home/ignac/RINGEST/repo/`.
- Leer y validar `repo_contract.json` por repo.
- Resolver dos necesidades declarativas:
  - `estimator_premium`
  - `bayes_baseline`
- Exponer adapters de inspección para `dingo` y `bilby`.
- Escribir artefactos de resolución bajo `/home/ignac/RINGEST/runs/<run_id>/repo_agent_v0/`.

## Qué NO hace
- No ejecuta entrenamiento ni inferencia externa.
- No muta repos de terceros bajo `/home/ignac/RINGEST/repo/`.
- No usa red.
- No integra nada downstream en stages canónicos.
- No crea datasets intermedios.
- No hace fallback silencioso cuando falta contrato o ruta compatible.

## Contrato de repo
Ruta esperada:

- `/home/ignac/RINGEST/repo/<name>/repo_contract.json`

Campos mínimos requeridos:

- `name`
- `origin_url`
- `commit_pinned`
- `license`
- `domain`
- `capabilities`
- `preferred_entrypoints`
- `read_only_default`
- `allowed_commands`
- `allowed_paths`
- `artifact_exports`
- `status`

Reglas de validación:

- Campo faltante: error explícito.
- Tipo incorrecto: error explícito.
- `capabilities` vacío: error explícito.
- `preferred_entrypoints` debe mapear capabilities declaradas a listas no vacías.
- `allowed_paths` debe ser relativa y no escapar de `/home/ignac/RINGEST/repo/<name>/`.

## Registry
Implementación: [tools/repo_registry.py](/home/ignac/RINGEST/tools/repo_registry.py)

Comportamiento:

- Recorre directorios hijos inmediatos bajo el root de repos.
- Si encuentra `repo_contract.json`, lo valida estrictamente.
- Si un directorio no tiene contrato, lo ignora y lo documenta en `ignored_dirs`.
- No ejecuta comandos.

## Router
Implementación: [tools/repo_router.py](/home/ignac/RINGEST/tools/repo_router.py)

Rutas declarativas soportadas:

- `estimator_premium -> dingo`
- `bayes_baseline -> bilby`

Criterios:

- El repo objetivo debe existir en el registry.
- El contrato debe declarar la capability requerida.
- Si falta repo o capability, se aborta con error explícito.
- No hay fallback a otro repo.

## Adapters
Implementaciones:

- [tools/repo_adapters/dingo_adapter.py](/home/ignac/RINGEST/tools/repo_adapters/dingo_adapter.py)
- [tools/repo_adapters/bilby_adapter.py](/home/ignac/RINGEST/tools/repo_adapters/bilby_adapter.py)

API v0:

- `inspect_repo(...)`
- `summarize_capabilities(...)`
- `resolve_entrypoint(...)`

Salida mínima:

- `repo_name`
- `contract_name`
- `selected_capability`
- `selected_entrypoint`
- `allowed_commands`
- `read_only_default`
- `notes`

Restricción:

- Solo inspección.
- No ejecutan código externo.

## Artefactos
Ruta de salida:

- `/home/ignac/RINGEST/runs/<run_id>/repo_agent_v0/manifest.json`
- `/home/ignac/RINGEST/runs/<run_id>/repo_agent_v0/stage_summary.json`
- `/home/ignac/RINGEST/runs/<run_id>/repo_agent_v0/resolution.json`

Campos mínimos de `resolution.json`:

- `run_id`
- `requested_need`
- `selected_repo`
- `selected_capability`
- `selected_entrypoint`
- `contract_path`
- `read_only_default`
- `allowed_commands`
- `verdict`

## Criterios de aborto
- Contrato ausente en el repo esperado para una resolución requerida.
- Contrato inválido.
- Capability requerida no declarada.
- Adapter inexistente para el repo seleccionado.

En esos casos el router aborta antes de escribir un run de éxito.

## Rutas exactas
- Root de repos: `/home/ignac/RINGEST/repo/`
- Contratos de prueba: `/home/ignac/RINGEST/tests/fixtures/repo/`
- Registry: `/home/ignac/RINGEST/tools/repo_registry.py`
- Contratos: `/home/ignac/RINGEST/tools/repo_contracts.py`
- Router: `/home/ignac/RINGEST/tools/repo_router.py`
- Adapters: `/home/ignac/RINGEST/tools/repo_adapters/`
