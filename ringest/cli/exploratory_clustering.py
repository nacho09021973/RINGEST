from __future__ import annotations

from ringest.exploratory_clustering import parse_args, run_exploratory_clustering


def main() -> int:
    args = parse_args()
    run_exploratory_clustering(
        run_id=args.run_id,
        exp001_run=args.exp001_run,
        exp002_run=args.exp002_run,
        random_seed=args.random_seed,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
