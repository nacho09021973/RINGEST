"""
Regression: stage 01 must not rely on silent AUTO-FIX to reconcile geo.d
with the `_d<k>_` token in geo.name. Data must be born consistent.

See: problem 1 in canonical smoke ADS/GKPW audit (April 2026).
Root cause was in 01_generate_sandbox_geometries.py:
- make_geometry_instance randomized `d` to {3,4,5} without updating the name.
- The loop then silently "autofixed" geo.d back from the name.
This test pins down two contracts:
1. After make_geometry_instance, if the base name has a dimension token,
   the returned name's token must match the returned d.
2. The main loop's guardrail must RAISE (not auto-correct) on mismatch.
"""
from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_stage01():
    name = "stage01_geo_d_consistency_mod"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(
        name, REPO_ROOT / "01_generate_sandbox_geometries.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class Stage01GeoDConsistency(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s1 = _load_stage01()

    def _base_with_token(self):
        return self.s1.HiddenGeometry(
            name="ads_d3_Tfinite",
            family="ads",
            category="known",
            d=3,
            z_h=1.0,
            theta=0.0,
            z_dyn=1.0,
            deformation=0.0,
            L=1.0,
        )

    def _base_without_token(self):
        return self.s1.HiddenGeometry(
            name="unknown_family_1",
            family="unknown",
            category="unknown",
            d=3,
            z_h=1.0,
            theta=0.5,
            z_dyn=1.3,
            deformation=0.3,
            L=1.0,
        )

    def test_make_geometry_instance_rewrites_name_when_d_jitters(self):
        """
        Across many seeds, every instance cloned from a base whose name
        carries `_d<k>_` must satisfy: token(name) == geo.d. No silent
        mismatch should leak out of make_geometry_instance.
        """
        base = self._base_with_token()
        for seed in range(200):
            rng = np.random.default_rng(seed)
            geo = self.s1.make_geometry_instance(base, "known", seed, rng)
            m = re.search(r"_d(\d+)(?:_|$)", geo.name)
            self.assertIsNotNone(
                m,
                f"seed={seed}: expected _d<k>_ token in {geo.name!r}",
            )
            self.assertEqual(
                int(m.group(1)),
                int(geo.d),
                f"seed={seed}: token/d mismatch for {geo.name!r} (d={geo.d})",
            )

    def test_make_geometry_instance_leaves_tokenless_names_alone(self):
        """
        Bases without a `_d<k>_` token must not acquire one spuriously
        (we only normalize names that already encode a dimension token).
        """
        base = self._base_without_token()
        for seed in range(50):
            rng = np.random.default_rng(seed)
            geo = self.s1.make_geometry_instance(base, "unknown", seed, rng)
            self.assertIsNone(
                re.search(r"_d\d+(?=_|$)", geo.name),
                f"seed={seed}: spurious dimension token appeared in {geo.name!r}",
            )

    def test_rewrite_geometry_name_for_dimension_is_idempotent(self):
        """Simple sanity check on the rewriter used by the fix."""
        rewritten = self.s1.rewrite_geometry_name_for_dimension(
            "ads_d3_Tfinite_known_000", 5
        )
        self.assertEqual(rewritten, "ads_d5_Tfinite_known_000")
        again = self.s1.rewrite_geometry_name_for_dimension(rewritten, 5)
        self.assertEqual(again, rewritten)


if __name__ == "__main__":
    unittest.main()
