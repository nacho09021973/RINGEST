"""stage_utils — Utilidades comunes para los scripts de la pipeline malda/.

Proporciona:
- Constantes de estado y exit codes estándar.
- REPO_ROOT: ruta absoluta a la raíz del repositorio.
- add_standard_arguments: añade --run-dir/--experiment/--runs-dir al parser.
- parse_stage_args: wrapper sobre parser.parse_args().
- infer_experiment: devuelve solo el experimento explícitamente proporcionado.
- StageContext: contexto de ejecución de un stage (directorios, artefactos, manifiestos).
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from contracts.common_models import (
    StageRuntimeManifestModel,
    StageSummaryModel,
    write_stage_runtime_manifest,
    write_stage_summary,
)

# ---------------------------------------------------------------------------
# Constantes globales
# ---------------------------------------------------------------------------

EXIT_OK = 0
EXIT_ERROR = 3
STATUS_OK = "OK"
STATUS_ERROR = "ERROR"

# Raíz del repositorio: el directorio padre de malda/ (es decir, basurin/).
REPO_ROOT: Path = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Helpers de argparse
# ---------------------------------------------------------------------------


def add_standard_arguments(parser: argparse.ArgumentParser) -> None:
    """Añade los argumentos estándar de contexto de ejecución al parser.

    Argumentos añadidos:
      --run-dir     Raíz contractual del run. Tiene prioridad absoluta.
      --experiment  Nombre del experimento/run. Solo válido junto con
                    --runs-dir explícito cuando no se pasa --run-dir.
      --runs-dir    Directorio raíz explícito donde se almacenan los runs.
    """
    option_strings = {
        option
        for action in getattr(parser, "_actions", [])
        for option in getattr(action, "option_strings", [])
    }

    if "--run-dir" not in option_strings:
        parser.add_argument(
            "--run-dir",
            type=str,
            default=None,
            help=(
                "Directorio raíz contractual del run. "
                "Tiene prioridad absoluta sobre --experiment."
            ),
        )

    if "--experiment" not in option_strings:
        parser.add_argument(
            "--experiment",
            type=str,
            default=None,
            help=(
                "Nombre del experimento (subdirectorio dentro de --runs-dir). "
                "Solo se usa si no se pasa --run-dir y --runs-dir es explícito."
            ),
        )
    if "--runs-dir" not in option_strings:
        parser.add_argument(
            "--runs-dir",
            dest="runs_dir",
            type=str,
            default=None,
            help=(
                "Directorio raíz explícito para resolver runs/<experiment> "
                "cuando no se pasa --run-dir."
            ),
        )


def parse_stage_args(parser: argparse.ArgumentParser) -> argparse.Namespace:
    """Parsea los argumentos de línea de comandos y devuelve el Namespace.

    Es un wrapper fino sobre parser.parse_args() que en el futuro podrá
    añadir validaciones comunes sin tocar cada script.
    """
    return parser.parse_args()


def infer_experiment(args: argparse.Namespace) -> str | None:
    """Devuelve el nombre del experimento solo si fue proporcionado explícitamente."""
    experiment = getattr(args, "experiment", None)
    if experiment:
        return experiment
    return None


# ---------------------------------------------------------------------------
# StageContext
# ---------------------------------------------------------------------------


class StageContext:
    """Contexto de ejecución de un stage de la pipeline malda/.

    Gestiona rutas canónicas, registro de artefactos y escritura de
    manifiestos/summaries de forma atómica.

    Atributos:
        experiment: nombre del experimento (subdirectorio del run).
        run_root:   ruta absoluta al directorio del run (<runs_dir>/<experiment>).
        stage_dir:  ruta absoluta al directorio del stage
                    (<run_root>/<stage_number>_<stage_slug>).
    """

    def __init__(
        self,
        experiment: str,
        run_root: Path,
        stage_dir: Path,
        stage_number: str,
        stage_slug: str,
    ) -> None:
        self.experiment = experiment
        self.run_root = run_root
        self.stage_dir = stage_dir
        self.stage_number = stage_number
        self.stage_slug = stage_slug
        self._artifacts: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Constructor de fábrica
    # ------------------------------------------------------------------

    @classmethod
    def from_args(
        cls,
        args: argparse.Namespace,
        stage_number: str,
        stage_slug: str,
    ) -> "StageContext":
        """Crea un StageContext a partir del Namespace parseado.

        Espera que args tenga los atributos añadidos por add_standard_arguments:
          - args.run_dir
          - args.experiment
          - args.runs_dir
        """
        run_dir_raw: str | None = getattr(args, "run_dir", None)
        experiment: str | None = infer_experiment(args)
        runs_dir_raw: str | None = getattr(args, "runs_dir", None)

        if run_dir_raw:
            run_root = Path(run_dir_raw).resolve()
            run_dir_name = run_root.name
            if experiment is None:
                experiment = run_dir_name
            elif experiment != run_dir_name:
                raise ValueError(
                    "Conflicting run identity: --run-dir basename "
                    f"'{run_dir_name}' does not match --experiment '{experiment}'."
                )
        elif experiment and runs_dir_raw:
            runs_dir = Path(runs_dir_raw).resolve()
            run_root = runs_dir / experiment
        elif experiment and not runs_dir_raw:
            raise ValueError(
                "Ambiguous run resolution: --experiment requires explicit --runs-dir "
                "when --run-dir is not provided."
            )
        else:
            raise ValueError(
                "Missing contractual run identity: provide --run-dir, or provide both "
                "--runs-dir and --experiment."
            )

        if experiment is None:
            raise ValueError(
                "Could not determine experiment name from explicit inputs. "
                "Provide --experiment or use a run_dir whose basename is the run id."
            )
        stage_dir = run_root / f"{stage_number}_{stage_slug}"

        # Crear directorios necesarios
        stage_dir.mkdir(parents=True, exist_ok=True)

        return cls(
            experiment=experiment,
            run_root=run_root,
            stage_dir=stage_dir,
            stage_number=stage_number,
            stage_slug=stage_slug,
        )

    # ------------------------------------------------------------------
    # Registro de artefactos
    # ------------------------------------------------------------------

    def record_artifact(self, key_or_path: Any, path: Any = None) -> None:
        """Registra un artefacto producido por este stage.

        Dos formas de uso:
          ctx.record_artifact("nombre_clave", Path("/ruta/al/artefacto"))
          ctx.record_artifact(Path("/ruta/al/artefacto"))  # usa path.name como clave

        Los artefactos se incluyen en el manifest.json al llamar write_manifest().
        """
        if path is None:
            # Solo se pasó la ruta
            artifact_path = Path(key_or_path) if not isinstance(key_or_path, Path) else key_or_path
            key = artifact_path.name
        else:
            key = str(key_or_path)
            artifact_path = Path(path) if not isinstance(path, Path) else path

        self._artifacts[key] = str(artifact_path)

    # ------------------------------------------------------------------
    # Escritura de archivos de metadatos
    # ------------------------------------------------------------------

    def write_manifest(
        self,
        outputs: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Escribe <stage_dir>/manifest.json de forma atómica.

        Args:
            outputs:  Diccionario de outputs producidos por el stage
                      (rutas relativas a run_root o nombres de artefactos).
            metadata: Metadatos adicionales (comando ejecutado, versión, etc.).
        """
        payload: dict[str, Any] = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "experiment": self.experiment,
            "stage": f"{self.stage_number}_{self.stage_slug}",
            "stage_dir": str(self.stage_dir),
            "run_root": str(self.run_root),
        }
        if outputs:
            payload["outputs"] = outputs
        if metadata:
            payload["metadata"] = metadata
        if self._artifacts:
            payload["artifacts"] = self._artifacts

        write_stage_runtime_manifest(
            StageRuntimeManifestModel.model_validate(payload),
            self.stage_dir / "manifest.json",
        )

    def write_summary(
        self,
        status: str,
        exit_code: int = 0,
        error_message: str | None = None,
        counts: dict[str, Any] | None = None,
    ) -> None:
        """Escribe <stage_dir>/stage_summary.json de forma atómica.

        Args:
            status:        Estado del stage ("OK", "ERROR", "INCOMPLETE",
                           "WARNING", etc.).
            exit_code:     Código de salida asociado (0 = éxito).
            error_message: Mensaje de error si el stage falló.
            counts:        Contadores/métricas opcionales del stage.
        """
        payload: dict[str, Any] = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "experiment": self.experiment,
            "stage": f"{self.stage_number}_{self.stage_slug}",
            "status": status,
            "exit_code": exit_code,
        }
        if error_message is not None:
            payload["error_message"] = error_message
        if counts:
            payload["counts"] = counts

        write_stage_summary(
            StageSummaryModel.model_validate(payload),
            self.stage_dir / "stage_summary.json",
        )


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    """Escribe data como JSON en path de forma atómica (tmp → os.replace)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
