"""
Regression tests for tools/decay_type_discrimination.py.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "tools" / "decay_type_discrimination.py"


class TestEmptyInputDirectoryFailsClearly(unittest.TestCase):
    """An empty input_dir must fail fast and must not write empty artifacts."""

    def test_empty_input_dir_exits_nonzero_without_writing_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            input_dir = tmp_path / "input"
            output_dir = tmp_path / "output"
            input_dir.mkdir()

            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--input-dir",
                    str(input_dir),
                    "--output-dir",
                    str(output_dir),
                    "--suffix",
                    "empty_case",
                ],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )

            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("No H5 files found", proc.stderr)
            self.assertFalse(
                (output_dir / "decay_type_discrimination_33_event_canonical_empty_case.csv").exists()
            )
            self.assertFalse(
                (output_dir / "decay_type_discrimination_33_event_canonical_empty_case.json").exists()
            )


if __name__ == "__main__":
    unittest.main()
