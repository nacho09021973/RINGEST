from __future__ import annotations

import argparse
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from stage_utils import StageContext, add_standard_arguments, infer_experiment


class StageUtilsContractTests(unittest.TestCase):
    def test_run_dir_precedence_over_experiment(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "runs" / "canonical_run"
            args = argparse.Namespace(
                run_dir=str(run_dir),
                experiment="canonical_run",
                runs_dir=str(root / "other_runs"),
            )

            ctx = StageContext.from_args(args, stage_number="03", stage_slug="discover_bulk_equations")

            self.assertEqual(ctx.run_root, run_dir.resolve())
            self.assertEqual(ctx.experiment, "canonical_run")
            self.assertEqual(ctx.stage_dir, run_dir.resolve() / "03_discover_bulk_equations")

    def test_no_run_identity_from_cwd(self):
        args = argparse.Namespace(experiment=None)
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch("stage_utils.Path.cwd", return_value=Path(tmp) / "cwd_name"):
                self.assertIsNone(infer_experiment(args))

        with self.assertRaisesRegex(ValueError, "Missing contractual run identity"):
            StageContext.from_args(
                argparse.Namespace(run_dir=None, experiment=None, runs_dir=None),
                stage_number="03",
                stage_slug="discover_bulk_equations",
            )

    def test_no_run_identity_from_env_default(self):
        parser = argparse.ArgumentParser()
        with mock.patch.dict(os.environ, {"CUERDAS_EXPERIMENT": "env_exp", "BASURIN_RUNS_ROOT": "/tmp/runs"}, clear=False):
            add_standard_arguments(parser)
            args = parser.parse_args([])

        self.assertIsNone(args.run_dir)
        self.assertIsNone(args.experiment)
        self.assertIsNone(args.runs_dir)
        self.assertIsNone(infer_experiment(args))

    def test_missing_run_dir_and_ambiguous_experiment_aborts(self):
        with self.assertRaisesRegex(ValueError, "requires explicit --runs-dir"):
            StageContext.from_args(
                argparse.Namespace(run_dir=None, experiment="exp_only", runs_dir=None),
                stage_number="03",
                stage_slug="discover_bulk_equations",
            )

    def test_run_dir_and_mismatched_experiment_abort(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "runs" / "canonical_run"
            with self.assertRaisesRegex(ValueError, "does not match --experiment"):
                StageContext.from_args(
                    argparse.Namespace(
                        run_dir=str(run_dir),
                        experiment="other_run",
                        runs_dir=str(root / "other_runs"),
                    ),
                    stage_number="03",
                    stage_slug="discover_bulk_equations",
                )


if __name__ == "__main__":
    unittest.main()
