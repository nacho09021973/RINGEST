"""
Regression: stage 02's full-cohort materialization must preserve the
ground-truth family as the canonical `family` attribute on emergent H5
files. The model's prediction must be stored as `family_pred`, never
overwriting the truth.

Root cause fixed in April 2026: previous code set
    f_out.attrs["family"] = family_pred_name
which degraded ADS/GKPW systems (name `ads_*`) to the model's best
guess (e.g. "massive_gravity", "dpbrane") in downstream stages 03/06.

This test pins the write pattern via AST so future refactors can't
silently regress it without also rewriting the test.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
STAGE_02 = REPO_ROOT / "02_emergent_geometry_engine.py"


def _get_function_source(module_path: Path, function_name: str) -> str:
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return ast.get_source_segment(source, node) or ""
    raise RuntimeError(f"Function {function_name} not found in {module_path}")


class Stage02FamilyTruthPreservation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = _get_function_source(STAGE_02, "run_train_mode")

    def test_family_attribute_is_written_from_truth(self):
        """
        In the full-cohort write loop, f_out.attrs["family"] must be
        assigned from the truth name (family_truth_name), not from the
        prediction (family_pred_name).
        """
        self.assertIn(
            'f_out.attrs["family"] = family_truth_name',
            self.source,
            msg=(
                "Expected family attr to be written from family_truth_name. "
                "Overwriting with family_pred_name loses canonical semantic "
                "trace in downstream stages (03/06)  see audit April 2026."
            ),
        )

    def test_family_pred_is_still_recorded_separately(self):
        """The prediction must remain accessible via family_pred."""
        self.assertIn(
            'f_out.attrs["family_pred"] = family_pred_name',
            self.source,
            msg=(
                "family_pred must continue to be written so the model's "
                "prediction remains observable for diagnostics."
            ),
        )

    def test_family_attribute_is_not_assigned_from_pred(self):
        """Guard against regressing to family = family_pred_name."""
        self.assertNotIn(
            'f_out.attrs["family"] = family_pred_name',
            self.source,
            msg=(
                "Regression: run_train_mode overwrites ground-truth family "
                "with the model prediction. This degraded ADS -> "
                "massive_gravity/dpbrane in the canonical smoke."
            ),
        )


if __name__ == "__main__":
    unittest.main()
