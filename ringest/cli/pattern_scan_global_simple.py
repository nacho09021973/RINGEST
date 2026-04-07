from __future__ import annotations

import sys

from ringest.pattern_scan_global_simple import ExecutiveContractError, parse_args, run_pattern_scan_global_simple


def main() -> int:
    args = parse_args()
    try:
        run_pattern_scan_global_simple(
            run_id=args.run_id,
            exp001_run=args.exp001_run,
        )
    except ExecutiveContractError as exc:
        print(f"exp002_pattern_scan_global_simple: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
