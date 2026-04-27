#!/usr/bin/env python3
"""
merge_manifests.py    Merge two geometries_manifest.json files into one.

Usage:
  python3 malda/merge_manifests.py \
      runs/sandbox_v1/01_generate_sandbox_geometries/geometries_manifest.json \
      runs/kerr_sandbox_v1/01b_generate_kerr_sandbox/geometries_manifest.json \
      --out-dir runs/sandbox_v5/01_merged \
      --data-dirs runs/sandbox_v1/01_generate_sandbox_geometries \
                  runs/kerr_sandbox_v1/01b_generate_kerr_sandbox
"""

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("manifests", nargs="+")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--data-dirs", nargs="+", required=True,
                    help="Source data dirs, one per manifest (same order)")
    args = ap.parse_args()

    assert len(args.manifests) == len(args.data_dirs), \
        "Number of --data-dirs must match number of manifests"

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_entries = []
    for manifest_path, data_dir_str in zip(args.manifests, args.data_dirs):
        data_dir = Path(data_dir_str)
        manifest = json.loads(Path(manifest_path).read_text())
        for entry in manifest["geometries"]:
            src = data_dir / f"{entry['name']}.h5"
            dst = out_dir / f"{entry['name']}.h5"
            if not dst.exists():
                shutil.copy2(src, dst)
            all_entries.append(entry)
        print(f"  Loaded {len(manifest['geometries'])} entries from {manifest_path}")

    merged = {
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "script": "merge_manifests.py",
        "version": "merged-v1",
        "geometries": all_entries,
    }
    out_path = out_dir / "geometries_manifest.json"
    out_path.write_text(json.dumps(merged, indent=2))
    print(f"\n[OK] Merged {len(all_entries)} geometries  {out_path}")


if __name__ == "__main__":
    main()
