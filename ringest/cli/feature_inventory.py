from __future__ import annotations

from pathlib import Path

from ringest.feature_inventory import parse_args, run_feature_inventory


def main() -> int:
    args = parse_args()
    run_feature_inventory(
        input_root=Path(args.input_root),
        run_id=args.run_id,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
