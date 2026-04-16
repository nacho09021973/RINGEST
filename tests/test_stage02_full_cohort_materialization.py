"""
tests/test_stage02_full_cohort_materialization.py

Regression: run_train_mode in 02_emergent_geometry_engine.py must materialize
geometry_emergent and predictions for the FULL cohort (n_train + n_test),
not only for the test subcohort. Without this, downstream Stage 03/04 see
only the test split.
"""
from __future__ import annotations

import ast
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _get_function_source(module_path: Path, function_name: str) -> str:
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return ast.get_source_segment(source, node) or ""
    raise RuntimeError(f"Function {function_name} not found in {module_path}")


class RunTrainModeMaterializesFullCohort(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = _get_function_source(
            REPO_ROOT / "02_emergent_geometry_engine.py",
            "run_train_mode",
        )
        cls.tree = ast.parse(cls.source)

    def test_builds_combined_names_list(self):
        """A combined list spanning train+test names must be constructed."""
        self.assertIn('train_data["names"]', self.source)
        self.assertIn('test_data["names"]', self.source)
        self.assertRegex(
            self.source,
            r'list\(train_data\["names"\]\)\s*\+\s*list\(test_data\["names"\]\)',
            msg="run_train_mode must build a combined cohort list (train + test) "
                "to materialize geometry_emergent and predictions for all systems.",
        )

    def test_h5_and_npz_writes_iterate_over_full_cohort(self):
        """
        The writing loop must iterate over the combined cohort, not only
        test_data. We detect this by locating h5py.File(...) writes inside a
        For-loop whose iterator walks a name list built from train + test.
        """
        found_full_cohort_write = False

        for node in ast.walk(self.tree):
            if not isinstance(node, ast.For):
                continue

            iter_src = ast.unparse(node.iter) if hasattr(ast, "unparse") else ""
            iterates_full_cohort = (
                "all_names" in iter_src
                or ("train_data" in iter_src and "test_data" in iter_src)
            )
            if not iterates_full_cohort:
                continue

            body_src = "\n".join(
                ast.unparse(child) if hasattr(ast, "unparse") else ""
                for child in node.body
            )
            if "h5py.File" in body_src and "np.savez" in body_src:
                found_full_cohort_write = True
                break

        self.assertTrue(
            found_full_cohort_write,
            msg="No loop writing both H5 (geometry_emergent) and NPZ (predictions) "
                "iterates over the full cohort (train+test). Stage 02 would only "
                "materialize the test subcohort, breaking Stage 03/04.",
        )

    def test_no_write_loop_restricted_to_test_only(self):
        """
        Guard against regressing to iterating solely over test_data['names']
        for H5+NPZ writes.
        """
        regression_sites = []
        for node in ast.walk(self.tree):
            if not isinstance(node, ast.For):
                continue
            iter_src = ast.unparse(node.iter) if hasattr(ast, "unparse") else ""
            if 'test_data["names"]' not in iter_src:
                continue
            if "train_data" in iter_src:
                # combined, fine
                continue
            body_src = "\n".join(
                ast.unparse(child) if hasattr(ast, "unparse") else ""
                for child in node.body
            )
            if "h5py.File" in body_src and "np.savez" in body_src:
                regression_sites.append(iter_src)

        self.assertFalse(
            regression_sites,
            msg=(
                "run_train_mode has a write loop restricted to test_data['names'] "
                "only: " + repr(regression_sites)
            ),
        )


if __name__ == "__main__":
    unittest.main()
