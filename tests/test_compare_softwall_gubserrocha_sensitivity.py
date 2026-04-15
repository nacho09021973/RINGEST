from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "tools" / "compare_softwall_gubserrocha_sensitivity.py"


def _load_module():
    name = "compare_softwall_gubserrocha_sensitivity_test"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


class TestSensitivityComparator(unittest.TestCase):
    def test_no_conclusive_when_all_reports_below_threshold(self):
        mod = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / "a.json"
            b = root / "b.json"
            out = root / "out.json"
            for path, value in [(a, 0.05), (b, 0.0)]:
                path.write_text(
                    json.dumps(
                        {
                            "primary_observable": {
                                "value": value,
                                "bootstrap": {"q025": 0.0},
                            },
                            "baseline_status": "NO_BASELINE_SIGNAL",
                        }
                    ),
                    encoding="utf-8",
                )

            exit_code = mod.main(
                [
                    "--sensitivity-name",
                    "n_epochs",
                    "--output-json",
                    str(out),
                    "--input",
                    "default",
                    str(a),
                    "--input",
                    "500",
                    str(b),
                ]
            )
            self.assertEqual(exit_code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["aggregate"]["verdict"], "NO_CONCLUSIVE_SEPARATION")


if __name__ == "__main__":
    unittest.main()
